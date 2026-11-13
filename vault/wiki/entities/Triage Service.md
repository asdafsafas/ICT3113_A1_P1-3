---
type: entity
title: "Triage Service"
created: 2026-11-13
updated: 2026-11-13
tags:
  - ict3113
  - entity
  - repository
status: mature
related:
  - "[[Ollama]]"
  - "[[Ticket Categories]]"
  - "[[Cascade Classification]]"
sources:
  - "[[Project Docs]]"
entity_type: repository
role: "The system under test: FastAPI service in Docker"
first_mentioned: "[[Assignment 1 Brief]]"
---

# Triage Service (system under test)

Code: `service/app/` (`main.py`, `classifier.py`, `config.py`, `reqlog.py`, `storage.py`), `service/Dockerfile`, `docker-compose.yml`.

## Endpoints

| Endpoint | Behaviour |
|---|---|
| `POST /tickets` | `{"narrative"}` → one Ollama call → store → `{id, category, model, request_id}`. **Returns only after the model answers.** 502 if Ollama fails or times out. |
| `GET /search?q=&limit=20` | `LIKE '%q%'` scan, newest first, 200-char snippet |
| `GET /stats` | Count per category + total |
| `GET /health` | Model, installed digest, prompt file |

## Deliberately unoptimised baseline
Synchronous; no cache; one model call per ticket; no full-text index; **1 uvicorn worker** (FastAPI thread pool of ~40); SQLite with a new connection per request.

## Prompt
`service/prompts/classify_v1.txt` (395 chars) lists the 7 category **names only, without definitions**, and asks for `{"category": ...}`. It is frozen. A2 keeps it unchanged.

## Request log (`logs/service/service-YYYY-MM-DD.jsonl`)
One line per request, with: `ts`, `request_id`, `method/path/status`, `latency_ms`, `model`, `model_digest`, `narrative_chars/words`, `ollama_total_ms`, `ollama_load_ms`, `ollama_prompt_eval_ms`, `prompt_tokens`, `ollama_eval_ms`, `output_tokens`, `category`, `ticket_id`, `result_count`, `error`. There is also a startup event line.
**`latency_ms − ollama_total_ms`** is the time spent queueing plus overhead.

## A2 changes (PR #13)
- `MODE=single` (the default) is unchanged from A1.
- `MODE=cascade` runs small model → rule → large model, and the caller still gets one category.
- The log gains `escalated`, `final_model`, `final_model_digest`, `small_category` and per-call `calls[]`.
- `/health` lists every model's digest (`model_digests`) and the rule.

See [[Cascade Classification]] and [[A2 Playbook]].
