"""Mercado falso, determinístico (seed), com arquétipos realistas de memecoins Solana.

Usado quando as APIs reais estão inacessíveis, no modo DEMO e nos testes.
"""
from __future__ import annotations

import random
import string

from ...core.events import utcnow
from ...core.models import SellQuote, TokenSnapshot

B58 = "".join(c for c in string.ascii_letters + string.digits if c not in "0OIl")

SYLL = ["pep", "bon", "wif", "moo", "cat", "dog", "zap", "fro", "gig", "nyx", "sol", "kek", "pump", "lun"]

# arquétipo → peso
ARCHETYPES = {
    "healthy": 3,
    "too_new": 2,
    "thin": 2,          # liquidez/volume baixos
    "whale": 2,         # concentração alta
    "mintable": 1,      # mint authority ativa
    "honeypot": 1,      # sem rota de venda
    "illiquid_exit": 1, # vende com impacto alto
}


def _addr(rng: random.Random) -> str:
    return "".join(rng.choice(B58) for _ in range(rng.choice([43, 44])))


class MockMarket:
    name = "mock"

    def __init__(self, seed: int = 7, max_ticket_usd: float = 20.0) -> None:
        self.rng = random.Random(seed)
        self.max_ticket_usd = max_ticket_usd
        self.archetype: dict[str, str] = {}

    def _make(self) -> TokenSnapshot:
        r = self.rng
        kind = r.choices(list(ARCHETYPES), weights=list(ARCHETYPES.values()))[0]
        sym = (r.choice(SYLL) + r.choice(SYLL)).upper()[:8]
        liq = r.uniform(15_000, 250_000)
        vol = liq * r.uniform(1.5, 12)
        snap = TokenSnapshot(
            ts=utcnow(), mint=_addr(r), symbol=sym, name=f"{sym.title()} Coin",
            pair_address=_addr(r), dex=r.choice(["raydium", "meteora", "pumpswap", "orca"]),
            price_usd=r.uniform(1e-6, 0.02), mcap_usd=liq * r.uniform(4, 20),
            liquidity_usd=liq, volume_h24=vol, trades_h24=int(vol / r.uniform(80, 400)),
            pair_age_min=r.uniform(20, 60 * 48), holders=r.randint(300, 8000),
            top_wallet_pct=r.uniform(0.01, 0.045), top10_pct=r.uniform(0.15, 0.5),
            decimals=6, mint_authority_revoked=True, freeze_authority_null=True, source="mock",
        )
        if kind == "too_new":
            snap.pair_age_min = r.uniform(1, 14)
        elif kind == "thin":
            snap.liquidity_usd = r.uniform(2_000, 11_000)
            snap.volume_h24 = r.uniform(3_000, 35_000)
            snap.trades_h24 = r.randint(20, 140)
            snap.mcap_usd = r.uniform(20_000, 55_000)
        elif kind == "whale":
            snap.top_wallet_pct = r.uniform(0.08, 0.35)
            snap.top10_pct = r.uniform(0.62, 0.9)
        elif kind == "mintable":
            snap.mint_authority_revoked = False
            snap.freeze_authority_null = r.random() < 0.5
        self.archetype[snap.mint] = kind
        return snap

    async def scan(self, limit: int) -> list[TokenSnapshot]:
        return [self._make() for _ in range(limit)]

    async def enrich(self, snap: TokenSnapshot) -> TokenSnapshot:
        s = snap.model_copy()
        kind = self.archetype.get(s.mint, "healthy")
        if kind == "honeypot":
            s.sell_quote = SellQuote(ok=False, error="mock: sem rota de venda")
            return s
        ticket = self.max_ticket_usd
        impact = ticket / max(s.liquidity_usd or 1, 1) * 2
        if kind == "illiquid_exit":
            impact = self.rng.uniform(0.06, 0.3)
        amount = int(ticket / (s.price_usd or 1) * 10 ** (s.decimals or 6))
        s.sell_quote = SellQuote(ok=True, in_amount=amount,
                                 out_amount=int(ticket * (1 - impact) * 1e6),
                                 price_impact=impact, route_labels=[s.dex or "?"])
        return s

    async def aclose(self) -> None:
        return None
