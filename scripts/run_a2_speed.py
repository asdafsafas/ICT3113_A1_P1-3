#!/usr/bin/env python3
"""Assignment 2 speed test, load-generator (JMeter) Mac side.

The SUT Mac must be running `python3 scripts/a2_sut_agent.py agent --bind 0.0.0.0` with the same
A2_AGENT_TOKEN. Every step resets and warms the SUT through that agent and saves all evidence here.

  1. Measure S once, with the service running the top model alone (MODE=single, MODEL=qwen2.5:7b):

         python3 scripts/run_a2_speed.py measure-s --host <SUT-IP>

     Restart + warm-up, then the 3 tickets in a2/speed-workload/s_tickets.tsv one at a time.
     S = the middle of the three times (seconds). Saved to results/a2/s-measure/S.json and used by
     every run:  rate = 60 / (2 x S) per minute,  run length = S minutes (at least 5),
     response timeout = 10 x S seconds (at least 5 minutes),  pause = timeout + 60 s.

  2. Three runs of one configuration (switch the SUT's .env first, then `docker compose up -d triage`):

         python3 scripts/run_a2_speed.py run --host <SUT-IP> --config 7b-alone
         python3 scripts/run_a2_speed.py run --host <SUT-IP> --config cascade-A

  3. Summarise every configuration run so far:

         python3 scripts/run_a2_speed.py summarise

Add --dry-run to `run` to print the JMeter commands without contacting anything.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import shlex
import statistics
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from a2_common import REPO, RESULTS, WORKLOAD_DIR, percentile, read_tsv_tickets, slug

S_DIR = RESULTS / "s-measure"
S_FILE = S_DIR / "S.json"
SPEED_DIR = RESULTS / "speed"
JMX = REPO / "loadtest" / "triage_a2.jmx"
PROPS = REPO / "loadtest" / "triage.properties"
TICKETS = WORKLOAD_DIR / "speed_tickets.tsv"
LOCK = REPO / "models" / "models.lock.json"
TOP_MODEL = "qwen2.5:7b"
RELOAD_MS = 1000.0


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def http_json(url: str, body=None, headers=None, timeout: float = 900):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method="POST" if data is not None else "GET",
                                 headers={"Content-Type": "application/json", **(headers or {})})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        return e.code, {"detail": e.read().decode(errors="replace")[:500]}


def agent(args, path: str, payload=None, timeout: float = 1800) -> dict:
    url = f"http://{args.host}:{args.agent_port}{path}"
    status, body = http_json(url, payload, headers={"Authorization": f"Bearer {args.token}"}, timeout=timeout)
    if status != 200 or not body.get("ok"):
        raise RuntimeError(f"SUT agent {path} failed ({status}): {body.get('error') or body}")
    return body


def pinned_digests() -> dict[str, str]:
    return {m["tag"]: m["digest"] for m in json.loads(LOCK.read_text(encoding="utf-8"))["models"]}


def service_health(args) -> dict:
    status, health = http_json(f"http://{args.host}:{args.port}/health", timeout=20)
    if status != 200 or health.get("status") != "ok":
        raise RuntimeError(f"Service /health is not ok: {health}")
    digests = health.get("model_digests") or {health["model"]: health["model_digest"]}
    pins = pinned_digests()
    for model, digest in digests.items():
        if pins.get(model) != digest:
            raise RuntimeError(f"{model} digest {digest} does not match models.lock.json ({pins.get(model)})")
    health["_digests"] = digests
    return health


def params_from_s(s_seconds: float) -> dict:
    timeout_s = max(math.ceil(10 * s_seconds), 300)
    return {"S_s": round(s_seconds, 3),
            "rate_per_min": round(60 / (2 * s_seconds), 4),
            "interval_s": round(2 * s_seconds, 3),
            "duration_s": max(round(s_seconds * 60), 300),
            "timeout_s": timeout_s,
            "pause_s": timeout_s + 60}


def save_evidence(resp: dict, out_dir: Path, stage: str) -> None:
    names = {"service.jsonl": f"service-{stage}.jsonl"}
    for key, text in resp["files"].items():
        path = out_dir / names.get(key, f"{stage}_{key}")
        if path.exists():
            raise RuntimeError(f"Refusing to overwrite {path}")
        path.write_text(text, encoding="utf-8", newline="\n")


# ---------------------------------------------------------------------------------------------

def measure_s(args) -> int:
    if S_FILE.exists():
        raise SystemExit(f"{S_FILE} already exists. S is measured once; move it aside to re-measure deliberately.")
    health = service_health(args)
    if health.get("model") != TOP_MODEL:
        raise SystemExit(f"S is measured on the top model alone; the service runs {health.get('model')!r}. "
                         f"Set MODE=single and MODEL={TOP_MODEL} in .env, then `docker compose up -d triage`.")
    stage = f"s-measure_{utc_stamp()}"
    out_dir = S_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    print("Restarting and warming the SUT...")
    agent(args, "/agent/prepare", {"stage_id": stage, "config_slug": "s-measure",
                                   "expected_model_label": TOP_MODEL, "expected_digests": health["_digests"]})
    timings, ids = [], []
    try:
        for row, text in read_tsv_tickets(WORKLOAD_DIR / "s_tickets.tsv"):
            rid = f"{stage}-{row}"
            ids.append(rid)
            start = time.perf_counter()
            status, body = http_json(f"http://{args.host}:{args.port}/tickets", {"narrative": text},
                                     headers={"X-Request-ID": rid})
            ms = round((time.perf_counter() - start) * 1000, 1)
            if status != 200:
                raise RuntimeError(f"S ticket {row} failed: {status} {body}")
            timings.append({"row": row, "chars": len(text), "client_ms": ms, "request_id": rid,
                            "category": body.get("category")})
            print(f"  row {row} ({len(text)} chars): {ms / 1000:.2f} s")
    finally:
        resp = agent(args, "/agent/finish", {"stage_id": stage, "request_ids": ids})
        save_evidence(resp, out_dir, stage)
    s = statistics.median(t["client_ms"] for t in timings) / 1000
    result = {"measured_at": stage.split("_", 1)[1], "stage_id": stage, "model": TOP_MODEL,
              "model_digest": health["_digests"][TOP_MODEL], "tickets": timings, **params_from_s(s)}
    S_FILE.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    p = result
    print(f"\nS = {p['S_s']} s  ->  one ticket every {p['interval_s']} s ({p['rate_per_min']}/min), "
          f"run {p['duration_s']} s, timeout {p['timeout_s']} s, pause {p['pause_s']} s")
    print(f"Saved {S_FILE.relative_to(REPO)}. Commit it with the evidence in {out_dir.relative_to(REPO)}.")
    return 0


# ---------------------------------------------------------------------------------------------

def jmeter_command(args, p: dict, jtl: Path, log: Path) -> list[str]:
    return [args.jmeter, "-n", "-t", str(JMX), "-q", str(PROPS),
            f"-Jhost={args.host}", f"-Jport={args.port}", f"-Jrate={p['rate_per_min']}",
            f"-Jduration_s={p['duration_s']}", f"-Jpause_s={p['pause_s']}", f"-Jtimeout_ms={p['timeout_s'] * 1000}",
            f"-Jdata={TICKETS}", "-l", str(jtl), "-j", str(log)]


def read_jtl(path: Path) -> list[dict]:
    import csv
    with path.open(newline="", encoding="utf-8") as f:
        return [r for r in csv.DictReader(f) if r.get("label", "").startswith("POST")]


def run_metrics(rows: list[dict], service_lines: list[dict], stats_before, stats_after) -> dict:
    ok = [r for r in rows if r["success"].lower() == "true"]
    failed = [r for r in rows if r["success"].lower() != "true"]
    http_err = [r for r in failed if r["responseCode"].isdigit()]
    unfinished = [r for r in failed if not r["responseCode"].isdigit()]  # timeouts, connection killed
    elapsed = [int(r["elapsed"]) for r in ok]
    if rows:
        t0 = min(int(r["timeStamp"]) for r in rows)
        t1 = max(int(r["timeStamp"]) + int(r["elapsed"]) for r in rows)
        window_s = max((t1 - t0) / 1000, 1e-9)
    else:
        window_s = None
    posts = [s for s in service_lines if s.get("path") == "/tickets" and s.get("method") == "POST"]
    with_flag = [s for s in posts if "escalated" in s]
    escalated = sum(bool(s.get("escalated")) for s in with_flag)
    reloads = sum(1 for s in posts for c in (s.get("calls") or [s]) if (c.get("ollama_load_ms") or 0) > RELOAD_MS)
    stored = (stats_after or {}).get("total", 0) - (stats_before or {}).get("total", 0) if stats_after else None
    return {"sent": len(rows), "completed": len(ok), "errored": len(http_err), "unfinished": len(unfinished),
            "stored_by_service": stored, "p50_ms": percentile(elapsed, 50), "p95_ms_this_run": percentile(elapsed, 95),
            "elapsed_ms": elapsed, "window_s": round(window_s, 1) if window_s else None,
            "throughput_per_s": round(len(ok) / window_s, 4) if window_s else None,
            "error_rate": round(len(failed) / len(rows), 4) if rows else None,
            "escalated": escalated if with_flag else None, "escalation_base": len(with_flag) or None,
            "escalation_fraction": round(escalated / len(with_flag), 4) if with_flag else None,
            "calls_with_model_reload": reloads, "rows_sent": [int(r["row"]) for r in rows if r.get("row", "").isdigit()]}


def run_config(args) -> int:
    if not S_FILE.exists():
        raise SystemExit(f"{S_FILE} not found. Run `measure-s` first.")
    s = json.loads(S_FILE.read_text(encoding="utf-8"))
    p = {k: s[k] for k in ("S_s", "rate_per_min", "interval_s", "duration_s", "timeout_s", "pause_s")}
    cfg = slug(args.config)
    out_dir = SPEED_DIR / cfg
    print(f"Configuration {cfg}: {p['rate_per_min']}/min for {p['duration_s']} s, timeout {p['timeout_s']} s, "
          f"pause {p['pause_s']} s, {args.runs} runs -> {out_dir.relative_to(REPO)}")
    if args.dry_run:
        for n in range(1, args.runs + 1):
            stage = f"{cfg}_run{n}"
            cmd = jmeter_command(args, p, out_dir / f"{stage}.jtl", out_dir / f"{stage}_jmeter.log")
            print("  " + " ".join(shlex.quote(c) for c in cmd))
        return 0
    if not args.jmeter:
        raise SystemExit("Pass --jmeter /path/to/apache-jmeter-5.6.3/bin/jmeter or set JMETER_BIN.")
    health = service_health(args)
    expected = int(math.ceil(p["rate_per_min"] * p["duration_s"] / 60))
    if expected * 1.6 > len(read_tsv_tickets(TICKETS)):
        raise SystemExit("The speed workload is too short for this rate; rebuild it with more rows.")
    out_dir.mkdir(parents=True, exist_ok=True)
    config_file = out_dir / "config.json"
    if config_file.exists():
        prev = json.loads(config_file.read_text(encoding="utf-8"))
        if prev["health"].get("model") != health.get("model") or prev["health"].get("cascade") != health.get("cascade"):
            raise SystemExit(f"{out_dir} holds runs of a different configuration ({prev['health'].get('model')}).")
    else:
        config_file.write_text(json.dumps({"config": cfg, "health": {k: v for k, v in health.items() if k != '_digests'},
                                           "digests": health["_digests"], "speed_params": p}, indent=2) + "\n",
                               encoding="utf-8")
    print(f"Service runs: {health['model']}")

    for n in range(1, args.runs + 1):
        stage = f"{cfg}_run{n}"
        jtl, jlog = out_dir / f"{stage}.jtl", out_dir / f"{stage}_jmeter.log"
        if jtl.exists():
            print(f"\n{stage}: already done, skipping (move its files away to repeat it).")
            continue
        print(f"\n=== {stage} ===\nRestarting Ollama and warming every model...")
        prep = agent(args, "/agent/prepare", {"stage_id": stage, "config_slug": cfg,
                                              "expected_model_label": health["model"],
                                              "expected_digests": health["_digests"]})
        print(f"Resident: {', '.join(prep['resident_models'])}; /stats total before = {prep['stats_before'].get('total')}")
        rows, failed = [], False
        try:
            cmd = jmeter_command(args, p, jtl, jlog)
            print("Running JMeter (" + f"{(p['duration_s'] + p['pause_s']) / 60:.1f} min incl. pause)...")
            failed = subprocess.run(cmd, cwd=REPO, check=False).returncode != 0
            if jtl.is_file() and jtl.stat().st_size:
                rows = read_jtl(jtl)
        finally:
            resp = agent(args, "/agent/finish", {"stage_id": stage, "request_ids": [r["rid"] for r in rows]})
            save_evidence(resp, out_dir, stage)
        if failed:
            raise SystemExit(f"JMeter exited with an error; evidence for {stage} was kept. See {jlog}.")
        service_lines = [json.loads(line) for line in resp["files"]["service.jsonl"].splitlines() if line.strip()]
        m = run_metrics(rows, service_lines, resp.get("stats_before"), resp.get("stats_after"))
        m.update({"stage_id": stage, "config": cfg, "model_label": health["model"],
                  "missing_service_records": resp.get("missing_request_ids"),
                  "resident_after": resp.get("resident_models_after"), "speed_params": p})
        (out_dir / f"{stage}_run.json").write_text(json.dumps(m, indent=2) + "\n", encoding="utf-8")
        print(f"sent {m['sent']}, completed {m['completed']}, errored {m['errored']}, unfinished {m['unfinished']}, "
              f"stored by service {m['stored_by_service']}; p50 {m['p50_ms'] / 1000 if m['p50_ms'] else 'n/a'} s"
              + (f"; escalated {m['escalated']}/{m['escalation_base']}" if m["escalation_base"] else ""))
        if m["missing_service_records"]:
            print(f"WARNING: {len(m['missing_service_records'])} JMeter samples have no service-log line.")
        if m["calls_with_model_reload"]:
            print(f"WARNING: {m['calls_with_model_reload']} model calls reloaded a model; the models did not all stay resident.")
        subprocess.run([sys.executable, str(REPO / "scripts" / "reconcile.py"), str(jtl), "--logs", str(out_dir)],
                       cwd=REPO, check=False)
    print(f"\nDone. Commit {out_dir.relative_to(REPO)} and run `summarise`.")
    return 0


# ---------------------------------------------------------------------------------------------

def summarise(_args) -> int:
    configs = sorted(d for d in SPEED_DIR.iterdir() if d.is_dir()) if SPEED_DIR.is_dir() else []
    if not configs:
        raise SystemExit("No speed-test runs found.")
    s = json.loads(S_FILE.read_text(encoding="utf-8"))
    s_rows = ", ".join(str(t["row"]) for t in s["tickets"])
    s_times = ", ".join("%.2f s" % (t["client_ms"] / 1000) for t in s["tickets"])
    lines = ["# Assignment 2 speed-test results", "",
             "Generated by `scripts/run_a2_speed.py summarise` from the per-run files in `results/a2/speed/`.", "",
             f"**S = {s['S_s']} s** (median of rows {s_rows}: {s_times}). "
             f"Rate {s['rate_per_min']}/min (one ticket every {s['interval_s']} s), run length {s['duration_s']} s, "
             f"response timeout {s['timeout_s']} s, pause {s['pause_s']} s. Same for every configuration.", "",
             "## Summary per configuration", "",
             "| Configuration | Runs | p50 per run (s) | p50 mean (min–max) | Pooled p95 (n) | Throughput /s (mean) | Errors | Escalation |",
             "|---|---:|---|---|---|---:|---:|---|"]
    detail = ["", "## Every run", "",
              "| Run | Sent | Completed | Errored | Unfinished | Stored by service | p50 s | Throughput /s | Error rate | Escalated | Reloads |",
              "|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|"]
    for d in configs:
        runs = [json.loads(f.read_text(encoding="utf-8")) for f in sorted(d.glob("*_run.json"))]
        if not runs:
            continue
        p50 = [r["p50_ms"] / 1000 for r in runs if r["p50_ms"] is not None]
        pooled = [x for r in runs for x in r["elapsed_ms"]]
        esc = [r for r in runs if r["escalation_base"]]
        esc_txt = (f"{sum(r['escalated'] for r in esc)}/{sum(r['escalation_base'] for r in esc)} = "
                   f"{sum(r['escalated'] for r in esc) / sum(r['escalation_base'] for r in esc):.1%}") if esc else "n/a"
        errors = sum(r["errored"] + r["unfinished"] for r in runs)
        lines.append(f"| {d.name} | {len(runs)} | {', '.join(f'{x:.2f}' for x in p50)} | "
                     f"{statistics.mean(p50):.2f} ({min(p50):.2f}–{max(p50):.2f}) | "
                     f"{percentile(pooled, 95) / 1000:.2f} s (n={len(pooled)}) | "
                     f"{statistics.mean(r['throughput_per_s'] for r in runs):.3f} | {errors} | {esc_txt} |")
        for r in runs:
            detail.append(f"| {r['stage_id']} | {r['sent']} | {r['completed']} | {r['errored']} | {r['unfinished']} | "
                          f"{r['stored_by_service']} | {r['p50_ms'] / 1000 if r['p50_ms'] else 'n/a'} | "
                          f"{r['throughput_per_s']} | {r['error_rate']:.1%} | "
                          f"{(str(r['escalated']) + '/' + str(r['escalation_base'])) if r['escalation_base'] else 'n/a'} | "
                          f"{r['calls_with_model_reload']} |")
    notes = ["", "Notes:",
             "- Latency is JMeter's elapsed time for successful requests. p50 per run; p95 pooled over the three runs "
             "(a single run of ~30 requests is too small for p95). No p99, as the brief asks.",
             "- Throughput = completed requests ÷ seconds from the first request sent to the last response received.",
             "- *Unfinished* = requests with no HTTP response (timeout or cut off). *Stored by service* = increase in "
             "GET /stats total; it should equal *Completed*.",
             "- Escalation fraction comes from the service log (`escalated` field) for the run's requests.",
             "- *Reloads* counts model calls whose Ollama load time exceeded 1 s: any non-zero value means a model "
             "was unloaded during the run, so that run measures loading, not the cascade.", ""]
    text = "\n".join(lines + detail + notes)
    (SPEED_DIR / "SUMMARY.md").write_text(text, encoding="utf-8", newline="\n")
    print(text)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="command", required=True)
    for name in ("measure-s", "run"):
        sp = sub.add_parser(name)
        sp.add_argument("--host", required=True, help="SUT Mac IP address")
        sp.add_argument("--port", type=int, default=8000)
        sp.add_argument("--agent-port", type=int, default=8766)
        sp.add_argument("--token", default=os.environ.get("A2_AGENT_TOKEN"))
        if name == "run":
            sp.add_argument("--config", required=True, help="short name for this configuration, e.g. 7b-alone, cascade-A")
            sp.add_argument("--runs", type=int, default=3)
            sp.add_argument("--jmeter", default=os.environ.get("JMETER_BIN"))
            sp.add_argument("--dry-run", action="store_true")
    sub.add_parser("summarise")
    args = ap.parse_args()
    if args.command == "summarise":
        return summarise(args)
    if not getattr(args, "dry_run", False) and (not args.token or len(args.token) < 12):
        raise SystemExit("Set --token or A2_AGENT_TOKEN (same value as on the SUT Mac, 12+ characters).")
    return measure_s(args) if args.command == "measure-s" else run_config(args)


if __name__ == "__main__":
    raise SystemExit(main())
