---
type: entity
title: "qwen2.5-3b"
created: 2026-11-13
updated: 2026-11-13
tags:
  - ict3113
  - entity
  - model
  - dropped
status: seed
related:
  - "[[Prediction Freeze]]"
  - "[[Candidate Model Comparison]]"
sources:
  - "[[Codex Chat Summary]]"
  - "[[Smoke Tests]]"
entity_type: product
role: "Fourth candidate in the frozen prediction record; dropped before measurement"
first_mentioned: "[[Codex Chat Summary]]"
aliases:
  - "qwen2.5:3b"
---

# qwen2.5:3b (dropped)

- It was in the **original four-model lock and prediction record** at tag `prediction-freeze`, and in the prototype smoke tests and a dry run.
- It was **dropped** because its licence did not suit a commercial client. This is constraint C2 in [[Requirements]].
- Its predictions were deleted from the working `planning/prediction-record.md` after testing began. `models/models.lock.json` notes that "the original pre-benchmark four-model lock remains at tag prediction-freeze".
- Slide 5 had all mention of it removed (`slides/pending-changes.md`).

> [!warning] Disclosure
> The brief forbids revising the prediction record after benchmarking starts. The [[Codex Chat Summary]] audit says to present the tagged four-model record honestly and explain why the 3B was dropped. Removing it from the slides conflicts with that advice. See [[Prediction Freeze]].

**A2 note:** A2 says "no new models may be introduced". Whether a pinned-but-unmeasured A1 candidate counts is unclear. It is excluded anyway on licence grounds.
