from __future__ import annotations

from pathlib import Path

from prompt_autoresearch.commands import ReportKeyFilesCommand
from prompt_autoresearch.protocols import NullLogger


class RecordingLogger(NullLogger):
    def __init__(self) -> None:
        self.messages: list[str] = []

    def report_message(self, message: str) -> None:
        self.messages.append(message)


def test_report_key_files_reports_absolute_paths(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    experiment_dir = tmp_path / "experiments" / "test"
    experiment_dir.mkdir(parents=True)
    (experiment_dir / "settings.yaml").write_text(
        "\n".join(
            [
                "max_simultaneous_evaluations: 1",
                "evaluations_per_input: 1",
                "high_score_threshold: 0",
                "paths:",
                '  evaluation_prompt: "evaluation_prompt.md"',
                '  trial_prompt: "trial_prompt.md"',
                '  eval_rubric: "rubric.md"',
                '  current_goal: "current_goal.md"',
                "  input_filenames:",
                '    - "inputs/one.md"',
                "trial_model:",
                '  name: "gpt-5.4"',
                '  effort: "medium"',
                "eval_model:",
                '  name: "gpt-5.4"',
                '  effort: "medium"',
                "eval_tags:",
                '  prompt_output_start_tag: "<output>"',
                '  prompt_output_end_tag: "</output>"',
                '  input_start_tag: "<input>"',
                '  input_end_tag: "</input>"',
            ]
        )
    )
    logger = RecordingLogger()

    ReportKeyFilesCommand(experiment_name="test").execute(logger)

    assert f"Results log: {(experiment_dir / 'results.tsv').resolve()}" in logger.messages
    assert f"Experiment journal: {(experiment_dir / 'experiment_journal.md').resolve()}" in logger.messages
    assert f"Trial prompt: {(experiment_dir / 'trial_prompt.md').resolve()}" in logger.messages
