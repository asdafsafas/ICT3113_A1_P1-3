# Actual JMeter Test Instructions

**Owner:** Ridwan  
**Purpose:** Official Assignment 1 load and stress testing on two separate Macs  
**Evidence produced:** JMeter `.jtl` files, service logs, container statistics, reconciliation output and summary tables

This guide starts after the synthetic dry run has passed. Do not report any result from `results/dry-run/`.

## 1. Official test matrix

Use the same system-under-test Mac, load-generator Mac, prompt, service commit, model settings and 800-ticket input for every run.

### Candidate models

- `qwen2.5:0.5b`
- `llama3.2:1b-instruct-q4_K_M`
- `qwen2.5:3b`
- `qwen2.5:7b`

### Load configurations

| Configuration | POST `/tickets` | GET `/search` | Arrivals | Duration | Drain | Runs per model |
|---|---:|---:|---|---:|---:|---:|
| Average | 1.1/min | 4.5/min | Open-loop | 15 min | 5 min | 3 |
| Peak | 2.4/min | 8/min | Open-loop | 15 min | 5 min | 3 |
| Headroom | 4.8/min | 8/min | Open-loop | 15 min | 5 min | 3 |

This is 36 measured load-test runs: 4 models × 3 configurations × 3 runs. Allow about 12 hours for the configured arrival and drain periods, excluding setup and reruns.

### Requirements checked

- **R1:** At 2.4 tickets/min plus 8 searches/min, POST p95 ≤ 15 s, POST p99 ≤ 30 s and error rate ≤ 1%, with no continuing latency growth.
- **R2:** At the same peak load, search p95 ≤ 1 s and search p99 ≤ 2 s.
- **R3:** At 4.8 tickets/min plus 8 searches/min, sustain at least 4.8 successful tickets/min, POST p95 ≤ 30 s, error rate ≤ 1% and no continuing latency growth.

## 2. Stop gate before official testing

Do not start official runs until every item below is confirmed.

- [ ] Golden set is frozen: 195 labelled tickets from the original 200-ticket pool.
- [ ] Prediction record is final and committed.
- [ ] Four model tags and digests are committed.
- [ ] Classification prompt and generation settings are committed.
- [ ] Freeze commit or tag is recorded: `____________________________`.
- [ ] `OLLAMA_NUM_PARALLEL=1` is confirmed inside the running container.
- [ ] Both Macs have pulled the same frozen commit.
- [ ] Nobody will run an accuracy test against the service during JMeter testing.

Record the frozen revision on both Macs:

```bash
git rev-parse HEAD
git describe --tags --always
```

## 3. Prepare the 800-ticket JMeter input

The repository contains `loadtest/data/load-test-tickets.csv` with rows 3200–3999. Convert it to the one-line TSV format expected by `loadtest/triage.jmx`:

```bash
python3 scripts/export_loadtest_data.py \
  --source loadtest/data/load-test-tickets.csv \
  --rows 3200-3999 \
  --out loadtest/data/tickets.tsv
```

Validate it:

```bash
wc -l loadtest/data/tickets.tsv
head -1 loadtest/data/tickets.tsv
tail -1 loadtest/data/tickets.tsv
```

Expected line count: `800`. Do not point the JMeter plan directly at the CSV; the plan expects tab-separated rows containing JSON-encoded narratives.

- [ ] `tickets.tsv` has 800 lines.
- [ ] First row ID is 3200.
- [ ] Last row ID is 3999.
- [ ] The golden rows 3000–3199 are not present.

## 4. Prepare the two Macs

### System-under-test Mac

This Mac runs Docker, the triage service and Ollama. Keep it connected to AC power and close unnecessary applications.

Record:

```bash
system_profiler SPHardwareDataType SPSoftwareDataType
docker version
docker compose version
docker compose exec ollama ollama --version
docker compose exec ollama printenv OLLAMA_NUM_PARALLEL
```

The last command must print:

```text
1
```

### Load-generator Mac

This Mac runs JMeter and must be different from the system-under-test Mac.

```bash
java -version
export JMETER_BIN="/Users/ridwan/Downloads/apache-jmeter-5.6.3/bin/jmeter"
export TICKET_DATA="$(pwd)/loadtest/data/tickets.tsv"
"$JMETER_BIN" --version
```

Set the service address for the current network:

```bash
export SUT_HOST="<SYSTEM-UNDER-TEST-IP>"
curl "http://$SUT_HOST:8000/health"
ping -c 10 "$SUT_HOST"
```

Record the network type and ping results. If the service is unreachable, fix the network or firewall before proceeding.

## 5. Select and verify one model

On the system-under-test Mac, edit `.env` and set exactly one model:

```text
MODEL=qwen2.5:0.5b
```

Also confirm these fixed settings:

```text
NUM_CTX=4096
TEMPERATURE=0
SEED=42
OLLAMA_TIMEOUT_S=600
OLLAMA_NUM_PARALLEL=1
OLLAMA_MAX_LOADED_MODELS=1
```

Recreate the triage container after changing the model:

```bash
docker compose up -d --force-recreate triage
curl http://localhost:8000/health
```

Confirm that `/health` returns the intended tag and digest. Warm up the model with an invented ticket:

```bash
curl -X POST http://localhost:8000/tickets \
  -H "Content-Type: application/json" \
  -d '{"narrative":"Synthetic warm-up ticket. Do not include this request in measured results."}'

docker compose exec ollama ollama ps
```

Confirm `ollama ps` shows the intended model and `100% CPU`.

## 6. Reset before every measured run

Resetting before every run gives each run the same empty starting database. It does not delete the downloaded Ollama models.

On the system-under-test Mac:

```bash
docker compose stop triage
docker compose rm -f triage
docker volume rm triage_triage-data
docker compose up -d triage
curl http://localhost:8000/health
```

Warm up again after the reset, then wait until the request finishes. Do not start JMeter while the warm-up is still running.

```bash
curl -X POST http://localhost:8000/tickets \
  -H "Content-Type: application/json" \
  -d '{"narrative":"Synthetic warm-up ticket. Do not include this request in measured results."}'
```

The warm-up remains in the database. If the team requires the measured database to start with exactly zero rows, reset once more after warming up. Ollama stays loaded because only the triage container and data volume are reset.

## 7. Start resource monitoring

On the system-under-test Mac, set a model folder name with the colon replaced by a hyphen. Example:

```bash
export MODEL_SLUG="qwen2.5-0.5b"
mkdir -p "results/load/$MODEL_SLUG"
```

Before each run, start this in a separate terminal. Replace the filename with the matching configuration and run number:

```bash
while true; do
  docker stats --no-stream --format "{{.Name}},{{.CPUPerc}},{{.MemUsage}}" | \
    sed "s/^/$(date +%s),/"
  sleep 5
done > "results/load/$MODEL_SLUG/2.4rpm_s8_run1_stats.csv"
```

Leave it running until JMeter prints `... end of run`, then stop it with Control-C.

## 8. Run the official load tests

Run JMeter only in non-GUI mode. Use a 600-second client timeout so it matches `OLLAMA_TIMEOUT_S=600`.

On the load-generator Mac:

```bash
mkdir -p "results/load/$MODEL_SLUG"
```

### Average load: 1.1 tickets/min and 4.5 searches/min

Run this three times, changing `run1` to `run2` and `run3`:

```bash
"$JMETER_BIN" -n \
  -t loadtest/triage.jmx \
  -q loadtest/triage.properties \
  -Jhost="$SUT_HOST" \
  -Jport=8000 \
  -Jrate=1.1 \
  -Jrate_end=1.1 \
  -Jsearch_rate=4.5 \
  -Jduration=15 \
  -Jdrain=5 \
  -Jtimeout_ms=600000 \
  -Jdata="$TICKET_DATA" \
  -l "results/load/$MODEL_SLUG/1.1rpm_s4.5_run1.jtl" \
  -j "results/load/$MODEL_SLUG/1.1rpm_s4.5_run1_jmeter.log"
```

### Peak load: 2.4 tickets/min and 8 searches/min

Run this three times:

```bash
"$JMETER_BIN" -n \
  -t loadtest/triage.jmx \
  -q loadtest/triage.properties \
  -Jhost="$SUT_HOST" \
  -Jport=8000 \
  -Jrate=2.4 \
  -Jrate_end=2.4 \
  -Jsearch_rate=8 \
  -Jduration=15 \
  -Jdrain=5 \
  -Jtimeout_ms=600000 \
  -Jdata="$TICKET_DATA" \
  -l "results/load/$MODEL_SLUG/2.4rpm_s8_run1.jtl" \
  -j "results/load/$MODEL_SLUG/2.4rpm_s8_run1_jmeter.log"
```

### Headroom load: 4.8 tickets/min and 8 searches/min

Run this three times:

```bash
"$JMETER_BIN" -n \
  -t loadtest/triage.jmx \
  -q loadtest/triage.properties \
  -Jhost="$SUT_HOST" \
  -Jport=8000 \
  -Jrate=4.8 \
  -Jrate_end=4.8 \
  -Jsearch_rate=8 \
  -Jduration=15 \
  -Jdrain=5 \
  -Jtimeout_ms=600000 \
  -Jdata="$TICKET_DATA" \
  -l "results/load/$MODEL_SLUG/4.8rpm_s8_run1.jtl" \
  -j "results/load/$MODEL_SLUG/4.8rpm_s8_run1_jmeter.log"
```

### After every run

- [ ] Wait for `... end of run`.
- [ ] Stop container monitoring with Control-C.
- [ ] Confirm the JTL exists and is non-empty.
- [ ] Record the run in the run log.
- [ ] Reconcile it before proceeding.
- [ ] Reset the database before the next measured run.
- [ ] Do not run accuracy testing or manually call the service during the run.

## 9. Reconcile every run

The `.jtl` is created on the load-generator Mac and the service log is created on the system-under-test Mac under `logs/service/`. Bring both into one checkout before reconciliation.

```bash
python3 scripts/reconcile.py \
  "results/load/$MODEL_SLUG/2.4rpm_s8_run1.jtl"
```

A valid run should show:

- Every JMeter request that reached the service has a matching request ID.
- No unexplained status-code mismatch.
- `Other requests the service handled during the run: 0`.

Connection failures that never reached the service can be missing from the service log, but they must be explained and counted as JMeter errors.

## 10. Repeat for all four models

Finish the nine load runs for one model before changing `.env` to the next model. This minimises model switching and configuration mistakes.

Use these result folders:

```text
results/load/qwen2.5-0.5b/
results/load/llama3.2-1b-instruct-q4_K_M/
results/load/qwen2.5-3b/
results/load/qwen2.5-7b/
```

For every model:

- [ ] Correct tag and digest confirmed through `/health`.
- [ ] `ollama ps` confirms CPU-only inference.
- [ ] Three average runs completed.
- [ ] Three peak runs completed.
- [ ] Three headroom runs completed.
- [ ] All nine JTL files reconciled.
- [ ] All nine stats files retained.
- [ ] JMeter logs retained for failed or suspicious runs.

## 11. Conduct the 7B stress test

The prediction estimates the 7B limit near 9.5 tickets/min. Use the 7B model because its limit is reachable within the planned rates.

### Ramp test

Reset, warm up and start resource monitoring. Then run:

```bash
"$JMETER_BIN" -n \
  -t loadtest/triage.jmx \
  -q loadtest/triage.properties \
  -Jhost="$SUT_HOST" \
  -Jport=8000 \
  -Jrate=2.4 \
  -Jrate_end=12 \
  -Jsearch_rate=8 \
  -Jduration=30 \
  -Jdrain=10 \
  -Jtimeout_ms=600000 \
  -Jdata="$TICKET_DATA" \
  -l "results/load/qwen2.5-7b/stress_2.4to12rpm_s8_run1.jtl" \
  -j "results/load/qwen2.5-7b/stress_2.4to12rpm_s8_run1_jmeter.log"
```

Generate an HTML dashboard:

```bash
"$JMETER_BIN" -g \
  results/load/qwen2.5-7b/stress_2.4to12rpm_s8_run1.jtl \
  -o results/load/qwen2.5-7b/stress_2.4to12rpm_s8_run1_report
```

Inspect:

- Response Times Over Time.
- Transactions per Second.
- Active Threads Over Time.
- Error table.

### Confirm below and above the limit

After separate resets, run one 15-minute constant-rate confirmation at each rate:

- **Below:** 7.2 tickets/min plus 8 searches/min.
- **Above:** 9.6 tickets/min plus 8 searches/min.

Use the normal command with `rate` and `rate_end` both set to the chosen value. Name the files:

```text
stress_7.2rpm_s8_confirm_run1.jtl
stress_9.6rpm_s8_confirm_run1.jtl
```

The measured limit is where achieved throughput stops following offered throughput and latency continues increasing through the run. Do not identify the limit from one high percentile alone; confirm it from the time-series charts, service queueing time and CPU statistics.

## 12. Summarise the results

Classification results:

```bash
python3 scripts/summarise_jtl.py results/load \
  --label "POST /tickets" \
  --csv results/load/post-summary.csv
```

Search results:

```bash
python3 scripts/summarise_jtl.py results/load \
  --label "GET /search" \
  --csv results/load/search-summary.csv
```

The model is warmed before each run, so these commands include the full measured 15 minutes. If the team decides before testing to exclude an initial measurement window, record that decision in the frozen playbook, apply the same `--skip-s` value everywhere and disclose it on the results slide. Never choose an exclusion after looking at the results. Keep the raw JTL files unchanged.

For every standard configuration, verify the summary reports `Runs = 3`.

## 13. Decide pass or fail

For each model, record:

| Model | R1 peak POST | R2 peak search | R3 headroom | Stress limit | Main evidence |
|---|---|---|---|---|---|
| qwen2.5:0.5b | | | | | |
| llama3.2:1b-instruct-q4_K_M | | | | | |
| qwen2.5:3b | | | | | |
| qwen2.5:7b | | | | | |

For the bottleneck diagnosis, compare:

- JMeter end-to-end latency.
- Service `latency_ms`.
- Ollama `ollama_total_ms`.
- `latency_ms - ollama_total_ms` as approximate queueing and service overhead.
- Ollama CPU and memory from the stats files.
- Offered versus achieved throughput.

Evidence for an Ollama CPU bottleneck is: Ollama CPU remains near its maximum, achieved throughput stops increasing, and queueing time grows while individual Ollama processing time remains comparatively stable.

## 14. Run log template

Create or update `results/load/RUNS.md` and add every successful, failed and discarded run.

| Date/time SGT | Model | POST/min | Search/min | Duration | Run | JTL file | Reconciled | Valid | Notes |
|---|---|---:|---:|---:|---:|---|---|---|---|
| | | | | | | | | | |

Never delete evidence of a failed run. Mark it invalid and explain why it was rerun.

## 15. Completion checklist

- [ ] Separate Macs were used for the service and load generator.
- [ ] All official traffic was open-loop.
- [ ] The 800-ticket load dataset was used.
- [ ] Accuracy testing did not run concurrently.
- [ ] Every standard configuration has three valid runs.
- [ ] Every reported run reconciles with service logs.
- [ ] p50, p95, p99, throughput and error rate are reported.
- [ ] Mean and min–max spread across the three runs are reported.
- [ ] The 7B stress limit was found and confirmed.
- [ ] The measured bottleneck is supported by latency, throughput and resource evidence.
- [ ] Raw JTL files, service logs, stats and summaries are committed.
- [ ] No dry-run timing appears in the final report or slides.
