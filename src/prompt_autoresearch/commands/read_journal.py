from __future__ import annotations

from dataclasses import KW_ONLY, dataclass
from pathlib import Path

from ..data import Settings
from ..helpers import load_journal
from ..utils import common_paths
from .experiment_base_command import ExperimentBaseCommand


@dataclass
class ReadJournalCommand(ExperimentBaseCommand):
    _: KW_ONLY

    def name(self) -> str:
        return "Read Journal"

    def process_session(self, settings: Settings, experiment_dir: Path) -> None:
        self.logger.report_message(f"{load_journal(common_paths.journal_filepath(self.experiment_name))}")
