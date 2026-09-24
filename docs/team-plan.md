# Team plan

**Due:** 23:59, Friday 9 October 2026 (Week 6) · **Worth:** 15% · **Submission:** `Group03.pptx` (max 12 slides) + supporting files

## Who owns what

Everyone owns one area end to end, including its slide(s). Owners do the work and make the decisions in their area; everyone reviews the final deck.

| Person | Labelling (Step 1) | Owns | Slides |
|---|---|---|---|
| **Zong Han** | Group A: rows 3000–3099 | Repo and Docker scaffold; running the service; golden-set merge (agreement, resolution sheets, freeze); final deck assembly | 1 Cover, 2 Architecture, 6 Golden set |
| **Ridwan** | Group A: rows 3000–3099 | Candidate models: shortlist 3–5 across ≥2 size classes, justify, pull and pin by digest; single-request latency; **compiles the prediction record** | 5 Candidate models |
| **Tze Han** | Group B: rows 3100–3199 | Load and stress testing: second (load-generator) machine, JMeter, test environment description, playbooks, 3-run load tests, stress test, bottleneck diagnosis | 7 Test environment, 8 Playbook, 9 Load and stress results |
| **Kannan** | Group B: rows 3100–3199 | Accuracy testing: exports load-test data, runs every golden ticket through each model, per-category accuracy and confusion matrices; checks every reported number against the logs | 10 Accuracy results |
| **Natalie** | Group B: rows 3100–3199 | Workload model (sourced figures and estimates) and the requirements derived from it; neutral tie-breaker when Group A can't agree on a label; references and licences | 3 Workload, 4 Requirements, 12 References |
| **Everyone** | | Predictions for your own area (to Ridwan before the freeze); the recommendation and defence | 11 Predictions and recommendation |

Group B has three labellers, so its rows get a third independent opinion: a 2-to-1 split shows which label is more defensible, and Fleiss' kappa (agreement across three people) goes on Slide 6 alongside each pair's Cohen's kappa. A majority is still only a starting point; every disagreement is discussed and recorded.

**Tie-breakers:** Natalie hasn't seen rows 3000–3099, so she's the neutral tie-breaker when Group A is stuck. For Group B, one of Group A (who haven't seen rows 3100–3199) plays that role. Record the tie-breaker's decision like any other resolution.

Natalie's workload model doesn't depend on the labels, so she should start on it straight away, alongside labelling.

## Timeline

Today is Thursday 24 September. The critical path is **labelling → freeze → benchmarks**, because no model may be tested until the golden set and prediction record are committed.

| Dates | Milestone | Who |
|---|---|---|
| Thu 24 – Sun 27 Sep | **Labelling done** (both groups, 100/100 each) | Everyone |
| Thu 24 – Sun 27 Sep | In parallel: workload model draft; model shortlist; JMeter set up on the second machine and dry-run with made-up tickets | Natalie, Ridwan, Tze Han |
| Mon 28 – Tue 29 Sep | Agreement statistic; resolution meetings; protocol v0.2; requirements final; predictions written | Each group (+ tie-breaker); Natalie; everyone |
| **Wed 30 Sep** | **FREEZE:** commit golden set, prediction record, `models.lock.json` and the prompt; tag `freeze` | Zong Han |
| Thu 1 – Sun 4 Oct | Accuracy runs (every model); load tests (3 runs × each rate × each model); stress test | Kannan; Tze Han |
| Mon 5 – Tue 6 Oct | Reconcile every number with the logs; diagnose the bottleneck; draft recommendation | Kannan, Tze Han; everyone |
| Wed 7 – Thu 8 Oct | Slides complete; full-team review | Everyone; Zong Han assembles |
| Fri 9 Oct | Submit (buffer day) | Zong Han |

## Budget the benchmark time now

Benchmarks are slow on CPU, and **all official runs must happen on the same machine** (see [setup.md](setup.md#one-machine-for-all-official-runs)). Rough budget:

- **Load tests:** e.g. 3 models × 3 arrival rates × 3 runs × 10 min ≈ **4.5 hours**, plus warm-up and resets.
- **Accuracy:** 200 tickets × per-ticket latency. A 7–8B model on CPU might take 10–30 s per ticket, which is **up to ~1.5 hours per model**.
- **Stress test:** 30–60 minutes.

Book the system-under-test machine for these blocks and don't use it for anything else while tests run.

## Hand-offs to watch

- **Ridwan → Tze Han, Kannan:** the pinned models (`models/models.lock.json`) before the freeze.
- **Natalie → Tze Han:** the arrival rates to test (average, peak, stress) from the workload model.
- **Natalie → everyone:** requirements, before predictions are written.
- **Tze Han, Kannan → everyone:** results with the reconcile output, so every slide number traces back to a log.
