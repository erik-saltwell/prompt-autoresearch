from __future__ import annotations

from pathlib import Path

from ..data import EvalTags, PromptData
from ..utils import FragmentID, get_fragment


def build_trial_prompt(trial_prompt_path: Path, input_file_path: Path) -> PromptData:
    return PromptData(system_prompt=trial_prompt_path.read_text(), user_prompt=input_file_path.read_text())


def build_evaluation_prompt(
    eval_prompt_path: Path, rubric_path: Path, trial_prompt: PromptData, prompt_output: str, tags: EvalTags
) -> PromptData:
    system_prompt: str = (
        eval_prompt_path.read_text() + get_fragment(FragmentID.EVALUATION_SCORING) + rubric_path.read_text()
    )
    user_prompt: str = tags.input_start_tag + trial_prompt.user_prompt + tags.input_end_tag
    user_prompt = user_prompt + tags.prompt_output_start_tag + prompt_output + tags.prompt_output_end_tag
    return PromptData(system_prompt, user_prompt)
