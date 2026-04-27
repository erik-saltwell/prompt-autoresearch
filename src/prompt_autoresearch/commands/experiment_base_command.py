from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import KW_ONLY, dataclass
from pathlib import Path
from time import perf_counter

import typer

from ..data import Settings
from ..protocols import CommandProtocol, LoggingProtocol
from ..utils import Tracer, common_paths, duration_from_perfcounters


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

    @property
    def safe_name(self) -> str:
        return self.name().replace(" ", "_")

    def execute(self) -> None:
        settings: Settings = Settings.load(common_paths.settings_filepath(self.experiment_name))
        start_time: float = perf_counter()
        self.logger.report_message(f"Processing {self.name()} for experiment {self.experiment_name}")
        common_paths.reset_experiment_dir(self.experiment_name)

        try:
            self.process_experiment(settings, common_paths.experiment_dir(self.experiment_name))
            self.tracer.add_context("success", "True")
            end_time: float = perf_counter()
            self.tracer.add_context("duration", (duration_from_perfcounters(start_time, end_time)))
            self.tracer.log(self.safe_name)
            self.logger.report_message(f"{self.name()} completed in {duration_from_perfcounters(start_time, end_time)} seconds.")
        except Exception as exc:
            self.tracer.add_context("success", "False")
            self.logger.report_exception(f"Error processing {self.name()}", exc)
            self.tracer.log_exception(exc, self.safe_name)
            raise typer.Exit(code=1) from exc
