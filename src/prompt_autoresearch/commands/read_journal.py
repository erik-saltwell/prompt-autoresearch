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
        self.logger.report_message(f"{journal_manager.load_journal(common_paths.journal_filepath(self.experiment_name), self.previous_entries)}")
