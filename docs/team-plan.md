# Team plan

**Due:** 23:59, Friday 9 October 2026 (Week 6) · **Worth:** 15% · **Submission:** `Group03.pptx` (max 12 slides) + supporting files

## Who owns what

This table records who did what in the end. It replaces the original allocation from 24 September, which changed as the work went on. **All five members contributed equally to the project.** Everyone reviewed the final deck.

| Person | Labelling (Step 1) | Areas | Slides |
|---|---|---|---|
| **Zong Han** | Group A: rows 3000–3099 | Repo and Docker scaffold; the triage service; workload model and requirements; prediction record; golden-set merge (agreement, resolution sheets, freeze); accuracy testing; final deck assembly | 1 Cover, 2 Architecture, 3 Workload, 4 Requirements, 6 Golden set, 10 Accuracy |
| **Ridwan** | Group A: rows 3000–3099 | Load and stress testing on the load-generator Mac: JMeter setup, dry runs, playbooks, 3-run load tests, stress test and adaptive stress test, reconciliation with the service logs | 7 Test environment, 8 Playbook, 9 Load and stress results |
| **Tze Han** | Group B: rows 3100–3199 | Candidate models: shortlist, justification, pull and pin by digest; smoke tests; ran the system-under-test Mac (Docker, Ollama, triage service) for every official run | 5 Candidate models |
| **Kannan** | Group B: rows 3100–3199 | Independent labelling and Group B resolutions; full-deck review | Review of all slides |
| **Natalie** | Group B: rows 3100–3199 | Independent labelling and Group B resolutions; neutral tie-breaker when Group A couldn't agree on a label; full-deck review | Review of all slides |
| **Everyone** | | Predictions and the recommendation and defence | 11 Predictions and recommendation, 12 References |

Group B has three labellers, so its rows get a third independent opinion: a 2-to-1 split shows which label is more defensible, and Fleiss' kappa (agreement across three people) goes on Slide 6 alongside each pair's Cohen's kappa. A majority is still only a starting point; every disagreement is discussed and recorded.

**Tie-breakers:** Natalie hasn't seen rows 3000–3099, so she's the neutral tie-breaker when Group A is stuck. For Group B, one of Group A (who haven't seen rows 3100–3199) plays that role. Record the tie-breaker's decision like any other resolution.

## Timeline

Today is Thursday 24 September. The critical path is **labelling → freeze → benchmarks**, because no model may be tested until the golden set and prediction record are committed.

| Dates | Milestone | Who |
|---|---|---|
| Thu 24 – Sun 27 Sep | **Labelling done** (both groups, 100/100 each) | Everyone |
| Thu 24 – Sun 27 Sep | In parallel: workload model draft; model shortlist; JMeter set up on the second machine and dry-run with made-up tickets | Zong Han, Tze Han, Ridwan |
| Mon 28 – Tue 29 Sep | Agreement statistic; resolution meetings; protocol v0.2; requirements final; predictions written | Each group (+ tie-breaker); Zong Han; everyone |
| **Wed 30 Sep** | **FREEZE:** commit golden set, prediction record, `models.lock.json` and the prompt; tag `freeze` | Zong Han |
| Thu 1 – Sun 4 Oct | Accuracy runs (every model); load tests (3 runs × each rate × each model); stress test | Zong Han; Ridwan and Tze Han |
| Mon 5 – Tue 6 Oct | Reconcile every number with the logs; diagnose the bottleneck; draft recommendation | Zong Han, Ridwan, Tze Han; everyone |
| Wed 7 – Thu 8 Oct | Slides complete; full-team review | Everyone; Zong Han assembles |
| Fri 9 Oct | Submit (buffer day) | Zong Han |

**What actually happened:** the protocol revisions (v0.2, v0.3) landed on 3 Oct, so the freeze moved to **6 Oct** (annotated tag `prediction-freeze`, 15:35 SGT). Every benchmark ran after the tag: load tests from 6 Oct, accuracy runs on 8 Oct, and the adaptive stress test on 9 Oct.

## Budget the benchmark time now

Benchmarks are slow on CPU, and **all official runs must happen on the same machine** (see [setup.md](setup.md#one-machine-for-all-official-runs)). Rough budget:

- **Load tests:** e.g. 3 models × 3 arrival rates × 3 runs × 10 min ≈ **4.5 hours**, plus warm-up and resets.
- **Accuracy:** 200 tickets × per-ticket latency. A 7–8B model on CPU might take 10–30 s per ticket, which is **up to ~1.5 hours per model**.
- **Stress test:** 30–60 minutes.

Book the system-under-test machine for these blocks and don't use it for anything else while tests run.

## Hand-offs to watch

- **Tze Han → Ridwan, Zong Han:** the pinned models (`models/models.lock.json`) before the freeze.
- **Zong Han → Ridwan:** the arrival rates to test (average, peak, stress) from the workload model.
- **Zong Han → everyone:** requirements, before predictions are written.
- **Ridwan, Tze Han, Zong Han → everyone:** results with the reconcile output, so every slide number traces back to a log.
