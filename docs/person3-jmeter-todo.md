# Person 3 JMeter Load and Stress Testing To Do

**Owner:** Tze Han  
**Due:** 23:59 Friday 9 October 2026  
**Assignment output:** Slides 7, 8 and 9, raw JMeter `.jtl` files, reconciled service logs, and stress-test evidence

Use this file as the working checklist. The detailed procedure remains in [load-testing.md](load-testing.md).

## Current status

- [x] Open-loop JMeter plan exists at `loadtest/triage.jmx`.
- [x] JMeter result settings exist at `loadtest/triage.properties`.
- [x] Dataset-export script exists at `scripts/export_loadtest_data.py`.
- [x] JTL summary script exists at `scripts/summarise_jtl.py`.
- [x] JMeter-to-service-log reconciliation script exists at `scripts/reconcile.py`.
- [ ] Separate load-generator machine is prepared.
- [ ] System-under-test address is confirmed.
- [ ] Synthetic dry run has passed.
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
- [ ] Start the service with one development model.
- [ ] From the load-generator machine, run:

  ```bash
  curl http://<SUT-IP>:8000/health
  ```

- [ ] Confirm that the health response identifies the expected model.
- [ ] Run JMeter at a very low rate for one minute:

  ```bash
  jmeter -n -t loadtest/triage.jmx -q loadtest/triage.properties \
    -Jhost=<SUT-IP> -Jrate=1 -Jduration=1 \
    -Jdata=<path-to-synthetic.tsv> \
    -l /tmp/triage-dry-run.jtl
  ```

- [ ] Confirm that the `.jtl` file contains successful `POST /tickets` samples.
- [ ] Confirm that the response categories are valid.
- [ ] Confirm that request IDs appear in the `.jtl` file.
- [ ] Confirm that matching request IDs appear in the service log.
- [ ] Run the reconciliation script against the dry-run file.
- [ ] Fix all connectivity, CSV/TSV, JSON or assertion problems before official testing.
- [ ] Delete or clearly retain the dry-run output as non-reportable evidence.

## 4. Prepare the final input when the dataset arrives

- [ ] Confirm that the source file is the course-provided CSV or XLSX.
- [ ] Confirm the team row allocation is 3000–3999.
- [ ] Export the JMeter input:

  ```bash
  python scripts/export_loadtest_data.py \
    --source <course-file.csv-or-xlsx> \
    --rows 3000-3999
  ```

- [ ] Confirm that `loadtest/data/tickets.tsv` was created.
- [ ] Confirm that exactly 1,000 allocated tickets were exported, or document why not.
- [ ] Record the printed ticket-length distribution for the workload model.
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

| Model tag | Model digest confirmed | Arrival rates per minute | Search rate per minute | Duration per run | Runs |
|---|---|---|---|---|---|
| | [ ] | | | | 3 |
| | [ ] | | | | 3 |
| | [ ] | | | | 3 |

- [ ] Include at least the workload-derived average and peak rates.
- [ ] Include another rate if needed to expose capacity behaviour.
- [ ] Use the same official system-under-test machine for every candidate.
- [ ] Use the same prompt, service version, dataset and measurement method for every candidate.
- [ ] Decide whether the first 60 seconds will be excluded from analysis.
- [ ] If using `--skip-s 60`, use it consistently and disclose it on the slide.

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
  -Jhost=<SUT-IP> -Jrate=<rate> -Jduration=<minutes> \
  -Jsearch_rate=<search-rate> \
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
    -Jhost=<SUT-IP> -Jrate=1 -Jrate_end=<high-rate> -Jduration=30 \
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
    --skip-s 60 \
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
