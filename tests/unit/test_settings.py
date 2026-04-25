from __future__ import annotations

from pathlib import Path

from prompt_autoresearch.data import Settings


def test_settings_load_resolves_input_filenames_relative_to_settings_file(tmp_path: Path) -> None:
    experiment_dir = tmp_path / "experiment"
    experiment_dir.mkdir()
    settings_path = experiment_dir / "settings.yaml"
    settings_path.write_text(
        "\n".join(
            [
                "evaluations_per_input: 2",
                "max_simultaneous_evaluations: 10",
                "high_score_threshold: 10",
                "paths:",
                '  evaluation_prompt: "evaluation_prompt.md"',
                '  trial_prompt: "trial_prompt.md"',
                '  eval_rubric: "evaluation_rubric.json"',
                "  input_filenames:",
                '    - "inputs/foo.md"',
                '    - "inputs/bar.md"',
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
                "",
            ]
        )
    )

    settings = Settings.load(settings_path)

    assert settings.paths.input_filenames == (
        experiment_dir / "inputs/foo.md",
        experiment_dir / "inputs/bar.md",
    )
