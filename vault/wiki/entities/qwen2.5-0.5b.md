---
type: entity
title: "qwen2.5-0.5b"
created: 2026-11-13
updated: 2026-11-13
tags:
  - ict3113
  - entity
  - model
status: mature
related:
  - "[[qwen2.5-7b]]"
  - "[[llama3.2-1b]]"
  - "[[Candidate Model Comparison]]"
sources:
  - "[[Accuracy Results]]"
  - "[[Load Test Results]]"
  - "[[Smoke Tests]]"
entity_type: product
role: "Smallest A1 candidate; possible A2 cascade first stage"
first_mentioned: "[[Prediction Record]]"
aliases:
  - "qwen2.5:0.5b"
---

# qwen2.5:0.5b

| Pin | Value |
|---|---|
| Tag | `qwen2.5:0.5b` |
| Digest | `a8b0c51577010a279d933d14c2a8ab4b268079d44c5c8830c0a93900f1827c67` |
| Params / quant | 494M, Q4_K_M, family `qwen2` |
| Size | 398 MB on disk; **695 MiB resident** |
| Licence | Apache 2.0 |

## Measured (A1)
- **Accuracy 17.9%**, below the predicted 35–55% range. **0% recall** on Debt collection, Mortgage, Consumer loan and Money transfer.
- It labels almost everything **Credit card** (~155 of 195 answers, derived). That is why Credit card recall is 94.4% while precision is only 11%.
- Accuracy-run p50 0.40 s, p95 0.77 s. Load-test p50 ~0.7 s, 0% errors.

## Implication
As a cascade first stage, its answers carry almost no signal beyond "probably not Credit card". A category-based acceptance rule built on it would accept very few tickets correctly. See [[Cascade Classification]].
