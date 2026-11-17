# Escalation rule (Assignment 2)

> Freeze this document with `planning/a2-prediction-record.md` before the first A2 benchmark run and tag the
> commit `a2-prediction-freeze`. The rule and settings below were chosen only from the 98-ticket tuning set in
> `a2/tuning-analysis.md`; the 97-ticket test set was not used to choose them.
>
> Decided by: Team P1-3 on 17 November 2026.

## Cascade

- Small model (answers first): `llama3.2:1b-instruct-q4_K_M`
  (`22bc6b92eb0160c4629782fca05a9032c59d306ab2058b7dacc8a4644fbafa02`).
- Large model (final answer when escalated): `qwen2.5:7b`
  (`845dbda0ea48ed749caafd9e6037047aa19acfcfd82e704d7ca97d631a0b697e`).
- Second small model: none; this is not an agreement rule.
- Prompt: `service/prompts/classify_v1.txt` for every call, unchanged. Generation options remain `NUM_CTX=4096`,
  `TEMPERATURE=0` and `SEED=42`, as in Assignment 1.
- Both models are resident at once with `OLLAMA_MAX_LOADED_MODELS=2`. The feasibility evidence is
  `results/a2/memory-check/qwen2.5-7b+llama3.2-1b-instruct-q4_K_M/SUMMARY.md`, which records a pass with no
  alternating-call model reloads.

## The rule

The small model classifies every ticket first. Accept its answer only when its **predicted category** is in the
setting's `ACCEPT_CATEGORIES` list. Otherwise, escalate the same narrative to `qwen2.5:7b` and use the 7B
answer as final. The decision does not use the true category, test-set results, confidence scores or ticket
content beyond the small model's predicted category.

This is implemented by `service/app/cascade.py`: for `RULE=category`, `accept()` returns
`small_category in ACCEPT_CATEGORIES`; `run()` calls the 7B only when `accept()` is false.

## Two settings

| Setting | Accepted small-model predictions | Tuning-set escalation | Simulated tuning accuracy | Worst category change vs 7B | Why this setting |
|---|---|---:|---:|---:|---|
| A | Mortgage, Credit card | 89/98 = 90.8% | 79/98 = 80.6% | Credit reporting: -4.5 points | Conservative setting: both predictions had at least 85% precision on the tuning set. |
| B | Mortgage, Credit card, Bank account or service | 86/98 = 87.8% | 78/98 = 79.6% | Money transfer: -9.1 points | Broader setting: accepts three more tuning tickets to test the accuracy/latency trade-off while remaining inside both limits. |

The reference 7B result on the same tuning rows was 80/98 = 81.6%. Both settings were within the allowed
10-point overall and 15-point per-category drops in the tuning simulation. These figures are design estimates,
not A2 test results.

### Setting A `.env`

```ini
MODE=cascade
SMALL_MODEL=llama3.2:1b-instruct-q4_K_M
LARGE_MODEL=qwen2.5:7b
RULE=category
RULE_SETTING=A
ACCEPT_CATEGORIES=Mortgage,Credit card
```

`LENGTH_MAX_CHARS` and `AGREE_MODEL` must be unset because they are not used by this rule.

### Setting B `.env`

```ini
MODE=cascade
SMALL_MODEL=llama3.2:1b-instruct-q4_K_M
LARGE_MODEL=qwen2.5:7b
RULE=category
RULE_SETTING=B
ACCEPT_CATEGORIES=Mortgage,Credit card,Bank account or service
```

`LENGTH_MAX_CHARS` and `AGREE_MODEL` must be unset because they are not used by this rule.

## Why this rule

On the tuning set, the 1B model's predicted-category precision was 6/7 (85.7%) for Mortgage, 2/2 (100%) for
Credit card and 2/3 (66.7%) for Bank account or service. Its other predicted categories were much less reliable:
Credit reporting was 18/58 (31.0%), Debt collection was 4/27 (14.8%) and Consumer loan was 0/1. Setting A
therefore accepts only the two strongest predictions. Setting B adds the next-best observed category to test
whether accepting a few more tickets improves speed without exceeding the accuracy limits.

The main risk is selection error: a wrong answer can still be accepted when the 1B model incorrectly predicts
one of the allowed categories. The tuning simulation shows this mainly as a 4.5-point loss in true Credit
reporting for both settings and an additional 9.1-point loss in true Money transfer for setting B. The tuning set
is small, so the test-set accuracy run must determine whether either setting actually passes.

## Evidence fields

Every `POST /tickets` service-log entry records `small_category`, `escalated`, `final_model`, `rule`,
`rule_setting` and each model call. The observed escalation fraction and final accuracy will therefore be derived
from the committed service logs and `results/a2/accuracy/`, not from the tuning estimates above.
