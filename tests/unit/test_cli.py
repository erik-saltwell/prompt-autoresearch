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
    assert "perform-experiment" in result.output
    assert "read-journal" in result.output
    assert "report-key-files" in result.output


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

    result = runner.invoke(
        app,
        [
            "perform-experiment",
            "clean_transcript",
            "--hypothesis",
            "Try stricter scoring",
            "--change",
            "Updated rubric text",
        ],
        color=False,
    )

    assert result.exit_code == 0
    assert calls == [
        (
            {
                "experiment_name": "clean_transcript",
                "hypothesis_tested": "Try stricter scoring",
                "change_to_prompt": "Updated rubric text",
            },
            logger,
        )
    ]


def test_read_journal_cli_delegates_previous_entries(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[dict[str, Any], object]] = []
    logger = object()

    class FakeReadJournalCommand:
        def __init__(self, **kwargs: Any) -> None:
            self.kwargs = kwargs

        def execute(self, command_logger: object) -> None:
            calls.append((self.kwargs, command_logger))

    monkeypatch.setattr(console_main, "ReadJournalCommand", FakeReadJournalCommand)
    monkeypatch.setattr(console_main, "create_logger", lambda: logger)

    result = runner.invoke(app, ["read-journal", "clean_transcript", "--previous-entries", "2"], color=False)

    assert result.exit_code == 0
    assert calls == [({"experiment_name": "clean_transcript", "previous_entries": 2}, logger)]
