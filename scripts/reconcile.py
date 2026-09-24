"""Check a JMeter result file against the service's request log.

    python scripts/reconcile.py results/load/<model>/<rate>rpm_run1.jtl

The brief requires every reported number to reconcile with the kept logs. This matches
each JMeter sample to its log line by request ID (JMeter sends X-Request-ID) and reports:
samples with no log line, status mismatches, other traffic the service handled during the
run, and how much of the client-side latency the service itself accounts for.
"""

import argparse
import json
from datetime import datetime
from pathlib import Path

from common import REPO, percentile, read_csv


def load_logs(log_dir):
    entries = {}
    for f in sorted(Path(log_dir).glob("service-*.jsonl")):
        with open(f, encoding="utf-8") as fh:
            for line in fh:
                e = json.loads(line)
                if "request_id" in e:
                    e["_ms"] = datetime.fromisoformat(e["ts"]).timestamp() * 1000
                    entries[e["request_id"]] = e
    return entries


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("jtl")
    ap.add_argument("--logs", default=str(REPO / "logs" / "service"))
    args = ap.parse_args()

    samples = read_csv(args.jtl)
    if samples and "rid" not in samples[0]:
        raise SystemExit("This .jtl has no 'rid' column. Run JMeter with -q loadtest/triage.properties.")
    logs = load_logs(args.logs)

    matched, missing, mismatched, overhead = 0, [], [], []
    for s in samples:
        e = logs.get(s["rid"])
        if e is None:
            missing.append(s)
            continue
        matched += 1
        if str(e["status"]) != s["responseCode"]:
            mismatched.append((s, e))
        overhead.append(int(s["elapsed"]) - e["latency_ms"])

    rids = {s["rid"] for s in samples}
    t0 = min(int(s["timeStamp"]) for s in samples)
    t1 = max(int(s["timeStamp"]) + int(s["elapsed"]) for s in samples)
    other = [e for e in logs.values() if t0 <= e["_ms"] <= t1 and e["request_id"] not in rids]

    print(f"JMeter samples:              {len(samples)}")
    print(f"  found in service log:      {matched}")
    print(f"  missing from service log:  {len(missing)}")
    for s in missing[:10]:
        print(f"    {s['label']} rid={s['rid']} code={s['responseCode']} {s['responseMessage'][:60]}")
    print(f"  status code mismatches:    {len(mismatched)}")
    for s, e in mismatched[:10]:
        print(f"    rid={s['rid']} jmeter={s['responseCode']} service={e['status']}")
    print(f"Other requests the service handled during the run: {len(other)}"
          + ("  <-- someone else was using the service; this run may be contaminated" if other else ""))
    if overhead:
        print(f"Client latency minus service latency (network + connection queueing), ms: "
              f"p50={percentile(overhead, 50):.0f}  p95={percentile(overhead, 95):.0f}  max={max(overhead):.0f}")
    print("\nMissing samples are normal for connection errors/timeouts that never reached the service;"
          "\nexplain any others before reporting numbers from this run.")


if __name__ == "__main__":
    main()
