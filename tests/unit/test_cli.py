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
    assert "init-agent" in result.output


def test_init_agent_cli_delegates_to_command(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[dict[str, Any]] = []
    logger = object()
    tracer = object()

    class FakeInitAgentCommand:
        def __init__(self, **kwargs: Any) -> None:
            self.kwargs = kwargs

        def execute(self) -> None:
            calls.append(self.kwargs)

    monkeypatch.setattr(console_main, "InitAgentCommand", FakeInitAgentCommand)
    monkeypatch.setattr(console_main, "create_logger", lambda experiment_name: (logger, tracer))

    result = runner.invoke(app, ["init-agent", "session_summarize", "--force"], color=False)

    assert result.exit_code == 0, result.output
    assert calls == [{"experiment_name": "session_summarize", "force": True, "logger": logger, "tracer": tracer}]


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
    calls: list[dict[str, Any]] = []
    logger = object()
    tracer = object()

    class FakePerformExperimentCommand:
        def __init__(self, **kwargs: Any) -> None:
            self.kwargs = kwargs

        def execute(self) -> None:
            calls.append(self.kwargs)

    monkeypatch.setattr(console_main, "PerformExperimentCommand", FakePerformExperimentCommand)
    monkeypatch.setattr(console_main, "create_logger", lambda experiment_name: (logger, tracer))

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
        {
            "experiment_name": "clean_transcript",
            "hypothesis_tested": "Try stricter scoring",
            "change_to_prompt": "Updated rubric text",
            "logger": logger,
            "tracer": tracer,
        }
    ]


def test_perform_experiment_cli_resolves_name_from_cwd(monkeypatch: pytest.MonkeyPatch, tmp_path: pytest.TempPathFactory) -> None:
    calls: list[dict[str, Any]] = []
    logger = object()
    tracer = object()

    class FakePerformExperimentCommand:
        def __init__(self, **kwargs: Any) -> None:
            self.kwargs = kwargs

        def execute(self) -> None:
            calls.append(self.kwargs)

    monkeypatch.setattr(console_main, "PerformExperimentCommand", FakePerformExperimentCommand)
    monkeypatch.setattr(console_main, "create_logger", lambda experiment_name: (logger, tracer))

    exp_dir = tmp_path / "experiments" / "from_cwd"  # type: ignore[operator]
    exp_dir.mkdir(parents=True)
    (exp_dir / "settings.yaml").write_text("paths: {}\n")
    monkeypatch.chdir(exp_dir)

    result = runner.invoke(
        app,
        ["perform-experiment", "--hypothesis", "h", "--change", "c"],
        color=False,
    )

    assert result.exit_code == 0, result.output
    assert calls == [{"experiment_name": "from_cwd", "hypothesis_tested": "h", "change_to_prompt": "c", "logger": logger, "tracer": tracer}]


def test_perform_experiment_cli_errors_when_no_name_and_no_settings_in_cwd(monkeypatch: pytest.MonkeyPatch, tmp_path: pytest.TempPathFactory) -> None:
    monkeypatch.setattr(console_main, "PerformExperimentCommand", lambda **kwargs: None)
    monkeypatch.chdir(tmp_path)  # type: ignore[arg-type]

    result = runner.invoke(
        app,
        ["perform-experiment", "--hypothesis", "h", "--change", "c"],
        color=False,
    )

    assert result.exit_code != 0
    assert "experiment" in result.output.lower()


def test_read_journal_cli_delegates_previous_entries(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[dict[str, Any]] = []
    logger = object()
    tracer = object()

    class FakeReadJournalCommand:
        def __init__(self, **kwargs: Any) -> None:
            self.kwargs = kwargs

        def execute(self) -> None:
            calls.append(self.kwargs)

    monkeypatch.setattr(console_main, "ReadJournalCommand", FakeReadJournalCommand)
    monkeypatch.setattr(console_main, "create_logger", lambda experiment_name: (logger, tracer))

    result = runner.invoke(app, ["read-journal", "clean_transcript", "--previous-entries", "2"], color=False)

    assert result.exit_code == 0
    assert calls == [{"experiment_name": "clean_transcript", "previous_entries": 2, "logger": logger, "tracer": tracer}]
