"""DEMO: generate a kipimo predictions file from any OpenAI-compatible endpoint.

kipimo itself never calls a model — this optional script lives outside the
package so the scorer stays neutral. It works identically for closed APIs,
hosted open-weight models, or a llama.cpp/vLLM server on your own machine:

    export KIPIMO_BASE_URL=https://openrouter.ai/api/v1   # or http://localhost:8000/v1
    export KIPIMO_API_KEY=sk-...                          # omit for local servers
    kipimo tasks > tasks.jsonl
    python examples/generate_predictions.py tasks.jsonl moonshotai/kimi-k3 > preds.jsonl
    kipimo score preds.jsonl

Stdlib only. DEMO quality: no retries, no batching, sequential calls.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.request

PROMPT = (
    "You are being evaluated on East Africa coordination tasks. Answer in the "
    "exact minimal form requested. If the task asks for server names or terms, "
    "reply with a JSON list of strings and nothing else.\n\nTask ({type}):\n{prompt}"
)


def call(base: str, key: str, model: str, content: str) -> list[str]:
    req = urllib.request.Request(
        base.rstrip("/") + "/chat/completions",
        data=json.dumps({
            "model": model,
            "messages": [{"role": "user", "content": content}],
            "temperature": 0,
        }).encode(),
        headers={
            "Content-Type": "application/json",
            **({"Authorization": f"Bearer {key}"} if key else {}),
        },
    )
    with urllib.request.urlopen(req, timeout=120) as r:
        text = json.loads(r.read())["choices"][0]["message"]["content"].strip()
    try:
        out = json.loads(text)
        return [str(x) for x in out] if isinstance(out, list) else [str(out)]
    except (json.JSONDecodeError, ValueError):
        return [text]


def main() -> int:
    if len(sys.argv) != 3:
        print(__doc__, file=sys.stderr)
        return 2
    tasks_path, model = sys.argv[1], sys.argv[2]
    base = os.environ.get("KIPIMO_BASE_URL", "")
    key = os.environ.get("KIPIMO_API_KEY", "")
    if not base:
        print("set KIPIMO_BASE_URL (OpenAI-compatible endpoint)", file=sys.stderr)
        return 2
    with open(tasks_path, encoding="utf-8") as f:
        tasks = [json.loads(x) for x in f if x.strip()]
    for i, t in enumerate(tasks, 1):
        pred = call(base, key, model, PROMPT.format(type=t["type"], prompt=t["prompt"]))
        print(json.dumps({"id": t["id"], "prediction": pred}, ensure_ascii=False))
        print(f"[{i}/{len(tasks)}] {t['id']}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
