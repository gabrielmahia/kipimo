# kipimo

Over one hundred million people coordinate their lives in Swahili, yet no benchmark measures whether an AI agent can route their requests correctly — send money, check drought status, find a clinic, verify a worker's credentials. Agents targeting East Africa are evaluated on English tasks and deployed on faith.

`kipimo` (Swahili: *a measure*) is a model-agnostic seed benchmark for exactly that gap: **46 tasks** across three types, with golds machine-derived from authoritative sources — the coordination-stack registry and the live `africa-coord-bus` routing table — never from memory.

| Type | n | What it measures | Metric |
|---|---|---|---|
| `server_routing` | 25 | Swahili request → correct stack server (payments, tax, health, land, labour…) | exact |
| `term_grounding` | 14 | Swahili domain term → English meaning | exact (case-insensitive) |
| `cascade_routing` | 7 | Coordination event → which sectors must be notified | set F1 |

**[Live leaderboard →](https://huggingface.co/spaces/gmahia/kipimo-leaderboard)** — score any model in your browser, no keys.

## Use it (any model, no API keys)

```bash
pip install kipimo
kipimo tasks > tasks.jsonl        # feed to your agent however you like
kipimo template > preds.jsonl     # fill "prediction": [...] per id
kipimo score preds.jsonl          # per-type + overall report
```

The harness never calls a model — you generate predictions with whatever system you're evaluating; kipimo only scores. Any lab can publish comparable numbers.

## Honesty box
- **v0.1 is a seed set.** 46 tasks establish the format and scoring; breadth comes from contributions.
- Swahili phrasing is simple-register and **pending native-speaker review** — that is [issue #1](https://github.com/gabrielmahia/kipimo/issues), and corrections are the most valuable contribution possible.
- Scores measure stack-routing competence, not general Swahili fluency.
- Dataset: **CC BY 4.0** (usable by everyone, including commercial labs — that's the point). Harness: **MIT**.

## IP & Collaboration

MIT-licensed harness, CC BY 4.0 data. Feedback via GitHub Issues only — pull requests are not accepted; task corrections and additions via Issues are actively wanted. Full policy: [docs/architecture/IP_POLICY.md](docs/architecture/IP_POLICY.md). Security: see [SECURITY.md](SECURITY.md).

<!-- interconnect:v1 -->
## Part of the East Africa coordination stack

- **Install & run:** `pip install reli-cli && reli list` — 33 MCP servers on the [official MCP Registry](https://registry.modelcontextprotocol.io) under `io.github.gabrielmahia`
- **Evaluate any model on Swahili agent tasks:** [kipimo](https://github.com/gabrielmahia/kipimo) · [dataset](https://huggingface.co/datasets/gmahia/kipimo) · [leaderboard](https://huggingface.co/spaces/gmahia/kipimo-leaderboard)
- **Coordinate across servers:** [africa-coord-bus](https://pypi.org/project/africa-coord-bus/) — offline-first event bus with a built-in Kenya routing table
- **Datasets:** [huggingface.co/gmahia](https://huggingface.co/gmahia) · **Docs hub:** [nairobi-stack](https://github.com/gabrielmahia/nairobi-stack)

Model-agnostic by design: closed APIs, open-weight models, and small distilled models are all first-class citizens.
<!-- /interconnect:v1 -->
