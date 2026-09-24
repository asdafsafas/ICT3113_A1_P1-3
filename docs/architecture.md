# Architecture (Slide 2)

```
  Load-generator machine                 System-under-test machine (Docker)
 ┌──────────────────────┐      HTTP     ┌───────────────────────────────────────────────┐
 │ Apache JMeter        │  ───────────▶ │  triage (FastAPI, port 8000)                  │
 │  open-loop arrivals  │               │   POST /tickets ──▶ Ollama /api/generate ──┐  │
 │  (plays the intake   │  ◀─────────── │   GET  /search                              │  │
 │   and the agents)    │               │   GET  /stats          ┌────────────────────▼┐ │
 └──────────────────────┘               │      │                 │ ollama (CPU only)   │ │
                                        │      ▼                 │ one candidate model │ │
                                        │  SQLite (volume)       └─────────────────────┘ │
                                        │  request log ──▶ logs/service/*.jsonl (git)    │
                                        └───────────────────────────────────────────────┘
```

## Endpoints

| Endpoint | What it does |
|---|---|
| `POST /tickets` | Body `{"narrative": "..."}`. Calls the model once to classify the ticket into one of the 7 categories, stores the ticket and category, returns `{"id", "category", "model", "request_id"}`. **Returns only after the model has answered.** |
| `GET /search?q=<text>&limit=20` | Stored tickets whose narrative contains the text (newest first), with a 200-character snippet. |
| `GET /stats` | Number of stored tickets per category, and the total. |
| `GET /health` | Model name, its digest as installed in Ollama, and the prompt file. Used by scripts before a run. |

The service starts empty. Tickets only arrive through `POST /tickets`; the dataset is never loaded directly.

## Baseline: deliberately unoptimised

As the brief requires, this is the straightforward version. Optimisation is Assignment 2.

- **Synchronous:** the request waits for the model. No background queue.
- **No caching:** the same narrative sent twice is classified twice.
- **One model call per ticket**, no batching.
- **Search** is a plain `LIKE '%text%'` scan over every stored ticket, with no full-text index.
- **One worker process** (uvicorn `--workers 1`); requests run in FastAPI's thread pool.
- **SQLite**, new connection per request.

Known characteristics to watch for in testing (possible bottlenecks, not bugs):

- Ollama processes `OLLAMA_NUM_PARALLEL` requests at a time (default **1**) and queues the rest, up to `OLLAMA_MAX_QUEUE` (512). Beyond that it rejects requests, which shows up as 502s from our service.
- FastAPI's thread pool runs about 40 requests at once; more requests wait for a free thread.
- A request that waits longer than JMeter's response timeout (default 5 min) counts as an error, even if the service finishes it later.

## Classification

- The prompt template is [`service/prompts/classify_v1.txt`](../service/prompts/classify_v1.txt). `{narrative}` is replaced by the ticket text.
- Ollama's **structured output** (`format` with a JSON schema) restricts the reply to `{"category": "<one of the 7>"}`, so the answer is always a valid category.
- Generation options: `temperature=0`, `seed=42`, `num_ctx=4096` (set in `.env`). Tickets longer than the context window are truncated by Ollama; check `prompt_tokens` in the logs.
- If Ollama fails or times out, `POST /tickets` returns **502** and the reason is logged.

## Request log format

Every request (including errors and 404s) is one JSON line in `logs/service/service-YYYY-MM-DD.jsonl` (UTC dates):

| Field | Meaning |
|---|---|
| `ts` | When the response finished (UTC, ms) |
| `request_id` | From the `X-Request-ID` header (JMeter sets it), otherwise generated. Returned in the response header too. |
| `method`, `path`, `query`, `status` | The request and its HTTP status |
| `latency_ms` | Time inside the service, from request received to response sent |
| `model`, `model_digest` | Which model classified it (POST /tickets) |
| `narrative_chars`, `narrative_words` | Ticket length |
| `ollama_total_ms` | Ollama's total time for this request |
| `ollama_load_ms` | Time loading the model into memory (large = cold start) |
| `ollama_prompt_eval_ms`, `prompt_tokens` | Time and tokens to read the prompt (grows with ticket length) |
| `ollama_eval_ms`, `output_tokens` | Time and tokens to generate the answer |
| `category`, `ticket_id` | The result |
| `result_count` | Number of search results (GET /search) |
| `error` | Why it failed (502s) |

`latency_ms − ollama_total_ms` is time spent **waiting** before the model started on this ticket (queueing) plus our own overhead. It's the main clue for finding the bottleneck.

The service also writes one `"event": "startup"` line with the model, digest, prompt and generation options every time it starts.
