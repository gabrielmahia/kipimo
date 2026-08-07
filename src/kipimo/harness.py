"""kipimo.harness — run the benchmark across targets in parallel, converge to a scorecard.

The diamond: fan out one worker per target, converge into a single ranked
scorecard. Targets are independent (a real dependency test — no target's
prediction informs another's), so they run concurrently; the scorecard is the
only true convergence point.

Two design rules, both deliberate:

1. **kipimo still never calls a model API.** This module orchestrates *generator
   commands you supply* (any process that reads tasks JSONL on stdin and writes
   predictions JSONL on stdout). Model access, keys, and endpoints stay outside
   the package, so the benchmark remains vendor-neutral and reproducible by
   anyone. See examples/generate_predictions.py for a stdlib generator.

2. **A missing run is never a zero.** The scoring path already treats an absent
   prediction as 0.0, which is correct *within* a run. Across targets it would
   be a lie: a target whose generator crashed, timed out, or was never
   configured has an UNKNOWN score, not a bad one. Conflating "the model failed
   the task" with "we never tested the model" is how an evaluation system starts
   training on its own assumptions instead of on evidence. Every result
   therefore carries an explicit ``status``:

       ok         — generator ran, predictions scored
       error      — generator failed (message retained)
       timeout    — generator exceeded its deadline
       skipped    — no generator configured for this target

   Only ``ok`` results carry a score. The scorecard reports coverage alongside
   results so a partial run can never be read as a complete one.
"""
from __future__ import annotations

import concurrent.futures
import json
import shlex
import subprocess
import tempfile
import time
from pathlib import Path

from .cli import load_tasks, score_file
from .targets import get_target, list_targets

DEFAULT_TIMEOUT = 600  # seconds per target; generators are network-bound


def _tasks_jsonl() -> str:
    return "\n".join(json.dumps(t, ensure_ascii=False) for t in load_tasks())


def run_target(target_id: str, command: str, timeout: int = DEFAULT_TIMEOUT) -> dict:
    """Run one generator command and score its predictions.

    ``command`` is a shell-style command that reads tasks JSONL on stdin and
    writes predictions JSONL ({"id":..., "prediction":[...]}) on stdout.
    Returns a result dict with an explicit status; never raises for generator
    failure (a broken target must not abort the whole scorecard).
    """
    started = time.time()
    base = {"target": target_id, "command": command}
    try:
        get_target(target_id)  # validate against the registry
    except Exception:
        base["registry"] = "unregistered"
    if not command:
        return {**base, "status": "skipped", "score": None,
                "reason": "no generator command configured"}
    try:
        proc = subprocess.run(
            shlex.split(command), input=_tasks_jsonl(), text=True,
            capture_output=True, timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return {**base, "status": "timeout", "score": None,
                "elapsed_s": round(time.time() - started, 1),
                "reason": f"exceeded {timeout}s"}
    except Exception as e:  # generator binary missing, bad command, etc.
        return {**base, "status": "error", "score": None,
                "reason": f"{type(e).__name__}: {e}"}
    if proc.returncode != 0:
        return {**base, "status": "error", "score": None,
                "reason": f"exit {proc.returncode}: {(proc.stderr or '').strip()[:200]}"}
    if not proc.stdout.strip():
        return {**base, "status": "error", "score": None,
                "reason": "generator produced no predictions"}
    with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False,
                                     encoding="utf-8") as fh:
        fh.write(proc.stdout)
        path = fh.name
    try:
        report = score_file(path)
    except Exception as e:
        return {**base, "status": "error", "score": None,
                "reason": f"unscoreable predictions: {type(e).__name__}: {e}"}
    finally:
        Path(path).unlink(missing_ok=True)
    return {**base, "status": "ok", "score": report["overall"], "report": report,
            "elapsed_s": round(time.time() - started, 1)}


def run_scorecard(generators: dict[str, str], timeout: int = DEFAULT_TIMEOUT,
                  max_workers: int = 4) -> dict:
    """Fan out across targets, converge to one scorecard.

    ``generators`` maps target_id -> generator command. Targets run in parallel
    because they are genuinely independent; the scorecard is the convergence.
    """
    results: list[dict] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {pool.submit(run_target, tid, cmd, timeout): tid
                   for tid, cmd in generators.items()}
        for fut in concurrent.futures.as_completed(futures):
            results.append(fut.result())
    ok = [r for r in results if r["status"] == "ok"]
    ranked = sorted(ok, key=lambda r: r["score"], reverse=True)
    untested = [r for r in results if r["status"] != "ok"]
    registry_total = len(list_targets())
    return {
        "kipimo_tasks": len(load_tasks()),
        "targets_attempted": len(results),
        "targets_scored": len(ok),
        "targets_untested": len(untested),
        "registry_targets": registry_total,
        # coverage makes an incomplete run impossible to misread as complete
        "coverage": f"{len(ok)}/{registry_total} registry targets scored",
        "ranked": [{"target": r["target"], "score": r["score"],
                    "by_type": {k: v for k, v in r["report"].items()
                                if k not in ("overall", "n_tasks", "n_missing")},
                    "n_missing": r["report"]["n_missing"]} for r in ranked],
        "untested": [{"target": r["target"], "status": r["status"],
                      "reason": r.get("reason", "")} for r in untested],
        "caveat": ("Scores are stack-routing competence, not general Swahili fluency. "
                   "Untested targets have UNKNOWN scores — not zero. A partial "
                   "scorecard is not a ranking of the field."),
    }


def load_generators(path: str) -> dict[str, str]:
    """Load a target_id -> command mapping from a JSON file."""
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError("generators file must be a JSON object: {target_id: command}")
    return {str(k): str(v) for k, v in data.items()}
