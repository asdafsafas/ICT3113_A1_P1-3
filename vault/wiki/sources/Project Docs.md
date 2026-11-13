---
type: source
title: "Project Docs"
created: 2026-11-13
updated: 2026-11-13
tags:
  - ict3113
  - source
  - docs
status: developing
related:
  - "[[Triage Service]]"
  - "[[Team P1-3]]"
  - "[[Test Environment]]"
sources:
  - "README.md"
  - "docs/README.md"
  - "docs/architecture.md"
  - "docs/team-plan.md"
  - "docs/models.md"
  - "docs/setup.md"
  - "docs/golden-set.md"
  - "docs/load-testing.md"
  - "docs/actual-jmeter-test.md"
  - "docs/accuracy-testing.md"
  - "docs/pre-freeze-steps.md"
  - "slides/pending-changes.md"
source_type: data
author: "Team P1-3"
date_published: 2026-10-09
url: ""
confidence: high
key_claims:
  - "Repository layout and per-step playbooks for the A1 project"
  - "Baseline is deliberately unoptimised: synchronous, no cache, 1 uvicorn worker, SQLite LIKE search"
  - "Freeze artefacts: golden set, prediction record, models.lock.json, prompt (tag prediction-freeze)"
---

# Project Docs (repository playbooks)

An umbrella page for the repo's `README.md`, `docs/` and `slides/` notes. The specific results have their own source pages.

## Map

| Doc | Covers | Wiki page |
|---|---|---|
| `README.md` | Labelling instructions (labeller app on :8765, groups, independence rules) | [[Golden Test Set]], [[Labelling Protocol]] |
| `docs/architecture.md` | Components, endpoints, baseline design, log fields | [[Triage Service]] |
| `docs/team-plan.md` | Owners, timeline, hand-offs | [[Team P1-3]] |
| `docs/models.md` | Candidate set, pinning, prompt rules | [[Candidate Model Comparison]] |
| `docs/setup.md` | Docker / Ollama setup, CPU-only check, one machine for official runs | [[Test Environment]] |
| `docs/golden-set.md` | Sheets → kappa → resolutions → freeze | [[Golden Test Set]] |
| `docs/load-testing.md`, `docs/actual-jmeter-test.md`, `docs/person3-jmeter-todo.md` | JMeter playbooks, official matrix, reconciliation | [[Open-Loop Load Testing]], [[Evidence Reconciliation]] |
| `docs/adaptive-stress-test.md` | Adaptive limit-finding | [[Adaptive Stress Test]] |
| `docs/accuracy-testing.md` | Guarded three-model accuracy runner | [[Accuracy Results]] |
| `docs/pre-freeze-steps.md` | Pin, smoke, reset DB, tag `prediction-freeze` | [[Prediction Freeze]], [[Smoke Tests]] |
| `slides/pending-changes.md`, `slides/build_deck.js` | Deck build (`Group03.pptx`) and outstanding edits | [[Team P1-3]] |

## Key scripts (`scripts/`, standard library only)
`pull_models.py` (pin / `--check` digests) · `agreement.py` (kappa) · `build_golden.py` · `export_protocol.py` · `export_loadtest_data.py` · `accuracy_test.py` / `run_accuracy_suite.py` / `accuracy_compare.py` · `summarise_jtl.py` · `reconcile.py` · `smoke_sut.py` · `run_official_jmeter_suite.py` · `run_7b_stress_suite.py` · `run_adaptive_stress.py` + `adaptive_stress_sut.py` · `ticket_lengths.py` · `mock_triage_server.py`.

## Outstanding deck items (`slides/pending-changes.md`)
- Optional: explain the UK-bank volumes vs US-CFPB tickets.
- (Closed 2026-11-13: labels confirmed as the team's own.)

## Timeline
`docs/team-plan.md` planned the freeze for Wed 30 Sep. The plan now records the actual dates: protocol revisions on 3 Oct, the `prediction-freeze` tag on **6 Oct 15:35 SGT**, and every benchmark after it (load from 6 Oct, accuracy 8 Oct, adaptive stress 9 Oct).
