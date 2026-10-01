"""Non-model reference points for kipimo. Additive: nothing here changes how tasks are scored.

Why: on `server_routing`, 12 of 25 requests literally contain a token of the gold server name
(e.g. "mkopo", "bima", "KRA"), so a matcher with no model scores well above small open models.
A routing score is only informative next to that floor, and split by whether the request
carries the server name. See issue #8.
"""
from __future__ import annotations

import re

# The tool catalog a deployment would list: public MCP fleet server names, taken from the public
# directory listing. It is NOT derived from the benchmark's gold answers (a test checks that it
# covers every routing gold, so a typo cannot silently cap the baseline).
FLEET: tuple[str, ...] = (
    "nyumba-mcp", "faida-mcp", "kra-mcp", "ardhi-mcp", "familia-mcp", "fomu-mcp", "bima-mcp",
    "kilimo-mcp", "elimu-mcp", "kazi-mcp", "soko-mcp", "remit-mcp", "offline-mcp",
    "haki-ya-kazi-mcp", "usafiri-mcp", "mkopo-mcp", "mpesa-mcp", "afya-mcp", "sifa-mcp",
    "wapimaji-mcp", "tafsiri-mcp", "nishati-mcp", "county-mcp", "diaspora-mcp", "habari-mcp",
    "mazingira-mcp", "historia-mcp", "church-mcp", "jumuia-mcp", "afya-ya-akili-mcp",
    "kenya-health-mcp", "swahili-health-mcp",
)


def _clean(s: str) -> str:
    return re.sub(r"[^a-z0-9 ]", " ", s.lower())


def _name_tokens(name: str) -> list[str]:
    return [x for x in name.replace("-mcp", "").split("-") if len(x) >= 3]


def is_literal(task: dict) -> bool:
    """True when a server_routing request literally contains a (3+ char) token of its gold server name."""
    if task.get("type") != "server_routing":
        return False
    txt = _clean(task["input"])
    return any(tok in txt for tok in _name_tokens(task["gold"][0]))


def strata(tasks: list[dict]) -> dict[str, list[str]]:
    """Split server_routing task ids into 'literal' (name token in the request) and 'semantic' (none)."""
    out: dict[str, list[str]] = {"literal": [], "semantic": []}
    for t in tasks:
        if t.get("type") == "server_routing":
            out["literal" if is_literal(t) else "semantic"].append(t["id"])
    return out


def _trigrams(s: str) -> set[str]:
    s = "  " + " ".join(_clean(s).split()) + "  "
    return {s[i:i + 3] for i in range(len(s) - 2)}


def lexical_predictions(tasks: list[dict], catalog: tuple[str, ...] = FLEET) -> dict[str, list[str]]:
    """No-model baseline for server_routing: the catalog name whose character trigrams best overlap
    the request (Jaccard). Ties go to the earliest catalog entry. Other task types are NOT predicted:
    they are untested, not zero."""
    grams = {c: _trigrams(c.replace("-mcp", "")) for c in catalog}
    preds: dict[str, list[str]] = {}
    for t in tasks:
        if t.get("type") != "server_routing":
            continue
        q = _trigrams(t["input"])
        best, best_score = catalog[0], -1.0
        for c in catalog:
            sc = len(q & grams[c]) / max(1, len(q | grams[c]))
            if sc > best_score:
                best, best_score = c, sc
        preds[t["id"]] = [best]
    return preds


def score_stratified(preds: dict[str, list[str]], tasks: list[dict]) -> dict[str, dict]:
    """server_routing accuracy split by stratum, using kipimo's own score_one (so it cannot drift)."""
    from .cli import score_one

    by_id = {t["id"]: t for t in tasks}
    out = {}
    for name, ids in strata(tasks).items():
        correct = sum(1 for i in ids if score_one(by_id[i], preds.get(i, [])) == 1.0)
        out[name] = {"n": len(ids), "correct": correct, "accuracy": round(correct / len(ids), 4) if ids else None}
    return out
