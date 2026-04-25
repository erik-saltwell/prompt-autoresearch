from __future__ import annotations

from prompt_autoresearch.data import ScoreDimension, ScoreQuestion
from prompt_autoresearch.helpers import get_low_scoring_questions, integrate_scores_into_dimensions


class WarningLogger:
    def __init__(self) -> None:
        self.warnings: list[str] = []

    def report_warning(self, message: str) -> None:
        self.warnings.append(message)


def test_get_low_scoring_questions_filters_dimensions_without_low_questions() -> None:
    dimensions = [
        ScoreDimension(
            name="All high",
            description="No low scores",
            tag="high",
            questions=[ScoreQuestion("high_01", "High score", scores=[3])],
        ),
        ScoreDimension(
            name="Mixed",
            description="Has one low score",
            tag="mixed",
            questions=[
                ScoreQuestion("mixed_01", "Low score", scores=[1]),
                ScoreQuestion("mixed_02", "High score", scores=[3]),
            ],
        ),
    ]

    low_dimensions = get_low_scoring_questions(dimensions, high_score_floor=5.0)

    assert low_dimensions == [
        ScoreDimension(
            name="Mixed",
            description="Has one low score",
            tag="mixed",
            questions=[ScoreQuestion("mixed_01", "Low score", scores=[1])],
        )
    ]


def test_integrate_scores_warns_when_output_contains_no_json_object() -> None:
    logger = WarningLogger()

    integrate_scores_into_dimensions("the evaluator returned prose", [], logger)

    assert logger.warnings == ["Evaluation output did not contain a JSON object; skipping scores."]


def test_integrate_scores_warns_when_output_contains_malformed_json() -> None:
    logger = WarningLogger()

    integrate_scores_into_dimensions('{"scores": }', [], logger)

    assert len(logger.warnings) == 1
    assert logger.warnings[0].startswith("Evaluation output contained malformed JSON; skipping scores.")


def test_integrate_scores_warns_when_score_id_has_no_dimension_prefix() -> None:
    logger = WarningLogger()

    integrate_scores_into_dimensions('{"scores": {"01": 3}}', [], logger)

    assert logger.warnings == ["Evaluation score ID '01' does not include a dimension prefix; skipping score."]


def test_integrate_scores_warns_and_skips_non_numeric_score() -> None:
    logger = WarningLogger()
    dimensions = [
        ScoreDimension(
            name="Completeness",
            description="Completeness checks",
            tag="comp",
            questions=[ScoreQuestion("comp_01", "Includes key beats")],
        )
    ]

    integrate_scores_into_dimensions('{"scores": {"comp_01": "high"}}', dimensions, logger)

    assert logger.warnings == ["Evaluation score ID 'comp_01' has non-numeric score 'high'; skipping score."]
    assert dimensions[0].questions[0].scores == []


def test_integrate_scores_warns_when_score_id_has_unknown_dimension_prefix() -> None:
    logger = WarningLogger()
    dimensions = [
        ScoreDimension(
            name="Completeness",
            description="Completeness checks",
            tag="comp",
            questions=[ScoreQuestion("comp_01", "Includes key beats")],
        )
    ]

    integrate_scores_into_dimensions('{"scores": {"focus_01": 3}}', dimensions, logger)

    assert logger.warnings == ["Evaluation score ID 'focus_01' uses unknown dimension prefix 'focus'; skipping score."]
    assert dimensions[0].questions[0].scores == []


def test_integrate_scores_warns_when_score_id_does_not_match_question() -> None:
    logger = WarningLogger()
    dimensions = [
        ScoreDimension(
            name="Completeness",
            description="Completeness checks",
            tag="comp",
            questions=[ScoreQuestion("comp_01", "Includes key beats")],
        )
    ]

    integrate_scores_into_dimensions('{"scores": {"comp_02": 3}}', dimensions, logger)

    assert logger.warnings == ["Evaluation score ID 'comp_02' does not match a rubric question; skipping score."]
    assert dimensions[0].questions[0].scores == []
