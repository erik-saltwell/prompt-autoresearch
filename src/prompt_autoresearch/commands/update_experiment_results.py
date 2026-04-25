from __future__ import annotations

from dataclasses import KW_ONLY, dataclass
from pathlib import Path

from ..data import ExperimentResults, ExperimentResultString, JournalEntry, Settings
from ..helpers import add_journal_entry, append_results
from ..tools.git import commit_files
from ..utils import common_paths
from .experiment_base_command import ExperimentBaseCommand


@dataclass
class UpdateExperimentResultsCommand(ExperimentBaseCommand):
    _: KW_ONLY
    journal_entry: JournalEntry
    commit_changes: bool = True

    def name(self) -> str:
        return "Update Results"

    def process_session(self, settings: Settings, experiment_dir: Path) -> None:
        was_successful: bool = True if self.journal_entry.result == ExperimentResultString.KEEP else False
        experiment_results: ExperimentResults = ExperimentResults(
            self.journal_entry.commit,
            was_successful,
            self.journal_entry.experimental_change,
            self.journal_entry.total_score,
            len(self.journal_entry.low_scoring_results),
        )
        append_results(experiment_results, common_paths.results_filepath(self.experiment_name))
        add_journal_entry(self.journal_entry, common_paths.journal_filepath(self.experiment_name))
        if self.commit_changes:
            commit_files(
                [
                    common_paths.results_filepath(self.experiment_name),
                    common_paths.journal_filepath(self.experiment_name),
                ],
                f"Logging results of experiment for {self.experiment_name}",
            )
        self.logger.report_message("Journal and results log have been updated.")
