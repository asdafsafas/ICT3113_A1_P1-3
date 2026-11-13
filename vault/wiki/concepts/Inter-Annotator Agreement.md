---
type: concept
title: "Inter-Annotator Agreement"
created: 2026-11-13
updated: 2026-11-13
tags:
  - ict3113
  - concept
  - statistics
status: developing
related:
  - "[[Golden Test Set]]"
  - "[[Requirements]]"
sources:
  - "[[Golden Set Summary]]"
complexity: intermediate
domain: "statistics"
aliases:
  - "Cohen's kappa"
  - "Fleiss' kappa"
---

# Inter-Annotator Agreement

These measure how far independent labellers agree beyond chance. Computed by `scripts/agreement.py` over all 8 labels (including None / unclear).

- **Cohen's κ** is used for two annotators. Group A: **0.735** (observed 78%).
- **Fleiss' κ** is used for three or more. Group B: **0.778**, with pairwise Cohen's κ of 0.826, 0.763 and 0.745.
- Both are "substantial" agreement on the Landis–Koch scale (0.61–0.80).

## Why it mattered downstream
- The A1 brief treats perfect agreement with no recorded resolutions as suspicious. High but imperfect agreement is evidence of care.
- **R4 (≥ 80%) was anchored on human agreement:** labellers agreed with each other on 78–85% of tickets before discussion, so 80% asks a model to "match a single trained human". See [[Requirements]].
- [[qwen2.5-7b]] at 82.6% therefore performs about as well as an individual labeller did against a peer. Individual labellers matched the *final* golden label 83–96% of the time.
