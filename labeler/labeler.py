"""Golden-set labelling tool for ICT3113 Assignment 1.

Run:  python labeler/labeler.py            (then open http://localhost:8765)
      python labeler/labeler.py --xlsx path/to/file.xlsx --port 8765

Each annotator's labels are saved to labeler/labels/labels_<annotator>.csv after
every save, so you can close the browser at any time and resume later.
Standard library only; no installs needed.
"""

import argparse
import csv
import json
import os
import re
import tempfile
import zipfile
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

HERE = Path(__file__).resolve().parent
XLSX_NAME = "ict3113_ticket_P1-3.xlsx"
# Look inside the labeler folder first (for sharing just this folder), then the project root.
DEFAULT_XLSX = next((p for p in (HERE / XLSX_NAME, HERE.parent / XLSX_NAME) if p.exists()),
                    HERE / XLSX_NAME)
LABELS_DIR = HERE / "labels"

CATEGORIES = [
    "Credit reporting",
    "Debt collection",
    "Mortgage",
    "Credit card",
    "Bank account or service",
    "Consumer loan",
    "Money transfer or service",
    "None / unclear",
]
CSV_FIELDS = ["row", "label", "secondary_label", "reasoning", "labelled_at"]

NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}


def col_index(cell_ref):
    """'C12' -> 2 (zero-based column index)."""
    letters = re.match(r"[A-Z]+", cell_ref).group(0)
    n = 0
    for ch in letters:
        n = n * 26 + (ord(ch) - 64)
    return n - 1


def read_xlsx(path):
    """Return the first sheet as a list of rows (lists of strings)."""
    with zipfile.ZipFile(path) as z:
        shared = []
        if "xl/sharedStrings.xml" in z.namelist():
            root = ET.fromstring(z.read("xl/sharedStrings.xml"))
            for si in root.findall("m:si", NS):
                # Rich-text strings are split across several <t> runs.
                shared.append("".join(t.text or "" for t in si.iter(f"{{{NS['m']}}}t")))
        sheet = ET.fromstring(z.read("xl/worksheets/sheet1.xml"))

    rows = []
    for r in sheet.iter(f"{{{NS['m']}}}row"):
        values = {}
        for c in r.findall("m:c", NS):
            kind = c.get("t")
            if kind == "inlineStr":
                text = "".join(t.text or "" for t in c.iter(f"{{{NS['m']}}}t"))
            else:
                v = c.find("m:v", NS)
                text = v.text if v is not None else ""
                if kind == "s":
                    text = shared[int(text)]
            values[col_index(c.get("r"))] = text
        width = max(values) + 1 if values else 0
        rows.append([values.get(i, "") for i in range(width)])
    return rows


def load_tickets(path):
    rows = read_xlsx(path)
    header = [h.strip().lower() for h in rows[0]]
    i_row, i_text = header.index("row"), header.index("narrative")
    tickets = []
    for r in rows[1:]:
        if len(r) <= max(i_row, i_text) or not r[i_row]:
            continue
        # The source_label column is deliberately NOT sent to the browser:
        # the raw labels are noisy and seeing them would bias the annotator.
        tickets.append({"row": int(float(r[i_row])), "narrative": r[i_text]})
    return tickets


def load_protocol():
    """Category definitions from protocol.json, re-read on every page load so edits apply on refresh."""
    try:
        return json.loads((HERE / "protocol.json").read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        print(f"Warning: could not read protocol.json ({e})")
        return {}


def safe_name(name):
    name = re.sub(r"[^A-Za-z0-9_-]+", "_", name.strip())[:40]
    if not name:
        raise ValueError("annotator name is required")
    return name


def labels_path(annotator):
    return LABELS_DIR / f"labels_{safe_name(annotator)}.csv"


def read_labels(annotator):
    path = labels_path(annotator)
    if not path.exists():
        return {}
    with open(path, newline="", encoding="utf-8-sig") as f:
        return {int(r["row"]): r for r in csv.DictReader(f)}


def write_labels(annotator, labels):
    """Write atomically so a crash mid-save never corrupts the file."""
    LABELS_DIR.mkdir(exist_ok=True)
    path = labels_path(annotator)
    fd, tmp = tempfile.mkstemp(dir=LABELS_DIR, suffix=".tmp")
    with os.fdopen(fd, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        w.writeheader()
        for row in sorted(labels):
            w.writerow({k: labels[row].get(k, "") for k in CSV_FIELDS})
    os.replace(tmp, path)


class Handler(BaseHTTPRequestHandler):
    tickets = []

    def log_message(self, fmt, *args):
        pass

    def send_json(self, obj, status=200):
        body = json.dumps(obj).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        url = urlparse(self.path)
        q = parse_qs(url.query)
        try:
            if url.path == "/":
                body = (HERE / "index.html").read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            elif url.path == "/api/tickets":
                self.send_json({"tickets": self.tickets, "categories": CATEGORIES,
                                "protocol": load_protocol()})
            elif url.path == "/api/labels":
                labels = read_labels(q.get("annotator", [""])[0])
                self.send_json({"labels": {str(k): v for k, v in labels.items()}})
            else:
                self.send_json({"error": "not found"}, 404)
        except ValueError as e:
            self.send_json({"error": str(e)}, 400)

    def do_POST(self):
        if urlparse(self.path).path != "/api/label":
            return self.send_json({"error": "not found"}, 404)
        try:
            data = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            row = int(data["row"])
            if row not in {t["row"] for t in self.tickets}:
                raise ValueError(f"unknown row {row}")
            if data["label"] not in CATEGORIES:
                raise ValueError("invalid label")
            secondary = data.get("secondary_label", "")
            if secondary and secondary not in CATEGORIES:
                raise ValueError("invalid secondary label")
            labels = read_labels(data["annotator"])
            labels[row] = {
                "row": row,
                "label": data["label"],
                "secondary_label": secondary,
                "reasoning": data.get("reasoning", "").strip(),
                "labelled_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            }
            write_labels(data["annotator"], labels)
            self.send_json({"ok": True, "count": len(labels)})
        except (ValueError, KeyError, TypeError) as e:
            self.send_json({"error": str(e)}, 400)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--xlsx", default=str(DEFAULT_XLSX))
    ap.add_argument("--port", type=int, default=8765)
    args = ap.parse_args()

    Handler.tickets = load_tickets(args.xlsx)
    print(f"Loaded {len(Handler.tickets)} tickets from {args.xlsx}")
    print(f"Labels are saved in {LABELS_DIR}")
    print(f"Open http://localhost:{args.port}  (Ctrl+C to stop)")
    ThreadingHTTPServer(("127.0.0.1", args.port), Handler).serve_forever()


if __name__ == "__main__":
    main()
