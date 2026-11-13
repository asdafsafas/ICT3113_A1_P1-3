# Assignment 2 playbook (two Macs)

**Due:** 23:59 Fri 27 Nov 2026 · **Brief:** `ICT3113_Assignment_2 - Copy (1).pdf`

Same two machines as Assignment 1:

| Role | Machine | Runs |
|---|---|---|
| **SUT Mac** (system under test) | Tze Han's MacBook Pro M5, Docker VM 10 CPUs / 9.7 GiB, **unchanged from A1** | Docker (triage + Ollama), `scripts/a2_sut_agent.py`, `scripts/a2_accuracy.py` |
| **LG Mac** (load generator) | Ridwan's Mac, JMeter 5.6.3 | `scripts/run_a2_speed.py` |

Both on the same network. Python 3.9+ (`python3`) on both; the scripts use the standard library only.

## What is already done (no machine needed)

| Item | File | Script |
|---|---|---|
| Golden split: tuning 98 (odd rows) / test 97 (even rows) | `a2/golden-split/` | `scripts/split_golden.py` |
| Accuracy limits from the top model's **test-set** accuracy | `a2/limits.md`, `a2/limits.json` | `scripts/a2_limits.py` |
| Single-model test-set accuracy (reuses the A1 runs, as the brief allows) | `a2/limits.md` | `scripts/a2_limits.py` |
| Rule design aid (**tuning set only**) | `a2/tuning-analysis.md` | `scripts/a2_tuning_analysis.py` |
| Speed workload: S tickets, warm-up tickets, fixed speed-test rows | `a2/speed-workload/` | `scripts/a2_workload.py` |

Limits: overall **73.5%** (7B 83.5% − 10). Per category: see `a2/limits.md` (Mortgage 85.0% is the tightest; Mortgage and Credit card are too small for a fair per-category test).
Neither small model passes alone, so only the **7B alone** and the **cascade at its two settings** are speed-tested.

---

## Order of work

```
1 SUT: settings + memory check      ->  2 TEAM: choose rule + 2 settings, write predictions, COMMIT
                                     ->  3 SUT: accuracy of each cascade setting (test set)
                                     ->  4 both: measure S  ->  5 both: speed tests (3 runs each)  ->  6 summarise
```

The brief requires the **prediction record and the written escalation rule to be committed before the first
A2 benchmark run** (steps 3–5). Step 1 is a feasibility check, not a benchmark.

---

## Step 1 (SUT Mac): settings and memory check

1. Pull the latest `main` and check the pins:
   ```bash
   cd ~/Documents/GitHub/ICT3113_A1_P1-3 && git pull
   docker compose up -d
   python3 scripts/pull_models.py --check          # all three must say OK
   ```
2. In `.env`, set **once for the whole of A2** and do not change again:
   ```
   OLLAMA_MAX_LOADED_MODELS=2        # 3 only if the team picks RULE=agreement (two small models + 7B)
   ```
   Everything else stays as in A1 (`OLLAMA_NUM_PARALLEL=1`, `NUM_CTX=4096`, `TEMPERATURE=0`, `SEED=42`, Ollama 0.35.1).
   Then `docker compose up -d ollama` and confirm: `docker compose exec ollama env | grep OLLAMA_`.
   > This setting is a change from A1 (where it was 1). It does not change threads, parallelism or context length,
   > which the brief freezes; state it on the test-environment slide. Worth a one-line check with the lecturer.
3. Memory check for each pair the team might use (about 2 minutes each):
   ```bash
   python3 scripts/a2_sut_agent.py memory-check --models qwen2.5:7b llama3.2:1b-instruct-q4_K_M
   python3 scripts/a2_sut_agent.py memory-check --models qwen2.5:7b qwen2.5:0.5b
   ```
   It restarts Ollama, loads both models, then alternates invented tickets between them. **PASS** means
   `ollama ps` lists both and no call had to reload a model. Evidence (incl. `ollama ps`) goes to
   `results/a2/memory-check/`. Commit it. If a pair fails, that pair cannot be used.

## Step 2 (whole team): rule, settings, predictions, then commit

1. Read `a2/tuning-analysis.md` (tuning set only) and choose **one rule** and **two settings**.
   Supported by the service without code changes (all set in `.env`):

   | RULE | Accepts the small model's answer when… | Setting |
   |---|---|---|
   | `category` | its **predicted** category is in `ACCEPT_CATEGORIES` | the category list |
   | `length` | the ticket has ≤ `LENGTH_MAX_CHARS` characters (longer tickets go straight to the 7B) | the cut-off |
   | `agreement` | `SMALL_MODEL` and `AGREE_MODEL` give the same answer (optionally only for `ACCEPT_CATEGORIES`) | the category filter |

   You may re-run the analysis with your own candidates (edit the lists in `scripts/a2_tuning_analysis.py`).
   **Never** use the test set to choose.
2. Fill in `a2/escalation-rule.md` (the rule, exactly reproducible) and `planning/a2-prediction-record.md`.
3. Commit both and tag before any benchmark:
   ```bash
   git add a2/escalation-rule.md planning/a2-prediction-record.md
   git commit -m "A2: escalation rule and prediction record (before testing)"
   git tag -a a2-prediction-freeze -m "A2 rule and predictions before the first benchmark"
   git push && git push origin a2-prediction-freeze
   ```

## Switching configuration (SUT Mac, any time a step says so)

Edit `.env`, then `docker compose up -d triage` and check `curl -s localhost:8000/health`.

**7B alone:**
```
MODE=single
MODEL=qwen2.5:7b
```
**Cascade, setting A** (example; use the team's rule):
```
MODE=cascade
SMALL_MODEL=llama3.2:1b-instruct-q4_K_M
LARGE_MODEL=qwen2.5:7b
RULE=category
RULE_SETTING=A
ACCEPT_CATEGORIES=Mortgage,Credit card
```
**Cascade, setting B:** same, with `RULE_SETTING=B` and the second setting's value.
Never change `OLLAMA_*`, `NUM_CTX`, `TEMPERATURE` or `SEED` between configurations.

## Step 3 (SUT Mac): accuracy of each cascade setting

For each setting (switch configuration first):
```bash
python3 scripts/a2_accuracy.py --config cascade-A      # 97 test tickets, one at a time
python3 scripts/a2_accuracy.py --config cascade-B
```
Each writes `results/a2/accuracy/<time>_<config>_test.{csv,json,md}`: overall and per-category accuracy against
the limits (with counts), the confusion matrix, the escalation count, and the accuracy of escalated vs accepted
tickets. Optional, for the slide comparison: `--split tuning`. Commit `results/a2/accuracy/` and `logs/service/`.

Single models: not re-run; `a2/limits.md` reuses A1 (say so in the report).

## Step 4 (both Macs): measure S once

1. **SUT Mac:** switch to **7B alone**, then start the agent and leave it running for steps 4–5:
   ```bash
   export A2_AGENT_TOKEN="<shared random token, 12+ characters>"     # same on both Macs, never committed
   python3 scripts/a2_sut_agent.py agent --bind 0.0.0.0
   ```
2. **LG Mac:**
   ```bash
   export A2_AGENT_TOKEN="<same token>"
   export SUT=<SUT Mac IP>
   python3 scripts/run_a2_speed.py measure-s --host $SUT
   ```
   It restarts Ollama, warms up, sends the 3 typical-length tickets (rows 3405, 3530, 3738) one at a time and
   takes the middle time as **S**. It derives everything else and saves `results/a2/s-measure/S.json`:
   rate = 60 / (2 × S) per minute, run length = S minutes (≥ 5), response timeout = 10 × S s (≥ 5 min),
   pause = timeout + 60 s. Commit it.
3. Compare the rate with the client peak from A1 (1.73 tickets/min). If it is higher (it will be), the result also
   shows the system handles the client's peak: say so on the limitations slide.

## Step 5 (both Macs): speed tests

Before the first real run, check JMeter accepts the A2 plan (LG Mac, 1 minute, against the A1 mock server):
```bash
python3 scripts/mock_triage_server.py --port 18000 --log-dir results/dry-run/a2 &
$JMETER_BIN -n -t loadtest/triage_a2.jmx -q loadtest/triage.properties -Jhost=127.0.0.1 -Jport=18000 \
  -Jrate=12 -Jduration_s=60 -Jpause_s=10 -Jtimeout_ms=5000 -l results/dry-run/a2/check.jtl
kill %1; wc -l results/dry-run/a2/check.jtl        # about 13 lines (header + ~12 requests)
```
(`results/dry-run/` is git-ignored; never report it.)

Then, for each configuration (**SUT Mac** switches `.env` + `docker compose up -d triage`; the agent keeps running):
```bash
# LG Mac
python3 scripts/run_a2_speed.py run --host $SUT --config 7b-alone  --jmeter $JMETER_BIN
python3 scripts/run_a2_speed.py run --host $SUT --config cascade-A --jmeter $JMETER_BIN
python3 scripts/run_a2_speed.py run --host $SUT --config cascade-B --jmeter $JMETER_BIN
```
Each command does 3 runs. Every run: the agent restarts Ollama (clears its prompt cache), sends the same
3 warm-up tickets, warms every model of the configuration, checks `ollama ps` lists them all, records
`GET /stats`, starts `docker stats`; JMeter sends the fixed ticket list open-loop at the S rate; the agent then
records `ollama ps` and `GET /stats` again and returns the run's service-log lines. Evidence per run in
`results/a2/speed/<config>/`: `.jtl`, JMeter log, `service-*.jsonl`, `_stats.csv`, `_health.json` (with /stats
before and after), `ollama ps` before/after, SUT audit log, `_run.json` (the run's numbers). Reconciliation runs
automatically. An interrupted command can be re-run; finished runs are skipped.

Each configuration takes about 3 × (S min + timeout + 1 min + ~2 min reset) ≈ 40 minutes when S ≈ 3 s.
Use `--dry-run` to see the JMeter commands first.

Watch for: **WARNING … reloaded a model** (the cascade's models did not stay resident: that run measures loading,
not the cascade) and **unfinished** requests (report them; do not throw the run away).

## Step 6: summarise and commit

```bash
python3 scripts/run_a2_speed.py summarise      # writes results/a2/speed/SUMMARY.md
git add results/a2 logs/service && git commit -m "A2 speed tests" && git push
```
`SUMMARY.md` has, per configuration: p50 per run with mean and min–max, **pooled p95 with n**, throughput,
errors and escalation fraction from the logs; and per run: sent / completed / errored / unfinished and the
`/stats` increase. No p99 (the brief says the sample is too small).

## Recommendation (Step 5 of the brief)

The fastest configuration that passes **both** limits on the test set. State how much faster it is than the
7B alone and how much accuracy it gives up, overall and by category. If the cascade is not faster, say so and
explain it with the measured escalation fraction and latencies.
