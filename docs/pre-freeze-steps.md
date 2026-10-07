# Pre-freeze steps (do in order, on the system-under-test Mac)

**Owner:** Tze Han. Nothing here sends a dataset row to a model.

## 0. Switch from the prototype stack to the team stack

The prototype in `~/ticket-triage` uses the same ports (8000, 11434). Stop it first and keep its smoke logs.

```bash
cd ~/ticket-triage && docker compose down          # stops the prototype; its model volume stays on disk
cd <team repo> && git pull
mkdir -p evidence/smoke-prototype
cp -R ~/ticket-triage/logs/smoke_* ~/ticket-triage/env evidence/smoke-prototype/
cp ~/ticket-triage/app/prompt.txt evidence/smoke-prototype/prototype_prompt.txt
ls evidence/smoke-prototype                         # 5 smoke_* folders + env/ + prototype_prompt.txt
```

## 1. Pin the models (`models/models.lock.json`)

```bash
cp .env.example .env                                # if .env does not exist yet
docker compose up -d --build
docker compose exec ollama sh -c 'env | grep ^OLLAMA_'   # must show OLLAMA_NUM_PARALLEL=1
python3 scripts/pull_models.py                      # team volume is new, so this re-downloads ~7.8 GB
python3 scripts/pull_models.py --check              # all three must say OK
```

The digests must match the prototype pins (`evidence/smoke-prototype/env/models_pinned.json`):

| Tag | Digest starts with |
|---|---|
| qwen2.5:0.5b | a8b0c5157701 |
| llama3.2:1b-instruct-q4_K_M | 22bc6b92eb01 |
| qwen2.5:7b | 845dbda0ea48 |

## 2. Smoke-test the real service (CPU and memory evidence)

Mac on AC power. Try one model first, then all of them:

```bash
python3 scripts/smoke_sut.py --models qwen2.5:0.5b  # check it switches, verifies and finishes
python3 scripts/smoke_sut.py                        # all three, about 5 minutes
cat evidence/smoke/SUMMARY.md
```

If you skip this step, delete the "Smoke tests on the real service" bullet from the prediction record, and do not cite any CPU or memory figure as measured.

## 3. Ticket lengths

```bash
python3 scripts/ticket_lengths.py                   # must match planning/workload-model.md section 4
```

## 4. Reset the database, then freeze

```bash
docker compose down && docker volume rm triage_triage-data && docker compose up -d
```

Then the team settles the latency bias note and the run-duration decision. Fill in `Committed on` in `planning/prediction-record.md`, and:

```bash
git add models/models.lock.json evidence/ planning/ scripts/ docs/ models/smoke-tickets.tsv
git commit -m "Freeze: golden set, prediction record, model pins, smoke evidence"
git tag -a prediction-freeze -m "Prediction record and golden set frozen before first official benchmark"
git push && git push origin prediction-freeze
git rev-list -n 1 prediction-freeze                 # record in docs/actual-jmeter-test.md section 2
```

After the tag, nobody edits `golden/`, `planning/prediction-record.md`, `service/prompts/` or `models/models.lock.json`.
