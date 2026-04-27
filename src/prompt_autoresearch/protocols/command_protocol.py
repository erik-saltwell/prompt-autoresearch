from __future__ import annotations

from typing import Protocol


class CommandProtocol(Protocol):
    def execute(self) -> None: ...
