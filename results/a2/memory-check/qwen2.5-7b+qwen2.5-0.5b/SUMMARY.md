# Memory check: qwen2.5:7b + qwen2.5:0.5b

Checked 2026-11-17T03:32:10.538+00:00. Docker VM: 10 CPUs, 9.70 GiB. OLLAMA_MAX_LOADED_MODELS=2.

**Result: PASS: every model stayed loaded**

| Phase | Model | Client ms | Ollama load ms | Ollama total ms |
|---|---|---:|---:|---:|
| load | `qwen2.5:7b` | 11958.4 | 8394.4 | 11914.3 |
| load | `qwen2.5:0.5b` | 1589.9 | 1043.6 | 1583.1 |
| alternate 1 | `qwen2.5:7b` | 2374.1 | 1.0 | 2370.7 |
| alternate 1 | `qwen2.5:0.5b` | 575.6 | 0.7 | 567.6 |
| alternate 2 | `qwen2.5:7b` | 4830.4 | 1.9 | 4813.5 |
| alternate 2 | `qwen2.5:0.5b` | 958.6 | 1.6 | 953.8 |
| alternate 3 | `qwen2.5:7b` | 6459.2 | 1.0 | 6434.6 |
| alternate 3 | `qwen2.5:0.5b` | 318.6 | 4.4 | 311.8 |

A load time above 1000 ms on an alternating call means the model had been unloaded.

## `ollama ps` at the end

```
NAME            ID              SIZE      PROCESSOR    CONTEXT    UNTIL               
qwen2.5:0.5b    a8b0c5157701    628 MB    100% CPU     4096       29 minutes from now    
qwen2.5:7b      845dbda0ea48    5.1 GB    100% CPU     4096       29 minutes from now
```

## `docker stats` at the end

```
triage-triage-1,0.34%,36.72MiB / 9.701GiB
triage-ollama-1,6.45%,5.483GiB / 9.701GiB
jobwise_nginx,0.00%,0B / 0B
jobwise_web,0.04%,162MiB / 9.701GiB
jobwise_db,0.03%,20.94MiB / 9.701GiB
jobwise_frontend,0.00%,104.2MiB / 9.701GiB
```
