---
type: entity
title: "qwen2.5-7b"
created: 2026-11-13
updated: 2026-11-13
tags:
  - ict3113
  - entity
  - model
status: mature
related:
  - "[[qwen2.5-0.5b]]"
  - "[[llama3.2-1b]]"
  - "[[Candidate Model Comparison]]"
  - "[[Adaptive Stress Test]]"
sources:
  - "[[Accuracy Results]]"
  - "[[Load Test Results]]"
  - "[[Smoke Tests]]"
entity_type: product
role: "Largest A1 candidate; recommended model; A2 reference (top model)"
first_mentioned: "[[Prediction Record]]"
aliases:
  - "qwen2.5:7b"
---

# qwen2.5:7b

| Pin | Value |
|---|---|
| Tag | `qwen2.5:7b` |
| Digest | `845dbda0ea48ed749caafd9e6037047aa19acfcfd82e704d7ca97d631a0b697e` |
| Params / quant | 7.6B, Q4_K_M, family `qwen2` |
| Size on disk | 4.68 GB; **4.82 GiB resident** |
| Licence | Apache 2.0 |

## Measured (A1)
- **Accuracy 82.6%** on 195 tickets: passes R4, **fails R5** (Money transfer recall 66.7%). Strongest categories: Bank account 94.6% and Mortgage 92.6%. See [[Accuracy Results]].
- Accuracy-run latency **p50 2.84 s, p95 5.22 s**. Smoke fit: 621 ms + 2.20 ms/char.
- Load tests: POST p50 3.4–3.7 s, p95 6.1–6.7 s, 0% errors at 1.45, 1.73 and 3.5/min. See [[Load Test Results]].
- **Stress limit:** 20/min sustained, 22 mixed, 24 overloaded (with 7 searches/min). See [[Adaptive Stress Test]].
- Uses ~1000% CPU (all 10 VM CPUs) during a request.

## Predicted vs measured
Predicted 78% accuracy and 6.1 s p50 with ~9.4/min capacity. Accuracy came in higher, latency about 2× lower, and capacity about 2.3× higher. See [[Predictions vs Outcomes]].

## Role
- **A1 recommendation**: the best candidate, though it does not meet every requirement.
- **A2 top model**: its test-set accuracy sets the limits, and the cascade's large stage would be this model. See [[Assignment 2 Planning]].
