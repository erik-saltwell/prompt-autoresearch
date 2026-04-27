from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import KW_ONLY, dataclass
from datetime import datetime
from pathlib import Path

from ..data import Settings
from ..protocols import CommandProtocol, LoggingProtocol
from ..utils import Tracer, common_paths


@dataclass
class ExperimentBaseCommand(ABC, CommandProtocol):
    _: KW_ONLY
    experiment_name: str
    tracer: Tracer
    logger: LoggingProtocol

    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    def process_experiment(self, settings: Settings, experiment_dir: Path) -> None: ...

    def execute(self) -> None:
        settings: Settings = Settings.load(common_paths.settings_filepath(self.experiment_name))
        start_time: datetime = datetime.now()
        self.logger.report_message(f"Processing {self.name()} for experiment {self.experiment_name}")
        common_paths.reset_experiment_dir(self.experiment_name)
        self.process_experiment(settings, common_paths.experiment_dir(self.experiment_name))
        end_time: datetime = datetime.now()
        duration = end_time - start_time
        self.logger.report_message(f"{self.name()} completed in {duration}.")
