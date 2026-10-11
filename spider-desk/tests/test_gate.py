import pytest

from backend.agents.gate import Gate
from backend.core.models import SellQuote


def test_good_token_passes(cfg, good_snap):
    r = Gate(cfg.gate).evaluate(good_snap)
    assert r.passed, r.failed


@pytest.mark.parametrize("field,value,rule", [
    ("pair_age_min", 5, "min_age_minutes"),
    ("liquidity_usd", 5_000, "min_liquidity_usd"),
    ("volume_h24", 1_000, "min_volume_h24"),
    ("mcap_usd", 10_000, "min_mcap_usd"),
    ("trades_h24", 10, "min_trades_h24"),
    ("top_wallet_pct", 0.2, "max_top_wallet"),
    ("top10_pct", 0.7, "max_top_10"),
    ("mint_authority_revoked", False, "require_mint_authority_revoked"),
    ("freeze_authority_null", False, "require_freeze_authority_null"),
])
def test_each_rule_rejects(cfg, good_snap, field, value, rule):
    s = good_snap.model_copy(update={field: value})
    r = Gate(cfg.gate).evaluate(s)
    assert not r.passed and [c.rule for c in r.failed] == [rule]


@pytest.mark.parametrize("field", ["liquidity_usd", "top_wallet_pct", "mint_authority_revoked"])
def test_missing_data_fails(cfg, good_snap, field):
    assert not Gate(cfg.gate).evaluate(good_snap.model_copy(update={field: None})).passed


def test_honeypot_and_high_impact(cfg, good_snap):
    g = Gate(cfg.gate)
    hp = good_snap.model_copy(update={"sell_quote": SellQuote(ok=False, error="no route")})
    assert {c.rule for c in g.evaluate(hp).failed} == {"require_sell_route", "max_sell_price_impact"}
    hi = good_snap.model_copy(update={"sell_quote": SellQuote(ok=True, price_impact=0.2)})
    assert [c.rule for c in g.evaluate(hi).failed] == ["max_sell_price_impact"]
    nq = good_snap.model_copy(update={"sell_quote": None})
    assert not g.evaluate(nq).passed


def test_blocklist(cfg, good_snap):
    r = Gate(cfg.gate, {good_snap.mint}).evaluate(good_snap)
    assert r.reason == "blocklist"


def test_market_stage_ignores_chain_rules(cfg, good_snap):
    s = good_snap.model_copy(update={"mint_authority_revoked": None, "sell_quote": None})
    assert Gate(cfg.gate).evaluate(s, stage="market").passed
