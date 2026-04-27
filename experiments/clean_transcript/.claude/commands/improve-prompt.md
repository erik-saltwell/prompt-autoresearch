---
description: Begin an unattended autoresearch loop in this experiment directory.
---

Use the auto-researcher subagent to begin an unattended improvement loop on this experiment's trial prompt. Continue iterating until you see `EXPERIMENT_STATUS: perfect` in stdout, the python app exits with a non-zero status, or I interrupt you. Do not stop earlier.

As an example use case, a user might leave you running while they sleep. If each experiment takes you ~10 minutes then you can run approx 6/hour, for a total of about 60 over the duration of the average human sleep. The user then wakes up to experimental results, all completed by you while they slept!
