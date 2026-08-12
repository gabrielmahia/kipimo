"""Pareto/deployment tests — the sovereignty question, and honesty about unknowns."""
from kipimo.pareto import analyze, build_rows, cheapest_qualifier, pareto_frontier

CARD = {"ranked": [
    {"target": "gpt-5.6", "score": 0.95}, {"target": "glm-5.2", "score": 0.93},
    {"target": "qwen3-14b", "score": 0.88}, {"target": "gemma-3-12b", "score": 0.86},
    {"target": "inkubalm-0.4b", "score": 0.61}], "untested": []}
COSTS = {"gpt-5.6": 12.5, "glm-5.2": 1.8, "qwen3-14b": 0.09,
         "gemma-3-12b": 0.05, "inkubalm-0.4b": 0.01}


def test_rows_join_registry_profile():
    rows = build_rows(CARD, COSTS)
    g = next(r for r in rows if r["target"] == "glm-5.2")
    assert g["license"] == "MIT" and g["self_hostable"] is True


def test_dominated_target_is_off_the_frontier():
    # a target both worse AND pricier than another must be excluded
    card = {"ranked": [{"target": "qwen3-14b", "score": 0.88},
                       {"target": "gemma-3-12b", "score": 0.70}]}
    front = pareto_frontier(build_rows(card, {"qwen3-14b": 0.09, "gemma-3-12b": 0.50}))
    assert [r["target"] for r in front] == ["qwen3-14b"]


def test_cheapest_sovereign_qualifier_excludes_api_only():
    rows = build_rows(CARD, COSTS)
    pick = cheapest_qualifier(rows, 0.85, self_hostable=True)
    assert pick["target"] == "gemma-3-12b"       # cheapest self-hostable clearing 0.85
    assert pick["self_hostable"] is True


def test_proprietary_wins_overall_but_not_sovereignty():
    a = analyze(CARD, COSTS, threshold=0.85)
    assert a["best_overall"] == "gpt-5.6"                    # highest score
    assert a["cheapest_sovereign_qualifier"] == "gemma-3-12b"  # but not deployable
    assert 0.8 < a["sovereign_vs_frontier_ratio"] < 1.0


def test_hardware_tier_constraint_respected():
    rows = build_rows(CARD, COSTS)
    pick = cheapest_qualifier(rows, 0.85, self_hostable=True, max_hardware_tier="workstation")
    assert pick["hardware_tier"] in ("edge", "workstation")   # datacenter excluded


def test_threshold_with_no_qualifier_reports_honestly():
    a = analyze(CARD, COSTS, threshold=0.99)
    assert a["cheapest_sovereign_qualifier"] is None
    assert "No self-hostable target clears" in a["reading"]


def test_unpriced_target_is_not_treated_as_free():
    a = analyze(CARD, {"gpt-5.6": 12.5}, threshold=0.85)   # only one cost supplied
    assert "qwen3-14b" in a["unpriced_targets"]
    assert "qwen3-14b" not in a["pareto_frontier"]         # excluded, not ranked cheapest
