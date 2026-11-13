---
type: concept
title: "Evidence Reconciliation"
created: 2026-11-13
updated: 2026-11-13
tags:
  - ict3113
  - concept
  - process
status: developing
related:
  - "[[Open-Loop Load Testing]]"
  - "[[Triage Service]]"
sources:
  - "[[Project Docs]]"
  - "[[Codex Chat Summary]]"
complexity: basic
domain: "research integrity"
aliases:
  - "reconcile"
  - "traceability"
---

# Evidence Reconciliation

The brief requires that **every reported number trace back to a kept log or `.jtl` file**. Untraceable numbers count as unsupported; fabricated or irreconcilable ones are an academic-integrity matter. This applies in both A1 and A2.

## How we do it
- JMeter sets `X-Request-ID`, and the service logs it on every line ([[Triage Service]]).
- `scripts/reconcile.py` matches each JTL sample to its service record and reports missing IDs, status mismatches, and client-vs-service latency.
- A **reportable run** has: JTL + JMeter log + dedicated service JSONL + `docker stats` CSV. The adaptive stress runs also have a `/health` snapshot and an SUT audit log.
- Adaptive stress result: **1,468 samples, 0 missing, 0 mismatches**.
- Invalid or superseded runs are **kept and marked**, never deleted (e.g. `results/archive/macos-attempt-2026-10-06/`, and `adaptive_14rpm_s7_run1`).

## Reporting vocabulary
Label every figure as one of: **measured** · **predicted (before testing)** · **estimated after testing** · **limit not observed within the tested range**.

> [!note] Run register filled 2026-11-13
> `results/load/RUNS.md` now lists all 40 load and stress runs: 27 standard, 3 initial stress, 10 adaptive. Each row was built from its JTL and reconciled against its own service log. Every row reconciles except `adaptive_14rpm_s7_run1` (2 missing, 2 status mismatches), which is marked invalid. For A2, add rows as runs happen.
