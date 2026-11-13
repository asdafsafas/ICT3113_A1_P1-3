---
type: concept
title: "Misrouting vs Speed Position"
created: 2026-11-13
updated: 2026-11-13
tags:
  - ict3113
  - concept
  - requirements
status: developing
related:
  - "[[Requirements]]"
  - "[[Assignment 2 Brief]]"
sources:
  - "[[Requirements]]"
complexity: basic
domain: "requirements"
aliases:
  - "cost position"
---

# Misrouting vs Speed: the team's position

The A1 brief deliberately left open whether a misrouted ticket or a slow triage costs the client more, and required teams to take a position.

**Team position (A1):** *a misrouted ticket costs more.* A misrouted complaint has to be noticed, re-read and passed on by a second team. A classification that takes 30 s instead of 5 s changes nothing for a complaint answered over hours or days.

Consequences:
- Strict accuracy requirements (R4 ≥ 80%, R5 ≥ 70% per category) and a loose latency requirement (R1 p95 ≤ 30 s).
- The recommendation of [[qwen2.5-7b]] follows from this position.

## Reversal in A2
In A2 the **client** sets the position: *speed is now the primary concern*. Accuracy may drop by up to 10 points overall and 15 points per category relative to the top model. The A2 report should acknowledge that this reverses the A1 position, and that this time the client chose it.
