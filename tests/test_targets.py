"""Registry sanity: schema, uniqueness, family coverage, CLI emission."""

import json

from kipimo import FAMILIES, TARGETS, get_target, list_targets
from kipimo.cli import main


CORE = {"id", "label", "family", "params_b", "endpoint_env", "notes"}
PROFILE = {"license", "self_hostable", "hardware_tier", "offline_capable"}
HARDWARE = {"edge", "workstation", "server", "datacenter", "api-only"}


def test_schema_and_uniqueness():
    ids = [t["id"] for t in TARGETS]
    assert len(ids) == len(set(ids))
    for t in TARGETS:
        assert CORE <= set(t), f"{t['id']} missing core keys"
        assert set(t) <= CORE | PROFILE, f"{t['id']} has unknown keys"
        assert t["family"] in FAMILIES
        assert isinstance(t["endpoint_env"], list) and t["endpoint_env"]


def test_deployment_profile_is_valid_where_present():
    for t in TARGETS:
        if "hardware_tier" in t:
            assert t["hardware_tier"] in HARDWARE, t["id"]
        if "self_hostable" in t:
            assert isinstance(t["self_hostable"], bool)
        if "offline_capable" in t:
            assert isinstance(t["offline_capable"], bool)
        # an api-only target can be neither self-hostable nor offline
        if t.get("hardware_tier") == "api-only":
            assert t.get("self_hostable") is False and t.get("offline_capable") is False, t["id"]


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
