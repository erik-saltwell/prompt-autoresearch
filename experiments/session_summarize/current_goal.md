# Current Experiment Goal

## The Prompt

We are working on a **TTRPG session summary system prompt** (`trial_prompt.md`). This prompt instructs an LLM to read a cleaned, diarized transcript of a tabletop roleplaying game session and produce a concise, structured session summary intended for future play reference — not as a historical record, but as a reincorporation tool.

The prompt defines:
- A strict output structure (Header, Starting Situation, Scene Breakdown, Ending Situation, Open Loops, Key Decisions & Events, Clocks)
- A core filtering principle called **reincorporation**: only include content likely to be referenced or acted on in future sessions
- Explicit exclusion rules (out-of-game talk, mechanical details, resolved events, deliberation)
- Tone and voice guidelines (terse, factual, bullet-driven)
- A final self-review checklist

## Current Experiment Goal

**Improve the trial prompt to produce higher-quality session summaries as measured by the evaluation rubric.**

The evaluation rubric (`evaluation_prompt.md`) scores summaries across five dimensions:

| Prefix | Dimension | What it measures |
|--------|-----------|-----------------|
| `str` | Structure | Correct sections, well-bounded scenes, clear progression |
| `rein` | Reincorporation | Only future-relevant details preserved |
| `nc` | Narrative Completeness | All materially important developments captured |
| `ni` | Narrative Impact | Focus on fiction-changing moments; mechanical/OOG noise excluded |
| `read` | Readability | Concise, self-contained, complete bullets |

Each criterion is scored 1–3 (3 = no flaws found). Scores are squared and summed per dimension to penalize low scores more heavily.

The goal of the current experiment is to iterate on `trial_prompt.md` to raise the aggregate squared-score totals across all five dimensions, with particular attention to dimensions where the prompt currently produces flawed output.
