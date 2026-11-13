---
type: source
title: "Smoke Tests"
created: 2026-11-13
updated: 2026-11-13
tags:
  - ict3113
  - source
  - smoke-test
status: mature
related:
  - "[[Prediction Record]]"
  - "[[Ollama Bottleneck]]"
  - "[[Test Environment]]"
sources:
  - "evidence/smoke/SUMMARY.md"
  - "evidence/smoke-prototype/"
source_type: data
author: "Team P1-3 (scripts/smoke_sut.py)"
date_published: 2026-10-06
url: ""
confidence: high
key_claims:
  - "Six invented tickets (186-2,000 chars) per model through the real service; no dataset rows used"
  - "Latency is linear in length: 7B ~621 ms + 2.20 ms/char (R2 0.995)"
  - "Ollama uses ~1000% CPU (all 10 VM CPUs); triage peaks at 1%"
  - "Resident memory: 0.5B 695 MiB, 1B 1.29 GiB, 7B 4.82 GiB of 9.7 GiB VM"
---

# Smoke Tests (pre-freeze evidence)

`evidence/smoke/SUMMARY.md` was generated 2026-10-06 by `scripts/smoke_sut.py` (git `7361d77`). It sent 6 **invented** tickets per model, one at a time, after a restart and a warm-up.

## Fitted single-request latency (`a + b × chars`)

| Model | a ms | b ms/char | R² | ms/prompt token | @ golden p50 | @ golden p95 | Ollama CPU % | Triage CPU % | Memory |
|---|---|---|---|---|---|---|---|---|---|
| [[qwen2.5-0.5b]] | 72 | 0.37 | 0.990 | 1.79 | 0.37 s | 0.71 s | 980 | 0 | 695 MiB |
| [[llama3.2-1b]] | 157 | 0.37 | 0.950 | 1.84 | 0.45 s | 0.78 s | 1017 | 1 | 1.29 GiB |
| [[qwen2.5-7b]] | 621 | 2.20 | 0.995 | 10.32 | 2.41 s | 4.39 s | 1001–1010 | 1 | 4.82 GiB |

Prompt evaluation dominates: on the 7B it took 4,596 ms of the 5,178 ms Ollama total for a 2,000-char ticket. This is the evidence behind [[Ollama Bottleneck]].

## Ollama container environment
`OLLAMA_NUM_PARALLEL=1`, `OLLAMA_MAX_LOADED_MODELS=1`, `OLLAMA_MAX_QUEUE=512`, `OLLAMA_KEEP_ALIVE=30m`, Ollama 0.35.1.

> [!note] Relevance to Assignment 2
> The 7B plus either small model uses about 5.5–6.1 GiB, which should fit in the 9.7 GiB Docker VM together. However, `OLLAMA_MAX_LOADED_MODELS=1` would force an unload on every escalation. See [[Assignment 2 Planning]].

## Prototype smoke tests (`evidence/smoke-prototype/`)
These ran 5 Oct through Tze Han's prototype service. Its prompt included category definitions (1,240 chars, ~300 tokens). They also covered `qwen2.5:3b` ([[qwen2.5-3b]]) and a `qwen2.5-0.5b_ac` run on AC power. The [[Prediction Record]]'s latency estimates were derived from these, hence its known bias.
