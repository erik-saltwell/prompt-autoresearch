from __future__ import annotations

from enum import StrEnum
from pathlib import Path
from typing import Any

from jinja2 import StrictUndefined, Template

from .common_paths import fragments_dir


class FragmentID(StrEnum):
    """Identifiers for text fragment files stored in the fragments directory."""

    NONE = "none.md"
    EVALUATION_SCORING = "evaluation_scoring.md"
    AUTO_RESEARCHER_AGENT = "auto_researcher_agent.md.j2"
    IMPROVE_PROMPT_COMMAND = "improve_prompt_command.md.j2"
    CLAUDE_SETTINGS = "claude_settings.json.j2"


def get_fragment(fragment_id: FragmentID) -> str:
    """Read and return the text content of the specified fragment file."""
    fragment_path = fragments_dir() / Path(fragment_id.value)
    with open(fragment_path, encoding="utf-8") as f:
        return f.read()


def render_fragment(fragment_id: FragmentID, **variables: Any) -> str:
    """Load a fragment as a Jinja template and render it with the given variables."""
    template_text = get_fragment(fragment_id)
    template = Template(template_text, undefined=StrictUndefined, keep_trailing_newline=True)
    return template.render(**variables)
