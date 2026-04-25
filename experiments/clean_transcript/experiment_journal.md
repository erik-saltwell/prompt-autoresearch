# Experiment Journal

---

## Baseline Run

- **Date/time:** 2026-04-24T10:19:55-07:00
- **Branch:** autoresearch/apr24
- **Commit:** 2ad604c
- **Hypothesis:** N/A — baseline measurement
- **Change:** None
- **Result summary:**
  - Total score: 100.2 / 110
  - Low-scoring criteria (5):
    - `comp_01` 9.6 — recap_log collapses multiple events into vague summary statements
    - `comp_02` 7.9 — session_log collapses distinct in-game beats instead of separating them
    - `comp_03` 6.5 — player character decisions, plans, intentions, stated thoughts, suspicions, changes in understanding not fully preserved
    - `corr_02` 8.2 — uncertainty and attribution not always preserved with cautious wording
    - `struct_03` 8.0 — some log entries are not complete standalone sentences (notes, fragments, verbatim utterances)
- **Decision:** keep (baseline)
- **Next hypothesis:** comp_03 is the biggest gap (6.5). The trial prompt mentions "Thoughts, Feelings, Intentions, and Suspicions" but may not be explicit enough about capturing stated decisions and changes in understanding. Strengthen the instruction to ensure these are captured as separate entries.

---

## Iteration 1

- **Date/time:** 2026-04-24T10:58:06-07:00
- **Branch:** autoresearch/apr24
- **Starting commit:** 2ad604c
- **Experiment commit:** 5774533
- **Hypothesis:** comp_03 (6.5) is caused by stated thoughts, decisions, and changes in understanding being merged or dropped. Strengthening sections 5 & 6 and adding a Critical Requirements bullet should force each as its own entry.
- **Change:** Added Critical Requirements bullet: "Treat each stated thought, suspicion, stated change in understanding, decision, and explicit intention as a required entry." Expanded section 5 to include "changes in understanding" and removed "only when" hedging. Expanded section 6 to require every in-character decision/plan as its own entry.
- **Result summary:**
  - Total score: 102.1 / 110 (↑ from 100.2)
  - Low criteria (7, up from 5):
    - `comp_01` 9.2 (was 9.6 — slight regression)
    - `comp_02` 9.2 (was 7.9 — improved)
    - `comp_03` 9.2 (was 6.5 — major improvement)
    - `comp_04` 9.6 (new low — fictional consequences)
    - `corr_01` 9.6 (new low — hallucination check)
    - `corr_02` 8.1 (was 8.2 — essentially flat)
    - `struct_03` 7.0 (was 8.0 — regressed)
- **Decision:** keep — total score improved
- **Why it helped:** Forcing granular entries for thoughts/decisions directly addressed comp_03. The side effect is more entries overall, which may have caused some to come out as fragments (struct_03 drop) or pushed the model to over-include, triggering corr_01.
- **Next hypothesis:** struct_03 dropped to 7.0 — entries are coming out as fragments, notes, or verbatim utterances rather than complete standalone sentences. Add a stronger formatting rule requiring every entry to be a complete sentence in narrator past tense, with an example of the difference between a fragment and a proper entry.

---

## Iteration 2

- **Date/time:** 2026-04-24T11:36:44-07:00
- **Branch:** autoresearch/apr24
- **Starting commit:** 5774533
- **Experiment commit:** 9446d37 (discarded)
- **Hypothesis:** struct_03 (7.0) is caused by entries being written as fragments or verbatim utterances. Adding an explicit Entry Format section with wrong/right examples would fix it.
- **Change:** Added "Entry Format" section with rules requiring complete sentences and wrong/right examples.
- **Result summary:**
  - Total score: 102.0 / 110 (↓ from 102.1)
  - Low criteria (6 vs 7 before, but total score slightly lower):
    - `comp_01` 9.2 (same)
    - `comp_02` 8.2 (regressed from 9.2)
    - `corr_01` 9.6 (same)
    - `corr_02` 8.2 (same)
    - `focus_02` 9.6 (new low)
    - `struct_03` 7.0 (unchanged — no improvement)
- **Decision:** discard — total score marginally lower, struct_03 unaffected
- **Why it hurt:** The Entry Format rules didn't address the actual struct_03 causes. Reading eval outputs revealed the real problems: (1) recap_log entries using "During the recap, the group recalled that..." are penalized as table-process language rather than in-fiction narration; (2) "John's character" fallback when character name unknown is penalized as a player-facing label.
- **Next hypothesis:** Change recap entry format from "the group recalled that..." to past-perfect in-fiction narration ("Prior to this session, [character] had..."). Change the unknown-name fallback away from "John's character" to an in-fiction description ("an unidentified figure", "the character whose name was not stated", etc.).

---

## Iteration 3

- **Date/time:** 2026-04-24T12:11:45-07:00
- **Branch:** autoresearch/apr24
- **Starting commit:** 5774533
- **Experiment commit:** 78776ac
- **Hypothesis:** struct_03 (7.0) is caused by: (1) recap entries using "the group recalled that..." table-process framing; (2) "John's character" player-facing labels. Switching to past-perfect in-fiction recap narration and in-fiction character descriptions would fix both.
- **Change:** Recap entries now use past-perfect in-fiction framing ("had previously..."). Unknown characters now described by in-fiction role/traits instead of "John's character." Schema example updated to match.
- **Result summary:**
  - Total score: 102.2 / 110 (↑ from 102.1)
  - Low criteria (7):
    - `comp_01` 9.6 (was 9.2 — improved)
    - `comp_02` 9.2 (same)
    - `comp_03` 7.1 (was 9.2 — major regression)
    - `comp_04` 8.9 (was 9.6 — regression)
    - `corr_02` 9.2 (was 8.1 — improved)
    - `focus_01` 9.6 (new low)
    - `focus_02` 9.2 (was 9.6 — slight regression)
    - `struct_03` 9.2 (was 7.0 — major improvement — target achieved)
- **Decision:** keep — total score marginally higher
- **Why it helped/hurt:** The recap and character-reference fixes resolved struct_03 completely. But comp_03 regressed significantly. Likely cause: removing "John's character" fallback leaves the model uncertain about how to refer to unnamed characters, so it drops their stated thoughts/decisions rather than attempt in-fiction descriptions.
- **Next hypothesis:** Address comp_03 regression (7.1) by explicitly reinforcing that even when a character's name is unknown, their stated thoughts/decisions/intentions must still be captured using the in-fiction description. Possibly also tackle comp_04 (8.9) — fictional consequences of attempts.

