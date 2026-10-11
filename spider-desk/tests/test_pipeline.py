from backend.adapters.mocks.market_mock import MockMarket
from backend.agents.crawler import Crawler
from backend.agents.gate import Gate
from backend.core.bus import EventBus
from backend.core.db import Database
from backend.pipeline import Desk


class BrokenEnrich(MockMarket):
    async def enrich(self, snap):
        raise RuntimeError("rpc down")


async def _desk(cfg, tmp_path, source):
    db = Database(tmp_path / "d.db")
    bus = EventBus()
    bus.subscribe(db.save_event)
    return Desk(Crawler(source, 40), Gate(cfg.gate), bus, db), db


async def test_mock_cycle_end_to_end(cfg, tmp_path):
    src = MockMarket(seed=3, max_ticket_usd=cfg.max_ticket_usd)
    desk, db = await _desk(cfg, tmp_path, src)
    results = await desk.run_cycle()
    assert len(results) == 40
    by_kind = {}
    for s, r in results:
        by_kind.setdefault(src.archetype[s.mint], []).append(r.passed)
    for bad in ("too_new", "thin", "whale", "mintable", "honeypot", "illiquid_exit"):
        assert not any(by_kind.get(bad, [])), bad
    assert any(by_kind["healthy"])
    evs = db.events()
    gate_final = [e for e in evs if e.agent == "gate" and e.kind in ("pass", "fail")]
    assert len(gate_final) == 40
    assert all("checks" in e.payload for e in gate_final)


async def test_enrich_failure_discards(cfg, tmp_path):
    desk, _ = await _desk(cfg, tmp_path, BrokenEnrich(seed=3, max_ticket_usd=20))
    results = await desk.run_cycle()
    assert results and not any(r.passed for _, r in results)
