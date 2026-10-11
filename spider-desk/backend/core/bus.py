"""EventBus assíncrono: agentes publicam, assinantes (DB, WebSocket, testes) consomem."""
from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable

import structlog

from .events import DeskEvent

log = structlog.get_logger()

Handler = Callable[[DeskEvent], Awaitable[None] | None]


class EventBus:
    def __init__(self) -> None:
        self._handlers: list[Handler] = []
        self._queues: set[asyncio.Queue[DeskEvent]] = set()

    def subscribe(self, handler: Handler) -> None:
        self._handlers.append(handler)

    def stream(self, maxsize: int = 1000) -> asyncio.Queue[DeskEvent]:
        """Fila para consumidores lentos (ex.: WebSocket). Remova com `unstream`."""
        q: asyncio.Queue[DeskEvent] = asyncio.Queue(maxsize=maxsize)
        self._queues.add(q)
        return q

    def unstream(self, q: asyncio.Queue[DeskEvent]) -> None:
        self._queues.discard(q)

    async def publish(self, event: DeskEvent) -> None:
        for h in self._handlers:
            try:
                res = h(event)
                if asyncio.iscoroutine(res):
                    await res
            except Exception:  # um assinante quebrado não pode parar a mesa
                log.exception("bus.handler_failed", agent=event.agent, kind=event.kind)
        for q in list(self._queues):
            if q.full():  # descarta o mais antigo em vez de travar o pipeline
                q.get_nowait()
            q.put_nowait(event)
