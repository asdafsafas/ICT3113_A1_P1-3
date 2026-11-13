---
type: source
title: "Requirements"
created: 2026-11-13
updated: 2026-11-13
tags:
  - ict3113
  - source
  - requirements
status: mature
related:
  - "[[Workload Model]]"
  - "[[Misrouting vs Speed Position]]"
  - "[[Predictions vs Outcomes]]"
sources:
  - "planning/requirements.md"
source_type: data
author: "Team P1-3 (owner listed as Zong Han)"
date_published: 2026-10-06
url: ""
confidence: high
key_claims:
  - "Position: a misrouted ticket costs more than a slow one"
  - "R1 POST p95 <= 30 s at 1.73/min; R2 search p95 <= 1 s under mixed peak load; R3 throughput >= 104/h, errors <= 1%"
  - "R4 overall accuracy >= 80%; R5 every category >= 70%"
---

# Performance and Accuracy Requirements (Slide 4)

Source: `planning/requirements.md`. The team's stated position, explained in [[Misrouting vs Speed Position]], is that **a misrouted ticket costs more than a slow one**.

| ID | Requirement | Load condition | Basis |
|---|---|---|---|
| **R1** | POST /tickets **p95 ≤ 30 s** | Peak 1.73/min, 10 min, 3 runs | A ticket arrives every ~35 s at peak; 30 s leaves headroom |
| **R2** | GET /search **p95 ≤ 1 s** | 1.73 POST + 3.5 search/min | Nielsen's 1 s flow-of-thought limit |
| **R3** | Throughput **≥ 104 tickets/h**, errors ≤ 1%, no latency growth | Peak 1.73/min | Peak-hour volume |
| **R4** | Overall accuracy **≥ 80%** | Golden set (195) | Human labellers agreed 78–85% before discussion |
| **R5** | Every category **≥ 70%** | Golden set, per category | Smallest categories have 17–18 tickets, so each ticket is worth ~6 points |

## Deployment constraints
- **C1:** local CPU-only Ollama, with no public API. Verified through `/health` and `ollama ps`.
- **C2:** the model's licence must allow the bank's commercial use. This is why [[qwen2.5-3b]] was dropped.

## Outcomes
See [[Predictions vs Outcomes]] and [[Candidate Model Comparison]]. Summary: all three models pass R1–R3. Only [[qwen2.5-7b]] passes R4 (82.6%), and **no model passes R5**: the 7B scores 66.7% on Money transfer.

> [!note] Assignment 2
> The A2 brief replaces R4/R5 with relative limits (top model −10 points overall, −15 points per category, on the test half). See [[Assignment 2 Brief]].
