from __future__ import annotations

from datetime import UTC, datetime

from prompt_autoresearch.data import ExperimentResultString, JournalEntry


def test_journal_entry_to_journal_string_formats_markdown_entry() -> None:
    entry = JournalEntry(
        entry_date=datetime(2026, 4, 24, 10, 19, 55, tzinfo=UTC),
        branch="autoresearch/apr24",
        commit="2ad604c",
        hypothesis="N/A - baseline measurement",
        experimental_change="None",
        total_score=100.2,
        result=ExperimentResultString.KEEP,
        low_scoring_results=[
            "`comp_01` 9.6 - recap_log collapses multiple events into vague summary statements",
            "`comp_02` 7.9 - session_log collapses distinct in-game beats",
        ],
    )

    assert entry.to_journal_string() == "\n".join(
        [
            "- **Date/time:** 2026-04-24T10:19:55+00:00",
            "- **Branch:** autoresearch/apr24",
            "- **Commit:** 2ad604c",
            "- **Hypothesis:** N/A - baseline measurement",
            "- **Change:** None",
            "- **Result:** keep",
            "- **Result summary:**",
            "  - Total score: 100.2",
            "  - Low-scoring criteria (2):",
            "    - `comp_01` 9.6 - recap_log collapses multiple events into vague summary statements",
            "    - `comp_02` 7.9 - session_log collapses distinct in-game beats",
        ]
    )


def test_journal_entry_to_journal_string_handles_no_low_scoring_results() -> None:
    entry = JournalEntry(
        entry_date=datetime(2026, 4, 24, 10, 19, 55),
        branch="autoresearch/apr24",
        commit="2ad604c",
        hypothesis="Try a clearer rubric",
        experimental_change="Updated prompt",
        total_score=110.0,
        result=ExperimentResultString.DISCARD,
    )

    assert entry.to_journal_string().splitlines()[-1] == "  - Low-scoring criteria (0):"
