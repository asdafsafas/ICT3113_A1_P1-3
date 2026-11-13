---
type: comparison
title: "Candidate Model Comparison"
created: 2026-11-13
updated: 2026-11-13
tags:
  - ict3113
  - comparison
  - models
status: mature
related:
  - "[[qwen2.5-0.5b]]"
  - "[[llama3.2-1b]]"
  - "[[qwen2.5-7b]]"
  - "[[Requirements]]"
sources:
  - "[[Accuracy Results]]"
  - "[[Load Test Results]]"
  - "[[Adaptive Stress Test]]"
  - "[[Smoke Tests]]"
subjects:
  - "[[qwen2.5-0.5b]]"
  - "[[llama3.2-1b]]"
  - "[[qwen2.5-7b]]"
dimensions:
  - "accuracy"
  - "latency"
  - "capacity"
  - "memory"
  - "licence"
verdict: "Recommend qwen2.5:7b: the only model meeting R1-R4; it fails R5 on Money transfer (66.7%), and no candidate meets every requirement."
---

# Candidate Model Comparison (Slides 5, 9, 10, 11)

All models are Q4_K_M, pulled from the Ollama library and pinned by digest in `models/models.lock.json`. The set spans the **<1B / ~1B** and **~7B** size classes. The same family at two sizes (Qwen 0.5B vs 7B) isolates the effect of size; the second family (Llama 1B) tests whether training matters as well as size. The two families differ in more than size, so equal quantisation does not make size the only difference. This was corrected on Slide 5.

| | [[qwen2.5-0.5b]] | [[llama3.2-1b]] | [[qwen2.5-7b]] |
|---|---|---|---|
| Params | 0.49B | 1.24B | 7.6B |
| Resident memory | 695 MiB | 1.29 GiB | 4.82 GiB |
| Licence | Apache 2.0 | Llama 3.2 Community | Apache 2.0 |
| **Accuracy (R4 ≥ 80%)** | 17.9% ❌ | 32.8% ❌ | **82.6% ✅** |
| Weakest category (R5 ≥ 70%) | 0% ❌ | 0% ❌ | MT 66.7% ❌ |
| Single-request p50 / p95 | 0.40 / 0.77 s | 0.46 / 0.84 s | 2.84 / 5.22 s |
| Peak POST p95 (R1 ≤ 30 s) | 1.02 s ✅ | 1.74 s ✅ | 6.06 s ✅ |
| Peak search p95 (R2 ≤ 1 s) | 0.33 s ✅ | 0.33 s ✅ | 0.46 s ✅ |
| Peak throughput, errors (R3) | ✅ 0% | ✅ 0% | ✅ 0% |
| Stress limit | not tested | not tested | 20 sustained, 22 mixed, 24 overloaded |

## Recommendation (A1)
**qwen2.5:7b.** It follows from the [[Misrouting vs Speed Position]]: it is the only model accurate enough to route reliably, and it has ample headroom at peak, with capacity ≥ 20/min against a 1.73/min peak, about 11×. **Stated plainly: no candidate meets R5.** Money transfer recall is 66.7% (20 of 30).

## Trade-off visible
Going from 0.5B to 7B costs ~7× the latency for +65 points of accuracy. On this hardware even the 7B is fast relative to the workload, so the brief's "large = too slow" trade-off barely bites at the client's rates. A2 makes speed the priority anyway.
