"""Run the JMeter plan safely against synthetic data.

The default ``--mock`` mode starts a local mock triage service, runs JMeter,
checks the resulting JTL columns, and reconciles request IDs with the mock
service log. Output is written below ``results/dry-run`` and ignored by Git.

Examples:

    python scripts/run_jmeter_dry_run.py --mock
    python scripts/run_jmeter_dry_run.py --host 192.168.1.50 --port 8000
    python scripts/run_jmeter_dry_run.py --mock --jmeter /path/to/jmeter
"""

import argparse
import csv
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen


REPO = Path(__file__).resolve().parents[1]
JMX = REPO / "loadtest" / "triage.jmx"
PROPERTIES = REPO / "loadtest" / "triage.properties"
DEFAULT_DATA = REPO / "loadtest" / "data" / "dry-run-tickets.tsv"
REQUIRED_JTL_COLUMNS = {
    "timeStamp",
    "elapsed",
    "label",
    "responseCode",
    "success",
    "rid",
    "row",
}


def resolve_jmeter(value):
    candidate = value or os.environ.get("JMETER_BIN") or shutil.which("jmeter")
    if not candidate:
        raise SystemExit(
            "JMeter was not found. Install JMeter 5.6.3, add it to PATH, set JMETER_BIN, "
            "or pass --jmeter /path/to/jmeter."
        )
    path = Path(candidate).expanduser()
    return str(path.resolve()) if path.exists() else candidate


def wait_for_health(host, port, timeout_s=20):
    url = f"http://{host}:{port}/health"
    deadline = time.monotonic() + timeout_s
    last_error = None
    while time.monotonic() < deadline:
        try:
            with urlopen(url, timeout=2) as response:
                payload = json.load(response)
            if payload.get("status") != "ok":
                raise RuntimeError(f"service health is {payload!r}")
            return payload
        except (URLError, TimeoutError, RuntimeError, json.JSONDecodeError) as error:
            last_error = error
            time.sleep(0.5)
    raise SystemExit(f"Could not reach a healthy service at {url}: {last_error}")


def check_jtl(path):
    if not path.exists() or path.stat().st_size == 0:
        raise SystemExit(f"JMeter did not produce a non-empty result file: {path}")
    with open(path, newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        fields = set(reader.fieldnames or [])
        missing = sorted(REQUIRED_JTL_COLUMNS - fields)
        if missing:
            raise SystemExit(f"JTL is missing required columns: {', '.join(missing)}")
        rows = list(reader)
    if not rows:
        raise SystemExit("The JTL contains headers but no samples")
    posts = [row for row in rows if row["label"] == "POST /tickets"]
    failed = [row for row in rows if row["success"].lower() != "true"]
    if not posts:
        raise SystemExit("The JTL contains no POST /tickets samples")
    print(f"JTL validation: {len(rows)} samples, {len(posts)} POST /tickets, {len(failed)} failed")
    if failed:
        for row in failed[:5]:
            print(f"  failed: {row['label']} code={row['responseCode']} rid={row['rid']}")
        raise SystemExit("Dry run contained failed samples; inspect jmeter.log and the service log")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--mock", action="store_true", help="start the bundled dry-run mock service")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=18000)
    parser.add_argument("--rate", type=float, default=12, help="arrivals per minute")
    parser.add_argument("--duration", type=float, default=1, help="duration in minutes")
    parser.add_argument("--drain", type=float, default=0.05, help="minutes allowed for in-flight requests to finish")
    parser.add_argument("--data", default=str(DEFAULT_DATA))
    parser.add_argument("--jmeter", help="JMeter executable; otherwise JMETER_BIN or PATH is used")
    parser.add_argument("--output-dir", help="must be empty; defaults below results/dry-run")
    args = parser.parse_args()

    jmeter = resolve_jmeter(args.jmeter)
    data = Path(args.data).expanduser().resolve()
    if not data.exists():
        raise SystemExit(f"Dry-run input does not exist: {data}")
    if args.rate <= 0 or args.duration <= 0 or args.drain <= 0:
        raise SystemExit("--rate, --duration and --drain must be greater than zero")

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output = Path(args.output_dir).expanduser().resolve() if args.output_dir else REPO / "results" / "dry-run" / timestamp
    if output.exists() and any(output.iterdir()):
        raise SystemExit(f"Output directory is not empty: {output}")
    output.mkdir(parents=True, exist_ok=True)

    mock = None
    try:
        if args.mock:
            mock = subprocess.Popen([
                sys.executable,
                str(REPO / "scripts" / "mock_triage_server.py"),
                "--host",
                args.host,
                "--port",
                str(args.port),
                "--log-dir",
                str(output / "mock-logs"),
            ])

        health = wait_for_health(args.host, args.port)
        print(
            f"Healthy target: model={health.get('model')} digest={health.get('model_digest')} "
            f"at http://{args.host}:{args.port}"
        )

        jtl = output / "dry-run.jtl"
        jmeter_log = output / "jmeter.log"
        command = [
            jmeter,
            "-n",
            "-t",
            str(JMX),
            "-q",
            str(PROPERTIES),
            f"-Jhost={args.host}",
            f"-Jport={args.port}",
            f"-Jrate={args.rate}",
            f"-Jrate_end={args.rate}",
            f"-Jduration={args.duration}",
            f"-Jdrain={args.drain}",
            "-Jsearch_rate=0",
            f"-Jdata={data}",
            "-l",
            str(jtl),
            "-j",
            str(jmeter_log),
        ]
        print("Running:", " ".join(command))
        completed = subprocess.run(command, cwd=REPO)
        if completed.returncode:
            raise SystemExit(f"JMeter exited with status {completed.returncode}; inspect {jmeter_log}")

        check_jtl(jtl)
        subprocess.run([sys.executable, str(REPO / "scripts" / "summarise_jtl.py"), str(jtl)], check=True)

        if args.mock:
            subprocess.run([
                sys.executable,
                str(REPO / "scripts" / "reconcile.py"),
                str(jtl),
                "--logs",
                str(output / "mock-logs"),
            ], check=True)
        else:
            print("Copy or pull the matching service logs, then run:")
            print(f"  python scripts/reconcile.py {jtl}")

        print(f"Dry run passed. Non-reportable output: {output}")
    finally:
        if mock is not None:
            mock.terminate()
            try:
                mock.wait(timeout=5)
            except subprocess.TimeoutExpired:
                mock.kill()


if __name__ == "__main__":
    main()
