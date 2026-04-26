from __future__ import annotations

from enum import StrEnum
from pathlib import Path


class KnownPathnames(StrEnum):
    EXPERIMENTS = "experiments"
    INPUTS = "inputs"
    OUTPUTS = "outputs"
    LOGS = "logs"
    SETTINGS = "settings.yaml"
    RESULTS = "results.tsv"
    EXPERIMENT_JOURNAL = "experiment_journal.md"
    LAST_COMPLETION = "last_completion.md"
    FRAGMENTS = "fragments"


def ensure_directory(dir: Path) -> None:
    dir.mkdir(parents=True, exist_ok=True)


def experiments_dir() -> Path:
    return Path.cwd() / KnownPathnames.EXPERIMENTS


def experiment_dir(experiment_name: str) -> Path:
    cwd = Path.cwd()
    if cwd.name == experiment_name and (cwd / KnownPathnames.SETTINGS).exists():
        return cwd
    return experiments_dir() / experiment_name


def resolve_experiment_name(provided: str | None) -> str:
    if provided is not None:
        return provided
    cwd = Path.cwd()
    if (cwd / KnownPathnames.SETTINGS).exists():
        return cwd.name
    raise ValueError(
        "No experiment name provided and current directory does not contain settings.yaml. "
        "Either pass the experiment name explicitly or cd into the experiment directory."
    )


def outputs_dir(experiment_name: str) -> Path:
    return experiment_dir(experiment_name) / KnownPathnames.OUTPUTS


def logs_dir(experiment_name: str) -> Path:
    return experiment_dir(experiment_name) / KnownPathnames.LOGS


def inputs_dir(experiment_name: str) -> Path:
    return experiment_dir(experiment_name) / KnownPathnames.INPUTS


def fragments_dir() -> Path:
    return Path.cwd() / KnownPathnames.FRAGMENTS


def experiment_filepath(experiment_name: str, filename: str) -> Path:
    return experiment_dir(experiment_name) / filename


def outputs_filepath(experiment_name: str, filename: str) -> Path:
    return outputs_dir(experiment_name) / filename


def logs_filepath(experiment_name: str, filename: str) -> Path:
    return logs_dir(experiment_name) / filename


def settings_filepath(experiment_name: str) -> Path:
    return experiment_filepath(experiment_name, KnownPathnames.SETTINGS)


def results_filepath(experiment_name: str) -> Path:
    return experiment_filepath(experiment_name, KnownPathnames.RESULTS)


def journal_filepath(experiment_name: str) -> Path:
    return experiment_filepath(experiment_name, KnownPathnames.EXPERIMENT_JOURNAL)


def last_completion_filepath(experiment_name: str) -> Path:
    return logs_dir(experiment_name) / KnownPathnames.LAST_COMPLETION


def prepare_output_directory(output_dir: Path) -> None:
    import shutil

    if output_dir.exists():
        shutil.rmtree(output_dir)

    ensure_directory(output_dir)


def reset_experiment_dir(experiment_name: str) -> None:
    # This functions makes sure the experiment dir exists and then clears the output and logs directories, emptying them
    # These directories will only have temporary feels that are ok to clean on each run.
    exp_dir: Path = experiment_dir(experiment_name)
    ensure_directory(exp_dir)
    prepare_output_directory(logs_dir(experiment_name))
    prepare_output_directory(outputs_dir(experiment_name))
