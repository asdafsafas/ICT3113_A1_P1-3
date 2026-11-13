---
type: concept
title: "Ollama Bottleneck"
created: 2026-11-13
updated: 2026-11-13
tags:
  - ict3113
  - concept
  - performance
status: mature
related:
  - "[[Ollama]]"
  - "[[Adaptive Stress Test]]"
  - "[[Cascade Classification]]"
sources:
  - "[[Smoke Tests]]"
  - "[[Prediction Record]]"
  - "[[Adaptive Stress Test]]"
complexity: intermediate
domain: "performance"
aliases:
  - "bottleneck diagnosis"
  - "prompt evaluation bottleneck"
---

# Ollama Bottleneck (diagnosed bottleneck)

**Claim:** the system's bottleneck is the [[Ollama]] model server, specifically **CPU time spent evaluating the prompt**, serialised by `OLLAMA_NUM_PARALLEL=1`.

## Evidence
- **CPU:** Ollama uses ~1000% CPU (all 10 Docker VM CPUs) during a request, while triage peaks at 0–1% ([[Smoke Tests]]).
- **Time split:** prompt eval is 80–90% of each request. A 2,000-char ticket on the 7B takes 4.6 s of prompt eval out of 5.2 s total.
- **Linearity:** latency is linear in ticket length (R² 0.95–0.995).
- **Queueing under stress:** at 24/min the backlog grew from 13–15 to 24–27 and p50 rose to 26–34 s while errors stayed at 0%. Throughput plateaued at about 21.6–23/min ([[Adaptive Stress Test]]).
- **Diagnostic formula:** `latency_ms − ollama_total_ms` in the service log is queue wait. If it grows while `ollama_total_ms` stays flat, the server is processing one request at a time.

## What was predicted but not seen
The **FastAPI 40-thread pool** was predicted to starve `GET /search` once ~40 POSTs were queued. The backlog never reached 40, and search p95 stayed ≤ 0.6 s.

## Implication (from the A2 brief's own analysis)
Service-code optimisation can't help much: Ollama takes seconds, the service milliseconds. Hence A2's focus on **arranging the models** ([[Cascade Classification]]) rather than tuning the code.
