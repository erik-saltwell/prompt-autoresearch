from __future__ import annotations

import asyncio
from pathlib import Path

from prompt_autoresearch.commands import perform_experiment
from prompt_autoresearch.data import (
    EvalTags,
    ModelEffort,
    ModelSettings,
    ModelString,
    PathSettings,
    PromptData,
    Settings,
)


def _settings(max_simultaneous_evaluations: int = 2) -> Settings:
    return Settings(
        max_simultaneous_evaluations=max_simultaneous_evaluations,
        evaluations_per_input=4,
        high_score_threshold=10,
        paths=PathSettings(
            evaluation_prompt=Path("evaluation_prompt.md"),
            trial_prompt=Path("trial_prompt.md"),
            eval_rubric=Path("evaluation_rubric.json"),
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
