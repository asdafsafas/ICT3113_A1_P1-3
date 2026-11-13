# Assignment 2 prediction record — TEMPLATE, team to complete

> Commit **before any A2 testing** (accuracy or speed), together with `a2/escalation-rule.md`, and tag
> `a2-prediction-freeze`. Not revised afterwards. Marks are for **specificity** and for the later account of
> where the predictions were wrong, not for being right. "The cascade will be faster" earns nothing; a range for
> the escalation fraction and a p50 relative to the 7B alone (e.g. "X–Y% slower") can be checked.
> The predictions must be the team's own.

**Committed on:** _(date, time SGT)_ · **Tag:** `a2-prediction-freeze`

**Known before predicting (no A2 measurement yet):** limits and single-model test-set accuracy (`a2/limits.md`,
reused from A1), tuning-set simulation (`a2/tuning-analysis.md`), A1 latencies (7B single-request p50 2.84 s),
memory check (`results/a2/memory-check/`).

## 1. Fastest configuration that will satisfy the accuracy limits, and why

_Name it, with the reason (escalation fraction vs break-even, small-model speed, queueing at the A2 rate)._

## 2. The cascade at each setting

| Setting | Escalation fraction (test set) | Overall accuracy (test set) | Median latency (p50) at the A2 rate | Passes both limits? |
|---|---|---|---|---|
| A | | | | |
| B | | | | |

_How each number was estimated._

## 3. Categories expected to lose the most accuracy when the small model's answer is accepted

_Which, how much (points), and why (e.g. the small model's precision on its accepted categories)._

## 4. Other predictions (optional)

_E.g. escalation fraction under load vs on the test set; p50 spread across the three runs; whether any run
shows a model reload; how S compares with the A1 single-request latency._
