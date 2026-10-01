"""Reference-floor tests. The numbers below are facts about the current task set (issue #8);
if the tasks change, update them deliberately rather than letting the floor drift."""
import json

from kipimo import load_tasks
from kipimo.baselines import FLEET, is_literal, lexical_predictions, score_stratified, strata
from kipimo.cli import main

TASKS = load_tasks()
ROUTING = [t for t in TASKS if t["type"] == "server_routing"]


def test_fleet_is_unique_and_covers_every_routing_gold():
    assert len(set(FLEET)) == len(FLEET)
    assert all(t["gold"][0] in FLEET for t in ROUTING)


def test_strata_partition_the_routing_tasks():
    s = strata(TASKS)
    assert sorted(s["literal"] + s["semantic"]) == sorted(t["id"] for t in ROUTING)
    assert not set(s["literal"]) & set(s["semantic"])


def test_known_stratum_sizes():
    s = strata(TASKS)
    assert (len(s["literal"]), len(s["semantic"])) == (12, 13)


def test_is_literal_ignores_other_task_types():
    assert not any(is_literal(t) for t in TASKS if t["type"] != "server_routing")


def test_lexical_floor_is_reproducible_and_routing_only():
    preds = lexical_predictions(TASKS)
    assert set(preds) == {t["id"] for t in ROUTING}
    st = score_stratified(preds, TASKS)
    assert st["literal"]["correct"] == 11 and st["semantic"]["correct"] == 0


def test_cli_baseline_and_stratify_round_trip(tmp_path, capsys):
    assert main(["baseline", "lexical"]) == 0
    out = capsys.readouterr().out
    rows = [json.loads(line) for line in out.splitlines() if line.strip()]
    assert len(rows) == len(ROUTING)
    f = tmp_path / "p.jsonl"; f.write_text(out)
    assert main(["score", str(f), "--stratify"]) == 0
    text = capsys.readouterr().out
    assert "server_routing_by_stratum" in text and '"semantic"' in text


def test_default_score_output_has_no_stratum_block(tmp_path, capsys):
    f = tmp_path / "p.jsonl"; f.write_text("\n".join(json.dumps({"id": t["id"], "prediction": []}) for t in TASKS))
    assert main(["score", str(f)]) == 0
    assert "server_routing_by_stratum" not in capsys.readouterr().out
