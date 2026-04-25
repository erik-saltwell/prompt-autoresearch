from __future__ import annotations

import asyncio
from collections.abc import Callable
from dataclasses import KW_ONLY, dataclass
from itertools import chain
from pathlib import Path

from ..data import (
    PromptData,
    ScoreDimension,
    Settings,
)
from ..helpers import (
    build_evaluation_prompt,
    build_trial_prompt,
    get_highest_possible_score,
    get_low_scoring_questions,
    get_total_score,
    integrate_scores_into_dimensions,
    load_previous_high_score,
    load_unscored_dimensions_from_rubric,
)
from ..tools.completions import get_completion
from ..tools.git import commit_file, revert_file
from ..utils import common_paths
from .experiment_base_command import ExperimentBaseCommand


async def evaluate_result(trial_prompt: PromptData, trial_output: str, run_idx: int, settings: Settings) -> str:
    eval_prompt: PromptData = build_evaluation_prompt(
        settings.paths.evaluation_prompt, settings.paths.eval_rubric, trial_prompt, trial_output, settings.eval_tags
    )
    eval_output: str = await get_completion(
        eval_prompt.system_prompt, eval_prompt.user_prompt, settings.eval_model.name, settings.eval_model.effort
    )

    return eval_output


async def evaluate_result_with_limit(
    trial_prompt: PromptData,
    trial_output: str,
    run_idx: int,
    settings: Settings,
    eval_semaphore: asyncio.Semaphore,
    on_eval_done: Callable[[], None] = lambda: None,
) -> str:
    async with eval_semaphore:
        result = await evaluate_result(trial_prompt, trial_output, run_idx, settings)
    on_eval_done()
    return result


async def evaluate_input(
    settings: Settings,
    input_filepath: Path,
    eval_semaphore: asyncio.Semaphore,
    on_input_done: Callable[[], None] = lambda: None,
    on_eval_done: Callable[[], None] = lambda: None,
) -> list[str]:
    results: list[str] = []
    trial_prompt: PromptData = build_trial_prompt(settings.paths.trial_prompt, input_filepath)
    trial_output: str = await get_completion(
        trial_prompt.system_prompt, trial_prompt.user_prompt, settings.trial_model.name, settings.trial_model.effort
    )
    on_input_done()
    eval_tasks = []
    for run_idx in range(settings.evaluations_per_input):
        eval_tasks.append(
            evaluate_result_with_limit(trial_prompt, trial_output, run_idx, settings, eval_semaphore, on_eval_done)
        )

    results = await asyncio.gather(*eval_tasks)
    return results


async def generate_all_evaluated_results(
    settings: Settings,
    on_input_done: Callable[[], None] = lambda: None,
    on_eval_done: Callable[[], None] = lambda: None,
) -> list[str]:
    results: list[str] = []
    input_tasks = []
    eval_semaphore = asyncio.Semaphore(settings.max_simultaneous_evaluations)
    for input_filepath in settings.paths.input_filenames:
        input_tasks.append(evaluate_input(settings, input_filepath, eval_semaphore, on_input_done, on_eval_done))
    results: list[str] = list(chain.from_iterable(await asyncio.gather(*input_tasks)))
    return results


@dataclass
class PerformExperimentCommand(ExperimentBaseCommand):
    _: KW_ONLY
    commit_changes: bool = True

    def name(self) -> str:
        return "Perform Experiment"

    def get_all_evaluation_results(
        self,
        settings: Settings,
        on_input_done: Callable[[], None] = lambda: None,
        on_eval_done: Callable[[], None] = lambda: None,
    ) -> list[str]:
        return asyncio.run(generate_all_evaluated_results(settings, on_input_done, on_eval_done))

    def process_session(self, settings: Settings, experiment_dir: Path) -> None:
        common_paths.reset_experiment_dir(self.experiment_name)

        total_inputs = len(settings.paths.input_filenames)
        total_evals = total_inputs * settings.evaluations_per_input
        completed_inputs = 0
        completed_evals = 0

        def report() -> None:
            self.logger.report_message(
                f"inputs: {completed_inputs}/{total_inputs} evals: {completed_evals}/{total_evals}"
            )

        def on_input_done() -> None:
            nonlocal completed_inputs
            completed_inputs += 1
            report()

        def on_eval_done() -> None:
            nonlocal completed_evals
            completed_evals += 1
            report()

        evaluation_results: list[str] = self.get_all_evaluation_results(settings, on_input_done, on_eval_done)
        scoring_dimensions: list[ScoreDimension] = load_unscored_dimensions_from_rubric(settings.paths.eval_rubric)
        for evaluation_result in evaluation_results:
            integrate_scores_into_dimensions(evaluation_result, scoring_dimensions, self.logger)
        previous_high_score: float = load_previous_high_score(common_paths.results_filepath(self.experiment_name))
        current_total_score: float = get_total_score(scoring_dimensions)
        maximum_possible_total_score: float = get_highest_possible_score(scoring_dimensions)
        self.logger.report_message(
            f"Experiment Result: {current_total_score} of {maximum_possible_total_score} possible."
        )
        if self.commit_changes:
            if current_total_score > previous_high_score:
                commit_file(
                    settings.paths.trial_prompt,
                    f"experiment {self.experiment_name} new total score {current_total_score}",
                )
                self.logger.report_message(
                    f"New high score.  Prior high score was {previous_high_score}. Changes have been committed to git."
                )
            else:
                revert_file(settings.paths.trial_prompt)
                self.logger.report_message(
                    f"Results are not an improvement over prior high score of {previous_high_score}. Changes reverted."
                )
        self.logger.report_message("Low scoring tests:")
        for low_dimension in get_low_scoring_questions(scoring_dimensions, settings.high_score_threshold):
            self.logger.report_message(f"{low_dimension.name} - {low_dimension.description}")
            for question in low_dimension.questions:
                self.logger.report_message(
                    f"  ID:{question.id} Score:{question.composite_score:.1f} criteria:{question.question_text}"
                )
