from __future__ import annotations

from pathlib import Path

from ..data import ExperimentResultString, JournalEntry


def setup_journal_if_necessary(filepath: Path) -> None:
    if not filepath.exists():
        filepath.write_text("")


def _format_entries(entries: list[str]) -> str:
    if not entries:
        return ""
    return JournalEntry.ENTRY_SEPARATOR + JournalEntry.ENTRY_SEPARATOR.join(entries)


def _is_keep(entry: str) -> bool:
    keep_line = f"- **Result:** {ExperimentResultString.KEEP}"
    return any(line.strip() == keep_line for line in entry.splitlines())


def _has_keep(entries: list[str]) -> bool:
    return any(_is_keep(entry) for entry in entries)


def _latest_keep(entries: list[str]) -> str | None:
    return next((entry for entry in reversed(entries) if _is_keep(entry)), None)


def load_journal(filepath: Path, previous_entries: int | None = None) -> str:
    if not filepath.exists():
        return "JOURNAL EMPTY"
    journal = filepath.read_text()
    if previous_entries is None:
        return journal
    if previous_entries < 0:
        raise ValueError("previous_entries must be greater than or equal to 0")

    # Split on the separator; parts[0] is anything before the first entry, parts[1:] are entries.
    parts = journal.split(JournalEntry.ENTRY_SEPARATOR)
    entries = parts[1:]
    selected = entries[-previous_entries:] if previous_entries > 0 else []
    if previous_entries > 0 and len(entries) <= previous_entries:
        return _format_entries(selected)
    if not _has_keep(selected):
        latest_keep = _latest_keep(entries)
        if latest_keep is not None:
            selected = [*selected, latest_keep]

    if not selected:
        return ""
    return JournalEntry.ENTRY_SEPARATOR + JournalEntry.ENTRY_SEPARATOR.join(selected)


def add_journal_entry(entry: JournalEntry, filepath: Path) -> None:
    with filepath.open("a") as file:
        file.write(f"{JournalEntry.ENTRY_SEPARATOR}{entry.to_journal_string()}\n")
