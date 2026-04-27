from __future__ import annotations

from dataclasses import KW_ONLY, dataclass
from pathlib import Path

from ..data import Settings
from ..helpers import journal_manager
from ..utils import common_paths
from .experiment_base_command import ExperimentBaseCommand


@dataclass
class ReadJournalCommand(ExperimentBaseCommand):
    _: KW_ONLY
    previous_entries: int | None = None

    def name(self) -> str:
        return "Read Journal"

    def process_experiment(self, settings: Settings, experiment_dir: Path) -> None:
        journal_text = journal_manager.load_journal(common_paths.journal_filepath(self.experiment_name), self.previous_entries)
        self.logger.report_message(journal_text)
        self.tracer.add_context("previous_entries_count", self.previous_entries)
        self.tracer.add_context("journal_length", len(journal_text))
