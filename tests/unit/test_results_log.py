from __future__ import annotations

from datetime import datetime
from pathlib import Path

from prompt_autoresearch.data import ExperimentResults
from prompt_autoresearch.helpers import append_results, initialize_results, load_results_from_file


def test_experiment_results_fields_returns_tsv_header_order() -> None:
    assert ExperimentResults.fields() == [
        "datetime",
        "total_score",
        "low_score_count",
        "result",
        "description",
        "commit_hash",
    ]


def test_experiment_results_to_fields_serializes_keep_result() -> None:
    created_at = datetime(2026, 4, 24, 12, 0, 0)
    result = ExperimentResults(
        checkin_hash="abc123",
        was_successful=True,
        description="improved baseline",
        total_score=93.5,
        low_scoring_tests=2,
        created_at=created_at,
    )

    fields = result.to_fields()

    assert fields[0] == "2026-04-24T12:00:00"
    assert fields[1:] == ["93.5", "2", "keep", "improved baseline", "abc123"]


def test_experiment_results_to_fields_serializes_discard_result() -> None:
    created_at = datetime(2026, 4, 24, 12, 0, 1)
    result = ExperimentResults(
        checkin_hash="def456",
        was_successful=False,
        description="worse output",
        total_score=12.0,
        low_scoring_tests=7,
        created_at=created_at,
    )

    fields = result.to_fields()

    assert fields[0] == "2026-04-24T12:00:01"
    assert fields[1:] == ["12.0", "7", "discard", "worse output", "def456"]


def test_experiment_results_to_fields_uses_construction_datetime() -> None:
    result = ExperimentResults("abc123", True, "improved baseline", 93.5, 2)

    assert result.to_fields()[0] == result.to_fields()[0]


def test_convert_results_to_string_returns_header_for_empty_iterable() -> None:
    text = ExperimentResults.convert_results_to_string([])

    assert text == "\t".join(ExperimentResults.fields())


def test_convert_results_to_string_preserves_result_order() -> None:
    results = [
        ExperimentResults("abc123", True, "first", 93.5, 2),
        ExperimentResults("def456", False, "second", 12.0, 7),
    ]

    text = ExperimentResults.convert_results_to_string(results)
    lines = text.splitlines()

    assert lines[0] == "\t".join(ExperimentResults.fields())
    assert lines[1].split("\t")[1:] == ["93.5", "2", "keep", "first", "abc123"]
    assert lines[2].split("\t")[1:] == ["12.0", "7", "discard", "second", "def456"]


def test_experiment_results_from_tsv_line() -> None:
    line = "2026-04-24T12:00:00\t93.5\t2\tkeep\timproved baseline\tabc123\n"

    result = ExperimentResults.from_tsv_line(line)

    assert result == ExperimentResults(
        checkin_hash="abc123",
        was_successful=True,
        description="improved baseline",
        total_score=93.5,
        low_scoring_tests=2,
        created_at=datetime(2026, 4, 24, 12, 0, 0),
    )


def test_experiment_results_from_tsv_line_parses_discard() -> None:
    line = "2026-04-24T12:00:00\t12.0\t7\tdiscard\tworse output\tdef456"

    result = ExperimentResults.from_tsv_line(line)

    assert result.was_successful is False
    assert result.total_score == 12.0
    assert result.low_scoring_tests == 7
    assert result.created_at == datetime(2026, 4, 24, 12, 0, 0)


def test_experiment_results_round_trip_preserves_recorded_datetime() -> None:
    result = ExperimentResults(
        checkin_hash="abc123",
        was_successful=True,
        description="improved baseline",
        total_score=93.5,
        low_scoring_tests=2,
        created_at=datetime(2026, 4, 24, 12, 0, 0),
    )

    restored = ExperimentResults.from_tsv_line("\t".join(result.to_fields()))

    assert restored == result


def test_initialize_results_creates_file_when_it_does_not_exist(tmp_path: Path) -> None:
    filepath = tmp_path / "results.tsv"
    header = "\t".join(ExperimentResults.fields())

    initialize_results(filepath)

    assert filepath.read_text() == f"{header}\n"


def test_initialize_results_preserves_existing_file(tmp_path: Path) -> None:
    filepath = tmp_path / "results.tsv"
    filepath.write_text("old content\n")

    initialize_results(filepath)

    assert filepath.read_text() == "old content\n"


def test_append_results_appends_one_tsv_line(tmp_path: Path) -> None:
    filepath = tmp_path / "results.tsv"
    initialize_results(filepath)
    result = ExperimentResults("abc123", True, "improved baseline", 93.5, 2)

    append_results(result, filepath)

    lines = filepath.read_text().splitlines()
    assert lines[0] == "\t".join(ExperimentResults.fields())
    assert lines[1].split("\t")[1:] == ["93.5", "2", "keep", "improved baseline", "abc123"]


def test_append_results_initializes_missing_file_before_appending(tmp_path: Path) -> None:
    filepath = tmp_path / "results.tsv"
    result = ExperimentResults("abc123", True, "improved baseline", 93.5, 2)

    append_results(result, filepath)

    assert load_results_from_file(filepath) == [result]


def test_append_results_initializes_empty_file_before_appending(tmp_path: Path) -> None:
    filepath = tmp_path / "results.tsv"
    filepath.write_text("")
    result = ExperimentResults("abc123", True, "improved baseline", 93.5, 2)

    append_results(result, filepath)

    assert load_results_from_file(filepath) == [result]


def test_load_results_from_file_returns_empty_list_for_header_only_file(tmp_path: Path) -> None:
    filepath = tmp_path / "results.tsv"
    initialize_results(filepath)

    assert load_results_from_file(filepath) == []


def test_load_results_from_file_returns_empty_list_for_empty_file(tmp_path: Path) -> None:
    filepath = tmp_path / "results.tsv"
    filepath.write_text("")

    assert load_results_from_file(filepath) == []


def test_load_results_from_file_returns_empty_list_for_missing_file(tmp_path: Path) -> None:
    filepath = tmp_path / "results.tsv"

    assert load_results_from_file(filepath) == []


def test_load_results_from_file_parses_non_empty_result_lines(tmp_path: Path) -> None:
    filepath = tmp_path / "results.tsv"
    initialize_results(filepath)
    expected_results = [
        ExperimentResults("abc123", True, "improved baseline", 93.5, 2),
        ExperimentResults("def456", False, "worse output", 12.0, 7),
    ]
    for result in expected_results:
        append_results(result, filepath)

    assert load_results_from_file(filepath) == expected_results
