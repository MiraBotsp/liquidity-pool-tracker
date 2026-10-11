"""DexScreener (API pública, sem chave). Docs: https://docs.dexscreener.com/api/reference

Endpoints usados:
- GET /token-profiles/latest/v1   (60 rpm)  → tokens com perfil recente (descoberta)
- GET /token-boosts/latest/v1     (60 rpm)  → tokens com boost recente (descoberta)
- GET /tokens/v1/{chainId}/{a,b,...}  (300 rpm, até 30 endereços) → pares do token
"""
from __future__ import annotations

from datetime import datetime, timezone

import httpx

from ..core.http import RateLimiter, request_json
from ..core.models import TokenSnapshot

BASE = "https://api.dexscreener.com"


class DexScreener:
    def __init__(self, client: httpx.AsyncClient, *, profiles_rpm: int, pairs_rpm: int,
                 chain_id: str = "solana", retries: int = 3, backoff: float = 0.5) -> None:
        self.c = client
        self.chain = chain_id
        self.lim_profiles = RateLimiter(profiles_rpm)
        self.lim_pairs = RateLimiter(pairs_rpm)
        self.retries, self.backoff = retries, backoff

    async def _get(self, path: str, limiter: RateLimiter):
        return await request_json(self.c, "GET", BASE + path, limiter=limiter,
                                  retries=self.retries, backoff=self.backoff)

    async def discover(self, limit: int) -> list[str]:
        """Mints recentes na rede, sem repetição, na ordem em que apareceram."""
        seen: dict[str, None] = {}
        for path in ("/token-profiles/latest/v1", "/token-boosts/latest/v1"):
            data = await self._get(path, self.lim_profiles)
            for item in data if isinstance(data, list) else []:
                if item.get("chainId") == self.chain and item.get("tokenAddress"):
                    seen.setdefault(item["tokenAddress"], None)
        return list(seen)[:limit]

    async def best_pairs(self, mints: list[str]) -> dict[str, TokenSnapshot]:
        """Para cada mint, o par de maior liquidez em que ele é o token base."""
        out: dict[str, TokenSnapshot] = {}
        for i in range(0, len(mints), 30):
            chunk = mints[i:i + 30]
            data = await self._get(f"/tokens/v1/{self.chain}/{','.join(chunk)}", self.lim_pairs)
            for pair in data if isinstance(data, list) else []:
                snap = parse_pair(pair)
                if snap is None or snap.mint not in chunk:
                    continue
                cur = out.get(snap.mint)
                if cur is None or (snap.liquidity_usd or 0) > (cur.liquidity_usd or 0):
                    out[snap.mint] = snap
        return out


def _f(x) -> float | None:
    try:
        return float(x) if x is not None else None
    except (TypeError, ValueError):
        return None


def parse_pair(p: dict, now: datetime | None = None) -> TokenSnapshot | None:
    base = p.get("baseToken") or {}
    if not base.get("address"):
        return None
    now = now or datetime.now(timezone.utc)
    created = p.get("pairCreatedAt")
    age = (now.timestamp() * 1000 - created) / 60_000 if created else None
    h24 = (p.get("txns") or {}).get("h24") or {}
    trades = (h24.get("buys") or 0) + (h24.get("sells") or 0) if h24 else None
    return TokenSnapshot(
        ts=now,
        mint=base["address"],
        symbol=str(base.get("symbol") or "?")[:20],
        name=str(base.get("name") or "?")[:60],
        pair_address=p.get("pairAddress"),
        dex=p.get("dexId"),
        price_usd=_f(p.get("priceUsd")),
        mcap_usd=_f(p.get("marketCap")) or _f(p.get("fdv")),
        liquidity_usd=_f((p.get("liquidity") or {}).get("usd")),
        volume_h24=_f((p.get("volume") or {}).get("h24")),
        trades_h24=trades,
        pair_age_min=age,
    )
