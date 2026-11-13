---
type: question
title: "Assignment 2 Planning"
created: 2026-11-13
updated: 2026-11-13
tags:
  - ict3113
  - question
  - assignment-2
status: developing
related:
  - "[[Assignment 2 Brief]]"
  - "[[Cascade Classification]]"
  - "[[qwen2.5-7b]]"
sources:
  - "[[Assignment 2 Brief]]"
  - "[[Accuracy Results]]"
  - "[[Smoke Tests]]"
  - "[[Golden Test Set]]"
question: "Given our A1 results and setup, what does A2 look like for Team P1-3, and what must be resolved first?"
answer_quality: draft
---

# Assignment 2 Planning (analysis)

> [!warning] Analysis, not measurement
> These are inferences from A1 full-golden-set data. A2 forbids tuning on the test half and reusing A1 speed numbers. Use this page to plan, not to report.

## Blockers to resolve first
1. **Machine:** confirmed as the MacBooks. The SUT is Tze Han's M5 MacBook Pro (Docker VM: 10 CPUs, 9.7 GiB). Make sure it is available and its Docker resources are unchanged. See [[Test Environment]].
2. **`OLLAMA_MAX_LOADED_MODELS=1`.** With it, a cascade reloads models on every escalation. It must be raised to 2, and both models confirmed in `ollama ps`. The brief lists only threads, parallelism and context length as frozen settings, but says to record settings once and hold them constant. So set `MAX_LOADED_MODELS=2` for **all** A2 configurations, including the single-model ones, and state this as a change from A1. *Worth confirming with the lecturer ("ask before collecting measurements").*
3. **Memory fit:** 7B 4.82 GiB + 1B 1.29 GiB ≈ 6.1 GiB (or + 0.5B ≈ 5.5 GiB), against a 9.7 GiB Docker VM. It looks feasible, but must be proven with `ollama ps` evidence.
4. ~~Commit the odd/even split~~ Done: `a2/golden-split/` (98 tuning / 97 test). See [[Golden Test Set]].
5. ~~The A2 brief is untracked~~ Done: committed in PR #11.

## Likely shape of the result
- **Single small models will fail accuracy.** The overall limit ≈ 7B test accuracy − 10 (likely ~70–75%), and the 0.5B and 1B scored 18% and 33%. Per A2, models that fail accuracy need no speed test.
- **Category-based cascade with the 1B (rough check on the full set):** accepting only its high-precision labels (Mortgage, Credit card, Bank account, Money transfer) would accept ~20 of 195 tickets, so **f ≈ 90%**. That is above the ~84% break-even ([[Cascade Classification]]). The cascade would likely be **slower than the 7B alone**, while staying close to it on accuracy.
- **0.5B first stage:** it predicts Credit card ~79% of the time with 11% precision, so almost nothing can be accepted safely and f ≈ 100%.
- **The likely recommendation is the 7B alone**, which A2 accepts ("acceptable to conclude the cascade did not improve on it"). The cascade must still be built, accuracy-tested and speed-tested.
- To give the cascade a real chance, look for a rule with low f: e.g. the 1B's Credit reporting answers when another signal agrees. Measure it on the tuning set and keep f well below 84%.

## Measured inputs (2026-11-13, no machine needed)
- **Limits** (`a2/limits.md`, from A1 runs re-scored on the test set): 7B 81/97 = **83.5%** → overall limit **73.5%**. Tightest category: **Mortgage 85.0%** (the 7B got 9/9, so the cascade may miss at most 1). The 0.5B (15.5%) and 1B (33.0%) fail alone, so they need no speed test.
- **Tuning-set rule analysis** (`a2/tuning-analysis.md`): no candidate is both **within the limits** and **faster than the 7B alone**.
  - Safe category or agreement rules escalate 85–100% of tickets.
  - Length rules are faster but break a category limit. The closest is the 1B at ≤300 chars: Debt collection −16.7 against −15 allowed, which is 1 ticket out of 6.
- The tooling for both Macs is in `docs/a2-playbook.md`.

## Speed-test parameters (estimate)
The 7B's single-request p50 was ~2.8 s, so **S ≈ 3 s** → one ticket every ~6 s (~10/min). Runs last 5 min (the minimum) with ~50 tickets each. That is far above the client peak of 1.73/min, so a pass also demonstrates the client's load. S must be **re-measured** as the brief specifies: 3 different typical tickets, and record their row numbers.

## Deliverables checklist
- [x] Split committed: `a2/golden-split/` via `scripts/split_golden.py` (PR #12, 2026-11-13)
- [ ] Escalation rule written (reproducible) + 2 settings
- [ ] A2 prediction record committed before testing
- [ ] Speed-test row list (outside the golden set; typical and long tickets; fixed order)
- [ ] Service log fields: final model + escalated flag
- [ ] Memory check evidence (`ollama ps`)
- [ ] `Group03_A2.pptx` (≤ 8 slides), due **27 Nov 2026**
