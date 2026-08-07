"""Harness tests — the load-bearing property is that UNTESTED is never scored as zero."""
import json
import sys

from kipimo.harness import run_target, run_scorecard

GOOD = f'{sys.executable} -c "import sys,json\nfor l in sys.stdin:\n    l=l.strip()\n    if l: t=json.loads(l); print(json.dumps({{\'id\':t[\'id\'],\'prediction\':[\'mpesa-mcp\']}}))"'
CRASH = f'{sys.executable} -c "import sys; sys.exit(3)"'
EMPTY = f'{sys.executable} -c "pass"'
HANG = f'{sys.executable} -c "import time; time.sleep(60)"'


def test_working_generator_scores():
    r = run_target("gemma-3-12b", GOOD, timeout=60)
    assert r["status"] == "ok"
    assert isinstance(r["score"], float)
    assert r["report"]["n_missing"] == 0


def test_crashed_generator_is_error_not_zero():
    r = run_target("gemma-3-12b", CRASH, timeout=60)
    assert r["status"] == "error"
    assert r["score"] is None          # NOT 0.0 — we did not test it
    assert "exit 3" in r["reason"]


def test_empty_output_is_error_not_zero():
    r = run_target("gemma-3-12b", EMPTY, timeout=60)
    assert r["status"] == "error"
    assert r["score"] is None
    assert "no predictions" in r["reason"]


def test_timeout_is_recorded_not_zero():
    r = run_target("gemma-3-12b", HANG, timeout=2)
    assert r["status"] == "timeout"
    assert r["score"] is None


def test_unconfigured_target_is_skipped():
    r = run_target("kimi-k3", "", timeout=5)
    assert r["status"] == "skipped"
    assert r["score"] is None


def test_scorecard_separates_scored_from_untested():
    card = run_scorecard({"gemma-3-12b": GOOD, "inkubalm-0.4b": CRASH, "kimi-k3": ""},
                         timeout=30, max_workers=3)
    assert card["targets_scored"] == 1
    assert card["targets_untested"] == 2
    ranked_ids = [r["target"] for r in card["ranked"]]
    assert ranked_ids == ["gemma-3-12b"]          # only real results ranked
    untested_ids = {r["target"] for r in card["untested"]}
    assert untested_ids == {"inkubalm-0.4b", "kimi-k3"}
    # coverage must make a partial run unmistakable
    assert "/" in card["coverage"]
    assert "not zero" in card["caveat"]


def test_one_broken_target_does_not_abort_the_run():
    card = run_scorecard({"a": CRASH, "b": GOOD}, timeout=30, max_workers=2)
    assert card["targets_attempted"] == 2
    assert card["targets_scored"] == 1            # the good one still ran


def test_ranking_is_by_score_descending():
    card = run_scorecard({"gemma-3-12b": GOOD, "qwen3-14b": GOOD}, timeout=30, max_workers=2)
    scores = [r["score"] for r in card["ranked"]]
    assert scores == sorted(scores, reverse=True)
