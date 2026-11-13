---
type: source
title: "Codex Chat Summary"
created: 2026-11-13
updated: 2026-11-13
tags:
  - ict3113
  - source
  - process
status: mature
related:
  - "[[Prediction Freeze]]"
  - "[[Evidence Reconciliation]]"
  - "[[Adaptive Stress Test]]"
sources:
  - "docs/assignment-1-chat-summary.md"
source_type: transcript
author: "Ridwan (summary of a chat with Codex)"
date_published: 2026-10-09
url: ""
confidence: medium
key_claims:
  - "Three active members split the work: Ridwan JMeter, Tze Han models + SUT Mac, Zong Han requirements/workload/predictions"
  - "prediction-freeze tag contains four candidates incl. qwen2.5:3b; the working record was edited later, which must be disclosed"
  - "Audit found slides 5, 7-9 and 11 needed corrections (adaptive result, Qwen vs Llama family wording, throughput window, p99 spread)"
  - "Reporting rule: distinguish measured, predicted, post-hoc estimate, and not-observed-within-range"
---

# Codex Chat Summary (process record)

Source: `docs/assignment-1-chat-summary.md`. It summarises one member's chat with an AI assistant (Codex) during A1. It records the process and does not replace the team's methodology.

## Roles in practice
- [[Ridwan]]: JMeter load and stress testing, evidence, reconciliation.
- [[Tze Han]]: model selection and download; operated the **SUT Mac** (Docker + Ollama + triage).
- [[Zong Han]]: requirements, workload model, predictions.

> [!note] Team plan now matches
> `docs/team-plan.md` was updated on 2026-11-13 to this split, with all five members recorded as equal contributors. See [[Team P1-3]].

## Notable events
- **Branches:** work on a Ridwan branch, then `attempt-2` for adaptive stress. Tze Han's SUT evidence overlapped with Ridwan's untracked files; all 40 overlapping files were byte-identical and merged cleanly (commit `aa1c5c1`).
- **Datasets:** golden set for accuracy only; the ~800 tickets in rows 3200–3999 for load and stress only.
- **Dry runs:** first against a mock, then against the real service. A dry run that made the 3B look faster than the 0.5B was correctly dismissed as warm-up noise.
- **Model set:** [[qwen2.5-3b]] dropped because its licence did not suit the commercial client (C2).
- **Stress testing:** the original ramp found no limit, so the [[Adaptive Stress Test]] was built and found the 22–24/min bracket. 1,468 samples reconciled with zero missing IDs.

## Audit findings for the final deck
- Slides 7–9 and 11 still described the old stress test ("no limit to 12/min, ~19/min estimate"). *Later marked done in `slides/pending-changes.md`.*
- Slide 5 wrongly implied that equal Q4_K_M quantisation made size the only difference, but Qwen and Llama are different families.
- Slide 9's `Done/min` window (first request → last completion) inflates throughput.
- Slide 9 lacks spread for p99 and throughput.
- The AI acknowledgement must separate the human labels from AI help with resolution docs.

## Reporting rule
Always label a figure as **measured**, **predicted before testing**, **estimated after testing**, or **limit not observed in the tested range**. See [[Evidence Reconciliation]].
