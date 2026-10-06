"""Smoke-test every pinned model on the real system under test, and keep the evidence.

    python3 scripts/smoke_sut.py                  # all models in models/models.lock.json
    python3 scripts/smoke_sut.py --models qwen2.5:3b

Run on the system-under-test machine, from the repo root, with the stack up
(`docker compose up -d`) and the models pulled (`python3 scripts/pull_models.py`).

Uses ONLY the invented tickets in models/smoke-tickets.tsv (6 lengths, about 180-2,000
characters). No row from 3000-3999 is ever sent to a model.

For each model it:
  1. switches MODEL in .env and recreates the triage container,
  2. checks /health reports the model with the digest pinned in models.lock.json,
  3. sends one warm-up ticket, then the six smoke tickets one at a time,
  4. samples `docker stats` (CPU %, memory) about once a second while the tickets run,
  5. writes evidence to evidence/smoke/<model>/ and a summary to evidence/smoke/SUMMARY.md.

The summary fits latency = a + b x characters per model, so single-request latency at the
golden set's p50 and p95 ticket lengths is measured on THIS service and prompt rather than
extrapolated from elsewhere. Commit evidence/smoke/ before the prediction-record freeze.

Afterwards .env is restored, and the smoke tickets remain in the database: reset the
data volume before official runs, as the JMeter playbook already says.
"""

import argparse
import json
import re
import subprocess
import sys
import threading
import time
import urllib.request
from datetime import datetime, timezone

from common import REPO, load_narratives, percentile

LOCK = REPO / "models" / "models.lock.json"
TICKETS = REPO / "models" / "smoke-tickets.tsv"
ENV = REPO / ".env"
OUT = REPO / "evidence" / "smoke"
LOG_DIR = REPO / "logs" / "service"
GOLDEN_XLSX = REPO / "ict3113_ticket_P1-3.xlsx"
# Warm-up text is deliberately different from every smoke ticket, so no measured
# request can reuse a prompt Ollama has cached from the warm-up.
WARMUP = ("I am writing because my savings account statement shows an interest payment that is lower than "
          "the rate advertised when I opened the account, and the branch could not explain the difference.")


def sh(*cmd, check=True):
    r = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True)
    if check and r.returncode != 0:
        raise SystemExit(f"{' '.join(cmd)} failed:\n{r.stderr or r.stdout}")
    return r.stdout.strip()


def http(base, path, body=None, headers=None, timeout=900):
    req = urllib.request.Request(base + path, data=json.dumps(body).encode() if body is not None else None,
                                 headers={"Content-Type": "application/json", **(headers or {})})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def slug(tag):
    return tag.replace(":", "-").replace("/", "-")


def set_env_model(tag):
    text = ENV.read_text(encoding="utf-8")
    new, n = re.subn(r"(?m)^MODEL=.*$", f"MODEL={tag}", text)
    if n != 1:
        raise SystemExit(".env must contain exactly one MODEL= line")
    ENV.write_text(new, encoding="utf-8")


def container_ids():
    return {svc: sh("docker", "compose", "ps", "-q", svc) for svc in ("ollama", "triage")}


class StatsSampler(threading.Thread):
    """Calls `docker stats --no-stream` in a loop (each call takes ~1-2 s)."""

    def __init__(self, ids, path):
        super().__init__(daemon=True)
        self.ids, self.path, self.stop = ids, path, threading.Event()
        self.rows = []

    def run(self):
        names = {v: k for k, v in self.ids.items()}
        with open(self.path, "w", encoding="utf-8") as f:
            while not self.stop.is_set():
                out = sh("docker", "stats", "--no-stream", "--format", "{{json .}}", *self.ids.values(), check=False)
                ts = time.time()
                for line in out.splitlines():
                    try:
                        s = json.loads(line)
                    except ValueError:
                        continue
                    sid = s.get("ID", "")
                    svc = next((n for cid, n in names.items() if sid and cid.startswith(sid)), s.get("Name"))
                    row = {"ts": ts, "service": svc, "cpu_pct": float(s["CPUPerc"].rstrip("%") or 0),
                           "mem": s.get("MemUsage"), "mem_pct": float(s.get("MemPerc", "0%").rstrip("%") or 0)}
                    self.rows.append(row)
                    f.write(json.dumps(row) + "\n")
                    f.flush()


def fit(xs, ys):
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    b = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sxx
    a = my - b * mx
    ss_tot = sum((y - my) ** 2 for y in ys)
    r2 = 1 - sum((y - (a + b * x)) ** 2 for x, y in zip(xs, ys)) / ss_tot if ss_tot else 1.0
    return a, b, r2


def log_lines(request_ids):
    found = {}
    for p in sorted(LOG_DIR.glob("service-*.jsonl")):
        for line in p.read_text(encoding="utf-8").splitlines():
            try:
                rec = json.loads(line)
            except ValueError:
                continue
            if rec.get("request_id") in request_ids:
                found[rec["request_id"]] = rec
    return found


def run_model(m, tickets, base, run_tag):
    tag, digest = m["tag"], m["digest"]
    d = OUT / slug(tag)
    d.mkdir(parents=True, exist_ok=True)
    print(f"\n== {tag}", flush=True)

    set_env_model(tag)
    sh("docker", "compose", "up", "-d", "--force-recreate", "triage")
    for _ in range(120):
        try:
            h = http(base, "/health", timeout=5)
            if h.get("model") == tag and h.get("model_digest"):
                break
        except Exception:
            pass
        time.sleep(1)
    else:
        raise SystemExit(f"{tag}: service did not come up on this model")
    if h["model_digest"] != digest:
        raise SystemExit(f"{tag}: DIGEST MISMATCH live {h['model_digest']} vs lock {digest}")
    (d / "health.json").write_text(json.dumps(h, indent=2) + "\n", encoding="utf-8")
    print(f"   verified digest {digest[:12]}", flush=True)

    rid = lambda name: f"{run_tag}-{slug(tag)}-{name}"
    http(base, "/tickets", {"narrative": WARMUP}, {"X-Request-ID": rid("warmup")})
    (d / "ollama_ps.txt").write_text(sh("docker", "compose", "exec", "-T", "ollama", "ollama", "ps") + "\n", encoding="utf-8")

    ids = container_ids()
    sampler = StatsSampler(ids, d / "docker_stats.jsonl")
    sampler.start()
    time.sleep(2.5)  # one idle sample first
    windows = []
    for name, text in tickets:
        t0 = time.time()
        res = http(base, "/tickets", {"narrative": text}, {"X-Request-ID": rid(name)})
        windows.append((t0, time.time()))
        print(f"   {name}: {len(text):>5} chars -> {res['category']}", flush=True)
    sampler.stop.set()
    sampler.join(timeout=10)

    time.sleep(1)
    wanted = [rid("warmup")] + [rid(n) for n, _ in tickets]
    recs = log_lines(set(wanted))
    missing = [r for r in wanted if r not in recs]
    if missing:
        raise SystemExit(f"{tag}: request IDs missing from logs/service: {missing}")
    with open(d / "service.jsonl", "w", encoding="utf-8") as f:
        for r in wanted:
            f.write(json.dumps(recs[r], ensure_ascii=False) + "\n")

    busy = [s for s in sampler.rows if any(a <= s["ts"] <= b + 1 for a, b in windows)]
    def peak(svc, key):
        vals = [s[key] for s in busy if s["service"] == svc]
        return max(vals) if vals else None
    def med(svc, key):
        vals = sorted(s[key] for s in busy if s["service"] == svc)
        return vals[len(vals) // 2] if vals else None
    mem = [s["mem"] for s in busy if s["service"] == "ollama"]
    return {
        "tag": tag, "digest": digest,
        "requests": [recs[rid(n)] for n, _ in tickets],
        "ollama_cpu_peak": peak("ollama", "cpu_pct"), "ollama_cpu_median": med("ollama", "cpu_pct"),
        "triage_cpu_peak": peak("triage", "cpu_pct"), "ollama_mem_last": mem[-1] if mem else None,
        "stats_samples": len(busy),
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base", default="http://localhost:8000")
    ap.add_argument("--models", nargs="*", help="subset of tags (default: every model in the lock file)")
    args = ap.parse_args()

    if not LOCK.exists():
        raise SystemExit("models/models.lock.json not found: run `python3 scripts/pull_models.py` first")
    lock = json.loads(LOCK.read_text(encoding="utf-8"))
    models = [m for m in lock["models"] if not args.models or m["tag"] in args.models]
    tickets = [(r, json.loads(t)) for r, t in (l.split("\t", 1) for l in TICKETS.read_text(encoding="utf-8").splitlines() if l.strip())]
    if not ENV.exists():
        raise SystemExit(".env not found: cp .env.example .env")

    # Restart Ollama so its prompt cache is empty: earlier runs sent these same tickets,
    # and a cached prompt makes prompt evaluation look almost free.
    print("Restarting Ollama to clear its prompt cache ...", flush=True)
    sh("docker", "compose", "restart", "ollama")
    for _ in range(60):
        if sh("docker", "compose", "exec", "-T", "ollama", "ollama", "list", check=False):
            break
        time.sleep(1)
    nproc = sh("docker", "compose", "exec", "-T", "ollama", "sh", "-c", "env | grep ^OLLAMA_ | sort")
    if "OLLAMA_NUM_PARALLEL=1" not in nproc.splitlines():
        print("WARNING: OLLAMA_NUM_PARALLEL=1 not set inside the ollama container:\n" + nproc)

    run_tag = "smoke-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    original_env = ENV.read_text(encoding="utf-8")
    OUT.mkdir(parents=True, exist_ok=True)
    results = []
    try:
        for m in models:
            results.append(run_model(m, tickets, args.base, run_tag))
    finally:
        ENV.write_text(original_env, encoding="utf-8")
        sh("docker", "compose", "up", "-d", "--force-recreate", "triage", check=False)

    golden = [len(t) for r, t in load_narratives(GOLDEN_XLSX).items() if 3000 <= r <= 3199]
    g50, g95 = percentile(golden, 50), percentile(golden, 95)

    lines = [
        "# Smoke tests on the system under test",
        "",
        f"Generated by `scripts/smoke_sut.py` at {datetime.now(timezone.utc).isoformat(timespec='seconds')} (run tag `{run_tag}`).",
        "Service: this repo's `service/`, prompt `" + json.loads((OUT / slug(models[0]['tag']) / 'health.json').read_text()).get('prompt_file', 'see health.json')
        + "`, settings from `.env`. Git revision: `" + sh("git", "rev-parse", "--short", "HEAD", check=False) + "`.",
        f"Ollama {lock.get('ollama_version')}; container environment:",
        "", "```", nproc, "```", "",
        f"Tickets: 6 **invented** narratives in `models/smoke-tickets.tsv` ({min(len(t) for _, t in tickets)}-{max(len(t) for _, t in tickets)} characters), "
        "sent one at a time after one warm-up request with a different invented text. Ollama was restarted first, so no prompt was served from its cache. No dataset row was sent to any model.",
        "Raw evidence per model: `service.jsonl` (service log lines, matched by X-Request-ID), `docker_stats.jsonl`, `health.json`, `ollama_ps.txt`.",
        "",
        "## Per-request timings",
        "",
        "| Model | Ticket | Chars | Prompt tokens | POST latency ms | Ollama total ms | Prompt eval ms | Generation ms |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for res in results:
        for r, (name, text) in zip(res["requests"], tickets):
            lines.append(f"| `{res['tag']}` | {name} | {r.get('narrative_chars')} | {r.get('prompt_tokens')} | {r.get('latency_ms')} | "
                         f"{r.get('ollama_total_ms')} | {r.get('ollama_prompt_eval_ms')} | {r.get('ollama_eval_ms')} |")
    lines += [
        "",
        "## Fitted single-request latency (POST /tickets, one request in flight)",
        "",
        f"Linear fit `latency_ms = a + b x chars` over the 6 tickets, evaluated at the golden pool's p50 ({g50} chars) and p95 ({g95} chars) "
        "ticket lengths (rows 3000-3199, lengths only).",
        "",
        "| Model | a (ms) | b (ms/char) | R² | ms per prompt token | at golden p50 | at golden p95 | Ollama CPU % median / peak | Triage CPU % peak | Ollama memory |",
        "|---|---:|---:|---:|---:|---:|---:|---|---:|---|",
    ]
    summary = {"run_tag": run_tag, "golden_p50_chars": g50, "golden_p95_chars": g95, "models": []}
    for res in results:
        xs = [r["narrative_chars"] for r in res["requests"]]
        ys = [r["latency_ms"] for r in res["requests"]]
        a, b, r2 = fit(xs, ys)
        pa, pb, _ = fit([r["prompt_tokens"] for r in res["requests"]], [r["ollama_prompt_eval_ms"] for r in res["requests"]])
        p50, p95 = a + b * g50, a + b * g95
        summary["models"].append({"tag": res["tag"], "digest": res["digest"], "a_ms": a, "b_ms_per_char": b, "r2": r2,
                                  "ms_per_prompt_token": pb, "pred_ms_golden_p50": p50, "pred_ms_golden_p95": p95,
                                  "ollama_cpu_median": res["ollama_cpu_median"], "ollama_cpu_peak": res["ollama_cpu_peak"],
                                  "triage_cpu_peak": res["triage_cpu_peak"], "ollama_mem": res["ollama_mem_last"]})
        fmt = lambda v: "n/a" if v is None else f"{v:.0f}"
        lines.append(f"| `{res['tag']}` | {a:.0f} | {b:.2f} | {r2:.3f} | {pb:.2f} | {p50 / 1000:.2f} s | {p95 / 1000:.2f} s | "
                     f"{fmt(res['ollama_cpu_median'])} / {fmt(res['ollama_cpu_peak'])} | {fmt(res['triage_cpu_peak'])} | {res['ollama_mem_last']} |")
    lines += [
        "",
        "`docker stats` CPU % is relative to one CPU, so 1000% = all 10 CPUs of the Docker VM. "
        "Samples are taken about once a second, so short requests may get few or no samples.",
        "",
    ]
    (OUT / "SUMMARY.md").write_text("\n".join(lines), encoding="utf-8")
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print("\n" + "\n".join(lines[lines.index("## Fitted single-request latency (POST /tickets, one request in flight)"):]))
    print(f"Wrote {OUT.relative_to(REPO)}/. Commit it before freezing the prediction record.")


if __name__ == "__main__":
    main()
