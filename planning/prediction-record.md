# Prediction record (Step 4, Slide 11)

> **Freeze rule:** this file is committed together with the golden set **before the first benchmark run**, and must not be edited afterwards. The commit history is our evidence. Corrections go in the report as "where we were wrong", never here.

**Committed on:** ____ · **Commit / tag:** ____

Marks are for being **specific enough to be proven wrong**, not for being right. "The model will be slow" earns nothing; "qwen2.5:7b will take 25–40 s per ticket and p95 will exceed 120 s at 4 tickets/min" can be checked.

**What these predictions are based on (all available before any model saw a golden ticket):**
- **Han's smoke tests:** one *invented* 136-character ticket per model on the system-under-test machine (logs `logs/smoke_*`).
- **Ticket lengths** of all 1,000 allocated rows (3000–3999): character counts only, no model involved ([workload model](workload-model.md), section 4).
- **The baseline service's configuration:** FastAPI with 1 uvicorn worker, synchronous endpoints, `OLLAMA_NUM_PARALLEL=1`, `OLLAMA_TIMEOUT_S=600`.
- **Our own labelling disagreements** ([golden/agreement_summary.md](../golden/agreement_summary.md)).

**How latency was extrapolated:**
- In the smoke tests, reading the prompt took 80–88% of each request. The time per prompt token (1.6 / 1.6 / 5.0 / 11.0 ms for 0.5B / 1B / 3B / 7B) was applied to each real ticket's length.
- Ticket length in tokens was estimated as characters ÷ 4, plus about 272 tokens of instructions. The smoke tests' answer-generation time was added.
- Queueing was estimated by treating Ollama as a single server (M/G/1 queue) handling one request at a time.
- The ranges allow ±30% for tokenizer differences and for prompt reading slowing down on longer prompts.

## 1. Where the bottleneck will be under load, and why

- **The bottleneck is the Ollama model server, specifically CPU time spent reading the prompt.** No other component comes close:
  - `OLLAMA_NUM_PARALLEL=1` makes Ollama classify one ticket at a time. Every other request waits in line.
  - While a 7B request runs, the Ollama container uses all 10 allocated CPUs (≥ 90% in `docker stats`). The triage service container stays **below 10% CPU**.
  - Memory holds steady at the loaded model size (about 5.1 GB for 7B) and does not grow during a run.
  - SQLite and the network are not expected to be limits at the assignment's standard rates. We predict `GET /search` p95 stays **under 100 ms** at peak, because each run stores fewer than 200 tickets and a full-table `LIKE` scan over them is fast.
- **Where it saturates, by model.** Ollama's capacity is about 1 ÷ mean service time.
  - **qwen2.5:7b** has a mean service time of about 6.4 s, so capacity is about **9.4 tickets/min**. At the stress steps:
    - **7.2/min:** still stable (utilisation about 0.76), but p95 rises to about **30–45 s**.
    - **9.6/min:** the queue does not drain during a sustained limit-finding run. p95 grows throughout the run and ends above 60 s.
    - **12/min:** the backlog grows by about 2.6 tickets/min.
  - **qwen2.5:3b** (capacity about 21/min), **llama3.2:1b** and **qwen2.5:0.5b** (about 65/min each) do not saturate at any rate up to 12/min.
- **What we expect to observe at saturation:**
  - Achieved throughput levels off at about 9.4/min while the offered rate keeps rising.
  - p95 and p99 latency rise in a straight line over time, not to a plateau.
  - Errors appear only once a request has waited longer than the 600 s Ollama timeout, which needs a backlog of about 95 tickets.
- **A second bottleneck, under stress only.** FastAPI runs synchronous endpoints on a shared pool of **40 threads**. Each waiting `POST /tickets` holds a thread while it waits for Ollama.
  - Once more than about 40 classification requests are queued, `GET /search` requests wait for a free thread too.
  - Search p95 then jumps from under 100 ms to **over 10 s**, even though search never touches the model.
  - For qwen2.5:7b at 12 tickets/min, this happens about **15 minutes** into the run (40 ÷ 2.6 per min).
  - At the assignment peak (1.73/min) and fixed beyond-peak check (3.5/min), the backlog stays far below 40, so search is unaffected.

## 2. Per candidate model

Hardware: MacBook Pro (Mac17,2), Apple M5, 10 cores (4 performance + 6 efficiency), 16 GB RAM, macOS 26.6.2. Docker 29.8.2 Linux VM with 10 CPUs and 9.7 GiB RAM. Ollama 0.35.1, CPU only. Settings: temperature 0, seed 42, `num_ctx` 4096, JSON-schema-constrained output.

**"Single-request latency"** means the predicted `POST /tickets` latency with one request in flight over the golden ticket-length distribution: the p50, with the p95 in brackets. These values must remain predictions until the frozen record is committed and the real accuracy test is run.

| Model (tag) | Size class | Expected accuracy on golden set | Expected single-request latency | Reasoning |
|---|---|---|---|---|
| `qwen2.5:0.5b` | < 1B | **45%** (range 35–55%) | **0.8 s** (range 0.6–1.1 s); p95 1.2 s | The prompt gives category names only, without definitions. A 0.5B model cannot tell apart categories it has never had defined (Consumer loan, Money transfer) and falls back on the most frequent-sounding one. Prediction: **Credit reporting accounts for over 35% of its answers**, against 22% in the golden set. |
| `llama3.2:1b-instruct-q4_K_M` | ~1B | **55%** (range 45–65%) | **0.9 s** (range 0.6–1.1 s); p95 1.2 s | Better at following instructions than the 0.5B model, but still too small to apply rules like "who is the complaint against". It reads input at the same speed as the 0.5B model (497 vs 502 ms in the smoke test), so **its p50 will be within 10% of the 0.5B model's** while being about 10 points more accurate. |
| `qwen2.5:3b` | ~3B | **72%** (range 64–79%) | **2.6 s** (range 1.8–3.4 s); p95 3.8 s | The usual large step up from 1B to 3B. Mostly correct on clear-cut tickets (Mortgage, Credit card), but loses the Credit reporting vs Debt collection and Bank account vs Money transfer splits that our own labellers argued about. Its non-commercial licence is predicted to fail the commercial-suitability constraint regardless of its benchmark result. |
| `qwen2.5:7b` | ~7B | **78%** (range 72–84%) | **6.1 s** (range 4.3–7.9 s); p95 8.6 s | The most accurate, but **slightly below R4's 80%**. Without our protocol's edge-case rules in the prompt, it labels collector complaints that mention credit reports as Credit reporting, which is the error our own labellers made before v0.2. |

**Predictions against the requirements:**
- **R1** (POST p95 ≤ 30 s at 1.73 tickets/min for 10 min): **all four models pass.** qwen2.5:7b has the highest predicted p95, about **9–11 s**, because its estimated utilisation is only about 0.18 at this rate.
- **R2** (search p95 ≤ 1 s at peak): **all four pass**, with p95 under 100 ms.
- **R3** (achieved throughput ≥ 104/hour, error rate ≤ 1%, and no growing latency at 1.73/min): **all four pass.** Even qwen2.5:7b's predicted capacity of about 9.4/min is well above the offered peak rate.
- **Fixed beyond-peak check** (3.5 tickets/min + 7 searches/min): **all four remain stable.** qwen2.5:7b has the least margin, with utilisation about 0.37 and predicted POST p95 around **12–15 s**.
- **R4** (overall accuracy ≥ 80%): **no candidate passes in the point predictions.** The best (qwen2.5:7b) falls short by about 2 points, although its prediction range crosses the threshold.
- **R5** (every category ≥ 70%): **no candidate passes.** qwen2.5:7b's weakest category is **Debt collection or Consumer loan, at 55–68%**.
- **Overall: no candidate meets every requirement in the point predictions.** All four pass R1–R3, but the 0.5B and 1B models miss R4 by about 25–35 points, the 3B model by about 8 points, and the 7B model by about 2 points. The 7B model also misses R5, while the 3B model is unsuitable for recommendation under the commercial-licence constraint regardless of performance.

## 3. Hardest categories to classify, and why

| Category | Why we expect it to be hard | Likely confused with |
|---|---|---|
| **Debt collection** | Most debt collection complaints also mention the credit report, because collectors report debts to the bureaus. Our protocol labels by **who the complaint is against** (rule v0.2), which a model given only category names cannot know. This was Group A's most common disagreement (4 tickets), and the source of 5 of Group A's resolutions (3025, 3039, 3055, 3071, 3072). | **Credit reporting** (most errors), then Credit card (card debt sold to a collector, e.g. 3175) |
| **Consumer loan** | The name is vague, and the category gathers loans that look unrelated: student loans, car loans, personal loans, and loans of unstated type (rule v0.3). Complaints about a lender's reporting go here under v0.2 (3080, 3141), but the text is mostly about the credit report. Our labellers split on Consumer loan vs Credit reporting 3 times in Group A alone. | **Credit reporting**, then Mortgage ("loan servicer", e.g. 3152) and Debt collection (3101) |
| **Bank account or service vs Money transfer or service** | Fraud and transfers are described in the same words in both categories ("wire", "transfer", "unauthorized"). Our split, bank-account takeover vs a transfer service the person used (v0.2/v0.3), depends on details. This was Group B's most common disagreement (6 tickets) and appears 3 times in Group A. | Each other, both ways. Expect **at least 25% of Money transfer tickets** labelled Bank account by qwen2.5:7b. |
| *Easiest:* **Mortgage** and **Credit reporting** | Distinctive vocabulary ("escrow", "servicer", "foreclosure"; "Equifax", "TransUnion", "dispute"). Credit reporting is also the largest class (42 of 195) and what models default to. | Expect **recall ≥ 90%** for both on qwen2.5:7b, but Credit reporting **precision ≤ 75%**, because it absorbs Debt collection and Consumer loan errors. |

## 4. Other predictions (optional)

- **Latency grows with ticket length.** Within each model, `POST /tickets` latency correlates strongly with narrative length (Pearson r ≥ 0.8). The longest quarter of tickets takes **≥ 1.5×** the median latency on qwen2.5:7b.
- **Accuracy does not grow as fast as latency.** Going from 3B to 7B costs about **2.3×** the latency for about **+6 points** of accuracy.
- **Run-to-run spread is small.** At temperature 0 with a fixed seed, the three runs of each load configuration differ by **less than 10%** in p50 latency. The same model gives identical labels on repeated accuracy passes.
- **Invalid outputs are rare.** The JSON schema constrains the output, so fewer than 1% of responses fail to map to one of the seven categories, for every model.
