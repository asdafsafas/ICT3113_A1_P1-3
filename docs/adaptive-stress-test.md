# Adaptive Stress Test

This procedure finds and records a repeatable 7B saturation boundary using two
separate Macs. Tze Han's Mac runs Docker, Ollama, the triage service and a
token-protected evidence agent. Ridwan's Mac runs JMeter and automatically
increases the open-loop classification arrival rate.

The test starts at 12 POST `/tickets` requests per minute and increases by 2 per
minute through a maximum of 24 per minute. Every rate also carries 7 GET
`/search` requests per minute. Each attempt uses 10 active minutes and 10 drain
minutes. Before every attempt, the SUT agent restarts Ollama and triage, recreates
the empty database, warms the selected model with invented text, clears the
warm-up database row and verifies the frozen model digest.

The first rate classified as overloaded is repeated after another full reset.
The suite stops only when the overload signal occurs in both attempts. It then
reports the highest sustained rate and first confirmed overloaded rate as a
measured capacity bracket.

## Evidence saved for every attempted rate

- Raw JMeter `.jtl`
- JMeter execution log
- Service JSONL containing the exact JMeter request IDs
- Docker CPU and memory statistics CSV sampled every five seconds
- `/health` model and digest snapshot
- SUT reset, warm-up and monitoring audit JSONL
- A continuously updated JSON decision record and Markdown summary

All files are stored under:

```text
results/load/qwen2.5-7b/adaptive-stress/
```

Do not edit the generated decision record. Report the measured bracket only if
the summary status is `LIMIT_BRACKETED`. If it says `NO_LIMIT_WITHIN_RANGE`, the
only supported conclusion is that sustainable capacity is at least the maximum
tested rate.

## Stop rule fixed before execution

A rate is classified as overloaded when any of the following is observed:

1. POST error rate exceeds 1%.
2. At least 15% of offered POSTs remain in flight at the end of the active
   period, with a minimum threshold of five requests.
3. The queue grows between the midpoint and active-period end, and last-half
   successful completion throughput falls below 90% of the offered rate.
4. The queue grows and late-half POST p50 is at least 1.5 times and at least two
   seconds greater than early-half POST p50.

This combines failure, throughput, queue and latency evidence. It does not call
high CPU utilisation alone a saturation point.

## One-time setup on both Macs

Both Macs must pull the commit containing these scripts. Confirm that the SUT
Mac `.env` selects `qwen2.5:7b` and keeps the frozen settings, including
`OLLAMA_NUM_PARALLEL=1`.

Choose one shared token of at least 12 characters. Use the same value on both
Macs. Do not commit it.

Example:

```bash
export STRESS_AGENT_TOKEN="replace-with-one-shared-random-token"
```

The test uses TCP port 8765 between the two Macs. They must remain on the same
network, and macOS may ask Tze Han to allow incoming Python connections.

## Command on Tze Han's SUT Mac

Run this from the repository and leave the terminal open:

```bash
cd ~/Documents/GitHub/ICT3113_A1_P1-3
git pull
export STRESS_AGENT_TOKEN="replace-with-the-shared-token"
python3 scripts/adaptive_stress_sut.py \
  --bind 0.0.0.0 \
  --model qwen2.5:7b
```

The agent handles every reset, warm-up, database clear, health check, statistics
capture and service-log extraction. Do not run another accuracy or load test
against the SUT while it is active.

## Command on Ridwan's JMeter Mac

Set the current SUT address and use the same shared token:

```bash
cd ~/Documents/GitHub/ICT3113_A1_P1-3
git pull
export SUT_HOST="172.20.10.2"
export JMETER_BIN="/Users/ridwan/Downloads/apache-jmeter-5.6.3/bin/jmeter"
export STRESS_AGENT_TOKEN="replace-with-the-shared-token"

python3 scripts/run_adaptive_stress.py \
  --host "$SUT_HOST" \
  --jmeter "$JMETER_BIN"
```

No `READY` or `PULLED` input is required. The load script commands the SUT agent,
downloads the evidence immediately after every attempt and stops automatically
after a repeated overload signal.

Before a real run, the complete JMeter plan can be inspected without contacting
the SUT:

```bash
python3 scripts/run_adaptive_stress.py \
  --host "$SUT_HOST" \
  --jmeter "$JMETER_BIN" \
  --dry-run
```

## Expected duration

Each attempted rate takes about 20 minutes plus several minutes for reset and
warm-up. If 12/min is sustained and 14/min is overloaded twice, allow about one
hour. If higher rates are required, the worst-case default plan is approximately
2 hours 20 minutes plus resets. A confirmation attempt adds about 20 minutes.

## After completion

Read these first:

```bash
cat results/load/qwen2.5-7b/adaptive-stress/adaptive-stress-summary.md
python3 -m json.tool \
  results/load/qwen2.5-7b/adaptive-stress/adaptive-stress-summary.json | less
```

Confirm that every attempted rate has all six raw evidence files before using
the result in Slide 9. Commit the complete `adaptive-stress` directory together;
do not commit a summary without its backing evidence.

```bash
git status --short
git add results/load/qwen2.5-7b/adaptive-stress
git commit -m "Add adaptive 7B stress limit evidence"
git push
```

If the test is interrupted, preserve the partial evidence directory. Move it to
a clearly named archival directory before starting again; the scripts refuse to
overwrite measured evidence.
