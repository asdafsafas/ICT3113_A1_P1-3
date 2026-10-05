# Load and stress testing (Step 5, Slides 7–9)

**Owner:** Tze Han

The rules the brief sets, which this setup already follows:

- **Open-loop traffic** at controlled arrival rates. `loadtest/triage.jmx` uses JMeter's **Open Model Thread Group**: requests arrive on schedule (random, Poisson-style arrivals) whether or not earlier ones have finished, so queue build-up is visible. Closed-loop results are not accepted.
- **p50, p95, p99 latency, achieved throughput and error rate** at each arrival rate.
- **Three runs per configuration**, reporting the mean and the spread.
- **Keep every `.jtl`** in the repo; they must reconcile with the service logs.
- **The load generator runs on a different machine** from the service.

## 1. The two machines

| Role | Runs | Notes |
|---|---|---|
| **System under test (SUT)** | Docker: triage + ollama ([setup.md](setup.md)) | The same machine for every reported run |
| **Load generator (LG)** | JMeter | Any laptop, on the same network |

Connect both to the **same network**, wired if possible. Record the network type and the round-trip time (`ping <SUT-IP>` from the LG).

Find the SUT's IP address: `ipconfig` (Windows) or `ipconfig getifaddr en0` (Mac). From the LG, check that you can reach it: `curl http://<SUT-IP>:8000/health`. If it times out, allow inbound port 8000 in the SUT's firewall (Windows usually prompts when Docker first starts). University Wi-Fi often blocks device-to-device traffic; a phone hotspot or a home router works if so.

## 2. Set up the load generator (once)

1. Install **Java 17+** ([Adoptium](https://adoptium.net)). Check with `java -version`.
2. Download **Apache JMeter 5.6.3** (binaries zip) from [jmeter.apache.org](https://jmeter.apache.org/download_jmeter.cgi) and unzip it. The command is `apache-jmeter-5.6.3/bin/jmeter` (Mac) or `jmeter.bat` (Windows). The Open Model Thread Group needs JMeter **5.5 or newer**.
3. Clone this repo on the LG too (it needs `loadtest/` and writes to `results/load/`).
4. Get the ticket data file (Kannan exports it once, after the freeze, and commits it):
   ```bash
   python scripts/export_loadtest_data.py --source <course CSV> --rows 3000-3999
   ```
   This writes `loadtest/data/tickets.tsv` (one ticket per line) and prints the ticket length distribution, which also feeds the workload model.

For a dry run **before the freeze**, use a file of made-up tickets in the same format (`<row>\t<narrative as a JSON string>`), passed with `-Jdata=<path>`.

### Validate the JMeter setup before the real service is available

The repository includes synthetic input and a dry-run-only mock service. This verifies that JMeter can parse the open-loop plan, read the TSV safely, write the required JTL fields and reconcile request IDs. Its timings are not assignment evidence.

```bash
python scripts/run_jmeter_dry_run.py --mock
```

If JMeter is not on `PATH`, either set `JMETER_BIN` or pass its executable explicitly:

```bash
python scripts/run_jmeter_dry_run.py --mock --jmeter /path/to/jmeter
```

Dry-run output is written below `results/dry-run/` and ignored by Git. After the real service is reachable from the separate load-generator machine, repeat without `--mock`:

```bash
python scripts/run_jmeter_dry_run.py --host <SUT-IP> --port 8000
```

## 3. JMeter settings

Set on the command line with `-J<name>=<value>`:

| Property | Meaning | Default |
|---|---|---|
| `host`, `port` | SUT address | `localhost`, `8000` |
| `rate` | POST /tickets arrivals per minute | 6 |
| `rate_end` | Arrivals per minute at the end of the run (for a ramp); defaults to `rate` | = `rate` |
| `duration` | Minutes of arrivals | 10 |
| `drain` | Minutes after arrivals stop for in-flight requests to finish | 5 |
| `search_rate` | GET /search arrivals per minute (mixed load) | 0 (off) |
| `timeout_ms` | A request slower than this counts as an error | 300000 (5 min) |
| `data` | Ticket file, relative to `loadtest/` | `data/tickets.tsv` |

`loadtest/triage.properties` (passed with `-q`) makes the `.jtl` a CSV file that includes a **request ID** column, which the service also logs. That's how the results reconcile.

## 4. Playbook: one load-test run

Repeat for every (model, arrival rate) configuration, **three times**.

**On the SUT:**

1. Close other applications. Plug in the laptop. Don't use the machine during the run.
2. Set the model: `MODEL=<tag>` in `.env`, then empty the database and start fresh:
   ```bash
   docker compose down
   docker volume rm triage_triage-data
   docker compose up -d
   python scripts/pull_models.py --check          # all OK?
   curl http://localhost:8000/health              # "status": "ok" and the right model?
   ```
3. **Warm up:** send one made-up ticket so the model is loaded into memory (the first request includes load time):
   ```bash
   curl -X POST http://localhost:8000/tickets -H "Content-Type: application/json" -d '{"narrative": "warm-up request"}'
   ```
4. Start recording resource use (CPU and memory per container, every 5 s) in a separate terminal. This uses bash (Terminal on Mac, **Git Bash** on Windows):
   ```bash
   mkdir -p results/load/<model>
   while true; do docker stats --no-stream --format "{{.Name}},{{.CPUPerc}},{{.MemUsage}}" | sed "s/^/$(date +%s),/"; sleep 5; done > results/load/<model>/<rate>rpm_run<N>_stats.csv
   ```

**On the LG:**

5. Run JMeter in non-GUI mode (never GUI mode for measurements):
   ```bash
   jmeter -n -t loadtest/triage.jmx -q loadtest/triage.properties \
     -Jhost=<SUT-IP> -Jrate=<rate> -Jduration=10 [-Jsearch_rate=<n>] \
     -l results/load/<model>/<rate>rpm_run<N>.jtl
   ```
   Naming: `<model>` is the tag with `:` replaced by `-` (e.g. `qwen2.5-1.5b`). Mixed-load runs: `<rate>rpm_s<search_rate>_run<N>.jtl`.
6. Wait for `... end of run`. The configured drain period allows slow in-flight requests to finish before JMeter exits. Use the same drain value for every comparable run and record it in the playbook.

**After the run:**

7. On the SUT, stop the stats recording (Ctrl+C) and commit the service log (`logs/service/`) and the stats file.
8. On the LG, commit the `.jtl`.
9. Bring them together on one machine (`git pull`) and reconcile:
   ```bash
   python scripts/reconcile.py results/load/<model>/<rate>rpm_run<N>.jtl
   ```
   Every sample should be found in the service log. "Other requests during the run" must be 0; if not, someone else used the service, and the run should be repeated.
10. Write the run in the run log (below).

## 5. Summarise

```bash
python scripts/summarise_jtl.py results/load --skip-s 60 --csv results/load/summary.csv
python scripts/summarise_jtl.py results/load --label "GET /search"     # search latency under mixed load
```

The table shows, per configuration, **mean (min–max) across the three runs** of: samples, offered rate, achieved throughput, p50/p95/p99 latency and error rate. `--skip-s 60` leaves out the first minute of each run. If you use it, say so on the slide and use the same value everywhere.

For **latency over time** (the clearest evidence of queue build-up), generate JMeter's HTML dashboard:

```bash
jmeter -g results/load/<model>/<rate>rpm_run1.jtl -o results/load/<model>/<rate>rpm_run1_report
```

Open `index.html` → Charts → Over Time → Response Times Over Time.

## 6. Stress test (one limit of the system)

The brief asks for **one** test that finds a limit, for at least one model. A suggested design: **the maximum sustainable arrival rate.**

- Ramp the arrival rate linearly from low to well above the expected capacity:
  ```bash
  jmeter -n -t loadtest/triage.jmx -q loadtest/triage.properties -Jhost=<SUT-IP> \
    -Jrate=1 -Jrate_end=<well above capacity> -Jduration=30 \
    -l results/load/<model>/stress_ramp_run1.jtl
  ```
- **The limit** is where achieved throughput stops rising with the offered rate and latency starts growing without bound. Read it from the dashboard's "Response Times Over Time" and "Transactions per Second" charts.
- Estimate the expected capacity first: if one ticket takes `t` seconds on its own and Ollama handles one at a time, capacity is about `60 / t` tickets per minute.
- Then **confirm** the limit with constant-rate runs just below and just above it: below, latency stays flat; above, it keeps climbing.
- Diagnose it with the service log: `latency_ms` minus `ollama_total_ms` is time spent waiting in a queue. If that grows while `ollama_total_ms` stays flat, the bottleneck is the model server processing one request at a time. Check the `docker stats` CPU too.

Other valid limits: the concurrency at which Ollama starts rejecting requests (`OLLAMA_MAX_QUEUE`), or the ticket length at which latency exceeds the requirement.

## 7. Run log

Keep a row for every run, including failed or discarded ones (say why). Keep this table in this file or in `results/load/RUNS.md`.

| Date/time (SGT) | Model | Rate /min | Search /min | Duration | Run | File | Reconciled? | Notes |
|---|---|---|---|---|---|---|---|---|
| | | | | | | | | |

## 8. Test environment (Slide 7)

Record for both machines: CPU model and cores, RAM, OS and version, Docker Desktop version and resource limits (SUT), Java and JMeter versions (LG), the network between them and its ping time, the Ollama version (`models/models.lock.json`), and the `.env` settings. Note anything that could make results unrepresentative (laptop thermal throttling, battery power, Wi-Fi, background apps) and how results would scale to the client's CPU servers (for example, more cores, but server CPUs often have lower clock speeds).
