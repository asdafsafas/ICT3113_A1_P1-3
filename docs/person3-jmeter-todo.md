# Person 3 JMeter Load and Stress Testing To Do

**Owner:** Ridwan
**Due:** 23:59 Friday 9 October 2026
**Assignment output:** Slides 7, 8 and 9, raw JMeter `.jtl` files, reconciled service logs, and stress-test evidence

Use this file as the working checklist. The exact official commands and frozen matrix are in [actual-jmeter-test.md](actual-jmeter-test.md); supporting explanations remain in [load-testing.md](load-testing.md).

## Current status

- [x] Open-loop JMeter plan exists at `loadtest/triage.jmx`.
- [x] JMeter result settings exist at `loadtest/triage.properties`.
- [x] Dataset-export script exists at `scripts/export_loadtest_data.py`.
- [x] JTL summary script exists at `scripts/summarise_jtl.py`.
- [x] JMeter-to-service-log reconciliation script exists at `scripts/reconcile.py`.
- [ ] Separate load-generator machine is prepared.
- [ ] System-under-test address is confirmed.
- [x] Local mock dry run has passed with JMeter 5.6.3.
- [x] Separate-machine dry run against the real service has passed.
- [ ] Final dataset has been exported.
- [ ] Golden set and prediction record have been frozen in Git.
- [ ] Official load tests have been completed.
- [ ] Stress-test limit has been found and confirmed.
- [ ] Slides 7, 8 and 9 are complete.

## 1. Information to obtain from teammates

### From Person 1 or the service owner

- [ ] Get the system-under-test IP address and port.
- [ ] Confirm that `GET /health` works from the load-generator machine.
- [ ] Confirm that `POST /tickets` accepts this structure:

  ```json
  {"narrative": "Complaint text"}
  ```

- [ ] Confirm where the service logs are written.
- [ ] Confirm how to verify the active Ollama model.
- [ ] Confirm how the database is cleared between configurations.
- [ ] Confirm that the system is the synchronous, unoptimised baseline.

### From the workload and requirements owner

- [ ] Obtain the average arrival rate to test.
- [ ] Obtain the peak arrival rate to test.
- [ ] Obtain the search-request rate for mixed-load testing, if required.
- [ ] Obtain the response-time, throughput and error-rate requirements.
- [ ] Agree on the duration of each official run.
- [ ] Agree on a drain period long enough for in-flight CPU inference to finish.

### From the model and freeze owners

- [ ] Obtain the final 3–5 candidate model tags.
- [ ] Obtain `models/models.lock.json` containing the pinned digests.
- [ ] Obtain confirmation that the golden set is final.
- [ ] Obtain confirmation that the prediction record is final.
- [ ] Record the freeze commit or tag: `____________________________`.

> **Stop condition:** Do not run an official benchmark until the golden set, prediction record, model pins and prompt have been committed and tagged as the freeze. Synthetic connectivity tests are allowed before the freeze.

## 2. Prepare the separate load-generator machine

- [ ] Install Java 17 or newer.
- [ ] Record the Java version with `java -version`.
- [ ] Install Apache JMeter 5.6.3.
- [ ] Record the JMeter version with `jmeter --version`.
- [ ] Clone or pull this repository onto the load-generator machine.
- [ ] Confirm that `loadtest/triage.jmx` is present.
- [ ] Confirm that `loadtest/triage.properties` is present.
- [ ] Confirm that the Open Model Thread Group loads without an error.
- [ ] Record the load-generator CPU, core count, RAM, operating system and version.
- [ ] Record the network type between the two machines.
- [ ] Measure and record the ping to the system-under-test machine.
- [ ] Confirm that the load generator and system under test are different machines.

## 3. Perform a synthetic dry run before the dataset arrives

- [x] Create a temporary TSV containing 5–10 made-up tickets (`loadtest/data/dry-run-tickets.tsv`).
- [x] Keep the synthetic input separate from the official `tickets.tsv` file.
- [x] Do not use unfinished golden-set narratives.
- [x] Validate the plan locally against the bundled dry-run mock:

  ```bash
  python scripts/run_jmeter_dry_run.py --mock
  ```

- [x] Confirm that the local mock run produces a valid `.jtl`, zero failed samples and complete request-ID reconciliation.
- [ ] Start the real service with one development model on the system-under-test machine.
- [ ] From the load-generator machine, run:

  ```bash
  curl http://<SUT-IP>:8000/health
  ```

- [ ] Confirm that the health response identifies the expected model.
- [ ] Run the same harness from the load-generator machine against the real service:

  ```bash
  python scripts/run_jmeter_dry_run.py \
    --host <SUT-IP> --port 8000
  ```

- [x] Confirm that the local `.jtl` file contains successful `POST /tickets` samples.
- [x] Confirm that the local response categories are valid.
- [x] Confirm that request IDs appear in the local `.jtl` file.
- [ ] Confirm that matching request IDs appear in the service log.
- [ ] Run the reconciliation script against the dry-run file.
- [ ] Fix all connectivity, CSV/TSV, JSON or assertion problems before official testing.
- [ ] Delete or clearly retain the dry-run output as non-reportable evidence.

## 4. Prepare the final 800-ticket input

- [x] Confirm that `loadtest/data/load-test-tickets.csv` contains team rows 3200–3999.
- [x] Confirm that the golden rows 3000–3199 are not used as JMeter load traffic.
- [ ] Export the JMeter input:

  ```bash
  python scripts/export_loadtest_data.py \
    --source loadtest/data/load-test-tickets.csv \
    --rows 3200-3999 \
    --out loadtest/data/tickets.tsv
  ```

- [ ] Confirm that `loadtest/data/tickets.tsv` was created.
- [ ] Confirm that exactly 800 non-golden tickets were exported.
- [ ] Record the printed ticket-length distribution for the test-environment notes.
- [ ] Inspect several short, median-length and long tickets.
- [ ] Check that quotation marks, commas, tabs, newlines and Unicode characters are safely encoded.
- [ ] Run another five-request validation using the real exported input.
- [ ] Confirm that the real-data validation reconciles with the service log.

## 5. Record the test environment for Slide 7

### System-under-test machine

- [ ] CPU model: `____________________________`
- [ ] Physical/logical cores: `____________________________`
- [ ] RAM: `____________________________`
- [ ] Operating system and version: `____________________________`
- [ ] Docker Desktop/Engine version: `____________________________`
- [ ] Docker CPU and memory limits: `____________________________`
- [ ] Ollama version: `____________________________`
- [ ] Service commit: `____________________________`

### Load-generator machine

- [ ] CPU model and cores: `____________________________`
- [ ] RAM: `____________________________`
- [ ] Operating system and version: `____________________________`
- [ ] Java version: `____________________________`
- [ ] JMeter version: `____________________________`
- [ ] Network type and ping: `____________________________`

### Limitations

- [ ] Note whether Wi-Fi, thermal throttling, battery power or background applications could affect results.
- [ ] Explain how the test hardware compares with the client’s commodity CPU servers.
- [ ] State that the load generator ran on a separate machine.

## 6. Lock the official test matrix

Fill this in before running tests.

| Model tag | Model digest confirmed | POST rates per minute | Matching search rates per minute | Duration per run | Runs per configuration |
|---|---|---|---|---|---|
| `qwen2.5:0.5b` | [ ] | 1.45, 1.73, 3.5 | 2.9, 3.5, 7 | 10 min | 3 |
| `llama3.2:1b-instruct-q4_K_M` | [ ] | 1.45, 1.73, 3.5 | 2.9, 3.5, 7 | 10 min | 3 |
| `qwen2.5:3b` | [ ] | 1.45, 1.73, 3.5 | 2.9, 3.5, 7 | 10 min | 3 |
| `qwen2.5:7b` | [ ] | 1.45, 1.73, 3.5 | 2.9, 3.5, 7 | 10 min | 3 |

- [ ] Include at least the workload-derived average and peak rates.
- [ ] Include another rate if needed to expose capacity behaviour.
- [ ] Use the same official system-under-test machine for every candidate.
- [ ] Use the same prompt, service version, dataset and measurement method for every candidate.
- [x] Include the complete measured 10-minute window; do not choose an exclusion after seeing results.
- [ ] Use the same drain period for every comparable run and document it.

## 7. Run each official load-test configuration

Repeat this section for every model and arrival rate.

### Before each configuration

- [ ] Pull the latest frozen repository state on both machines.
- [ ] Close unnecessary applications on both machines.
- [ ] Connect both laptops to power.
- [ ] Activate the intended Ollama model.
- [ ] Record the exact model tag and digest.
- [ ] Stop the old containers.
- [ ] Clear the database according to the documented procedure.
- [ ] Start the baseline service.
- [ ] Check `GET /health` and confirm the correct model.
- [ ] Send one made-up warm-up ticket.
- [ ] Start container CPU and memory monitoring.
- [ ] Confirm nobody else is using the service.

### Three measured runs

- [ ] Run 1 completed and saved as `<rate>rpm_run1.jtl`.
- [ ] Run 2 completed and saved as `<rate>rpm_run2.jtl`.
- [ ] Run 3 completed and saved as `<rate>rpm_run3.jtl`.
- [ ] Matching service logs were retained for all three runs.
- [ ] Matching container-stat files were retained for all three runs.
- [ ] No GUI result listeners were enabled during measurement.
- [ ] No accuracy test or other workload ran at the same time.

Command template:

```bash
jmeter -n -t loadtest/triage.jmx -q loadtest/triage.properties \
  -Jhost=<SUT-IP> -Jport=8000 \
  -Jrate=<rate> -Jrate_end=<rate> -Jsearch_rate=<search-rate> \
  -Jduration=10 -Jdrain=5 -Jtimeout_ms=600000 \
  -Jdata=<absolute-path-to-loadtest/data/tickets.tsv> \
  -l results/load/<model>/<rate>rpm_run<N>.jtl
```

### Validate each measured run immediately

- [ ] JMeter completed without an unexpected interruption.
- [ ] The `.jtl` file is non-empty.
- [ ] The achieved request count is plausible for the configured arrival rate and duration.
- [ ] The active model was unchanged during the run.
- [ ] Reconciliation found every JMeter request in the service log.
- [ ] “Other requests during the run” equals zero.
- [ ] Environmental problems and discarded runs are recorded in `results/load/RUNS.md`.
- [ ] Invalid runs were repeated rather than silently included.

Reconciliation command:

```bash
python scripts/reconcile.py results/load/<model>/<rate>rpm_run<N>.jtl
```

## 8. Conduct the stress test

- [ ] Select at least one representative candidate model.
- [ ] Estimate capacity from its single-request latency: approximately `60 / latency_seconds` tickets per minute if requests are processed serially.
- [ ] Select a ramp ending well above the estimated capacity.
- [ ] Run the open-loop ramp stress test:

  ```bash
  jmeter -n -t loadtest/triage.jmx -q loadtest/triage.properties \
    -Jhost=<SUT-IP> -Jrate=3.5 -Jrate_end=12 -Jsearch_rate=7 \
    -Jduration=30 -Jdrain=10 -Jtimeout_ms=600000 \
    -l results/load/<model>/stress_ramp_run1.jtl
  ```

- [ ] Generate or inspect latency-over-time and throughput-over-time charts.
- [ ] Identify the approximate point where latency begins growing continuously or throughput stops increasing.
- [ ] Run a constant-rate confirmation just below that point.
- [ ] Run a constant-rate confirmation just above that point.
- [ ] State the measured system limit.
- [ ] Diagnose the limiting component using service timings, CPU/memory statistics and errors.
- [ ] Reconcile every stress-test request with the service logs.

## 9. Summarise and verify results

- [ ] Summarise all official load runs:

  ```bash
  python scripts/summarise_jtl.py results/load \
    --csv results/load/summary.csv
  ```

- [ ] Confirm that every configuration contains three runs.
- [ ] Report p50, p95 and p99 latency.
- [ ] Report achieved throughput.
- [ ] Report error rate.
- [ ] Report the mean and spread across the three runs.
- [ ] Compare achieved throughput with offered arrival rate.
- [ ] Check latency over time for queue growth.
- [ ] Compare each result with the final requirements.
- [ ] Identify which models and rates pass or fail.
- [ ] Confirm that every reported number can be traced to a `.jtl` file and service log.

If mixed-load search testing is used:

```bash
python scripts/summarise_jtl.py results/load --label "GET /search"
```

## 10. Complete the presentation content

### Slide 7 — Test environment

- [ ] Hardware and software for both machines.
- [ ] Diagram or clear statement showing the machines are separate.
- [ ] Network details and ping.
- [ ] Assumptions and limitations.
- [ ] Explanation of how results might scale to the client environment.

### Slide 8 — Testing playbook

- [ ] Open-loop arrival process and why it was used.
- [ ] Data flow from `tickets.tsv` to JMeter to `POST /tickets`.
- [ ] Warm-up, reset and model-switching procedure.
- [ ] Arrival rates, duration and three-run repetition.
- [ ] JMeter/service-log reconciliation procedure.
- [ ] Stress-test procedure.

### Slide 9 — Load and stress results

- [ ] Compact table or chart comparing models and arrival rates.
- [ ] p50, p95 and p99 latency.
- [ ] Achieved throughput and error rate.
- [ ] Mean and spread across three runs.
- [ ] Stress-test limit.
- [ ] Short bottleneck diagnosis.
- [ ] Clear pass/fail statements against the requirements.

## 11. Commit and hand off

- [ ] Commit every official `.jtl` file.
- [ ] Commit every matching service log.
- [ ] Commit every container-resource-stat file.
- [ ] Commit `results/load/summary.csv`.
- [ ] Commit `results/load/RUNS.md`.
- [ ] Commit the final Slides 7–9 content or source material.
- [ ] Send the verified result table to the recommendation owner.
- [ ] Send the bottleneck diagnosis to the team.
- [ ] Ask another member to independently trace at least three slide values back to raw evidence.
- [ ] Confirm that no synthetic dry-run number appears in the final slides.

## Suggested remaining schedule

### Monday 5 October

- [ ] Prepare the separate JMeter machine.
- [ ] Complete the synthetic dry run.
- [ ] Resolve all connectivity and JMX problems.
- [ ] Obtain arrival rates and requirements from teammates.

### Tuesday 6 October

- [ ] Export and validate the real input once available.
- [ ] Confirm the freeze commit.
- [ ] Begin official three-run load tests.

### Wednesday 7 October

- [ ] Complete remaining load tests.
- [ ] Perform and confirm the stress test.
- [ ] Reconcile and summarise all results.

### Thursday 8 October

- [ ] Complete Slides 7–9.
- [ ] Support the final recommendation and full-deck review.
- [ ] Verify every reported number against raw evidence.

### Friday 9 October

- [ ] Reserve for reruns, final checks and submission buffer only.

## Definition of done

Person 3’s work is complete only when:

- [ ] The load generator and system under test were separate machines.
- [ ] Traffic was open-loop at controlled arrival rates.
- [ ] Every official configuration has three valid runs.
- [ ] p50, p95, p99, achieved throughput and error rate are reported.
- [ ] Mean and spread across runs are reported.
- [ ] At least one meaningful system limit was measured through a stress test.
- [ ] The bottleneck is supported by evidence.
- [ ] Every reported request reconciles with the service logs.
- [ ] All raw `.jtl` and log files are committed.
- [ ] Slides 7, 8 and 9 are complete and internally consistent.
