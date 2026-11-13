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


# --- Assignment 2: cascade -------------------------------------------------------------------
# MODE=single (default) is the unchanged Assignment 1 behaviour: one call to MODEL per ticket.
# MODE=cascade: SMALL_MODEL classifies every ticket; RULE decides whether to accept that answer
# or escalate the ticket to LARGE_MODEL, whose answer is final. Every call uses the same prompt
# and the same generation options. Nothing is cached.
def _csv(name):
    return [v.strip() for v in os.environ.get(name, "").split(",") if v.strip()]


MODE = os.environ.get("MODE", "single").strip().lower()
SMALL_MODEL = os.environ.get("SMALL_MODEL", "").strip()
LARGE_MODEL = os.environ.get("LARGE_MODEL", "").strip()

# RULE is one of:
#   category   accept the small model's answer when its PREDICTED category is in ACCEPT_CATEGORIES
#   length     narratives of at most LENGTH_MAX_CHARS characters go to the small model; longer ones
#              go STRAIGHT to the large model (no small-model call), as in the brief's method 4
#   agreement  ask AGREE_MODEL too; accept when both small models give the same category
#              (optionally only when that shared category is in ACCEPT_CATEGORIES)
RULE = os.environ.get("RULE", "").strip().lower()
RULE_SETTING = os.environ.get("RULE_SETTING", "").strip()  # free label for logs, e.g. "A" or "B"
ACCEPT_CATEGORIES = _csv("ACCEPT_CATEGORIES")
LENGTH_MAX_CHARS = int(os.environ.get("LENGTH_MAX_CHARS", "0") or 0)
AGREE_MODEL = os.environ.get("AGREE_MODEL", "").strip()

RULES = ("category", "length", "agreement")


def validate():
    """Fail fast at startup on an inconsistent configuration."""
    if MODE == "single":
        if not MODEL:
            raise RuntimeError("MODEL is not set; copy .env.example to .env and choose a model")
        return
    if MODE != "cascade":
        raise RuntimeError(f"MODE must be 'single' or 'cascade', not {MODE!r}")
    if not SMALL_MODEL or not LARGE_MODEL:
        raise RuntimeError("MODE=cascade needs SMALL_MODEL and LARGE_MODEL")
    if RULE not in RULES:
        raise RuntimeError(f"RULE must be one of {RULES}, not {RULE!r}")
    unknown = [c for c in ACCEPT_CATEGORIES if c not in CATEGORIES]
    if unknown:
        raise RuntimeError(f"ACCEPT_CATEGORIES has unknown categories: {unknown}")
    if RULE == "category" and not ACCEPT_CATEGORIES:
        raise RuntimeError("RULE=category needs ACCEPT_CATEGORIES")
    if RULE == "length" and LENGTH_MAX_CHARS <= 0:
        raise RuntimeError("RULE=length needs LENGTH_MAX_CHARS > 0")
    if RULE == "agreement" and not AGREE_MODEL:
        raise RuntimeError("RULE=agreement needs AGREE_MODEL")


def models_in_use():
    """Every model this configuration calls, in call order."""
    if MODE == "single":
        return [MODEL]
    models = [SMALL_MODEL] + ([AGREE_MODEL] if RULE == "agreement" else []) + [LARGE_MODEL]
    return list(dict.fromkeys(models))


def config_label():
    """Name of the configuration, the same for every ticket (the caller can't tell which model answered)."""
    if MODE == "single":
        return MODEL
    setting = f"[{RULE_SETTING}]" if RULE_SETTING else ""
    return f"cascade:{SMALL_MODEL}>{LARGE_MODEL}:{RULE}{setting}"


def rule_description():
    if MODE == "single":
        return None
    d = {"rule": RULE, "setting": RULE_SETTING or None, "small_model": SMALL_MODEL, "large_model": LARGE_MODEL}
    if RULE in ("category", "agreement") and ACCEPT_CATEGORIES:
        d["accept_categories"] = ACCEPT_CATEGORIES
    if RULE == "length":
        d["length_max_chars"] = LENGTH_MAX_CHARS
    if RULE == "agreement":
        d["agree_model"] = AGREE_MODEL
    return d
