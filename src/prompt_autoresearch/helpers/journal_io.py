from __future__ import annotations

from pathlib import Path

from ..data import JournalEntry


def initialize_journal(filepath: Path) -> None:
    if not filepath.exists():
        filepath.write_text("")


def load_journal(filepath: Path) -> str:
    return filepath.read_text()


def add_journal_entry(entry: JournalEntry, filepath: Path) -> None:
    with filepath.open("a") as file:
        file.write(f"\n{entry.to_journal_string()}\n\n")
