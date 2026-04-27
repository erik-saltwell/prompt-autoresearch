from __future__ import annotations

from datetime import datetime
from importlib.metadata import PackageNotFoundError, metadata
from importlib.metadata import version as dist_version
from typing import Annotated

import typer
from dotenv import load_dotenv
from rich.console import Console

from ..commands import (
    InitAgentCommand,
    PerformExperimentCommand,
    ReadJournalCommand,
    ReportKeyFilesCommand,
)
from ..protocols import CompositeLogger, LoggingProtocol
from ..utils import Tracer, common_paths, initialize_request, initialize_tracing
from .file_logging_protocol import FileLogger
from .rich_logging_protocol import RichConsoleLogger

app = typer.Typer(
    name="prompt-autoresearch",
    add_completion=True,
    help="Tools used by your coding agent to run autoresearch on your prompt.",
)


def create_logger(experiment_name: str) -> tuple[LoggingProtocol, Tracer]:
    console = Console()
    console_logger: RichConsoleLogger = RichConsoleLogger(console)
    logfilename: str = datetime.now().strftime("%Y%m%d_%H_%M_%S") + ".log"
    file_logger: FileLogger = FileLogger(common_paths.logs_dir(experiment_name) / logfilename)

    initialize_tracing(experiment_name)
    request_id: str = initialize_request()

    logger = CompositeLogger([console_logger, file_logger])
    logger.report_message(f"[blue]Session id: {request_id}[/blue]")
    return logger, Tracer()


_EXPERIMENT_NAME_HELP = "Experiment directory name. Optional when run from inside an experiment directory (one containing settings.yaml)."


def _resolve_experiment_name(provided: str | None) -> str:
    try:
        return common_paths.resolve_experiment_name(provided)
    except ValueError as exc:
        raise typer.BadParameter(str(exc), param_hint="experiment_name") from exc


@app.command("perform-experiment")
def perform_experiment(
    hypothesis: Annotated[str, typer.Option("--hypothesis", help="Hypothesis tested by this run.")],
    experimental_change: Annotated[
        str,
        typer.Option("--change", help="The change made to the prompt in this run."),
    ],
    experiment_name: Annotated[str | None, typer.Argument(help=_EXPERIMENT_NAME_HELP)] = None,
) -> None:
    """Run trial prompts and evaluate the outputs."""
    resolved_name = _resolve_experiment_name(experiment_name)
    logger, tracer = create_logger(resolved_name)
    PerformExperimentCommand(
        experiment_name=resolved_name, hypothesis_tested=hypothesis, change_to_prompt=experimental_change, logger=logger, tracer=tracer
    ).execute()


@app.command("read-journal")
def read_journal(
    experiment_name: Annotated[str | None, typer.Argument(help=_EXPERIMENT_NAME_HELP)] = None,
    previous_entries: Annotated[
        int,
        typer.Option(
            "--previous-entries",
            "-n",
            min=0,
            help="Maximum number of most recent journal entries to print. Defaults to 10.",
        ),
    ] = 10,
) -> None:
    """Print the experiment journal."""
    resolved_name = _resolve_experiment_name(experiment_name)
    logger, tracer = create_logger(resolved_name)
    ReadJournalCommand(experiment_name=resolved_name, previous_entries=previous_entries, logger=logger, tracer=tracer).execute()


@app.command("report-key-files")
def report_key_files(
    experiment_name: Annotated[str | None, typer.Argument(help=_EXPERIMENT_NAME_HELP)] = None,
) -> None:
    """Print absolute paths to the key files for an experiment."""
    resolved_name = _resolve_experiment_name(experiment_name)
    logger, tracer = create_logger(resolved_name)
    ReportKeyFilesCommand(experiment_name=resolved_name, logger=logger, tracer=tracer).execute()


@app.command("init-agent")
def init_agent(
    experiment_name: Annotated[str | None, typer.Argument(help=_EXPERIMENT_NAME_HELP)] = None,
    force: Annotated[bool, typer.Option("--force", help="Overwrite existing .claude files if present.")] = False,
) -> None:
    """Scaffold the auto-researcher subagent, slash command, and permissions in this experiment's .claude directory."""
    resolved_name = _resolve_experiment_name(experiment_name)
    logger, tracer = create_logger(resolved_name)
    InitAgentCommand(experiment_name=resolved_name, force=force, logger=logger, tracer=tracer).execute()


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
