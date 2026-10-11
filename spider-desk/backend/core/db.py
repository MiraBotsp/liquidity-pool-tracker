"""SQLite: eventos (auditoria + replay) e snapshots de mercado."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from .events import DeskEvent
from .models import TokenSnapshot

SCHEMA = """
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL,
    cycle_id TEXT NOT NULL,
    token TEXT,
    agent TEXT NOT NULL,
    kind TEXT NOT NULL,
    score REAL,
    payload TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_events_ts ON events(ts);
CREATE INDEX IF NOT EXISTS ix_events_cycle ON events(cycle_id);
CREATE INDEX IF NOT EXISTS ix_events_token ON events(token);

CREATE TABLE IF NOT EXISTS snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL,
    cycle_id TEXT NOT NULL,
    mint TEXT NOT NULL,
    price_usd REAL,
    liquidity_usd REAL,
    data TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_snap_mint_ts ON snapshots(mint, ts);
"""


class Database:
    def __init__(self, path: str | Path) -> None:
        self.conn = sqlite3.connect(str(path))
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.executescript(SCHEMA)

    def close(self) -> None:
        self.conn.close()

    def save_event(self, e: DeskEvent) -> None:
        self.conn.execute(
            "INSERT INTO events(ts,cycle_id,token,agent,kind,score,payload) VALUES (?,?,?,?,?,?,?)",
            (e.ts.isoformat(), e.cycle_id, e.token, e.agent, e.kind, e.score,
             json.dumps(e.payload, default=str)),
        )
        self.conn.commit()

    def save_snapshot(self, cycle_id: str, s: TokenSnapshot) -> None:
        self.conn.execute(
            "INSERT INTO snapshots(ts,cycle_id,mint,price_usd,liquidity_usd,data) VALUES (?,?,?,?,?,?)",
            (s.ts.isoformat(), cycle_id, s.mint, s.price_usd, s.liquidity_usd, s.model_dump_json()),
        )
        self.conn.commit()

    def events(self, *, since: str | None = None, until: str | None = None,
               cycle_id: str | None = None, limit: int = 10_000) -> list[DeskEvent]:
        """Leitura ordenada por tempo — base do REPLAY (nunca retorna nada após `until`)."""
        q, args = "SELECT * FROM events WHERE 1=1", []
        if since:
            q += " AND ts >= ?"; args.append(since)
        if until:
            q += " AND ts <= ?"; args.append(until)
        if cycle_id:
            q += " AND cycle_id = ?"; args.append(cycle_id)
        q += " ORDER BY ts, id LIMIT ?"; args.append(limit)
        return [DeskEvent(ts=r["ts"], cycle_id=r["cycle_id"], token=r["token"], agent=r["agent"],
                          kind=r["kind"], score=r["score"], payload=json.loads(r["payload"]))
                for r in self.conn.execute(q, args)]

    def snapshots_for(self, mint: str, until: str | None = None) -> list[TokenSnapshot]:
        q, args = "SELECT data FROM snapshots WHERE mint = ?", [mint]
        if until:
            q += " AND ts <= ?"; args.append(until)
        q += " ORDER BY ts"
        return [TokenSnapshot.model_validate_json(r["data"]) for r in self.conn.execute(q, args)]
