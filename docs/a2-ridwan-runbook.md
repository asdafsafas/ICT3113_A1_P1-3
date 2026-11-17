# Assignment 2 - Ridwan runbook

**Role:** Load-generator Mac - terminal JMeter, remote SUT control, speed evidence and summaries.  
**Partner:** Tze Han's SUT Mac - see [Tze Han runbook](a2-tze-han-runbook.md).  
**Deadline:** 23:59 SGT, Friday 27 November 2026.

Run these commands only on Ridwan's Mac. `run_a2_speed.py` launches JMeter in terminal/non-GUI mode; do not start JMeter separately for an official run.

> **Benchmark gate:** Do not run `measure-s` or an official speed run until `a2/escalation-rule.md` and `planning/a2-prediction-record.md` are complete, committed and tagged `a2-prediction-freeze`.

## 1. Update and verify the repository

```bash
export A2_REPO="$HOME/Documents/GitHub/ICT3113_A1_P1-3"
cd "$A2_REPO"
git switch main
git pull --ff-only
git status --short
git rev-parse --short HEAD
git rev-parse --short origin/main
```

Check:

- `git status --short` prints nothing.
- The two hashes match.
- Tze Han reports the same hash.

```bash
python3 scripts/split_golden.py --check
python3 scripts/a2_workload.py --check
python3 -m compileall -q service/app scripts
```

Expected: tuning 98, test 97, workload `OK`, and no compilation error.

## 2. Verify terminal JMeter

```bash
export JMETER_BIN="$HOME/Downloads/apache-jmeter-5.6.3/bin/jmeter"
test -x "$JMETER_BIN" && echo 'JMeter executable found'
"$JMETER_BIN" --version
java -version
```

Expected: JMeter 5.6.3 and Java 17. Keep this `JMETER_BIN` variable in the terminal used for official tests.

## 3. Verify the benchmark gate

After the team freezes the escalation rule and prediction record:

```bash
cd "$A2_REPO"
git pull --ff-only
git tag --list a2-prediction-freeze
git show --stat --oneline a2-prediction-freeze
git status --short
```

Do not continue unless the tag is displayed, status is clean, and Tze Han has committed the cascade accuracy results.

```bash
find results/a2/accuracy -maxdepth 1 -type f | sort
rg -n 'Overall|PASS|FAIL|Escalat|Confusion' results/a2/accuracy/*.md
```

## 4. Generate and share the private agent token

Generate one token:

```bash
openssl rand -hex 16
```

Send that result privately to Tze Han. On your Mac, paste it into the same terminal used for testing:

```bash
export A2_AGENT_TOKEN='PASTE_THE_SHARED_RANDOM_TOKEN_HERE'
test ${#A2_AGENT_TOKEN} -ge 12 && echo 'Token length OK'
```

Never commit the token.

## 5. Set Tze Han's IP and check both connections

After Tze Han starts `a2_sut_agent.py agent --bind 0.0.0.0`, set the private LAN IP he sends:

```bash
export SUT='PASTE_TZE_HANS_PRIVATE_LAN_IP_HERE'
```

Check the triage service:

```bash
curl -s "http://$SUT:8000/health" | python3 -m json.tool
```

Check the protected SUT agent:

```bash
curl -s -H "Authorization: Bearer $A2_AGENT_TOKEN" \
  "http://$SUT:8766/agent/health" | python3 -m json.tool
```

Pass criteria:

- Service response has `"status": "ok"`.
- Agent response has `"ok": true` and `"active_stage": null`.
- If either fails, do not start an official run.

## 6. Measure S once

Wait until Tze Han says **7B ready**. Check it remotely:

```bash
curl -s "http://$SUT:8000/health" | python3 -m json.tool
```

The response must show `qwen2.5:7b` in single mode. Then:

```bash
cd "$A2_REPO"
python3 scripts/run_a2_speed.py measure-s --host "$SUT"
cat results/a2/s-measure/S.json | python3 -m json.tool
```

Check:

- Rows 3405, 3530 and 3738 were measured.
- `S_s`, `rate_per_min`, `duration_s`, `timeout_s` and `pause_s` are present.
- The same derived rate and duration will be used for all configurations.
- Compare `rate_per_min` with the A1 client peak of 1.73 tickets/min.

Commit the measurement and evidence:

```bash
git add results/a2/s-measure
git commit -m "A2: measure top-model S and fixed test rate"
git push origin main
```

## 7. Run three speed tests of 7B alone

Confirm with Tze Han that the SUT is still untouched and configured as 7B alone:

```bash
curl -s "http://$SUT:8000/health" | python3 -m json.tool
```

Run all three official runs:

```bash
cd "$A2_REPO"
python3 scripts/run_a2_speed.py run \
  --host "$SUT" \
  --config 7b-alone \
  --jmeter "$JMETER_BIN"
```

Tell Tze Han when the command has fully finished.

## 8. Run three speed tests of cascade A

Wait until Tze Han says **cascade A ready**. Verify remotely:

```bash
curl -s "http://$SUT:8000/health" | python3 -m json.tool
```

Check that the response exactly matches frozen setting A, then:

```bash
python3 scripts/run_a2_speed.py run \
  --host "$SUT" \
  --config cascade-A \
  --jmeter "$JMETER_BIN"
```

Tell Tze Han when all three runs have fully finished.

## 9. Run three speed tests of cascade B

Wait until Tze Han says **cascade B ready**. Verify remotely:

```bash
curl -s "http://$SUT:8000/health" | python3 -m json.tool
```

Check that the response exactly matches frozen setting B, then:

```bash
python3 scripts/run_a2_speed.py run \
  --host "$SUT" \
  --config cascade-B \
  --jmeter "$JMETER_BIN"
```

Tell Tze Han when all three runs have fully finished. He should keep the agent open until your checks are complete.

## 10. Check all nine runs

There must be three run summaries for each configuration:

```bash
find results/a2/speed/7b-alone -name '*_run.json' | wc -l
find results/a2/speed/cascade-A -name '*_run.json' | wc -l
find results/a2/speed/cascade-B -name '*_run.json' | wc -l
```

Expected: `3`, `3`, `3`.

Inspect all critical fields:

```bash
rg -n '"sent"|"completed"|"errored"|"unfinished"|"stored_by_service"|"missing_service_records"|"calls_with_model_reload"|"escalation_fraction"' \
  results/a2/speed/*/*_run.json
```

For a clean run:

- `completed` equals `sent`.
- `errored` is 0.
- `unfinished` is 0. If not, retain and report it; do not silently discard it.
- `stored_by_service` equals `completed`.
- `missing_service_records` is empty.
- `calls_with_model_reload` is 0.
- Cascade runs contain a non-null escalation fraction.

List the retained raw evidence:

```bash
find results/a2/speed -maxdepth 2 -type f | sort
```

Each run should include a JTL, JMeter log, service JSONL, resource statistics, health/stats snapshot, `ollama ps`, SUT audit log and `_run.json`.

## 11. Summarise and commit speed evidence

```bash
cd "$A2_REPO"
python3 scripts/run_a2_speed.py summarise
sed -n '1,260p' results/a2/speed/SUMMARY.md
git status --short
```

The summary must contain:

- p50 for each run plus mean and spread.
- Pooled p95 and its sample count.
- Throughput and error rate.
- Sent, completed, errored and unfinished counts.
- Cascade escalation fraction under load.
- No p99.

Commit the authoritative evidence:

```bash
git add results/a2/speed
git commit -m "A2: record and summarise official speed tests"
git push origin main
```

Tell Tze Han to pull and stop his agent only after the push succeeds.

Final check:

```bash
git pull --ff-only
git status --short
git rev-parse --short HEAD
git rev-parse --short origin/main
```

Status must be clean and both hashes must match.

## Ridwan troubleshooting

### JMeter executable not found

```bash
export JMETER_BIN="$HOME/Downloads/apache-jmeter-5.6.3/bin/jmeter"
test -x "$JMETER_BIN" && "$JMETER_BIN" --version
```

### Port 8000 cannot connect

Ask Tze Han to run:

```bash
docker compose ps
curl -s http://127.0.0.1:8000/health | python3 -m json.tool
```

Confirm both Macs are on the same LAN and that `$SUT` still contains his current IP.

### Port 8766 cannot connect

Ask Tze Han to confirm his agent terminal says `0.0.0.0:8766` and that incoming Python connections are allowed.

### Agent returns `unauthorised`

The two terminals have different tokens. On both Macs:

```bash
echo ${#A2_AGENT_TOKEN}
```

Set the exact same token again without printing or committing the token itself.

### A run is interrupted

- Keep the partial evidence.
- The runner skips a completed run whose JTL already exists.
- Discuss partial files before moving anything aside or repeating a run.
- Never change S, workload, model options or timeouts simply to make a run pass.

