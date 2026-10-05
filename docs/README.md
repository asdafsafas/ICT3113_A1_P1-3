# Project documentation

| Doc | What it covers | Owner |
|---|---|---|
| [team-plan.md](team-plan.md) | Who does what, timeline, hand-offs | Everyone |
| [setup.md](setup.md) | Installing Docker, running the service and Ollama (Windows and Mac), CPU-only check, troubleshooting | Zong Han |
| [architecture.md](architecture.md) | Components, endpoints, baseline design, request log format | Zong Han |
| [golden-set.md](golden-set.md) | From label sheets to agreement statistic, resolutions and the frozen golden set | Zong Han |
| [models.md](models.md) | Choosing, pinning and checking candidate models; prompt rules | Ridwan |
| [load-testing.md](load-testing.md) | Two-machine JMeter setup, load-test playbook, stress test, run log, test environment | Tze Han |
| [person3-jmeter-todo.md](person3-jmeter-todo.md) | Checkbox-based execution plan for Person 3's JMeter, evidence and slide work | Tze Han |
| [accuracy-testing.md](accuracy-testing.md) | Accuracy test playbook and reading the report | Kannan |

Planning documents (drafts to fill in) live in [`planning/`](../planning/):
[workload model](../planning/workload-model.md) (Natalie), [requirements](../planning/requirements.md) (Natalie), [prediction record](../planning/prediction-record.md) (Ridwan compiles; frozen before benchmarks).

## Repository layout

```
docker-compose.yml       system under test: triage service + Ollama (CPU only)
.env.example             settings (copy to .env): model, prompt, Ollama options
service/                 the triage service (FastAPI) and its prompt templates
labeler/                 golden-set labelling app (see main README)
scripts/                 helper scripts (Python, standard library only)
  pull_models.py           pull and pin candidate models → models/models.lock.json
  export_protocol.py       labeler/protocol.json → golden/PROTOCOL.md (readable, submittable)
  agreement.py             Cohen's/Fleiss' kappa + resolution sheets from label files
  build_golden.py          resolved sheets → golden/golden_set.csv
  export_loadtest_data.py  course data → loadtest/data/tickets.tsv (+ ticket lengths)
  accuracy_test.py         golden set through POST /tickets → accuracy report
  summarise_jtl.py         JMeter results → p50/p95/p99, throughput, errors across runs
  reconcile.py             check a JMeter run against the service log
models/                  candidates.txt (chosen tags), models.lock.json (pinned digests)
golden/                  PROTOCOL.md, label sheets, resolution sheets, golden_set.csv
planning/                workload model, requirements, prediction record
loadtest/                JMeter test plan, properties, ticket data
results/                 load (.jtl) and accuracy results (committed)
logs/service/            service request logs (committed)
docs/                    these documents
```

## What must be committed, and when

| Item | When | Why |
|---|---|---|
| Independent label sheets | As soon as each labelling group finishes | Brief: submitted as evidence of independent labelling |
| Golden set + prediction record + model pins + prompt | Together, **before the first benchmark**, tagged `freeze` | Brief: commit history proves they came before measurements |
| Every `.jtl`, accuracy result and `logs/service/` file | After every run you might report | Brief: every number must reconcile with kept logs |
