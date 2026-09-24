"""Export ticket narratives to the tab-separated file JMeter reads, and print length statistics.

    python scripts/export_loadtest_data.py --source path/to/course_extract.csv --rows 3000-3999

Output (loadtest/data/tickets.tsv): one ticket per line, "<row>\\t<narrative as a JSON string>".
The narrative is JSON-encoded so JMeter can paste it straight into the request body.
The length statistics feed the workload model (ticket length distribution).
"""

import argparse
import json
from pathlib import Path

from common import REPO, load_narratives, md_table, parse_rows, percentile

DEFAULT_OUT = REPO / "loadtest" / "data" / "tickets.tsv"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--source", required=True, help="course .csv or .xlsx")
    ap.add_argument("--rows", required=True, help="inclusive row range, e.g. 3000-3999")
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    args = ap.parse_args()

    lo, hi = parse_rows(args.rows)
    tickets = {r: t for r, t in load_narratives(args.source).items() if lo <= r <= hi}
    if not tickets:
        raise SystemExit(f"No tickets with rows {lo}-{hi} in {args.source}")

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        for row in sorted(tickets):
            # json.dumps escapes tabs and newlines, so each ticket stays on one line.
            f.write(f"{row}\t{json.dumps(tickets[row], ensure_ascii=False)}\n")

    words = [len(t.split()) for t in tickets.values()]
    chars = [len(t) for t in tickets.values()]
    stats = [["Words"] + [percentile(words, p) for p in (5, 25, 50, 75, 95, 99)] + [max(words)],
             ["Characters"] + [percentile(chars, p) for p in (5, 25, 50, 75, 95, 99)] + [max(chars)]]
    print(f"Wrote {len(tickets)} tickets (rows {min(tickets)}-{max(tickets)}) to {out}\n")
    print("Ticket length distribution (for the workload model):\n")
    print(md_table(["", "p5", "p25", "p50", "p75", "p95", "p99", "max"], stats))


if __name__ == "__main__":
    main()
