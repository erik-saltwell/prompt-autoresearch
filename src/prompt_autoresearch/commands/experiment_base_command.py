from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import KW_ONLY, dataclass, field
from pathlib import Path

from ..data import Settings
from ..protocols import CommandProtocol, LoggingProtocol, NullLogger
from ..utils import common_paths


@dataclass
class ExperimentBaseCommand(ABC, CommandProtocol):
    _: KW_ONLY
    experiment_name: str
    logger: LoggingProtocol = field(default_factory=NullLogger)

    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    def process_session(self, settings: Settings, experiment_dir: Path) -> None: ...

    def execute(self, logger: LoggingProtocol) -> None:
        self.logger: LoggingProtocol = logger
        settings: Settings = Settings.load(common_paths.settings_filepath(self.experiment_name))
        self.process_session(settings, common_paths.experiment_dir(self.experiment_name))
