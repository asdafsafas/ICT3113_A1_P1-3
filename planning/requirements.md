# Performance and accuracy requirements (Step 4, Slide 4)

**Owner:** Natalie (with input from everyone) · **Status:** draft

Each requirement must be **testable**: a number, a percentile where relevant, and the load condition under which it must hold. Each must be justified from the [workload model](workload-model.md) and other considerations: usability, the staffing cost of misrouted tickets, and capacity. If the workload model has peaks, the requirement must hold at the peak.

The brief deliberately does not say whether a misrouted ticket or a slow triage costs the client more. **Take a position here and state it**, because the recommendation must follow from it.

**Our position on misrouting vs speed:** ____

| ID | Requirement | Load condition | Measured by | Justification |
|---|---|---|---|---|
| R1 (response time) | e.g. p95 latency of POST /tickets ≤ __ s | e.g. at peak arrival rate of __ tickets/min, sustained for 10 min | JMeter, 3 runs | |
| R2 (response time, search) | e.g. p95 latency of GET /search ≤ __ ms | under mixed load: peak tickets + __ searches/min | JMeter, 3 runs | |
| R3 (throughput) | e.g. ≥ __ tickets classified per hour with error rate ≤ __% | sustained at peak for 10 min | JMeter, 3 runs | |
| R4 (accuracy, overall) | e.g. ≥ __% of golden-set tickets correct | golden set, one pass | accuracy_test.py | |
| R5 (accuracy, per category) | e.g. every category ≥ __% | golden set | accuracy_test.py | |

## Notes

- Percentiles: we report p50, p95 and p99 over successful requests; failed requests count towards the error rate.
- "Sustained" means the arrival rate is held for the full run and the latency does not keep growing (check the latency-over-time trend, not just the percentiles).
