from __future__ import annotations

from dataclasses import KW_ONLY, dataclass
from pathlib import Path

from ..data import Settings
from ..utils import common_paths
from .experiment_base_command import ExperimentBaseCommand


@dataclass
class ReportKeyFilesCommand(ExperimentBaseCommand):
    _: KW_ONLY

    def name(self) -> str:
        return "Report Key Files"

    def process_experiment(self, settings: Settings, experiment_dir: Path) -> None:
        self.logger.report_message(f"Results log: {common_paths.results_filepath(self.experiment_name).resolve()}")
        self.logger.report_message(
            f"Experiment journal: {common_paths.journal_filepath(self.experiment_name).resolve()}"
        )
        self.logger.report_message(f"Trial prompt: {settings.paths.trial_prompt.resolve()}")
