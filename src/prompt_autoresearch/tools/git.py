from __future__ import annotations

import subprocess
from collections.abc import Iterable
from pathlib import Path

from ..utils import run_process


def create_branch(branchname: str) -> None:
    """Create a new git branch, or switch to it if it already exists."""
    try:
        run_process(["git", "rev-parse", "--verify", f"refs/heads/{branchname}"], capture_output=True)
        run_process(["git", "switch", branchname])
        return
    except subprocess.CalledProcessError:
        pass

    run_process(["git", "switch", "-c", branchname])


def file_is_dirty(filepath: Path) -> bool:
    """Return whether a file has staged, unstaged, or untracked changes."""
    path = str(filepath)
    try:
        run_process(["git", "diff", "--quiet", "--", path])
        run_process(["git", "diff", "--cached", "--quiet", "--", path])
        untracked = run_process(["git", "ls-files", "--others", "--exclude-standard", "--", path], capture_output=True)
    except subprocess.CalledProcessError as error:
        if error.returncode != 1:
            raise
        return True
    return bool(untracked.stdout.strip())


def file_is_untracked(filepath: Path) -> bool:
    """Return whether a file is untracked by git."""
    path = str(filepath)
    result = run_process(["git", "ls-files", "--others", "--exclude-standard", "--", path], capture_output=True)
    return bool(result.stdout.strip())


def local_branches() -> list[str]:
    """Return all local branch names for the current git repository."""
    result = run_process(["git", "branch", "--format=%(refname:short)"], capture_output=True)
    return [branch for line in result.stdout.splitlines() if (branch := line.strip())]


def commit_files(filepaths: Iterable[Path], commit_message: str) -> str:
    """Commit current changes to the specified files if any are dirty."""
    paths = list(filepaths)
    if not any(file_is_dirty(path) for path in paths):
        return ""

    path_strings = [str(path) for path in paths]
    run_process(["git", "add", "--", *path_strings])
    run_process(["git", "commit", "-m", commit_message, "--", *path_strings])
    result = run_process(["git", "rev-parse", "HEAD"], capture_output=True)
    return result.stdout.strip()


def commit_file(filepath: Path, commit_message: str) -> str:
    """Commit current changes to only the specified file."""
    return commit_files([filepath], commit_message)


def revert_file(filepath: Path) -> None:
    """Revert staged and unstaged changes to the specified file."""
    if not file_is_dirty(filepath):
        return
    if file_is_untracked(filepath):
        filepath.unlink(missing_ok=True)
        return
    run_process(["git", "restore", "--staged", "--worktree", "--", str(filepath)])
