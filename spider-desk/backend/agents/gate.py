"""GATE — regras duras em Python puro, custo zero. Dado ausente = reprova."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from pydantic import BaseModel

from ..core.config import GateCfg
from ..core.models import TokenSnapshot


class RuleCheck(BaseModel):
    rule: str
    passed: bool
    value: float | bool | str | None
    threshold: float | bool | str | None


class GateResult(BaseModel):
    passed: bool
    checks: list[RuleCheck]

    @property
    def failed(self) -> list[RuleCheck]:
        return [c for c in self.checks if not c.passed]

    @property
    def reason(self) -> str | None:
        f = self.failed
        return f[0].rule if f else None


@dataclass(frozen=True)
class Rule:
    name: str
    stage: str                       # "market" (DexScreener) ou "chain" (RPC/Jupiter)
    enabled: Callable[[GateCfg], bool]
    check: Callable[[TokenSnapshot, GateCfg], tuple[bool, object, object]]


def _min(field: str, attr: str):
    def f(s: TokenSnapshot, g: GateCfg):
        v, t = getattr(s, field), getattr(g, attr)
        return (v is not None and v >= t), v, t
    return f


def _max(field: str, attr: str):
    def f(s: TokenSnapshot, g: GateCfg):
        v, t = getattr(s, field), getattr(g, attr)
        return (v is not None and v <= t), v, t
    return f


def _sell_route(s: TokenSnapshot, g: GateCfg):
    ok = bool(s.sell_quote and s.sell_quote.ok)
    return ok, ok if s.sell_quote else None, True


def _sell_impact(s: TokenSnapshot, g: GateCfg):
    v = s.sell_quote.price_impact if (s.sell_quote and s.sell_quote.ok) else None
    return (v is not None and v <= g.max_sell_price_impact), v, g.max_sell_price_impact


ALWAYS = lambda g: True  # noqa: E731

RULES: list[Rule] = [
    Rule("min_age_minutes", "market", ALWAYS, _min("pair_age_min", "min_age_minutes")),
    Rule("min_liquidity_usd", "market", ALWAYS, _min("liquidity_usd", "min_liquidity_usd")),
    Rule("min_volume_h24", "market", ALWAYS, _min("volume_h24", "min_volume_h24")),
    Rule("min_mcap_usd", "market", ALWAYS, _min("mcap_usd", "min_mcap_usd")),
    Rule("min_trades_h24", "market", ALWAYS, _min("trades_h24", "min_trades_h24")),
    Rule("require_mint_authority_revoked", "chain", lambda g: g.require_mint_authority_revoked,
         lambda s, g: (s.mint_authority_revoked is True, s.mint_authority_revoked, True)),
    Rule("require_freeze_authority_null", "chain", lambda g: g.require_freeze_authority_null,
         lambda s, g: (s.freeze_authority_null is True, s.freeze_authority_null, True)),
    Rule("max_top_wallet", "chain", ALWAYS, _max("top_wallet_pct", "max_top_wallet")),
    Rule("max_top_10", "chain", ALWAYS, _max("top10_pct", "max_top_10")),
    Rule("require_sell_route", "chain", lambda g: g.require_sell_route, _sell_route),
    Rule("max_sell_price_impact", "chain", ALWAYS, _sell_impact),
]


class Gate:
    def __init__(self, cfg: GateCfg, blocklist: set[str] | None = None) -> None:
        self.cfg = cfg
        self.blocklist = blocklist or set()

    def evaluate(self, s: TokenSnapshot, stage: str | None = None) -> GateResult:
        """`stage="market"` avalia só o que vem do DexScreener (antes de gastar RPC)."""
        checks = [RuleCheck(rule="blocklist", passed=s.mint not in self.blocklist,
                            value=s.mint in self.blocklist, threshold=False)]
        for r in RULES:
            if (stage and r.stage != stage) or not r.enabled(self.cfg):
                continue
            ok, v, t = r.check(s, self.cfg)
            checks.append(RuleCheck(rule=r.name, passed=bool(ok), value=v, threshold=t))
        return GateResult(passed=all(c.passed for c in checks), checks=checks)
