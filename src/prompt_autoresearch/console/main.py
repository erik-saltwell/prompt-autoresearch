from __future__ import annotations

from datetime import datetime
from importlib.metadata import PackageNotFoundError, metadata
from importlib.metadata import version as dist_version
from typing import Annotated

import typer
from dotenv import load_dotenv
from rich.console import Console

from ..commands import (
    PerformExperimentCommand,
    ReadJournalCommand,
    SetupExperimentCommand,
    UpdateExperimentResultsCommand,
)
from ..data import ExperimentResultString, JournalEntry
from ..protocols import CompositeLogger, LoggingProtocol
from .file_logging_protocol import FileLogger
from .rich_logging_protocol import RichConsoleLogger

app = typer.Typer(
    name="prompt-autoresearch",
    add_completion=True,
    help="Tools used by your coding agent to run autoresearch on your prompt.",
)

LOG_FILENAME: str = "prompt_autoresearch.log"


def create_logger() -> LoggingProtocol:
    console = Console()
    console_logger: RichConsoleLogger = RichConsoleLogger(console)
    file_logger: FileLogger = FileLogger(LOG_FILENAME, verbose_training=True)
    return CompositeLogger([console_logger, file_logger])


@app.command("setup-experiment")
def setup_experiment(experiment_name: Annotated[str, typer.Argument(help="Experiment directory name.")]) -> None:
    """Initialize a new experiment run."""
    SetupExperimentCommand(experiment_name=experiment_name).execute(create_logger())


@app.command("perform-experiment")
def perform_experiment(
    experiment_name: Annotated[str, typer.Argument(help="Experiment directory name.")],
) -> None:
    """Run trial prompts and evaluate the outputs."""
    PerformExperimentCommand(experiment_name=experiment_name).execute(create_logger())


@app.command("read-journal")
def read_journal(experiment_name: Annotated[str, typer.Argument(help="Experiment directory name.")]) -> None:
    """Print the experiment journal."""
    ReadJournalCommand(experiment_name=experiment_name).execute(create_logger())


@app.command("update-results")
def update_results(
    experiment_name: Annotated[str, typer.Argument(help="Experiment directory name.")],
    branch: Annotated[str, typer.Option("--branch", help="Branch used for this experiment result.")],
    commit: Annotated[str, typer.Option("--commit-hash", help="Commit hash for this experiment result.")],
    hypothesis: Annotated[str, typer.Option("--hypothesis", help="Hypothesis tested by this experiment result.")],
    experimental_change: Annotated[
        str,
        typer.Option("--change", help="Prompt or workflow change tested by this experiment result."),
    ],
    total_score: Annotated[float, typer.Option("--total-score", help="Total score for this experiment result.")],
    result: Annotated[
        ExperimentResultString,
        typer.Option("--result", help="Must be either 'keep' or 'discard' to note if we committed the changes."),
    ],
    low_scoring_results: Annotated[
        list[str] | None,
        typer.Option("--low-scoring-result", help="Low-scoring result note. May be provided multiple times."),
    ] = None,
) -> None:
    """Append a completed experiment result to the results log and journal."""
    journal_entry = JournalEntry(
        entry_date=datetime.now(),
        branch=branch,
        commit=commit,
        hypothesis=hypothesis,
        experimental_change=experimental_change,
        total_score=total_score,
        result=result,
        low_scoring_results=low_scoring_results or [],
    )
    UpdateExperimentResultsCommand(
        experiment_name=experiment_name,
        journal_entry=journal_entry,
    ).execute(create_logger())


def _version_callback(value: bool) -> None:
    """Print version and exit."""
    if not value:
        return

    # IMPORTANT: distribution name (pyproject.toml [project].name), often hyphenated.
    # Example: "my-tool" even if your import package is "my_tool".
    DIST_NAME = "prompt-autoresearch"

    console = Console()

    try:
        pkg_version = dist_version(DIST_NAME)
        md = metadata(DIST_NAME)
        try:
            pkg_name = md["Name"]
        except KeyError:
            pkg_name = DIST_NAME

        console.print(f"{pkg_name} {pkg_version}")
    except PackageNotFoundError:
        # Running from source without an installed distribution
        console.print(f"{DIST_NAME} 0.0.0+unknown")

    raise typer.Exit()


@app.callback()
def _callback(
    version: bool = typer.Option(
        False,
        "--version",
        "-v",
        help="Show version and exit.",
        callback=_version_callback,
        is_eager=True,
    ),
) -> None:
    """Root command group for prompt-autoresearch."""
    load_dotenv()


if __name__ == "__main__":
    app()
