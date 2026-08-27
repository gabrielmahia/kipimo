#!/usr/bin/env python3
"""Generate a kipimo predictions file from any OpenAI-compatible endpoint.

kipimo itself never calls a model (so the harness stays model-agnostic and
key-free). This *example* shows the other half: how to produce a predictions
file from an open-weight model — Kimi, GLM, DeepSeek, or anything served via an
OpenAI-compatible API (vLLM, SGLang, Ollama, or a hosted endpoint) — so the
"can an open, self-hostable model serve Swahili?" question becomes testable
rather than rhetorical.

Why this matters for East Africa deployment
-------------------------------------------
The models that can actually be deployed under data-sovereignty constraints are
open-weight and self-hostable — you run them on your own infrastructure and your
data never leaves it. This script targets exactly that path: point it at a local
or self-hosted endpoint and measure whether the open option is good enough,
instead of assuming only a frontier closed API will do.

Usage
-----
    # 1. Serve an open-weight model with an OpenAI-compatible endpoint, e.g.:
    #      ollama serve            (then `ollama pull <model>`)
    #      or vLLM / SGLang for Kimi-K2.6 / K3-class weights
    #
    # 2. Point this script at it (OpenAI-compatible convention):
    export KIPIMO_BASE_URL="http://localhost:11434/v1"   # Ollama example
    export KIPIMO_API_KEY="not-needed-for-local"
    export KIPIMO_MODEL="kimi-k2.6"                        # or any served id
    #
    # 3. Generate predictions, then score with kipimo:
    kipimo tasks > tasks.jsonl
    python examples/generate_predictions.py tasks.jsonl > preds.jsonl
    kipimo score preds.jsonl

This uses only the Python standard library — no SDK, no lock-in.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.request

SYSTEM = (
    "You are an assistant that routes Swahili user requests in an East African "
    "coordination system. Answer ONLY with what is asked — a server name, an "
    "English term, or a comma-separated list of sector names. No explanation."
)


def call_model(base_url: str, api_key: str, model: str, prompt: str) -> str:
    body = json.dumps({
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0,
        "max_tokens": 120,
    }).encode()
    req = urllib.request.Request(
        base_url.rstrip("/") + "/chat/completions",
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        data = json.load(r)
    return data["choices"][0]["message"]["content"].strip()


def parse_prediction(task_type: str, raw: str) -> list[str]:
    """Turn a raw model answer into the list shape kipimo scores."""
    raw = raw.strip().strip(".")
    if task_type == "cascade_routing":
        # comma/space separated sector names
        parts = [p.strip().lower() for p in raw.replace(";", ",").split(",")]
        return [p for p in parts if p]
    # server_routing / term_grounding: first token/line is the answer
    first = raw.splitlines()[0].strip() if raw else ""
    return [first] if first else []


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("usage: generate_predictions.py tasks.jsonl > preds.jsonl", file=sys.stderr)
        return 2
    base_url = os.environ.get("KIPIMO_BASE_URL")
    api_key = os.environ.get("KIPIMO_API_KEY", "not-needed")
    model = os.environ.get("KIPIMO_MODEL")
    if not base_url or not model:
        print("Set KIPIMO_BASE_URL and KIPIMO_MODEL (OpenAI-compatible endpoint).",
              file=sys.stderr)
        return 2

    with open(argv[1], encoding="utf-8") as f:
        tasks = [json.loads(line) for line in f if line.strip()]

    for t in tasks:
        try:
            raw = call_model(base_url, api_key, model, t["input"])
            pred = parse_prediction(t["type"], raw)
        except Exception as e:
            print(f"# {t['id']} failed: {e}", file=sys.stderr)
            pred = []
        print(json.dumps({"id": t["id"], "prediction": pred}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
