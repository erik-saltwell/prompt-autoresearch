from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field

from .model_settings import ModelEffort, ModelString


class ModelSettings(BaseModel):
    model_config = ConfigDict(frozen=True)
    name: ModelString
    effort: ModelEffort


class EvalTags(BaseModel):
    model_config = ConfigDict(frozen=True)
    prompt_output_start_tag: str
    prompt_output_end_tag: str
    input_start_tag: str
    input_end_tag: str


class PathSettings(BaseModel):
    model_config = ConfigDict(frozen=True)
    evaluation_prompt: Path
    trial_prompt: Path
    eval_rubric: Path
    current_goal: Path
    input_filenames: tuple[Path, ...] = Field(min_length=1)


def _resolve_from_settings_dir(path: Path, settings_dir: Path) -> Path:
    if path.is_absolute():
        return path
    return settings_dir / path


class Settings(BaseModel):
    model_config = ConfigDict(frozen=True)
    max_simultaneous_evaluations: int = Field(gt=0)
    evaluations_per_input: int = Field(gt=0)
    high_score_threshold: float = Field(ge=0.0)

    paths: PathSettings
    trial_model: ModelSettings
    eval_model: ModelSettings
    eval_tags: EvalTags

    @classmethod
    def load(cls, path: Path = Path("settings.yaml")) -> "Settings":
        settings_path = path if path.is_absolute() else Path.cwd() / path

        raw_settings = yaml.safe_load(settings_path.read_text())
        if not isinstance(raw_settings, dict):
            raise ValueError(f"{settings_path} must contain a YAML mapping.")

        settings = cls.model_validate(raw_settings)
        settings_dir = settings_path.parent
        resolved_paths = settings.paths.model_copy(
            update={
                "evaluation_prompt": _resolve_from_settings_dir(settings.paths.evaluation_prompt, settings_dir),
                "trial_prompt": _resolve_from_settings_dir(settings.paths.trial_prompt, settings_dir),
                "eval_rubric": _resolve_from_settings_dir(settings.paths.eval_rubric, settings_dir),
                "current_goal": _resolve_from_settings_dir(settings.paths.current_goal, settings_dir),
                "input_filenames": tuple(_resolve_from_settings_dir(input_filename, settings_dir) for input_filename in settings.paths.input_filenames),
            }
        )

        return settings.model_copy(update={"paths": resolved_paths})
