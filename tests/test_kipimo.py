"""Integrity + scoring tests for the kipimo seed benchmark."""
import json
import subprocess
import sys

from kipimo import load_tasks, score_one


def test_dataset_integrity():
    tasks = load_tasks()
    assert len(tasks) == 46
    ids = [t["id"] for t in tasks]
    assert len(ids) == len(set(ids)), "duplicate ids"
    for t in tasks:
        assert t["type"] in ("server_routing", "term_grounding", "cascade_routing")
        assert t["gold"], t["id"]
        assert t["metric"] in ("exact", "exact_ci", "set_f1")
        assert t["input"].strip()


def test_exact_scoring():
    t = {"gold": ["mpesa-mcp"], "metric": "exact"}
    assert score_one(t, ["mpesa-mcp"]) == 1.0
    assert score_one(t, ["MPESA-MCP"]) == 1.0  # normalized
    assert score_one(t, ["kra-mcp"]) == 0.0
    assert score_one(t, []) == 0.0


def test_set_f1_scoring():
    t = {"gold": ["health", "finance"], "metric": "set_f1"}
    assert score_one(t, ["health", "finance"]) == 1.0
    assert 0 < score_one(t, ["health"]) < 1.0
    assert score_one(t, ["water"]) == 0.0


def test_cli_end_to_end(tmp_path):
    r = subprocess.run([sys.executable, "-m", "kipimo.cli", "template"],
                       capture_output=True, text=True)
    assert r.returncode == 0
    preds = tmp_path / "p.jsonl"
    # perfect predictions = gold copied in
    lines = [json.dumps({"id": t["id"], "prediction": t["gold"]}) for t in load_tasks()]
    preds.write_text("\n".join(lines))
    r = subprocess.run([sys.executable, "-m", "kipimo.cli", "score", str(preds)],
                       capture_output=True, text=True)
    rep = json.loads(r.stdout)
    assert rep["overall"] == 1.0 and rep["n_missing"] == 0
