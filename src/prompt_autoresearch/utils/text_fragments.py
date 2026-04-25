from __future__ import annotations

from enum import StrEnum
from pathlib import Path

from .common_paths import fragments_dir


class FragmentID(StrEnum):
    """Identifiers for text fragment files stored in the fragments directory."""

    NONE = "none.md"
    EVALUATION_SCORING = "evaluation_scoring.md"


def get_fragment(fragment_id: FragmentID) -> str:
    """Read and return the text content of the specified fragment file."""
    fragment_path = fragments_dir() / Path(fragment_id.value)
    with open(fragment_path, encoding="utf-8") as f:
        return f.read()
