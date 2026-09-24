# Workload model (Step 3, Slide 3)

**Owner:** Natalie · **Status:** draft

The brief asks for a quantitative estimate of the client's workload, with a source for every figure. Mark each figure as **Sourced** (with a citation) or **Estimated** (with how you estimated it). Requirements in [requirements.md](requirements.md) must follow from these numbers.

## 1. Ticket volume

| Quantity | Value | Sourced / Estimated | Source or method |
|---|---|---|---|
| Complaints per year received by the client's desk | | | |
| Complaints per business day | | | |
| Complaints per hour, average | | | |

Suggested approach: start from published CFPB complaint volumes (for example, total complaints per year and the share going to large institutions), then scale to a plausible mid-sized financial services company. State the scaling assumption.

## 2. Peak vs non-peak

| Period | Share of daily tickets | Tickets per hour | Sourced / Estimated | Source or method |
|---|---|---|---|---|
| Peak hour(s) | | | | |
| Normal business hours | | | | |
| Nights / weekends | | | | |

Include any seasonal peaks (for example, tax season, month-end statements) if you find evidence for them.
**Peak-to-average ratio:** ____ (requirements must cater for the peak).

## 3. Agent searches (GET /search)

| Quantity | Value | Sourced / Estimated | Source or method |
|---|---|---|---|
| Agents on the desk | | | |
| Searches per agent per hour | | | |
| Searches per minute at peak | | | |

## 4. Ticket length distribution

Measured from our team's rows by running `python scripts/export_loadtest_data.py --source <course csv> --rows 3000-3999`:

| | p5 | p25 | p50 | p75 | p95 | p99 | max |
|---|---|---|---|---|---|---|---|
| Words | | | | | | | |
| Characters | | | | | | | |

Note what this means for the model: long tickets take longer to process, and tickets over the context window (NUM_CTX tokens) get truncated.

## 5. Summary: load levels to test

| Load level | Tickets per minute | Searches per minute | Why |
|---|---|---|---|
| Average | | | |
| Peak | | | |
| Stress (beyond peak) | | | |

These rates become the JMeter `rate` and `search_rate` values in [docs/load-testing.md](../docs/load-testing.md).

## Sources

1.
