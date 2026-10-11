"""Jupiter Swap API — cotação (GET /quote). Docs: https://dev.jup.ag/docs/swap-api

lite-api.jup.ag é o plano gratuito sem chave; api.jup.ag exige x-api-key.
Resposta usada: inAmount, outAmount (strings), priceImpactPct (string, fração), routePlan[].swapInfo.label
"""
from __future__ import annotations

import httpx

from ..core.http import ApiError, RateLimiter, request_json
from ..core.models import SellQuote

LITE = "https://lite-api.jup.ag/swap/v1"


class Jupiter:
    def __init__(self, client: httpx.AsyncClient, *, rpm: int, base_url: str = LITE,
                 retries: int = 3, backoff: float = 0.5) -> None:
        self.c = client
        self.base = base_url
        self.lim = RateLimiter(rpm)
        self.retries, self.backoff = retries, backoff

    async def quote(self, input_mint: str, output_mint: str, amount: int,
                    slippage_bps: int = 100) -> SellQuote:
        if amount <= 0:
            return SellQuote(ok=False, error="amount<=0")
        try:
            d = await request_json(
                self.c, "GET", f"{self.base}/quote", limiter=self.lim,
                retries=self.retries, backoff=self.backoff,
                params={"inputMint": input_mint, "outputMint": output_mint,
                        "amount": str(amount), "slippageBps": slippage_bps},
            )
        except ApiError as e:   # sem rota = 4xx; tratamos como "sem rota de venda"
            return SellQuote(ok=False, in_amount=amount, error=str(e)[:200])
        try:
            out = int(d["outAmount"])
            impact = float(d.get("priceImpactPct") or 0)
        except (KeyError, TypeError, ValueError):
            return SellQuote(ok=False, in_amount=amount, error="resposta inválida")
        labels = [((r.get("swapInfo") or {}).get("label") or "?") for r in d.get("routePlan", [])]
        return SellQuote(ok=out > 0, in_amount=int(d.get("inAmount", amount)), out_amount=out,
                         price_impact=abs(impact), route_labels=labels)
