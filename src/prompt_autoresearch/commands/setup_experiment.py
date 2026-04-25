from __future__ import annotations

from dataclasses import KW_ONLY, dataclass
from datetime import datetime
from pathlib import Path

from ..data import Settings
from ..helpers import initialize_journal, initialize_results
from ..tools.git import commit_files, create_branch, local_branches
from ..utils import common_paths
from .experiment_base_command import ExperimentBaseCommand


def _branch_name_from_date(suffix: str) -> str:
    sdate = datetime.now().strftime("%Y%m%d")
    return f"{sdate}_{suffix}"


def _create_branch_name(current_branches: list[str]) -> str:
    letters = [chr(i) for i in range(ord("a"), ord("z") + 1)]
    for letter in letters:
        testname = _branch_name_from_date(letter)
        if testname not in current_branches:
            return testname
    raise RuntimeError("Too many branches")


@dataclass
class SetupExperimentCommand(ExperimentBaseCommand):
    _: KW_ONLY

    def name(self) -> str:
        return "Setup Experiment"

    def process_session(self, settings: Settings, experiment_dir: Path) -> None:
        common_paths.reset_experiment_dir(self.experiment_name)
        current_branches: list[str] = local_branches()
        new_branch_name: str = _create_branch_name(current_branches)
        results_path = common_paths.results_filepath(self.experiment_name)
        journal_path: Path = common_paths.journal_filepath(self.experiment_name)

        create_branch(new_branch_name)
        initialize_results(results_path)
        initialize_journal(journal_path)
        commit_files([results_path, journal_path], f"initialize experiment {new_branch_name}")
        self.logger.report_message("Experiment setup complete.")
