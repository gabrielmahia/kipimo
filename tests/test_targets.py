"""Registry sanity: schema, uniqueness, family coverage, CLI emission."""

import json

from kipimo import FAMILIES, TARGETS, get_target, list_targets
from kipimo.cli import main


def test_schema_and_uniqueness():
    ids = [t["id"] for t in TARGETS]
    assert len(ids) == len(set(ids))
    for t in TARGETS:
        assert set(t) == {"id", "label", "family", "params_b", "endpoint_env", "notes"}
        assert t["family"] in FAMILIES
        assert isinstance(t["endpoint_env"], list) and t["endpoint_env"]


def test_every_family_represented():
    for fam in FAMILIES:
        assert list_targets(fam), f"no targets in family {fam}"


def test_small_open_is_actually_small():
    assert all(t["params_b"] and t["params_b"] <= 32 for t in list_targets("small-open"))


def test_get_target_and_errors():
    assert get_target("kimi-k3")["family"] == "open-weight"
    try:
        get_target("nope")
        raise AssertionError("expected KeyError")
    except KeyError:
        pass
    try:
        list_targets("bogus")
        raise AssertionError("expected ValueError")
    except ValueError:
        pass


def test_cli_targets_emits_jsonl(capsys):
    assert main(["targets", "--family", "small-open"]) == 0
    out = capsys.readouterr().out.strip().splitlines()
    rows = [json.loads(x) for x in out]
    assert rows and all(r["family"] == "small-open" for r in rows)
