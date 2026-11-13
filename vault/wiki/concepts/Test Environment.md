---
type: concept
title: "Test Environment"
created: 2026-11-13
updated: 2026-11-13
tags:
  - ict3113
  - concept
  - environment
status: developing
related:
  - "[[Ollama]]"
  - "[[Apache JMeter]]"
  - "[[Assignment 2 Planning]]"
sources:
  - "[[Prediction Record]]"
  - "[[Smoke Tests]]"
  - "[[Adaptive Stress Test]]"
complexity: basic
domain: "performance testing"
aliases:
  - "SUT machine"
  - "Slide 7"
---

# Test Environment (Slide 7)

## System under test (Tze Han's Mac)
- MacBook Pro (Mac17,2), **Apple M5**, 10 cores (4P + 6E), **16 GB RAM**, macOS 26.6.2.
- Docker 29.8.2 Linux VM: **10 CPUs, 9.7 GiB RAM**.
- Ollama 0.35.1, CPU only; triage service; SQLite volume.

## Load generator (Ridwan's Mac)
- Apache JMeter 5.6.3, on the same LAN. During the adaptive test the SUT was at `172.20.10.2`, which is a phone-hotspot-style subnet. This may matter for network variance.

## Limitations to state
Laptop thermal throttling, battery vs AC power (there was a `_ac` smoke run), Wi-Fi, background apps. ARM laptop vs the client's x86 servers: more cores, but server CPUs often have lower clocks.

> [!note] Resolved 2026-11-13: MacBooks
> The team confirmed that **every official load test ran on the two MacBooks**. The "Windows" wording in `results/load/RUNS.md` and the archive README was wrong and has been corrected. The archived `macos-attempt-2026-10-06` was the first attempt on the same Macs, retired because its resource-statistics CSVs were missing.
>
> For A2 (same machine, CPU and RAM), the SUT is **Tze Han's M5 MacBook Pro** with the Docker VM at 10 CPUs and 9.7 GiB.
