# Adaptive Stress Test Summary

Model: `qwen2.5:7b`

## Predeclared stop rule

A rate is classified as overloaded when POST errors exceed 1%, or when material queue growth is accompanied by a completion-rate shortfall or late-half latency growth, or when at least 15% of offered POSTs remain in flight at the end of the active period. The first overloaded rate is repeated before reporting a bracket.

## Results

| Rate /min | Attempt | Result | POST p50 s | p95 s | p99 s | Errors % | Backlog mid/end | Last-half throughput /min |
|---:|---:|---|---:|---:|---:|---:|---:|---:|
| 20.00 | 1 | SUSTAINED | 9.05 | 21.83 | 25.27 | 0.00 | 1/4 | 20.80 |
| 22.00 | 1 | OVERLOADED | 16.21 | 31.90 | 38.47 | 0.00 | 8/12 | 21.60 |
| 22.00 | 2 | SUSTAINED | 25.33 | 43.97 | 46.55 | 0.00 | 10/7 | 22.40 |
| 24.00 | 1 | OVERLOADED | 26.62 | 53.82 | 64.13 | 0.00 | 15/24 | 23.00 |
| 24.00 | 2 | OVERLOADED | 34.01 | 71.66 | 75.02 | 0.00 | 13/27 | 22.80 |

## Conclusion

The measured sustainable mixed-load capacity is bracketed above 22 and at or below 24 classification requests per minute, with 7 searches per minute. The higher rate met the predeclared overload rule in two independent reset-and-warm attempts.

Each row is backed by a JTL, JMeter log, matched service JSONL, Docker statistics CSV, health snapshot and SUT audit log in this directory.
