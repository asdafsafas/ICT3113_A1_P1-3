"""Ticket Triage Service.

Assignment 1 baseline (MODE=single, the default): POST /tickets is synchronous and calls
one model once per request, with no caching, batching or queueing.

Assignment 2 (MODE=cascade): a small model classifies every ticket and a rule decides
whether to escalate it to a large model. Still synchronous, still no caching. The response
looks the same either way; only the service log records which model answered.
"""

import time
import uuid

from fastapi import FastAPI, HTTPException, Query, Request
from pydantic import BaseModel, Field

from . import cascade, classifier, config, reqlog, storage

app = FastAPI(title="Ticket Triage Service")


def digests():
    return {m: classifier.model_digest(m) for m in config.models_in_use()}


@app.on_event("startup")
def startup():
    config.validate()
    storage.init()
    entry = {"event": "startup", "mode": config.MODE, "model": config.config_label(),
             "prompt_file": config.PROMPT_FILE.name, "num_ctx": config.NUM_CTX,
             "temperature": config.TEMPERATURE, "seed": config.SEED}
    if config.MODE == "single":
        entry["model_digest"] = classifier.model_digest()
    else:
        entry["model_digests"] = digests()
        entry["cascade"] = config.rule_description()
    reqlog.write(entry)


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
    log.update({"narrative_chars": len(ticket.narrative), "narrative_words": len(ticket.narrative.split())})

    if config.MODE == "single":
        log.update({"model": config.MODEL, "model_digest": classifier.model_digest()})
        try:
            category, stats = classifier.classify(ticket.narrative)
        except classifier.ClassificationError as e:
            log["error"] = str(e)
            raise HTTPException(status_code=502, detail=str(e))
        log.update(stats)
        final_model = config.MODEL
    else:
        log.update({"mode": "cascade", "model": config.config_label(), "model_digests": digests()})
        try:
            category, final_model = cascade.run(ticket.narrative, log)
        except classifier.ClassificationError as e:
            log["error"] = str(e)
            raise HTTPException(status_code=502, detail=str(e))
        log["final_model_digest"] = classifier.model_digest(final_model)
    log["category"] = category

    ticket_id = storage.insert_ticket(ticket.narrative, category, final_model, request.state.request_id,
                                      reqlog.utc_now().isoformat(timespec="milliseconds"))
    log["ticket_id"] = ticket_id
    # The response names the configuration, not the model that answered this ticket.
    return {"id": ticket_id, "category": category, "model": config.config_label(),
            "request_id": request.state.request_id}


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
    if config.MODE == "single":
        digest = classifier.model_digest()
        return {"status": "ok" if digest else "model_missing", "model": config.MODEL, "model_digest": digest,
                "prompt_file": config.PROMPT_FILE.name}
    d = digests()
    ok = all(d.values())
    return {"status": "ok" if ok else "model_missing", "mode": "cascade", "model": config.config_label(),
            # One string covering every model, so A1 scripts that require a digest still work.
            "model_digest": "+".join(d[m] for m in config.models_in_use()) if ok else None,
            "model_digests": d, "cascade": config.rule_description(), "prompt_file": config.PROMPT_FILE.name}
