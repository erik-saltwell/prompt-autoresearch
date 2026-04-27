from __future__ import annotations

import json
from pathlib import Path

import pytest

from prompt_autoresearch.commands.init_agent import (
    AGENT_FILENAME,
    SETTINGS_FILENAME,
    SLASH_COMMAND_FILENAME,
    InitAgentCommand,
)
from prompt_autoresearch.data import (
    EvalTags,
    ModelEffort,
    ModelSettings,
    ModelString,
    PathSettings,
    Settings,
)
from prompt_autoresearch.utils import Tracer


class _RecordingLogger:
    def __init__(self) -> None:
        self.messages: list[str] = []

    def report_message(self, message: str) -> None:
        self.messages.append(message)


def _settings_for(experiment_dir: Path, trial_prompt_relpath: str = "trial_prompt.md") -> Settings:
    return Settings(
        max_simultaneous_evaluations=1,
        evaluations_per_input=1,
        high_score_threshold=10,
        paths=PathSettings(
            evaluation_prompt=experiment_dir / "evaluation_prompt.md",
            trial_prompt=experiment_dir / trial_prompt_relpath,
            eval_rubric=experiment_dir / "evaluation_rubric.json",
            current_goal=experiment_dir / "current_goal.md",
            input_filenames=(experiment_dir / "input.md",),
        ),
        trial_model=ModelSettings(name=ModelString.GPT_5_4, effort=ModelEffort.MEDIUM),
        eval_model=ModelSettings(name=ModelString.GPT_5_4, effort=ModelEffort.MEDIUM),
        eval_tags=EvalTags(
            prompt_output_start_tag="<o>",
            prompt_output_end_tag="</o>",
            input_start_tag="<i>",
            input_end_tag="</i>",
        ),
    )


def _make_command(experiment_name: str = "myexp", force: bool = False) -> InitAgentCommand:
    return InitAgentCommand(experiment_name=experiment_name, force=force, logger=_RecordingLogger(), tracer=Tracer())  # type: ignore[arg-type]


def test_init_agent_writes_three_files(tmp_path: Path) -> None:
    cmd = _make_command()

    cmd.process_experiment(_settings_for(tmp_path), tmp_path)

    assert (tmp_path / ".claude" / "agents" / AGENT_FILENAME).exists()
    assert (tmp_path / ".claude" / "commands" / SLASH_COMMAND_FILENAME).exists()
    assert (tmp_path / ".claude" / SETTINGS_FILENAME).exists()


def test_init_agent_settings_json_has_correct_permissions(tmp_path: Path) -> None:
    cmd = _make_command()
    cmd.process_experiment(_settings_for(tmp_path), tmp_path)

    settings_path = tmp_path / ".claude" / SETTINGS_FILENAME
    payload = json.loads(settings_path.read_text())
    allow = payload["permissions"]["allow"]
    assert "Read(./**)" in allow
    assert "Edit(./trial_prompt.md)" in allow
    assert "Bash(uv run prompt-autoresearch:*)" in allow


def test_init_agent_uses_relative_trial_prompt_in_templates(tmp_path: Path) -> None:
    nested = "prompts/main.md"
    (tmp_path / "prompts").mkdir()
    cmd = _make_command()
    cmd.process_experiment(_settings_for(tmp_path, trial_prompt_relpath=nested), tmp_path)

    settings_payload = json.loads((tmp_path / ".claude" / SETTINGS_FILENAME).read_text())
    assert f"Edit(./{nested})" in settings_payload["permissions"]["allow"]

    agent_body = (tmp_path / ".claude" / "agents" / AGENT_FILENAME).read_text()
    assert nested in agent_body


def test_init_agent_agent_file_includes_experiment_name(tmp_path: Path) -> None:
    cmd = _make_command("my_unique_experiment")
    cmd.process_experiment(_settings_for(tmp_path), tmp_path)

    agent_body = (tmp_path / ".claude" / "agents" / AGENT_FILENAME).read_text()
    assert "my_unique_experiment" in agent_body
    assert agent_body.startswith("---\nname: auto-researcher\n")


def test_init_agent_refuses_to_overwrite_without_force(tmp_path: Path) -> None:
    cmd = _make_command()
    cmd.process_experiment(_settings_for(tmp_path), tmp_path)

    cmd2 = _make_command(force=False)
    with pytest.raises(FileExistsError, match="--force"):
        cmd2.process_experiment(_settings_for(tmp_path), tmp_path)


def test_init_agent_overwrites_with_force(tmp_path: Path) -> None:
    cmd = _make_command()
    cmd.process_experiment(_settings_for(tmp_path), tmp_path)

    agent_path = tmp_path / ".claude" / "agents" / AGENT_FILENAME
    agent_path.write_text("STALE")

    cmd2 = _make_command(force=True)
    cmd2.process_experiment(_settings_for(tmp_path), tmp_path)

    assert agent_path.read_text() != "STALE"


def test_init_agent_rejects_trial_prompt_outside_experiment_dir(tmp_path: Path) -> None:
    other_dir = tmp_path / "other"
    other_dir.mkdir()
    experiment_dir = tmp_path / "exp"
    experiment_dir.mkdir()

    settings = Settings(
        max_simultaneous_evaluations=1,
        evaluations_per_input=1,
        high_score_threshold=10,
        paths=PathSettings(
            evaluation_prompt=experiment_dir / "evaluation_prompt.md",
            trial_prompt=other_dir / "trial_prompt.md",
            eval_rubric=experiment_dir / "evaluation_rubric.json",
            current_goal=experiment_dir / "current_goal.md",
            input_filenames=(experiment_dir / "input.md",),
        ),
        trial_model=ModelSettings(name=ModelString.GPT_5_4, effort=ModelEffort.MEDIUM),
        eval_model=ModelSettings(name=ModelString.GPT_5_4, effort=ModelEffort.MEDIUM),
        eval_tags=EvalTags(
            prompt_output_start_tag="<o>",
            prompt_output_end_tag="</o>",
            input_start_tag="<i>",
            input_end_tag="</i>",
        ),
    )

    cmd = _make_command()
    with pytest.raises(ValueError, match="not inside experiment dir"):
        cmd.process_experiment(settings, experiment_dir)
