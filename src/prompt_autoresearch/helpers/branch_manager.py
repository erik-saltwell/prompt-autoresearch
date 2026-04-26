from __future__ import annotations

import re
from datetime import datetime
from math import ceil, log10

from ..tools import git

BRANCH_LIMIT: int = 1000


def _is_main(current_branch: str) -> bool:
    return current_branch == git.BRANCH_NAME_MAIN


def _is_correct_autoresearch_branch(experiment_name: str, current_branch: str) -> bool:
    branch_pattern = rf"{re.escape(git.BRANCH_PREFIX_AUTORESEARCH + experiment_name)}_\d{{8}}_\d+"
    return re.fullmatch(branch_pattern, current_branch) is not None


def _branch_prefix_from_date(experiment_name: str) -> str:
    sdate = datetime.now().strftime("%Y%m%d")
    return f"{git.BRANCH_PREFIX_AUTORESEARCH}{experiment_name}_{sdate}_"


def _unique_autoresearch_branchname(experiment_name: str, local_branches: list[str]) -> str:
    # This intentionally only checks local branches. Not worth complexity for this project to do otherwise.
    branch_prefix: str = _branch_prefix_from_date(experiment_name)
    max_idx_digit_length: int = ceil(log10(BRANCH_LIMIT))  # computes how many char digits in branch idx
    for idx in range(BRANCH_LIMIT):
        candidate_branch_name: str = (
            branch_prefix + f"{idx:0{max_idx_digit_length}d}"  # compute correct num of digits for BRANCH_LIMIT.
        )
        if candidate_branch_name not in local_branches:
            return candidate_branch_name
    raise RuntimeError(f"Exceeded the limit of {BRANCH_LIMIT} branches for experiment {experiment_name}")


def setup_branch_if_necessary(experiment_name: str) -> None:
    current_branch: str = git.current_branch()
    if _is_correct_autoresearch_branch(experiment_name, current_branch):
        return

    if not _is_main(current_branch):
        git.switch_to_main()

    local_branch_names: list[str] = git.local_branches()
    new_branch_name = _unique_autoresearch_branchname(experiment_name, local_branch_names)
    git.create_and_switch_to_branch(new_branch_name)
