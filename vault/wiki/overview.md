---
type: overview
title: "Overview"
created: 2026-11-13
updated: 2026-11-13
tags:
  - ict3113
  - meta
status: developing
related:
  - "[[index]]"
  - "[[hot]]"
sources:
  - "[[Assignment 1 Brief]]"
  - "[[Assignment 2 Brief]]"
---

# ICT3113 Ticket Triage: Overview

**What this is:** [[Team P1-3]]'s ICT3113 project. A CPU-only LLM ticket-classification service ([[Triage Service]] + [[Ollama]]) for a financial complaints desk. It is measured against requirements the team derived from a [[Workload Model]].

## Assignment 1 (done, submitted 9 Oct 2026)
- **Golden set:** 195 hand-labelled tickets, κ 0.735 / 0.778, protocol revised to v0.3. See [[Golden Test Set]].
- **Requirements:** latency and throughput at a 1.73/min peak; accuracy ≥ 80% overall and ≥ 70% per category. The team's position is that misrouting is the costlier failure. See [[Requirements]], [[Misrouting vs Speed Position]].
- **Models:** [[qwen2.5-0.5b]], [[llama3.2-1b]], [[qwen2.5-7b]]. [[qwen2.5-3b]] was dropped for licence reasons after the freeze.
- **Results:**
  - Accuracy 17.9% / 32.8% / **82.6%**.
  - All models pass the latency and throughput requirements with 0% errors.
  - 7B stress limit: 20/min sustained, 22 mixed, 24 overloaded.
  - Bottleneck: Ollama prompt evaluation on CPU.
  - See [[Candidate Model Comparison]], [[Adaptive Stress Test]], [[Ollama Bottleneck]].
- **Recommendation:** qwen2.5:7b. **No candidate met every requirement** (R5: Money transfer 66.7%).
- **Predictions:** the bottleneck was right; latency and capacity were too pessimistic; small-model accuracy was far too optimistic. See [[Predictions vs Outcomes]].

## Assignment 2 (in progress, due 27 Nov 2026)
Find the **fastest configuration within 10 points overall and 15 points per category** of the 7B's test-half accuracy. Test every model alone plus a [[Cascade Classification|cascade]] at two settings, with both models resident in memory on the same machine. See [[Assignment 2 Brief]] and [[Assignment 2 Planning]].

## Open issues
None blocking. The machine, ownership, AI wording, freeze date, run register and 3B removal were all settled on 2026-11-13. See [[hot]].
