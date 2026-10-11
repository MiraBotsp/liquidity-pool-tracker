"""Cliente HTTP com rate limiter por host, timeout e retry com backoff."""
from __future__ import annotations

import asyncio
import time
from typing import Any

import httpx
import structlog

log = structlog.get_logger()


class RateLimiter:
    """Espaçamento mínimo entre requisições (rpm) — simples e previsível."""

    def __init__(self, rpm: int) -> None:
        self.interval = 60.0 / rpm
        self._next = 0.0
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        async with self._lock:
            now = time.monotonic()
            wait = self._next - now
            if wait > 0:
                await asyncio.sleep(wait)
                now = time.monotonic()
            self._next = now + self.interval


class ApiError(RuntimeError):
    def __init__(self, msg: str, status: int | None = None) -> None:
        super().__init__(msg)
        self.status = status


RETRYABLE = {429, 500, 502, 503, 504}


async def request_json(client: httpx.AsyncClient, method: str, url: str, *,
                       limiter: RateLimiter | None = None, retries: int = 3,
                       backoff: float = 0.5, **kw: Any) -> Any:
    last: Exception | None = None
    for attempt in range(retries + 1):
        if limiter:
            await limiter.acquire()
        try:
            r = await client.request(method, url, **kw)
            if r.status_code >= 400:
                # corpo truncado; nunca logamos headers (podem conter chaves)
                raise ApiError(f"HTTP {r.status_code}: {r.text[:200]}", r.status_code)
            return r.json()
        except (httpx.TransportError, ApiError, ValueError) as e:
            last = e
            if isinstance(e, ApiError) and e.status not in RETRYABLE:
                break  # 4xx definitivo: não adianta repetir
            if attempt < retries:
                await asyncio.sleep(backoff * 2 ** attempt)
    host = httpx.URL(url).host
    log.warning("http.failed", host=host, error=str(last))
    raise ApiError(f"{host}: {last}")
