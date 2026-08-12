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
    kipimo run generators.json   # run targets in parallel -> ranked scorecard
    kipimo analyze card.json     # -> Pareto frontier + cheapest sovereign qualifier
    kipimo targets               # emit the scorecard target registry (v0.2)
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from importlib import resources

__version__ = "0.4.0"

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
    tp = sub.add_parser("targets", help="emit scorecard target registry JSONL to stdout")
    tp.add_argument("--family", choices=("closed-api", "open-weight", "small-open"),
                    default=None, help="filter by target family")
    sub.add_parser("template", help="emit empty predictions JSONL to stdout")
    rp = sub.add_parser("run", help="run generators across targets in parallel -> scorecard")
    rp.add_argument("generators", help='JSON file: {"target_id": "generator command", ...}')
    rp.add_argument("--timeout", type=int, default=600, help="seconds per target (default 600)")
    rp.add_argument("--workers", type=int, default=4, help="parallel targets (default 4)")
    ap = sub.add_parser("analyze", help="scorecard -> deployment decision (Pareto + cheapest qualifier)")
    ap.add_argument("scorecard", help="JSON scorecard from `kipimo run`")
    ap.add_argument("--costs", default=None, help='JSON file: {"target_id": cost_per_1k_tasks}')
    ap.add_argument("--threshold", type=float, default=0.8, help="competence bar (default 0.8)")
    sp = sub.add_parser("score", help="score a predictions file")
    sp.add_argument("predictions", help="JSONL with {id, prediction:[...]} rows")
    args = p.parse_args(argv)

    if args.cmd == "targets":
        from .targets import list_targets
        for t in list_targets(args.family):
            print(json.dumps(t, ensure_ascii=False))
    elif args.cmd == "tasks":
        for t in load_tasks():
            print(json.dumps(t, ensure_ascii=False))
    elif args.cmd == "template":
        for t in load_tasks():
            print(json.dumps({"id": t["id"], "prediction": []}))
    elif args.cmd == "analyze":
        from .pareto import analyze
        with open(args.scorecard, encoding="utf-8") as f:
            card = json.load(f)
        costs = {}
        if args.costs:
            with open(args.costs, encoding="utf-8") as f:
                costs = {str(k): float(v) for k, v in json.load(f).items()}
        print(json.dumps(analyze(card, costs, args.threshold), indent=2, ensure_ascii=False))
        print(f"\n{DISCLAIMER}", file=sys.stderr)
    elif args.cmd == "run":
        from .harness import load_generators, run_scorecard
        card = run_scorecard(load_generators(args.generators),
                             timeout=args.timeout, max_workers=args.workers)
        print(json.dumps(card, indent=2, ensure_ascii=False))
        if card["targets_untested"]:
            print(f"\nNote: {card['targets_untested']} target(s) UNTESTED (unknown, not zero). "
                  f"See 'untested' in the scorecard.", file=sys.stderr)
        print(f"\n{DISCLAIMER}", file=sys.stderr)
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
