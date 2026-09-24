# Setup: running the system under test

The system under test is two Docker containers, started with one command:

- **triage**: our web service (`POST /tickets`, `GET /search`, `GET /stats`)
- **ollama**: the model server, **CPU only**

Docker gives everyone, Windows or Mac, the same setup. It also guarantees the client's no-GPU rule: Ollama inside Docker never uses a GPU unless explicitly configured to, which we never do.

## 1. Install

| | Windows | macOS |
|---|---|---|
| Docker | [Docker Desktop](https://www.docker.com/products/docker-desktop/) (uses WSL 2) | [Docker Desktop](https://www.docker.com/products/docker-desktop/) (Apple Silicon or Intel) |
| Python | 3.9+ from python.org (for the helper scripts) | 3.9+ (`python3`) |
| Git | [git-scm.com](https://git-scm.com) or GitHub Desktop | preinstalled, or `xcode-select --install` |

Start Docker Desktop and wait until it says it's running.

### Give Docker enough memory (important on Mac)

Docker Desktop limits how much CPU and RAM the containers get. Models need roughly: 1–2B → 2 GB, 3–4B → 4 GB, 7–8B → 6–8 GB.

- **Mac:** Docker Desktop → Settings → Resources. Set **CPUs** to the maximum and **Memory** to at least 8 GB (or as much as you can spare).
- **Windows:** Docker uses WSL 2 and by default can use most of your RAM. To cap or raise it, create `%UserProfile%\.wslconfig` (see Microsoft's WSL docs).

Whatever you set, **record it**: it's part of the test environment description.

### Don't run native Ollama at the same time

If you've installed the Ollama desktop app, **quit it** (tray/menu bar icon → Quit) before starting Docker. It uses the same port (11434), and the native app **uses your GPU** (NVIDIA on Windows, Metal on Mac), which the client's rules don't allow.

## 2. First run

```bash
git clone https://github.com/asdafsafas/ICT3113_A1_P1-3.git
cd ICT3113_A1_P1-3

cp .env.example .env              # Windows PowerShell: copy .env.example .env
# edit .env: set MODEL to one of the models in models/candidates.txt

docker compose up -d --build      # first time downloads ~1 GB of images
python scripts/pull_models.py     # pulls the candidate models, writes models/models.lock.json
```

On Mac, use `python3` instead of `python`.

Check it works:

```bash
curl http://localhost:8000/health
# {"status":"ok","model":"qwen2.5:1.5b","model_digest":"...", ...}
```

`"status": "model_missing"` means the model in `.env` hasn't been pulled yet. Run `pull_models.py` or check the spelling of the tag.

> **Don't test with the golden-set tickets** (rows 3000–3199) until the golden set is frozen. To try the service, write your own made-up complaint:
>
> ```bash
> curl -X POST http://localhost:8000/tickets -H "Content-Type: application/json" \
>      -d '{"narrative": "A debt collector keeps calling me about a bill I already paid."}'
> ```

## 3. Confirm it's CPU only

While a model is loaded (just after a request):

```bash
docker compose exec ollama ollama ps
# NAME           ID              SIZE      PROCESSOR    ...
# qwen2.5:1.5b   <id>            ...       100% CPU     ...
```

The PROCESSOR column must say **100% CPU**. Screenshot this for the test environment slide.

## 4. Everyday commands

| Task | Command |
|---|---|
| Start | `docker compose up -d` |
| Stop | `docker compose down` |
| Switch model | edit `MODEL` in `.env`, then `docker compose up -d triage` |
| See service output | `docker compose logs -f triage` |
| Check model pins | `python scripts/pull_models.py --check` |
| Empty the ticket database | `docker compose down` then `docker volume rm triage_triage-data`, then start again |
| Rebuild after code changes | `docker compose up -d --build` |

The request logs are written to `logs/service/service-YYYY-MM-DD.jsonl` on your machine. These are evidence: **commit the logs from every run you report.**

## One machine for all official runs

Docker makes the setup identical, **not the speed**. A MacBook Air, a gaming PC and a lab machine give very different latencies. So:

1. **Pick one system-under-test (SUT) machine** for every benchmark and accuracy run you report. Ideally it's plugged in, has the most RAM, and isn't used for anything else during runs.
2. **Record its hardware:** CPU model and core count, RAM, OS, Docker Desktop resource limits, and the Ollama and service versions. Run `docker info` and `docker compose exec ollama ollama --version`.
3. **The load generator (JMeter) runs on a different machine** on the same network (see [load-testing.md](load-testing.md)).

Everyone else can run the stack on their own laptop for development and trying things out.

## Troubleshooting

| Problem | Fix |
|---|---|
| `port is already allocated` on 11434 | Native Ollama is running. Quit it. |
| `port is already allocated` on 8000 | Something else uses port 8000. Stop it, or change the left side of `"8000:8000"` in `docker-compose.yml`. |
| `MODEL is not set` in `docker compose logs triage` | You didn't create `.env`, or `MODEL=` is empty. |
| Requests fail with 502 and "model ... not found" | Pull the model: `python scripts/pull_models.py`. |
| Very slow first request | The model is being loaded into memory (see `ollama_load_ms` in the log). Send one warm-up request before any measurement. |
| Ollama crashes or the container restarts with large models | Not enough memory for Docker. Raise it in Docker Desktop → Resources. |
| Mac: `python` not found | Use `python3`. |
