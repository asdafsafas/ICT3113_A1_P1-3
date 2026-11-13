---
type: source
title: "Assignment 1 Brief"
created: 2026-11-13
updated: 2026-11-13
tags:
  - ict3113
  - source
  - brief
status: mature
related:
  - "[[Assignment 2 Brief]]"
  - "[[Triage Service]]"
  - "[[Golden Test Set]]"
  - "[[Prediction Freeze]]"
sources:
  - "ICT3113_Assignment_1.docx"
source_type: paper
author: "ICT3113 course staff"
date_published: 2026-09-01
url: ""
confidence: high
key_claims:
  - "Client is a financial complaints desk; no public model API, CPU-only commodity servers"
  - "Golden set (150-200 tickets) and prediction record must be committed before the first benchmark"
  - "Load tests must be open-loop JMeter, 3 runs per configuration, p50/p95/p99 + throughput + errors"
  - "Every reported number must reconcile with kept logs and .jtl files"
---

# Assignment 1 Brief: Performance Requirements & Testing

**Worth:** 15% · **Due:** 23:59 Fri 9 Oct 2026 (Week 6) · **Deliverable:** `Group03.pptx` (≤ 12 slides) + supporting files. Repo file: `ICT3113_Assignment_1.docx`.

## Scenario
A financial services client wants complaint tickets classified automatically into 7 categories (see [[Ticket Categories]]). **Constraint:** no public model API. Inference must run on client-controlled, **CPU-only** hardware. The brief frames it as a constraint problem: *what should the client deploy, and what service quality can you promise?*

## System under test
- [[Triage Service]] in Docker: `POST /tickets`, `GET /search`, `GET /stats`. It starts empty, and tickets arrive only through POST.
- [[Ollama]] backend, CPU only, with 3–5 candidate models across ≥ 2 size classes, pinned by tag and digest.
- Dataset: a course extract of the [[CFPB Consumer Complaint Database]]. Each team uses rows n×1000 … n×1000+999 (Team 3 → rows 3000–3999). The raw labels are noisy.
- Instrumentation: log every request. Numbers that can't be traced to the logs count as "unsupported".

## Six steps
1. Build the [[Golden Test Set]]: a protocol, ≥ 2 independent labellers, an agreement statistic, and every disagreement resolved and recorded. See [[Labelling Protocol]] and [[Inter-Annotator Agreement]].
2. Build a **deliberately unoptimised** synchronous baseline (no caching, no queuing).
3. Build a [[Workload Model]] from public figures, with citations.
4. Choose candidates, set testable [[Requirements]], and write the [[Prediction Record]].
5. Test: open-loop [[Apache JMeter]] load tests (3 runs per configuration), accuracy tests with a confusion matrix, and **one stress test** that finds a limit, all from a separate load-generator machine. See [[Open-Loop Load Testing]].
6. Make a recommendation that follows from the team's own requirements. "No candidate meets every requirement" is an acceptable, strong finding.

## Marking (15%)
Implementation 5% · Requirements and golden set 5% · Measurement and recommendation 5%. Fabricated or irreconcilable numbers are an academic-integrity matter. See [[Evidence Reconciliation]].

## Slide map
1 Cover · 2 Architecture · 3 Workload · 4 Requirements · 5 Candidate models · 6 Golden set · 7 Test environment · 8 Playbook · 9 Load & stress results · 10 Accuracy · 11 Predictions, recommendation, defence · 12 References.
