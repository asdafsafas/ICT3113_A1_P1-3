# JMeter Run Log

This active register was reset on 2026-10-06 for the clean Windows test series.
The earlier Mac attempt is preserved outside the active results tree at
`results/archive/macos-attempt-2026-10-06/` and must not be included in official
summaries.

All timestamps use Singapore Time (SGT, UTC+08:00). Every official run must have
its JTL, JMeter log, matching service log and resource-statistics CSV before it is
marked valid.

| Date/time SGT | Model | POST/min | Search/min | Duration | Run | JTL file | Reconciled | Valid | Notes |
|---|---|---:|---:|---:|---:|---|---|---|---|

## Windows restart checklist

- [ ] Record the Windows load-generator and SUT environment details.
- [ ] Confirm the frozen commit, prompt, model tag and digest.
- [ ] Confirm `OLLAMA_NUM_PARALLEL=1` inside the running Ollama container.
- [ ] Confirm `loadtest/data/tickets.tsv` contains rows 3200–3999.
- [ ] Before every run, restart Ollama, warm it with invented text, clear the warm-up database row and start resource monitoring.
- [ ] After every run, retain the JTL, JMeter log, dedicated service log and matching `_stats.csv` file.
- [ ] Reconcile every JMeter sample before marking the run valid.
