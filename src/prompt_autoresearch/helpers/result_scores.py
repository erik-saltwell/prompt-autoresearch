from __future__ import annotations

import json
from pathlib import Path
from typing import Protocol

from ..data import (
    HIGHEST_COMPOSITE_SCORE_FOR_A_QUESTION,
    HIGHEST_SCORE_FOR_A_RESPONSE,
    ScoreDimension,
    ScoreQuestion,
)


class WarningReporter(Protocol):
    def report_warning(self, message: str) -> None: ...


def load_unscored_dimensions_from_rubric(filepath: Path) -> list[ScoreDimension]:
    rubric_data = json.loads(filepath.read_text())

    return [
        ScoreDimension(
            name=dimension["name"],
            description=dimension["description"],
            tag=dimension["tag"],
            questions=[
                ScoreQuestion(
                    id=criterion["id"],
                    question_text=criterion["text"],
                )
                for criterion in dimension["criteria"]
            ],
        )
        for dimension in rubric_data["dimensions"]
    ]


def _get_dimension_by_tag(dimensions: list[ScoreDimension], tag: str) -> ScoreDimension | None:
    return next((dimension for dimension in dimensions if dimension.tag == tag), None)


def _get_tag_from_question_id(question_id: str) -> str:
    idx: int = question_id.find("_")
    if idx < 0:
        return ""
    return question_id[0:idx]


def _get_question_from_question_id(question_id: str, dimension: ScoreDimension) -> ScoreQuestion | None:
    return next((question for question in dimension.questions if question.id == question_id), None)


def integrate_scores_into_dimensions(
    scores_json: str, dimensions: list[ScoreDimension], logger: WarningReporter | None = None
) -> None:
    start = scores_json.find("{")
    end = scores_json.rfind("}")
    if start == -1 or end == -1:
        if logger is not None:
            logger.report_warning("Evaluation output did not contain a JSON object; skipping scores.")
        return
    trimmed = scores_json[start : end + 1]
    try:
        data = json.loads(trimmed)
    except json.JSONDecodeError as error:
        if logger is not None:
            logger.report_warning(f"Evaluation output contained malformed JSON; skipping scores. Error: {error}")
        return
    scores = data.get("scores", {})

    for id, score in scores.items():
        tag = _get_tag_from_question_id(id)
        if len(tag) == 0:
            if logger is not None:
                logger.report_warning(
                    f"Evaluation score ID '{id}' does not include a dimension prefix; skipping score."
                )
            continue
        target_dimension: ScoreDimension | None = _get_dimension_by_tag(dimensions, tag)
        if target_dimension is None:
            if logger is not None:
                logger.report_warning(
                    f"Evaluation score ID '{id}' uses unknown dimension prefix '{tag}'; skipping score."
                )
            continue
        target_question: ScoreQuestion | None = _get_question_from_question_id(id, target_dimension)
        if target_question is None:
            if logger is not None:
                logger.report_warning(f"Evaluation score ID '{id}' does not match a rubric question; skipping score.")
            continue
        try:
            numeric_score = int(score)
        except (TypeError, ValueError):
            if logger is not None:
                logger.report_warning(f"Evaluation score ID '{id}' has non-numeric score '{score}'; skipping score.")
            continue
        target_question.scores.append(max(1, min(numeric_score, int(HIGHEST_SCORE_FOR_A_RESPONSE))))


def get_highest_possible_score(dimensions: list[ScoreDimension]) -> float:
    result: float = HIGHEST_COMPOSITE_SCORE_FOR_A_QUESTION * sum([len(dimension.questions) for dimension in dimensions])
    return result


def get_total_score(dimensions: list[ScoreDimension]) -> float:
    total_score = sum(question.composite_score for dimension in dimensions for question in dimension.questions)
    return total_score


def get_low_scoring_questions(dimensions: list[ScoreDimension], high_score_floor: float) -> list[ScoreDimension]:
    results: list[ScoreDimension] = []
    for dimension in dimensions:
        low_scoring_questions: list[ScoreQuestion] = [
            question for question in dimension.questions if question.composite_score < high_score_floor
        ]
        if not low_scoring_questions:
            continue
        new_dimension: ScoreDimension = ScoreDimension(
            dimension.name, dimension.description, dimension.tag, low_scoring_questions
        )
        results.append(new_dimension)
    return results
