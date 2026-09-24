"""Summarise JMeter result files: p50/p95/p99, throughput and error rate, with the spread across runs.

    python scripts/summarise_jtl.py results/load                  # every .jtl under the folder
    python scripts/summarise_jtl.py results/load --skip-s 60      # ignore the first 60 s of each run (warm-up)

Naming convention (see docs/load-testing.md): results/load/<model>/<rate>rpm_run<N>.jtl
Runs of the same configuration (same folder, same name apart from _runN) are grouped;
the table shows the mean across runs and the min-max range.
Latency percentiles are over successful samples; failures count only towards the error rate.
"""

import argparse
import re
import statistics
from collections import defaultdict
from pathlib import Path

from common import REPO, md_table, percentile, read_csv, write_csv

RUN_RE = re.compile(r"(?P<config>.+)_run(?P<run>\d+)$")


def summarise_run(path, label, skip_s):
    rows = [r for r in read_csv(path) if r["label"] == label]
    if not rows:
        return None
    t0 = min(int(r["timeStamp"]) for r in rows)
    rows = [r for r in rows if int(r["timeStamp"]) >= t0 + skip_s * 1000]
    if not rows:
        return None
    ok = [r for r in rows if r["success"] == "true"]
    starts = [int(r["timeStamp"]) for r in rows]
    ends = [int(r["timeStamp"]) + int(r["elapsed"]) for r in rows]
    window_min = max(1, max(ends) - min(starts)) / 60000
    start_window_min = max(1, max(starts) - min(starts)) / 60000
    elapsed = [int(r["elapsed"]) / 1000 for r in ok]
    return {
        "samples": len(rows),
        "offered_rpm": (len(rows) - 1) / start_window_min if len(rows) > 1 else None,
        "throughput_rpm": len(ok) / window_min,
        "error_rate": 1 - len(ok) / len(rows),
        "p50": percentile(elapsed, 50),
        "p95": percentile(elapsed, 95),
        "p99": percentile(elapsed, 99),
        "max_threads": max(int(r.get("allThreads") or 0) for r in rows),
    }


def fmt(values, spec):
    values = [v for v in values if v is not None]
    if not values:
        return "n/a"
    mean = statistics.mean(values)
    if len(values) == 1:
        return format(mean, spec)
    return f"{format(mean, spec)} ({format(min(values), spec)}-{format(max(values), spec)})"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("paths", nargs="+", help=".jtl files or folders")
    ap.add_argument("--label", default="POST /tickets", help="sampler label to summarise")
    ap.add_argument("--skip-s", type=int, default=0, help="exclude samples started in the first N seconds")
    ap.add_argument("--csv", help="also write per-run numbers to this CSV")
    args = ap.parse_args()

    files = []
    for p in map(Path, args.paths):
        files += sorted(p.rglob("*.jtl")) if p.is_dir() else [p]

    groups, per_run = defaultdict(list), []
    for f in files:
        s = summarise_run(f, args.label, args.skip_s)
        if s is None:
            print(f"(skipped {f}: no '{args.label}' samples)")
            continue
        m = RUN_RE.match(f.stem)
        config = f"{f.parent.name}/{m.group('config') if m else f.stem}"
        groups[config].append(s)
        per_run.append({"file": f.as_posix(), "config": config, **{k: round(v, 4) if isinstance(v, float) else v
                                                                    for k, v in s.items()}})

    table = []
    for config, runs in sorted(groups.items()):
        table.append([config, len(runs), fmt([r["samples"] for r in runs], ".0f"),
                      fmt([r["offered_rpm"] for r in runs], ".2f"), fmt([r["throughput_rpm"] for r in runs], ".2f"),
                      fmt([r["p50"] for r in runs], ".2f"), fmt([r["p95"] for r in runs], ".2f"),
                      fmt([r["p99"] for r in runs], ".2f"), fmt([100 * r["error_rate"] for r in runs], ".1f")])
    print(f"Label: {args.label}" + (f", first {args.skip_s}s excluded" if args.skip_s else "") +
          ". Values are mean (min-max) across runs.\n")
    print(md_table(["Configuration", "Runs", "Samples", "Offered /min", "Throughput /min", "p50 s", "p95 s",
                    "p99 s", "Errors %"], table))
    if any(len(r) < 3 for r in groups.values()):
        print("\nNote: the brief requires three runs per configuration; some have fewer.")
    if args.csv:
        write_csv(args.csv, per_run, list(per_run[0].keys()))
        print(f"\nWrote {args.csv}")


if __name__ == "__main__":
    main()
