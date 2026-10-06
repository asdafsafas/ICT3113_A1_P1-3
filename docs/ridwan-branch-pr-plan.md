# Ridwan Branch Pull Request Plan

This checklist prepares `ridwan-branch` for review and merge into `main`. Merging the pull request does not start official testing; the benchmark stop gate in [actual-jmeter-test.md](actual-jmeter-test.md) still applies.

## Phase 1 Sync with main

- [x] Fetch the latest remote branches.
- [x] Merge `origin/main` into `ridwan-branch`.
- [x] Preserve the golden-set, workload, requirements and prediction work already merged into `main`.

## Phase 2 Align the official JMeter procedure

- [x] Use the final average load: 1.45 tickets/min and 2.9 searches/min.
- [x] Use the final peak load: 1.73 tickets/min and 3.5 searches/min.
- [x] Use the fixed beyond-peak check: 3.5 tickets/min and 7 searches/min.
- [x] Use 10-minute standard runs, a consistent 5-minute drain and three runs per configuration.
- [x] Align R1, R2 and R3 with `planning/requirements.md`.
- [x] Align filenames, reconciliation examples and the 7B stress procedure.

## Phase 3 Align data, models and ownership

- [x] Keep the 800 non-golden tickets from rows 3200-3999 as JMeter traffic.
- [x] Document the CSV-to-TSV export command.
- [x] Replace the removed 1.5B model in setup examples.
- [x] Document the four selected model tags and their comparison rationale.
- [x] Set the documented Ollama version to 0.35.1.
- [x] Assign JMeter work to Ridwan, model selection to Tze Han and accuracy testing to Zong Han.
- [ ] Generate and commit `models/models.lock.json` on the system-under-test machine.

## Phase 4 Validate and open the pull request

- [ ] Check Python syntax and protocol consistency.
- [ ] Validate the 800-ticket CSV and JMeter XML.
- [ ] Scan for stale workload rates and removed candidate tags.
- [ ] Push `ridwan-branch`.
- [ ] Open a pull request into `main` with verification and pre-benchmark blockers recorded.

## Required after merge and before official benchmarks

- [ ] Commit the exact model digests from the system-under-test machine.
- [ ] Record the freeze commit or tag.
- [ ] Pull that exact frozen revision on both Macs.
- [ ] Confirm `OLLAMA_NUM_PARALLEL=1`, CPU-only inference, the active model digest and the network details.
- [ ] Export `loadtest/data/tickets.tsv` and complete the stop gate before the first measured run.
