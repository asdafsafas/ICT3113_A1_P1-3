#!/usr/bin/env python3
"""Assignment 2, system-under-test (SUT) Mac side. Two commands:

  1. Memory check (Step 2 of the brief): can the cascade's models stay loaded together?

         python3 scripts/a2_sut_agent.py memory-check --models qwen2.5:7b llama3.2:1b-instruct-q4_K_M

     Restarts Ollama, loads each model, then sends invented tickets to each model in turn and
     checks that no call has to reload its model (Ollama's load_duration stays small) and that
     `ollama ps` lists every model. Evidence goes to results/a2/memory-check/<models>/.

  2. Agent for the speed test: the load-generator Mac (scripts/run_a2_speed.py) calls it
     before and after every run.

         export A2_AGENT_TOKEN="<shared token, 12+ characters>"
         python3 scripts/a2_sut_agent.py agent --bind 0.0.0.0

     prepare: restart Ollama (clears its prompt cache; no model loaded) -> wait for /health ->
              check the configuration and digests -> send the 3 fixed warm-up tickets one at a time
              (a2/speed-workload/warmup_tickets.tsv; timings thrown away) -> send one warm-up call
              straight to every model the configuration uses, so a cascade's large model is warm
              too -> check `ollama ps` lists every model -> record GET /stats -> start docker stats.
     finish:  stop docker stats -> `ollama ps` again -> record GET /stats -> copy the service-log
              lines for the run's request IDs -> return all evidence to the load-generator Mac.

The agent binds to localhost unless --bind is given; use it only on a trusted network.
Its own copy of the evidence goes to results/a2/sut-copy/ (git-ignored); the load-generator Mac
commits the authoritative copy.
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
WARMUP = REPO / "a2" / "speed-workload" / "warmup_tickets.tsv"
SMOKE = REPO / "models" / "smoke-tickets.tsv"  # invented tickets, never dataset rows
PROMPT = REPO / "service" / "prompts" / "classify_v1.txt"
SERVICE = "http://127.0.0.1:8000"
OLLAMA = "http://127.0.0.1:11434"
STAGE_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,119}\Z")
CATEGORIES = ["Credit reporting", "Debt collection", "Mortgage", "Credit card", "Bank account or service",
              "Consumer loan", "Money transfer or service"]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def http_json(url: str, body: Any = None, timeout: float = 30, headers: dict | None = None) -> tuple[int, Any]:
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method="POST" if data is not None else "GET",
                                 headers={"Content-Type": "application/json", **(headers or {})})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        return e.code, {"detail": e.read().decode(errors="replace")[:500]}


def read_tickets(path: Path) -> list[tuple[str, str]]:
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            row, enc = line.split("\t", 1)
            out.append((row, json.loads(enc)))
    return out


def dotenv(name: str, default: str) -> str:
    """A setting from the repo's .env (what the service uses), falling back to the default."""
    path = REPO / ".env"
    if path.is_file():
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                if key.strip() == name:
                    return value.strip()
    return default


def generate(model: str, narrative: str, timeout: float = 900) -> dict[str, Any]:
    """One classification call straight to Ollama, same prompt and options as the service."""
    body = {"model": model, "prompt": PROMPT.read_text(encoding="utf-8").replace("{narrative}", narrative),
            "stream": False,
            "format": {"type": "object", "properties": {"category": {"type": "string", "enum": CATEGORIES}},
                       "required": ["category"]},
            "options": {"temperature": float(dotenv("TEMPERATURE", "0")),
                        "seed": int(dotenv("SEED", "42")),
                        "num_ctx": int(dotenv("NUM_CTX", "4096"))}}
    start = time.perf_counter()
    status, data = http_json(f"{OLLAMA}/api/generate", body, timeout=timeout)
    if status != 200:
        raise RuntimeError(f"Ollama /api/generate for {model} returned {status}: {data}")
    return {"model": model, "client_ms": round((time.perf_counter() - start) * 1000, 1),
            "load_ms": round((data.get("load_duration") or 0) / 1e6, 1),
            "total_ms": round((data.get("total_duration") or 0) / 1e6, 1),
            "response": data.get("response")}


class Sut:
    """Docker and evidence helpers shared by both commands."""

    def __init__(self, audit_path: Path | None = None) -> None:
        self.audit_path = audit_path

    def audit(self, event: str, **fields: Any) -> None:
        line = json.dumps({"ts": utc_now(), "event": event, **fields}, ensure_ascii=False)
        print(line, flush=True)
        if self.audit_path is not None:
            self.audit_path.parent.mkdir(parents=True, exist_ok=True)
            with self.audit_path.open("a", encoding="utf-8") as f:
                f.write(line + "\n")

    def run(self, command: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(command, cwd=REPO, text=True, capture_output=True, check=False)
        self.audit("command", command=command, returncode=result.returncode,
                   stdout=result.stdout[-3000:], stderr=result.stderr[-3000:])
        if check and result.returncode:
            raise RuntimeError(f"Command failed ({result.returncode}): {' '.join(command)}\n{result.stderr.strip()}")
        return result

    def ollama_env(self) -> dict[str, str]:
        out = self.run(["docker", "compose", "exec", "-T", "ollama", "env"]).stdout
        return dict(line.split("=", 1) for line in out.splitlines() if line.startswith("OLLAMA_") and "=" in line)

    def restart_ollama(self) -> None:
        self.run(["docker", "compose", "restart", "ollama"])
        deadline = time.monotonic() + 180
        while time.monotonic() < deadline:
            if self.run(["docker", "compose", "exec", "-T", "ollama", "ollama", "list"], check=False).returncode == 0:
                return
            time.sleep(2)
        raise RuntimeError("Ollama did not become ready within 180 s after restart")

    def wait_health(self, timeout_s: int = 180) -> dict[str, Any]:
        deadline, last = time.monotonic() + timeout_s, None
        while time.monotonic() < deadline:
            try:
                status, health = http_json(f"{SERVICE}/health", timeout=10)
                if status == 200 and health.get("status") == "ok":
                    return health
                last = health
            except OSError as e:
                last = str(e)
            time.sleep(2)
        raise RuntimeError(f"Triage /health not ok within {timeout_s} s: {last}")

    def ollama_ps(self) -> tuple[str, list[str]]:
        text = self.run(["docker", "compose", "exec", "-T", "ollama", "ollama", "ps"]).stdout
        status, data = http_json(f"{OLLAMA}/api/ps", timeout=10)
        names = [m.get("name") or m.get("model") for m in (data.get("models", []) if status == 200 else [])]
        return text, names

    def docker_info(self) -> dict[str, Any]:
        out = self.run(["docker", "info", "--format", "{{json .}}"]).stdout
        info = json.loads(out)
        return {k: info.get(k) for k in ("NCPU", "MemTotal", "ServerVersion", "OperatingSystem", "Architecture")}

    def docker_stats_once(self) -> str:
        return self.run(["docker", "stats", "--no-stream", "--format",
                         "{{.Name}},{{.CPUPerc}},{{.MemUsage}}"], check=False).stdout


# ---------------------------------------------------------------------------------------------
# Command 1: memory check
# ---------------------------------------------------------------------------------------------

def memory_check(models: list[str], rounds: int, reload_ms: float) -> int:
    out_dir = REPO / "results" / "a2" / "memory-check" / "+".join(m.replace(":", "-") for m in models)
    if out_dir.exists() and any(out_dir.iterdir()):
        raise SystemExit(f"Evidence already exists in {out_dir}; move it before re-running.")
    sut = Sut(out_dir / "audit.jsonl")
    tickets = [t for _, t in read_tickets(SMOKE)]
    env = sut.ollama_env()
    sut.audit("ollama_env", env=env)
    max_loaded = int(env.get("OLLAMA_MAX_LOADED_MODELS", "1") or 1)
    if max_loaded < len(models):
        raise SystemExit(f"OLLAMA_MAX_LOADED_MODELS={max_loaded} inside the container, but {len(models)} models must "
                         "stay loaded. Set it in .env, run `docker compose up -d ollama`, then re-run.")
    info = sut.docker_info()
    sut.audit("docker_info", **info)
    sut.restart_ollama()

    calls = []
    for i, model in enumerate(models):  # first call per model loads it
        r = generate(model, tickets[i % len(tickets)])
        r.update(phase="load", ticket=i % len(tickets))
        calls.append(r)
        sut.audit("call", **{k: v for k, v in r.items() if k != "response"})
    ps_after_load, _ = sut.ollama_ps()
    for k in range(rounds):  # then alternate: any reload would show as a large load_duration
        for j, model in enumerate(models):
            t = (k * len(models) + j + 1) % len(tickets)
            r = generate(model, tickets[t])
            r.update(phase="alternate", round=k + 1, ticket=t)
            calls.append(r)
            sut.audit("call", **{k2: v for k2, v in r.items() if k2 != "response"})
    ps_text, resident = sut.ollama_ps()
    stats = sut.docker_stats_once()

    reloads = [c for c in calls if c["phase"] == "alternate" and c["load_ms"] > reload_ms]
    missing = [m for m in models if m not in resident]
    passed = not reloads and not missing
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "ollama_ps_after_load.txt").write_text(ps_after_load, encoding="utf-8")
    (out_dir / "ollama_ps_final.txt").write_text(ps_text, encoding="utf-8")
    (out_dir / "docker_stats.txt").write_text(stats, encoding="utf-8")
    result = {"checked_at": utc_now(), "models": models, "passed": passed, "ollama_env": env, "docker": info,
              "resident_at_end": resident, "missing_at_end": missing, "reload_threshold_ms": reload_ms,
              "alternate_calls_with_reload": len(reloads),
              "calls": [{k: v for k, v in c.items() if k != "response"} for c in calls]}
    (out_dir / "memory-check.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")

    lines = [f"# Memory check: {' + '.join(models)}", "",
             f"Checked {result['checked_at']}. Docker VM: {info.get('NCPU')} CPUs, "
             f"{(info.get('MemTotal') or 0) / 2**30:.2f} GiB. OLLAMA_MAX_LOADED_MODELS={max_loaded}.", "",
             f"**Result: {'PASS: every model stayed loaded' if passed else 'FAIL'}**", "",
             "| Phase | Model | Client ms | Ollama load ms | Ollama total ms |", "|---|---|---:|---:|---:|"]
    for c in calls:
        lines.append(f"| {c['phase']}{' ' + str(c.get('round')) if c.get('round') else ''} | `{c['model']}` | "
                     f"{c['client_ms']} | {c['load_ms']} | {c['total_ms']} |")
    lines += ["", f"A load time above {reload_ms:.0f} ms on an alternating call means the model had been unloaded.",
              "", "## `ollama ps` at the end", "", "```", ps_text.rstrip(), "```", "",
              "## `docker stats` at the end", "", "```", stats.rstrip(), "```", ""]
    if missing:
        lines.insert(6, f"Not resident at the end: {', '.join(missing)}.")
    (out_dir / "SUMMARY.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    print(f"Evidence: {out_dir.relative_to(REPO)}")
    return 0 if passed else 1


# ---------------------------------------------------------------------------------------------
# Command 2: speed-test agent
# ---------------------------------------------------------------------------------------------

class Agent:
    def __init__(self, results_dir: Path, stats_interval: float) -> None:
        self.results_dir = results_dir
        self.stats_interval = stats_interval
        self.lock = threading.Lock()
        self.stage: str | None = None
        self.paths: dict[str, Path] = {}
        self.sut: Sut | None = None
        self.stats_before: dict[str, Any] | None = None
        self.stop_event: threading.Event | None = None
        self.stats_thread: threading.Thread | None = None

    def _stats_loop(self, path: Path, stop: threading.Event) -> None:
        with path.open("w", encoding="utf-8", buffering=1) as f:
            f.write("epoch_s,container,cpu_percent,memory_usage\n")
            while not stop.is_set():
                result = subprocess.run(["docker", "stats", "--no-stream", "--format",
                                         "{{.Name}},{{.CPUPerc}},{{.MemUsage}}"],
                                        cwd=REPO, text=True, capture_output=True, check=False)
                epoch = f"{time.time():.3f}"
                for line in result.stdout.splitlines():
                    if line.strip():
                        f.write(f"{epoch},{line}\n")
                stop.wait(self.stats_interval)

    def _stop_stats(self) -> None:
        if self.stop_event is not None:
            self.stop_event.set()
        if self.stats_thread is not None:
            self.stats_thread.join(timeout=self.stats_interval + 30)
        self.stop_event = self.stats_thread = None

    def _reset(self) -> None:
        self.stage, self.paths, self.sut, self.stats_before = None, {}, None, None

    def prepare(self, p: dict[str, Any]) -> dict[str, Any]:
        stage = str(p.get("stage_id", ""))
        if not STAGE_RE.fullmatch(stage):
            raise RuntimeError(f"Invalid stage_id {stage!r}")
        expected_label = str(p.get("expected_model_label", ""))
        expected_digests = p.get("expected_digests") or {}
        with self.lock:
            if self.stage is not None:
                raise RuntimeError(f"Stage {self.stage!r} is already active")
            stage_dir = self.results_dir / str(p.get("config_slug", "misc"))
            self.paths = {k: stage_dir / f"{stage}_{k}" for k in
                          ("stats.csv", "sut-audit.jsonl", "health.json", "ollama_ps_before.txt", "ollama_ps_after.txt")}
            for path in self.paths.values():
                if path.exists():
                    self.paths = {}
                    raise RuntimeError(f"Refusing to overwrite existing evidence: {path}")
            self.stage = stage
            self.sut = sut = Sut(self.paths["sut-audit.jsonl"])
            try:
                sut.audit("prepare_started", stage_id=stage)
                env = sut.ollama_env()
                sut.audit("ollama_env", env=env)
                sut.restart_ollama()
                health = sut.wait_health()
                if expected_label and health.get("model") != expected_label:
                    raise RuntimeError(f"Service runs {health.get('model')!r}, expected {expected_label!r}. "
                                       "Edit .env and run `docker compose up -d triage` first.")
                digests = health.get("model_digests") or {health.get("model"): health.get("model_digest")}
                for model, digest in expected_digests.items():
                    if digests.get(model) != digest:
                        raise RuntimeError(f"Digest of {model} is {digests.get(model)}, expected pinned {digest}")
                models = list(digests)
                if int(env.get("OLLAMA_MAX_LOADED_MODELS", "1") or 1) < len(models):
                    raise RuntimeError(f"OLLAMA_MAX_LOADED_MODELS={env.get('OLLAMA_MAX_LOADED_MODELS')} is below "
                                       f"the {len(models)} models this configuration needs")
                warm = []
                for row, text in read_tickets(WARMUP):  # the 3 fixed warm-up tickets, through the service
                    start = time.perf_counter()
                    status, body = http_json(f"{SERVICE}/tickets", {"narrative": text}, timeout=900,
                                             headers={"X-Request-ID": f"warmup-{stage}-{row}"})
                    warm.append({"row": row, "status": status, "client_ms": round((time.perf_counter() - start) * 1000, 1)})
                    if status != 200:
                        raise RuntimeError(f"Warm-up ticket {row} failed: {status} {body}")
                first = read_tickets(WARMUP)[0][1]
                direct = [{k: v for k, v in generate(m, first).items() if k != "response"} for m in models]
                sut.audit("warmup_completed", service=warm, direct=direct)
                ps_text, resident = sut.ollama_ps()
                self.paths["ollama_ps_before.txt"].parent.mkdir(parents=True, exist_ok=True)
                self.paths["ollama_ps_before.txt"].write_text(ps_text, encoding="utf-8")
                missing = [m for m in models if m not in resident]
                if missing:
                    raise RuntimeError(f"Not resident after warm-up: {missing}. `ollama ps` shows {resident}")
                status, stats = http_json(f"{SERVICE}/stats", timeout=30)
                if status != 200:
                    raise RuntimeError(f"GET /stats failed: {stats}")
                self.stats_before = stats
                self.paths["health.json"].write_text(json.dumps(
                    {"captured_at": utc_now(), "stage_id": stage, "health": health, "ollama_env": env,
                     "docker": sut.docker_info(), "resident_models": resident, "warmup": warm,
                     "direct_warmup": direct, "stats_before": stats}, indent=2) + "\n", encoding="utf-8")
                self.stop_event = threading.Event()
                self.stats_thread = threading.Thread(target=self._stats_loop, daemon=True,
                                                     args=(self.paths["stats.csv"], self.stop_event))
                self.stats_thread.start()
                sut.audit("prepare_completed", stage_id=stage, resident=resident, stats_total_before=stats.get("total"))
                return {"ok": True, "stage_id": stage, "health": health, "resident_models": resident,
                        "stats_before": stats}
            except Exception:
                self._stop_stats()
                self._reset()
                raise

    def finish(self, p: dict[str, Any]) -> dict[str, Any]:
        stage = str(p.get("stage_id", ""))
        ids = [str(x) for x in (p.get("request_ids") or [])]
        with self.lock:
            if self.stage != stage or self.sut is None:
                raise RuntimeError(f"Active stage is {self.stage!r}, cannot finish {stage!r}")
            sut = self.sut
            try:
                self._stop_stats()
                ps_text, resident = sut.ollama_ps()
                self.paths["ollama_ps_after.txt"].write_text(ps_text, encoding="utf-8")
                status, stats_after = http_json(f"{SERVICE}/stats", timeout=30)
                wanted, matched = set(ids), {}
                for path in sorted((REPO / "logs" / "service").glob("service-*.jsonl")):
                    with path.open(encoding="utf-8") as f:
                        for line in f:
                            try:
                                rec = json.loads(line)
                            except json.JSONDecodeError:
                                continue
                            if rec.get("request_id") in wanted:
                                matched[rec["request_id"]] = json.dumps(rec, ensure_ascii=False) + "\n"
                service_text = "".join(matched[i] for i in ids if i in matched)
                missing = [i for i in ids if i not in matched]
                sut.audit("finish_completed", stage_id=stage, requested=len(ids), matched=len(ids) - len(missing),
                          stats_total_before=(self.stats_before or {}).get("total"),
                          stats_total_after=stats_after.get("total") if status == 200 else None,
                          resident_after=resident)
                health = json.loads(self.paths["health.json"].read_text(encoding="utf-8"))
                health["stats_after"] = stats_after if status == 200 else None
                health["resident_models_after"] = resident
                self.paths["health.json"].write_text(json.dumps(health, indent=2) + "\n", encoding="utf-8")
                files = {"service.jsonl": service_text}
                for key, path in self.paths.items():
                    files[key] = path.read_text(encoding="utf-8")
                (self.paths["stats.csv"].parent / f"service-{stage}.jsonl").write_text(service_text, encoding="utf-8")
                return {"ok": True, "stage_id": stage, "missing_request_ids": missing,
                        "stats_before": self.stats_before, "stats_after": stats_after if status == 200 else None,
                        "resident_models_after": resident, "files": files,
                        "sha256": {k: sha256_text(v) for k, v in files.items()}}
            finally:
                self._reset()

    def abort(self, p: dict[str, Any]) -> dict[str, Any]:
        with self.lock:
            was = self.stage is not None and self.stage == str(p.get("stage_id", ""))
            if was:
                self._stop_stats()
                if self.sut:
                    self.sut.audit("stage_aborted", stage_id=self.stage)
                self._reset()
            return {"ok": True, "was_active": was}


def serve(bind: str, port: int, token: str, results_dir: Path, stats_interval: float) -> int:
    agent = Agent(results_dir, stats_interval)

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt: str, *args: Any) -> None:
            sys.stderr.write(f"{self.address_string()} - {fmt % args}\n")

        def reply(self, status: int, payload: dict[str, Any]) -> None:
            data = json.dumps(payload).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def ok_token(self) -> bool:
            return self.headers.get("Authorization") == f"Bearer {token}"

        def do_GET(self) -> None:
            if not self.ok_token():
                return self.reply(401, {"ok": False, "error": "unauthorised"})
            if self.path != "/agent/health":
                return self.reply(404, {"ok": False, "error": "not found"})
            self.reply(200, {"ok": True, "active_stage": agent.stage, "repo": str(REPO)})

        def do_POST(self) -> None:
            if not self.ok_token():
                return self.reply(401, {"ok": False, "error": "unauthorised"})
            try:
                n = int(self.headers.get("Content-Length", "0"))
                payload = json.loads(self.rfile.read(n) or b"{}") if 0 <= n <= 5_000_000 else {}
                action = {"/agent/prepare": agent.prepare, "/agent/finish": agent.finish,
                          "/agent/abort": agent.abort}.get(self.path)
                if action is None:
                    return self.reply(404, {"ok": False, "error": "not found"})
                self.reply(200, action(payload))
            except Exception as e:  # report every failure to the load-generator Mac
                self.reply(500, {"ok": False, "error": str(e)})

    server = ThreadingHTTPServer((bind, port), Handler)
    print(f"A2 SUT agent listening on http://{bind}:{port}  (evidence copy: {results_dir})")
    print("Leave this terminal open until the load-generator Mac has finished.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping.")
    finally:
        server.server_close()
        if agent.stage:
            agent.abort({"stage_id": agent.stage})
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="command", required=True)
    m = sub.add_parser("memory-check", help="check that the cascade's models stay loaded together")
    m.add_argument("--models", nargs="+", required=True)
    m.add_argument("--rounds", type=int, default=3, help="alternating rounds after loading (default 3)")
    m.add_argument("--reload-ms", type=float, default=1000.0, help="load time that counts as a reload")
    a = sub.add_parser("agent", help="serve the speed-test agent for the load-generator Mac")
    a.add_argument("--bind", default="127.0.0.1")
    a.add_argument("--port", type=int, default=8766)
    a.add_argument("--token", default=os.environ.get("A2_AGENT_TOKEN"))
    a.add_argument("--stats-interval", type=float, default=5.0)
    a.add_argument("--results-dir", type=Path, default=REPO / "results" / "a2" / "sut-copy")
    args = ap.parse_args()
    if not (REPO / "docker-compose.yml").is_file():
        raise SystemExit("Run from a clone of the repository (docker-compose.yml not found).")
    if args.command == "memory-check":
        return memory_check(args.models, args.rounds, args.reload_ms)
    if not args.token or len(args.token) < 12:
        raise SystemExit("Set --token or A2_AGENT_TOKEN to at least 12 characters.")
    return serve(args.bind, args.port, args.token, args.results_dir.resolve(), args.stats_interval)


if __name__ == "__main__":
    raise SystemExit(main())
