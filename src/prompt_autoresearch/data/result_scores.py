from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, field

HIGHEST_COMPOSITE_SCORE_FOR_A_QUESTION: float = 10.0
HIGHEST_SCORE_FOR_A_RESPONSE: int = 3
LOWEST_SCORE_FOR_A_RESPONSE: int = 1


@dataclass
class ScoreQuestion:
    id: str
    question_text: str
    scores: list[int] = field(default_factory=list)
    counter_examples: list[str] = field(default_factory=list)

    @property
    def composite_score(self) -> float:
        if not self.scores:
            return 0.0
        score: float = sum([1 + (score**2) for score in self.scores]) / len(self.scores)
        assert score <= HIGHEST_COMPOSITE_SCORE_FOR_A_QUESTION
        assert score >= 1
        return score

    def clear_scores(self) -> None:
        self.scores.clear()
        self.counter_examples.clear()


@dataclass
class ScoreDimension:
    name: str
    description: str
    tag: str
    questions: list[ScoreQuestion]

    def score_ids(self) -> Iterator[str]:
        yield from [question.id for question in self.questions]

    def get_question(self, question_id: str) -> ScoreQuestion | None:
        return next((question for question in self.questions if question.id == question_id), None)

    def clear_scores(self) -> None:
        for question in self.questions:
            question.clear_scores()
