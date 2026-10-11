import asyncio
from datetime import datetime, timedelta, timezone

import pytest
import yaml
from pydantic import ValidationError

from backend.core.bus import EventBus
from backend.core.config import DeskConfig, ROOT, load_config, load_secrets
from backend.core.db import Database
from backend.core.events import DeskEvent


def test_config_loads_paper_by_default(cfg):
    assert cfg.mode == "paper"
    assert cfg.max_ticket_usd == pytest.approx(20.0)


def test_config_rejects_unknown_and_out_of_range():
    data = yaml.safe_load((ROOT / "config.yaml").read_text())
    data["gate"]["max_top_wallet"] = 1.5
    with pytest.raises(ValidationError):
        DeskConfig.model_validate(data)
    data = yaml.safe_load((ROOT / "config.yaml").read_text())
    data["gate"]["typo_rule"] = 1
    with pytest.raises(ValidationError):
        DeskConfig.model_validate(data)


def test_live_mode_refused(tmp_path):
    data = yaml.safe_load((ROOT / "config.yaml").read_text())
    data["mode"] = "live"
    p = tmp_path / "c.yaml"
    p.write_text(yaml.safe_dump(data))
    with pytest.raises(ValueError):
        load_config(p)


def test_secrets_are_masked(monkeypatch, tmp_path):
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-v1-secret")
    s = load_secrets(tmp_path / "missing.env")
    assert "sk-or" not in repr(s) and "sk-or" not in s.model_dump_json()
    assert s.openrouter_api_key.get_secret_value() == "sk-or-v1-secret"
    assert s.live_trading is False


def test_event_requires_timezone():
    with pytest.raises(ValidationError):
        DeskEvent(ts=datetime(2026, 1, 1), cycle_id="c", agent="gate", kind="pass")


async def test_bus_survives_broken_handler_and_streams():
    bus, got = EventBus(), []
    bus.subscribe(lambda e: 1 / 0)
    bus.subscribe(got.append)
    q = bus.stream()
    await bus.publish(DeskEvent(cycle_id="c", agent="gate", kind="pass"))
    assert len(got) == 1 and q.qsize() == 1


async def test_bus_stream_drops_oldest_when_full():
    bus = EventBus()
    q = bus.stream(maxsize=2)
    for i in range(3):
        await bus.publish(DeskEvent(cycle_id=str(i), agent="gate", kind="pass"))
    assert [q.get_nowait().cycle_id for _ in range(2)] == ["1", "2"]


def test_db_roundtrip_and_no_lookahead(tmp_path, good_snap):
    db = Database(tmp_path / "t.db")
    t0 = datetime(2026, 1, 1, tzinfo=timezone.utc)
    for i in range(3):
        db.save_event(DeskEvent(ts=t0 + timedelta(minutes=i), cycle_id="c", token="m",
                                agent="gate", kind="pass", payload={"i": i}))
    evs = db.events(until=(t0 + timedelta(minutes=1)).isoformat())
    assert [e.payload["i"] for e in evs] == [0, 1]
    db.save_snapshot("c", good_snap)
    assert db.snapshots_for(good_snap.mint)[0].symbol == "GOOD"
