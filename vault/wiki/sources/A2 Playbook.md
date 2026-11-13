---
type: source
title: "A2 Playbook"
created: 2026-11-13
updated: 2026-11-13
tags:
  - ict3113
  - source
  - assignment-2
status: developing
related:
  - "[[Assignment 2 Brief]]"
  - "[[Assignment 2 Planning]]"
  - "[[Cascade Classification]]"
  - "[[Triage Service]]"
sources:
  - "docs/a2-playbook.md"
  - "a2/limits.md"
  - "a2/tuning-analysis.md"
  - "a2/speed-workload/README.md"
source_type: data
author: "Team P1-3 (tooling generated with AI assistance, 2026-11-13)"
date_published: 2026-11-13
url: ""
confidence: high
key_claims:
  - "Overall limit 73.5% (7B test-set 83.5% - 10); Mortgage limit 85.0% is the tightest"
  - "Neither small model passes alone, so only the 7B alone and the cascade settings are speed-tested"
  - "On the tuning set, no candidate rule is both within the limits and faster than the 7B alone"
  - "The SUT agent and the LG runner automate reset, warm-up, evidence and S-derived JMeter settings"
---

# A2 Playbook and tooling

Source: `docs/a2-playbook.md` (PR #13). It gives the step-by-step order of work for the two Macs, which are the same as in A1 (see [[Test Environment]]).

## Order of work
1. **SUT Mac:** set `OLLAMA_MAX_LOADED_MODELS` once for all of A2 (2, or 3 for an agreement rule) and run the **memory check** (`a2_sut_agent.py memory-check`).
2. **Team:** choose the rule and two settings from `a2/tuning-analysis.md`. Fill in `a2/escalation-rule.md` and `planning/a2-prediction-record.md`, commit both and tag `a2-prediction-freeze`, **before any test** (see [[Prediction Freeze]]).
3. **SUT Mac:** test-set accuracy for each cascade setting (`a2_accuracy.py`).
4. **Both Macs:** measure **S** once on the 7B (`run_a2_speed.py measure-s`).
5. **Both Macs:** speed tests, 3 runs each, for `7b-alone`, `cascade-A` and `cascade-B` (`run_a2_speed.py run`).
6. `run_a2_speed.py summarise` → `results/a2/speed/SUMMARY.md`.

## Numbers already fixed (no machine needed)
- **Limits** (`a2/limits.md`), from the A1 runs re-scored on the test set:
  - 7B: 81/97 = **83.5%**, so the **overall limit is 73.5%**.
  - Per-category limits are the 7B's score − 15 points. **Mortgage at 85.0%** is the tightest: the 7B got 9/9, so the cascade can miss at most 1.
  - Mortgage (9 tickets) and Credit card (7) are too small for a fair per-category test.
- **Single models on the test set:** the 0.5B scores 15.5% and the 1B 33.0%. Both fail, so they need no speed test.
- **Tuning-set rule analysis** (`a2/tuning-analysis.md`, estimates only): no candidate is both within the limits and faster than the 7B alone.
  - Safe category and agreement rules escalate 85–100% of tickets.
  - Length rules are faster but break a category limit. The closest is the 1B at ≤300 chars, with Debt collection at −16.7 against −15 allowed: one ticket out of 6.
- **Speed workload** (`a2/speed-workload/`):
  - S tickets: rows 3405, 3530 and 3738.
  - Warm-up tickets: rows 3273, 3808 and 3887.
  - Speed-test list: 200 rows from 3200 upwards, in fixed order.

## Speed-test settings derived from S
- Rate = 60 ÷ (2S) per minute.
- Run length = S minutes, at least 5.
- Response timeout = 10S seconds, at least 300.
- Pause = timeout + 60 s.

These come from `loadtest/triage_a2.jmx` (POST only); the A1 plan is unchanged. See [[Open-Loop Load Testing]].

## Evidence per run (`results/a2/speed/<config>/`)
- JTL and JMeter log.
- The run's service-log lines.
- `docker stats` CSV.
- Health JSON, with `GET /stats` before and after.
- `ollama ps` before and after.
- SUT audit log.
- `_run.json` with the run's numbers: sent / completed / errored / unfinished, p50, throughput, escalation fraction, and a reload count.

See [[Evidence Reconciliation]].

## Not yet verified on the Macs
- The agent's Docker steps.
- JMeter accepting the `sec` duration unit.

The playbook starts with a 1-minute JMeter check against the mock server and with the memory check.
