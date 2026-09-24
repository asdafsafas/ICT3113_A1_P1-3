"""Calls Ollama to classify one narrative. Baseline: one synchronous HTTP call per ticket, no caching."""

import json

import httpx

from . import config


class ClassificationError(Exception):
    pass


# Constrains the model's reply to {"category": "<one of the seven>"} (Ollama structured outputs).
RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {"category": {"type": "string", "enum": config.CATEGORIES}},
    "required": ["category"],
}

_client = httpx.Client(base_url=config.OLLAMA_URL, timeout=config.OLLAMA_TIMEOUT_S)
_prompt_template = None
_digest = None


def prompt_template():
    global _prompt_template
    if _prompt_template is None:
        _prompt_template = config.PROMPT_FILE.read_text(encoding="utf-8")
    return _prompt_template


def model_digest():
    """Digest of the configured model as installed in Ollama (None if not pulled yet)."""
    global _digest
    if _digest is None:
        try:
            tags = _client.get("/api/tags", timeout=10).json()
        except (httpx.HTTPError, ValueError):
            return None
        for m in tags.get("models", []):
            if m.get("name") == config.MODEL or m.get("model") == config.MODEL:
                _digest = m.get("digest")
    return _digest


def ns_to_ms(ns):
    return round(ns / 1e6, 1) if ns is not None else None


def classify(narrative):
    """Returns (category, stats) or raises ClassificationError."""
    body = {
        "model": config.MODEL,
        "prompt": prompt_template().replace("{narrative}", narrative),
        "stream": False,
        "format": RESPONSE_SCHEMA,
        "options": {"temperature": config.TEMPERATURE, "seed": config.SEED, "num_ctx": config.NUM_CTX},
    }
    try:
        resp = _client.post("/api/generate", json=body)
    except httpx.HTTPError as e:
        raise ClassificationError(f"ollama request failed: {type(e).__name__}: {e}") from e
    if resp.status_code != 200:
        raise ClassificationError(f"ollama returned {resp.status_code}: {resp.text[:300]}")

    data = resp.json()
    stats = {
        "ollama_total_ms": ns_to_ms(data.get("total_duration")),
        "ollama_load_ms": ns_to_ms(data.get("load_duration")),
        "ollama_prompt_eval_ms": ns_to_ms(data.get("prompt_eval_duration")),
        "ollama_eval_ms": ns_to_ms(data.get("eval_duration")),
        "prompt_tokens": data.get("prompt_eval_count"),
        "output_tokens": data.get("eval_count"),
    }
    raw = data.get("response", "")
    try:
        category = json.loads(raw)["category"]
    except (ValueError, KeyError, TypeError):
        raise ClassificationError(f"unparseable model output: {raw[:300]!r}")
    if category not in config.CATEGORIES:
        raise ClassificationError(f"model returned unknown category: {category!r}")
    return category, stats
