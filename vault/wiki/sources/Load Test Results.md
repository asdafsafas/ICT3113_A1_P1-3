---
type: source
title: "Load Test Results"
created: 2026-11-13
updated: 2026-11-13
tags:
  - ict3113
  - source
  - load-test
  - results
status: developing
related:
  - "[[Open-Loop Load Testing]]"
  - "[[Adaptive Stress Test]]"
  - "[[Candidate Model Comparison]]"
sources:
  - "results/load/"
  - "scripts/summarise_jtl.py"
source_type: data
author: "Team P1-3; table generated at ingest by scripts/summarise_jtl.py"
date_published: 2026-10-09
url: ""
confidence: high
key_claims:
  - "All three models: 0% errors and POST p95 <= 2 s (small models) or <= 6.7 s (7B) at average, peak and beyond-peak rates"
  - "Search p95 0.22-0.56 s across standard configurations"
  - "Initial 7B stress (ramp to 12/min, 7.2 and 9.6 confirmations) found no limit"
---

# Load Test Results (Slide 9)

There is **no committed summary file**. At ingest (2026-11-13) this table was produced by running `scripts/summarise_jtl.py results/load --label ...` over the raw `.jtl` files, with no `--skip-s`. Values are the mean (min–max) across 3 runs, and each run is 10 min.

## POST /tickets, standard matrix

| Model | Rate | Samples | p50 s | p95 s | p99 s | Err |
|---|---|---|---|---|---|---|
| [[qwen2.5-0.5b]] | 1.45 | 14 | 0.77 (0.65–0.84) | 1.95 (1.19–3.33) | 1.95 | 0% |
| | 1.73 | 17 | 0.67 (0.63–0.69) | 1.02 (1.00–1.04) | 1.02 | 0% |
| | 3.5 | 35 | 0.68 (0.60–0.81) | 1.27 (1.16–1.40) | 1.65 | 0% |
| [[llama3.2-1b]] | 1.45 | 14 | 0.76 (0.66–0.93) | 1.46 (1.19–1.70) | 1.46 | 0% |
| | 1.73 | 17 | 0.72 (0.63–0.79) | 1.74 (1.07–2.88) | 1.74 | 0% |
| | 3.5 | 35 | 0.86 (0.79–0.97) | 1.41 (1.08–1.69) | 1.69 | 0% |
| [[qwen2.5-7b]] | 1.45 | 14 | 3.38 (3.07–3.91) | 6.60 (5.55–8.37) | 6.60 | 0% |
| | 1.73 | 17 | 3.74 (3.69–3.78) | 6.06 (5.55–6.71) | 6.06 | 0% |
| | 3.5 | 35 | 3.54 (3.16–3.99) | 6.71 (6.09–7.13) | 8.51 | 0% |

## GET /search p95 (mixed load)
Between **0.22 and 0.56 s** across every standard configuration. The p99 sometimes exceeds 1 s (e.g. 1B average-load mean 1.23 s), but R2 is a p95 requirement, so it passes.

## Initial 7B stress (superseded)

| Config | Samples | Offered/min | p50 | p95 | Err |
|---|---|---|---|---|---|
| Ramp 3.5 → 12 | 232 | 7.94 | 3.90 | 10.17 | 0% |
| 7.2 confirm | 108 | 7.17 | 4.22 | 8.67 | 0% |
| 9.6 confirm | 144 | 9.88 | 4.22 | 17.31 | 0% |

No limit was found, so the team ran the [[Adaptive Stress Test]].

## Caveats
- With only 14–35 samples per run, **p95 and p99 are nearly the max sample**, which is why p95 = p99 at the low rates.
- Achieved "Throughput /min" is slightly *above* the offered rate. The window runs from the first request to the last completion. This was flagged in an audit as needing a clear label on Slide 9 (see [[Codex Chat Summary]]).
- Offered rates drift from the targets (e.g. 0.5B peak 1.91 vs 1.73) because random arrivals over short runs vary.

> [!note] Run register
> All runs were on the two MacBooks. `results/load/RUNS.md` was filled on 2026-11-13 with all 40 runs. Standard runs took place on 7 Oct (0.5B, 1B) and 8 Oct (7B); every standard run is complete and reconciles. See [[Evidence Reconciliation]].
