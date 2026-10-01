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

## Data sovereignty

The models deployable under African data-sovereignty constraints are open-weight and self-hostable. kipimo scores that tier on equal terms with frontier APIs so builders can test whether the model they are *allowed* to run is good enough — see [docs/DATA_SOVEREIGNTY.md](docs/DATA_SOVEREIGNTY.md) and `examples/generate_predictions.py`.

## Honesty box
- **v0.1 is a seed set.** 46 tasks establish the format and scoring; breadth comes from contributions.
- Swahili phrasing is simple-register and **pending native-speaker review** — that is [issue #1](https://github.com/gabrielmahia/kipimo/issues), and corrections are the most valuable contribution possible.
- Scores measure stack-routing competence, not general Swahili fluency.
- Dataset: **CC BY 4.0** (usable by everyone, including commercial labs — that's the point). Harness: **MIT**.

## Reference floor: a baseline with no model

On `server_routing`, 12 of the 25 requests literally contain a token of the gold server name (for example `mkopo`, `bima`, `KRA`). A matcher with no model scores 11/25 on this task set: 11/12 on those requests and 0/13 on the rest. Read any routing score next to that floor, and split by stratum:

```
kipimo baseline lexical > floor.jsonl     # no model; server_routing only
kipimo score floor.jsonl --stratify       # adds server_routing_by_stratum (literal vs semantic)
```

Only the `server_routing` figure is meaningful for the baseline; the other task types are untested (unknown, not zero), so ignore `overall`. The server list it matches against is the public fleet listing, independent of the benchmark's gold answers. Background and measurements: issue #8.

## Complementary benchmarks — what kipimo does not measure

kipimo measures institutional-routing competence: can a model correctly navigate
the East Africa coordination stack in Swahili. It deliberately does not measure
general reasoning, NLI, or math in African languages — that would duplicate work
that already exists and is well-maintained.

**[IrokoBench](https://arxiv.org/abs/2406.03368)** (Masakhane, Lelapa AI, Cohere
For AI, and 13 other institutions) covers NLI, mathematical reasoning, and
multiple-choice QA across 17 African languages including Swahili. If you need to
know whether a model can *reason* in Swahili, use IrokoBench. If you need to know
whether it can *route a Swahili institutional request through an unfamiliar MCP
ecosystem*, use kipimo. The two are complementary axes, not competing
leaderboards — a model can score well on one and poorly on the other, and both
numbers are useful.

We do not vendor or duplicate IrokoBench's tasks here. Contribute upstream to
Masakhane rather than building a parallel general-reasoning suite inside kipimo.

## Related evaluation gaps (tracked upstream)

Independent research corroborates a gap this stack has also identified
separately (`nairobi-stack` gap register, G13): current models largely
**cannot process speech in African languages at all** — see the Afri-MCQA
findings presented at AfricaNLP 2026 (7th Workshop, EACL 2026), which found
models "unable to process speech in African languages," lacking cultural
context, and struggling to *generate* culturally relevant responses rather than
merely recognize them. Two independent efforts converging on the same missing
capability from different directions is a stronger signal than either alone.

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

## Running a scorecard (`kipimo run`)

Fan out across targets in parallel, converge to one ranked scorecard. kipimo
still never calls a model API — you supply a *generator command* per target
(any process that reads tasks JSONL on stdin and writes predictions JSONL on
stdout; see `examples/generate_predictions.py`).

```bash
cat > generators.json <<'JSON'
{
  "gemma-3-12b":    "python generate_predictions.py --model gemma-3-12b",
  "inkubalm-0.4b":  "python generate_predictions.py --model inkubalm-0.4b",
  "kimi-k3":        ""
}
JSON

kipimo run generators.json --timeout 600 --workers 4
```

**An untested target is UNKNOWN, never zero.** If a generator crashes, times
out, or is unconfigured, that target appears under `untested` with a reason —
it is not ranked at 0.0. Conflating "the model failed the task" with "we never
tested the model" is how an evaluation starts measuring its own assumptions
instead of reality. Every scorecard also reports `coverage`, so a partial run
cannot be misread as a ranking of the field.

## From leaderboard to deployment decision (`kipimo analyze`)

A ranking says which model scored highest. Institutions need a different answer:
**what is the cheapest model we may lawfully run ourselves that clears the bar?**

```bash
kipimo run generators.json > card.json
kipimo analyze card.json --costs costs.json --threshold 0.85
```

Targets carry a deployment profile (`license`, `self_hostable`, `hardware_tier`,
`offline_capable`), which `analyze` joins with measured accuracy and
operator-supplied cost to report the Pareto frontier and the cheapest
self-hostable qualifier:

> *"gemma-3-12b is self-hostable, clears 0.85, and reaches 90% of the best
> measured target's score."*

Costs are supplied per run, never stored in the registry — vendor prices move
weekly and a stale number in a public benchmark is worse than none. A target
with no cost supplied is excluded from the frontier, **not treated as free**.
