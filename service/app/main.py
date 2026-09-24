"""Ticket Triage Service (Assignment 1 baseline).

Deliberately naive: POST /tickets is synchronous and calls the model once per
request, with no caching, batching or queueing. Optimisation is Assignment 2.
"""

import time
import uuid

from fastapi import FastAPI, HTTPException, Query, Request
from pydantic import BaseModel, Field

from . import classifier, config, reqlog, storage

app = FastAPI(title="Ticket Triage Service")


@app.on_event("startup")
def startup():
    if not config.MODEL:
        raise RuntimeError("MODEL is not set; copy .env.example to .env and choose a model")
    storage.init()
    reqlog.write({"event": "startup", "model": config.MODEL, "model_digest": classifier.model_digest(),
                  "prompt_file": config.PROMPT_FILE.name, "num_ctx": config.NUM_CTX,
                  "temperature": config.TEMPERATURE, "seed": config.SEED})


@app.middleware("http")
async def log_every_request(request: Request, call_next):
    request_id = request.headers.get("x-request-id") or uuid.uuid4().hex
    request.state.request_id = request_id
    request.state.log = {}
    start = time.perf_counter()
    status = 500
    try:
        response = await call_next(request)
        status = response.status_code
        response.headers["X-Request-ID"] = request_id
        return response
    finally:
        reqlog.write({
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "query": request.url.query or None,
            "status": status,
            "latency_ms": round((time.perf_counter() - start) * 1000, 1),
            "client": request.client.host if request.client else None,
            **request.state.log,
        })


class TicketIn(BaseModel):
    narrative: str = Field(min_length=1)


@app.post("/tickets")
def create_ticket(ticket: TicketIn, request: Request):
    log = request.state.log
    log.update({"model": config.MODEL, "model_digest": classifier.model_digest(),
                "narrative_chars": len(ticket.narrative), "narrative_words": len(ticket.narrative.split())})
    try:
        category, stats = classifier.classify(ticket.narrative)
    except classifier.ClassificationError as e:
        log["error"] = str(e)
        raise HTTPException(status_code=502, detail=str(e))
    log.update(stats)
    log["category"] = category

    ticket_id = storage.insert_ticket(ticket.narrative, category, config.MODEL, request.state.request_id,
                                      reqlog.utc_now().isoformat(timespec="milliseconds"))
    log["ticket_id"] = ticket_id
    return {"id": ticket_id, "category": category, "model": config.MODEL, "request_id": request.state.request_id}


@app.get("/search")
def search(request: Request, q: str = Query(min_length=1), limit: int = Query(20, ge=1, le=100)):
    results = storage.search(q, limit)
    request.state.log["result_count"] = len(results)
    return {
        "query": q,
        "count": len(results),
        "results": [
            {"id": r["id"], "category": r["category"], "created_at": r["created_at"],
             "snippet": r["narrative"][:200]}
            for r in results
        ],
    }


@app.get("/stats")
def stats():
    counts = storage.counts_by_category()
    by_category = {c: counts.get(c, 0) for c in config.CATEGORIES}
    return {"total": sum(by_category.values()), "by_category": by_category}


@app.get("/health")
def health():
    digest = classifier.model_digest()
    return {"status": "ok" if digest else "model_missing", "model": config.MODEL, "model_digest": digest,
            "prompt_file": config.PROMPT_FILE.name}
