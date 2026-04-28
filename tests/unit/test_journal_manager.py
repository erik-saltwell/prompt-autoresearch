from __future__ import annotations

from pathlib import Path

import pytest

from prompt_autoresearch.data import ExperimentResultString, JournalEntry
from prompt_autoresearch.helpers import journal_manager


def _entry(entry_number: int, result: ExperimentResultString = ExperimentResultString.KEEP) -> str:
    return "\n".join(
        [
            f"- **Date/time:** 2026-04-2{entry_number}T10:19:55",
            f"- **Branch:** branch-{entry_number}",
            f"- **Commit:** commit-{entry_number}",
            f"- **Hypothesis:** hypothesis-{entry_number}",
            f"- **Change:** change-{entry_number}",
            f"- **Result:** {result}",
            "- **Result summary:**",
            "  - Total score: 100.0",
            "  - Low-scoring criteria (0):",
        ]
    )


def _journal_text(*entries: tuple[int, ExperimentResultString] | int) -> str:
    sep = JournalEntry.ENTRY_SEPARATOR
    return "".join(f"{sep}{_entry(*entry) if isinstance(entry, tuple) else _entry(entry)}\n" for entry in entries)


def test_load_journal_limits_to_most_recent_entries(tmp_path: Path) -> None:
    journal_path = tmp_path / "experiment_journal.md"
    journal_path.write_text(_journal_text(1, 2, 3))

    journal = journal_manager.load_journal(journal_path, previous_entries=2)

    assert "branch-1" not in journal
    assert "branch-2" in journal
    assert "branch-3" in journal


def test_load_journal_appends_latest_keep_when_recent_entries_have_no_keeps(tmp_path: Path) -> None:
    journal_path = tmp_path / "experiment_journal.md"
    journal_path.write_text(
        _journal_text(
            (1, ExperimentResultString.KEEP),
            (2, ExperimentResultString.DISCARD),
            (3, ExperimentResultString.DISCARD),
            (4, ExperimentResultString.DISCARD),
        )
    )

    journal = journal_manager.load_journal(journal_path, previous_entries=2)

    assert "branch-1" in journal
    assert "branch-2" not in journal
    assert "branch-3" in journal
    assert "branch-4" in journal
    assert journal.endswith(_entry(1) + "\n")


def test_load_journal_does_not_append_latest_keep_when_recent_entries_include_keep(tmp_path: Path) -> None:
    journal_path = tmp_path / "experiment_journal.md"
    journal_path.write_text(
        _journal_text(
            (1, ExperimentResultString.KEEP),
            (2, ExperimentResultString.DISCARD),
            (3, ExperimentResultString.KEEP),
            (4, ExperimentResultString.DISCARD),
        )
    )

    journal = journal_manager.load_journal(journal_path, previous_entries=2)

    assert "branch-1" not in journal
    assert "branch-2" not in journal
    assert "branch-3" in journal
    assert "branch-4" in journal


def test_load_journal_with_zero_previous_entries_returns_latest_keep(tmp_path: Path) -> None:
    journal_path = tmp_path / "experiment_journal.md"
    journal_path.write_text(
        _journal_text(
            (1, ExperimentResultString.KEEP),
            (2, ExperimentResultString.DISCARD),
            (3, ExperimentResultString.KEEP),
            (4, ExperimentResultString.DISCARD),
        )
    )

    journal = journal_manager.load_journal(journal_path, previous_entries=0)

    assert "branch-1" not in journal
    assert "branch-2" not in journal
    assert "branch-3" in journal
    assert "branch-4" not in journal


def test_load_journal_with_no_keeps_does_not_append_fallback(tmp_path: Path) -> None:
    journal_path = tmp_path / "experiment_journal.md"
    journal_path.write_text(
        _journal_text(
            (1, ExperimentResultString.DISCARD),
            (2, ExperimentResultString.DISCARD),
            (3, ExperimentResultString.DISCARD),
        )
    )

    journal = journal_manager.load_journal(journal_path, previous_entries=2)

    assert "branch-1" not in journal
    assert "branch-2" in journal
    assert "branch-3" in journal
    assert "keep" not in journal


def test_load_journal_returns_all_entries_by_default(tmp_path: Path) -> None:
    journal_path = tmp_path / "experiment_journal.md"
    journal_path.write_text(_journal_text(1, 2))

    assert journal_manager.load_journal(journal_path) == journal_path.read_text()


def test_load_journal_rejects_negative_previous_entries(tmp_path: Path) -> None:
    journal_path = tmp_path / "experiment_journal.md"
    journal_path.write_text("")

    with pytest.raises(ValueError, match="previous_entries"):
        journal_manager.load_journal(journal_path, previous_entries=-1)
