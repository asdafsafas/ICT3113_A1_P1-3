"""Service settings, read once from environment variables (set them in .env)."""

import os
from pathlib import Path

CATEGORIES = [
    "Credit reporting",
    "Debt collection",
    "Mortgage",
    "Credit card",
    "Bank account or service",
    "Consumer loan",
    "Money transfer or service",
]

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://ollama:11434").rstrip("/")
MODEL = os.environ.get("MODEL", "")
PROMPT_FILE = Path(os.environ.get("PROMPT_FILE", "/app/prompts/classify_v1.txt"))

# Generation options sent with every request. They are logged so every run is reproducible.
OLLAMA_TIMEOUT_S = float(os.environ.get("OLLAMA_TIMEOUT_S", "600"))
NUM_CTX = int(os.environ.get("NUM_CTX", "4096"))
TEMPERATURE = float(os.environ.get("TEMPERATURE", "0"))
SEED = int(os.environ.get("SEED", "42"))

DB_PATH = Path(os.environ.get("DB_PATH", "/data/tickets.db"))
LOG_DIR = Path(os.environ.get("LOG_DIR", "/logs"))
