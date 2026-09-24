# Prediction record (Step 4, Slide 11)

> **Freeze rule:** this file is committed together with the golden set **before the first benchmark run**, and must not be edited afterwards. The commit history is our evidence. Corrections go in the report as "where we were wrong", never here.

**Committed on:** ____ · **Commit / tag:** ____

Marks are for being **specific enough to be proven wrong**, not for being right. "The model will be slow" earns nothing; "qwen2.5:7b will take 25–40 s per ticket and p95 will exceed 120 s at 4 tickets/min" can be checked.

## 1. Where the bottleneck will be under load, and why

Name the component (triage service, Ollama, CPU, memory, disk/SQLite, network), the load level at which it saturates, and what we expect to observe (for example, queue build-up: p95 grows steadily through the run while CPU stays at 100%).

-

## 2. Per candidate model

Hardware: ____ (the system-under-test machine from [docs/setup.md](../docs/setup.md))

| Model (tag) | Size class | Expected accuracy on golden set | Expected single-request latency | Reasoning |
|---|---|---|---|---|
| | | __% (range __–__%) | __ s (range __–__ s) | |
| | | | | |
| | | | | |

## 3. Hardest categories to classify, and why

| Category | Why we expect it to be hard | Likely confused with |
|---|---|---|
| | | |
| | | |

## 4. Other predictions (optional)

-
