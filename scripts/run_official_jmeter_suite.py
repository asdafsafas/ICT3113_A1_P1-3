#!/usr/bin/env python3
"""Run the nine standard JMeter tests for one model with evidence gates.

The load generator cannot reset or monitor the system-under-test (SUT) Mac, so this
runner pauses before and after every measured run.  The operator must complete the
documented reset/warm-up and resource-monitoring steps on the SUT before entering
READY, then pull the service log and statistics file before entering PULLED.

Examples:
    python3 scripts/run_official_jmeter_suite.py \
        --host 172.20.10.2 --model qwen2.5:0.5b

    # Continue the current model without overwriting completed JMeter evidence.
    python3 scripts/run_official_jmeter_suite.py \
        --host 172.20.10.2 --model qwen2.5:0.5b --resume

    # Print the remaining commands without running them.
    python3 scripts/run_official_jmeter_suite.py \
        --host 172.20.10.2 --model qwen2.5:0.5b --resume --dry-run
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import shlex
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from collections import Counter
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Configuration:
    name: str
    post_rate: str
    post_rate_end: str
    search_rate: str
    duration_min: int
    drain_min: int
    stem: str


CONFIGURATIONS = (
    Configuration("average", "1.45", "1.45", "2.9", 10, 5, "1.45rpm_s2.9"),
    Configuration("peak", "1.73", "1.73", "3.5", 10, 5, "1.73rpm_s3.5"),
    Configuration("beyond-peak", "3.5", "3.5", "7", 10, 5, "3.5rpm_s7"),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", required=True, help="SUT Mac IP address")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument(
        "--model",
        required=True,
        help="Expected Ollama model tag, for example qwen2.5:0.5b",
    )
    parser.add_argument(
        "--jmeter",
        help="JMeter executable; otherwise use JMETER_BIN, PATH, or the known Downloads path",
    )
    parser.add_argument(
        "--data",
        type=Path,
        default=REPO / "loadtest" / "data" / "tickets.tsv",
    )
    parser.add_argument(
        "--configs",
        nargs="+",
        choices=[config.name for config in CONFIGURATIONS],
        default=[config.name for config in CONFIGURATIONS],
        help="Configurations to run in order (default: all three)",
    )
    parser.add_argument(
        "--runs",
        nargs="+",
        type=int,
        choices=(1, 2, 3),
        default=[1, 2, 3],
        help="Repetition numbers to run (default: 1 2 3)",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Skip runs whose JTL and JMeter log both already exist",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the plan and commands without executing JMeter or writing files",
    )
    parser.add_argument("--timeout-ms", type=int, default=600_000)
    return parser.parse_args()


def resolve_jmeter(value: str | None) -> Path:
    candidates = [
        value,
        os.environ.get("JMETER_BIN"),
        shutil.which("jmeter"),
        str(Path.home() / "Downloads" / "apache-jmeter-5.6.3" / "bin" / "jmeter"),
    ]
    for candidate in candidates:
        if candidate and Path(candidate).is_file() and os.access(candidate, os.X_OK):
            return Path(candidate).resolve()
    raise SystemExit(
        "Could not find an executable JMeter binary. Pass --jmeter /path/to/bin/jmeter."
    )


def model_slug(model: str) -> str:
    return model.replace(":", "-").replace("/", "-")


def check_ticket_data(path: Path) -> None:
    if not path.is_file():
        raise SystemExit(f"Ticket data does not exist: {path}")
    rows: list[tuple[str, str]] = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            try:
                row_id, encoded_narrative = line.rstrip("\n").split("\t", 1)
                narrative = json.loads(encoded_narrative)
            except (ValueError, json.JSONDecodeError) as exc:
                raise SystemExit(f"Malformed TSV record at {path}:{line_number}: {exc}") from exc
            if not isinstance(narrative, str) or not narrative.strip():
                raise SystemExit(f"Empty or non-text narrative at {path}:{line_number}.")
            rows.append((row_id, narrative))
    if len(rows) != 800:
        raise SystemExit(f"Expected exactly 800 ticket rows in {path}; found {len(rows)}.")
    try:
        row_ids = [int(row[0]) for row in rows]
    except ValueError as exc:
        raise SystemExit(f"Ticket data contains a non-numeric row ID: {path}") from exc
    expected_ids = list(range(3200, 4000))
    if row_ids != expected_ids:
        raise SystemExit(
            f"Ticket IDs in {path} must be exactly 3200 through 3999 in order; "
            f"found {row_ids[0]} through {row_ids[-1]}."
        )


def read_health(host: str, port: int, expected_model: str) -> dict:
    url = f"http://{host}:{port}/health"
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            health = json.load(response)
    except (OSError, urllib.error.URLError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Could not read healthy SUT metadata from {url}: {exc}") from exc

    if health.get("status") not in (None, "ok"):
        raise RuntimeError(f"SUT health is not OK: {health}")
    if health.get("model") != expected_model:
        raise RuntimeError(
            f"Wrong model at {url}: expected {expected_model!r}, got {health.get('model')!r}."
        )
    if not health.get("model_digest"):
        raise RuntimeError(f"SUT health response has no model digest: {health}")
    return health


def build_command(
    jmeter: Path,
    host: str,
    port: int,
    data: Path,
    config: Configuration,
    timeout_ms: int,
    jtl: Path,
    jmeter_log: Path,
) -> list[str]:
    return [
        str(jmeter),
        "-n",
        "-t",
        str(REPO / "loadtest" / "triage.jmx"),
        "-q",
        str(REPO / "loadtest" / "triage.properties"),
        f"-Jhost={host}",
        f"-Jport={port}",
        f"-Jrate={config.post_rate}",
        f"-Jrate_end={config.post_rate_end}",
        f"-Jsearch_rate={config.search_rate}",
        f"-Jduration={config.duration_min}",
        f"-Jdrain={config.drain_min}",
        f"-Jtimeout_ms={timeout_ms}",
        f"-Jdata={data}",
        "-l",
        str(jtl),
        "-j",
        str(jmeter_log),
    ]


def require_exact_input(prompt: str, expected: str) -> None:
    try:
        answer = input(prompt).strip()
    except (EOFError, KeyboardInterrupt):
        print("\nStopped without starting the next run.")
        raise SystemExit(130)
    if answer != expected:
        raise SystemExit(f"Expected {expected!r}; stopped without starting the next run.")


def inspect_jtl(path: Path) -> tuple[list[dict[str, str]], Counter]:
    if not path.is_file() or path.stat().st_size == 0:
        raise RuntimeError(f"JMeter did not create a non-empty result file: {path}")
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise RuntimeError(f"JMeter result contains no samples: {path}")
    request_ids = [row.get("rid", "") for row in rows]
    if any(not request_id for request_id in request_ids):
        raise RuntimeError(f"JMeter result contains a sample with no request ID: {path}")
    if len(set(request_ids)) != len(request_ids):
        raise RuntimeError(f"JMeter result contains duplicate request IDs: {path}")
    failures = [row for row in rows if row.get("success", "").lower() != "true"]
    labels = Counter(row.get("label", "") for row in rows)
    print(
        f"JTL validation: {len(rows)} samples, {len(failures)} failed; "
        + ", ".join(f"{label}={count}" for label, count in sorted(labels.items()))
    )
    return rows, labels


def validate_completed_run(
    jtl: Path, jmeter_log: Path, config: Configuration
) -> list[dict[str, str]]:
    if not jmeter_log.is_file() or jmeter_log.stat().st_size == 0:
        raise RuntimeError(f"JMeter log is missing or empty: {jmeter_log}")
    log_text = jmeter_log.read_text(encoding="utf-8", errors="replace")
    completion_markers = (
        "Notifying test listeners of end of test",
        "Forced JVM shutdown requested at end of test",
    )
    if not all(marker in log_text for marker in completion_markers):
        raise RuntimeError(
            f"Existing output is not a completed run: {jmeter_log}. "
            "Preserve it as invalid evidence before choosing a new filename."
        )

    rows, labels = inspect_jtl(jtl)
    expected = {
        "POST /tickets": int(Decimal(config.post_rate) * config.duration_min),
        "GET /search": int(Decimal(config.search_rate) * config.duration_min),
    }
    wrong_counts = {
        label: (labels.get(label, 0), count)
        for label, count in expected.items()
        if labels.get(label, 0) != count
    }
    if wrong_counts:
        details = ", ".join(
            f"{label}: found {found}, expected {wanted}"
            for label, (found, wanted) in wrong_counts.items()
        )
        raise RuntimeError(f"Completed JTL has unexpected sample counts ({details}): {jtl}")
    return rows


def consolidate_service_log(jtl_rows: list[dict[str, str]], destination: Path) -> None:
    request_ids = {row.get("rid", "") for row in jtl_rows}
    request_ids.discard("")
    matched: dict[str, str] = {}
    log_dir = REPO / "logs" / "service"
    for path in sorted(log_dir.glob("service-*.jsonl")):
        with path.open(encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                try:
                    record = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise RuntimeError(f"Invalid JSON in {path}:{line_number}: {exc}") from exc
                request_id = record.get("request_id")
                if request_id in request_ids:
                    matched[request_id] = json.dumps(record, ensure_ascii=False) + "\n"

    missing = request_ids - matched.keys()
    if missing:
        raise RuntimeError(
            f"Pulled service logs are missing {len(missing)} of {len(request_ids)} request IDs."
        )

    ordered_lines = [matched[row["rid"]] for row in jtl_rows]
    content = "".join(ordered_lines)
    if destination.exists():
        if destination.read_text(encoding="utf-8") != content:
            raise RuntimeError(f"Refusing to overwrite different service evidence: {destination}")
        print(f"Service evidence already matches: {destination.relative_to(REPO)}")
        return
    destination.write_text(content, encoding="utf-8")
    print(f"Saved {len(ordered_lines)} service records: {destination.relative_to(REPO)}")


def run_reconciliation(jtl: Path, log_dir: Path) -> None:
    command = [
        sys.executable,
        str(REPO / "scripts" / "reconcile.py"),
        str(jtl),
        "--logs",
        str(log_dir),
    ]
    result = subprocess.run(command, cwd=REPO, check=False)
    if result.returncode:
        raise RuntimeError(f"Reconciliation command failed with exit code {result.returncode}.")


def main() -> int:
    args = parse_args()
    jmeter = resolve_jmeter(args.jmeter)
    data = args.data.expanduser().resolve()
    check_ticket_data(data)
    slug = model_slug(args.model)
    result_dir = REPO / "results" / "load" / slug
    selected = [config for config in CONFIGURATIONS if config.name in args.configs]

    print(f"Model:       {args.model}")
    print(f"SUT:         http://{args.host}:{args.port}")
    print(f"JMeter:      {jmeter}")
    print(f"Ticket data: {data} (800 rows)")
    print(f"Matrix:      {len(selected) * len(args.runs)} measured runs")

    frozen_digest: str | None = None
    planned = 0
    completed = 0
    skipped = 0

    for config in selected:
        for run_number in args.runs:
            planned += 1
            base = f"{config.stem}_run{run_number}"
            jtl = result_dir / f"{base}.jtl"
            jmeter_log = result_dir / f"{base}_jmeter.log"
            stats = result_dir / f"{base}_stats.csv"
            service_log = result_dir / f"service-{base}.jsonl"
            command = build_command(
                jmeter,
                args.host,
                args.port,
                data,
                config,
                args.timeout_ms,
                jtl,
                jmeter_log,
            )

            print(f"\n[{planned}/{len(selected) * len(args.runs)}] {config.name} run {run_number}")
            print("Command:")
            print("  " + " \\\n    ".join(shlex.quote(part) for part in command))

            existing = (jtl.exists(), jmeter_log.exists())
            if any(existing):
                if not all(existing):
                    raise SystemExit(
                        f"Partial output collision: JTL exists={existing[0]}, "
                        f"JMeter log exists={existing[1]} for {base}. Resolve it manually."
                    )
                if not args.resume:
                    raise SystemExit(
                        f"Output already exists for {base}. Use --resume to skip completed runs."
                    )
                validate_completed_run(jtl, jmeter_log, config)
                missing_evidence = [
                    path.relative_to(REPO)
                    for path in (service_log, stats)
                    if not path.is_file() or path.stat().st_size == 0
                ]
                print("Skipped: validated JTL and JMeter log already exist (--resume).")
                if missing_evidence:
                    print("WARNING: skipped run still lacks evidence:")
                    for path in missing_evidence:
                        print(f"  {path}")
                skipped += 1
                continue

            if args.dry_run:
                continue

            print("\nOn the SUT Mac, complete Section 6 of docs/actual-jmeter-test.md:")
            print("  1. Restart Ollama and triage; recreate the empty database.")
            print("  2. Warm with invented text, then clear only the warm-up database row.")
            print(f"  3. Confirm /health reports {args.model} and the frozen digest.")
            print("  4. Start docker stats in another terminal, writing exactly:")
            print(f"     {stats.relative_to(REPO)}")
            require_exact_input("Type READY only after all four steps are complete: ", "READY")

            health = read_health(args.host, args.port, args.model)
            digest = str(health["model_digest"])
            if frozen_digest is None:
                frozen_digest = digest
            elif digest != frozen_digest:
                raise SystemExit(
                    f"Model digest changed during the suite: {frozen_digest} -> {digest}."
                )
            print(f"Healthy target confirmed: model={args.model} digest={digest}")

            result_dir.mkdir(parents=True, exist_ok=True)
            result = subprocess.run(command, cwd=REPO, check=False)
            if result.returncode:
                raise SystemExit(f"JMeter failed with exit code {result.returncode}; suite stopped.")
            rows = validate_completed_run(jtl, jmeter_log, config)

            print("\nOn the SUT Mac:")
            print("  1. Stop docker stats with Control-C.")
            print("  2. Commit and push the daily service log and this statistics file:")
            print(f"     {stats.relative_to(REPO)}")
            print("On this Mac, pull those files from main.")
            require_exact_input("Type PULLED only after both evidence files are local: ", "PULLED")

            consolidate_service_log(rows, service_log)
            run_reconciliation(jtl, result_dir)
            if not stats.is_file() or stats.stat().st_size == 0:
                raise SystemExit(
                    f"Required resource statistics are still missing or empty: {stats}\n"
                    "Suite stopped so the next measured run does not start without complete evidence."
                )
            print(f"Resource evidence present: {stats.relative_to(REPO)}")
            completed += 1

    print(
        f"\nSuite finished: planned={planned}, newly completed={completed}, "
        f"skipped={skipped}."
    )
    if args.dry_run:
        print("Dry run only: JMeter was not executed and no evidence was written.")
    else:
        print("Run the summary commands in Section 12 and update results/load/RUNS.md.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1) from None
