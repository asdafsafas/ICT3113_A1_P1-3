"""Shared helpers for the scripts in this folder. Standard library only."""

import csv
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from labeler.labeler import CATEGORIES as LABEL_CHOICES, read_xlsx  # noqa: E402

NONE_LABEL = "None / unclear"
CATEGORIES = [c for c in LABEL_CHOICES if c != NONE_LABEL]  # the seven real categories


def parse_rows(spec):
    """'3000-3099' -> (3000, 3099)."""
    m = re.fullmatch(r"\s*(\d+)\s*-\s*(\d+)\s*", spec or "")
    if not m:
        raise ValueError(f"row range must look like 3000-3099, got {spec!r}")
    return int(m.group(1)), int(m.group(2))


def load_narratives(path):
    """{row: narrative} from the course .xlsx or .csv.

    Uses a 'row' column when present, otherwise the 0-based data-line index.
    The narrative column is 'narrative' or anything containing 'narrative'.
    """
    path = Path(path)
    if path.suffix.lower() == ".xlsx":
        rows = read_xlsx(path)
        header, data = rows[0], rows[1:]
    else:
        with open(path, newline="", encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            header = next(reader)
            data = list(reader)
    lower = [h.strip().lower() for h in header]
    text_col = next((i for i, h in enumerate(lower) if h == "narrative"), None)
    if text_col is None:
        text_col = next(i for i, h in enumerate(lower) if "narrative" in h)
    row_col = lower.index("row") if "row" in lower else None

    out = {}
    for i, r in enumerate(data):
        if len(r) <= text_col or not r[text_col].strip():
            continue
        row = int(float(r[row_col])) if row_col is not None and r[row_col] else i
        out[row] = r[text_col]
    return out


def read_csv(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_csv(path, rows, fields):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def percentile(values, p):
    """Nearest-rank percentile (the value at or below which p% of samples fall)."""
    if not values:
        return None
    s = sorted(values)
    k = max(0, min(len(s) - 1, -(-len(s) * p // 100) - 1))
    return s[int(k)]


def md_table(header, rows):
    lines = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    lines += ["| " + " | ".join("" if v is None else str(v) for v in r) + " |" for r in rows]
    return "\n".join(lines)
