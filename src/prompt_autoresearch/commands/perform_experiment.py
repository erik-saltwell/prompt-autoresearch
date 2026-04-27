from __future__ import annotations

import asyncio
from collections.abc import Callable
from dataclasses import KW_ONLY, dataclass, field
from datetime import datetime
from itertools import chain
from pathlib import Path

from ..data import (
    ExperimentResults,
    ExperimentResultString,
    JournalEntry,
    PromptData,
    ScoreDimension,
    Settings,
)
from ..helpers import branch_manager, journal_manager, prompt_builder, results_log_manager, score_manager
from ..tools import completions, git
from ..utils import common_paths
from .experiment_base_command import ExperimentBaseCommand

DISCARDED_HASH_INDICATOR: str = "NO_COMMIT"  # used to indicate in log files that prompt was not committed, so there is no hash

# Machine-parseable status sentinels emitted as the last stdout line of perform-experiment.
# Consumed by the auto-research loop to decide whether to continue, stop, or react to a discard.
EXPERIMENT_STATUS_PREFIX: str = "EXPERIMENT_STATUS:"
EXPERIMENT_STATUS_PERFECT: str = "perfect"
EXPERIMENT_STATUS_IMPROVED: str = "improved"
EXPERIMENT_STATUS_DISCARDED: str = "discarded"
EXPERIMENT_STATUS_UNCHANGED: str = "unchanged"
EXPERIMENT_STATUS_CRASHED: str = "crashed"


async def evaluate_result(trial_prompt: PromptData, trial_output: str, run_idx: int, settings: Settings) -> str:
    eval_prompt: PromptData = prompt_builder.build_evaluation_prompt(
        settings.paths.evaluation_prompt, settings.paths.eval_rubric, trial_prompt, trial_output, settings.eval_tags
    )
    eval_output: str = await completions.get_completion(
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
    trial_prompt: PromptData = prompt_builder.build_trial_prompt(settings.paths.trial_prompt, input_filepath)
    trial_output: str = await completions.get_completion(
        trial_prompt.system_prompt, trial_prompt.user_prompt, settings.trial_model.name, settings.trial_model.effort
    )
    on_input_done()
    eval_tasks = []
    for run_idx in range(settings.evaluations_per_input):
        eval_tasks.append(evaluate_result_with_limit(trial_prompt, trial_output, run_idx, settings, eval_semaphore, on_eval_done))

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
class ScoredResults:
    dimensions_with_low_scores: list[ScoreDimension]
    total_score: float
    maximum_possible_score: float
    previous_high_score: float

    @property
    def is_new_high_score(self) -> bool:
        return self.total_score > self.previous_high_score  # A tie is not a new high score intentionally

    def get_all_questions_as_strings(self) -> list[str]:
        return [
            f"{question.id} {question.composite_score:.1f} - {question.question_text}"
            for dimension in self.dimensions_with_low_scores
            for question in dimension.questions
        ]


@dataclass
class PerformExperimentCommand(ExperimentBaseCommand):
    _: KW_ONLY
    hypothesis_tested: str
    change_to_prompt: str
    total_inputs: int = 0
    total_evals: int = 0
    completed_inputs: int = 0
    completed_evals: int = 0
    _last_score_info: ScoredResults | None = field(default=None, init=False)
    _last_commit_hash: str | None = field(default=None, init=False)

    def reset_counts(self, settings: Settings) -> None:
        self.total_inputs = len(settings.paths.input_filenames)
        self.total_evals = self.total_inputs * settings.evaluations_per_input
        self.completed_inputs = 0
        self.completed_evals = 0

    def report_progress(self) -> None:
        self.logger.report_message(
            f"time: {datetime.now().time().isoformat(timespec='milliseconds')} inputs: {self.completed_inputs}/"
            f"{self.total_inputs} evals: {self.completed_evals}/{self.total_evals}",
        )

    def on_input_done(self) -> None:
        self.completed_inputs += 1
        self.report_progress()

    def on_eval_done(self) -> None:
        self.completed_evals += 1
        self.report_progress()

    def name(self) -> str:
        return "Perform Experiment"

    def execute(self) -> None:
        self._last_score_info = None
        self._last_commit_hash = None
        super().execute()
        if self._last_score_info is not None:
            self.report_status(self._last_score_info, self._last_commit_hash)

    def perform_necessary_setup(self, settings: Settings) -> None:
        self._last_score_info = None
        self._last_commit_hash = None
        common_paths.reset_experiment_dir(self.experiment_name)
        self.reset_counts(settings)
        branch_manager.setup_branch_if_necessary(self.experiment_name)
        results_log_manager.setup_results_if_necessary(common_paths.results_filepath(self.experiment_name))
        journal_manager.setup_journal_if_necessary(common_paths.journal_filepath(self.experiment_name))

    def get_all_evaluation_results(
        self,
        settings: Settings,
        on_input_done: Callable[[], None] = lambda: None,
        on_eval_done: Callable[[], None] = lambda: None,
    ) -> list[str]:
        return asyncio.run(generate_all_evaluated_results(settings, on_input_done, on_eval_done))

    def process_scores(self, evaluation_results: list[str], settings: Settings) -> ScoredResults:
        dimensions: list[ScoreDimension] = score_manager.load_unscored_dimensions_from_rubric(settings.paths.eval_rubric)
        for evaluation_result in evaluation_results:
            score_manager.integrate_scores_into_dimensions(evaluation_result, dimensions, self.logger)

        previous_high_score: float = results_log_manager.load_previous_high_score(common_paths.results_filepath(self.experiment_name))
        current_total_score: float = score_manager.get_total_score(dimensions)
        maximum_possible_total_score: float = score_manager.get_highest_possible_score(dimensions)
        low_scoring_questions: list[ScoreDimension] = score_manager.get_low_scoring_questions(dimensions, settings.high_score_threshold)

        results: ScoredResults = ScoredResults(low_scoring_questions, current_total_score, maximum_possible_total_score, previous_high_score)
        self.tracer.add_context("total_score", results.total_score)
        self.tracer.add_context("previous_high_score", results.previous_high_score)
        self.tracer.add_context("low_questions_count", len(results.get_all_questions_as_strings()))
        self.tracer.add_context("is_new_high_score", results.is_new_high_score)
        return results

    def commit_prompt_if_necessary(self, score_info: ScoredResults, settings: Settings) -> str | None:
        if not git.file_is_dirty(settings.paths.trial_prompt):
            self.logger.report_message("Prompt has not changed (likely baseline run), no commit of prompt required.")
            return None
        if score_info.is_new_high_score:
            commit_hash: str = git.commit_file(settings.paths.trial_prompt, self.change_to_prompt)
            self.logger.report_message("Trial prompt committed with hash: " + commit_hash)
            return commit_hash
        else:
            git.revert_file(settings.paths.trial_prompt)
            self.logger.report_message("Trial prompt reverted.")
            return DISCARDED_HASH_INDICATOR

    def update_result_logs(self, commit_hash: str, score_info: ScoredResults, experiment_datetime: datetime, settings: Settings) -> None:
        low_scoring_question_strings = score_info.get_all_questions_as_strings()
        experiment_results: ExperimentResults = ExperimentResults(
            commit_hash,
            score_info.is_new_high_score,
            self.change_to_prompt,
            score_info.total_score,
            len(low_scoring_question_strings),
            experiment_datetime,
        )
        journal_entry: JournalEntry = JournalEntry(
            experiment_datetime,
            git.current_branch(),
            commit_hash,
            self.hypothesis_tested,
            self.change_to_prompt,
            score_info.total_score,
            ExperimentResultString.KEEP if score_info.is_new_high_score else ExperimentResultString.DISCARD,
            low_scoring_question_strings,
        )

        results_log_manager.append_results(experiment_results, common_paths.results_filepath(self.experiment_name))
        journal_manager.add_journal_entry(journal_entry, common_paths.journal_filepath(self.experiment_name))
        git.commit_files(
            [common_paths.results_filepath(self.experiment_name), common_paths.journal_filepath(self.experiment_name)],
            f"Update experiment result logs for {self.experiment_name}.",
        )

    def report_low_scores(self, score_info: ScoredResults) -> None:
        self.logger.report_message("Low scoring tests:")
        for low_dimension in score_info.dimensions_with_low_scores:
            self.logger.report_message(f"{low_dimension.name} - {low_dimension.description}")
            for question in low_dimension.questions:
                self.logger.report_message(f"  ID:{question.id} Score:{question.composite_score:.1f} criteria:{question.question_text}")

    def _classify_status(self, score_info: ScoredResults, commit_hash: str | None) -> str:
        if score_info.total_score >= score_info.maximum_possible_score:
            return EXPERIMENT_STATUS_PERFECT
        if commit_hash is None:
            return EXPERIMENT_STATUS_UNCHANGED
        if score_info.is_new_high_score:
            return EXPERIMENT_STATUS_IMPROVED
        return EXPERIMENT_STATUS_DISCARDED

    def report_status(self, score_info: ScoredResults, commit_hash: str | None) -> None:
        status = self._classify_status(score_info, commit_hash)
        self.logger.report_message(f"{EXPERIMENT_STATUS_PREFIX} {status} total={score_info.total_score} max={score_info.maximum_possible_score}")

    def _revert_prompt_safely(self, settings: Settings) -> None:
        try:
            git.revert_file(settings.paths.trial_prompt)
        except Exception as exc:
            self.logger.report_warning(f"Failed to revert trial prompt during crash recovery: {exc}")

    def process_experiment(self, settings: Settings, experiment_dir: Path) -> None:
        self.perform_necessary_setup(settings)
        self.report_progress()

        # KeyboardInterrupt is intentionally NOT caught: Ctrl-C is a user "stop now" and they may
        # want to inspect any dirty edit. Only Exception is caught for crash recovery.
        commit_decision_made: bool = False
        try:
            experiment_datetime: datetime = datetime.now()
            self.tracer.add_context("experiment_datetime", experiment_datetime)
            evaluation_results: list[str] = self.get_all_evaluation_results(settings, self.on_input_done, self.on_eval_done)

            score_info: ScoredResults = self.process_scores(evaluation_results, settings)

            commit_hash: str | None = self.commit_prompt_if_necessary(score_info, settings)

            commit_decision_made = True
            if commit_hash is not None:  # None means that no commit happened
                self.tracer.add_context("commit_hash", commit_hash)
                self.update_result_logs(commit_hash, score_info, experiment_datetime, settings)
            else:
                self.tracer.add_context("commit_hash", "NO_CHANGES")
            self.report_low_scores(score_info)
            self._last_score_info = score_info
            self._last_commit_hash = commit_hash
        except Exception:
            if not commit_decision_made:
                self._revert_prompt_safely(settings)
            self.logger.report_message(f"{EXPERIMENT_STATUS_PREFIX} {EXPERIMENT_STATUS_CRASHED}")
            raise
