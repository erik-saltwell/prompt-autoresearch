from __future__ import annotations

from pathlib import Path

import pytest

from prompt_autoresearch.utils import common_paths


def _make_experiment_dir(root: Path, name: str) -> Path:
    exp_dir = root / "experiments" / name
    exp_dir.mkdir(parents=True)
    (exp_dir / common_paths.KnownPathnames.SETTINGS).write_text("paths: {}\n")
    return exp_dir


def test_resolve_experiment_name_returns_provided_when_set(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    assert common_paths.resolve_experiment_name("explicit") == "explicit"


def test_resolve_experiment_name_uses_cwd_when_inside_experiment_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    exp_dir = _make_experiment_dir(tmp_path, "session_summarize")
    monkeypatch.chdir(exp_dir)
    assert common_paths.resolve_experiment_name(None) == "session_summarize"


def test_resolve_experiment_name_raises_when_no_settings_in_cwd(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    with pytest.raises(ValueError, match="No experiment name provided"):
        common_paths.resolve_experiment_name(None)


def test_experiment_dir_returns_cwd_when_inside_matching_experiment(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    exp_dir = _make_experiment_dir(tmp_path, "myexp")
    monkeypatch.chdir(exp_dir)
    assert common_paths.experiment_dir("myexp") == exp_dir


def test_experiment_dir_falls_back_to_experiments_subdir_from_project_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    exp_dir = _make_experiment_dir(tmp_path, "myexp")
    monkeypatch.chdir(tmp_path)
    assert common_paths.experiment_dir("myexp") == exp_dir
