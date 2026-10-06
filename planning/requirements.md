# Performance and accuracy requirements (Step 4, Slide 4)

**Owner:** Zong Han (with input from everyone) · **Status:** draft for final team review before freeze

Each requirement must be **testable**: a number, a percentile where relevant, and the load condition under which it must hold. Each must be justified from the [workload model](workload-model.md) and other considerations: usability, the staffing cost of misrouted tickets, and capacity. If the workload model has peaks, the requirement must hold at the peak.

The brief deliberately does not say whether a misrouted ticket or a slow triage costs the client more. **Take a position here and state it**, because the recommendation must follow from it.

**Our position on misrouting vs speed:** a misrouted ticket costs the client more than a slow one. A misrouted complaint has to be noticed, re-read and passed on by a second team, which adds staff time and delays the customer's resolution. A classification that takes 30 seconds instead of 5 changes nothing for a customer whose complaint is answered by a person over hours or days. Our accuracy requirements therefore ask the model to match a trained human, and our latency requirement only has to keep the desk from falling behind.

| ID | Requirement | Load condition | Measured by | Justification |
|---|---|---|---|---|
| R1 (response time) | p95 latency of POST /tickets ≤ 30 s | Peak arrival rate of 1.73 tickets/min, sustained for 10 min | JMeter, 3 runs | At peak a ticket arrives every ~35 s (60 ÷ 1.73, [workload model](workload-model.md) section 2). If tickets are classified one at a time, classification slower than that builds a queue that does not clear; 30 s leaves headroom. Not stricter, because speed matters less than accuracy (our position above) |
| R2 (response time, search) | p95 latency of GET /search ≤ 1 s | Mixed load: 1.73 tickets/min + 3.5 searches/min, sustained for 10 min | JMeter, 3 runs | Searches are made by a handler waiting at a screen. About 1 s is the limit for a user's flow of thought to stay uninterrupted [1]. Search rate from workload model section 3 |
| R3 (throughput) | Achieved throughput ≥ 104 tickets classified per hour (1.73 per minute), error rate ≤ 1%, latency not growing over the run | Peak arrival rate of 1.73 tickets/min, sustained for 10 min | JMeter, 3 runs | 104 per hour is the peak-hour volume (workload model section 2). Throughput below the arrival rate means a growing backlog |
| R4 (accuracy, overall) | ≥ 80% of golden-set tickets correct | Golden set (195 tickets), one pass | accuracy_test.py | Before discussion, our own labellers agreed with each other on 78% to 85% of tickets ([golden/agreement_summary.md](../golden/agreement_summary.md)). 80% asks the model to match a single trained human. Not set lower, because misrouting is the costlier failure |
| R5 (accuracy, per category) | Every category ≥ 70% correct | Golden set, per category | accuracy_test.py | The smallest categories have 17 (Debt collection) and 18 (Credit card) golden tickets, so each error moves the score by about 6 points. A per-category bar must sit below the overall one to avoid failing a model on one or two tickets |

## Deployment constraints

- **C1 (local CPU inference):** testing and the recommendation must use Ollama locally on the assigned CPU-only machine; no public model API. Confirm the active model and processor using the service health data and `ollama ps`.
- **C2 (commercial suitability):** the recommended model must have licence terms compatible with the bank's commercial use. A model that fails this constraint may still be benchmarked for comparison, but cannot be recommended without a separate suitable licence.

## Sources

1. Nielsen, J. (1993). Response Times: The 3 Important Limits. Excerpt from Usability Engineering, Nielsen Norman Group. https://www.nngroup.com/articles/response-times-3-important-limits/

## Notes

- Percentiles: we report p50, p95 and p99 over successful requests; failed requests count towards the error rate.
- "Sustained" means the arrival rate is held for the full run and the latency does not keep growing (check the latency-over-time trend, not just the percentiles).
