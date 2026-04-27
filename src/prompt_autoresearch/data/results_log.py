from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import datetime

from ..utils import datetime_format, parse_datetime
from .experiment_result_string import ExperimentResultString


def _now() -> datetime:
    return datetime.now().replace(microsecond=0)


@dataclass
class ExperimentResults:
    checkin_hash: str
    was_successful: bool
    description: str
    total_score: float
    low_scoring_tests: int
    experiment_datetime: datetime = field(default_factory=_now)

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
        experiment_datetime, total_score, low_scoring_tests, result, description, checkin_hash = line.rstrip("\n").split("\t")
        return cls(
            checkin_hash=checkin_hash,
            was_successful=result == ExperimentResultString.KEEP,
            description=description,
            total_score=float(total_score),
            low_scoring_tests=int(low_scoring_tests),
            experiment_datetime=parse_datetime(experiment_datetime),
        )

    def to_fields(self) -> list[str]:
        return [
            datetime_format(self.experiment_datetime),
            str(self.total_score),
            str(self.low_scoring_tests),
            ExperimentResultString.KEEP.value if self.was_successful else ExperimentResultString.DISCARD.value,
            self.description,
            self.checkin_hash,
        ]
