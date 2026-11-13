---
type: entity
title: "llama3.2-1b"
created: 2026-11-13
updated: 2026-11-13
tags:
  - ict3113
  - entity
  - model
status: mature
related:
  - "[[qwen2.5-7b]]"
  - "[[qwen2.5-0.5b]]"
  - "[[Candidate Model Comparison]]"
sources:
  - "[[Accuracy Results]]"
  - "[[Load Test Results]]"
  - "[[Smoke Tests]]"
entity_type: product
role: "Second-family small A1 candidate; possible A2 cascade first stage"
first_mentioned: "[[Prediction Record]]"
aliases:
  - "llama3.2:1b-instruct-q4_K_M"
---

# llama3.2:1b-instruct-q4_K_M

| Pin | Value |
|---|---|
| Tag | `llama3.2:1b-instruct-q4_K_M` |
| Digest | `22bc6b92eb0160c4629782fca05a9032c59d306ab2058b7dacc8a4644fbafa02` |
| Params / quant | 1.2B, Q4_K_M, family `llama` |
| Size | 808 MB on disk; **1.29 GiB resident** |
| Licence | **Llama 3.2 Community Licence**, which allows commercial use under conditions (see Meta's GitHub, cited on Slide 12) |

## Measured (A1)
- **Accuracy 32.8%** (predicted 45–65%). It defaults to **Credit reporting** (~121 of 195 answers, derived): CR recall is 85.7% but precision only 29.8%.
- **High precision, low recall** elsewhere: Credit card 100%/16.7%, Money transfer 100%/3.3%, Mortgage 88.9%/29.6%, Bank account 85.7%/16.2%.
- Accuracy-run p50 0.46 s, p95 0.84 s. Load-test p50 0.72–0.86 s, 0% errors.

## Implication
It is the better cascade first stage of the two small models: when it says Mortgage, Credit card, Bank account or Money transfer, it is usually right. But it says those labels rarely, so escalation would be high. See [[Assignment 2 Planning]].
