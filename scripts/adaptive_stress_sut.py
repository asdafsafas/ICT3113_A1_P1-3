#!/usr/bin/env python3
"""Run the SUT side of the adaptive 7B stress test.

Start this once on the Mac that runs Docker.  The load-generator script calls
this small token-protected HTTP agent before and after every rate.  It resets
and warms the SUT, captures Docker statistics, extracts the exact service-log
records named by JMeter request IDs, and returns the evidence to the load Mac.

The agent is intended only for a trusted local network.  It deliberately binds
to localhost unless --bind is supplied.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[1]
DEFAULT_MODEL = "qwen2.5:7b"
STAGE_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,79}\Z")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def read_json_url(url: str, timeout: float = 10) -> dict[str, Any]:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            return json.load(response)
    except (OSError, urllib.error.URLError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Could not read {url}: {exc}") from exc


class SutController:
    def __init__(self, model: str, results_dir: Path, stats_interval: float) -> None:
        self.model = model
        self.results_dir = results_dir
        self.stats_interval = stats_interval
        self.lock = threading.Lock()
        self.stage_id: str | None = None
        self.stats_path: Path | None = None
        self.audit_path: Path | None = None
        self.health_path: Path | None = None
        self.stats_stop: threading.Event | None = None
        self.stats_thread: threading.Thread | None = None

    def audit(self, event: str, **fields: Any) -> None:
        record = {"ts": utc_now(), "event": event, **fields}
        line = json.dumps(record, ensure_ascii=False) + "\n"
        print(line.rstrip(), flush=True)
        if self.audit_path is not None:
            self.audit_path.parent.mkdir(parents=True, exist_ok=True)
            with self.audit_path.open("a", encoding="utf-8") as handle:
                handle.write(line)

    def run(self, command: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
        self.audit("command_start", command=command)
        result = subprocess.run(
            command,
            cwd=REPO,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.audit(
            "command_end",
            command=command,
            returncode=result.returncode,
            stdout=result.stdout[-4000:],
            stderr=result.stderr[-4000:],
        )
        if check and result.returncode:
            raise RuntimeError(
                f"Command failed ({result.returncode}): {' '.join(command)}\n"
                f"{result.stderr.strip()}"
            )
        return result

    def wait_for_ollama(self, timeout_s: int = 180) -> None:
        deadline = time.monotonic() + timeout_s
        while time.monotonic() < deadline:
            result = self.run(
                ["docker", "compose", "exec", "-T", "ollama", "ollama", "list"],
                check=False,
            )
            if result.returncode == 0:
                return
            time.sleep(2)
        raise RuntimeError("Ollama did not become ready within 180 seconds.")

    def wait_for_health(self, timeout_s: int = 180) -> dict[str, Any]:
        deadline = time.monotonic() + timeout_s
        last_error = "no response"
        while time.monotonic() < deadline:
            try:
                health = read_json_url("http://127.0.0.1:8000/health")
                if health.get("status") in (None, "ok") and health.get("model_digest"):
                    return health
                last_error = f"unhealthy response: {health}"
            except RuntimeError as exc:
                last_error = str(exc)
            time.sleep(2)
        raise RuntimeError(f"Triage did not become healthy within 180 seconds: {last_error}")

    def remove_triage_volume(self) -> None:
        result = self.run(
            [
                "docker",
                "volume",
                "ls",
                "--filter",
                "label=com.docker.compose.project=triage",
                "--filter",
                "label=com.docker.compose.volume=triage-data",
                "--format",
                "{{.Name}}",
            ]
        )
        names = [line.strip() for line in result.stdout.splitlines() if line.strip()]
        if len(names) != 1:
            raise RuntimeError(
                "Expected exactly one Compose triage-data volume; found "
                f"{len(names)}: {names}"
            )
        self.run(["docker", "volume", "rm", names[0]])

    def recreate_empty_triage(self) -> None:
        self.run(["docker", "compose", "stop", "triage"])
        self.run(["docker", "compose", "rm", "-f", "triage"])
        self.remove_triage_volume()
        self.run(["docker", "compose", "up", "-d", "triage"])
        self.wait_for_health()

    def warm(self) -> None:
        payload = json.dumps(
            {
                "narrative": (
                    "Synthetic adaptive stress-test warm-up ticket. "
                    "This invented text is excluded from measured results."
                )
            }
        ).encode("utf-8")
        request = urllib.request.Request(
            "http://127.0.0.1:8000/tickets",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=600) as response:
                response.read()
        except (OSError, urllib.error.URLError) as exc:
            raise RuntimeError(f"Warm-up request failed: {exc}") from exc

    def stats_loop(self, path: Path, stop: threading.Event) -> None:
        with path.open("w", encoding="utf-8", buffering=1) as handle:
            handle.write("epoch_s,container,cpu_percent,memory_usage\n")
            while not stop.is_set():
                result = subprocess.run(
                    [
                        "docker",
                        "stats",
                        "--no-stream",
                        "--format",
                        "{{.Name}},{{.CPUPerc}},{{.MemUsage}}",
                    ],
                    cwd=REPO,
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    check=False,
                )
                epoch = f"{time.time():.3f}"
                if result.returncode == 0:
                    for line in result.stdout.splitlines():
                        if line.strip():
                            handle.write(f"{epoch},{line}\n")
                else:
                    self.audit(
                        "stats_sample_failed",
                        returncode=result.returncode,
                        stderr=result.stderr[-1000:],
                    )
                stop.wait(self.stats_interval)

    def start_stats(self, path: Path) -> None:
        stop = threading.Event()
        thread = threading.Thread(
            target=self.stats_loop,
            args=(path, stop),
            name="docker-stats",
            daemon=True,
        )
        self.stats_stop = stop
        self.stats_thread = thread
        thread.start()

    def stop_stats(self) -> None:
        if self.stats_stop is not None:
            self.stats_stop.set()
        if self.stats_thread is not None:
            self.stats_thread.join(timeout=max(15, self.stats_interval + 10))
            if self.stats_thread.is_alive():
                raise RuntimeError("Docker statistics monitor did not stop cleanly.")
        self.stats_stop = None
        self.stats_thread = None

    def prepare(self, payload: dict[str, Any]) -> dict[str, Any]:
        stage_id = str(payload.get("stage_id", ""))
        if not STAGE_RE.fullmatch(stage_id):
            raise RuntimeError(f"Invalid stage_id: {stage_id!r}")
        expected_model = str(payload.get("expected_model", ""))
        expected_digest = str(payload.get("expected_digest", ""))
        if expected_model != self.model:
            raise RuntimeError(
                f"Agent is configured for {self.model!r}, not {expected_model!r}."
            )

        with self.lock:
            if self.stage_id is not None:
                raise RuntimeError(f"Stage {self.stage_id!r} is already active.")
            self.results_dir.mkdir(parents=True, exist_ok=True)
            self.stage_id = stage_id
            self.stats_path = self.results_dir / f"{stage_id}_stats.csv"
            self.audit_path = self.results_dir / f"{stage_id}_sut-audit.jsonl"
            self.health_path = self.results_dir / f"{stage_id}_health.json"
            for path in (self.stats_path, self.audit_path, self.health_path):
                if path.exists():
                    self.stage_id = None
                    self.stats_path = None
                    self.audit_path = None
                    self.health_path = None
                    raise RuntimeError(f"Refusing to overwrite existing evidence: {path}")

            try:
                self.audit("prepare_started", stage_id=stage_id, model=self.model)
                self.run(["docker", "compose", "stop", "triage"])
                self.run(["docker", "compose", "restart", "ollama"])
                self.wait_for_ollama()
                self.run(["docker", "compose", "rm", "-f", "triage"])
                self.remove_triage_volume()
                self.run(["docker", "compose", "up", "-d", "triage"])
                health_before_warm = self.wait_for_health()
                self.warm()
                self.audit("warmup_completed")
                self.recreate_empty_triage()
                health = self.wait_for_health()
                if health.get("model") != expected_model:
                    raise RuntimeError(
                        f"Health reports {health.get('model')!r}; expected {expected_model!r}."
                    )
                if expected_digest and health.get("model_digest") != expected_digest:
                    raise RuntimeError(
                        "Model digest mismatch: expected "
                        f"{expected_digest}, got {health.get('model_digest')}."
                    )
                health_evidence = {
                    "captured_at": utc_now(),
                    "stage_id": stage_id,
                    "before_warm": health_before_warm,
                    "measured_service": health,
                }
                assert self.health_path is not None
                self.health_path.write_text(
                    json.dumps(health_evidence, indent=2) + "\n", encoding="utf-8"
                )
                assert self.stats_path is not None
                self.start_stats(self.stats_path)
                self.audit(
                    "prepare_completed",
                    stage_id=stage_id,
                    model=health.get("model"),
                    model_digest=health.get("model_digest"),
                    stats_file=str(self.stats_path.relative_to(REPO)),
                )
                return {
                    "ok": True,
                    "stage_id": stage_id,
                    "health": health,
                    "prepared_at": utc_now(),
                }
            except Exception:
                try:
                    self.stop_stats()
                finally:
                    self.stage_id = None
                raise

    def collect_service_records(self, request_ids: list[str]) -> tuple[str, list[str]]:
        wanted = set(request_ids)
        matched: dict[str, str] = {}
        for path in sorted((REPO / "logs" / "service").glob("service-*.jsonl")):
            with path.open(encoding="utf-8") as handle:
                for line_number, line in enumerate(handle, start=1):
                    try:
                        record = json.loads(line)
                    except json.JSONDecodeError as exc:
                        raise RuntimeError(f"Invalid JSON in {path}:{line_number}: {exc}") from exc
                    request_id = record.get("request_id")
                    if request_id in wanted:
                        matched[str(request_id)] = json.dumps(record, ensure_ascii=False) + "\n"
        ordered = "".join(matched[rid] for rid in request_ids if rid in matched)
        missing = [rid for rid in request_ids if rid not in matched]
        return ordered, missing

    def finish(self, payload: dict[str, Any]) -> dict[str, Any]:
        stage_id = str(payload.get("stage_id", ""))
        raw_ids = payload.get("request_ids", [])
        if not isinstance(raw_ids, list) or len(raw_ids) > 5000:
            raise RuntimeError("request_ids must be a list containing at most 5000 values.")
        request_ids = [str(value) for value in raw_ids]
        if len(request_ids) != len(set(request_ids)):
            raise RuntimeError("request_ids contains duplicates.")

        with self.lock:
            if self.stage_id != stage_id:
                raise RuntimeError(
                    f"Active stage is {self.stage_id!r}; cannot finish {stage_id!r}."
                )
            try:
                self.stop_stats()
                self.audit("stats_stopped", stage_id=stage_id)
                service_text, missing = self.collect_service_records(request_ids)
                service_path = self.results_dir / f"service-{stage_id}.jsonl"
                service_path.write_text(service_text, encoding="utf-8")
                self.audit(
                    "finish_completed",
                    stage_id=stage_id,
                    requested_records=len(request_ids),
                    matched_records=len(request_ids) - len(missing),
                    missing_records=len(missing),
                    service_file=str(service_path.relative_to(REPO)),
                )
                assert self.stats_path is not None
                assert self.audit_path is not None
                assert self.health_path is not None
                stats_text = self.stats_path.read_text(encoding="utf-8")
                audit_text = self.audit_path.read_text(encoding="utf-8")
                health_text = self.health_path.read_text(encoding="utf-8")
                return {
                    "ok": True,
                    "stage_id": stage_id,
                    "missing_request_ids": missing,
                    "service_jsonl": service_text,
                    "stats_csv": stats_text,
                    "sut_audit_jsonl": audit_text,
                    "health_json": health_text,
                    "sha256": {
                        "service_jsonl": sha256_text(service_text),
                        "stats_csv": sha256_text(stats_text),
                        "sut_audit_jsonl": sha256_text(audit_text),
                        "health_json": sha256_text(health_text),
                    },
                }
            finally:
                self.stage_id = None
                self.stats_path = None
                self.audit_path = None
                self.health_path = None

    def abort(self, payload: dict[str, Any]) -> dict[str, Any]:
        stage_id = str(payload.get("stage_id", ""))
        with self.lock:
            if self.stage_id != stage_id:
                return {"ok": True, "stage_id": stage_id, "was_active": False}
            try:
                self.stop_stats()
                self.audit("stage_aborted", stage_id=stage_id)
                return {"ok": True, "stage_id": stage_id, "was_active": True}
            finally:
                self.stage_id = None
                self.stats_path = None
                self.audit_path = None
                self.health_path = None


class AgentHandler(BaseHTTPRequestHandler):
    controller: SutController
    token: str

    def log_message(self, format: str, *args: Any) -> None:
        sys.stderr.write(f"{self.address_string()} - {format % args}\n")

    def send_json(self, status: int, payload: dict[str, Any]) -> None:
        encoded = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def authorised(self) -> bool:
        return self.headers.get("Authorization") == f"Bearer {self.token}"

    def read_payload(self) -> dict[str, Any]:
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError as exc:
            raise RuntimeError("Invalid Content-Length.") from exc
        if length < 0 or length > 5_000_000:
            raise RuntimeError("Request body is too large.")
        try:
            value = json.loads(self.rfile.read(length) or b"{}")
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"Invalid JSON request: {exc}") from exc
        if not isinstance(value, dict):
            raise RuntimeError("JSON request must be an object.")
        return value

    def do_GET(self) -> None:
        if not self.authorised():
            self.send_json(401, {"ok": False, "error": "unauthorised"})
            return
        if self.path != "/agent/health":
            self.send_json(404, {"ok": False, "error": "not found"})
            return
        self.send_json(
            200,
            {
                "ok": True,
                "model": self.controller.model,
                "active_stage": self.controller.stage_id,
                "repo": str(REPO),
            },
        )

    def do_POST(self) -> None:
        if not self.authorised():
            self.send_json(401, {"ok": False, "error": "unauthorised"})
            return
        try:
            payload = self.read_payload()
            if self.path == "/agent/prepare":
                result = self.controller.prepare(payload)
            elif self.path == "/agent/finish":
                result = self.controller.finish(payload)
            elif self.path == "/agent/abort":
                result = self.controller.abort(payload)
            else:
                self.send_json(404, {"ok": False, "error": "not found"})
                return
        except Exception as exc:
            self.send_json(500, {"ok": False, "error": str(exc)})
            return
        self.send_json(200, result)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bind", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument(
        "--token",
        default=os.environ.get("STRESS_AGENT_TOKEN"),
        help="Shared token, or set STRESS_AGENT_TOKEN",
    )
    parser.add_argument("--stats-interval", type=float, default=5.0)
    parser.add_argument(
        "--results-dir",
        type=Path,
        default=REPO / "results" / "load" / "qwen2.5-7b" / "adaptive-stress",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.token or len(args.token) < 12:
        raise SystemExit("Set --token or STRESS_AGENT_TOKEN to at least 12 characters.")
    if args.stats_interval < 1:
        raise SystemExit("--stats-interval must be at least 1 second.")
    if not (REPO / "docker-compose.yml").is_file():
        raise SystemExit(f"docker-compose.yml not found in {REPO}")

    controller = SutController(
        args.model,
        args.results_dir.expanduser().resolve(),
        args.stats_interval,
    )
    AgentHandler.controller = controller
    AgentHandler.token = args.token
    server = ThreadingHTTPServer((args.bind, args.port), AgentHandler)
    print(f"Adaptive stress SUT agent listening on http://{args.bind}:{args.port}")
    print(f"Model: {args.model}")
    print(f"Evidence directory: {controller.results_dir}")
    print("Leave this terminal open until the load-generator script finishes.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping SUT agent...")
    finally:
        server.server_close()
        if controller.stage_id is not None:
            controller.abort({"stage_id": controller.stage_id})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
