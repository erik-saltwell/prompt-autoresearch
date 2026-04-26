from __future__ import annotations

from pathlib import Path

from ..data import JournalEntry


def setup_journal_if_necessary(filepath: Path) -> None:
    if not filepath.exists():
        filepath.write_text("")


def load_journal(filepath: Path, previous_entries: int | None = None) -> str:
    journal = filepath.read_text()
    if previous_entries is None:
        return journal
    if previous_entries < 0:
        raise ValueError("previous_entries must be greater than or equal to 0")
    if previous_entries == 0:
        return ""

    # Split on the separator; parts[0] is anything before the first entry, parts[1:] are entries.
    parts = journal.split(JournalEntry.ENTRY_SEPARATOR)
    entries = parts[1:]
    if len(entries) <= previous_entries:
        return journal
    selected = entries[-previous_entries:]
    return JournalEntry.ENTRY_SEPARATOR + JournalEntry.ENTRY_SEPARATOR.join(selected)


def add_journal_entry(entry: JournalEntry, filepath: Path) -> None:
    with filepath.open("a") as file:
        file.write(f"{JournalEntry.ENTRY_SEPARATOR}{entry.to_journal_string()}\n")
