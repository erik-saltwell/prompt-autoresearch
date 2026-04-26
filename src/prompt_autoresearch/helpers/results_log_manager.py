from __future__ import annotations

from pathlib import Path

from ..data import ExperimentResults


def setup_results_if_necessary(filepath: Path) -> None:
    # if file doesn't exist, make it.
    # if file is empty, add header.
    if not filepath.exists():
        filepath.touch()

    if filepath.stat().st_size == 0:
        header = "\t".join(ExperimentResults.fields())
        filepath.write_text(f"{header}\n")


def append_results(results: ExperimentResults, filepath: Path) -> None:
    if not filepath.exists() or filepath.stat().st_size == 0:
        setup_results_if_necessary(filepath)

    line = "\t".join(results.to_fields())
    with filepath.open("a") as file:
        file.write(f"{line}\n")


def load_results_from_file(filepath: Path) -> list[ExperimentResults]:
    if not filepath.exists():
        return []

    results: list[ExperimentResults] = []
    lines: list[str] = filepath.read_text().splitlines()[1:]
    results.extend(ExperimentResults.from_tsv_line(line) for line in lines if line)
    return results


def load_previous_high_score(filepath: Path) -> float:
    return max((result.total_score for result in load_results_from_file(filepath)), default=0.0)
