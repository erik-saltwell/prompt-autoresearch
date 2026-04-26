from __future__ import annotations

from pathlib import Path

import pytest

from prompt_autoresearch.data import JournalEntry
from prompt_autoresearch.helpers import journal_manager


def _entry(entry_number: int) -> str:
    return "\n".join(
        [
            f"- **Date/time:** 2026-04-2{entry_number}T10:19:55",
            f"- **Branch:** branch-{entry_number}",
            f"- **Commit:** commit-{entry_number}",
            f"- **Hypothesis:** hypothesis-{entry_number}",
            f"- **Change:** change-{entry_number}",
            "- **Result:** keep",
            "- **Result summary:**",
            "  - Total score: 100.0",
            "  - Low-scoring criteria (0):",
        ]
    )


def _journal_text(*entry_numbers: int) -> str:
    sep = JournalEntry.ENTRY_SEPARATOR
    return "".join(f"{sep}{_entry(n)}\n" for n in entry_numbers)


def test_load_journal_limits_to_most_recent_entries(tmp_path: Path) -> None:
    journal_path = tmp_path / "experiment_journal.md"
    journal_path.write_text(_journal_text(1, 2, 3))

    journal = journal_manager.load_journal(journal_path, previous_entries=2)

    assert "branch-1" not in journal
    assert "branch-2" in journal
    assert "branch-3" in journal


def test_load_journal_returns_all_entries_by_default(tmp_path: Path) -> None:
    journal_path = tmp_path / "experiment_journal.md"
    journal_path.write_text(_journal_text(1, 2))

    assert journal_manager.load_journal(journal_path) == journal_path.read_text()


def test_load_journal_rejects_negative_previous_entries(tmp_path: Path) -> None:
    journal_path = tmp_path / "experiment_journal.md"
    journal_path.write_text("")

    with pytest.raises(ValueError, match="previous_entries"):
        journal_manager.load_journal(journal_path, previous_entries=-1)
