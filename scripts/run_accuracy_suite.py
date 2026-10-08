#!/usr/bin/env python3
"""Run the frozen golden-set accuracy test for all active candidate models.

Run this on the system-under-test (SUT) Mac, not the JMeter Mac. The runner:

* verifies the frozen golden set and prompt;
* verifies all locally installed model digests;
* selects each model in .env;
* restarts Ollama and clears the database;
* warms the model with invented text and clears the warm-up row;
* runs all 195 golden tickets sequentially;
* validates every result against the service logs; and
* creates the three-model comparison report.

Examples:
    python3 scripts/run_accuracy_suite.py
    python3 scripts/run_accuracy_suite.py --resume
    python3 scripts/run_accuracy_suite.py --dry-run
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import shlex
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
LOCK_PATH = REPO / "models" / "models.lock.json"
GOLDEN_PATH = REPO / "golden" / "golden_set.csv"
RESULTS_DIR = REPO / "results" / "accuracy"
SERVICE_LOG_DIR = REPO / "logs" / "service"
FREEZE_TAG = "prediction-freeze"
ACTIVE_MODELS = (
    "qwen2.5:0.5b",
    "llama3.2:1b-instruct-q4_K_M",
    "qwen2.5:7b",
)
FIXED_SETTINGS = {
    "NUM_CTX": "4096",
    "TEMPERATURE": "0",
    "SEED": "42",
    "OLLAMA_TIMEOUT_S": "600",
    "OLLAMA_NUM_PARALLEL": "1",
    "OLLAMA_MAX_LOADED_MODELS": "1",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--models",
        nargs="+",
        choices=ACTIVE_MODELS,
        default=list(ACTIVE_MODELS),
        help="Models to run in order (default: all three)",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Continue the newest incomplete run and skip complete validated runs",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate frozen inputs and print the plan without changing Docker or .env",
    )
    return parser.parse_args()


def model_slug(model: str) -> str:
    return model.replace(":", "-").replace("/", "-")


def run(
    command: list[str],
    *,
    capture: bool = False,
    allowed_returncodes: tuple[int, ...] = (0,),
) -> subprocess.CompletedProcess[str]:
    print("+ " + " ".join(shlex.quote(part) for part in command), flush=True)
    result = subprocess.run(
        command,
        cwd=REPO,
        text=True,
        capture_output=capture,
        check=False,
    )
    if result.returncode not in allowed_returncodes:
        if capture:
            if result.stdout:
                print(result.stdout, end="")
            if result.stderr:
                print(result.stderr, end="", file=sys.stderr)
        raise RuntimeError(
            f"Command failed with exit code {result.returncode}: "
            + " ".join(shlex.quote(part) for part in command)
        )
    return result


def require_confirmation() -> None:
    try:
        answer = input(
            "Confirm JMeter and all other traffic are stopped, then type ACCURACY: "
        ).strip()
    except (EOFError, KeyboardInterrupt):
        raise SystemExit("Stopped before changing the SUT.")
    if answer != "ACCURACY":
        raise SystemExit("Expected ACCURACY; stopped before changing the SUT.")


def load_lock() -> dict[str, str]:
    try:
        lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Could not read {LOCK_PATH}: {exc}") from exc
    locked = {
        str(item.get("tag")): str(item.get("digest"))
        for item in lock.get("models", [])
        if item.get("tag") and item.get("digest")
    }
    missing = [model for model in ACTIVE_MODELS if model not in locked]
    if missing:
        raise RuntimeError(f"Active models missing from the lock file: {', '.join(missing)}")
    return locked


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def frozen_golden_rows() -> set[str]:
    tag_check = run(
        ["git", "rev-parse", "--verify", "--quiet", f"refs/tags/{FREEZE_TAG}"],
        capture=True,
        allowed_returncodes=(0, 1),
    )
    if tag_check.returncode:
        raise RuntimeError(f"Required freeze tag does not exist: {FREEZE_TAG}")
    unchanged = run(
        [
            "git",
            "diff",
            "--quiet",
            FREEZE_TAG,
            "--",
            "golden/golden_set.csv",
            "service/prompts/classify_v1.txt",
        ],
        allowed_returncodes=(0, 1),
    )
    if unchanged.returncode:
        raise RuntimeError(
            "The golden set or classification prompt differs from prediction-freeze. "
            "Do not run official accuracy testing until this is resolved."
        )
    rows = read_csv(GOLDEN_PATH)
    row_ids = [row.get("row", "") for row in rows]
    if len(rows) != 195 or len(set(row_ids)) != 195 or any(not row_id for row_id in row_ids):
        raise RuntimeError(
            f"Expected 195 unique frozen golden rows in {GOLDEN_PATH}; found {len(rows)}."
        )
    return set(row_ids)


def read_env() -> tuple[list[str], dict[str, str]]:
    path = REPO / ".env"
    if not path.is_file():
        raise RuntimeError(f"Missing {path}. Copy .env.example to .env first.")
    lines = path.read_text(encoding="utf-8").splitlines()
    values: dict[str, str] = {}
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        values[key.strip()] = value.strip()
    wrong = {
        key: (values.get(key), expected)
        for key, expected in FIXED_SETTINGS.items()
        if values.get(key) != expected
    }
    if wrong:
        details = ", ".join(
            f"{key}={actual!r} (expected {expected!r})"
            for key, (actual, expected) in wrong.items()
        )
        raise RuntimeError(f".env has non-frozen settings: {details}")
    return lines, values


def select_model(model: str) -> None:
    path = REPO / ".env"
    lines, _ = read_env()
    updated: list[str] = []
    replaced = False
    for line in lines:
        if line.strip().startswith("MODEL="):
            if not replaced:
                updated.append(f"MODEL={model}")
                replaced = True
            continue
        updated.append(line)
    if not replaced:
        updated.append(f"MODEL={model}")
    path.write_text("\n".join(updated) + "\n", encoding="utf-8")
    print(f"Selected MODEL={model} in .env")


def http_json(url: str, body: dict | None = None, timeout: int = 30) -> tuple[int, dict]:
    request = urllib.request.Request(
        url,
        data=json.dumps(body).encode() if body is not None else None,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status, json.load(response)
    except urllib.error.HTTPError as exc:
        return exc.code, {"detail": exc.read().decode(errors="replace")[:300]}


def wait_for_health(model: str, digest: str, timeout_s: int = 180) -> dict:
    deadline = time.monotonic() + timeout_s
    last_error = "service did not respond"
    while time.monotonic() < deadline:
        try:
            status, health = http_json("http://localhost:8000/health", timeout=5)
            if (
                status == 200
                and health.get("status") == "ok"
                and health.get("model") == model
                and health.get("model_digest") == digest
            ):
                return health
            last_error = f"health={health}"
        except (OSError, urllib.error.URLError, json.JSONDecodeError) as exc:
            last_error = str(exc)
        time.sleep(2)
    raise RuntimeError(
        f"SUT did not become healthy with model={model} digest={digest}: {last_error}"
    )


def remove_database_volume() -> None:
    run(
        ["docker", "volume", "rm", "triage_triage-data"],
        allowed_returncodes=(0, 1),
    )


def prepare_model(model: str, digest: str) -> None:
    select_model(model)
    run(["docker", "compose", "down"])
    remove_database_volume()
    run(["docker", "compose", "up", "-d"])
    health = wait_for_health(model, digest)
    print(f"Frozen target verified: {health['model']} {health['model_digest']}")

    parallel = run(
        ["docker", "compose", "exec", "-T", "ollama", "printenv", "OLLAMA_NUM_PARALLEL"],
        capture=True,
    ).stdout.strip()
    if parallel != "1":
        raise RuntimeError(f"OLLAMA_NUM_PARALLEL is {parallel!r}; expected '1'.")

    status, body = http_json(
        "http://localhost:8000/tickets",
        {
            "narrative": (
                "Synthetic accuracy warm-up ticket. It is invented and is not part of "
                "the golden set."
            )
        },
        timeout=900,
    )
    if status != 200:
        raise RuntimeError(f"Warm-up failed with HTTP {status}: {body}")

    ollama_ps = run(
        ["docker", "compose", "exec", "-T", "ollama", "ollama", "ps"],
        capture=True,
    ).stdout
    print(ollama_ps, end="")
    if model not in ollama_ps or "100% CPU" not in ollama_ps:
        raise RuntimeError(
            "ollama ps did not confirm the expected model on 100% CPU. "
            "Do not continue with official accuracy testing."
        )

    run(["docker", "compose", "stop", "triage"])
    run(["docker", "compose", "rm", "-f", "triage"])
    remove_database_volume()
    run(["docker", "compose", "up", "-d", "triage"])
    wait_for_health(model, digest)
    print("Warm-up row cleared; measured database is empty and Ollama remains loaded.")


def result_candidates(model: str) -> list[Path]:
    return sorted(RESULTS_DIR.glob(f"*_{model_slug(model)}.csv"))


def validate_result(
    path: Path,
    model: str,
    digest: str,
    golden_rows: set[str],
    *,
    require_complete: bool,
) -> list[dict[str, str]]:
    rows = read_csv(path)
    row_ids = [row.get("row", "") for row in rows]
    if len(set(row_ids)) != len(row_ids):
        raise RuntimeError(f"Accuracy result contains duplicate golden rows: {path}")
    unexpected = set(row_ids) - golden_rows
    if unexpected:
        raise RuntimeError(f"Accuracy result contains non-golden rows {sorted(unexpected)}: {path}")
    if require_complete and set(row_ids) != golden_rows:
        raise RuntimeError(
            f"Accuracy run is incomplete: {len(rows)}/195 rows in {path.relative_to(REPO)}"
        )
    for row in rows:
        if row.get("model") != model:
            raise RuntimeError(
                f"Mixed or wrong model in {path}: expected {model}, got {row.get('model')}"
            )
        if row.get("model_digest") != digest:
            raise RuntimeError(
                f"Wrong digest in {path}: expected {digest}, got {row.get('model_digest')}"
            )
        if not row.get("request_id"):
            raise RuntimeError(f"Missing request ID in accuracy result: {path}")
    return rows


def validate_service_evidence(rows: list[dict[str, str]], result_path: Path) -> None:
    wanted = {row["request_id"]: row for row in rows}
    found: dict[str, dict] = {}
    for path in sorted(SERVICE_LOG_DIR.glob("service-*.jsonl")):
        with path.open(encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                try:
                    record = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise RuntimeError(f"Invalid JSON in {path}:{line_number}: {exc}") from exc
                request_id = record.get("request_id")
                if request_id in wanted:
                    found[request_id] = record
    missing = set(wanted) - set(found)
    if missing:
        raise RuntimeError(
            f"Service logs are missing {len(missing)} accuracy request IDs for "
            f"{result_path.relative_to(REPO)}."
        )
    mismatches = [
        request_id
        for request_id, result_row in wanted.items()
        if str(found[request_id].get("status")) != result_row.get("status")
    ]
    if mismatches:
        raise RuntimeError(
            f"Service/accuracy status mismatch for {len(mismatches)} request IDs."
        )
    print(f"Service evidence verified: {len(rows)}/{len(rows)} request IDs matched.")


def find_resume_result(
    model: str, digest: str, golden_rows: set[str]
) -> tuple[Path | None, bool]:
    candidates = result_candidates(model)
    if not candidates:
        return None, False
    newest = candidates[-1]
    rows = validate_result(
        newest,
        model,
        digest,
        golden_rows,
        require_complete=False,
    )
    return newest, len(rows) == len(golden_rows)


def run_accuracy(model: str, resume_path: Path | None) -> Path:
    before = set(result_candidates(model))
    command = [sys.executable, str(REPO / "scripts" / "accuracy_test.py")]
    if resume_path is not None:
        command.extend(["--resume", str(resume_path)])
    run(command)
    if resume_path is not None:
        return resume_path
    created = set(result_candidates(model)) - before
    if len(created) != 1:
        raise RuntimeError(
            f"Expected one new accuracy CSV for {model}; found {len(created)}."
        )
    return created.pop()


def ensure_report(result_path: Path) -> None:
    report_path = result_path.with_suffix(".md")
    if report_path.is_file() and report_path.stat().st_size > 0:
        return
    run(
        [
            sys.executable,
            str(REPO / "scripts" / "accuracy_test.py"),
            "--report",
            str(result_path),
        ]
    )


def main() -> int:
    args = parse_args()
    locked = load_lock()
    golden_rows = frozen_golden_rows()

    print(f"Freeze tag:   {FREEZE_TAG}")
    print(f"Golden set:   {len(golden_rows)} tickets")
    print(f"Models:       {', '.join(args.models)}")
    print(f"Total calls:  {len(golden_rows) * len(args.models)} sequential golden requests")

    if args.dry_run:
        for number, model in enumerate(args.models, start=1):
            print(f"  {number}. {model} digest={locked[model]}")
        print("Dry run only: Docker, .env and result files were not changed or checked.")
        return 0

    read_env()
    require_confirmation()
    run(["docker", "compose", "up", "-d", "ollama"])
    run(
        [sys.executable, str(REPO / "scripts" / "pull_models.py"), "--check"]
    )

    completed_results: list[Path] = []
    for number, model in enumerate(args.models, start=1):
        digest = locked[model]
        resume_path: Path | None = None
        if args.resume:
            resume_path, complete = find_resume_result(model, digest, golden_rows)
            if resume_path is not None and complete:
                rows = validate_result(
                    resume_path,
                    model,
                    digest,
                    golden_rows,
                    require_complete=True,
                )
                validate_service_evidence(rows, resume_path)
                ensure_report(resume_path)
                print(
                    f"\n[{number}/{len(args.models)}] {model}: skipped complete run "
                    f"{resume_path.relative_to(REPO)}"
                )
                completed_results.append(resume_path)
                continue

        print(f"\n[{number}/{len(args.models)}] Preparing {model}")
        if resume_path is not None:
            existing_rows = read_csv(resume_path)
            print(
                f"Resuming {resume_path.relative_to(REPO)} "
                f"from {len(existing_rows)}/195 tickets."
            )
        prepare_model(model, digest)
        result_path = run_accuracy(model, resume_path)
        rows = validate_result(
            result_path,
            model,
            digest,
            golden_rows,
            require_complete=True,
        )
        validate_service_evidence(rows, result_path)
        ensure_report(result_path)
        completed_results.append(result_path)
        print(f"Completed and validated: {result_path.relative_to(REPO)}")

    comparison_command = [
        sys.executable,
        str(REPO / "scripts" / "accuracy_compare.py"),
        *(str(path) for path in completed_results),
    ]
    run(comparison_command)
    print("\nAccuracy suite complete. Preserve the evidence with:")
    print("  git add results/accuracy logs/service")
    print('  git commit -m "Add official three-model accuracy evidence"')
    print("  git push")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1) from None
