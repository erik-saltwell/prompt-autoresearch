from .completions import get_completion
from .git import (
    BRANCH_NAME_MAIN,
    BRANCH_PREFIX_AUTORESEARCH,
    commit_file,
    commit_files,
    create_and_switch_to_branch,
    current_branch,
    file_is_dirty,
    local_branches,
    revert_file,
    switch_to_main,
    tree_is_dirty,
)

__all__ = [
    "create_and_switch_to_branch",
    "file_is_dirty",
    "local_branches",
    "commit_file",
    "commit_files",
    "revert_file",
    "switch_to_main",
    "tree_is_dirty",
    "get_completion",
    "current_branch",
    "BRANCH_NAME_MAIN",
    "BRANCH_PREFIX_AUTORESEARCH",
]
