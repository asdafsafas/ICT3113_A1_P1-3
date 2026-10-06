"""Dry-run-only HTTP server matching the triage service contract.

This exists solely to validate the JMeter plan before the real service is
available. It does not call Ollama and its timings must never be reported as
assignment results.
"""

import argparse
import json
import threading
import time
import uuid
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse


CATEGORIES = [
    "Credit reporting",
    "Debt collection",
    "Mortgage",
    "Credit card",
    "Bank account or service",
    "Consumer loan",
    "Money transfer or service",
]


def utc_now():
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


class State:
    def __init__(self, log_dir, delay_ms):
        self.log_dir = Path(log_dir)
        self.delay_ms = delay_ms
        self.lock = threading.Lock()
        self.next_id = 1
        self.tickets = []

    def add_ticket(self, narrative, category, request_id):
        with self.lock:
            ticket_id = self.next_id
            self.next_id += 1
            self.tickets.append({
                "id": ticket_id,
                "narrative": narrative,
                "category": category,
                "request_id": request_id,
                "created_at": utc_now(),
            })
            return ticket_id

    def write_log(self, entry):
        self.log_dir.mkdir(parents=True, exist_ok=True)
        path = self.log_dir / f"service-{datetime.now(timezone.utc):%Y-%m-%d}.jsonl"
        with self.lock, open(path, "a", encoding="utf-8") as handle:
            handle.write(json.dumps({"ts": utc_now(), **entry}, ensure_ascii=False) + "\n")


class Handler(BaseHTTPRequestHandler):
    server_version = "TriageDryRunMock/1.0"

    def log_message(self, _format, *_args):
        return

    def send_json(self, status, payload, request_id):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Request-ID", request_id)
        self.end_headers()
        self.wfile.write(body)

    def request_id(self):
        return self.headers.get("X-Request-ID") or uuid.uuid4().hex

    def do_GET(self):
        started = time.perf_counter()
        request_id = self.request_id()
        parsed = urlparse(self.path)
        status = 200

        if parsed.path == "/health":
            payload = {
                "status": "ok",
                "model": "dry-run-mock",
                "model_digest": "dry-run-only",
                "prompt_file": "none",
            }
        elif parsed.path == "/search":
            query = parse_qs(parsed.query).get("q", [""])[0]
            matches = [
                {
                    "id": ticket["id"],
                    "category": ticket["category"],
                    "created_at": ticket["created_at"],
                    "snippet": ticket["narrative"][:200],
                }
                for ticket in self.server.state.tickets
                if query.lower() in ticket["narrative"].lower()
            ][:20]
            payload = {"query": query, "count": len(matches), "results": matches}
        elif parsed.path == "/stats":
            counts = {category: 0 for category in CATEGORIES}
            for ticket in self.server.state.tickets:
                counts[ticket["category"]] += 1
            payload = {"total": len(self.server.state.tickets), "by_category": counts}
        else:
            status = 404
            payload = {"detail": "Not found"}

        self.send_json(status, payload, request_id)
        self.server.state.write_log({
            "request_id": request_id,
            "method": "GET",
            "path": parsed.path,
            "query": parsed.query or None,
            "status": status,
            "latency_ms": round((time.perf_counter() - started) * 1000, 1),
            "model": "dry-run-mock",
        })

    def do_POST(self):
        started = time.perf_counter()
        request_id = self.request_id()
        parsed = urlparse(self.path)
        status = 200

        try:
            size = int(self.headers.get("Content-Length", "0"))
            body = json.loads(self.rfile.read(size).decode("utf-8"))
        except (ValueError, UnicodeDecodeError, json.JSONDecodeError):
            body = None

        if parsed.path != "/tickets":
            status = 404
            payload = {"detail": "Not found"}
        elif not isinstance(body, dict) or not isinstance(body.get("narrative"), str) or not body["narrative"].strip():
            status = 422
            payload = {"detail": "A non-empty narrative is required"}
        else:
            narrative = body["narrative"].strip()
            if self.server.state.delay_ms:
                time.sleep(self.server.state.delay_ms / 1000)
            category = CATEGORIES[sum(narrative.encode("utf-8")) % len(CATEGORIES)]
            ticket_id = self.server.state.add_ticket(narrative, category, request_id)
            payload = {
                "id": ticket_id,
                "category": category,
                "model": "dry-run-mock",
                "request_id": request_id,
            }

        self.send_json(status, payload, request_id)
        self.server.state.write_log({
            "request_id": request_id,
            "method": "POST",
            "path": parsed.path,
            "query": None,
            "status": status,
            "latency_ms": round((time.perf_counter() - started) * 1000, 1),
            "model": "dry-run-mock",
            "category": payload.get("category"),
        })


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=18000)
    parser.add_argument("--delay-ms", type=int, default=25)
    parser.add_argument("--log-dir", required=True)
    args = parser.parse_args()

    server = ThreadingHTTPServer((args.host, args.port), Handler)
    server.state = State(args.log_dir, args.delay_ms)
    print(f"Dry-run mock listening on http://{args.host}:{args.port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
