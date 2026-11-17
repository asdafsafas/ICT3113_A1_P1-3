# Memory check: qwen2.5:7b + llama3.2:1b-instruct-q4_K_M

Checked 2026-11-17T03:31:33.170+00:00. Docker VM: 10 CPUs, 9.70 GiB. OLLAMA_MAX_LOADED_MODELS=2.

**Result: PASS: every model stayed loaded**

| Phase | Model | Client ms | Ollama load ms | Ollama total ms |
|---|---|---:|---:|---:|
| load | `qwen2.5:7b` | 8789.3 | 6611.6 | 8762.6 |
| load | `llama3.2:1b-instruct-q4_K_M` | 2385.3 | 1807.9 | 2377.2 |
| alternate 1 | `qwen2.5:7b` | 3009.9 | 0.9 | 3004.3 |
| alternate 1 | `llama3.2:1b-instruct-q4_K_M` | 773.0 | 5.1 | 767.8 |
| alternate 2 | `qwen2.5:7b` | 3918.5 | 0.9 | 3910.6 |
| alternate 2 | `llama3.2:1b-instruct-q4_K_M` | 1115.2 | 1.6 | 1110.8 |
| alternate 3 | `qwen2.5:7b` | 6870.2 | 2.3 | 6854.1 |
| alternate 3 | `llama3.2:1b-instruct-q4_K_M` | 456.6 | 1.4 | 450.6 |

A load time above 1000 ms on an alternating call means the model had been unloaded.

## `ollama ps` at the end

```
NAME                           ID              SIZE      PROCESSOR    CONTEXT    UNTIL               
qwen2.5:7b                     845dbda0ea48    5.1 GB    100% CPU     4096       29 minutes from now    
llama3.2:1b-instruct-q4_K_M    22bc6b92eb01    1.2 GB    100% CPU     4096       29 minutes from now
```

## `docker stats` at the end

```
triage-triage-1,0.22%,36.72MiB / 9.701GiB
triage-ollama-1,0.03%,6.078GiB / 9.701GiB
jobwise_nginx,0.00%,3.16MiB / 9.701GiB
jobwise_web,0.03%,162.2MiB / 9.701GiB
jobwise_db,3.60%,21.66MiB / 9.701GiB
jobwise_frontend,0.00%,104.2MiB / 9.701GiB
```
