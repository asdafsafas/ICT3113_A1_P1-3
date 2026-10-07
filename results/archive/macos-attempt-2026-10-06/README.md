# Archived Mac load-test attempt — 2026-10-06

This directory preserves the first `qwen2.5:0.5b` load-test attempt conducted
across the two Macs. It was retired before the clean Windows restart because the
required per-run Docker/Ollama resource-statistics CSV files were not captured or
committed.

Contents include:

- Raw JMeter JTL files and JMeter logs.
- Dedicated service logs extracted by request ID.
- Invalid and superseded attempts retained for traceability.
- The final `RUNS.md` snapshot from the Mac attempt.
- A snapshot of the source daily service log.

These files are recoverable historical evidence, not official Windows results.
Do not pass this archive to `scripts/summarise_jtl.py`; official summaries should
read only `results/load/`.
