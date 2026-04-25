from __future__ import annotations

from typing import Any, cast

from litellm import acompletion

from ..data import ModelEffort, ModelString


async def get_completion(system_prompt: str, user_prompt: str, model: ModelString, effort: ModelEffort) -> str:
    response = cast(
        dict[str, Any],
        await acompletion(
            model=model.value,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            reasoning_effort=effort.value,
            stream=False,
        ),
    )
    response_text: str | None = response["choices"][0]["message"]["content"]
    if response_text is None:
        return ""
    else:
        return response_text
