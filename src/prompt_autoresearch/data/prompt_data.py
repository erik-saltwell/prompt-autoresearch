from __future__ import annotations

from dataclasses import dataclass


@dataclass
class PromptData:
    system_prompt: str
    user_prompt: str
