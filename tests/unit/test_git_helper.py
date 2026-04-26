from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from prompt_autoresearch.tools import git


def test_create_and_switch_branch_switches_to_existing_branch(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[list[str], bool]] = []

    def fake_run_process(cmd: list[str], capture_output: bool = False) -> subprocess.CompletedProcess[str]:
        calls.append((cmd, capture_output))
        return subprocess.CompletedProcess(cmd, 0)

    monkeypatch.setattr(git, "run_process", fake_run_process)

    git.create_and_switch_to_branch("existing-branch")

    assert calls == [
        (["git", "rev-parse", "--verify", "refs/heads/existing-branch"], True),
        (["git", "switch", "existing-branch"], False),
    ]


def test_create_and_swtich_branch_creates_missing_branch(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[list[str], bool]] = []

    def fake_run_process(cmd: list[str], capture_output: bool = False) -> subprocess.CompletedProcess[str]:
        calls.append((cmd, capture_output))
        if cmd[:3] == ["git", "rev-parse", "--verify"]:
            raise subprocess.CalledProcessError(1, cmd)
        return subprocess.CompletedProcess(cmd, 0)

    monkeypatch.setattr(git, "run_process", fake_run_process)

    git.create_and_switch_to_branch("new-branch")

    assert calls == [
        (["git", "rev-parse", "--verify", "refs/heads/new-branch"], True),
        (["git", "switch", "-c", "new-branch"], False),
    ]


def test_commit_file_commits_only_requested_path(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[list[str]] = []

    def fake_run_process(cmd: list[str], capture_output: bool = False) -> subprocess.CompletedProcess[str]:
        calls.append(cmd)
        if cmd == ["git", "rev-parse", "HEAD"]:
            return subprocess.CompletedProcess(cmd, 0, stdout="abc123\n")
        return subprocess.CompletedProcess(cmd, 0)

    monkeypatch.setattr(git, "run_process", fake_run_process)
    monkeypatch.setattr(git, "file_is_dirty", lambda filepath: True)

    commit_hash = git.commit_file(Path("src/example.py"), "commit message")

    assert calls == [
        ["git", "add", "--", "src/example.py"],
        ["git", "commit", "-m", "commit message", "--", "src/example.py"],
        ["git", "rev-parse", "HEAD"],
    ]
    assert commit_hash == "abc123"


def test_commit_file_returns_empty_string_when_file_is_clean(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[list[str]] = []

    def fake_run_process(cmd: list[str], capture_output: bool = False) -> subprocess.CompletedProcess[str]:
        calls.append(cmd)
        return subprocess.CompletedProcess(cmd, 0)

    monkeypatch.setattr(git, "run_process", fake_run_process)
    monkeypatch.setattr(git, "file_is_dirty", lambda filepath: False)

    assert git.commit_file(Path("src/example.py"), "commit message") == ""
    assert calls == []


def test_commit_files_commits_all_requested_paths_when_any_file_is_dirty(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[list[str]] = []
    dirty_paths = {Path("src/dirty.py")}

    def fake_run_process(cmd: list[str], capture_output: bool = False) -> subprocess.CompletedProcess[str]:
        calls.append(cmd)
        if cmd == ["git", "rev-parse", "HEAD"]:
            return subprocess.CompletedProcess(cmd, 0, stdout="abc123\n")
        return subprocess.CompletedProcess(cmd, 0)

    monkeypatch.setattr(git, "run_process", fake_run_process)
    monkeypatch.setattr(git, "file_is_dirty", lambda filepath: filepath in dirty_paths)

    commit_hash = git.commit_files([Path("src/clean.py"), Path("src/dirty.py")], "commit message")

    assert commit_hash == "abc123"
    assert calls == [
        ["git", "add", "--", "src/clean.py", "src/dirty.py"],
        ["git", "commit", "-m", "commit message", "--", "src/clean.py", "src/dirty.py"],
        ["git", "rev-parse", "HEAD"],
    ]


def test_commit_files_returns_empty_string_when_no_files_are_dirty(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[list[str]] = []

    def fake_run_process(cmd: list[str], capture_output: bool = False) -> subprocess.CompletedProcess[str]:
        calls.append(cmd)
        return subprocess.CompletedProcess(cmd, 0)

    monkeypatch.setattr(git, "run_process", fake_run_process)
    monkeypatch.setattr(git, "file_is_dirty", lambda filepath: False)

    assert git.commit_files([Path("src/clean.py"), Path("src/also_clean.py")], "commit message") == ""
    assert calls == []


def test_revert_file_restores_requested_path(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[list[str]] = []

    def fake_run_process(cmd: list[str], capture_output: bool = False) -> subprocess.CompletedProcess[str]:
        calls.append(cmd)
        if cmd[:2] == ["git", "ls-files"]:
            return subprocess.CompletedProcess(cmd, 0, stdout="")
        return subprocess.CompletedProcess(cmd, 0)

    monkeypatch.setattr(git, "run_process", fake_run_process)
    monkeypatch.setattr(git, "file_is_dirty", lambda filepath: True)

    git.revert_file(Path("src/example.py"))

    assert calls == [
        ["git", "ls-files", "--others", "--exclude-standard", "--", "src/example.py"],
        ["git", "restore", "--staged", "--worktree", "--", "src/example.py"],
    ]


def test_revert_file_deletes_untracked_path(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    filepath = tmp_path / "generated.txt"
    filepath.write_text("generated content")
    calls: list[list[str]] = []

    def fake_run_process(cmd: list[str], capture_output: bool = False) -> subprocess.CompletedProcess[str]:
        calls.append(cmd)
        if cmd[:2] == ["git", "ls-files"]:
            return subprocess.CompletedProcess(cmd, 0, stdout=f"{filepath}\n")
        return subprocess.CompletedProcess(cmd, 0)

    monkeypatch.setattr(git, "run_process", fake_run_process)
    monkeypatch.setattr(git, "file_is_dirty", lambda path: True)

    git.revert_file(filepath)

    assert not filepath.exists()
    assert calls == [["git", "ls-files", "--others", "--exclude-standard", "--", str(filepath)]]


def test_local_branches_returns_branch_names(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[list[str], bool]] = []

    def fake_run_process(cmd: list[str], capture_output: bool = False) -> subprocess.CompletedProcess[str]:
        calls.append((cmd, capture_output))
        return subprocess.CompletedProcess(cmd, 0, stdout="main\n feature/test \n\n")

    monkeypatch.setattr(git, "run_process", fake_run_process)

    branches = git.local_branches()

    assert branches == ["main", "feature/test"]
    assert calls == [(["git", "branch", "--format=%(refname:short)"], True)]


def test_current_branch_returns_active_branch(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[list[str], bool]] = []

    def fake_run_process(cmd: list[str], capture_output: bool = False) -> subprocess.CompletedProcess[str]:
        calls.append((cmd, capture_output))
        return subprocess.CompletedProcess(cmd, 0, stdout="feature/current\n")

    monkeypatch.setattr(git, "run_process", fake_run_process)

    branch = git.current_branch()

    assert branch == "feature/current"
    assert calls == [(["git", "branch", "--show-current"], True)]


def test_switch_to_main_switches_to_main_branch(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[list[str], bool]] = []

    def fake_run_process(cmd: list[str], capture_output: bool = False) -> subprocess.CompletedProcess[str]:
        calls.append((cmd, capture_output))
        return subprocess.CompletedProcess(cmd, 0)

    monkeypatch.setattr(git, "run_process", fake_run_process)

    git.switch_to_main()

    assert calls == [(["git", "switch", "main"], False)]


def test_tree_is_dirty_returns_false_for_clean_tree(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[list[str], bool]] = []

    def fake_run_process(cmd: list[str], capture_output: bool = False) -> subprocess.CompletedProcess[str]:
        calls.append((cmd, capture_output))
        if cmd[:2] == ["git", "ls-files"]:
            return subprocess.CompletedProcess(cmd, 0, stdout="")
        return subprocess.CompletedProcess(cmd, 0)

    monkeypatch.setattr(git, "run_process", fake_run_process)

    assert git.tree_is_dirty() is False
    assert calls == [
        (["git", "diff", "--quiet"], False),
        (["git", "diff", "--cached", "--quiet"], False),
        (["git", "ls-files", "--others", "--exclude-standard"], True),
    ]


def test_tree_is_dirty_returns_true_for_unstaged_changes(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[list[str], bool]] = []

    def fake_run_process(cmd: list[str], capture_output: bool = False) -> subprocess.CompletedProcess[str]:
        calls.append((cmd, capture_output))
        raise subprocess.CalledProcessError(1, cmd)

    monkeypatch.setattr(git, "run_process", fake_run_process)

    assert git.tree_is_dirty() is True
    assert calls == [(["git", "diff", "--quiet"], False)]


def test_tree_is_dirty_returns_true_for_staged_changes(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[list[str], bool]] = []

    def fake_run_process(cmd: list[str], capture_output: bool = False) -> subprocess.CompletedProcess[str]:
        calls.append((cmd, capture_output))
        if cmd == ["git", "diff", "--cached", "--quiet"]:
            raise subprocess.CalledProcessError(1, cmd)
        return subprocess.CompletedProcess(cmd, 0)

    monkeypatch.setattr(git, "run_process", fake_run_process)

    assert git.tree_is_dirty() is True
    assert calls == [
        (["git", "diff", "--quiet"], False),
        (["git", "diff", "--cached", "--quiet"], False),
    ]


def test_tree_is_dirty_returns_true_for_untracked_files(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[list[str], bool]] = []

    def fake_run_process(cmd: list[str], capture_output: bool = False) -> subprocess.CompletedProcess[str]:
        calls.append((cmd, capture_output))
        if cmd[:2] == ["git", "ls-files"]:
            return subprocess.CompletedProcess(cmd, 0, stdout="new-file.txt\n")
        return subprocess.CompletedProcess(cmd, 0)

    monkeypatch.setattr(git, "run_process", fake_run_process)

    assert git.tree_is_dirty() is True
    assert calls == [
        (["git", "diff", "--quiet"], False),
        (["git", "diff", "--cached", "--quiet"], False),
        (["git", "ls-files", "--others", "--exclude-standard"], True),
    ]


def test_tree_is_dirty_reraises_git_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    error = subprocess.CalledProcessError(128, ["git", "diff"])

    def fake_run_process(cmd: list[str], capture_output: bool = False) -> subprocess.CompletedProcess[str]:
        raise error

    monkeypatch.setattr(git, "run_process", fake_run_process)

    with pytest.raises(subprocess.CalledProcessError) as raised:
        git.tree_is_dirty()

    assert raised.value is error


def test_file_is_dirty_returns_false_for_clean_file(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[list[str]] = []

    def fake_run_process(cmd: list[str], capture_output: bool = False) -> subprocess.CompletedProcess[str]:
        calls.append(cmd)
        if cmd[:2] == ["git", "ls-files"]:
            return subprocess.CompletedProcess(cmd, 0, stdout="")
        return subprocess.CompletedProcess(cmd, 0)

    monkeypatch.setattr(git, "run_process", fake_run_process)

    assert git.file_is_dirty(Path("src/example.py")) is False
    assert calls == [
        ["git", "diff", "--quiet", "--", "src/example.py"],
        ["git", "diff", "--cached", "--quiet", "--", "src/example.py"],
        ["git", "ls-files", "--others", "--exclude-standard", "--", "src/example.py"],
    ]


def test_file_is_dirty_returns_true_for_unstaged_changes(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[list[str]] = []

    def fake_run_process(cmd: list[str], capture_output: bool = False) -> subprocess.CompletedProcess[str]:
        calls.append(cmd)
        raise subprocess.CalledProcessError(1, cmd)

    monkeypatch.setattr(git, "run_process", fake_run_process)

    assert git.file_is_dirty(Path("src/example.py")) is True
    assert calls == [["git", "diff", "--quiet", "--", "src/example.py"]]


def test_file_is_dirty_returns_true_for_staged_changes(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[list[str]] = []

    def fake_run_process(cmd: list[str], capture_output: bool = False) -> subprocess.CompletedProcess[str]:
        calls.append(cmd)
        if cmd[:3] == ["git", "diff", "--cached"]:
            raise subprocess.CalledProcessError(1, cmd)
        return subprocess.CompletedProcess(cmd, 0)

    monkeypatch.setattr(git, "run_process", fake_run_process)

    assert git.file_is_dirty(Path("src/example.py")) is True
    assert calls == [
        ["git", "diff", "--quiet", "--", "src/example.py"],
        ["git", "diff", "--cached", "--quiet", "--", "src/example.py"],
    ]


def test_file_is_dirty_returns_true_for_untracked_file(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[list[str]] = []

    def fake_run_process(cmd: list[str], capture_output: bool = False) -> subprocess.CompletedProcess[str]:
        calls.append(cmd)
        if cmd[:2] == ["git", "ls-files"]:
            return subprocess.CompletedProcess(cmd, 0, stdout="src/example.py\n")
        return subprocess.CompletedProcess(cmd, 0)

    monkeypatch.setattr(git, "run_process", fake_run_process)

    assert git.file_is_dirty(Path("src/example.py")) is True
    assert calls == [
        ["git", "diff", "--quiet", "--", "src/example.py"],
        ["git", "diff", "--cached", "--quiet", "--", "src/example.py"],
        ["git", "ls-files", "--others", "--exclude-standard", "--", "src/example.py"],
    ]


def test_file_is_dirty_reraises_git_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    error = subprocess.CalledProcessError(128, ["git", "diff"])

    def fake_run_process(cmd: list[str], capture_output: bool = False) -> subprocess.CompletedProcess[str]:
        raise error

    monkeypatch.setattr(git, "run_process", fake_run_process)

    with pytest.raises(subprocess.CalledProcessError) as raised:
        git.file_is_dirty(Path("src/example.py"))

    assert raised.value is error
