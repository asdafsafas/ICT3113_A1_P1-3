---
type: meta
title: "Log"
created: 2026-11-13
updated: 2026-11-13
tags:
  - meta
  - log
status: developing
---

# Wiki Log

## [2026-11-13] ingest | A2 tooling (PRs #12, #13)
- Sources: `docs/a2-playbook.md`, `a2/limits.md`, `a2/tuning-analysis.md`, `a2/speed-workload/README.md`, `a2/golden-split/SPLIT.md`
- Pages created: [[A2 Playbook]]
- Pages updated: [[Cascade Classification]], [[Triage Service]], [[Evidence Reconciliation]], [[Assignment 2 Planning]], [[hot]], [[index]]
- Key insight: on the tuning set, no escalation rule stays within the limits (overall 73.5%; Mortgage 85.0%) while beating the 7B alone. The 7B alone is the likely recommendation, but the cascade must still be built and measured.

## [2026-11-13] update | Run register filled
- Repo change: `results/load/RUNS.md` filled with 40 rows (27 standard, 3 initial stress, 10 adaptive). Built from each JTL and reconciled against its dedicated service log. Orphan log and supplemental whole-day log noted.
- Pages updated: [[Evidence Reconciliation]], [[Load Test Results]], [[hot]]
- Team confirmed [[qwen2.5-3b]] has already been removed; recorded in [[hot]].

## [2026-11-13] update | Team resolutions of flagged contradictions
- Repo changes:
  - `docs/team-plan.md`: actual role split, all five recorded as equal contributors; timeline and hand-offs updated; actual freeze date added.
  - `results/load/RUNS.md` and `results/archive/macos-attempt-2026-10-06/README.md`: "Windows" → the two Macs.
  - `slides/pending-changes.md`: AI-assistance item moved to Done.
- Pages updated: [[Test Environment]], [[Load Test Results]], [[Golden Set Summary]], [[Team P1-3]], [[Zong Han]], [[Ridwan]], [[Tze Han]], [[Kannan]], [[Natalie]], [[Codex Chat Summary]], [[Project Docs]], [[Assignment 2 Planning]], [[hot]], [[overview]]
- Still open: post-freeze removal of [[qwen2.5-3b]]; empty run register.

## [2026-11-13] ingest | ICT3113_A1_P1-3 repository (initial batch)
- Sources (repo-relative, read in place, not copied to `.raw/`): `ICT3113_Assignment_1.docx`, `ICT3113_Assignment_2 - Copy (1).pdf`, `README.md`, `docs/*.md`, `planning/*.md`, `golden/SUMMARY.md`, `golden/agreement_summary.md`, `golden/golden_set.csv`, `labeler/protocol.json`, `results/accuracy/comparison.md`, `results/load/**/*.jtl` (via `scripts/summarise_jtl.py`), `results/load/RUNS.md`, `results/load/qwen2.5-7b/adaptive-stress/adaptive-stress-summary.md`, `evidence/smoke/SUMMARY.md`, `models/models.lock.json`, `service/prompts/classify_v1.txt`, `.env.example`, `slides/pending-changes.md`
- Summaries: [[Assignment 1 Brief]], [[Assignment 2 Brief]], [[Workload Model]], [[Requirements]], [[Prediction Record]], [[Golden Set Summary]], [[Accuracy Results]], [[Load Test Results]], [[Adaptive Stress Test]], [[Smoke Tests]], [[Codex Chat Summary]], [[Project Docs]]
- Pages created:
  - Entities: [[Team P1-3]], [[Zong Han]], [[Ridwan]], [[Tze Han]], [[Kannan]], [[Natalie]], [[qwen2.5-7b]], [[qwen2.5-0.5b]], [[llama3.2-1b]], [[qwen2.5-3b]], [[Ollama]], [[Apache JMeter]], [[Triage Service]], [[CFPB Consumer Complaint Database]]
  - Concepts: [[Golden Test Set]], [[Labelling Protocol]], [[Ticket Categories]], [[Inter-Annotator Agreement]], [[Prediction Freeze]], [[Ollama Bottleneck]], [[Open-Loop Load Testing]], [[Evidence Reconciliation]], [[Misrouting vs Speed Position]], [[Test Environment]], [[Cascade Classification]]
  - Comparisons and questions: [[Predictions vs Outcomes]], [[Candidate Model Comparison]], [[Assignment 2 Planning]]
  - Meta: [[overview]], [[index]], [[hot]]
- Pages updated: none (new vault)
- Key insight: the small models didn't just score low; they **collapsed onto a single label** (0.5B → Credit card, 1B → Credit reporting). A category-based cascade would therefore escalate ~90% of tickets, above the ~84% break-even. The 7B alone is the likely A2 answer.
- Contradictions flagged: 6 (see [[hot]]).
- Derived at ingest (not from committed files): the load-test table (ran `summarise_jtl.py` read-only), the A2 odd/even split counts, and the predicted-label counts (recall × n ÷ precision).
