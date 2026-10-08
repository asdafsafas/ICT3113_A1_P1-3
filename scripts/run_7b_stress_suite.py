#!/usr/bin/env python3
"""Run the three guarded 7B stress-test stages and collect their evidence.

The load-generator Mac cannot reset or monitor the SUT Mac. This runner therefore
pauses before each stage for READY and afterwards for PULLED. It refuses to start
the stress test until all nine standard 7B runs have JMeter, service-log and
resource-statistics evidence.

Examples:
    python3 scripts/run_7b_stress_suite.py --host 172.20.10.2
    python3 scripts/run_7b_stress_suite.py --host 172.20.10.2 --resume
    python3 scripts/run_7b_stress_suite.py --host 172.20.10.2 --dry-run
"""

from __future__ import annotations

import argparse
import json
import math
import shlex
import subprocess
import sys
from collections import Counter
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

from run_official_jmeter_suite import (
    CONFIGURATIONS,
    REPO,
    Configuration,
    build_command,
    check_ticket_data,
    inspect_jtl,
    read_health,
    require_exact_input,
    resolve_jmeter,
    run_reconciliation,
)


MODEL = "qwen2.5:7b"
MODEL_SLUG = "qwen2.5-7b"


@dataclass(frozen=True)
class StressStage:
    name: str
    description: str
    base: str
    configuration: Configuration


STAGES = (
    StressStage(
        "ramp",
        "30-minute ramp from 3.5 to 12 POST/min",
        "stress_3.5to12rpm_s7_run1",
        Configuration("stress-ramp", "3.5", "12", "7", 30, 10, "unused"),
    ),
    StressStage(
        "below",
        "15-minute below-limit confirmation at 7.2 POST/min",
        "stress_7.2rpm_s7_confirm_run1",
        Configuration("stress-below", "7.2", "7.2", "7", 15, 10, "unused"),
    ),
    StressStage(
        "above",
        "15-minute above-limit confirmation at 9.6 POST/min",
        "stress_9.6rpm_s7_confirm_run1",
        Configuration("stress-above", "9.6", "9.6", "7", 15, 10, "unused"),
    ),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", required=True, help="SUT Mac IP address")
    parser.add_argument("--port", type=int, default=8000)
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
        "--stages",
        nargs="+",
        choices=[stage.name for stage in STAGES],
        default=[stage.name for stage in STAGES],
        help="Stages to run in order (default: ramp below above)",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Validate and skip stages that already have complete evidence",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the plan and commands without checking prerequisites or running JMeter",
    )
    parser.add_argument("--timeout-ms", type=int, default=600_000)
    return parser.parse_args()


def pinned_digest() -> str:
    lock_path = REPO / "models" / "models.lock.json"
    try:
        lock = json.loads(lock_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Could not read model lock {lock_path}: {exc}") from exc
    for model in lock.get("models", []):
        if model.get("tag") == MODEL and model.get("digest"):
            return str(model["digest"])
    raise RuntimeError(f"No frozen digest for {MODEL} in {lock_path}.")


def require_standard_7b_evidence(result_dir: Path) -> None:
    missing: list[Path] = []
    for config in CONFIGURATIONS:
        for run_number in (1, 2, 3):
            base = f"{config.stem}_run{run_number}"
            for path in (
                result_dir / f"{base}.jtl",
                result_dir / f"{base}_jmeter.log",
                result_dir / f"{base}_stats.csv",
                result_dir / f"service-{base}.jsonl",
            ):
                if not path.is_file() or path.stat().st_size == 0:
                    missing.append(path)
    if missing:
        formatted = "\n".join(f"  {path.relative_to(REPO)}" for path in missing)
        raise RuntimeError(
            "The standard 7B matrix is not complete. Finish or restore these evidence "
            f"files before stress testing:\n{formatted}"
        )


def expected_arrivals(rate_start: str, rate_end: str, duration_min: int) -> set[int]:
    exact = (
        (Decimal(rate_start) + Decimal(rate_end))
        * Decimal(duration_min)
        / Decimal(2)
    )
    return {math.floor(exact), math.ceil(exact)}


def validate_stress_run(
    jtl: Path, jmeter_log: Path, configuration: Configuration
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
    allowed = {
        "POST /tickets": expected_arrivals(
            configuration.post_rate,
            configuration.post_rate_end,
            configuration.duration_min,
        ),
        "GET /search": expected_arrivals(
            configuration.search_rate,
            configuration.search_rate,
            configuration.duration_min,
        ),
    }
    wrong_counts = {
        label: (labels.get(label, 0), sorted(counts))
        for label, counts in allowed.items()
        if labels.get(label, 0) not in counts
    }
    unexpected = Counter(labels)
    for label in allowed:
        unexpected.pop(label, None)
    if wrong_counts or unexpected:
        details = [
            f"{label}: found {found}, expected one of {wanted}"
            for label, (found, wanted) in wrong_counts.items()
        ]
        details.extend(f"unexpected label {label}={count}" for label, count in unexpected.items())
        raise RuntimeError(
            f"Completed stress JTL has unexpected sample counts ({'; '.join(details)}): {jtl}"
        )
    return rows


def consolidate_available_service_records(
    jtl_rows: list[dict[str, str]], destination: Path
) -> tuple[int, int]:
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

    ordered_lines = [matched[row["rid"]] for row in jtl_rows if row["rid"] in matched]
    content = "".join(ordered_lines)
    if destination.exists():
        existing_content = destination.read_text(encoding="utf-8")
        if existing_content and existing_content != content:
            raise RuntimeError(f"Refusing to overwrite different service evidence: {destination}")
        if existing_content == content:
            print(f"Service evidence already matches: {destination.relative_to(REPO)}")
        else:
            destination.write_text(content, encoding="utf-8")
            print(
                f"Repaired empty service evidence with {len(ordered_lines)} records: "
                f"{destination.relative_to(REPO)}"
            )
    else:
        destination.write_text(content, encoding="utf-8")
        print(
            f"Saved {len(ordered_lines)} matched service records: "
            f"{destination.relative_to(REPO)}"
        )
    return len(ordered_lines), len(request_ids) - len(matched)


def generate_dashboard(jmeter: Path, jtl: Path, report_dir: Path) -> None:
    if report_dir.exists():
        if (report_dir / "index.html").is_file():
            print(f"HTML dashboard already exists: {report_dir.relative_to(REPO)}")
            return
        raise RuntimeError(
            f"Dashboard directory exists but is incomplete: {report_dir}. "
            "Move it aside before resuming."
        )
    command = [str(jmeter), "-g", str(jtl), "-o", str(report_dir)]
    print("Generating ramp dashboard:")
    print("  " + " \\\n    ".join(shlex.quote(part) for part in command))
    result = subprocess.run(command, cwd=REPO, check=False)
    if result.returncode or not (report_dir / "index.html").is_file():
        raise RuntimeError("JMeter did not generate a complete stress-test dashboard.")


def main() -> int:
    args = parse_args()
    jmeter = resolve_jmeter(args.jmeter)
    data = args.data.expanduser().resolve()
    check_ticket_data(data)
    result_dir = REPO / "results" / "load" / MODEL_SLUG
    selected = [stage for stage in STAGES if stage.name in args.stages]
    frozen_digest = pinned_digest()

    print(f"Model:         {MODEL}")
    print(f"Frozen digest: {frozen_digest}")
    print(f"SUT:           http://{args.host}:{args.port}")
    print(f"JMeter:        {jmeter}")
    print(f"Ticket data:   {data} (800 rows)")
    print(f"Stages:        {', '.join(stage.name for stage in selected)}")

    if not args.dry_run:
        require_standard_7b_evidence(result_dir)

    newly_completed = 0
    skipped = 0
    for stage_number, stage in enumerate(selected, start=1):
        config = stage.configuration
        jtl = result_dir / f"{stage.base}.jtl"
        jmeter_log = result_dir / f"{stage.base}_jmeter.log"
        stats = result_dir / f"{stage.base}_stats.csv"
        service_log = result_dir / f"service-{stage.base}.jsonl"
        report_dir = result_dir / f"{stage.base}_report"
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

        print(f"\n[{stage_number}/{len(selected)}] {stage.description}")
        print("Command:")
        print("  " + " \\\n    ".join(shlex.quote(part) for part in command))

        if args.dry_run:
            continue

        existing = (jtl.exists(), jmeter_log.exists())
        if any(existing):
            if not all(existing):
                raise RuntimeError(
                    f"Partial output collision for {stage.base}: JTL exists={existing[0]}, "
                    f"JMeter log exists={existing[1]}. Preserve or move it before continuing."
                )
            if not args.resume:
                raise RuntimeError(
                    f"Output already exists for {stage.base}. Use --resume after verifying it."
                )
            rows = validate_stress_run(jtl, jmeter_log, config)
            if not stats.is_file() or stats.stat().st_size == 0:
                raise RuntimeError(
                    "A completed stress stage still lacks its resource statistics. Pull or "
                    f"restore this file before resuming:\n  {stats.relative_to(REPO)}"
                )
            matched, missing = consolidate_available_service_records(rows, service_log)
            if matched == 0:
                raise RuntimeError(
                    "None of the JMeter request IDs appeared in the local service logs. "
                    "Pull the SUT service log, then run --resume again."
                )
            run_reconciliation(jtl, result_dir)
            if missing:
                print(
                    f"NOTE: {missing} JMeter samples have no service record. This is acceptable "
                    "only for connection errors/timeouts that never reached the service; explain "
                    "them in the report."
                )
            if stage.name == "ramp":
                generate_dashboard(jmeter, jtl, report_dir)
            print(f"Skipped: {stage.base} already has complete evidence (--resume).")
            print(f"Validated {len(rows)} JMeter samples.")
            skipped += 1
            continue

        print("\nOn the SUT Mac, complete the full reset in Section 6:")
        print("  1. Restart Ollama and triage; recreate the empty database.")
        print("  2. Warm with invented text, then clear only the warm-up database row.")
        print(f"  3. Confirm /health reports {MODEL} and digest {frozen_digest}.")
        print("  4. Start docker stats in another terminal, writing exactly:")
        print(f"     {stats.relative_to(REPO)}")
        require_exact_input("Type READY only after all four steps are complete: ", "READY")

        health = read_health(args.host, args.port, MODEL)
        actual_digest = str(health["model_digest"])
        if actual_digest != frozen_digest:
            raise RuntimeError(
                f"Wrong 7B digest: expected {frozen_digest}, got {actual_digest}."
            )
        print(f"Healthy frozen target confirmed: model={MODEL} digest={actual_digest}")

        result_dir.mkdir(parents=True, exist_ok=True)
        result = subprocess.run(command, cwd=REPO, check=False)
        if result.returncode:
            raise RuntimeError(
                f"JMeter failed with exit code {result.returncode}; stress suite stopped."
            )
        rows = validate_stress_run(jtl, jmeter_log, config)

        print("\nOn the SUT Mac:")
        print("  1. Stop docker stats with Control-C.")
        print("  2. Commit and push the daily service log and this statistics file:")
        print(f"     {stats.relative_to(REPO)}")
        print("On this Mac, pull those files from main.")
        require_exact_input("Type PULLED only after both evidence files are local: ", "PULLED")

        matched, missing = consolidate_available_service_records(rows, service_log)
        if matched == 0:
            raise RuntimeError(
                "None of the JMeter request IDs appeared in the pulled service logs."
            )
        run_reconciliation(jtl, result_dir)
        if not stats.is_file() or stats.stat().st_size == 0:
            raise RuntimeError(
                f"Required resource statistics are still missing or empty: {stats}\n"
                "The next stress stage will not start without complete evidence."
            )
        print(f"Resource evidence present: {stats.relative_to(REPO)}")
        if missing:
            print(
                f"NOTE: {missing} JMeter samples have no service record. This is acceptable "
                "only for connection errors/timeouts that never reached the service; explain "
                "them in the report."
            )
        if stage.name == "ramp":
            generate_dashboard(jmeter, jtl, report_dir)
        newly_completed += 1

    print(
        f"\nStress suite finished: planned={len(selected)}, "
        f"newly completed={newly_completed}, skipped={skipped}."
    )
    if args.dry_run:
        print("Dry run only: JMeter was not executed and no evidence was written.")
    else:
        print("Inspect the ramp dashboard and compare offered throughput, latency and CPU.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1) from None
