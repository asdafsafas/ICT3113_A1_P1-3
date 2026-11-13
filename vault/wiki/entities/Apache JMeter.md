---
type: entity
title: "Apache JMeter"
created: 2026-11-13
updated: 2026-11-13
tags:
  - ict3113
  - entity
  - tool
status: developing
related:
  - "[[Open-Loop Load Testing]]"
  - "[[Load Test Results]]"
  - "[[Adaptive Stress Test]]"
sources:
  - "[[Project Docs]]"
entity_type: product
role: "Load generator, playing the client's complaint intake"
first_mentioned: "[[Assignment 1 Brief]]"
---

# Apache JMeter

The load generator required by the brief. It plays the complaint intake.

- **Version used:** 5.6.3 on Ridwan's Mac (`/Users/ridwan/Downloads/apache-jmeter-5.6.3`).
- **Plan:** `loadtest/triage.jmx` + `loadtest/triage.properties`. It reads `loadtest/data/tickets.tsv` (rows **3200–3999**, about 800 tickets, never golden rows). Properties include `rate`, `rate_end`, `search_rate`, `duration` and `host`.
- **Open-loop** arrivals (Open Model Thread Group / Precise Throughput Timer). See [[Open-Loop Load Testing]].
- Sets the `X-Request-ID` header, which lets each sample be matched to a service log line ([[Evidence Reconciliation]]).
- Outputs: `.jtl` per run plus a `_jmeter.log`, summarised by `scripts/summarise_jtl.py`, with an HTML dashboard (`jmeter -g`) for latency over time.
- Default response timeout is 5 min. A2 requires a timeout of 10×S and an end pause longer than the timeout.
