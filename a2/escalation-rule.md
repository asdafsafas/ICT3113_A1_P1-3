# Escalation rule (Assignment 2) — TEMPLATE, team to complete

> Commit this **before the first A2 benchmark run** (with `planning/a2-prediction-record.md`, tag
> `a2-prediction-freeze`). Write it so another team could implement it from this page alone.
> Decided by: _(names)_ on _(date)_. Chosen from the **tuning set only** (`a2/tuning-analysis.md`).

## Cascade

- Small model (answers first): `____` (tag and digest from `models/models.lock.json`)
- Large model (final answer when escalated): `qwen2.5:7b` (`845dbda0ea48…`)
- Second small model (agreement rule only): `____`
- Prompt: `service/prompts/classify_v1.txt` for every call, unchanged. Generation options as in A1.
- Both (all) models resident at once: memory check `results/a2/memory-check/____/SUMMARY.md`.

## The rule

_Exactly what decides accept vs escalate, using only what is known when the ticket arrives
(the small model's **predicted** category, the narrative, a second small model's answer)._

## Two settings

| Setting | Value | Tuning-set escalation | Tuning-set accuracy (est.) | Why this setting |
|---|---|---:|---:|---|
| A | | | | |
| B | | | | |

`.env` for each setting:

```
# Setting A
MODE=cascade
SMALL_MODEL=
LARGE_MODEL=qwen2.5:7b
RULE=
RULE_SETTING=A
ACCEPT_CATEGORIES=
LENGTH_MAX_CHARS=
AGREE_MODEL=
```

## Why this rule

_Which signal it relies on, why it should catch the small model's mistakes, and the risk
(e.g. wrong answers slipping through in a "safe" predicted category)._

## Implementation

`service/app/cascade.py` (`accept()` and `run()`), settings from `.env` (`service/app/config.py`).
Every POST /tickets log line records `small_category`, `escalated`, `final_model` and each model call,
so the escalation fraction is derived from `logs/service/`.
