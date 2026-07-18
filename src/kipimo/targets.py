"""kipimo.targets — declarative registry of scorecard evaluation targets.

This module contains METADATA ONLY. kipimo never calls a model API: prediction
files are produced externally (see examples/generate_predictions.py for one
stdlib-only pattern) and scored with `kipimo score`. The registry exists so
that published scorecards name targets consistently and so that the
deployment tier that actually matters for East Africa — small distilled
open-weight models runnable near the edge — is measured on equal terms with
frontier closed APIs.

Families:
    closed-api   — proprietary models reachable only via vendor API
    open-weight  — frontier-adjacent models with downloadable weights
    small-open   — <=32B-class open models; the realistic African deployment tier

`endpoint_env` names the environment variables an external generator is
expected to read (OpenAI-compatible convention). Nothing here reads them.
"""

from __future__ import annotations

FAMILIES = ("closed-api", "open-weight", "small-open")

TARGETS: list[dict] = [
    # --- closed APIs (reference ceiling) ---
    {
        "id": "claude-fable-5",
        "label": "Claude Fable 5",
        "family": "closed-api",
        "params_b": None,
        "endpoint_env": ["ANTHROPIC_API_KEY"],
        "notes": "reference frontier closed model",
    },
    {
        "id": "gpt-5.6",
        "label": "GPT-5.6",
        "family": "closed-api",
        "params_b": None,
        "endpoint_env": ["OPENAI_API_KEY"],
        "notes": "reference frontier closed model",
    },
    # --- open weights (frontier-adjacent, downloadable) ---
    {
        "id": "kimi-k3",
        "label": "Kimi K3 (Moonshot)",
        "family": "open-weight",
        "params_b": 2800,
        "endpoint_env": ["KIPIMO_BASE_URL", "KIPIMO_API_KEY"],
        "notes": "weights public from 2026-07-27; MoE",
    },
    {
        "id": "glm-5.2",
        "label": "GLM 5.2 (Zhipu)",
        "family": "open-weight",
        "params_b": None,
        "endpoint_env": ["KIPIMO_BASE_URL", "KIPIMO_API_KEY"],
        "notes": "leads open-weight intelligence indices at time of listing",
    },
    {
        "id": "deepseek-v4-pro",
        "label": "DeepSeek V4 Pro",
        "family": "open-weight",
        "params_b": None,
        "endpoint_env": ["KIPIMO_BASE_URL", "KIPIMO_API_KEY"],
        "notes": "measurable regional install base (11-14% share in four African markets)",
    },
    {
        "id": "nemotron-3-ultra",
        "label": "Nemotron 3 Ultra (NVIDIA)",
        "family": "open-weight",
        "params_b": None,
        "endpoint_env": ["KIPIMO_BASE_URL", "KIPIMO_API_KEY"],
        "notes": "US open-weight entrant; ships with open data and recipes",
    },
    # --- small open (the deployment tier nobody measures) ---
    {
        "id": "qwen3-14b",
        "label": "Qwen3 14B",
        "family": "small-open",
        "params_b": 14,
        "endpoint_env": ["KIPIMO_BASE_URL", "KIPIMO_API_KEY"],
        "notes": "runnable on a single consumer GPU",
    },
    {
        "id": "llama-4-scout",
        "label": "Llama 4 Scout",
        "family": "small-open",
        "params_b": 17,
        "endpoint_env": ["KIPIMO_BASE_URL", "KIPIMO_API_KEY"],
        "notes": "active-parameter class; edge-adjacent",
    },
    {
        "id": "gemma-3-12b",
        "label": "Gemma 3 12B",
        "family": "small-open",
        "params_b": 12,
        "endpoint_env": ["KIPIMO_BASE_URL", "KIPIMO_API_KEY"],
        "notes": "runnable on a single consumer GPU",
    },
]


def list_targets(family: str | None = None) -> list[dict]:
    """Return registered targets, optionally filtered by family."""
    if family is not None and family not in FAMILIES:
        raise ValueError(f"unknown family {family!r}; expected one of {FAMILIES}")
    return [t for t in TARGETS if family is None or t["family"] == family]


def get_target(target_id: str) -> dict:
    """Return a single target by id."""
    for t in TARGETS:
        if t["id"] == target_id:
            return t
    raise KeyError(f"unknown target {target_id!r}; run `kipimo targets` for the list")
