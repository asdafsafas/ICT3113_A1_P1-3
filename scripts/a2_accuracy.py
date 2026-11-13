"""Assignment 2 accuracy test: every ticket of the test (or tuning) set through POST /tickets.

Run it ON THE SUT MAC (it reads the service log in logs/service/ to see which tickets escalated):

    python3 scripts/a2_accuracy.py --config cascade-A                 # test set (what is reported)
    python3 scripts/a2_accuracy.py --config cascade-A --split tuning  # tuning set (design only)
    python3 scripts/a2_accuracy.py --report results/a2/accuracy/<run>.csv   # re-score a finished run

Uses whatever configuration the service is running (.env). Tickets are sent one at a time; this
measures accuracy, not speed. Writes results/a2/accuracy/<timestamp>_<config>_<split>.csv and .md:
overall accuracy (count and %), per-category accuracy against the A2 limits (a2/limits.json),
a confusion matrix and, for a cascade, how many tickets escalated and the accuracy of escalated
and non-escalated tickets separately. A stopped run continues with --resume <csv>.
"""

import argparse
import csv
import json
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from a2_common import (CATEGORIES, LIMITS_JSON, REPO, RESULTS, SHORT, fmt_pct, http_json, read_csv, score, slug,
                       split_rows)
from common import load_narratives, md_table

OUT = RESULTS / "accuracy"
LOG_DIR = REPO / "logs" / "service"  # --logs overrides
FIELDS = ["row", "golden", "predicted", "correct", "status", "latency_ms", "model_label", "final_model",
          "escalated", "small_category", "request_id", "error"]


def service_records(ids):
    wanted, found = set(ids), {}
    for path in sorted(Path(LOG_DIR).glob("service-*.jsonl")):
        with open(path, encoding="utf-8") as f:
            for line in f:
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if rec.get("request_id") in wanted:
                    found[rec["request_id"]] = rec
    return found


def report(csv_path):
    rows = read_csv(csv_path)
    meta_path = Path(csv_path).with_suffix(".json")
    meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {}
    split = meta.get("split", "test")
    # Fill escalation fields from the service log if this machine has it (the SUT Mac does).
    recs = service_records([r["request_id"] for r in rows])
    for r in rows:
        rec = recs.get(r["request_id"])
        if rec:
            r["final_model"] = rec.get("final_model") or rec.get("model", "")
            r["escalated"] = "" if "escalated" not in rec else ("Y" if rec["escalated"] else "N")
            r["small_category"] = rec.get("small_category", "")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)

    golden = {int(r["row"]): r["golden"] for r in rows}
    pred = {int(r["row"]): r["predicted"] for r in rows if r["predicted"]}
    s = score(golden, pred)
    limits = json.loads(LIMITS_JSON.read_text(encoding="utf-8")) if LIMITS_JSON.exists() else None
    label = next((r["model_label"] for r in rows if r["model_label"]), "?")
    failed = sum(r["status"] != "200" for r in rows)

    lines = [f"# A2 accuracy: `{label}` on the {split} set", "",
             f"Source: `{Path(csv_path).name}`. {len(rows)} tickets sent one at a time through POST /tickets.", "",
             f"**Overall: {s['right']}/{s['n']} = {fmt_pct(s['acc'])}**" + (f" ({failed} requests failed, counted wrong)" if failed else "")]
    if limits and split == "test":
        ok = s["acc"] >= limits["overall_limit"] - 1e-9
        lines[-1] += f" against the overall limit {fmt_pct(limits['overall_limit'])}: **{'PASS' if ok else 'FAIL'}**"
    elif split != "test":
        lines[-1] += " (tuning set: for designing the rule only; not used to decide pass or fail)"
    lines += ["", "## Per category", ""]
    table = []
    cat_fail = []
    for c in CATEGORIES:
        p = s["per_category"][c]
        row = [c, p["n"], p["right"], p["n"] - p["right"], fmt_pct(p["acc"])]
        if limits and split == "test":
            lim = limits["per_category"][c]
            ok = p["acc"] is not None and p["acc"] >= lim["limit"] - 1e-9
            if not ok:
                cat_fail.append(c)
            row += [fmt_pct(lim["limit"]), ("PASS" if ok else "FAIL") + (" (small: 1 ticket = %.1f pts)" % (100 / p["n"]) if lim["too_small"] else "")]
        table.append(row)
    hdr = ["Category", "n", "Right", "Wrong", "Accuracy"] + (["Limit", "Result"] if limits and split == "test" else [])
    lines += [md_table(hdr, table), ""]
    if limits and split == "test":
        both = s["acc"] >= limits["overall_limit"] - 1e-9 and not cat_fail
        lines += [f"**Passes both limits: {'YES' if both else 'NO'}**" + (f" (below the category limit: {', '.join(cat_fail)})" if cat_fail else ""), ""]

    esc_rows = [r for r in rows if r.get("escalated") in ("Y", "N")]
    if esc_rows:
        e = [r for r in esc_rows if r["escalated"] == "Y"]
        a = [r for r in esc_rows if r["escalated"] == "N"]

        def acc(rs):
            k = sum(r["correct"] == "Y" for r in rs)
            return f"{k}/{len(rs)} = {fmt_pct(k / len(rs) if rs else None)}"

        lines += ["## Escalation", "",
                  f"- Escalated: **{len(e)}/{len(esc_rows)} = {fmt_pct(len(e) / len(esc_rows))}** (from the service log `escalated` field)",
                  f"- Accuracy of escalated tickets (answered by the large model): {acc(e)}",
                  f"- Accuracy of accepted tickets (answered by the small model): {acc(a)}",
                  "", "Accepted tickets by the small model's answer (is the rule letting wrong answers through?):", "",
                  md_table(["Small model answered", "Accepted", "Right", "Wrong"],
                           [[c, len(g), sum(r['correct'] == 'Y' for r in g), sum(r['correct'] != 'Y' for r in g)]
                            for c in CATEGORIES for g in [[r for r in a if r['predicted'] == c]] if g]) if a else "None accepted.",
                  ""]
    pairs = Counter((r["golden"], r["predicted"] or "(error)") for r in rows)
    cols = CATEGORIES + (["(error)"] if failed else [])
    lines += ["## Confusion matrix (rows = golden, columns = predicted)", "",
              md_table(["Golden \\ Predicted"] + [SHORT.get(c, c) for c in cols],
                       [[f"**{SHORT[g]}** {g}"] + [pairs.get((g, p), "") or "·" for p in cols] for g in CATEGORIES]), ""]
    out = Path(csv_path).with_suffix(".md")
    out.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    print(f"Wrote {out}")


def main():
    global LOG_DIR
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--service", default="http://127.0.0.1:8000")
    ap.add_argument("--config", help="short name for the configuration, e.g. cascade-A")
    ap.add_argument("--split", choices=["test", "tuning"], default="test")
    ap.add_argument("--source", default=str(REPO / "ict3113_ticket_P1-3.xlsx"))
    ap.add_argument("--resume")
    ap.add_argument("--report")
    ap.add_argument("--logs", default=str(LOG_DIR), help="service log folder (default logs/service)")
    args = ap.parse_args()
    LOG_DIR = args.logs
    if args.report:
        return report(args.report)
    if not args.config and not args.resume:
        raise SystemExit("--config is required")

    status, health = http_json(args.service.rstrip("/") + "/health", timeout=30)
    if status != 200 or health.get("status") != "ok":
        raise SystemExit(f"Service not ready: {health}")
    golden = split_rows(args.split)
    narratives = load_narratives(args.source)
    missing = [r for r in golden if r not in narratives]
    if missing:
        raise SystemExit(f"No narrative for rows {missing[:10]} in {args.source}")

    if args.resume:
        out = Path(args.resume)
        done = {int(r["row"]) for r in read_csv(out)}
        meta = json.loads(out.with_suffix(".json").read_text(encoding="utf-8"))
        if meta["health"].get("model") != health.get("model"):
            raise SystemExit(f"Service now runs {health.get('model')}, but the run was {meta['health'].get('model')}")
    else:
        OUT.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        out = OUT / f"{stamp}_{slug(args.config)}_{args.split}.csv"
        out.write_text(",".join(FIELDS) + "\n", encoding="utf-8")
        out.with_suffix(".json").write_text(json.dumps({"config": args.config, "split": args.split, "health": health},
                                                       indent=2) + "\n", encoding="utf-8")
        done = set()

    todo = [r for r in sorted(golden) if r not in done]
    print(f"{health['model']}: {len(todo)} {args.split}-set tickets to send -> {out}")
    for i, row in enumerate(todo, 1):
        rid = f"a2acc-{out.stem}-{row}"
        start = time.perf_counter()
        status, body = http_json(args.service.rstrip("/") + "/tickets", {"narrative": narratives[row]},
                                 headers={"X-Request-ID": rid})
        predicted = body.get("category", "") if status == 200 else ""
        rec = {"row": row, "golden": golden[row], "predicted": predicted,
               "correct": "Y" if predicted == golden[row] else "N", "status": status,
               "latency_ms": round((time.perf_counter() - start) * 1000, 1), "model_label": body.get("model", health["model"]),
               "request_id": rid, "error": "" if status == 200 else body.get("detail", "")}
        with open(out, "a", newline="", encoding="utf-8") as f:
            csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore").writerow(rec)
        print(f"  [{i}/{len(todo)}] row {row}: {predicted or 'ERROR ' + str(status)} "
              f"({'ok' if rec['correct'] == 'Y' else 'wrong'}, {rec['latency_ms'] / 1000:.1f}s)", flush=True)
    report(out)


if __name__ == "__main__":
    main()
