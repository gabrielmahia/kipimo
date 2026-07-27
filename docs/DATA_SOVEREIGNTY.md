# Data sovereignty and open-weight models

*Why kipimo measures the open-weight tier on equal terms with frontier APIs.*

## The constraint that shapes African AI deployment

An institution that holds citizens' health, land, or financial records often
cannot send that data to a foreign closed API — for legal, regulatory, or
sovereignty reasons. For that institution, the only deployable models are ones
whose **weights can be downloaded and run on infrastructure they control**, so
the data never leaves their perimeter.

This is not a preference. It is frequently a hard requirement, and it silently
excludes most frontier closed models from the deployment set.

## What changed in 2026

Open-weight models closed most of the capability gap for agentic, tool-using
work — the exact shape of MCP-server coordination:

- **Kimi K2.6** (Moonshot, open-weight, ~1T MoE) — publicly downloadable,
  self-hostable via vLLM / SGLang / Ollama, at a fraction of frontier API cost,
  and strong specifically at agentic tool use. Kimi K3 (2.8T) is announced with
  weights slated for public release; verify the checkpoint before relying on it.
- Other open-weight families (GLM, DeepSeek, Qwen) occupy the same tier.

For an East African deployment, this means the data-sovereignty option is no
longer a large capability sacrifice — *if* the open model is actually good enough
at the regional task. That "if" is an empirical question, not a marketing one.

## kipimo's role

kipimo makes the question testable. Its target registry
([`kipimo targets`](../src/kipimo/targets.py)) lists three families —
`closed-api`, `open-weight`, and `small-open` (≤32B, the realistic edge-deploy
tier) — and scores them on the **same** Swahili agent-task set.

The runnable path:

```bash
# Serve an open-weight model with an OpenAI-compatible endpoint
# (Ollama, vLLM, or SGLang — all keep the weights on your own hardware)
export KIPIMO_BASE_URL="http://localhost:11434/v1"
export KIPIMO_MODEL="kimi-k2.6"

kipimo tasks > tasks.jsonl
python examples/generate_predictions.py tasks.jsonl > preds.jsonl
kipimo score preds.jsonl
```

The score answers the only question that matters for a sovereignty-constrained
deployment: **does the model I am allowed to run actually serve Swahili speakers
well enough?** Not "is the frontier model better" — it usually is — but "is the
deployable one good enough for this task."

## What kipimo deliberately does NOT claim

- It does not rank models overall; it measures one regional task family.
- A high score is competence at stack routing, not general fluency.
- The seed benchmark (46 tasks) is directional. Native-speaker review remains
  the highest-value contribution.

The point is to let a builder under a data-sovereignty constraint make an
evidence-based choice, instead of assuming they must either surrender their data
or ship a model nobody measured.
