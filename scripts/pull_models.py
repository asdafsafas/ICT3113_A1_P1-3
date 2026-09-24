"""Pull the candidate models into Ollama and pin them by digest.

    python scripts/pull_models.py            # pull everything in models/candidates.txt, write models/models.lock.json
    python scripts/pull_models.py --check    # verify installed digests still match the lock file (run before every benchmark)

Talks to Ollama at http://localhost:11434 (the port docker-compose publishes locally).
"""

import argparse
import json
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from common import REPO

CANDIDATES = REPO / "models" / "candidates.txt"
LOCK = REPO / "models" / "models.lock.json"


def api(base, path, body=None, timeout=30):
    req = urllib.request.Request(base + path, data=json.dumps(body).encode() if body is not None else None,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def pull(base, tag):
    req = urllib.request.Request(base + "/api/pull", data=json.dumps({"model": tag}).encode(),
                                 headers={"Content-Type": "application/json"})
    last = None
    with urllib.request.urlopen(req, timeout=3600) as r:
        for line in r:  # streamed progress, one JSON object per line
            msg = json.loads(line)
            if "error" in msg:
                raise SystemExit(f"{tag}: {msg['error']}")
            status = msg.get("status")
            if msg.get("total"):
                pct = 100 * msg.get("completed", 0) // msg["total"]
                status = f"{status} {pct}%"
            if status != last and (not msg.get("total") or status.endswith("0%")):
                print(f"  {tag}: {status}", flush=True)
                last = status


def candidates(path):
    tags = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.split("#", 1)[0].strip()
        if line:
            tags.append(line)
    return tags


def installed(base):
    return {m["name"]: m for m in api(base, "/api/tags")["models"]}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ollama", default="http://localhost:11434")
    ap.add_argument("--candidates", default=str(CANDIDATES), help="list of Ollama tags to pull")
    ap.add_argument("--check", action="store_true", help="only verify digests against the lock file")
    args = ap.parse_args()
    base = args.ollama.rstrip("/")

    if args.check:
        lock = json.loads(LOCK.read_text(encoding="utf-8"))
        have = installed(base)
        ok = True
        for m in lock["models"]:
            got = have.get(m["tag"], {}).get("digest")
            status = "OK" if got == m["digest"] else f"MISMATCH (installed: {got or 'not pulled'})"
            ok &= got == m["digest"]
            print(f"{m['tag']:<30} {m['digest'][:12]}  {status}")
        sys.exit(0 if ok else 1)

    tags = candidates(args.candidates)
    if not tags:
        raise SystemExit(f"No models listed in {args.candidates}")
    for tag in tags:
        print(f"Pulling {tag} ...", flush=True)
        pull(base, tag)

    have = installed(base)
    models = []
    for tag in tags:
        info = have[tag]
        show = api(base, "/api/show", {"model": tag})
        details = info.get("details", {})
        models.append({
            "tag": tag,
            "digest": info["digest"],
            "size_bytes": info.get("size"),
            "family": details.get("family"),
            "parameter_size": details.get("parameter_size"),
            "quantization": details.get("quantization_level"),
            "license_first_line": (show.get("license") or "").strip().splitlines()[0] if show.get("license") else None,
        })
    lock = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "ollama_version": api(base, "/api/version").get("version"),
        "models": models,
    }
    LOCK.write_text(json.dumps(lock, indent=2) + "\n", encoding="utf-8")
    for m in models:
        print(f"{m['tag']:<30} {m['digest'][:12]}  {m['parameter_size']:>6}  {m['quantization']}")
    print(f"Wrote {LOCK.relative_to(REPO)}. Commit it; these pins go on Slide 5.")


if __name__ == "__main__":
    main()
