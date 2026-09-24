"""Request log: one JSON object per line, one file per UTC day.

Every request the service handles is written here. These files are the evidence
that the numbers in the report came from real runs, so they are committed to git.
"""

import json
import threading
from datetime import datetime, timezone

from . import config

_lock = threading.Lock()


def utc_now():
    return datetime.now(timezone.utc)


def write(entry):
    now = utc_now()
    entry = {"ts": now.isoformat(timespec="milliseconds"), **entry}
    line = json.dumps(entry, ensure_ascii=False)
    path = config.LOG_DIR / f"service-{now:%Y-%m-%d}.jsonl"
    with _lock:
        config.LOG_DIR.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(line + "\n")
