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

DEPLOYMENT PROFILE (optional, per target)
-----------------------------------------
Accuracy alone cannot answer the question East African institutions actually
face, which is not "which model is best?" but "what is the cheapest model we
can run ourselves that clears the competence bar?" Targets may therefore carry:

    license        SPDX-ish string ("MIT", "Apache-2.0", "CC-BY-NC-4.0",
                   "proprietary", "custom") — governs whether self-hosting and
                   commercial/civic redeployment are even permitted
    self_hostable  bool — weights obtainable and runnable outside a vendor API
    hardware_tier  "edge" | "workstation" | "server" | "datacenter" | "api-only"
    offline_capable bool — can serve with no internet at inference time

Cost and latency are deliberately NOT stored here. Vendor prices change weekly
and vary by region; a number frozen in a registry is a number that quietly goes
wrong. Cost is supplied per-run by the operator (see kipimo.pareto) and latency
is measured by the harness. The registry holds only slow-moving facts.
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
        "license": "proprietary",
        "self_hostable": False,
        "hardware_tier": "api-only",
        "offline_capable": False,
    },
    {
        "id": "gpt-5.6",
        "label": "GPT-5.6",
        "family": "closed-api",
        "params_b": None,
        "endpoint_env": ["OPENAI_API_KEY"],
        "notes": "reference frontier closed model",
        "license": "proprietary",
        "self_hostable": False,
        "hardware_tier": "api-only",
        "offline_capable": False,
    },
    # --- open weights (frontier-adjacent, downloadable) ---
    {
        "id": "kimi-k2.6",
        "label": "Kimi K2.6 (Moonshot)",
        "family": "open-weight",
        "params_b": 1000,
        "endpoint_env": ["KIPIMO_BASE_URL", "KIPIMO_API_KEY"],
        "notes": "weights public (HF, ~900k downloads); 1T MoE; strong agentic/tool-use; self-hostable via vLLM/SGLang/Ollama",
        "license": "Modified-MIT",
        "self_hostable": True,
        "hardware_tier": "datacenter",
        "offline_capable": True,
    },
    {
        "id": "kimi-k3",
        "label": "Kimi K3 (Moonshot)",
        "family": "open-weight",
        "params_b": 2800,
        "endpoint_env": ["KIPIMO_BASE_URL", "KIPIMO_API_KEY"],
        "notes": "2.8T MoE, 104B active; weights PUBLIC on HF (moonshotai/Kimi-K3, native multimodal, 1M ctx) under the custom \"Kimi K3 License\" — read LICENSE before redistribution (NOT MIT/Apache); strong agentic/MCP scores make it a valid frontier reference",
        "license": "custom (Kimi K3 License)",
        "self_hostable": True,
        "hardware_tier": "datacenter",
        "offline_capable": True,
    },
    {
        "id": "glm-5.2",
        "label": "GLM 5.2 (Zhipu)",
        "family": "open-weight",
        "params_b": None,
        "endpoint_env": ["KIPIMO_BASE_URL", "KIPIMO_API_KEY"],
        "notes": "leads open-weight intelligence indices at time of listing",
        "license": "MIT",
        "self_hostable": True,
        "hardware_tier": "datacenter",
        "offline_capable": True,
    },
    {
        "id": "deepseek-v4-pro",
        "label": "DeepSeek V4 Pro",
        "family": "open-weight",
        "params_b": None,
        "endpoint_env": ["KIPIMO_BASE_URL", "KIPIMO_API_KEY"],
        "notes": "measurable regional install base (11-14% share in four African markets)",
        "license": "MIT (verify on repo)",
        "self_hostable": True,
        "hardware_tier": "datacenter",
        "offline_capable": True,
    },
    {
        "id": "nemotron-3-ultra",
        "label": "Nemotron 3 Ultra (NVIDIA)",
        "family": "open-weight",
        "params_b": None,
        "endpoint_env": ["KIPIMO_BASE_URL", "KIPIMO_API_KEY"],
        "notes": "US open-weight entrant; ships with open data and recipes",
        "license": "NVIDIA-Open-Model (verify)",
        "self_hostable": True,
        "hardware_tier": "datacenter",
        "offline_capable": True,
    },
    # --- small open (the deployment tier nobody measures) ---
    {
        "id": "qwen3-14b",
        "label": "Qwen3 14B",
        "family": "small-open",
        "params_b": 14,
        "endpoint_env": ["KIPIMO_BASE_URL", "KIPIMO_API_KEY"],
        "notes": "runnable on a single consumer GPU",
        "license": "Apache-2.0",
        "self_hostable": True,
        "hardware_tier": "workstation",
        "offline_capable": True,
    },
    {
        "id": "llama-4-scout",
        "label": "Llama 4 Scout",
        "family": "small-open",
        "params_b": 17,
        "endpoint_env": ["KIPIMO_BASE_URL", "KIPIMO_API_KEY"],
        "notes": "active-parameter class; edge-adjacent",
        "license": "Llama-4-Community",
        "self_hostable": True,
        "hardware_tier": "server",
        "offline_capable": True,
    },
    {
        "id": "gemma-3-12b",
        "label": "Gemma 3 12B",
        "family": "small-open",
        "params_b": 12,
        "endpoint_env": ["KIPIMO_BASE_URL", "KIPIMO_API_KEY"],
        "notes": "runnable on a single consumer GPU",
        "license": "Gemma-Terms",
        "self_hostable": True,
        "hardware_tier": "workstation",
        "offline_capable": True,
    },
    {
        "id": "tiny-aya-earth",
        "label": "Tiny Aya Earth (Cohere Labs)",
        "family": "small-open",
        "params_b": 3.35,
        "endpoint_env": ["KIPIMO_BASE_URL", "KIPIMO_API_KEY"],
        "notes": (
            "Cohere Labs Tiny Aya (Feb 2026), Earth variant tuned for West-Asian + "
            "African languages incl. Swahili; 70+ langs, 8K ctx, mobile/edge-runnable, "
            "CC-BY-NC-4.0. Sits between InkubaLM 0.4B and the ~12B tier. Verify exact "
            "HF repo id before use."
        ),
        "license": "CC-BY-NC-4.0",
        "self_hostable": True,
        "hardware_tier": "edge",
        "offline_capable": True,
    },
    {
        "id": "inkubalm-0.4b",
        "label": "InkubaLM 0.4B (Lelapa AI)",
        "family": "small-open",
        "params_b": 0.4,
        "endpoint_env": ["KIPIMO_BASE_URL", "KIPIMO_API_KEY"],
        "notes": (
            "African-built SLM (hf: lelapa/InkubaLM-0.4B) covering Swahili + "
            "isiZulu/Yoruba/Hausa/isiXhosa; MobileLLM-class, mobile/edge-runnable "
            "(community variants down to ~40M). License CC BY-NC 4.0 — evaluatable, "
            "non-commercial redistribution. The floor of the deployment tier this "
            "benchmark exists to measure."
        ),
        "license": "CC-BY-NC-4.0",
        "self_hostable": True,
        "hardware_tier": "edge",
        "offline_capable": True,
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
