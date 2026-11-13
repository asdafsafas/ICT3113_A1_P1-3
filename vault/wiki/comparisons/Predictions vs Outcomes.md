---
type: comparison
title: "Predictions vs Outcomes"
created: 2026-11-13
updated: 2026-11-13
tags:
  - ict3113
  - comparison
  - predictions
status: mature
related:
  - "[[Prediction Record]]"
  - "[[Accuracy Results]]"
  - "[[Load Test Results]]"
  - "[[Adaptive Stress Test]]"
sources:
  - "[[Prediction Record]]"
  - "[[Accuracy Results]]"
  - "[[Load Test Results]]"
  - "[[Adaptive Stress Test]]"
  - "[[Smoke Tests]]"
subjects:
  - "[[Prediction Record]]"
  - "[[Accuracy Results]]"
dimensions:
  - "accuracy"
  - "latency"
  - "capacity"
  - "bottleneck"
  - "category difficulty"
verdict: "Bottleneck right; latency ~2x too pessimistic; 7B capacity ~2.3x too low; small-model accuracy far too optimistic; 7B weak spot was Money transfer, not Debt collection."
---

# Predictions vs Outcomes (Slide 11)

✅ = held · ❌ = wrong · ◐ = partly held. Where the "outcome" is computed rather than taken from a results file, it is marked *derived*.

## Accuracy

| Prediction | Outcome | |
|---|---|---|
| 0.5B 45% (35–55) | **17.9%** | ❌ 27 points too high |
| 1B 55% (45–65) | **32.8%** | ❌ 22 points too high |
| 7B 78% (72–84) | **82.6%** | ✅ inside the range, above the point |
| No model passes R4 | 7B passes R4 | ❌ |
| No model passes R5 | None passes R5 | ✅ |
| 7B weakest: Debt collection / Consumer loan, 55–68% | DC **82.4%**, CL 70.8%; weakest is **Money transfer 66.7%** | ❌ wrong category |
| 0.5B: Credit reporting > 35% of answers | CR ~20% (derived); **Credit card ~79%** | ❌ wrong default label |
| ≥ 25% of Money transfer tickets → Bank account (7B) | MT recall 66.7%, Bank account precision 76% | ◐ consistent (check the confusion matrix) |
| Mortgage and CR recall ≥ 90% (7B) | Mortgage 92.6% ✅, CR 81.0% ❌ | ◐ |
| CR precision ≤ 75% (7B) | **87.2%** | ❌ |
| 0.5B → 7B: 7.6× latency for +33 points | 7.1× latency (2.84 / 0.40) for **+64.7 points** | ❌ accuracy gain was far larger |

## Latency and capacity

| Prediction | Outcome | |
|---|---|---|
| Single-request p50: 0.8 / 0.9 / 6.1 s | Accuracy run: **0.40 / 0.46 / 2.84 s** | ❌ ~2× too slow |
| 7B p95 at peak 9–11 s | **6.06 s** (5.55–6.71) | ❌ too pessimistic, but R1 passes either way |
| R1, R2, R3 pass for all | All pass, 0% errors | ✅ |
| Search p95 < 100 ms at peak | **0.33–0.46 s** | ❌ (R2 still passes) |
| 7B capacity ~9.4/min; 9.6/min doesn't drain | 9.6/min sustained; **20 sustained, 22 mixed, 24 overloaded** | ❌ ~2.3× too low |
| Throughput plateaus while the offered rate rises; latency grows linearly | At 24/min throughput ~21.6–23/min, with backlog and p50 growing | ✅ |
| Errors only after the 600 s timeout | 0 errors even at overload | ✅ |
| Thread-pool (40) starves search under stress | Backlog peaked at ~27 and search p95 ≤ 0.6 s | ◐ not triggered, so untested |
| Run-to-run p50 spread < 10% | 7B peak 3.69–3.78 ✅; 0.5B average 0.65–0.84 (~26%) ❌ | ◐ |

## Bottleneck

| Prediction | Outcome | |
|---|---|---|
| Ollama prompt eval is the bottleneck | Prompt eval is 80–90% of time; Ollama ~1000% CPU | ✅ |
| Ollama ≥ 900% CPU, triage < 10% | ~1000% vs 0–1% | ✅ |
| Memory flat at model size | 7B 4.82 GiB (smoke) | ✅ (check the stats CSVs for growth) |

## Why the predictions were wrong
1. **Latency:** the estimates were built from the *prototype* prompt (~300 tokens vs ~100 for `classify_v1.txt`), on top of a ±30% band. That bias was stated in the record but not corrected. Faster latency in turn explains the higher 7B capacity (60 ÷ 2.84 ≈ 21/min).
2. **Small-model accuracy:** the predictions assumed the small models would behave like weaker versions of the 7B. Instead they **collapsed onto one label** (0.5B → Credit card, 1B → Credit reporting). Without category definitions in the prompt, the small models had nothing to anchor the less obvious names to.
3. **The 7B's weak category:** the 7B handled "who is the complaint against" better than feared. The Bank account ↔ Money transfer boundary, which also split Group B most often, proved harder.
