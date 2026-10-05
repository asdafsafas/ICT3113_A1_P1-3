# Workload model (Step 3, Slide 3)

**Owner:** Natalie · **Status:** draft (figures compiled 5 Oct 2026; for Natalie to review)

The brief asks for a quantitative estimate of the client's workload, with a source for every figure. Each figure is marked **Sourced** (with a citation) or **Estimated** (with how we estimated it). Requirements in [requirements.md](requirements.md) follow from these numbers.

## Before the freeze (open items)

- [ ] **Natalie to review the three key estimates.** They are the weakest figures, and every rate below scales with them, so they need defending on Slide 3: the **15 : 1** direct-to-CFPB ratio (section 1); the busiest hour carrying **12%** of a day (section 2); and **~35 agents × 3 searches per ticket** (section 3). Replace any of them with better-sourced figures if you have them.
- [ ] Re-run the ticket-length table on all of rows 3000–3999 (section 4). The local spreadsheet has only rows 3000–3199.
- [ ] If any rate changes, update R1–R3 in [requirements.md](requirements.md) and the load levels used in the [prediction record](prediction-record.md) **before** the freeze.

## 0. Who the client is

The brief describes "a financial services company whose customer relations desk receives a steady stream of complaint tickets" across all seven categories. We model it as a **large US retail bank** (cards, deposits, mortgages, loans, payments), the kind of company that appears near the top of the CFPB's complaint list. We chose a large bank because a desk small enough to route tickets by hand comfortably would have little reason to automate.

## 1. Ticket volume

| Quantity | Value | Sourced / Estimated | Source or method |
|---|---|---|---|
| CFPB complaints about each of the five largest-volume banks, 2024 | Capital One 20,532; JPMorgan Chase 19,272; Wells Fargo 15,206; Citibank 14,668; Bank of America 14,341 (**mean 16,800**) | Sourced | CFPB Consumer Complaint Database API, complaints received 1 Jan–31 Dec 2024, aggregated by company [1] |
| Complaints a firm receives directly, per complaint escalated to an external body | **~15 : 1** (range 12–18) | Estimated | UK firms received 3.64 million complaints in 2024 (1.86 m H1 + 1.78 m H2) [3]. The Financial Ombudsman received 198,798 new complaints in 2023/24 and 305,726 in 2024/25 [4]. That gives a ratio of 12–18 direct complaints per escalated one. We assume the US pattern is similar and use the midpoint. |
| Complaints per year received by the client's desk | **~252,000** | Estimated | 16,800 CFPB complaints × 15 |
| Complaints per day, average (all days) | **~690** | Estimated | 252,000 ÷ 365 |
| Complaints per weekday, average | **~814** | Estimated | Weekly volume 4,833 × 84.2% weekday share (section 2) ÷ 5 |
| Complaints per hour, average (all hours of the year) | **~29** | Estimated | 252,000 ÷ 8,760 |

Every figure in the rest of this model scales linearly with the 15 : 1 ratio. At 12 : 1, all rates are 20% lower; at 18 : 1, they are 20% higher.

## 2. Peak vs non-peak

**Day of week (Sourced).** We measured this from every 2024 CFPB complaint about three banks: Truist (3,983 complaints), U.S. Bancorp (4,580) and TD Bank (4,050) [1]. All three show the same pattern:

| | Mon | Tue | Wed | Thu | Fri | Sat | Sun |
|---|---|---|---|---|---|---|---|
| Share of weekly complaints (mean of 3 banks) | 15.2% | **18.3%** | 17.5% | 17.0% | 16.2% | 8.9% | 6.8% |

**Busy days (Sourced).** Across the same three banks:
- the 95th-percentile day carries **1.7×** the mean daily volume (Truist 19 vs 10.9; U.S. Bancorp 21 vs 12.5; TD 19 vs 11.1);
- the busiest day of the year carries **2.3×** (24, 30 and 26 complaints respectively).

**Seasonality (Sourced).** The busiest month is 16–26% above the monthly mean: December for Truist, October for U.S. Bancorp and TD. October to December is busier than the first half of the year at all three banks [1]. The 95th-percentile day above already includes this.

**Hour of day (Estimated).** CFPB data records only the date, so the hourly profile is estimated. Contact centres see their busiest hours between 11:00 and 19:00 on weekdays [5]. Complaints can be submitted online at any hour, but most are written in the daytime. We assume:
- **70%** of a day's tickets arrive in the 9 business hours (09:00–18:00);
- the busiest single hour carries **12%** of the day (versus 11% for an even spread over those 9 hours, allowing for the midday peak).

| Period | Share of daily tickets | Tickets per hour | Sourced / Estimated | Source or method |
|---|---|---|---|---|
| Peak hour (busiest hour of a 95th-percentile day) | 12% | **~142** (2.4 per min) | Estimated, from sourced day ratios | 690 × 1.7 = 1,180 tickets/day; × 12% |
| Surge hour (busiest hour of the busiest day of the year) | 12% | **~191** (3.2 per min) | Estimated, from sourced day ratios | 690 × 2.3 = 1,590 tickets/day; × 12% |
| Normal business hours (average weekday) | 70% over 9 h | **~63** (1.1 per min) | Estimated | 814 × 70% ÷ 9 |
| Weekday nights | 30% over 15 h | **~16** (0.3 per min) | Estimated | 814 × 30% ÷ 15 |
| Weekends | Sat 8.9%, Sun 6.8% of the week | **~16** average (0.3 per min) | Sourced shares, estimated hours | 4,833 × 7.9% ≈ 380 per day ÷ 24 |

**Peak-to-average ratio:** about **4.9** (peak hour 142 ÷ year-round hourly average 29), or about **2.3** against an average business hour (142 ÷ 63). Requirements are set at the peak hour, with headroom for the surge hour.

## 3. Agent searches (GET /search)

No public source gives search rates for a complaints desk, so this whole section is estimated.

| Quantity | Value | Sourced / Estimated | Source or method |
|---|---|---|---|
| Agents on the desk | **~35** | Estimated | 814 tickets per weekday ÷ an assumed ~25 tickets handled per agent per day (about 15–20 minutes per ticket over a working day) |
| Searches per agent per hour | **~8** | Estimated | We assume ~3 searches per ticket handled (earlier complaints from the same customer, the same company, similar issues). 25 tickets × 3 ÷ 9 h ≈ 8 |
| Searches per minute, average business hour | **~4.5** | Estimated | 814 × 3 ÷ 9 h ÷ 60 |
| Searches per minute at peak | **~8** | Estimated | Peak day 1,180 × 3 ÷ 9 h ÷ 60 = 6.6, × 1.2 for the busiest hour of the day |

## 4. Ticket length distribution

We measured this from the 200 narratives in our local copy of the extract (rows 3000–3199, `ict3113_ticket_P1-3.xlsx`):

| | p5 | p25 | p50 | p75 | p95 | p99 | max |
|---|---|---|---|---|---|---|---|
| Words | 46 | 93 | 150 | 229 | 321 | 355 | 365 |
| Characters | 257 | 513 | 811 | 1,301 | 1,709 | 1,920 | 2,000 |

**To do:** re-run on all 1,000 of our rows with `python scripts/export_loadtest_data.py --source <course csv> --rows 3000-3999` and replace this table.

**What this means for the model:**
- At roughly 4 characters per token, the median ticket is about **200 tokens** and the 95th percentile about **430 tokens**. Our classification instructions add about 270 tokens.
- Total prompts are therefore about 470–700 tokens. That is far below the 4,096-token context window, so **no ticket is truncated**.
- The longest narrative is exactly 2,000 characters, which suggests the course extract caps narratives at that length. Real complaints can be much longer, so real-world latency could be higher than we measure. We state this as a limitation on Slide 7.
- Reading the input dominates latency on our hardware (80–88% of the time in Han's smoke tests). Latency should therefore grow roughly in proportion to ticket length. The p95 ticket should take noticeably longer than the median.

## 5. Summary: load levels to test

| Load level | Tickets per minute | Searches per minute | Why |
|---|---|---|---|
| Average | **1.1** | 4.5 | Average weekday business hour |
| Peak | **2.4** | 8 | Busiest hour of a 95th-percentile day. Requirements R1 and R2 must hold here. |
| Headroom | **4.8** | 8 | 2 × peak. Covers the surge hour (3.2 per min) with margin. Requirement R3. |
| Stress (beyond peak) | Steps of 2.4 (2.4, 4.8, 7.2, 9.6, 12, …) until latency grows without bound or errors exceed 1% | 8 | Finds the sustainable limit for each model |

These rates become the JMeter `rate` and `search_rate` values in [docs/load-testing.md](../docs/load-testing.md). At 2.4 tickets per minute, a 15-minute run sends about 36 tickets, so percentiles are pooled across the three runs of each configuration.

## Sources

1. Consumer Financial Protection Bureau, *Consumer Complaint Database*, search API, complaints received 1 Jan–31 Dec 2024, queried 5 Oct 2026. https://www.consumerfinance.gov/data-research/consumer-complaints/
2. Consumer Financial Protection Bureau, *Consumer Response Annual Report, January 1 – December 31, 2024* (May 2025). The CFPB received ~3,187,900 complaints and sent ~2,829,400 to ~3,600 companies. Companies must respond within 15 days and close within 60 days. https://files.consumerfinance.gov/f/documents/cfpb_cr-annual-report_2025-05.pdf
3. Financial Conduct Authority, *Aggregate complaints data 2024 H2* (2025). https://www.fca.org.uk/data/complaints-data/aggregate-complaints-data-2024-h2
4. Financial Ombudsman Service, *Annual complaints data and insight 2024/25* (2025). https://www.financial-ombudsman.org.uk/data-insight/our-insight/annual-complaints-data-insight-2024-25
5. Bright Pattern, *What are the busiest call center hours?* https://www.brightpattern.com/what-are-the-busiest-call-center-hours/
