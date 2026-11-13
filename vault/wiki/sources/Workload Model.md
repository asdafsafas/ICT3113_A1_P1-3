---
type: source
title: "Workload Model"
created: 2026-11-13
updated: 2026-11-13
tags:
  - ict3113
  - source
  - workload
status: mature
related:
  - "[[Requirements]]"
  - "[[Open-Loop Load Testing]]"
  - "[[Load Test Results]]"
sources:
  - "planning/workload-model.md"
source_type: data
author: "Team P1-3 (owner listed as Zong Han)"
date_published: 2026-10-06
url: ""
confidence: medium
key_claims:
  - "~173,400 in-scope complaints a year, anchored on Bank of Scotland plc H2 2025 (86,719 per half-year)"
  - "Average 1.45 tickets/min; peak hour 1.73 tickets/min (15% of daily volume); stress check 3.5/min"
  - "2 searches per ticket: 2.9 searches/min average, 3.5/min peak"
  - "Ticket length p50 797 chars, p95 1,780, max 2,000; no truncation at num_ctx 4096"
---

# Workload Model (Slide 3)

Source: `planning/workload-model.md`. Every figure is marked **Sourced** or **Estimated**.

## Volume
- **Client assumption:** a large UK retail bank, anchored on **Bank of Scotland plc** (Lloyds Banking Group) complaints for 1 Jul – 31 Dec 2025: **86,719** in-scope complaints (banking & cards 67,071 + home finance 12,223 + credit related 7,425). Sourced.
- ×2 → **~173,438 a year** → ÷ 250 business days → **~694 a day** → ÷ 8 hours → **~87/hour ≈ 1.45/min**. Estimated.
- Counting every complaint as a ticket, including phone complaints, overstates written volume. That makes the test harder, which is deliberate.

## Peak
- Peak hour = **15% of daily volume** (call-centre staffing source) → **~104/hour ≈ 1.73/min**. Estimated.
- Peak-to-average ratio is 1.2. No seasonal or day-of-week peak is modelled.

## Searches (`GET /search`)
- Estimated at **2 per ticket** (the customer's history + similar complaints) → **2.9/min average, 3.5/min peak**.

## Ticket lengths (measured over all 1,000 rows, 3000–3999)

| | p5 | p25 | p50 | p75 | p95 | p99 | max |
|---|---|---|---|---|---|---|---|
| Words | 49 | 94 | 144 | 214 | 322 | 361 | 385 |
| Chars | 263 | 512 | 797 | 1214 | 1780 | 1938 | 2000 |

A correction made before the freeze replaced earlier figures that likely counted `\r\n` line endings as two characters. Lengths appear **capped at 2,000 chars** in the extract. The longest ticket plus the prompt (395 chars) fits easily in `num_ctx` 4096.

## Load levels tested

| Level | POST/min | Search/min |
|---|---|---|
| Average | 1.45 | 2.9 |
| Peak | 1.73 | 3.5 |
| Beyond-peak (2× peak) | 3.5 | 7 |

> [!note] Pending decision
> `slides/pending-changes.md` asks whether Slide 3 should explain why the volumes come from a UK bank while the tickets come from the US CFPB.
