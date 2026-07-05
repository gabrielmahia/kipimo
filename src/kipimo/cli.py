"""kipimo — Swahili agent-task evaluation for the East Africa coordination stack.

Model-agnostic by design: kipimo emits tasks and scores prediction files. It
never calls a model API, so any lab, student, or vendor can evaluate any agent
against the same gold set. Golds are machine-derived from authoritative
sources (the stack registry; the africa-coord-bus routing table), never from
memory.

Usage:
    kipimo tasks                 # emit the task set (JSONL) to stdout
    kipimo template              # emit an empty predictions file to fill in
    kipimo score preds.jsonl     # score predictions against gold
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from importlib import resources

__version__ = "0.1.0"

DISCLAIMER = ("kipimo v0.1 is a SEED benchmark (46 tasks). Swahili phrasing is "
              "simple-register and pending native-speaker review (issue #1). "
              "Scores indicate stack-routing competence, not general Swahili "
              "fluency. Do not use as a sole deployment gate.")


def load_tasks() -> list[dict]:
    text = resources.files("kipimo").joinpath("data/kipimo_v0.1.jsonl").read_text("utf-8")
    return [json.loads(line) for line in text.splitlines() if line.strip()]


def _norm(s: str) -> str:
    return " ".join(str(s).lower().split())


def score_one(task: dict, pred: list[str]) -> float:
    gold = [_norm(g) for g in task["gold"]]
    p = [_norm(x) for x in (pred or [])]
    if task["metric"] in ("exact", "exact_ci"):
        return 1.0 if p and p[0] in gold else 0.0
    if task["metric"] == "set_f1":
        gs, ps = set(gold), set(p)
        if not ps:
            return 0.0
        tp = len(gs & ps)
        prec, rec = tp / len(ps), tp / len(gs)
        return 0.0 if tp == 0 else 2 * prec * rec / (prec + rec)
    raise ValueError(f"unknown metric {task['metric']}")


def score_file(path: str) -> dict:
    preds = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                row = json.loads(line)
                preds[row["id"]] = row.get("prediction", [])
    tasks = load_tasks()
    by_type: dict[str, list[float]] = defaultdict(list)
    missing = []
    for t in tasks:
        if t["id"] not in preds:
            missing.append(t["id"])
            by_type[t["type"]].append(0.0)
        else:
            by_type[t["type"]].append(score_one(t, preds[t["id"]]))
    report = {k: round(sum(v) / len(v), 4) for k, v in by_type.items()}
    allv = [x for v in by_type.values() for x in v]
    report["overall"] = round(sum(allv) / len(allv), 4)
    report["n_tasks"] = len(tasks)
    report["n_missing"] = len(missing)
    return report


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="kipimo", description=__doc__.split("\n")[0],
                                epilog=DISCLAIMER)
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("tasks", help="emit task set JSONL to stdout")
    sub.add_parser("template", help="emit empty predictions JSONL to stdout")
    sp = sub.add_parser("score", help="score a predictions file")
    sp.add_argument("predictions", help="JSONL with {id, prediction:[...]} rows")
    args = p.parse_args(argv)

    if args.cmd == "tasks":
        for t in load_tasks():
            print(json.dumps(t, ensure_ascii=False))
    elif args.cmd == "template":
        for t in load_tasks():
            print(json.dumps({"id": t["id"], "prediction": []}))
    else:
        rep = score_file(args.predictions)
        print(json.dumps(rep, indent=2))
        print(f"\n{DISCLAIMER}", file=sys.stderr)
        if rep["n_missing"]:
            print(f"Note: {rep['n_missing']} task(s) had no prediction and scored 0. "
                  f"Run `kipimo template` for the full id list.", file=sys.stderr)
    return 0


def _main() -> int:
    try:
        return main()
    except BrokenPipeError:
        import os
        os.dup2(os.open(os.devnull, os.O_WRONLY), sys.stdout.fileno())
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
