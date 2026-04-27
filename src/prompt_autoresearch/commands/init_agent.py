from __future__ import annotations

from dataclasses import KW_ONLY, dataclass
from pathlib import Path

from ..data import Settings
from ..utils import FragmentID, render_fragment
from ..utils.common_paths import KnownPathnames
from .experiment_base_command import ExperimentBaseCommand

CLAUDE_DIR_NAME: str = ".claude"
AGENT_FILENAME: str = "auto-researcher.md"
SLASH_COMMAND_FILENAME: str = "improve-prompt.md"
SETTINGS_FILENAME: str = "settings.json"


@dataclass
class InitAgentCommand(ExperimentBaseCommand):
    _: KW_ONLY
    force: bool = False

    def name(self) -> str:
        return "Init Agent"

    def _target_paths(self, experiment_dir: Path) -> dict[str, Path]:
        claude_dir = experiment_dir / CLAUDE_DIR_NAME
        return {
            "agent": claude_dir / "agents" / AGENT_FILENAME,
            "slash_command": claude_dir / "commands" / SLASH_COMMAND_FILENAME,
            "settings": claude_dir / SETTINGS_FILENAME,
        }

    def _check_existing(self, paths: dict[str, Path]) -> None:
        existing = [path for path in paths.values() if path.exists()]
        if existing and not self.force:
            existing_str = ", ".join(str(path) for path in existing)
            raise FileExistsError(f"Refusing to overwrite existing files: {existing_str}. Re-run with --force to overwrite.")

    def _relpath(self, path: Path, experiment_dir: Path, label: str) -> str:
        try:
            return path.relative_to(experiment_dir).as_posix()
        except ValueError as exc:
            raise ValueError(
                f"{label} path {path} is not inside experiment dir {experiment_dir}; init-agent requires this file to live within the experiment directory."
            ) from exc

    def process_experiment(self, settings: Settings, experiment_dir: Path) -> None:
        trial_prompt_relpath = self._relpath(settings.paths.trial_prompt, experiment_dir, "trial_prompt")
        evaluation_prompt_relpath = self._relpath(settings.paths.evaluation_prompt, experiment_dir, "evaluation_prompt")
        eval_rubric_relpath = self._relpath(settings.paths.eval_rubric, experiment_dir, "eval_rubric")
        current_goal_relpath = self._relpath(settings.paths.current_goal, experiment_dir, "current_goal")

        paths = self._target_paths(experiment_dir)
        self._check_existing(paths)

        for path in paths.values():
            path.parent.mkdir(parents=True, exist_ok=True)

        rendered = {
            "agent": render_fragment(
                FragmentID.AUTO_RESEARCHER_AGENT,
                experiment_name=self.experiment_name,
                trial_prompt_relpath=trial_prompt_relpath,
                evaluation_prompt_relpath=evaluation_prompt_relpath,
                eval_rubric_relpath=eval_rubric_relpath,
                current_goal_relpath=current_goal_relpath,
                journal_relpath=KnownPathnames.EXPERIMENT_JOURNAL.value,
                results_relpath=KnownPathnames.RESULTS.value,
            ),
            "slash_command": render_fragment(FragmentID.IMPROVE_PROMPT_COMMAND),
            "settings": render_fragment(
                FragmentID.CLAUDE_SETTINGS,
                trial_prompt_relpath=trial_prompt_relpath,
            ),
        }

        for label, path in paths.items():
            path.write_text(rendered[label])

        for label, path in paths.items():
            self.logger.report_message(f"Wrote {label}: {path}")
