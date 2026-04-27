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
        results_log_path: Path = common_paths.results_filepath(self.experiment_name).resolve()
        journal_path: Path = common_paths.journal_filepath(self.experiment_name).resolve()
        prompt_path: Path = settings.paths.trial_prompt.resolve()
        self.logger.report_message(f"Results log: {results_log_path}")
        self.logger.report_message(f"Experiment journal: {journal_path}")
        self.logger.report_message(f"Trial prompt: {prompt_path}")
        self.tracer.add_context("results_log_path", results_log_path)
        self.tracer.add_context("journal_path", journal_path)
        self.tracer.add_context("prompt_path", prompt_path)
