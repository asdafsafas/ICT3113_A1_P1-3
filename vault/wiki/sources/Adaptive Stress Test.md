---
type: source
title: "Adaptive Stress Test"
created: 2026-11-13
updated: 2026-11-13
tags:
  - ict3113
  - source
  - stress-test
  - results
status: mature
related:
  - "[[Load Test Results]]"
  - "[[Ollama Bottleneck]]"
  - "[[qwen2.5-7b]]"
sources:
  - "docs/adaptive-stress-test.md"
  - "results/load/qwen2.5-7b/adaptive-stress/adaptive-stress-summary.md"
  - "docs/actual-jmeter-test.md"
source_type: data
author: "Team P1-3 (Ridwan: JMeter side; Tze Han: SUT side)"
date_published: 2026-10-09
url: ""
confidence: high
key_claims:
  - "qwen2.5:7b sustained 20 POST/min, was mixed at 22/min, and was overloaded twice at 24/min (7 searches/min throughout)"
  - "Auto-generated bracket: above 22 and at or below 24/min; cautious slide wording: 20 sustained, 22 mixed, 24 overloaded"
  - "No errors at any of the five reportable rates: overload showed as backlog and latency growth"
  - "All 1,468 JMeter samples in the five attempts reconcile with service logs"
---

# Adaptive Stress Test (the A1 stress limit)

This is the stress test that found the system's limit for [[qwen2.5-7b]]. The initial ramp to 12/min found none (see [[Load Test Results]]).

## Procedure
- **Two Macs:** Tze Han's SUT Mac runs Docker, Ollama, triage and a token-protected **evidence agent** (`scripts/adaptive_stress_sut.py`). Ridwan's Mac runs JMeter (`scripts/run_adaptive_stress.py`) and drives the agent over TCP 8765.
- The rate starts at 20 POST/min and rises in steps of 2 up to a cap of 24, with **7 searches/min** at every step. Each attempt runs 10 min active + 10 min drain.
- Before every attempt: restart Ollama and triage, recreate the empty DB, warm up with invented text, delete the warm-up row, and verify the digest.
- The first overloaded rate is repeated after a full reset. The suite stops only when both attempts are overloaded.

## Stop rule (fixed before running)
A rate counts as overloaded if any of these holds:
1. POST errors > 1%.
2. ≥ 15% of offered POSTs (minimum 5) are still in flight at the end of the active period.
3. The queue grows from midpoint to end **and** last-half throughput < 90% of offered.
4. The queue grows **and** late-half p50 ≥ 1.5× early-half p50 and at least 2 s more.

High CPU alone is not treated as saturation.

## Results

| Rate/min | Attempt | Result | p50 s | p95 s | p99 s | Backlog mid/end | Last-half thr/min |
|---|---|---|---|---|---|---|---|
| 20 | 1 | SUSTAINED | 9.05 | 21.83 | 25.27 | 1/4 | 20.8 |
| 22 | 1 | OVERLOADED | 16.21 | 31.90 | 38.47 | 8/12 | 21.6 |
| 22 | 2 | SUSTAINED | 25.33 | 43.97 | 46.55 | 10/7 | 22.4 |
| 24 | 1 | OVERLOADED | 26.62 | 53.82 | 64.13 | 15/24 | 23.0 |
| 24 | 2 | OVERLOADED | 34.01 | 71.66 | 75.02 | 13/27 | 22.8 |

Errors were 0% in every row. Search p95 stayed ≤ 0.6 s throughout, so the predicted thread-pool starvation never happened: the backlog peaked at about 27, below 40.

## Interpretation
- The generated summary reports a **bracket: > 22 and ≤ 24/min**.
- `docs/actual-jmeter-test.md` asks the slides to use the **more cautious wording**: 20/min sustained, 22/min mixed, 24/min overloaded twice. Keep the raw decision record unchanged.
- The earlier `adaptive_14rpm_s7_run1` had connection failures and socket timeouts. It is kept as diagnostic evidence and excluded from the conclusion. An orphan `service-adaptive_20rpm_s7_run2.jsonl` has no matching JTL and must not be reported.

> [!key-insight] Prediction was ~2.4× too pessimistic
> The [[Prediction Record]] put 7B capacity at **~9.4/min**, assuming a ~6.4 s service time. The measured single-request p50 was ~2.8 s, and 60 ÷ 2.84 ≈ 21/min, which matches the measured 20–24 bracket. The over-long prototype prompt behind the latency estimate explains most of the gap. See [[Predictions vs Outcomes]].
