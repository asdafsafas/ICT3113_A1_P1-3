---
type: concept
title: "Golden Test Set"
created: 2026-11-13
updated: 2026-11-13
tags:
  - ict3113
  - concept
  - golden-set
status: mature
related:
  - "[[Labelling Protocol]]"
  - "[[Inter-Annotator Agreement]]"
  - "[[Prediction Freeze]]"
sources:
  - "[[Golden Set Summary]]"
  - "[[Assignment 1 Brief]]"
complexity: intermediate
domain: "evaluation"
aliases:
  - "golden set"
  - "golden_set.csv"
---

# Golden Test Set

A hand-labelled set of tickets used as ground truth for accuracy, because the raw CFPB labels are noisy. **It must be built and committed before any model sees it**; otherwise the labels drift towards model outputs.

## Ours
- **195 tickets** (rows 3000–3199) in `golden/golden_set.csv`, plus **5 excluded**.
- Labelled in the local labeller app (`labeler/labeler.py`, http://localhost:8765). Two groups worked independently:
  - Group A: 2 labellers.
  - Group B: 3 labellers, which allows Fleiss' κ and 2-to-1 majorities.
- Rules: no conferring until the whole group is done, **no asking an AI**, only the in-app definitions, never look at `source_label`.
- 49 disagreements were resolved and recorded in `golden/pairs/`. The protocol was revised twice ([[Labelling Protocol]]).
- Frozen in tag `prediction-freeze` ([[Prediction Freeze]]).

Category counts and agreement figures: [[Golden Set Summary]].

## In Assignment 2
- It is **split by row parity**: odd rows are the tuning set, even rows the test set. Commit the split first.
- All reported A2 accuracy uses the test half only. Limits = top-model test accuracy −10 points overall and −15 points per category.
- Caveat stated in the brief: every model has already seen the full set in A1, so the test half is not new data.

Split computed from `golden/golden_set.csv` at ingest:

| Category | Tuning (odd) | Test (even) |
|---|---|---|
| Credit reporting | 22 | 20 |
| Bank account | 17 | 20 |
| Money transfer | 11 | 19 |
| Mortgage | 18 | **9** |
| Consumer loan | 13 | 11 |
| Credit card | 11 | **7** |
| Debt collection | **6** | 11 |
| **Total** | **98** | **97** |

> [!warning] Small cells
> - On the test set, one Credit card ticket is worth **14.3 points** and one Mortgage ticket **11.1 points**, so the −15-point per-category limit is close to a one-ticket margin there. Flag both as "too small for a fair per-category test".
> - The tuning set has only **6 Debt collection** tickets, a weak basis for any category-based escalation rule involving that class.
