---
type: meta
title: "Hot Cache"
created: 2026-11-13
updated: 2026-11-13
tags:
  - meta
  - hot
status: developing
---

# Hot Cache (read this first)

**Last update:** 2026-11-13, A2 tooling built (PRs #12 golden split, #13 cascade + two-Mac harness).

## Current focus
**Assignment 2**, due **27 Nov 2026**: the fastest configuration within the accuracy floor, built around a cascade. See [[Assignment 2 Planning]] and [[A2 Playbook]].

**Next steps:**
1. **SUT Mac:** set `OLLAMA_MAX_LOADED_MODELS` and run the memory check. Ask the lecturer whether changing that setting is acceptable.
2. **Team:** choose the rule and two settings, write the predictions, and commit both with the `a2-prediction-freeze` tag.
3. Then the accuracy tests, S, and the speed tests (`docs/a2-playbook.md`).

**A2 limits:** overall **73.5%**; Mortgage **85.0%** is the tightest. Small models fail alone. On the tuning set, no rule is both within the limits and faster than the 7B alone.

## Key numbers
- Golden set: 195 tickets. Split for A2: **98 tuning (odd) / 97 test (even)**; smallest test cells are Credit card 7 and Mortgage 9.
- Accuracy: 0.5B **17.9%**, 1B **32.8%**, 7B **82.6%**. The 7B's weakest category is Money transfer (66.7%).
- Single-request p50: 0.40 / 0.46 / **2.84 s**.
- 7B capacity: 20 sustained, 22 mixed, 24 overloaded (POST/min with 7 search/min).
- Memory: 0.7 / 1.3 / 4.8 GiB of a 9.7 GiB Docker VM. `OLLAMA_MAX_LOADED_MODELS=1` must change for a cascade.
- Cascade break-even escalation fraction ≈ 84–86%. A category-based 1B rule would escalate ≈ 90%, so the cascade likely loses to the 7B alone.

## Deferred (team chose to leave the slides for now)
In `slides/build_deck.js`:
- Slide 5 line 289 says "size is the only difference", but Qwen and Llama are different families.
- Slide 9's "Done /min" window (first request → last completion) is unlabelled and inflates throughput.
- Slide 9 has no min–max spread for p99 and throughput.

Avoid all three in the A2 deck.

## Resolved 2026-11-13
- **Run register:** `results/load/RUNS.md` now lists all 40 runs, reconciled. See [[Evidence Reconciliation]].
- **3B model:** the team has removed [[qwen2.5-3b]] from the deck and records. The `prediction-freeze` tag still holds the four-model version. See [[Prediction Freeze]].
- **Test machine:** all official runs used the two MacBooks; the "Windows" wording was fixed. See [[Test Environment]].
- **Ownership:** `docs/team-plan.md` updated to the actual split, with all five recorded as equal contributors. See [[Team P1-3]].
- **Labels are the team's own:** the AI note is gone from `golden/SUMMARY.md`, and the pending deck item is closed. See [[Golden Set Summary]].
- **Freeze date:** the team plan now records the actual 6 Oct tag.
