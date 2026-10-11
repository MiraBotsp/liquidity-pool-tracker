"""Jev (TypeSafe) via OpenRouter Decisions API — POST {base_url}/decisions.

Formato (exemplo oficial do OpenRouter): o modelo responde perguntas tipadas sobre um `state`.
- "noul":   criteria {"true": ..., "false": ...}  → answers[q] = {"type": "noul", "noul": p_sim}
- "choice": criteria {opção: descrição}          → {"type": "choice", "choice": str, "probabilities": {...}}
- "score":  criteria [rótulos em ordem]           → {"type": "score", "score": float, ...}
O Jev não gera texto livre. Toda resposta é validada; qualquer desvio levanta JevError
e o token é descartado (nunca comprado).
"""
from __future__ import annotations

import json
import math
from typing import Annotated, Literal, Union

import httpx
from pydantic import BaseModel, Field, ValidationError

from ..core.http import ApiError, RateLimiter, request_json


class JevError(RuntimeError):
    pass


# ---- perguntas -------------------------------------------------------------

class NoulQ(BaseModel):
    type: Literal["noul"] = "noul"
    instructions: str
    criteria: dict[Literal["true", "false"], str]


class ChoiceQ(BaseModel):
    type: Literal["choice"] = "choice"
    instructions: str
    criteria: dict[str, str]


class ScoreQ(BaseModel):
    type: Literal["score"] = "score"
    instructions: str
    criteria: list[str]


Question = Union[NoulQ, ChoiceQ, ScoreQ]

# ---- respostas -------------------------------------------------------------

Prob = Annotated[float, Field(ge=0, le=1)]


class NoulA(BaseModel):
    type: Literal["noul"]
    noul: Prob


class ChoiceA(BaseModel):
    type: Literal["choice"]
    choice: str
    probabilities: dict[str, Prob]


class ScoreA(BaseModel):
    type: Literal["score"]
    score: float
    probabilities: list[Prob] | dict[str, Prob] | None = None


Answer = Annotated[Union[NoulA, ChoiceA, ScoreA], Field(discriminator="type")]


class DecisionResponse(BaseModel):
    answers: dict[str, Answer]


def validate_answers(questions: dict[str, Question], raw: object) -> dict[str, NoulA | ChoiceA | ScoreA]:
    """Confere schema, tipo de cada resposta e coerência das probabilidades."""
    try:
        resp = DecisionResponse.model_validate(raw)
    except ValidationError as e:
        raise JevError(f"resposta fora do schema: {e.error_count()} erro(s)") from e
    out = {}
    for name, q in questions.items():
        a = resp.answers.get(name)
        if a is None:
            raise JevError(f"pergunta sem resposta: {name}")
        if a.type != q.type:
            raise JevError(f"{name}: tipo {a.type} ≠ {q.type}")
        if isinstance(a, ChoiceA):
            assert isinstance(q, ChoiceQ)
            if set(a.probabilities) != set(q.criteria) or a.choice not in q.criteria:
                raise JevError(f"{name}: opções desconhecidas")
            if not math.isclose(sum(a.probabilities.values()), 1.0, abs_tol=0.02):
                raise JevError(f"{name}: probabilidades não somam 1")
        if isinstance(a, ScoreA):
            assert isinstance(q, ScoreQ)
            if not (0 <= a.score <= len(q.criteria) - 1 or 0 <= a.score <= 1):
                raise JevError(f"{name}: score fora da escala")
        out[name] = a
    return out


class JevClient:
    def __init__(self, client: httpx.AsyncClient, api_key: str, *, model: str,
                 base_url: str, rpm: int = 60, retries: int = 2, backoff: float = 0.5,
                 site_name: str = "Spider Desk") -> None:
        self.c = client
        self.model = model
        self.url = base_url.rstrip("/") + "/decisions"
        self._headers = {"Authorization": f"Bearer {api_key}",
                         "Content-Type": "application/json",
                         "X-OpenRouter-Title": site_name}
        self.lim = RateLimiter(rpm)
        self.retries, self.backoff = retries, backoff

    async def decide(self, state: str | dict, questions: dict[str, Question]):
        """`state` é dado (features numéricas serializadas), nunca instrução."""
        body = {
            "model": self.model,
            "state": state if isinstance(state, str) else json.dumps(state, sort_keys=True),
            "questions": {k: q.model_dump() for k, q in questions.items()},
        }
        try:
            raw = await request_json(self.c, "POST", self.url, json=body, headers=self._headers,
                                     limiter=self.lim, retries=self.retries, backoff=self.backoff)
        except ApiError as e:
            raise JevError(f"falha de rede/API: {e}") from e
        return validate_answers(questions, raw)
