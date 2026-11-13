"""Shared helpers for the Assignment 2 scripts. Standard library only."""

import csv
import json
import urllib.error
import urllib.request
from pathlib import Path

from common import CATEGORIES, REPO, percentile, read_csv  # noqa: F401  (re-exported)

A2 = REPO / "a2"
SPLIT_DIR = A2 / "golden-split"
WORKLOAD_DIR = A2 / "speed-workload"
LIMITS_JSON = A2 / "limits.json"
RESULTS = REPO / "results" / "a2"
A1_ACCURACY = REPO / "results" / "accuracy"
TOP_MODEL = "qwen2.5:7b"
A1_RUNS = {  # Assignment 1 accuracy runs (per-ticket CSVs), reusable for single models in A2
    "qwen2.5:0.5b": "20261008T121229Z_qwen2.5-0.5b.csv",
    "llama3.2:1b-instruct-q4_K_M": "20261008T121407Z_llama3.2-1b-instruct-q4_K_M.csv",
    "qwen2.5:7b": "20261008T121609Z_qwen2.5-7b.csv",
}
SHORT = {"Credit reporting": "CR", "Debt collection": "DC", "Mortgage": "Mo", "Credit card": "CC",
         "Bank account or service": "BA", "Consumer loan": "CL", "Money transfer or service": "MT"}


def split_rows(name):
    """{row: label} for 'tuning' or 'test'."""
    path = SPLIT_DIR / f"{name}_set.csv"
    if not path.is_file():
        raise SystemExit(f"{path} not found; run scripts/split_golden.py first")
    return {int(r["row"]): r["label"] for r in read_csv(path)}


def a1_predictions(model):
    """{row: predicted} from the Assignment 1 accuracy run of a model."""
    return {int(r["row"]): r["predicted"] for r in read_csv(A1_ACCURACY / A1_RUNS[model])}


def a1_latency(model):
    return {int(r["row"]): float(r["latency_ms"]) for r in read_csv(A1_ACCURACY / A1_RUNS[model])}


def slug(text):
    return "".join(c if c.isalnum() or c in "._-" else "-" for c in text).strip("-")


def read_tsv_tickets(path):
    """[(row, narrative)] from a JMeter ticket file: row<TAB>JSON-encoded narrative."""
    out = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                row, enc = line.rstrip("\n").split("\t", 1)
                out.append((int(row), json.loads(enc)))
    return out


def write_tsv_tickets(path, tickets):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        for row, text in tickets:
            f.write(f"{row}\t{json.dumps(text, ensure_ascii=False)}\n")


def score(golden, predicted):
    """Overall and per-category accuracy. golden/predicted: {row: label}. Missing predictions count as wrong."""
    rows = sorted(golden)
    right = sum(predicted.get(r) == golden[r] for r in rows)
    per = {}
    for c in CATEGORIES:
        rs = [r for r in rows if golden[r] == c]
        k = sum(predicted.get(r) == c for r in rs)
        per[c] = {"n": len(rs), "right": k, "acc": k / len(rs) if rs else None}
    return {"n": len(rows), "right": right, "acc": right / len(rows) if rows else None, "per_category": per}


def fmt_pct(x):
    return "n/a" if x is None else f"{x * 100:.1f}%"


def http_json(url, body=None, headers=None, timeout=900, method=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method or ("POST" if data else "GET"),
                                 headers={"Content-Type": "application/json", **(headers or {})})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        return e.code, {"detail": e.read().decode(errors="replace")[:500]}


def write_csv(path, rows, fields):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
