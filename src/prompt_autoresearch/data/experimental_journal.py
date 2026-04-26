from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import ClassVar

from .experiment_result_string import ExperimentResultString


@dataclass
class JournalEntry:
    ENTRY_SEPARATOR: ClassVar[str] = "\n---new experiment---\n"

    entry_date: datetime
    branch: str
    commit: str
    hypothesis: str
    experimental_change: str
    total_score: float
    result: ExperimentResultString
    low_scoring_results: list[str] = field(default_factory=list)

    def to_journal_string(self) -> str:
        lines = [
            f"- **Date/time:** {self.entry_date.isoformat()}",
            f"- **Branch:** {self.branch}",
            f"- **Commit:** {self.commit}",
            f"- **Hypothesis:** {self.hypothesis}",
            f"- **Change:** {self.experimental_change}",
            f"- **Result:** {self.result}",
            "- **Result summary:**",
            f"  - Total score: {self.total_score}",
            f"  - Low-scoring criteria ({len(self.low_scoring_results)}):",
        ]
        lines.extend(f"    - {result}" for result in self.low_scoring_results)
        return "\n".join(lines)
