"""Eventos tipados: a única coisa que o frontend enxerga."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field, field_validator

Agent = Literal["crawler", "gate", "scan", "vet", "social", "chief", "size", "card",
                "fills", "risk", "journal", "system"]
Kind = Literal["start", "pass", "fail", "decision", "order", "fill", "exit", "alert",
               "levelup", "achievement"]


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class DeskEvent(BaseModel):
    ts: datetime = Field(default_factory=utcnow)   # sempre UTC
    cycle_id: str
    token: str | None = None
    agent: Agent
    kind: Kind
    score: float | None = None
    payload: dict = Field(default_factory=dict)

    @field_validator("ts")
    @classmethod
    def _utc(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("ts precisa ter fuso (UTC)")
        return v.astimezone(timezone.utc)
