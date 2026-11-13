---
type: concept
title: "Open-Loop Load Testing"
created: 2026-11-13
updated: 2026-11-13
tags:
  - ict3113
  - concept
  - load-test
status: mature
related:
  - "[[Apache JMeter]]"
  - "[[Load Test Results]]"
  - "[[Evidence Reconciliation]]"
sources:
  - "[[Assignment 1 Brief]]"
  - "[[Project Docs]]"
complexity: intermediate
domain: "performance testing"
aliases:
  - "open model"
  - "open-loop"
---

# Open-Loop Load Testing

**Open-loop** means requests arrive at a controlled rate whether or not earlier ones have finished. **Closed-loop** (N threads, each waiting for its response) self-throttles when the server slows, which hides queue build-up. The brief **rejects closed-loop results** as evidence.

## Our A1 playbook (summary of `docs/actual-jmeter-test.md`)
1. **Two machines:** the load generator and the SUT on the same network.
2. **Stop gate:** freeze tag present, digests verified (`pull_models.py --check`), `OLLAMA_NUM_PARALLEL=1` confirmed, `tickets.tsv` = rows 3200–3999.
3. **Before every run:** restart Ollama, warm up with invented text, delete the warm-up DB row, start `docker stats` to a per-run CSV.
4. **Run:** 10 min open-loop at the target POST and search rates. Configurations: 1.45/2.9, 1.73/3.5, 3.5/7. Three runs each, for each of 3 models (27 runs).
5. **After every run:** keep the `.jtl`, the JMeter log, a dedicated service JSONL and the stats CSV. Then [[Evidence Reconciliation|reconcile]].
6. **Summarise:** `summarise_jtl.py`, reporting mean (min–max) across runs of p50/p95/p99, throughput and errors.

## Pitfalls met
- Short 10-min runs at 1.45/min give only 14 samples, so p95 ≈ p99 ≈ the max.
- Throughput windows must be defined clearly.
- Accidental cache or DB carry-over between runs.

## A2 differences
The rate is derived from S (one ticket every 2S s). Runs last max(S, 5) min with about 30 tickets each. Report **pooled p95** over the 3 runs and **no p99**. Fixed ticket order. Three fixed warm-up tickets. Record `/stats` before and after. Timeout of 10×S, with the end pause longer than the timeout. See [[Assignment 2 Brief]].
