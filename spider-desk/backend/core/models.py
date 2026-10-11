"""Modelos de dados de mercado compartilhados por adapters e agentes."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from .events import utcnow


class SellQuote(BaseModel):
    ok: bool
    in_amount: int = 0          # unidades brutas do token
    out_amount: int = 0         # unidades brutas do quote (USDC, 6 casas)
    price_impact: float | None = None   # fração (0.01 = 1%)
    route_labels: list[str] = []
    error: str | None = None


class TokenSnapshot(BaseModel):
    """Retrato de um token num instante. Campos None = dado indisponível (o GATE reprova)."""
    ts: datetime = Field(default_factory=utcnow)
    mint: str
    symbol: str = "?"
    name: str = "?"                     # dado NÃO confiável (vem da internet)
    pair_address: str | None = None
    dex: str | None = None
    price_usd: float | None = None
    mcap_usd: float | None = None
    liquidity_usd: float | None = None
    volume_h24: float | None = None
    trades_h24: int | None = None
    pair_age_min: float | None = None
    holders: int | None = None
    top_wallet_pct: float | None = None   # fração, já sem pool/burn
    top10_pct: float | None = None
    decimals: int | None = None
    mint_authority_revoked: bool | None = None
    freeze_authority_null: bool | None = None
    sell_quote: SellQuote | None = None
    source: str = "real"                  # real | mock
