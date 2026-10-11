"""CRAWLER — descobre tokens e completa dados on-chain, sempre via MarketSource."""
from __future__ import annotations

import asyncio

from ..adapters.market import MarketSource
from ..core.models import TokenSnapshot


class Crawler:
    def __init__(self, source: MarketSource, max_tokens: int, concurrency: int = 4) -> None:
        self.source = source
        self.max_tokens = max_tokens
        self._sem = asyncio.Semaphore(concurrency)

    async def scan(self) -> list[TokenSnapshot]:
        return await self.source.scan(self.max_tokens)

    async def enrich(self, snap: TokenSnapshot) -> TokenSnapshot:
        async with self._sem:
            return await self.source.enrich(snap)
