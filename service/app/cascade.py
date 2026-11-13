"""Assignment 2 cascade: small model first, then a rule decides whether to escalate to the large model.

The rule only sees what is known when the ticket arrives: the small model's PREDICTED category,
the narrative itself, and (for the agreement rule) a second small model's predicted category.
"""

import time

from . import classifier, config

# Summed across every model call of one ticket, so latency_ms - ollama_total_ms is still queue wait + overhead.
SUMMED = ("ollama_total_ms", "ollama_load_ms", "ollama_prompt_eval_ms", "ollama_eval_ms",
          "prompt_tokens", "output_tokens")


def accept(small_category, narrative, agree_category=None):
    """True to accept the small model's answer, False to escalate. Pure function of the configured rule."""
    if config.RULE == "category":
        return small_category in config.ACCEPT_CATEGORIES
    if config.RULE == "length":
        return len(narrative) <= config.LENGTH_MAX_CHARS
    if config.RULE == "agreement":
        if agree_category != small_category:
            return False
        return not config.ACCEPT_CATEGORIES or small_category in config.ACCEPT_CATEGORIES
    raise RuntimeError(f"unknown RULE {config.RULE!r}")


def _call(narrative, model, role, calls):
    start = time.perf_counter()
    try:
        category, stats = classifier.classify(narrative, model)
    except classifier.ClassificationError as e:
        calls.append({"role": role, "model": model, "error": str(e),
                      "call_ms": round((time.perf_counter() - start) * 1000, 1)})
        raise
    calls.append({"role": role, "model": model, "category": category,
                  "call_ms": round((time.perf_counter() - start) * 1000, 1), **stats})
    return category


def run(narrative, log):
    """Classify through the cascade. Fills `log` with what the service log needs, returns (category, final_model)."""
    calls = []
    log["calls"] = calls
    log["rule"] = config.RULE
    log["rule_setting"] = config.RULE_SETTING or None
    try:
        if config.RULE == "length":
            # Brief, method 4: short tickets go to the small model, long tickets STRAIGHT to the large model.
            # The decision needs only the narrative, so long tickets never pay for a small-model call.
            escalated = not accept(None, narrative)
            log["escalated"] = escalated
            log["routed_directly"] = escalated
            if escalated:
                category, final_model = _call(narrative, config.LARGE_MODEL, "large", calls), config.LARGE_MODEL
            else:
                category = _call(narrative, config.SMALL_MODEL, "small", calls)
                log["small_category"] = category
                final_model = config.SMALL_MODEL
        else:
            small = _call(narrative, config.SMALL_MODEL, "small", calls)
            agree = _call(narrative, config.AGREE_MODEL, "agree", calls) if config.RULE == "agreement" else None
            log["small_category"] = small
            if agree is not None:
                log["agree_category"] = agree
            escalated = not accept(small, narrative, agree)
            log["escalated"] = escalated
            if escalated:
                category, final_model = _call(narrative, config.LARGE_MODEL, "large", calls), config.LARGE_MODEL
            else:
                category, final_model = small, config.SMALL_MODEL
    finally:
        for key in SUMMED:
            values = [c[key] for c in calls if c.get(key) is not None]
            log[key] = round(sum(values), 1) if values else None
        log["model_calls"] = len(calls)
    log["final_model"] = final_model
    return category, final_model
