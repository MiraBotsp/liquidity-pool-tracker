"""Fachada de dados de mercado: real (DexScreener + RPC + Jupiter) ou mock."""
from __future__ import annotations

from typing import Protocol

import httpx
import structlog

from ..core.config import DeskConfig, Secrets
from ..core.http import ApiError
from ..core.models import SellQuote, TokenSnapshot
from .dexscreener import DexScreener
from .jupiter import Jupiter
from .solana_rpc import SolanaRpc

log = structlog.get_logger()


class MarketSource(Protocol):
    name: str

    async def scan(self, limit: int) -> list[TokenSnapshot]:
        """Descobre tokens e devolve dados de mercado (preço, liquidez, volume...)."""

    async def enrich(self, snap: TokenSnapshot) -> TokenSnapshot:
        """Completa com dados on-chain e cotação de venda. Campos indisponíveis ficam None."""

    async def aclose(self) -> None: ...


class RealMarket:
    name = "real"

    def __init__(self, cfg: DeskConfig, secrets: Secrets) -> None:
        self.cfg = cfg
        self.client = httpx.AsyncClient(timeout=cfg.http.timeout_s,
                                        headers={"User-Agent": "spider-desk/0.1"})
        rl, h = cfg.rate_limits, cfg.http
        kw = dict(retries=h.retries, backoff=h.backoff_base_s)
        self.dex = DexScreener(self.client, profiles_rpm=rl.dexscreener_profiles_rpm,
                               pairs_rpm=rl.dexscreener_pairs_rpm, chain_id=cfg.crawl.chain_id, **kw)
        rpc_url = secrets.solana_rpc_url.get_secret_value() if secrets.solana_rpc_url else None
        self.rpc = SolanaRpc(self.client, rpc_url, rpm=rl.solana_rpc_rpm, **kw)
        self.jup = Jupiter(self.client, rpm=rl.jupiter_rpm, **kw)
        self.excluded = set(cfg.gate.excluded_owners)

    async def probe(self) -> bool:
        try:
            await self.dex.discover(1)
            return True
        except Exception as e:
            log.warning("market.probe_failed", error=str(e))
            return False

    async def scan(self, limit: int) -> list[TokenSnapshot]:
        mints = await self.dex.discover(limit)
        pairs = await self.dex.best_pairs(mints)
        return [pairs[m] for m in mints if m in pairs]

    async def enrich(self, snap: TokenSnapshot) -> TokenSnapshot:
        s = snap.model_copy()
        try:
            info = await self.rpc.mint_info(s.mint)
            s.decimals = info["decimals"]
            s.mint_authority_revoked = info["mint_authority_revoked"]
            s.freeze_authority_null = info["freeze_authority_null"]
            excluded = self.excluded | ({s.pair_address} if s.pair_address else set())
            s.top_wallet_pct, s.top10_pct = await self.rpc.concentration(s.mint, info["supply"], excluded)
        except ApiError as e:
            log.info("enrich.rpc_failed", mint=s.mint, error=str(e))
        s.sell_quote = await self._sell_quote(s)
        return s

    async def _sell_quote(self, s: TokenSnapshot) -> SellQuote:
        if not s.price_usd or s.decimals is None:
            return SellQuote(ok=False, error="sem preço/decimais")
        amount = int(self.cfg.max_ticket_usd / s.price_usd * 10 ** s.decimals)
        return await self.jup.quote(s.mint, self.cfg.crawl.quote_mint, amount)

    async def aclose(self) -> None:
        await self.client.aclose()
