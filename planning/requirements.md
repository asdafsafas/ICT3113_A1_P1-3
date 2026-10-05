# Performance and accuracy requirements (Step 4, Slide 4)

**Owner:** Natalie (with input from everyone) · **Status:** draft (5 Oct 2026; for team review before the freeze)

Each requirement must be **testable**: a number, a percentile where relevant, and the load condition under which it must hold. Each must be justified from the [workload model](workload-model.md) and other considerations: usability, the staffing cost of misrouted tickets, and capacity. If the workload model has peaks, the requirement must hold at the peak.

The brief deliberately does not say whether a misrouted ticket or a slow triage costs the client more. **Take a position here and state it**, because the recommendation must follow from it.

## Before the freeze (open items)

- [ ] Team agrees the position and thresholds below. They are stated before any benchmark and are not adjusted afterwards.
- [x] **Licences verified for C2** (see the C2 check below). `qwen2.5:3b` is under the Qwen Research License (non-commercial) and fails C2. It cannot be recommended, whatever it scores, but it is still benchmarked so the size trade-off is visible.
- [ ] The prediction record predicts against these load levels: **2.4 tickets/min** (peak, R1/R2), **4.8 tickets/min** (R3) and the stress steps, not the smoke-test throughput ceilings.

## Our position on misrouting vs speed

**A misrouted ticket costs the client more than a slow triage.** So we set firm accuracy requirements. On latency, we only ask that triage stays inside the intake's timeout and keeps up with peak arrivals.

- **Misrouting costs agent time and delays resolution.** A ticket in the wrong queue waits there until someone notices, then has to be re-read and re-routed. We estimate about 15 minutes of agent time per misrouted ticket, plus the delay. At ~252,000 tickets a year, every percentage point of accuracy is about 2,500 misrouted tickets, or about 630 agent-hours a year. Raising accuracy from 70% to 85% saves roughly 9,500 agent-hours, about five full-time agents.
- **Misrouting also puts regulatory deadlines at risk.** Companies must respond to a CFPB complaint within 15 days and close it within 60 [2]. Time a ticket spends in the wrong queue comes out of that window.
- **A few seconds of triage latency costs almost nothing.** The ticket then waits hours for an agent anyway, and the customer never sees triage happen. Latency only matters in two ways:
  - the synchronous `POST /tickets` must answer before the intake system gives up on it;
  - the service must keep up with peak arrivals, or a backlog builds without limit.

This position means we prefer a slower, more accurate model, **as long as it meets R1–R3**. It does not mean "the biggest model wins": a model that cannot sustain the peak fails R1/R3, however accurate it is.

## Requirements

All load conditions use open-loop arrivals at the stated rate (JMeter Open Model Thread Group or Precise Throughput Timer). Each configuration is run **3 times**, and percentiles are pooled across the runs.

| ID | Requirement | Load condition | Measured by | Justification |
|---|---|---|---|---|
| **R1** (response time, classification) | p95 latency of `POST /tickets` **≤ 15 s** and p99 **≤ 30 s**; error rate **≤ 1%** | Peak: **2.4 tickets/min** plus **8 searches/min**, sustained for 15 min, with latency not trending upward | JMeter `.jtl`, 3 runs; checked against service logs | 2.4/min is the busiest hour of a 95th-percentile day (workload model, section 2). The p99 bound of 30 s is half of nginx's default 60 s proxy read timeout [6], so a request behind a typical reverse proxy is not cut off. p95 ≤ 15 s leaves room for queueing behind the next arrival. |
| **R2** (response time, search) | p95 latency of `GET /search` **≤ 1 s** and p99 **≤ 2 s** | Mixed load: **2.4 tickets/min + 8 searches/min** (same runs as R1) | JMeter `.jtl`, 3 runs | Agents search interactively while working a ticket. 1 s is the limit for keeping the user's flow of thought uninterrupted [7]. 8 searches/min is the peak estimate (workload model, section 3). Search does not need the model, so it should not be slowed by classification queued behind it. |
| **R3** (throughput, headroom) | Sustain **≥ 4.8 tickets/min (288 tickets/hour)** with error rate **≤ 1%**, p95 `POST /tickets` **≤ 30 s**, and no upward latency trend | 4.8 tickets/min + 8 searches/min, sustained for 15 min | JMeter `.jtl`, 3 runs | 2 × the peak hour. Covers the surge hour (3.2/min, busiest day of the year at 2.3 × mean) with margin, plus uncertainty in the 15 : 1 direct-to-CFPB scaling (±20%). Below this, a surge builds a backlog that keeps growing until the surge ends. |
| **R4** (accuracy, overall) | **≥ 85%** of golden-set tickets classified correctly | Golden set (195 tickets), one pass per model, temperature 0 | `scripts/accuracy_test.py` | We treat misrouting as the dominant cost (position above). Our least accurate labeller matched the final golden labels on 83% of tickets (range 83–96% across the five labellers). A model that is not at least as good as a careful human labeller costs agents more re-routing time than it saves. That comparison flatters the humans slightly, because the golden labels came from their own sheets. At 85%, ~38,000 tickets a year would still be misrouted (about 9,500 agent-hours). |
| **R5** (accuracy, per category) | Every one of the 7 categories **≥ 70%** recall (share of that category's golden tickets classified correctly) | Golden set, as R4 | `scripts/accuracy_test.py` (per-category table and confusion matrix) | Each category is routed to a different team. Below 70%, about one in three of a team's tickets lands in another team's queue, and that team can no longer rely on its queue. The bound is lower than R4 because the smallest categories have only 17–18 golden tickets: one ticket moves a category's score by about 6 percentage points. |

## Constraints (pass/fail, from the brief and the client)

| ID | Constraint | How we check it |
|---|---|---|
| **C1** | Inference runs on CPU only, on hardware we control. No GPU, no public model API. | `ollama ps` shows `100% CPU` (screenshot for Slide 7). The model runs in Docker. |
| **C2** | The model's licence permits commercial deployment by the client. | Licence of each pinned model, checked on its Ollama or Hugging Face page (Slide 12). A model that fails C2 cannot be recommended, however well it scores. |

### C2 check: candidate sizes and licences (verified 5 Oct 2026)

The digests (first 12 characters) were confirmed against each model's Ollama library page. The licences were checked against each model's licence text.

| Model (Ollama tag) | Params | Quant | Size | Digest | Licence | Commercial use | C2 |
|---|---|---|---|---|---|---|---|
| `qwen2.5:0.5b` | 0.49B | Q4_K_M | 0.40 GB | `a8b0c5157701` | Apache 2.0 [8] | Yes | ✅ Pass |
| `llama3.2:1b-instruct-q4_K_M` | 1.24B | Q4_K_M | 0.81 GB | `22bc6b92eb01` | Llama 3.2 Community License [9] | Yes, unless the licensee has over 700 million monthly active users. Requires "Built with Llama" to be displayed and the Acceptable Use Policy to be followed. | ✅ Pass (with attribution) |
| `qwen2.5:3b` | 3.1B | Q4_K_M | 1.93 GB | `357c53fb659c` | **Qwen Research License** [10] | **No.** Rights are granted "for non-commercial purposes only", meaning "research or evaluation purposes only". Commercial users "shall request a license" from Alibaba Cloud. | ❌ **Fail.** Can be benchmarked (evaluation is permitted), but cannot be recommended without a separate commercial licence. |
| `qwen2.5:7b` | 7.6B | Q4_K_M | 4.68 GB | `845dbda0ea48` | Apache 2.0 [11] | Yes | ✅ Pass |

## Notes

- Percentiles: we report p50, p95 and p99 over successful requests; failed requests count towards the error rate.
- "Sustained" means the arrival rate is held for the full run and the latency does not keep growing (check the latency-over-time trend, not just the percentiles).
- **Small samples:** R1 and R3 runs send 36–72 tickets each, so p99 rests on very few requests. That is why we pool the three runs and report the spread across them.
- **Synchronous baseline:** `POST /tickets` blocks until the model answers. If the service handles requests one at a time, searches queue behind classification, and R2 can fail even though search itself is fast. That would be a finding to diagnose, not to fix in Assignment 1.
- **Every rate here scales with the workload model.** If Natalie revises the volume estimate, update R1–R3 before the freeze, not after.

## Sources

Sources [1]–[5] are listed in the [workload model](workload-model.md#sources).

6. NGINX, *ngx_http_proxy_module: `proxy_read_timeout`* (default 60 s). https://nginx.org/en/docs/http/ngx_http_proxy_module.html#proxy_read_timeout
7. J. Nielsen, *Response Times: The 3 Important Limits*, Nielsen Norman Group (1993, updated 2014). https://www.nngroup.com/articles/response-times-3-important-limits/
8. Qwen, *Qwen2.5-0.5B-Instruct* model card (Apache 2.0). https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct
9. Meta, *Llama 3.2 Community License Agreement* (25 Sep 2024), sections 1.b.i and 2. https://github.com/meta-llama/llama-models/blob/main/models/llama3_2/LICENSE
10. Alibaba Cloud, *Qwen Research License Agreement*, sections 1.i, 2.a and 2.b. https://huggingface.co/Qwen/Qwen2.5-3B-Instruct/blob/main/LICENSE
11. Qwen, *Qwen2.5-7B-Instruct* model card (Apache 2.0). https://huggingface.co/Qwen/Qwen2.5-7B-Instruct
