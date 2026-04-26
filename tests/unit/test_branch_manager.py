from __future__ import annotations

import pytest

from prompt_autoresearch.helpers.branch_manager import _is_correct_autoresearch_branch


@pytest.mark.parametrize(
    ("experiment_name", "current_branch", "expected"),
    [
        ("test", "autoresearch/test_20260426_000", True),
        ("clean_transcript", "autoresearch/clean_transcript_20260426_001", True),
        ("test", "main", False),
        ("test", "feature/test_20260426_000", False),
        ("test", "autoresearch/test2_20260426_000", False),
        ("clean", "autoresearch/clean_transcript_20260426_000", False),
    ],
)
def test_is_correct_autoresearch_branch_requires_exact_experiment_prefix(
    experiment_name: str, current_branch: str, expected: bool
) -> None:
    assert _is_correct_autoresearch_branch(experiment_name, current_branch) is expected
