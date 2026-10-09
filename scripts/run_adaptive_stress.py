#!/usr/bin/env python3
"""Increase 7B load until a repeatable saturation signal is observed.

This runs on the JMeter Mac.  It coordinates with adaptive_stress_sut.py on the
SUT Mac, so every rate starts from the same reset/warm state and every rate
produces JMeter, service, health, resource, and SUT-audit evidence.

The stop rule is declared before the test:
  * POST error rate above 1%, or
  * material queue growth at the end of the active period together with either
    a completion-rate shortfall or at least 1.5x late-half p50 growth, or
  * at least 15% of offered POSTs still in flight at the active-period end.

The first overloaded rate is repeated once by default.  The script reports a
measured bracket only when both attempts show overload.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import re
import shlex
import subprocess
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any

from common import percentile
from run_official_jmeter_suite import (
    REPO,
    Configuration,
    build_command,
    check_ticket_data,
    inspect_jtl,
    resolve_jmeter,
    run_reconciliation,
)


MODEL = "qwen2.5:7b"
MODEL_SLUG = "qwen2.5-7b"


@dataclass(frozen=True)
class Thresholds:
    error_percent: float = 1.0
    minimum_backlog: int = 5
    material_backlog_fraction: float = 0.15
    throughput_ratio: float = 0.90
    latency_growth_ratio: float = 1.50
    latency_growth_floor_ms: int = 2_000


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", required=True, help="SUT Mac IP address")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument(
        "--agent-url",
        help="SUT agent base URL; defaults to http://HOST:8765",
    )
    parser.add_argument(
        "--token",
        default=os.environ.get("STRESS_AGENT_TOKEN"),
        help="Shared token, or set STRESS_AGENT_TOKEN",
    )
    parser.add_argument("--jmeter", help="Path to the JMeter executable")
    parser.add_argument(
        "--data",
        type=Path,
        default=REPO / "loadtest" / "data" / "tickets.tsv",
    )
    parser.add_argument("--start-rate", type=Decimal, default=Decimal("20"))
    parser.add_argument("--step", type=Decimal, default=Decimal("2"))
    parser.add_argument("--max-rate", type=Decimal, default=Decimal("24"))
    parser.add_argument("--search-rate", type=Decimal, default=Decimal("7"))
    parser.add_argument("--duration", type=int, default=10, help="Active minutes per rate")
    parser.add_argument("--drain", type=int, default=10, help="Drain minutes per rate")
    parser.add_argument("--timeout-ms", type=int, default=600_000)
    parser.add_argument(
        "--confirm-runs",
        type=int,
        default=1,
        help="Extra attempts at the first overloaded rate (default: 1)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=REPO / "results" / "load" / MODEL_SLUG / "adaptive-stress",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the rate plan and commands without contacting the SUT or running JMeter",
    )
    return parser.parse_args()


def decimal_text(value: Decimal) -> str:
    return format(value.normalize(), "f")


def rate_stem(value: Decimal) -> str:
    return decimal_text(value).replace("-", "neg")


def rate_sequence(start: Decimal, step: Decimal, maximum: Decimal) -> list[Decimal]:
    if start <= 0 or step <= 0 or maximum < start:
        raise SystemExit("Require 0 < --start-rate <= --max-rate and --step > 0.")
    values: list[Decimal] = []
    value = start
    while value <= maximum:
        values.append(value)
        value += step
    return values


def pinned_digest() -> str:
    path = REPO / "models" / "models.lock.json"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"Could not read {path}: {exc}") from exc
    for model in payload.get("models", []):
        if model.get("tag") == MODEL and model.get("digest"):
            return str(model["digest"])
    raise SystemExit(f"No frozen digest for {MODEL} in {path}.")


def agent_request(
    agent_url: str,
    token: str,
    path: str,
    payload: dict[str, Any] | None = None,
    timeout: int = 900,
) -> dict[str, Any]:
    url = agent_url.rstrip("/") + path
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        method="GET" if payload is None else "POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            result = json.load(response)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"SUT agent returned HTTP {exc.code} for {path}: {detail}") from exc
    except (OSError, urllib.error.URLError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Could not call SUT agent at {url}: {exc}") from exc
    if not result.get("ok"):
        raise RuntimeError(f"SUT agent rejected {path}: {result}")
    return result


def expected_count(rate: Decimal, duration_min: int) -> set[int]:
    """Allow one arrival of scheduler jitter at an active-period boundary."""
    exact = rate * Decimal(duration_min)
    lower = max(0, math.floor(exact) - 1)
    upper = math.ceil(exact) + 1
    return set(range(lower, upper + 1))


def validate_counts(
    rows: list[dict[str, str]], post_rate: Decimal, search_rate: Decimal, duration: int
) -> None:
    labels: dict[str, int] = {}
    for row in rows:
        label = row.get("label", "")
        labels[label] = labels.get(label, 0) + 1
    allowed = {
        "POST /tickets": expected_count(post_rate, duration),
        "GET /search": expected_count(search_rate, duration),
    }
    problems = []
    for label, counts in allowed.items():
        if labels.get(label, 0) not in counts:
            problems.append(f"{label}={labels.get(label, 0)}, expected one of {sorted(counts)}")
    unexpected = {key: value for key, value in labels.items() if key not in allowed}
    if unexpected:
        problems.append(f"unexpected labels={unexpected}")
    if problems:
        raise RuntimeError("Unexpected JMeter sample counts: " + "; ".join(problems))


def read_jmeter_start_ms(path: Path, fallback_ms: int) -> int:
    """Read JMeter's own test-start epoch instead of guessing from first arrival."""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return fallback_ms
    match = re.search(r"(?:Running test|Starting standalone test @ .*) \((\d{13})\)", text)
    return int(match.group(1)) if match else fallback_ms


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def save_agent_evidence(
    response: dict[str, Any], output_dir: Path, stage_id: str
) -> dict[str, Path]:
    mapping = {
        "service_jsonl": output_dir / f"service-{stage_id}.jsonl",
        "stats_csv": output_dir / f"{stage_id}_stats.csv",
        "sut_audit_jsonl": output_dir / f"{stage_id}_sut-audit.jsonl",
        "health_json": output_dir / f"{stage_id}_health.json",
    }
    hashes = response.get("sha256", {})
    for key, path in mapping.items():
        value = response.get(key)
        if not isinstance(value, str):
            raise RuntimeError(f"SUT agent response has no text field {key!r}.")
        expected_hash = hashes.get(key)
        actual_hash = sha256_text(value)
        if expected_hash != actual_hash:
            raise RuntimeError(
                f"Evidence transfer hash mismatch for {key}: {expected_hash} != {actual_hash}"
            )
        if path.exists():
            raise RuntimeError(f"Refusing to overwrite existing evidence: {path}")
        path.write_text(value, encoding="utf-8")
    return mapping


def fmt_seconds(value_ms: float | int | None) -> str:
    return "n/a" if value_ms is None else f"{float(value_ms) / 1000:.2f}"


def ratio(numerator: float | int | None, denominator: float | int | None) -> float | None:
    if numerator is None or denominator in (None, 0):
        return None
    return float(numerator) / float(denominator)


def analyse_stage(
    rows: list[dict[str, str]],
    offered_rate: Decimal,
    duration_min: int,
    active_start_ms: int,
    thresholds: Thresholds,
) -> dict[str, Any]:
    posts = [row for row in rows if row.get("label") == "POST /tickets"]
    searches = [row for row in rows if row.get("label") == "GET /search"]
    successes = [row for row in posts if row.get("success", "").lower() == "true"]
    failures = [row for row in posts if row.get("success", "").lower() != "true"]
    active_end_ms = active_start_ms + duration_min * 60_000
    midpoint_ms = active_start_ms + duration_min * 30_000

    def started(row: dict[str, str]) -> int:
        return int(row["timeStamp"])

    def finished(row: dict[str, str]) -> int:
        return int(row["timeStamp"]) + int(row["elapsed"])

    def in_flight_at(instant_ms: int) -> int:
        return sum(1 for row in posts if started(row) <= instant_ms < finished(row))

    early = [int(row["elapsed"]) for row in successes if started(row) < midpoint_ms]
    late = [int(row["elapsed"]) for row in successes if started(row) >= midpoint_ms]
    elapsed = [int(row["elapsed"]) for row in successes]
    last_half_completions = sum(
        1 for row in successes if midpoint_ms <= finished(row) <= active_end_ms
    )
    last_half_throughput = last_half_completions / (duration_min / 2)
    offered = float(offered_rate)
    backlog_mid = in_flight_at(midpoint_ms)
    backlog_end = in_flight_at(active_end_ms)
    error_percent = 100 * len(failures) / len(posts) if posts else 100.0
    early_p50 = percentile(early, 50)
    late_p50 = percentile(late, 50)
    latency_ratio = ratio(late_p50, early_p50)
    material_backlog = max(
        thresholds.minimum_backlog,
        math.ceil(len(posts) * thresholds.material_backlog_fraction),
    )
    queue_grew = backlog_end >= thresholds.minimum_backlog and backlog_end > backlog_mid
    throughput_shortfall = last_half_throughput < offered * thresholds.throughput_ratio
    latency_growth = bool(
        latency_ratio is not None
        and latency_ratio >= thresholds.latency_growth_ratio
        and late_p50 is not None
        and early_p50 is not None
        and late_p50 - early_p50 >= thresholds.latency_growth_floor_ms
    )

    reasons: list[str] = []
    if error_percent > thresholds.error_percent:
        reasons.append(
            f"POST error rate {error_percent:.2f}% exceeded {thresholds.error_percent:.2f}%"
        )
    if backlog_end >= material_backlog:
        reasons.append(
            f"end backlog {backlog_end} reached material threshold {material_backlog}"
        )
    if queue_grew and throughput_shortfall:
        reasons.append(
            f"backlog grew {backlog_mid}->{backlog_end} while last-half throughput "
            f"{last_half_throughput:.2f}/min was below 90% of offered load"
        )
    if queue_grew and latency_growth:
        reasons.append(
            f"backlog grew {backlog_mid}->{backlog_end} and late-half p50 was "
            f"{latency_ratio:.2f}x early-half p50"
        )

    saturated = bool(reasons)
    return {
        "offered_post_per_min": offered,
        "post_samples": len(posts),
        "search_samples": len(searches),
        "post_successes": len(successes),
        "post_failures": len(failures),
        "post_error_percent": round(error_percent, 4),
        "post_p50_ms": percentile(elapsed, 50),
        "post_p95_ms": percentile(elapsed, 95),
        "post_p99_ms": percentile(elapsed, 99),
        "early_half_post_p50_ms": early_p50,
        "late_half_post_p50_ms": late_p50,
        "late_to_early_p50_ratio": None if latency_ratio is None else round(latency_ratio, 4),
        "backlog_at_midpoint": backlog_mid,
        "backlog_at_active_end": backlog_end,
        "material_backlog_threshold": material_backlog,
        "last_half_successful_completions": last_half_completions,
        "last_half_throughput_per_min": round(last_half_throughput, 4),
        "throughput_to_offered_ratio": round(last_half_throughput / offered, 4),
        "queue_grew": queue_grew,
        "throughput_shortfall": throughput_shortfall,
        "latency_growth": latency_growth,
        "classification": "OVERLOADED" if saturated else "SUSTAINED",
        "reasons": reasons or ["none of the predeclared saturation conditions was met"],
        "active_start_epoch_ms": active_start_ms,
        "active_end_epoch_ms": active_end_ms,
    }


def stats_summary(path: Path) -> dict[str, Any]:
    by_container: dict[str, list[float]] = {}
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            name = row.get("container", "")
            raw_cpu = row.get("cpu_percent", "").strip().rstrip("%")
            try:
                cpu = float(raw_cpu)
            except ValueError:
                continue
            by_container.setdefault(name, []).append(cpu)
    result: dict[str, Any] = {}
    for name, values in by_container.items():
        result[name] = {
            "samples": len(values),
            "mean_cpu_percent": round(sum(values) / len(values), 2),
            "p95_cpu_percent": percentile(values, 95),
            "max_cpu_percent": max(values),
        }
    return result


def write_summary(
    output_dir: Path,
    attempts: list[dict[str, Any]],
    conclusion: dict[str, Any],
    settings: dict[str, Any],
) -> None:
    payload = {
        "generated_at_epoch_s": time.time(),
        "model": MODEL,
        "settings": settings,
        "attempts": attempts,
        "conclusion": conclusion,
    }
    (output_dir / "adaptive-stress-summary.json").write_text(
        json.dumps(payload, indent=2) + "\n", encoding="utf-8"
    )

    lines = [
        "# Adaptive Stress Test Summary",
        "",
        f"Model: `{MODEL}`",
        "",
        "## Predeclared stop rule",
        "",
        (
            "A rate is classified as overloaded when POST errors exceed 1%, or when "
            "material queue growth is accompanied by a completion-rate shortfall or "
            "late-half latency growth, or when at least 15% of offered POSTs remain in "
            "flight at the end of the active period. The first overloaded rate is "
            "repeated before reporting a bracket."
        ),
        "",
        "## Results",
        "",
        "| Rate /min | Attempt | Result | POST p50 s | p95 s | p99 s | Errors % | "
        "Backlog mid/end | Last-half throughput /min |",
        "|---:|---:|---|---:|---:|---:|---:|---:|---:|",
    ]
    for item in attempts:
        lines.append(
            "| {rate:.2f} | {attempt} | {classification} | {p50} | {p95} | {p99} | "
            "{errors:.2f} | {mid}/{end} | {throughput:.2f} |".format(
                rate=item["offered_post_per_min"],
                attempt=item["attempt"],
                classification=item["classification"],
                p50=fmt_seconds(item["post_p50_ms"]),
                p95=fmt_seconds(item["post_p95_ms"]),
                p99=fmt_seconds(item["post_p99_ms"]),
                errors=item["post_error_percent"],
                mid=item["backlog_at_midpoint"],
                end=item["backlog_at_active_end"],
                throughput=item["last_half_throughput_per_min"],
            )
        )
    lines.extend(
        [
            "",
            "## Conclusion",
            "",
            conclusion["report_text"],
            "",
            "Each row is backed by a JTL, JMeter log, matched service JSONL, Docker "
            "statistics CSV, health snapshot and SUT audit log in this directory.",
            "",
        ]
    )
    (output_dir / "adaptive-stress-summary.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )


def make_conclusion(
    attempts: list[dict[str, Any]],
    maximum_rate: Decimal,
) -> dict[str, Any]:
    by_rate: dict[float, list[dict[str, Any]]] = {}
    for item in attempts:
        by_rate.setdefault(item["offered_post_per_min"], []).append(item)
    confirmed_overload: float | None = None
    for rate in sorted(by_rate):
        results = by_rate[rate]
        if len(results) >= 2 and all(item["classification"] == "OVERLOADED" for item in results):
            confirmed_overload = rate
            break
    sustained_rates = [
        item["offered_post_per_min"]
        for item in attempts
        if item["classification"] == "SUSTAINED"
        and (confirmed_overload is None or item["offered_post_per_min"] < confirmed_overload)
    ]
    highest_sustained = max(sustained_rates) if sustained_rates else None

    if confirmed_overload is not None and highest_sustained is not None:
        report_text = (
            f"The measured sustainable mixed-load capacity is bracketed above "
            f"{highest_sustained:g} and at or below {confirmed_overload:g} classification "
            "requests per minute, with 7 searches per minute. The higher rate met the "
            "predeclared overload rule in two independent reset-and-warm attempts."
        )
        status = "LIMIT_BRACKETED"
    elif confirmed_overload is not None:
        report_text = (
            f"Overload was reproduced at {confirmed_overload:g} classification requests "
            "per minute, but no lower sustained rate was measured in this run."
        )
        status = "OVERLOAD_FOUND_NO_LOWER_BOUND"
    else:
        max_tested = max(
            (item["offered_post_per_min"] for item in attempts),
            default=float(maximum_rate),
        )
        report_text = (
            f"No repeatable overload was found through the maximum tested rate of "
            f"{max_tested:g} classification requests per minute. The demonstrated "
            f"capacity is therefore at least {max_tested:g}/min; the true limit is higher."
        )
        status = "NO_LIMIT_WITHIN_RANGE"
    return {
        "status": status,
        "highest_sustained_post_per_min": highest_sustained,
        "first_confirmed_overloaded_post_per_min": confirmed_overload,
        "report_text": report_text,
    }


def main() -> int:
    args = parse_args()
    if not args.token or len(args.token) < 12:
        raise SystemExit("Set --token or STRESS_AGENT_TOKEN to at least 12 characters.")
    if args.duration < 5:
        raise SystemExit("Use --duration of at least 5 minutes for a defensible trend.")
    if args.drain < 1:
        raise SystemExit("--drain must be at least 1 minute.")
    if args.confirm_runs < 1:
        raise SystemExit("--confirm-runs must be at least 1.")

    rates = rate_sequence(args.start_rate, args.step, args.max_rate)
    digest = pinned_digest()
    data = args.data.expanduser().resolve()
    check_ticket_data(data)
    jmeter = resolve_jmeter(args.jmeter)
    output_dir = args.output_dir.expanduser().resolve()
    agent_url = args.agent_url or f"http://{args.host}:8765"
    thresholds = Thresholds()

    print(f"Model:            {MODEL}")
    print(f"Frozen digest:    {digest}")
    print(f"SUT:              http://{args.host}:{args.port}")
    print(f"SUT agent:        {agent_url}")
    print(f"Rates:            {', '.join(decimal_text(rate) for rate in rates)} POST/min")
    print(f"Search load:      {decimal_text(args.search_rate)}/min")
    print(f"Stage timing:     {args.duration} min active + {args.drain} min drain")
    print(f"Evidence:         {output_dir}")

    if args.dry_run:
        for rate in rates:
            stage_id = (
                f"adaptive_{rate_stem(rate)}rpm_s{rate_stem(args.search_rate)}_run1"
            )
            config = Configuration(
                "adaptive",
                decimal_text(rate),
                decimal_text(rate),
                decimal_text(args.search_rate),
                args.duration,
                args.drain,
                stage_id,
            )
            command = build_command(
                jmeter,
                args.host,
                args.port,
                data,
                config,
                args.timeout_ms,
                output_dir / f"{stage_id}.jtl",
                output_dir / f"{stage_id}_jmeter.log",
            )
            print("\n" + " \\\n  ".join(shlex.quote(part) for part in command))
        print("\nDry run only; no files were written and the SUT agent was not contacted.")
        return 0

    output_dir.mkdir(parents=True, exist_ok=True)
    collisions: list[Path] = []
    for rate in rates:
        stage_prefix = (
            f"adaptive_{rate_stem(rate)}rpm_s{rate_stem(args.search_rate)}_run"
        )
        collisions.extend(output_dir.glob(f"{stage_prefix}*"))
        collisions.extend(output_dir.glob(f"service-{stage_prefix}*"))
    for summary_name in ("adaptive-stress-summary.md", "adaptive-stress-summary.json"):
        summary_path = output_dir / summary_name
        if summary_path.exists():
            collisions.append(summary_path)
    if collisions:
        names = ", ".join(sorted(path.name for path in collisions))
        raise SystemExit(
            f"Evidence for the requested rate plan already exists in {output_dir}: {names}. "
            "Preserve or move those files before starting a new measured test."
        )

    agent_health = agent_request(agent_url, args.token, "/agent/health", timeout=20)
    if agent_health.get("model") != MODEL:
        raise RuntimeError(
            f"SUT agent is configured for {agent_health.get('model')!r}, expected {MODEL!r}."
        )
    if agent_health.get("active_stage"):
        raise RuntimeError(f"SUT agent already has an active stage: {agent_health}")

    settings = {
        "host": args.host,
        "port": args.port,
        "frozen_digest": digest,
        "rates_post_per_min": [float(rate) for rate in rates],
        "search_rate_per_min": float(args.search_rate),
        "duration_min": args.duration,
        "drain_min": args.drain,
        "confirm_runs": args.confirm_runs,
        "thresholds": thresholds.__dict__,
    }
    attempts: list[dict[str, Any]] = []
    stop = False

    for rate in rates:
        attempts_at_rate = 1
        attempt_number = 1
        while attempt_number <= attempts_at_rate:
            stage_id = (
                f"adaptive_{rate_stem(rate)}rpm_s{rate_stem(args.search_rate)}_run{attempt_number}"
            )
            jtl = output_dir / f"{stage_id}.jtl"
            jmeter_log = output_dir / f"{stage_id}_jmeter.log"
            for path in (jtl, jmeter_log):
                if path.exists():
                    raise RuntimeError(f"Refusing to overwrite existing evidence: {path}")
            config = Configuration(
                "adaptive",
                decimal_text(rate),
                decimal_text(rate),
                decimal_text(args.search_rate),
                args.duration,
                args.drain,
                stage_id,
            )
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

            print(
                f"\n=== {decimal_text(rate)} POST/min, attempt {attempt_number} "
                f"({args.duration}+{args.drain} min) ==="
            )
            print("Preparing, restarting and warming the SUT...")
            agent_request(
                agent_url,
                args.token,
                "/agent/prepare",
                {
                    "stage_id": stage_id,
                    "expected_model": MODEL,
                    "expected_digest": digest,
                },
            )

            rows: list[dict[str, str]] = []
            process_launch_ms = int(time.time() * 1000)
            jmeter_failed = False
            try:
                print("Running:")
                print("  " + " \\\n    ".join(shlex.quote(part) for part in command))
                result = subprocess.run(command, cwd=REPO, check=False)
                jmeter_failed = result.returncode != 0
                if jtl.is_file() and jtl.stat().st_size:
                    rows, _ = inspect_jtl(jtl)
            finally:
                request_ids = [row.get("rid", "") for row in rows if row.get("rid")]
                print("Stopping SUT monitoring and downloading evidence...")
                response = agent_request(
                    agent_url,
                    args.token,
                    "/agent/finish",
                    {"stage_id": stage_id, "request_ids": request_ids},
                )
                evidence_paths = save_agent_evidence(response, output_dir, stage_id)

            if jmeter_failed:
                raise RuntimeError(
                    "JMeter failed. Evidence was preserved; inspect the JMeter and SUT audit logs."
                )
            validate_counts(rows, rate, args.search_rate, args.duration)
            active_start_ms = read_jmeter_start_ms(jmeter_log, process_launch_ms)
            missing = response.get("missing_request_ids", [])
            if missing:
                failures = [
                    row
                    for row in rows
                    if row.get("rid") in set(missing)
                    and row.get("success", "").lower() != "true"
                ]
                if len(failures) != len(missing):
                    raise RuntimeError(
                        f"SUT service evidence is missing {len(missing)} request IDs, including "
                        "successful requests. The run is not reportable."
                    )
                print(
                    f"NOTE: {len(missing)} failed requests never reached the service; "
                    "their JMeter records remain evidence."
                )
            run_reconciliation(jtl, output_dir)

            analysis = analyse_stage(
                rows,
                rate,
                args.duration,
                active_start_ms,
                thresholds,
            )
            analysis.update(
                {
                    "stage_id": stage_id,
                    "attempt": attempt_number,
                    "jtl": str(jtl.relative_to(REPO)),
                    "jmeter_log": str(jmeter_log.relative_to(REPO)),
                    "service_log": str(evidence_paths["service_jsonl"].relative_to(REPO)),
                    "stats_csv": str(evidence_paths["stats_csv"].relative_to(REPO)),
                    "health_json": str(evidence_paths["health_json"].relative_to(REPO)),
                    "sut_audit_log": str(
                        evidence_paths["sut_audit_jsonl"].relative_to(REPO)
                    ),
                    "resource_summary": stats_summary(evidence_paths["stats_csv"]),
                }
            )
            attempts.append(analysis)
            print(
                f"Result: {analysis['classification']} | POST p95 "
                f"{fmt_seconds(analysis['post_p95_ms'])} s | errors "
                f"{analysis['post_error_percent']:.2f}% | backlog "
                f"{analysis['backlog_at_midpoint']}->{analysis['backlog_at_active_end']} | "
                f"last-half throughput {analysis['last_half_throughput_per_min']:.2f}/min"
            )
            for reason in analysis["reasons"]:
                print(f"  - {reason}")

            interim = make_conclusion(attempts, args.max_rate)
            write_summary(output_dir, attempts, interim, settings)

            if analysis["classification"] == "OVERLOADED" and attempt_number == 1:
                attempts_at_rate = 1 + args.confirm_runs
                print(
                    f"Overload signal detected. Automatically repeating this rate "
                    f"{args.confirm_runs} more time(s) after a fresh reset."
                )
            attempt_number += 1

        results_at_rate = [
            item for item in attempts if item["offered_post_per_min"] == float(rate)
        ]
        if (
            len(results_at_rate) >= 2
            and all(item["classification"] == "OVERLOADED" for item in results_at_rate)
        ):
            stop = True
            break

    conclusion = make_conclusion(attempts, args.max_rate)
    write_summary(output_dir, attempts, conclusion, settings)
    print("\n=== Adaptive stress test complete ===")
    print(conclusion["report_text"])
    print(f"Summary: {output_dir / 'adaptive-stress-summary.md'}")
    print(f"Raw decision record: {output_dir / 'adaptive-stress-summary.json'}")
    if stop:
        print("Stopped automatically after the first repeatable overload signal.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1) from None
