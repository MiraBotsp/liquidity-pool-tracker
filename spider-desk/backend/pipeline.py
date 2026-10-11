"""Orquestra um ciclo: CRAWLER → GATE (mercado) → enriquecer → GATE (on-chain).

Fase 1 termina no GATE. As próximas estações entram aqui nas fases seguintes.
"""
from __future__ import annotations

import asyncio
import uuid

import structlog

from .agents.crawler import Crawler
from .agents.gate import Gate, GateResult
from .core.bus import EventBus
from .core.db import Database
from .core.events import DeskEvent, utcnow
from .core.models import TokenSnapshot

log = structlog.get_logger()


def new_cycle_id() -> str:
    return utcnow().strftime("%Y%m%dT%H%M%S") + "-" + uuid.uuid4().hex[:6]


def _gate_payload(s: TokenSnapshot, r: GateResult) -> dict:
    return {
        "symbol": s.symbol,
        "reason": r.reason,
        "checks": [c.model_dump() for c in r.checks],
        "price_usd": s.price_usd,
        "liquidity_usd": s.liquidity_usd,
        "source": s.source,
    }


class Desk:
    def __init__(self, crawler: Crawler, gate: Gate, bus: EventBus, db: Database) -> None:
        self.crawler, self.gate, self.bus, self.db = crawler, gate, bus, db

    async def emit(self, **kw) -> None:
        await self.bus.publish(DeskEvent(**kw))

    async def run_cycle(self) -> list[tuple[TokenSnapshot, GateResult]]:
        cid = new_cycle_id()
        await self.emit(cycle_id=cid, agent="crawler", kind="start", payload={})
        try:
            snaps = await self.crawler.scan()
        except Exception as e:
            await self.emit(cycle_id=cid, agent="system", kind="alert",
                            payload={"msg": "falha no crawler", "error": str(e)[:200]})
            return []
        await self.emit(cycle_id=cid, agent="crawler", kind="pass",
                        payload={"found": len(snaps)})
        results = await asyncio.gather(*(self._process(cid, s) for s in snaps))
        return list(results)

    async def _process(self, cid: str, snap: TokenSnapshot) -> tuple[TokenSnapshot, GateResult]:
        await self.emit(cycle_id=cid, token=snap.mint, agent="gate", kind="start",
                        payload={"symbol": snap.symbol})
        result = self.gate.evaluate(snap, stage="market")   # barato primeiro
        if result.passed:
            try:
                snap = await self.crawler.enrich(snap)
            except Exception as e:      # falha = descartar, nunca comprar
                log.info("enrich.failed", mint=snap.mint, error=str(e))
            result = self.gate.evaluate(snap)
        self.db.save_snapshot(cid, snap)
        passed_n = sum(c.passed for c in result.checks)
        await self.emit(cycle_id=cid, token=snap.mint, agent="gate",
                        kind="pass" if result.passed else "fail",
                        score=passed_n / len(result.checks), payload=_gate_payload(snap, result))
        return snap, result
