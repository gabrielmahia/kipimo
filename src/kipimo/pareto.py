"""kipimo.pareto — turn a scorecard into a deployment decision.

A leaderboard answers "which model scored highest?". That is rarely the question
an African institution faces. Theirs is:

    What is the CHEAPEST model we are allowed to run OURSELVES that clears the
    competence bar for this task?

Answering it needs three things a score alone does not carry: what the model
costs to run, whether the licence permits self-hosting, and what hardware it
demands. This module joins measured accuracy (from the harness) with the
registry's deployment profile and operator-supplied cost, then reports:

  * the **Pareto frontier** — targets not beaten on BOTH accuracy and cost by
    some other target. Everything off the frontier is strictly dominated and can
    be dropped from consideration without argument.
  * the **cheapest qualifier** at a competence threshold, optionally restricted
    to self-hostable / offline-capable / hardware-tier-limited targets. This is
    the sovereign-deployment answer.

Cost is passed in per run, never stored in the registry: vendor prices move
weekly and differ by region, and a stale number in a public benchmark is worse
than no number. Targets without a cost are ranked on accuracy and reported
separately rather than silently assigned zero — the same discipline the harness
applies to untested targets.
"""
from __future__ import annotations

from .targets import get_target

HARDWARE_ORDER = ["edge", "workstation", "server", "datacenter", "api-only"]


def _profile(target_id: str) -> dict:
    try:
        t = get_target(target_id)
    except Exception:
        return {}
    return {k: t.get(k) for k in
            ("license", "self_hostable", "hardware_tier", "offline_capable", "family")}


def build_rows(scorecard: dict, costs: dict[str, float] | None = None) -> list[dict]:
    """Join harness results with registry profiles and operator-supplied costs.

    ``costs`` maps target_id -> cost per 1k tasks (any consistent currency).
    """
    costs = costs or {}
    rows = []
    for r in scorecard.get("ranked", []):
        tid = r["target"]
        rows.append({"target": tid, "score": r["score"],
                     "cost_per_1k": costs.get(tid),  # None = not supplied, not free
                     **_profile(tid)})
    return rows


def pareto_frontier(rows: list[dict]) -> list[dict]:
    """Targets not dominated on both accuracy (higher better) and cost (lower better).

    Rows without a cost cannot be compared on cost and are excluded here; they
    are reported separately by ``analyze`` rather than dropped silently.
    """
    priced = [r for r in rows if r.get("cost_per_1k") is not None and r.get("score") is not None]
    frontier = []
    for r in priced:
        dominated = any(
            o is not r
            and o["score"] >= r["score"]
            and o["cost_per_1k"] <= r["cost_per_1k"]
            and (o["score"] > r["score"] or o["cost_per_1k"] < r["cost_per_1k"])
            for o in priced
        )
        if not dominated:
            frontier.append(r)
    return sorted(frontier, key=lambda r: r["cost_per_1k"])


def cheapest_qualifier(rows: list[dict], threshold: float, *,
                       self_hostable: bool | None = None,
                       offline_capable: bool | None = None,
                       max_hardware_tier: str | None = None) -> dict | None:
    """Cheapest target clearing ``threshold``, under deployment constraints.

    With ``self_hostable=True`` this answers the sovereignty question directly:
    the cheapest model an institution may lawfully run on its own hardware while
    still clearing the competence bar.
    """
    cands = [r for r in rows if (r.get("score") or 0) >= threshold]
    if self_hostable is not None:
        cands = [r for r in cands if r.get("self_hostable") is self_hostable]
    if offline_capable is not None:
        cands = [r for r in cands if r.get("offline_capable") is offline_capable]
    if max_hardware_tier:
        limit = HARDWARE_ORDER.index(max_hardware_tier)
        cands = [r for r in cands
                 if r.get("hardware_tier") in HARDWARE_ORDER
                 and HARDWARE_ORDER.index(r["hardware_tier"]) <= limit]
    if not cands:
        return None
    priced = [r for r in cands if r.get("cost_per_1k") is not None]
    # cheapest if costs known; otherwise the qualifier on the smallest hardware
    if priced:
        return min(priced, key=lambda r: r["cost_per_1k"])
    return min(cands, key=lambda r: HARDWARE_ORDER.index(r.get("hardware_tier") or "api-only"))


def analyze(scorecard: dict, costs: dict[str, float] | None = None,
            threshold: float = 0.8) -> dict:
    """Full deployment analysis over a harness scorecard."""
    rows = build_rows(scorecard, costs)
    unpriced = [r["target"] for r in rows if r.get("cost_per_1k") is None]
    sovereign = cheapest_qualifier(rows, threshold, self_hostable=True)
    edge = cheapest_qualifier(rows, threshold, self_hostable=True,
                              max_hardware_tier="workstation")
    best = max(rows, key=lambda r: r["score"]) if rows else None
    gap = None
    if best and sovereign and best["score"]:
        gap = round(sovereign["score"] / best["score"], 3)
    return {
        "threshold": threshold,
        "rows": rows,
        "pareto_frontier": [r["target"] for r in pareto_frontier(rows)],
        "unpriced_targets": unpriced,
        "best_overall": best["target"] if best else None,
        "cheapest_sovereign_qualifier": sovereign["target"] if sovereign else None,
        "cheapest_edge_qualifier": edge["target"] if edge else None,
        "sovereign_vs_frontier_ratio": gap,
        "reading": (
            f"{sovereign['target']} is self-hostable, clears {threshold}, and reaches "
            f"{int(gap*100)}% of the best measured target's score."
            if sovereign and gap else
            f"No self-hostable target clears {threshold} in this run."
        ),
        "caveat": ("Costs are operator-supplied for this run, not registry facts. "
                   "Unpriced targets are excluded from the Pareto frontier — not "
                   "treated as free. Licences marked '(verify)' must be confirmed "
                   "on the model's own repository before deployment."),
    }
