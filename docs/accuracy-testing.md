# Accuracy testing (Step 5, Slide 10)

**Owner:** Zong Han

The brief: send **every golden-set ticket through `POST /tickets`** for each candidate model, and report overall and per-category accuracy against the golden labels, with a confusion matrix.

> Only after the **freeze** (`git tag prediction-freeze` exists, see [golden-set.md](golden-set.md)). Before that, no model may see golden-set tickets.

## Guarded three-model runner

After JMeter testing has completely stopped, the SUT operator can run the full
three-model accuracy suite with one command:

```bash
python3 scripts/run_accuracy_suite.py
```

Type `ACCURACY` only after confirming that JMeter and all other traffic have
stopped. The runner verifies `prediction-freeze`, the 195-ticket golden set, the
frozen prompt, model digests and fixed `.env` settings. For each active model it
then selects the model, performs the reset/warm-up/database-clear procedure below,
runs all golden tickets sequentially, verifies their service-log evidence and
finally creates `results/accuracy/comparison.md`.

If interrupted, run the same command with `--resume`. It continues the newest
partial CSV and skips completed, validated model runs:

```bash
python3 scripts/run_accuracy_suite.py --resume
```

Use `--dry-run` to validate the frozen inputs and print the model plan without
changing `.env`, Docker or result files.

## Playbook: one model

On the SUT machine ([setup.md](setup.md)):

1. Set `MODEL=<tag>` in `.env`, then start fresh. Do this before every full accuracy run or restarted attempt, even when the model is unchanged:
   ```bash
   docker compose down
   docker volume rm triage_triage-data
   docker compose up -d
   python scripts/pull_models.py --check
   curl http://localhost:8000/health      # "status": "ok", correct model and digest
   ```
2. Warm Ollama with invented text, then remove the warm-up row without restarting Ollama:
   ```bash
   curl -X POST http://localhost:8000/tickets \
     -H "Content-Type: application/json" \
     -d '{"narrative":"Synthetic accuracy warm-up ticket. It is not part of the golden set."}'
   docker compose stop triage
   docker compose rm -f triage
   docker volume rm triage_triage-data
   docker compose up -d triage
   curl http://localhost:8000/health
   ```
   This gives every model a freshly restarted, equally warmed Ollama process and an empty measured database. Do not use a golden-set ticket for warm-up.
3. Run the test:
   ```bash
   python scripts/accuracy_test.py
   ```
   It sends the tickets **one at a time** (this measures accuracy, not load), prints each answer as it goes, and writes:
   - `results/accuracy/<timestamp>_<model>.csv`: one line per ticket (golden label, predicted label, status, latency, request ID)
   - `results/accuracy/<timestamp>_<model>.md`: overall accuracy, per-category accuracy, confusion matrix, most common mistakes

   If it stops part-way (e.g. laptop sleeps), continue with `--resume results/accuracy/<that file>.csv`.
4. Don't run load tests on the SUT at the same time.
5. Commit the results and `logs/service/`.

Repeat for every candidate model. The prompt, generation settings and golden set must be identical across models; the `startup` line in the service log records them.

## Reading the report

- **Overall accuracy** = correct / all golden tickets. Failed requests (non-200) count as wrong and are listed separately.
- **Per-category accuracy** = of the golden tickets in a category, the share the model got right (recall). Small categories give noisy percentages; always show the count next to the percentage.
- **Confusion matrix:** rows are golden labels, columns are predictions. Off-diagonal cells are the mistakes; the "most common mistakes" table lists the biggest ones. Compare them with the prediction record's "hardest categories".
- **Mean single-request latency** comes from the same run (sequential requests, no load). It's the measured version of the prediction record's "expected single-request latency".

Once every model has been run, put them side by side for Slide 10:

```bash
python scripts/accuracy_compare.py      # latest run per model -> results/accuracy/comparison.md
```

This gives overall accuracy, per-category recall and precision, the R4 (≥ 80%) and R5 (every category ≥ 70%) verdicts from [requirements.md](../planning/requirements.md), and single-request latency p50/p95 per model.

To regenerate a report from a results CSV without re-running: `python scripts/accuracy_test.py --report results/accuracy/<file>.csv`.

## Reconciling with the logs

Every request carries the ID `acc-<run>-<row>`, so each line of the results CSV matches one line in `logs/service/`. Keep both.
