from __future__ import annotations

import importlib.metadata as im
from typing import Any

import pytest
from typer.testing import CliRunner

import prompt_autoresearch.console.main as console_main
from prompt_autoresearch.console.main import app

runner = CliRunner()


def _dist_name() -> str:
    """
    Best-effort: map the import package name to its installed distribution name.
    This avoids hardcoding kebab-case vs snake_case.
    """
    mapping = im.packages_distributions()
    dists = mapping.get("prompt_autoresearch") or []
    return dists[0] if dists else "prompt-autoresearch"


def test_help() -> None:
    result = runner.invoke(app, ["--help"], color=False)
    assert result.exit_code == 0
    assert "Usage" in result.output
    assert "setup-experiment" in result.output
    assert "perform-experiment" in result.output
    assert "read-journal" in result.output
    assert "update-results" in result.output


def test_version() -> None:
    dist = _dist_name()
    expected_version = im.version(dist)

    result = runner.invoke(app, ["--version"], color=False)
    assert result.exit_code == 0

    out = result.output.strip()
    assert expected_version in out
    # Optional sanity check: output is typically "name version"
    assert out.endswith(expected_version)


def test_perform_experiment_cli_delegates_to_command(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[dict[str, Any], object]] = []
    logger = object()

    class FakePerformExperimentCommand:
        def __init__(self, **kwargs: Any) -> None:
            self.kwargs = kwargs

        def execute(self, command_logger: object) -> None:
            calls.append((self.kwargs, command_logger))

    monkeypatch.setattr(console_main, "PerformExperimentCommand", FakePerformExperimentCommand)
    monkeypatch.setattr(console_main, "create_logger", lambda: logger)

    result = runner.invoke(app, ["perform-experiment", "clean_transcript", "--no-commit"], color=False)

    assert result.exit_code == 0
    assert calls == [({"experiment_name": "clean_transcript", "commit_changes": False}, logger)]


def test_update_results_cli_builds_journal_entry(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[dict[str, Any], object]] = []
    logger = object()

    class FakeUpdateExperimentResultsCommand:
        def __init__(self, **kwargs: Any) -> None:
            self.kwargs = kwargs

        def execute(self, command_logger: object) -> None:
            calls.append((self.kwargs, command_logger))

    monkeypatch.setattr(console_main, "UpdateExperimentResultsCommand", FakeUpdateExperimentResultsCommand)
    monkeypatch.setattr(console_main, "create_logger", lambda: logger)

    result = runner.invoke(
        app,
        [
            "update-results",
            "clean_transcript",
            "--branch",
            "20260425_a",
            "--commit-hash",
            "abc123",
            "--hypothesis",
            "Try stricter scoring",
            "--change",
            "Updated rubric text",
            "--total-score",
            "104.5",
            "--result",
            "keep",
            "--low-scoring-result",
            "struct_01",
            "--low-scoring-result",
            "comp_03",
            "--no-commit",
        ],
        color=False,
    )

    assert result.exit_code == 0
    assert len(calls) == 1
    kwargs, command_logger = calls[0]
    journal_entry = kwargs["journal_entry"]
    assert kwargs["experiment_name"] == "clean_transcript"
    assert kwargs["commit_changes"] is False
    assert journal_entry.branch == "20260425_a"
    assert journal_entry.commit == "abc123"
    assert journal_entry.hypothesis == "Try stricter scoring"
    assert journal_entry.experimental_change == "Updated rubric text"
    assert journal_entry.total_score == 104.5
    assert journal_entry.result == console_main.ExperimentResultString.KEEP
    assert journal_entry.low_scoring_results == ["struct_01", "comp_03"]
    assert command_logger is logger
