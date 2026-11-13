---
type: entity
title: "CFPB Consumer Complaint Database"
created: 2026-11-13
updated: 2026-11-13
tags:
  - ict3113
  - entity
  - dataset
status: seed
related:
  - "[[Ticket Categories]]"
  - "[[Golden Test Set]]"
sources:
  - "[[Assignment 1 Brief]]"
entity_type: organization
role: "Source of ticket narratives (US Consumer Financial Protection Bureau)"
first_mentioned: "[[Assignment 1 Brief]]"
---

# CFPB Consumer Complaint Database

Real consumer complaint narratives published by the US **Consumer Financial Protection Bureau**, with consent and with personal data removed at source (shown as `XXXX`). Original: consumerfinance.gov/data-research/consumer-complaints/.

- The course extract was distributed via xSiTe. Team rows: **3000–3999**, stored in `ict3113_ticket_P1-3.xlsx` (rows 3000–3199) and `loadtest/data/load-test-tickets.csv` (3200–3999).
- The `source_label` column was chosen by consumers and is **noisy**, so labellers were told not to look at it.
- Narrative length appears capped at 2,000 chars (see [[Workload Model]]).
- Acknowledged on Slide 12, with the extract credited to SIT via xSiTe.

**Split of use:** 3000–3199 → [[Golden Test Set]] (accuracy only); 3200–3999 → load and stress traffic. In A2, speed-test tickets must also come from outside the golden set.
