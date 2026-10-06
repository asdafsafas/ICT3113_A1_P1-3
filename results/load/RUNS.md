# JMeter Run Log

All timestamps use Singapore Time (SGT, UTC+08:00). A run marked **provisional** has passed the load-generator checks but is not reportable until its JTL is reconciled with the matching service log from the system-under-test Mac.

| Date/time SGT | Model | POST/min | Search/min | Duration | Run | JTL file | Reconciled | Valid | Notes |
|---|---|---:|---:|---:|---:|---|---|---|---|
| 2026-10-06 16:42:48 | `qwen2.5:0.5b` | 1.45 | 2.9 | Stopped after about 3 min 28 s | 1 (discarded attempt) | `qwen2.5-0.5b/invalid/1.45rpm_s2.9_run1_incomplete_20261006_1646.jtl` | No | No | Interrupted before the full 10-minute arrivals plus 5-minute drain schedule completed. The shutdown hook ran at 16:46:15. Evidence retained: 5 POSTs and 10 GETs, all HTTP 200, but the run is incomplete and must not be reported. |
| 2026-10-06 16:53:40 | `qwen2.5:0.5b` | 1.45 | 2.9 | 10 min arrivals + 5 min drain | 1 | `qwen2.5-0.5b/1.45rpm_s2.9_run1.jtl` | Pending | Provisional | JMeter completed normally at 17:08:40: 14 POSTs and 29 GETs, all HTTP 200, 0% errors. POST p50/p95/p99 = 0.53/1.13/1.13 s; GET p50/p95/p99 = 0.14/0.45/0.72 s. Model digest checked before launch: `a8b0c51577010a279d933d14c2a8ab4b268079d44c5c8830c0a93900f1827c67`. Copy the matching service log and resource statistics from the SUT Mac, then reconcile before marking valid. |

## Reconciliation queue

- [ ] Copy the service log covering 2026-10-06 16:53:40–17:08:40 SGT from the SUT Mac. The current local `logs/service/service-2026-10-06.jsonl` ends at 15:24:47 SGT and therefore contains none of this run's 43 request IDs.
- [ ] Copy the matching Docker/Ollama resource-statistics file from the SUT Mac.
- [ ] Run `python3 scripts/reconcile.py results/load/qwen2.5-0.5b/1.45rpm_s2.9_run1.jtl` after the service log is present locally.
- [ ] If reconciliation passes with no unexplained traffic, change the official run's `Reconciled` and `Valid` fields to `Yes`.
