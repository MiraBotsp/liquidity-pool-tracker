"""Jev falso: devolve respostas no mesmo formato da API, com probabilidades plausíveis.

`corrupt=True` produz respostas inválidas para testar o descarte.
"""
from __future__ import annotations

import random

from ..jev import ChoiceQ, NoulQ, Question, ScoreQ, validate_answers


class MockJev:
    def __init__(self, seed: int = 11, corrupt: bool = False) -> None:
        self.rng = random.Random(seed)
        self.corrupt = corrupt
        self.calls = 0

    def _raw(self, questions: dict[str, Question]) -> dict:
        r, answers = self.rng, {}
        for name, q in questions.items():
            if isinstance(q, NoulQ):
                answers[name] = {"type": "noul", "noul": round(r.random(), 3)}
            elif isinstance(q, ChoiceQ):
                w = [r.random() + 0.05 for _ in q.criteria]
                t = sum(w)
                probs = {k: round(x / t, 4) for k, x in zip(q.criteria, w)}
                answers[name] = {"type": "choice", "choice": max(probs, key=probs.get),
                                 "probabilities": probs}
            elif isinstance(q, ScoreQ):
                answers[name] = {"type": "score", "score": round(r.uniform(0, len(q.criteria) - 1), 3)}
        if self.corrupt:
            victim = next(iter(answers))
            answers[victim] = {"type": "noul", "noul": 1.7}
        return {"answers": answers}

    async def decide(self, state, questions: dict[str, Question]):
        self.calls += 1
        return validate_answers(questions, self._raw(questions))
