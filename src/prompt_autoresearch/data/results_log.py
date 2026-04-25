from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import datetime

from .experiment_result_string import ExperimentResultString


@dataclass
class ExperimentResults:
    checkin_hash: str
    was_successful: bool
    description: str
    total_score: float
    low_scoring_tests: int
    created_at: datetime = field(default_factory=datetime.now)

    @classmethod
    def fields(cls) -> list[str]:
        results: list[str] = ["datetime", "total_score", "low_score_count", "result", "description", "commit_hash"]
        return results

    @classmethod
    def convert_results_to_string(cls, result_set: Iterable[ExperimentResults]) -> str:
        lines: list[str] = []
        lines.append("\t".join(cls.fields()))
        lines.extend(["\t".join(result.to_fields()) for result in result_set])
        return "\n".join(lines)

    @classmethod
    def from_tsv_line(cls, line: str) -> ExperimentResults:
        created_at, total_score, low_scoring_tests, result, description, checkin_hash = line.rstrip("\n").split("\t")
        return cls(
            checkin_hash=checkin_hash,
            was_successful=result == ExperimentResultString.KEEP,
            description=description,
            total_score=float(total_score),
            low_scoring_tests=int(low_scoring_tests),
            created_at=datetime.fromisoformat(created_at),
        )

    def to_fields(self) -> list[str]:
        return [
            self.created_at.isoformat(),
            str(self.total_score),
            str(self.low_scoring_tests),
            ExperimentResultString.KEEP.value if self.was_successful else ExperimentResultString.DISCARD.value,
            self.description,
            self.checkin_hash,
        ]
