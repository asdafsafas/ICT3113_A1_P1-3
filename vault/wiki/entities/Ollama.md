---
type: entity
title: "Ollama"
created: 2026-11-13
updated: 2026-11-13
tags:
  - ict3113
  - entity
  - tool
status: developing
related:
  - "[[Triage Service]]"
  - "[[Ollama Bottleneck]]"
  - "[[Cascade Classification]]"
sources:
  - "[[Project Docs]]"
  - "[[Smoke Tests]]"
entity_type: product
role: "CPU-only model server (backend of the triage service)"
first_mentioned: "[[Assignment 1 Brief]]"
---

# Ollama

The model backend required by the brief, running **CPU-only** in Docker.

- **Version:** 0.35.1, image `ollama/ollama@sha256:292ee794…7b278c` (pinned in `models/models.lock.json`).
- **Settings** (`.env`, logged at startup): `OLLAMA_NUM_PARALLEL=1`, `OLLAMA_MAX_LOADED_MODELS=1`, `OLLAMA_MAX_QUEUE=512`, `OLLAMA_KEEP_ALIVE=30m`. Generation: `temperature 0`, `seed 42`, `num_ctx 4096`, JSON-schema `format` constraining the output to `{"category": …}`.
- **Behaviour:** handles NUM_PARALLEL requests at a time and queues the rest up to MAX_QUEUE, then rejects them (→ 502 from triage). It caches prompts it has seen, which is why A2 says to restart it and never time the same ticket twice.
- **CPU check:** `ollama ps` shows `100% CPU`.

## Why it matters
- In A1 it is the bottleneck: nearly all latency is prompt evaluation. See [[Ollama Bottleneck]].
- In A2, `MAX_LOADED_MODELS=1` would prevent a cascade. The setting must allow 2 resident models and stay constant across configurations. See [[Assignment 2 Planning]].
