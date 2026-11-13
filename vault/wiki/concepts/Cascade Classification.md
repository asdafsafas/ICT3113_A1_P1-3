---
type: concept
title: "Cascade Classification"
created: 2026-11-13
updated: 2026-11-13
tags:
  - ict3113
  - concept
  - assignment-2
status: developing
related:
  - "[[Assignment 2 Brief]]"
  - "[[Assignment 2 Planning]]"
  - "[[Ollama Bottleneck]]"
sources:
  - "[[Assignment 2 Brief]]"
complexity: intermediate
domain: "performance"
aliases:
  - "cascade"
  - "model cascade"
  - "escalation"
---

# Cascade Classification

A cheap model classifies every ticket. A **rule** then decides whether to accept its answer or **escalate** the ticket to a larger model, whose answer is final.

## Latency model (from the A2 brief)
E[latency] ≈ L_small + f × L_large, where **f** is the escalation fraction. This ignores queueing and routing overhead.

The cascade beats the large model alone only if **f < 1 − L_small / L_large**.

Plugging in our A1 accuracy-run p50s (analysis; A2 needs fresh speed numbers):

| Small stage | L_small | L_large (7B) | Break-even f |
|---|---|---|---|
| [[qwen2.5-0.5b]] | 0.40 s | 2.84 s | **< 86%** |
| [[llama3.2-1b]] | 0.46 s | 2.84 s | **< 84%** |

If the rule itself needs a second small call (agreement or confidence methods), L_small roughly doubles and break-even falls to about 68–72%.

## Rule families (from the brief)
1. **Category-based:** accept if the predicted category is "reliable" on the tuning set. The rule can use only the *predicted* category, so it depends on per-category **precision**, not recall.
2. **Agreement:** two small calls (two models, or one model with two wordings); escalate on disagreement.
3. **Self-reported confidence:** HIGH/LOW. Small models are often confident and wrong.
4. **Ticket length:** route long tickets straight to the large model. Useful only if length predicts errors.

Each family has a dial (category list, length cut-off, and so on). A2 tests **two settings**, chosen on the tuning set.

## Hard constraints
- **Both models must be resident** (`ollama ps` lists both) on the A1 machine, with no extra RAM. Otherwise the result measures model loading.
- **No caching**, **no change to Ollama inference settings** between configurations, the same prompt for every call, and the caller cannot tell which model answered.
- The log must record the final model and an escalation flag per ticket. The escalation fraction is reported from the logs.

## Repo-specific feasibility
See [[Assignment 2 Planning]].
