from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from prompt_autoresearch.commands import experiment_base_command, perform_experiment
from prompt_autoresearch.commands.perform_experiment import (
    EXPERIMENT_STATUS_CRASHED,
    EXPERIMENT_STATUS_DISCARDED,
    EXPERIMENT_STATUS_IMPROVED,
    EXPERIMENT_STATUS_PERFECT,
    EXPERIMENT_STATUS_PREFIX,
    EXPERIMENT_STATUS_UNCHANGED,
    PerformExperimentCommand,
    ScoredResults,
)
from prompt_autoresearch.data import (
    EvalTags,
    ModelEffort,
    ModelSettings,
    ModelString,
    PathSettings,
    PromptData,
    Settings,
)
from prompt_autoresearch.utils import Tracer


def _settings(max_simultaneous_evaluations: int = 2) -> Settings:
    return Settings(
        max_simultaneous_evaluations=max_simultaneous_evaluations,
        evaluations_per_input=4,
        high_score_threshold=10,
        paths=PathSettings(
            evaluation_prompt=Path("evaluation_prompt.md"),
            trial_prompt=Path("trial_prompt.md"),
            eval_rubric=Path("evaluation_rubric.json"),
            current_goal=Path("current_goal.md"),
            input_filenames=(Path("input-1.md"), Path("input-2.md"), Path("input-3.md")),
        ),
        trial_model=ModelSettings(name=ModelString.GPT_5_4, effort=ModelEffort.MEDIUM),
        eval_model=ModelSettings(name=ModelString.GPT_5_4, effort=ModelEffort.MEDIUM),
        eval_tags=EvalTags(
            prompt_output_start_tag="<output>",
            prompt_output_end_tag="</output>",
            input_start_tag="<input>",
            input_end_tag="</input>",
        ),
    )


def test_generate_all_evaluated_results_caps_simultaneous_evaluations(monkeypatch) -> None:
    active_evaluations = 0
    max_active_evaluations = 0

    def fake_build_trial_prompt(trial_prompt_path: Path, input_filepath: Path) -> PromptData:
        return PromptData(system_prompt=f"system {trial_prompt_path}", user_prompt=f"user {input_filepath}")

    async def fake_get_completion(system_prompt: str, user_prompt: str, model: ModelString, effort: ModelEffort) -> str:
        return f"{system_prompt} {user_prompt} {model} {effort}"

    async def fake_evaluate_result(trial_prompt: PromptData, trial_output: str, run_idx: int, settings: Settings) -> str:
        nonlocal active_evaluations, max_active_evaluations
        active_evaluations += 1
        max_active_evaluations = max(max_active_evaluations, active_evaluations)
        await asyncio.sleep(0.01)
        active_evaluations -= 1
        return f"evaluation-{run_idx}"

    monkeypatch.setattr(perform_experiment.prompt_builder, "build_trial_prompt", fake_build_trial_prompt)
    monkeypatch.setattr(perform_experiment.completions, "get_completion", fake_get_completion)
    monkeypatch.setattr(perform_experiment, "evaluate_result", fake_evaluate_result)

    results = asyncio.run(perform_experiment.generate_all_evaluated_results(_settings()))

    assert len(results) == 12
    assert max_active_evaluations <= 2


class _RecordingLogger:
    def __init__(self) -> None:
        self.messages: list[str] = []
        self.warnings: list[str] = []

    def report_message(self, message: str) -> None:
        self.messages.append(message)

    def report_warning(self, message: str) -> None:
        self.warnings.append(message)


def _make_command() -> PerformExperimentCommand:
    return PerformExperimentCommand(
        experiment_name="test_exp",
        hypothesis_tested="h",
        change_to_prompt="c",
        logger=_RecordingLogger(),  # type: ignore[arg-type]
        tracer=Tracer(),
    )


@pytest.mark.parametrize(
    ("total", "maximum", "previous_high", "commit_hash", "expected"),
    [
        (110.0, 110.0, 100.0, "abc123", EXPERIMENT_STATUS_PERFECT),
        (110.0, 110.0, 110.0, "abc123", EXPERIMENT_STATUS_PERFECT),  # tie at max still perfect
        (102.0, 110.0, 100.0, "abc123", EXPERIMENT_STATUS_IMPROVED),
        (99.0, 110.0, 100.0, perform_experiment.DISCARDED_HASH_INDICATOR, EXPERIMENT_STATUS_DISCARDED),
        (100.0, 110.0, 100.0, perform_experiment.DISCARDED_HASH_INDICATOR, EXPERIMENT_STATUS_DISCARDED),  # tie != improvement
        (100.0, 110.0, 100.0, None, EXPERIMENT_STATUS_UNCHANGED),  # baseline / no prompt edit
    ],
)
def test_classify_status_covers_all_outcomes(total: float, maximum: float, previous_high: float, commit_hash: str | None, expected: str) -> None:
    score_info = ScoredResults(
        dimensions_with_low_scores=[],
        total_score=total,
        maximum_possible_score=maximum,
        previous_high_score=previous_high,
    )
    assert _make_command()._classify_status(score_info, commit_hash) == expected


def test_report_status_emits_sentinel_with_totals() -> None:
    messages: list[str] = []

    class FakeLogger:
        def report_message(self, message: str) -> None:
            messages.append(message)

    cmd = _make_command()
    cmd.logger = FakeLogger()  # type: ignore[assignment]
    score_info = ScoredResults(
        dimensions_with_low_scores=[],
        total_score=102.1,
        maximum_possible_score=110.0,
        previous_high_score=100.0,
    )
    cmd.report_status(score_info, "abc123")

    assert messages == [f"{EXPERIMENT_STATUS_PREFIX} {EXPERIMENT_STATUS_IMPROVED} total=102.1 max=110.0"]


def _settings_with_prompt(tmp_path: Path) -> Settings:
    prompt_path = tmp_path / "trial_prompt.md"
    return Settings(
        max_simultaneous_evaluations=1,
        evaluations_per_input=1,
        high_score_threshold=10,
        paths=PathSettings(
            evaluation_prompt=tmp_path / "evaluation_prompt.md",
            trial_prompt=prompt_path,
            eval_rubric=tmp_path / "evaluation_rubric.json",
            current_goal=tmp_path / "current_goal.md",
            input_filenames=(tmp_path / "input.md",),
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


def test_execute_emits_status_after_completion(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    cmd = _make_command()
    logger = _RecordingLogger()
    settings = _settings_with_prompt(tmp_path)
    score_info = ScoredResults(
        dimensions_with_low_scores=[],
        total_score=102.1,
        maximum_possible_score=110.0,
        previous_high_score=100.0,
    )

    def fake_process_experiment(settings: Settings, experiment_dir: Path) -> None:
        cmd.logger.report_message("process body")
        cmd._last_score_info = score_info
        cmd._last_commit_hash = "abc123"

    monkeypatch.setattr(experiment_base_command.Settings, "load", lambda path: settings)
    monkeypatch.setattr(cmd, "process_experiment", fake_process_experiment)

    cmd.logger = logger  # type: ignore[assignment]
    cmd.execute()

    assert logger.messages[-2].startswith("Perform Experiment completed in ")
    assert logger.messages[-1] == f"{EXPERIMENT_STATUS_PREFIX} {EXPERIMENT_STATUS_IMPROVED} total=102.1 max=110.0"


def _patch_setup(monkeypatch: pytest.MonkeyPatch, cmd: PerformExperimentCommand) -> None:
    monkeypatch.setattr(cmd, "perform_necessary_setup", lambda settings: cmd.reset_counts(settings))
    monkeypatch.setattr(cmd, "report_progress", lambda: None)


def test_process_experiment_reverts_prompt_on_crash_before_commit(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    cmd = _make_command()
    cmd.logger = _RecordingLogger()  # type: ignore[assignment]
    settings = _settings_with_prompt(tmp_path)

    revert_calls: list[Path] = []
    monkeypatch.setattr(perform_experiment.git, "revert_file", lambda path: revert_calls.append(path))

    _patch_setup(monkeypatch, cmd)
    monkeypatch.setattr(
        cmd,
        "get_all_evaluation_results",
        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("boom")),
    )

    with pytest.raises(RuntimeError, match="boom"):
        cmd.process_experiment(settings, tmp_path)

    assert revert_calls == [settings.paths.trial_prompt]
    assert cmd.logger.messages[-1] == f"{EXPERIMENT_STATUS_PREFIX} {EXPERIMENT_STATUS_CRASHED}"  # type: ignore[attr-defined]


def test_process_experiment_does_not_revert_after_commit_decision(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    cmd = _make_command()
    cmd.logger = _RecordingLogger()  # type: ignore[assignment]
    settings = _settings_with_prompt(tmp_path)

    revert_calls: list[Path] = []
    monkeypatch.setattr(perform_experiment.git, "revert_file", lambda path: revert_calls.append(path))

    _patch_setup(monkeypatch, cmd)
    score_info = ScoredResults(
        dimensions_with_low_scores=[],
        total_score=102.0,
        maximum_possible_score=110.0,
        previous_high_score=100.0,
    )
    monkeypatch.setattr(cmd, "get_all_evaluation_results", lambda *a, **k: [])
    monkeypatch.setattr(cmd, "process_scores", lambda results, settings: score_info)
    monkeypatch.setattr(cmd, "commit_prompt_if_necessary", lambda score, settings: "abc123")
    monkeypatch.setattr(
        cmd,
        "update_result_logs",
        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("post-commit failure")),
    )

    with pytest.raises(RuntimeError, match="post-commit failure"):
        cmd.process_experiment(settings, tmp_path)

    assert revert_calls == []  # commit decision was already made; do not undo it
    assert cmd.logger.messages[-1] == f"{EXPERIMENT_STATUS_PREFIX} {EXPERIMENT_STATUS_CRASHED}"  # type: ignore[attr-defined]


def test_revert_failure_does_not_mask_original_exception(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    cmd = _make_command()
    cmd.logger = _RecordingLogger()  # type: ignore[assignment]
    settings = _settings_with_prompt(tmp_path)

    def failing_revert(path: Path) -> None:
        raise RuntimeError("revert failed")

    monkeypatch.setattr(perform_experiment.git, "revert_file", failing_revert)

    _patch_setup(monkeypatch, cmd)
    monkeypatch.setattr(
        cmd,
        "get_all_evaluation_results",
        lambda *args, **kwargs: (_ for _ in ()).throw(ValueError("primary")),
    )

    with pytest.raises(ValueError, match="primary"):
        cmd.process_experiment(settings, tmp_path)

    # The revert failure was swallowed and reported as a warning; the primary exception propagated.
    assert any("Failed to revert" in w for w in cmd.logger.warnings)  # type: ignore[attr-defined]
