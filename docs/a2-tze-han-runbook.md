# Assignment 2 - Tze Han runbook

**Role:** System-under-test (SUT) Mac - Docker, Ollama, triage service, cascade accuracy and SUT agent.  
**Partner:** Ridwan's JMeter Mac - see [Ridwan runbook](a2-ridwan-runbook.md).  
**Deadline:** 23:59 SGT, Friday 27 November 2026.

Run these commands only on Tze Han's Mac. Keep this Mac otherwise idle during official measurements.

> **Benchmark gate:** The memory check may be run now. Do not run cascade accuracy or an official speed test until `a2/escalation-rule.md` and `planning/a2-prediction-record.md` are complete, committed and tagged `a2-prediction-freeze`.

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
- Ridwan reports the same hash.

```bash
python3 scripts/split_golden.py --check
python3 scripts/a2_workload.py --check
python3 -m compileall -q service/app scripts
```

Expected: tuning 98, test 97, workload `OK`, and no compilation error.

## 2. Prepare Docker, Ollama and `.env`

```bash
cd "$A2_REPO"
if [[ ! -f .env ]]; then cp .env.example .env; fi
nano .env
```

For a two-model cascade, confirm these fixed values:

```ini
NUM_CTX=4096
TEMPERATURE=0
SEED=42
OLLAMA_IMAGE=ollama/ollama:0.35.1
OLLAMA_NUM_PARALLEL=1
OLLAMA_MAX_LOADED_MODELS=2
OLLAMA_MAX_QUEUE=512
OLLAMA_KEEP_ALIVE=30m
```

Use `OLLAMA_MAX_LOADED_MODELS=3` only if the frozen design uses the agreement rule with two small models. Do not change these values between A2 configurations.

Save `nano` with `Ctrl-O`, Enter, then exit with `Ctrl-X`.

```bash
docker compose up -d --build
docker compose ps
python3 scripts/pull_models.py --check
docker compose exec -T ollama env | grep '^OLLAMA_'
curl -s http://127.0.0.1:8000/health | python3 -m json.tool
```

Check:

- `ollama` and `triage` are running.
- All three pinned models report `OK`.
- `OLLAMA_NUM_PARALLEL=1`.
- `OLLAMA_MAX_LOADED_MODELS=2` (or 3 for agreement).
- `/health` returns `"status": "ok"`.

## 3. Run and commit the memory check

Likely 1B + 7B pair:

```bash
cd "$A2_REPO"
python3 scripts/a2_sut_agent.py memory-check \
  --models qwen2.5:7b llama3.2:1b-instruct-q4_K_M
```

If the team may use 0.5B + 7B, check it separately:

```bash
python3 scripts/a2_sut_agent.py memory-check \
  --models qwen2.5:7b qwen2.5:0.5b
```

```bash
find results/a2/memory-check -maxdepth 2 -type f | sort
rg -n 'Result:|resident|reload' results/a2/memory-check
```

Pass criteria:

- `SUMMARY.md` says every model stayed loaded.
- Final `ollama ps` contains both model names.
- `alternate_calls_with_reload` is 0.

Commit the evidence:

```bash
git add results/a2/memory-check
git commit -m "A2: record cascade memory check"
git push origin main
```

Tell Ridwan to pull.

## 4. Verify the team has passed the benchmark gate

After the team completes and freezes the escalation rule and prediction record:

```bash
cd "$A2_REPO"
git pull --ff-only
git tag --list a2-prediction-freeze
git show --stat --oneline a2-prediction-freeze
git status --short
```

Do not continue unless the tag is displayed and the working tree is clean.

## 5. Run cascade accuracy - setting A

Edit `.env` so it exactly matches setting A in the frozen `a2/escalation-rule.md`:

```bash
cd "$A2_REPO"
nano .env
```

Example shape only - use the frozen values:

```ini
MODE=cascade
SMALL_MODEL=llama3.2:1b-instruct-q4_K_M
LARGE_MODEL=qwen2.5:7b
RULE=category
RULE_SETTING=A
ACCEPT_CATEGORIES=Mortgage,Credit card
```

```bash
docker compose up -d triage
curl -s http://127.0.0.1:8000/health | python3 -m json.tool
python3 scripts/a2_accuracy.py --config cascade-A
```

Before running accuracy, `/health` must show cascade setting A, the frozen rule and the pinned model digests.

## 6. Run cascade accuracy - setting B

```bash
nano .env
```

Change `RULE_SETTING=B` and only the rule setting defined in the frozen design. Do not change the models, prompt, Ollama options or generation options.

```bash
docker compose up -d triage
curl -s http://127.0.0.1:8000/health | python3 -m json.tool
python3 scripts/a2_accuracy.py --config cascade-B
```

Check and commit both accuracy results:

```bash
find results/a2/accuracy -maxdepth 1 -type f | sort
rg -n 'Overall|PASS|FAIL|Escalat|Confusion' results/a2/accuracy/*.md
git status --short
```

Each report must contain 97 tickets, overall and per-category counts, a confusion matrix, escalation fraction, and separate escalated/non-escalated accuracy.

```bash
git add results/a2/accuracy logs/service
git commit -m "A2: record cascade accuracy results"
git push origin main
```

Tell Ridwan to pull.

## 7. Create the shared private token and start the SUT agent

Ridwan will privately send one random token. In a dedicated terminal:

```bash
export A2_REPO="$HOME/Documents/GitHub/ICT3113_A1_P1-3"
cd "$A2_REPO"
export A2_AGENT_TOKEN='PASTE_THE_SHARED_RANDOM_TOKEN_HERE'
test ${#A2_AGENT_TOKEN} -ge 12 && echo 'Token length OK'
```

Find this Mac's private LAN IP:

```bash
ipconfig getifaddr en0
```

If blank:

```bash
ipconfig getifaddr en1
```

Send the IP to Ridwan, then start the agent and leave this terminal open:

```bash
python3 scripts/a2_sut_agent.py agent --bind 0.0.0.0
```

Expected: `A2 SUT agent listening on http://0.0.0.0:8766`.

If macOS prompts for incoming Python connections, allow them on the trusted network. Do not expose ports 8000 or 8766 to the public internet.

## 8. Configure 7B alone for S measurement and speed tests

Use a second terminal; leave the agent running:

```bash
export A2_REPO="$HOME/Documents/GitHub/ICT3113_A1_P1-3"
cd "$A2_REPO"
nano .env
```

Set:

```ini
MODE=single
MODEL=qwen2.5:7b
```

```bash
docker compose up -d triage
curl -s http://127.0.0.1:8000/health | python3 -m json.tool
```

Check that `model` is exactly `qwen2.5:7b`. Tell Ridwan: **7B ready**. Ridwan will measure S once and then run all three 7B speed runs.

Do not edit `.env`, restart containers, or use this Mac while Ridwan's command is running.

## 9. Configure cascade A for speed tests

Wait until Ridwan says the 7B runs are finished. Then:

```bash
cd "$A2_REPO"
nano .env
```

Set the exact frozen cascade A configuration, then:

```bash
docker compose up -d triage
curl -s http://127.0.0.1:8000/health | python3 -m json.tool
```

Check setting A and tell Ridwan: **cascade A ready**. Do not touch the SUT until his three runs finish.

## 10. Configure cascade B for speed tests

Wait until Ridwan says cascade A is finished. Then:

```bash
cd "$A2_REPO"
nano .env
```

Set the exact frozen cascade B configuration, then:

```bash
docker compose up -d triage
curl -s http://127.0.0.1:8000/health | python3 -m json.tool
```

Check setting B and tell Ridwan: **cascade B ready**. Do not touch the SUT until his three runs finish.

## 11. Finish

After Ridwan confirms all nine runs and the final evidence push are complete:

```bash
cd "$A2_REPO"
git pull --ff-only
git status --short
git rev-parse --short HEAD
git rev-parse --short origin/main
```

The hashes must match and status must be clean. Stop the agent with `Ctrl-C` in its dedicated terminal.

## Tze Han troubleshooting

### Ridwan cannot reach port 8000

```bash
docker compose ps
curl -s http://127.0.0.1:8000/health | python3 -m json.tool
```

Confirm both Macs are on the same LAN, the IP has not changed, and Docker incoming connections are allowed.

### Ridwan cannot reach port 8766

Confirm the agent terminal says `0.0.0.0:8766`. Restart it if needed:

```bash
export A2_AGENT_TOKEN='PASTE_THE_SHARED_RANDOM_TOKEN_HERE'
python3 scripts/a2_sut_agent.py agent --bind 0.0.0.0
```

### Service reports the wrong configuration

```bash
nano .env
docker compose up -d triage
curl -s http://127.0.0.1:8000/health | python3 -m json.tool
```

Never start a run until `/health` exactly matches the intended frozen configuration.

