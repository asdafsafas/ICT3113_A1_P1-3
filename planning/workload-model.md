# Workload model (Step 3, Slide 3)

**Owner:** Zong Han · **Status:** draft for final team review before freeze

The brief asks for a quantitative estimate of the client's workload, with a source for every figure. Mark each figure as **Sourced** (with a citation) or **Estimated** (with how you estimated it). Requirements in [requirements.md](requirements.md) must follow from these numbers.

## 1. Ticket volume

**Client assumption:** a large UK retail bank, anchored on the published complaints report of Bank of Scotland plc (Lloyds Banking Group, covering brands including Bank of Scotland and Halifax) for 1 July to 31 December 2025 [1]. The report counts complaints from all channels, including phone [5]; we treat every complaint as a ticket, which overstates written volume and so makes testing more demanding.

| Quantity | Value | Sourced / Estimated | Source or method |
|---|---|---|---|
| In-scope complaints per half-year | 86,719 | Sourced | [1]: Banking and credit cards 67,071 + Home finance 12,223 + Credit related 7,425. Insurance, pensions and investments (214) excluded as outside our 7 categories |
| Complaints per year received by the client's desk | ~173,400 | Estimated | 86,719 × 2. UK complaint totals have stayed between 1.7m and 2.0m per half-year since 2021 [2], so one half-year is a fair basis |
| Complaints per business day | ~694 | Estimated | 173,438 ÷ 250 business days |
| Complaints per hour, average | ~87 (≈ 1.45 per minute) | Estimated | 694 ÷ 8 business hours. Assumes all complaints are handled in business hours, which overstates the hourly rate; section 2 models the peak hour |

## 2. Peak vs non-peak

Arrivals at a bank's contact centre are not flat across the day: volume peaks mid-morning and mid-afternoon [3]. We model one peak hour and treat the rest of the business day as normal load.

| Period | Share of daily tickets | Tickets per hour | Sourced / Estimated | Source or method |
|---|---|---|---|---|
| Peak hour | 15% | ~104 (≈ 1.73 per minute) | Estimated | Busiest hour carries about 15% of a day's volume [4]. 694 × 15% ≈ 104 |
| Normal business hours (other 7 hours) | 85% | ~84 (≈ 1.4 per minute) | Estimated | (694 − 104) ÷ 7 hours |
| Nights / weekends | 0% (folded into business hours) | 0 | Estimated | Out-of-hours submissions are treated as arriving in business hours (section 1). This puts all load into business hours, the more demanding case for testing |

No seasonal or day-of-week peak is modelled, since we found no published figure for its size; the stress level in section 5 covers load above this peak.

**Peak-to-average ratio:** 1.2 (104 ÷ 87). Requirements must hold at the exact peak test rate of **1.73 tickets per minute** (104 ÷ 60).

## 3. Agent searches (GET /search)

We found no published figure for how often complaint handlers search past cases, so this section is estimated. We tie the search rate to ticket volume rather than to headcount, since each search is triggered by a handler working on a ticket.

| Quantity | Value | Sourced / Estimated | Source or method |
|---|---|---|---|
| Agents on the desk | Not modelled | n/a | Not needed: the search rate is derived per ticket below, so it does not depend on headcount |
| Searches per ticket handled | 2 | Estimated | One search for the customer's earlier complaints, one for similar complaints (duplicates or a wider issue) |
| Searches per minute, average | ~2.9 | Estimated | 1.45 tickets per minute (section 1) × 2 |
| Searches per minute at peak | ~3.5 | Estimated | 1.73 tickets per minute (section 2: 104 ÷ 60) × 2 |

## 4. Ticket length distribution

Measured from the exact 1,000 tickets committed in this repository: rows 3000–3199 from `ict3113_ticket_P1-3.xlsx` plus rows 3200–3999 from `loadtest/data/load-test-tickets.csv` (1,000 rows, contiguous, no overlap). Lengths are counted exactly as stored (Python `len()` for characters, whitespace-split for words, nearest-rank percentiles via `scripts/common.py`). Reproduce with `python3 scripts/ticket_lengths.py`.

| | p5 | p25 | p50 | p75 | p95 | p99 | max |
|---|---|---|---|---|---|---|---|
| Words | 49 | 94 | 144 | 214 | 322 | 361 | 385 |
| Characters | 263 | 512 | 797 | 1214 | 1780 | 1938 | 2000 |

*Correction (before the prediction freeze):* an earlier version of this table, computed from the course CSV, reported p25 514, p75 1,218, p95 1,789 and p99 1,940 characters. The committed files store line breaks as `\n` only (72 of the 1,000 tickets contain line breaks; none contain `\r`), so the earlier figures most likely counted Windows `\r\n` line endings as two characters. Word counts and the median are unchanged. The committed figures are what the service receives, because JMeter sends the committed narratives.

What this means for the model:

- **Processing time varies with length.** A p95 ticket (1,780 characters) is about 2.2 times the length of a median ticket (797), so per-ticket latency should vary noticeably across the test traffic.
- **No ticket should be truncated.** The longest ticket plus the prompt template (`service/prompts/classify_v1.txt`, 395 characters) is 2,395 characters. Even at one token per character, far more than English text normally uses, this fits within the default context window of 4,096 tokens (`NUM_CTX` in `.env.example`). The service logs `prompt_tokens` per request, so this can be confirmed from the logs.
- **Ticket length appears capped at 2,000 characters** in our allocated extract: the longest of our 1,000 rows is exactly 2,000 characters. The real client could see longer tickets than those available to our team.

## 5. Summary: load levels to test

| Load level | Tickets per minute | Searches per minute | Why |
|---|---|---|---|
| Average | 1.45 | 2.9 | Average business-hour rate (sections 1 and 3) |
| Peak | 1.73 | 3.5 | Busiest hour: 104 ÷ 60 (sections 2 and 3). Requirements must hold at this level |
| Stress (beyond peak) | 3.5 | 7 | Estimated: twice the peak (1.73 × 2), to cover the day-of-week and seasonal surges we could not size from published data (section 2) |

These rates become the JMeter `rate` and `search_rate` values in [docs/load-testing.md](../docs/load-testing.md). The stress level above is a fixed check beyond peak; the separate stress test that finds the system's limit (docs/load-testing.md, section 6) ramps the rate up until latency grows without bound.

## Sources

1. Lloyds Banking Group, Complaints publication report: Bank of Scotland plc, 1 July to 31 December 2025. https://www.lloydsbankinggroup.com/assets/pdfs/who-we-are/customer-complaints/2025/h2-2025/bank-of-scotland-plc.pdf
2. Financial Conduct Authority, Aggregate complaints data: 2025 H2. https://www.fca.org.uk/data/complaints-data/aggregate-complaints-data-2025-h2
3. Brown, L., Gans, N., Mandelbaum, A., Sakov, A., Shen, H., Zeltyn, S. and Zhao, L. (2005). Statistical Analysis of a Telephone Call Center: A Queueing-Science Perspective. Journal of the American Statistical Association, 100(469), 36-50. https://core.ac.uk/download/132271168.pdf
4. Soon, How many agents do you need for 500 calls a day? https://soon.works/staffing/call-center/500-calls-per-day
5. Financial Conduct Authority, FCA Handbook Glossary: complaint. https://handbook.fca.org.uk/glossary/G197
