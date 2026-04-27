# prompt-autoresearch

A workbench for systematically improving an LLM system prompt by running it against fixed inputs, scoring the outputs against a rubric, and iterating. Each iteration tests one hypothesized change; the change is kept if the total score improves and reverted otherwise. A Claude Code subagent can drive the loop unattended.

Inspired by Andrej Karpathy's autoresearch concept.

---

## Table of contents

1. [Concepts](#concepts)
2. [Installation](#installation)
3. [Quick start: run the bundled example](#quick-start-run-the-bundled-example)
4. [Anatomy of an experiment directory](#anatomy-of-an-experiment-directory)
5. [Creating a new experiment](#creating-a-new-experiment)
6. [Running the auto-research loop with Claude Code](#running-the-auto-research-loop-with-claude-code)
7. [`settings.yaml` reference](#settingsyaml-reference)
8. [Starter `settings.yaml`](#starter-settingsyaml)
9. [Authoring an evaluation rubric](#authoring-an-evaluation-rubric)
10. [Authoring an evaluation prompt](#authoring-an-evaluation-prompt)
11. [How scoring works](#how-scoring-works)
12. [CLI reference](#cli-reference)
13. [Branches, commits, journal, and results.tsv](#branches-commits-journal-and-resultstsv)
14. [Troubleshooting](#troubleshooting)

---

## Concepts

The unit of work is an **experiment**. An experiment is a directory containing:

- a **trial prompt** — the system prompt you are trying to improve;
- a set of fixed **inputs** — sample user messages your prompt will be run against;
- an **evaluation prompt** — the system prompt for an evaluator LLM that judges the trial's output;
- an **evaluation rubric** — a JSON file listing the criteria the evaluator scores each output against;
- a `settings.yaml` — wires the above together, picks models, and sets evaluation breadth.

A single iteration of the **experiment loop** does the following:

1. Run the trial prompt against every input file, getting one output per input.
2. For each output, run the evaluator `evaluations_per_input` times against the rubric. Each run produces a 1/2/3 score for every criterion.
3. Aggregate scores into a single **total score** (see [How scoring works](#how-scoring-works)).
4. If the new total score beats the previous best, commit the trial prompt change to a per-experiment git branch. Otherwise, revert the change.
5. Append a journal entry and a `results.tsv` row recording the hypothesis, the change, and the result.

The **auto-research loop** is the same iteration repeated by an LLM agent that reads the journal, hypothesizes the next change, edits the trial prompt, runs the iteration, and repeats — until a perfect score is hit, the python app crashes, or the user interrupts.

---

## Installation

### Requirements

- Python ≥ 3.11
- [`uv`](https://docs.astral.sh/uv/) (used as both the package manager and the runner)
- `git` (every experiment commits to a per-day branch — git is required, not optional)
- API keys for whatever models you configure in `settings.yaml`. The current model registry supports OpenAI (`gpt-5.4`), Anthropic (`claude-opus-4-7`, `claude-opus-4-6`, `claude-sonnet-4-6`), and Google (`gemini/gemini-3.1-pro-preview`). All routing is done by [LiteLLM](https://github.com/BerriAI/litellm).
- (Optional, for the auto-research loop) [Claude Code](https://claude.com/claude-code).

### Clone & install

```bash
git clone <this-repo-url> prompt-autoresearch
cd prompt-autoresearch
uv sync                     # installs deps and creates the venv
```

### Configure API keys

Create a `.env` file in the project root (see `.env.example`):

```bash
OPENAI_API_KEY="sk-..."
ANTHROPIC_API_KEY="sk-ant-..."
GEMINI_API_KEY="..."
LOG_LEVEL=INFO
```

Only the keys for models you actually use need to be present. The CLI auto-loads `.env` at startup via `python-dotenv`.

### Verify

```bash
uv run prompt-autoresearch --help
```

You should see four subcommands: `perform-experiment`, `read-journal`, `report-key-files`, `init-agent`.

---

## Quick start: run the bundled example

The `experiments/test/` directory is a minimal experiment shipped with the repo for kicking the tires:

```bash
cd experiments/test
uv run prompt-autoresearch perform-experiment \
  --hypothesis "Baseline measurement, no change yet." \
  --change "None"
```

The first run takes a few minutes (it calls the trial and eval models). On completion, you will see (roughly):

```
Experiment Result: 87.3 of 110 possible.
EXPERIMENT_STATUS: improved total=87.3 max=110.0
```

`EXPERIMENT_STATUS:` is a machine-parseable sentinel — its statuses are documented in [the loop section](#running-the-auto-research-loop-with-claude-code).

A new git branch was created on your repo (`autoresearch/test_<YYYYMMDD>_000`), and `experiments/test/results.tsv` and `experiments/test/experiment_journal.md` were created/appended.

Re-run after a small edit to `experiments/test/trial_prompt.md` to see the keep/revert flow in action.

---

## Anatomy of an experiment directory

Each experiment lives at `experiments/<name>/`. The required files are:

```
experiments/<name>/
├── settings.yaml          # experiment configuration (REQUIRED)
├── trial_prompt.md        # the prompt being improved (REQUIRED)
├── evaluation_prompt.md   # system prompt for the evaluator LLM (REQUIRED)
├── evaluation_rubric.json # criteria the evaluator scores against (REQUIRED)
├── current_goal.md        # human-readable goal of this experiment (recommended)
├── inputs/                # one or more sample inputs (REQUIRED)
│   ├── 20260203.md
│   └── 20260225.md
├── experiment_journal.md  # auto-created on first run; agent's durable memory
├── results.tsv            # auto-created on first run; scoreboard
└── .claude/               # auto-created by `init-agent` when you scaffold the loop
    ├── agents/auto-researcher.md
    ├── commands/improve-prompt.md
    └── settings.json
```

`outputs/` and `logs/` (auto-created) are wiped at the start of every run — don't keep anything you care about there. `trial_prompt.md`, `evaluation_prompt.md`, and `evaluation_rubric.json` paths can be overridden in `settings.yaml`, but the defaults are recommended.

---

## Creating a new experiment

### 1. Scaffold the directory

```bash
mkdir -p experiments/my_experiment/inputs
cd experiments/my_experiment
```

### 2. Drop in some inputs

Place 2–8 representative sample inputs into `inputs/` as `.md` files. **Each input file becomes the user message** when the trial prompt runs. The filename is irrelevant; the contents are what matter. Keep the set small — every iteration runs the trial on every input.

### 3. Write the trial prompt

Put the system prompt you want to improve into `trial_prompt.md`. This is the prompt under iteration; the auto-researcher will edit it.

### 4. Write the evaluation rubric

Create `evaluation_rubric.json`. See [Authoring an evaluation rubric](#authoring-an-evaluation-rubric) — this is the most important file you'll write.

### 5. Write the evaluation prompt

Create `evaluation_prompt.md`. See [Authoring an evaluation prompt](#authoring-an-evaluation-prompt).

### 6. Write the goal note

Create `current_goal.md`. A few paragraphs explaining what this experiment is trying to achieve, so future you (and the auto-researcher) understand the intent. Optional but strongly recommended.

### 7. Write `settings.yaml`

See the [reference](#settingsyaml-reference) and [starter](#starter-settingsyaml) below.

### 8. Sanity-check with one manual run

```bash
cd experiments/my_experiment
uv run prompt-autoresearch perform-experiment \
  --hypothesis "Baseline measurement." \
  --change "None"
```

If this run produces a sensible total score and the journal/results files look right, you're ready to run the loop.

---

## Running the auto-research loop with Claude Code

### One-time scaffolding

From the experiment directory:

```bash
cd experiments/my_experiment
uv run prompt-autoresearch init-agent
```

This writes three files into `experiments/my_experiment/.claude/`:

| File                                       | Purpose                                                                              |
| ------------------------------------------ | ------------------------------------------------------------------------------------ |
| `agents/auto-researcher.md`                | The auto-researcher subagent definition (system prompt, tool restrictions, mode).    |
| `commands/improve-prompt.md`               | A `/improve-prompt` slash command that delegates to the subagent.                    |
| `settings.json`                            | Permission allowlist — only `Read(./**)`, `Edit(./trial_prompt.md)`, and `Bash(uv run prompt-autoresearch:*)`. |

Re-run with `--force` to regenerate them after upstream template changes.

### Starting the loop

```bash
cd experiments/my_experiment
claude
```

In the Claude Code prompt, type:

```
/improve-prompt
```

The auto-researcher subagent takes over, reading the journal, the rubric, and the current trial prompt. It then enters the loop: hypothesize → edit → run → parse status → repeat.

### Stop conditions

The loop runs until **exactly one** of:

- stdout from `perform-experiment` contains `EXPERIMENT_STATUS: perfect` (total score equals the max possible);
- the python app exits non-zero (a crash or unhandled error);
- you interrupt the agent (Esc / Ctrl-C in Claude Code).

### Status sentinels

Every `perform-experiment` run ends with one machine-parseable line:

```
EXPERIMENT_STATUS: <status> total=<x> max=<y>
```

| `<status>`   | Meaning                                                                       |
| ------------ | ----------------------------------------------------------------------------- |
| `perfect`    | Total score equals max — the loop stops here.                                 |
| `improved`   | New high score; the prompt change was committed.                              |
| `discarded`  | Score didn't improve; the prompt change was reverted (working copy is clean). |
| `unchanged`  | The prompt was not actually edited — likely an agent bug.                     |
| `crashed`    | An exception propagated; the prompt was reverted before failing.              |

The auto-researcher's system prompt explains how to react to each.

### Crash safety

If `perform-experiment` raises an exception **before** the keep/revert decision was made, the python app reverts `trial_prompt.md` automatically and emits `EXPERIMENT_STATUS: crashed`. Consequence: the next iteration always reads either the previous high-score commit or, on a clean baseline, your starting prompt — never a half-tested edit.

`KeyboardInterrupt` (Ctrl-C) is **not** caught — pressing Ctrl-C preserves the in-flight edit so you can inspect what the agent was trying.

---

## `settings.yaml` reference

Every experiment must have a `settings.yaml`. All keys are required unless marked optional.

| Key                                 | Type           | Description |
| ----------------------------------- | -------------- | ----------- |
| `evaluations_per_input`             | int (≥ 1)      | How many times the evaluator scores each trial output. Higher = lower noise but more API calls. **2 is shaky, 4–6 is reasonable, 8+ is statistically clean.** |
| `max_simultaneous_evaluations`      | int (≥ 1)      | Concurrency cap on evaluator API calls. Set to whatever your evaluator provider tolerates (often 5–20). |
| `high_score_threshold`              | float (≥ 0)    | Composite score (per criterion, scale 0–10) below which a criterion is reported in the per-run "low scoring tests" output. The auto-researcher uses these to choose what to attack next. **Reasonable default: 10** (every imperfect criterion is reported). |
| `paths.evaluation_prompt`           | str            | Path (relative to `settings.yaml`) of the evaluation prompt file. Conventionally `evaluation_prompt.md`. |
| `paths.trial_prompt`                | str            | Path of the trial prompt file. Conventionally `trial_prompt.md`. **The auto-researcher only has Edit permission on this file.** |
| `paths.eval_rubric`                 | str            | Path of the rubric JSON. Conventionally `evaluation_rubric.json`. |
| `paths.input_filenames`             | list[str] (≥1) | List of paths to the input files. Each file becomes a user message that the trial is run against. |
| `trial_model.name`                  | str            | Model ID for the trial. One of `gpt-5.4`, `claude-opus-4-7`, `claude-opus-4-6`, `claude-sonnet-4-6`, `gemini/gemini-3.1-pro-preview`. |
| `trial_model.effort`                | str            | Reasoning effort: `minimal`, `low`, `medium`, `high`, `xhigh`. Higher = better outputs, longer wait, more cost. |
| `eval_model.name`                   | str            | Model ID for the evaluator. **Use a different model** than the trial when possible — same-model self-eval is biased. |
| `eval_model.effort`                 | str            | Same scale as `trial_model.effort`. The evaluator should usually run at `medium` or `high`. |
| `eval_tags.input_start_tag`         | str            | Opening tag wrapping the input file content in the evaluator's user message. e.g. `"<session_logs>"`. |
| `eval_tags.input_end_tag`           | str            | Matching closing tag, e.g. `"</session_logs>"`. |
| `eval_tags.prompt_output_start_tag` | str            | Opening tag wrapping the trial output in the evaluator's user message. e.g. `"<summary>"`. |
| `eval_tags.prompt_output_end_tag`   | str            | Matching closing tag, e.g. `"</summary>"`. |

### Notes on tags

The evaluator's user message is constructed as:

```
{input_start_tag}{input_file_contents}{input_end_tag}{prompt_output_start_tag}{trial_output}{prompt_output_end_tag}
```

Choose tags that are:

- semantically meaningful for your domain (the evaluator LLM benefits from clear delimiters);
- **unlikely to appear** in either the input or the trial output (collisions confuse the evaluator).

XML-style tags work well. Generic `<input>`/`<output>` are fine but less clear than domain-specific ones.

### Cost & noise trade-off

Total LLM calls per iteration ≈ `len(input_filenames) × (1 + evaluations_per_input)`. With 4 inputs and `evaluations_per_input: 6`, every iteration is ≈ 28 calls. Multiply by the number of iterations the auto-researcher will run (often 20–100). Budget accordingly.

---

## Starter `settings.yaml`

Drop this into your new experiment dir and adjust:

```yaml
# Number of times the evaluator re-scores each trial output. Increase to reduce score noise.
evaluations_per_input: 4

# Concurrency cap on evaluator API calls.
max_simultaneous_evaluations: 8

# Composite-score floor below which a criterion is flagged as "low scoring" in run output.
# 10 means every imperfect criterion is flagged.
high_score_threshold: 10

paths:
  evaluation_prompt: "evaluation_prompt.md"
  trial_prompt: "trial_prompt.md"
  eval_rubric: "evaluation_rubric.json"
  input_filenames:
    - "inputs/example_01.md"
    - "inputs/example_02.md"

# The model under test. Pick whichever you're optimizing the prompt for.
trial_model:
  name: "claude-opus-4-7"
  effort: "medium"

# The judge. Use a DIFFERENT model from the trial whenever possible to reduce self-eval bias.
eval_model:
  name: "gpt-5.4"
  effort: "medium"

# Tags wrapping the input and trial output in the evaluator's user message.
# Pick tags that are semantically clear and unlikely to appear in your data.
eval_tags:
  input_start_tag: "<input>"
  input_end_tag: "</input>"
  prompt_output_start_tag: "<output>"
  prompt_output_end_tag: "</output>"
```

---

## Authoring an evaluation rubric

**This is the most important file in your experiment.** A bad rubric makes prompt improvement impossible — the auto-researcher will optimize toward a target that doesn't reflect what you actually want. A good rubric makes the loop converge.

### The rubric data structure

```json
{
    "scoring": {
        "scale": [1, 2, 3],
        "labels": {
            "1": "More than one non-trivial counterexample, or one major counterexample.",
            "2": "Exactly one non-trivial counterexample.",
            "3": "No non-trivial counterexamples."
        }
    },
    "dimensions": [
        {
            "name": "Completeness",
            "tag": "comp",
            "description": "Evaluates whether the cleaned transcript captures the in-game fiction at high resolution.",
            "criteria": [
                {
                    "id": "comp_01",
                    "text": "session_log includes separate entries for distinct in-game actions, observations, and state changes during live play, rather than collapsing them into broad summaries."
                },
                {
                    "id": "comp_02",
                    "text": "The logs preserve the player characters' explicit decisions, plans, intentions, stated thoughts, suspicions, and stated changes in understanding when present in the transcript."
                }
            ]
        }
    ]
}
```

Key invariants:

- The `scoring` block is reproduced into the evaluator's prompt verbatim — keep these labels stable.
- Each `dimension` has a `tag` (short prefix) and one or more `criteria`.
- Each `criterion.id` **must begin with `<dimension.tag>_`** (e.g., dimension tag `comp` → criterion ids `comp_01`, `comp_02`, …). The score parser uses this prefix to route scores back to the right dimension. If you typo this, the score is silently dropped and a warning is logged.
- `id` strings should be stable across rubric edits. The journal references them — renaming `comp_03` to `comp_99` makes historical entries hard to interpret.

### The 1-2-3 scoring scale

The evaluator does not subjectively rate "quality 1–10." It runs a procedure:

1. Look for **non-trivial counterexamples** to the criterion in the trial output.
2. Score by counterexample count: 0 → 3, 1 → 2, 2+ (or one major) → 1.

This is dramatically more reliable than free-form quality ratings because it gives the LLM judge a clear, falsifiable rule. Your rubric's job is to make the criteria such that "counterexample" is unambiguous.

### Designing good criteria

A criterion is good if a careful reader, given the trial output and the criterion text, can quickly find or rule out counterexamples. Practical rules:

1. **Phrase as a positive assertion.** "The summary includes X" — not "The summary should include X" and not "Does the summary include X?". The evaluator looks for violations of an assertion.

2. **One concept per criterion.** Bad: *"The summary is concise and accurate."* Good: split into two criteria, one on conciseness, one on accuracy. Compound criteria force the evaluator to make trade-offs internally.

3. **Falsifiable by location.** A counterexample should be pointable: a specific bullet, sentence, section, or omission. Criteria that can only be assessed gestalt-wise ("the tone is right") give noisy scores.

4. **Define your scope.** If a criterion is about omission, say so and clarify what kinds of omissions count. If structural ("must use bullet list of < 4 sentences each"), state the structure exactly. The session_summarize rubric in `experiments/session_summarize/evaluation_rubric.json` is a strong reference for criterion phrasing.

5. **Use scope notes for genuinely ambiguous concepts.** If a domain concept like "discovery" or "scene" needs careful definition, put the definition in `evaluation_prompt.md` (not in every criterion's text) and refer to it. The session_summarize evaluation prompt has a "Discovery scope note" and a "Clock scope note" — see those for the pattern.

6. **Avoid criteria that always max out.** If every output scores 3 on a criterion, it provides no improvement signal. Watch the first few iterations and rewrite or remove dead criteria.

7. **Avoid criteria that always min out.** If every output scores 1, either the criterion is impossible, or the trial prompt cannot perform the underlying task. Loosen, split, or fix the trial.

8. **Keep criteria stable, but iterate.** It is normal to tune the rubric over the first few experiments. After the loop has been running for a while, only change the rubric for compelling reasons — historical scores in the journal become harder to compare.

### Dimensions are bookkeeping

Dimensions exist to group related criteria for human readability. The total score is computed across all criteria globally — dimensions don't weight anything. Use whatever grouping makes the rubric easiest for *you* to read and maintain.

### How many criteria?

Five to fifty. Below five, the score is too coarse to guide iteration. Above fifty, the evaluator's context bloats and per-criterion noise rises. The two bundled examples have 17 (`clean_transcript`) and 53 (`session_summarize`) — both work, but the smaller one converges faster.

### Test your rubric before running the loop

Before turning the auto-researcher loose:

1. **Run the loop once with the existing trial prompt.** Look at the resulting `EXPERIMENT_STATUS:` line and the per-criterion low-score report. Do the low-scoring criteria match what *you* think is wrong with the output? If not, the rubric isn't measuring what you care about.
2. **Hand-write a deliberately bad output** and feed it through manually (you can edit `trial_prompt.md` to "Output the word 'no' regardless of input." and run a single iteration). Does the rubric score it abysmally? If a deliberately bad output gets a high score, the rubric has holes.
3. **Hand-write a deliberately good output** and check the inverse. If your hand-written gold standard scores poorly, your rubric over-penalizes legitimate outputs.

A rubric that fails either test will mislead the loop. Fix the rubric, not the trial prompt.

### Worked minimal example

Suppose you're improving a prompt that summarizes a meeting transcript into action items. A starter rubric:

```json
{
    "scoring": {
        "scale": [1, 2, 3],
        "labels": {
            "1": "More than one non-trivial counterexample, or one major counterexample.",
            "2": "Exactly one non-trivial counterexample.",
            "3": "No non-trivial counterexamples."
        }
    },
    "dimensions": [
        {
            "name": "Completeness",
            "tag": "comp",
            "description": "Every action item explicitly named in the transcript appears in the summary.",
            "criteria": [
                {
                    "id": "comp_01",
                    "text": "Every action item explicitly assigned to a named person in the transcript appears in the summary, attributed to the same person."
                },
                {
                    "id": "comp_02",
                    "text": "Every deadline explicitly stated for an action item in the transcript appears alongside that item in the summary."
                }
            ]
        },
        {
            "name": "Fidelity",
            "tag": "fid",
            "description": "The summary does not invent or distort.",
            "criteria": [
                {
                    "id": "fid_01",
                    "text": "Every action item in the summary is explicitly stated or directly implied in the transcript; no items are fabricated."
                },
                {
                    "id": "fid_02",
                    "text": "Owners and deadlines in the summary match the transcript without conflation across speakers or items."
                }
            ]
        },
        {
            "name": "Format",
            "tag": "fmt",
            "description": "Output is a clean, parseable list.",
            "criteria": [
                {
                    "id": "fmt_01",
                    "text": "The summary is a flat bullet list, one action item per bullet, with no nested sublists or extra prose."
                },
                {
                    "id": "fmt_02",
                    "text": "Each bullet uses the form '<owner>: <action> [by <deadline>]' or '<owner>: <action>' if no deadline was stated."
                }
            ]
        }
    ]
}
```

Six criteria, three dimensions. Max score = 60 (10 per criterion × 6). Each criterion is falsifiable: you can point at the offending bullet and explain what's missing or wrong. None overlap. None require subjective judgment about "quality."

---

## Authoring an evaluation prompt

`evaluation_prompt.md` is the **system prompt for the evaluator LLM**. It explains what the evaluator is doing, defines any ambiguous domain concepts, and sets the contract for how it should approach scoring.

### The contract: what gets stitched together

When `perform-experiment` runs, the evaluator's system prompt is built as:

```
{evaluation_prompt.md}
{fragments/evaluation_scoring.md}    <-- shared, auto-appended
{evaluation_rubric.json}             <-- raw JSON, auto-appended
```

The evaluator's user message is:

```
{input_start_tag}{input file contents}{input_end_tag}{prompt_output_start_tag}{trial output}{prompt_output_end_tag}
```

You author **only** `evaluation_prompt.md`. The scoring instructions and JSON output contract come from `fragments/evaluation_scoring.md` (a project-wide constant) — you don't need to repeat them.

### What to put in your evaluation prompt

A complete `evaluation_prompt.md` should:

1. **Identify the role.** "You are a careful evaluator of <thing>."
2. **Define the inputs.** Tell the evaluator what `<input_start_tag>...<input_end_tag>` contains and what `<prompt_output_start_tag>...<prompt_output_end_tag>` contains. **Use the actual tag strings you configured in `settings.yaml`.**
3. **State the task.** Evaluate the output against the criteria defined in the rubric (referenced as `RUBRIC_JSON` in the appended scoring fragment). Treat the input as ground truth / context only.
4. **Define ambiguous domain concepts.** If your rubric uses domain terms like "discovery", "scene", "action item", "side note", define them once here — not in every criterion. Add scope notes for edge cases.
5. **Calibrate counterexample sensitivity.** "Do not count tiny stylistic preferences" / "treat formatting violations as non-trivial." The defaults in the appended scoring fragment are general; your domain may need tightening.
6. **End at the rubric handoff.** The last section of your eval prompt should be `<RUBRIC_JSON>` (or similar) — the actual rubric JSON gets appended after this. The session_summarize evaluation prompt ends with the literal text `<RUBRIC_JSON>` followed by a blank line.

### Worked minimal example

For the meeting-action-items rubric above, a starter `evaluation_prompt.md`:

```markdown
<Task Overview>
You are a careful evaluator of meeting action-item summaries.

The user message contains:
1. A meeting transcript wrapped in <transcript>...</transcript>
2. An action-item summary wrapped in <summary>...</summary>

Use the transcript as ground truth. The summary is the object being evaluated.

Definitions:
- Action item: a specific task, decision, or commitment that someone in the meeting is expected to follow up on. Mere ideas, options discussed, or things merely mentioned do NOT count as action items unless someone agrees to do them.
- Owner: the person assigned responsibility for an action item; must be named explicitly in the transcript.
- Deadline: a date, time, or relative timeframe ("by Friday", "next sprint") explicitly tied to an action item in the transcript.

General rules:
- Treat each criterion in RUBRIC_JSON as a positive assertion about the summary.
- For each criterion, look for non-trivial counterexamples — concrete failures of the criterion that meaningfully harm quality.
- Do not penalize stylistic differences or alternative-but-equivalent phrasings.
- Do not count items as "missing" if no qualifying instance appears in the transcript.

Scope notes:
- An action item that is mentioned in passing but not assigned and not committed to is NOT a qualifying instance.
- A deadline phrased as a relative time ("end of week") is qualifying.
- The owner must be the person actually committed, not the person who proposed the task.

<RUBRIC_JSON>
```

The evaluator now has the role, the input format (matching the tags in `settings.yaml`), domain definitions, and scope rules. The scoring fragment and rubric JSON get appended after `<RUBRIC_JSON>`.

For a more substantial reference, read `experiments/session_summarize/evaluation_prompt.md`.

---

## How scoring works

Each criterion is rated 1–3 by the evaluator. Each output is evaluated `evaluations_per_input` times, so each criterion accumulates `evaluations_per_input × len(input_filenames)` raw scores. The criterion's **composite score** is:

```
composite = mean(1 + raw_score² for raw_score in scores)
```

| Raw scores         | Composite |
| ------------------ | --------- |
| All 1s             | 2.0       |
| All 2s             | 5.0       |
| All 3s             | **10.0**  |
| Half 2s, half 3s   | 7.5       |
| Half 1s, half 3s   | 6.0       |

The maximum composite per criterion is 10.0. The **total score** for the run is the sum of all composite scores. The maximum possible total is `10.0 × number_of_criteria`.

### Why squared?

Squaring the raw score before averaging makes "always 3" (10.0) much more valuable than "mostly 2 with the occasional 3" (~6). This deliberately incentivizes the auto-researcher to *finish* a criterion (drive it to consistent 3s) rather than half-fixing many criteria at once. It also means going from 1→2 is worth less than 2→3 — the loop will rationally prefer to push almost-perfect criteria over the line rather than rescue deeply broken ones.

If your iteration history shows the auto-researcher ignoring obviously broken criteria, this is why. You can either (a) wait — once the easier criteria are maxed, it will turn to the hard ones — or (b) tighten or split the criteria that always score 1 to make them tractable.

---

## CLI reference

All commands work either from the project root with `<experiment_name>` as a positional argument, or from inside an experiment directory (where `settings.yaml` is present) with no argument.

### `perform-experiment`

```bash
uv run prompt-autoresearch perform-experiment [EXPERIMENT_NAME] \
  --hypothesis "<text>" \
  --change "<text>"
```

Runs one full iteration: trial completions → evaluations → scoring → keep/revert → journal/results updates → status sentinel.

### `read-journal`

```bash
uv run prompt-autoresearch read-journal [EXPERIMENT_NAME] [-n N]
```

Prints the last `N` (default 10) journal entries. Used by the auto-researcher at the start of every iteration.

### `report-key-files`

```bash
uv run prompt-autoresearch report-key-files [EXPERIMENT_NAME]
```

Prints absolute paths to `results.tsv`, `experiment_journal.md`, and `trial_prompt.md`. Useful for orientation.

### `init-agent`

```bash
uv run prompt-autoresearch init-agent [EXPERIMENT_NAME] [--force]
```

Scaffolds `.claude/agents/auto-researcher.md`, `.claude/commands/improve-prompt.md`, and `.claude/settings.json` in the experiment directory. Refuses to overwrite existing files unless `--force` is passed.

---

## Branches, commits, journal, and results.tsv

### Per-experiment branches

The first `perform-experiment` run on a given day creates a branch named `autoresearch/<experiment_name>_<YYYYMMDD>_<NNN>` (e.g., `autoresearch/session_summarize_20260424_000`) and switches to it. Subsequent runs the same day stay on the same branch. Subsequent days create the next branch in sequence.

If the working tree is on `main` at the start of a run, it switches to the autoresearch branch. If it's already on a valid autoresearch branch for this experiment, it stays.

### Commits per iteration

Each kept iteration produces **two commits**:

1. **Prompt commit** — only `trial_prompt.md`, with the `--change` text as the commit message.
2. **Logs commit** — `experiment_journal.md` and `results.tsv`, with a generic `"Update experiment result logs for <name>."` message.

Discarded iterations produce **one commit**: just the logs commit. The prompt is reverted before logging, so `trial_prompt.md` stays untouched.

### `experiment_journal.md`

Append-only Markdown. Every iteration writes one section with date, branch, starting/experiment commit hashes, hypothesis, change, total score, decision (keep/discard), and the IDs of low-scoring criteria. **The journal is the auto-researcher's durable memory across context compaction** — it always re-reads the journal at the start of each iteration before hypothesizing.

### `results.tsv`

Append-only TSV scoreboard intended for humans (`column -t -s$'\t' results.tsv` to read in a terminal). One row per iteration, fields: commit hash, kept/discarded, change description, total score, count of low-scoring criteria, datetime.

---

## Troubleshooting

### "No experiment name provided and current directory does not contain settings.yaml"

You're running the CLI from a directory that's neither the project root nor an experiment directory. Either `cd` into the experiment dir, or pass the experiment name as an argument.

### `Evaluation output did not contain a JSON object; skipping scores`

The evaluator returned non-JSON, or the JSON was malformed. The criterion scores for that single evaluation are dropped (other evaluations still count). Common causes:

- The evaluator model isn't strong enough. Bump effort or switch to a more capable model.
- The evaluation prompt isn't crisp about the JSON contract. Make sure it ends with the rubric handoff (`<RUBRIC_JSON>` or equivalent) and doesn't add post-rubric instructions that contradict the auto-appended `evaluation_scoring.md`.
- The trial output contains tag strings that collide with `eval_tags` (e.g., your trial output literally contains `</output>` and your `prompt_output_end_tag` is `</output>`). Pick less generic tags.

### Scores are noisy run-over-run on the same prompt

Increase `evaluations_per_input`. Going from 2 to 6 typically cuts the standard deviation by half. Alternatively, use a stronger evaluator or raise `eval_model.effort`.

### Auto-researcher keeps making the same change

It probably can't see far enough back. Bump `read-journal -n` in the agent's loop (edit `.claude/agents/auto-researcher.md`), or condense old journal entries.

### "Refusing to overwrite existing files"

`init-agent` is conservative by design. Re-run with `--force` if you want to regenerate. **Note:** `--force` clobbers any manual edits you made to the agent's system prompt. Save them first.

### `EXPERIMENT_STATUS: unchanged`

The agent ran `perform-experiment` without actually editing `trial_prompt.md`. The python app detects an unchanged prompt and skips the keep/revert step. Diagnose by checking the agent's recent transcript — it likely planned a change but skipped the Edit tool call.

### `EXPERIMENT_STATUS: crashed`

The python app raised. The trial prompt was reverted automatically. Look at the traceback (printed before the sentinel) for the cause — most often, an API key issue, a malformed `settings.yaml`, or a network blip mid-run.

### Branch names are getting unwieldy

The `_<NNN>` suffix increments only when you create more than one branch on the same day for the same experiment (rare). If you really do have hundreds of branches, the index width grows automatically up to `BRANCH_LIMIT = 1000`. To clean up, delete old branches manually with `git branch -D`.
