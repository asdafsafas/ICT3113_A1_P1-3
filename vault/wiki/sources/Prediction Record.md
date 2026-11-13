---
type: source
title: "Prediction Record"
created: 2026-11-13
updated: 2026-11-13
tags:
  - ict3113
  - source
  - predictions
status: mature
related:
  - "[[Prediction Freeze]]"
  - "[[Predictions vs Outcomes]]"
  - "[[Ollama Bottleneck]]"
sources:
  - "planning/prediction-record.md"
source_type: data
author: "Team P1-3 (compiled by Ridwan per team-plan)"
date_published: 2026-10-06
url: ""
confidence: high
key_claims:
  - "Bottleneck = Ollama CPU time reading the prompt (NUM_PARALLEL=1); triage container < 10% CPU"
  - "7B capacity ~9.4 tickets/min; secondary bottleneck = 40-thread FastAPI pool under stress"
  - "Accuracy: 0.5B 45%, 1B 55%, 7B 78%; no candidate passes R4 or R5 in point predictions"
  - "Latency p50: 0.5B 0.8 s, 1B 0.9 s, 7B 6.1 s"
---

# Prediction Record (Slide 11)

Source: `planning/prediction-record.md`. Frozen at annotated tag **`prediction-freeze`**, committed 2026-10-06 15:35 SGT together with the golden set, the prompt and the model pins. See [[Prediction Freeze]].

> [!contradiction] Edited after the freeze
> The tagged version lists **four** candidates, including [[qwen2.5-3b]]. The working copy was edited after testing began to remove the 3B model. The brief says the record "cannot be revised afterwards", so the submission must disclose this and point to the tag (see [[Codex Chat Summary]]).

## Basis
- Prototype smoke tests (5 Oct): one invented 136-char ticket per model through Tze Han's *prototype* service, whose prompt was 1,240 chars. See `evidence/smoke-prototype/`.
- Real-service [[Smoke Tests]] (6 Oct): 6 invented tickets per model.
- Latency method: the measured time per prompt token × (chars ÷ 4 + **272** instruction tokens). The queue was modelled as M/G/1.
- **Known bias, stated in the record:** the 272 tokens come from the prototype prompt. `classify_v1.txt` is about ⅓ that length, so the method overstates latency by about 0.3 s for 0.5B/1B and 1.9 s for 7B.

## Predictions

**Bottleneck** ([[Ollama Bottleneck]])
- Ollama prompt evaluation on CPU is the bottleneck; Ollama uses ≥ 900% CPU and triage < 10%.
- Search p95 stays < 100 ms at peak.
- 7B capacity is ~9.4/min. At 9.6/min the queue does not drain, and at 12/min the backlog grows by 2.6/min.
- Second bottleneck: once ~40 POSTs are queued, the **40-thread pool** makes search p95 exceed 10 s (about 15 min into a 12/min run).

**Per model**

| Model | Accuracy | p50 latency (p95) |
|---|---|---|
| [[qwen2.5-0.5b]] | 45% (35–55) | 0.8 s (1.2) |
| [[llama3.2-1b]] | 55% (45–65) | 0.9 s (1.2) |
| [[qwen2.5-7b]] | 78% (72–84) | 6.1 s (8.6) |

- R1–R3 pass for all models. R4 fails for all (7B misses by ~2 points). R5 fails for all; the 7B's weakest is Debt collection / Consumer loan at 55–68%.
- 0.5B: **Credit reporting > 35% of its answers**.

**Hardest categories:** Debt collection (vs Credit reporting), Consumer loan, Bank account vs Money transfer (≥ 25% of MT tickets labelled Bank by the 7B). **Easiest:** Mortgage and Credit reporting, with recall ≥ 90% but CR precision ≤ 75%.

**Other predictions:** latency correlates with length (r ≥ 0.8); 0.5B → 7B costs 7.6× the latency for +33 points; run-to-run p50 spread < 10%; < 1% invalid outputs.

Checked against the results in [[Predictions vs Outcomes]].

## Hardware stated in the record
MacBook Pro (Mac17,2), Apple M5, 10 cores (4P + 6E), 16 GB RAM, macOS 26.6.2. Docker VM: 10 CPUs, 9.7 GiB. Ollama 0.35.1, CPU only. See [[Test Environment]].
