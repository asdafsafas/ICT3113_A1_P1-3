---
type: concept
title: "Prediction Freeze"
created: 2026-11-13
updated: 2026-11-13
tags:
  - ict3113
  - concept
  - process
status: mature
related:
  - "[[Prediction Record]]"
  - "[[Golden Test Set]]"
  - "[[qwen2.5-3b]]"
sources:
  - "[[Project Docs]]"
  - "[[Codex Chat Summary]]"
complexity: basic
domain: "research integrity"
aliases:
  - "prediction-freeze"
  - "freeze tag"
---

# Prediction Freeze

The brief requires the golden set and the prediction record to be **committed before the first benchmark**. The commit history is the evidence that predictions came before measurements. They **cannot be revised afterwards**. Predictions are marked on specificity and on the later account of where they went wrong.

## A1 implementation
- Annotated git tag **`prediction-freeze`**, committed 2026-10-06 15:35 SGT (`git rev-list -n 1 prediction-freeze`).
- Contents: `golden/`, `planning/prediction-record.md`, `service/prompts/classify_v1.txt`, `models/models.lock.json` (4 models at the time), and the [[Smoke Tests]] evidence.
- After the tag, nobody edits `golden/`, the prediction record, `service/prompts/` or the lock file (`docs/pre-freeze-steps.md`).

> [!contradiction] Post-freeze edits
> Both the lock file (`scope_updated_at: 2026-10-07`) and `planning/prediction-record.md` were later edited to remove [[qwen2.5-3b]]. The record now opens with a note pointing to the tag, and the remaining three models' predictions are said to be unchanged. This needs open disclosure, not concealment.

## A2 equivalent
Before the first A2 benchmark, commit: the tuning/test **split**, the A2 **prediction record**, and the **written escalation rule**. A separate tag such as `a2-freeze` would follow the same pattern. This is a suggestion, not a requirement.
