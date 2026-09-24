"""Accuracy test: send every golden-set ticket through POST /tickets and score the answers.

    python scripts/accuracy_test.py --service http://<service-host>:8000
    python scripts/accuracy_test.py --report results/accuracy/<run>.csv     # re-score an existing run

Uses whichever model the service is currently running (switch it via MODEL in .env).
Tickets are sent one at a time; this measures accuracy, not performance.
Writes results/accuracy/<timestamp>_<model>.csv (one line per ticket, written as it goes)
and a matching .md report with overall and per-category accuracy and a confusion matrix.
A run that stops part-way can be continued with --resume <that csv>.
"""

import argparse
import csv
import json
import time
import urllib.error
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from common import CATEGORIES, REPO, load_narratives, md_table, read_csv

OUT_DIR = REPO / "results" / "accuracy"
FIELDS = ["row", "golden", "predicted", "correct", "status", "latency_ms", "model", "model_digest", "request_id", "error"]
SHORT = {"Credit reporting": "CR", "Debt collection": "DC", "Mortgage": "Mo", "Credit card": "CC",
         "Bank account or service": "BA", "Consumer loan": "CL", "Money transfer or service": "MT"}


def http_json(url, body=None, headers=None, timeout=900):
    req = urllib.request.Request(url, data=json.dumps(body).encode() if body is not None else None,
                                 headers={"Content-Type": "application/json", **(headers or {})})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, {"detail": e.read().decode(errors="replace")[:300]}


def report(csv_path):
    rows = read_csv(csv_path)
    model = next((r["model"] for r in rows if r["model"]), "?")
    n = len(rows)
    correct = sum(r["correct"] == "Y" for r in rows)
    failed = sum(r["status"] != "200" for r in rows)
    per_cat = []
    for c in CATEGORIES:
        support = [r for r in rows if r["golden"] == c]
        hits = sum(r["correct"] == "Y" for r in support)
        per_cat.append([c, len(support), hits, f"{hits / len(support):.1%}" if support else "n/a"])

    pairs = Counter((r["golden"], r["predicted"] or "(error)") for r in rows)
    cols = CATEGORIES + (["(error)"] if failed else [])
    matrix = [[f"**{SHORT[g]}** {g}"] + [pairs.get((g, p), "") or "·" for p in cols] for g in CATEGORIES]
    errors = Counter((r["golden"], r["predicted"]) for r in rows if r["correct"] != "Y" and r["predicted"])

    lat = [float(r["latency_ms"]) for r in rows if r["status"] == "200"]
    lines = [
        f"# Accuracy: {model}", "",
        f"Source: `{Path(csv_path).name}`, digest `{next((r['model_digest'] for r in rows if r['model_digest']), '?')[:19]}`", "",
        f"**Overall accuracy: {correct}/{n} = {correct / n:.1%}**"
        + (f" ({failed} requests failed and count as wrong)" if failed else ""), "",
        f"Mean single-request latency (sequential, successful requests): {sum(lat) / len(lat) / 1000:.2f} s" if lat else "", "",
        "## Per category (recall: share of each golden category classified correctly)", "",
        md_table(["Category", "Golden tickets", "Correct", "Accuracy"], per_cat), "",
        "## Confusion matrix (rows = golden label, columns = predicted)", "",
        md_table(["Golden \\ Predicted"] + [SHORT.get(p, p) for p in cols], matrix), "",
        "## Most common mistakes", "",
        md_table(["Golden", "Predicted", "Count"], [[g, p, k] for (g, p), k in errors.most_common(8)]) if errors else "None.",
        "",
    ]
    out = Path(csv_path).with_suffix(".md")
    out.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    print(f"Wrote {out}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--service", default="http://localhost:8000")
    ap.add_argument("--golden", default=str(REPO / "golden" / "golden_set.csv"))
    ap.add_argument("--source", default=str(REPO / "ict3113_ticket_P1-3.xlsx"), help="where the narratives come from")
    ap.add_argument("--resume", help="continue an interrupted run's CSV")
    ap.add_argument("--report", help="only re-score an existing results CSV")
    args = ap.parse_args()

    if args.report:
        return report(args.report)

    status, health = http_json(args.service.rstrip("/") + "/health", timeout=30)
    if status != 200 or health.get("status") != "ok":
        raise SystemExit(f"Service not ready: {health}")
    model = health["model"]

    golden = read_csv(args.golden)
    narratives = load_narratives(args.source)
    missing = [g["row"] for g in golden if int(g["row"]) not in narratives]
    if missing:
        raise SystemExit(f"No narrative for golden rows {missing[:10]} in {args.source}")

    if args.resume:
        out = Path(args.resume)
        done = {r["row"] for r in read_csv(out)}
    else:
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        out = OUT_DIR / f"{stamp}_{model.replace(':', '-').replace('/', '-')}.csv"
        out.write_text(",".join(FIELDS) + "\n", encoding="utf-8-sig")
        done = set()

    run_id = out.stem
    todo = [g for g in golden if g["row"] not in done]
    print(f"Model {model}: {len(todo)} tickets to send ({len(done)} already done) -> {out}")
    for i, g in enumerate(todo, 1):
        rid = f"acc-{run_id}-{g['row']}"
        start = time.perf_counter()
        status, body = http_json(args.service.rstrip("/") + "/tickets", {"narrative": narratives[int(g["row"])]},
                                 headers={"X-Request-ID": rid})
        predicted = body.get("category", "") if status == 200 else ""
        rec = {"row": g["row"], "golden": g["label"], "predicted": predicted,
               "correct": "Y" if predicted == g["label"] else "N", "status": status,
               "latency_ms": round((time.perf_counter() - start) * 1000, 1), "model": body.get("model", model),
               "model_digest": health.get("model_digest"), "request_id": rid,
               "error": "" if status == 200 else body.get("detail", "")}
        with open(out, "a", newline="", encoding="utf-8") as f:
            csv.DictWriter(f, fieldnames=FIELDS).writerow(rec)
        print(f"  [{i}/{len(todo)}] row {g['row']}: {predicted or 'ERROR ' + str(status)} "
              f"({'ok' if rec['correct'] == 'Y' else 'wrong'}, {rec['latency_ms'] / 1000:.1f}s)", flush=True)
    report(out)


if __name__ == "__main__":
    main()
