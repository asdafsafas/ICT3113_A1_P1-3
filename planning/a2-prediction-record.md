# Assignment 2 prediction record

> Freeze this record with `a2/escalation-rule.md` before any A2 accuracy or speed benchmark. Do not revise the
> predictions after the `a2-prediction-freeze` tag is created. Later results should be compared with this frozen
> version, including where these predictions were wrong.

**Prepared on:** 2026-11-17 11:39 SGT

**Freeze tag to create:** `a2-prediction-freeze`

**Known before predicting (no A2 benchmark measurement yet):** the limits and reused Assignment 1 single-model
test accuracy in `a2/limits.md`; the tuning-only simulation in `a2/tuning-analysis.md`; the Assignment 1 7B
single-request mean of 2.84 s; and the completed memory check in `results/a2/memory-check/`.

## 1. Fastest configuration expected to satisfy both accuracy limits

We predict that **7B alone will be the fastest passing configuration**. It already passes by construction at
83.5% overall on the test split and meets every per-category limit. Both cascades are expected to pass, but they
first call the 1B model and then escalate about nine out of ten tickets to the 7B. Their estimated tuning-set mean
service times are therefore 3.04 s for setting A and 2.96 s for setting B, both above the 7B-alone reference of
2.84 s.

The A2 offered rate is derived from the 7B's measured S and targets approximately half of the 7B-alone service
capacity. Adding a 1B call to most tickets raises cascade utilisation and queueing rather than creating enough
accepted fast paths to compensate. Of the cascades, setting B should be faster because it accepts slightly more
1B answers, but we do not expect it to beat 7B alone.

## 2. Predictions for each cascade setting

| Setting | Predicted test-set escalation | Predicted test-set overall accuracy | Predicted p50 at the A2 rate | Passes both limits? |
|---|---:|---:|---:|---|
| A: accept Mortgage or Credit card | **88-95%** (point: 91%) | **78-83%** (point: 81%) | **1.05-1.20x** the 7B-alone p50; approximately 3.0-3.4 s if the 2.84 s A1 reference persists | **Yes** |
| B: also accept Bank account or service | **84-92%** (point: 88%) | **77-82%** (point: 80%) | **1.03-1.18x** the 7B-alone p50; approximately 2.9-3.4 s if the 2.84 s A1 reference persists | **Yes** |

Setting A is based on the tuning simulation's 90.8% escalation and 80.6% accuracy. Setting B is based on 87.8%
escalation and 79.6% accuracy. The ranges allow for sampling variation between the 98 tuning tickets and 97 test
tickets, especially in the small Mortgage and Credit card categories. The p50 ranges start from the tuning
latency estimates (3.04 s and 2.96 s versus 2.84 s for the 7B) and allow extra queueing under open-loop load.

We predict both settings remain above the 73.5% overall limit and within 15 points of the 7B in every category.
This is uncertain for the small categories: one Mortgage error changes its measured accuracy by 11.1 points and
one Credit card error by 14.3 points.

## 3. Categories expected to lose the most accuracy

- **Setting A:** Credit reporting is expected to lose about **0-6 points** versus the 7B. The tuning simulation
  lost one Credit reporting ticket, or 4.5 points, when the 1B incorrectly produced an accepted Mortgage or
  Credit card answer. No other tuning category lost accuracy.
- **Setting B:** Money transfer or service is expected to lose about **5-12 points**, with Credit reporting also
  losing about **0-6 points**. On the tuning set, adding predicted Bank account or service accepted one wrong
  Money transfer answer, producing a 9.1-point loss. This confusion is plausible because complaints about bank
  accounts and transfers often use the same fraud and transaction vocabulary.
- Mortgage and Credit card predictions had high tuning precision, but their test samples contain only 9 and 7
  tickets. We therefore predict they pass while recognising that a single additional error could bring a result
  close to its per-category limit.

## 4. Other predictions

- The escalation fraction under the fixed speed workload will be within **5 percentage points** of the test-set
  escalation fraction for each setting; a larger difference would indicate workload mix sensitivity.
- No official run will show a model reload because the memory check retained the 1B and 7B together with
  `OLLAMA_MAX_LOADED_MODELS=2`. Thus `calls_with_model_reload` should be 0 in all nine run summaries.
- Across the three runs of one configuration, p50 spread will be **under 15% of that configuration's mean p50**
  because the prompt, temperature, seed, workload order and model versions are fixed.
- S will be close to the Assignment 1 7B single-request latency: **2.5-3.5 s**. This implies an A2 offered rate of
  approximately **8.6-12.0 tickets/min**, comfortably above the Assignment 1 client peak of 1.73 tickets/min.
- Setting B will be the faster cascade, but its mean p50 advantage over setting A will be **under 10%**, because
  their predicted escalation fractions differ by only about three percentage points.
