#!/usr/bin/env python3
"""One-shot entrypoint for skill description optimization."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from run_eval import run_eval, find_project_root
from run_loop import run_loop
from utils import load_eval_set, parse_skill_md, update_skill_description


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run baseline eval + optimization loop for a skill description"
    )
    parser.add_argument("--eval-set", required=True, help="Path to eval set JSON")
    parser.add_argument("--skill-path", required=True, help="Path to skill directory")
    parser.add_argument("--num-workers", type=int, default=10)
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--runs-per-query", type=int, default=3)
    parser.add_argument("--trigger-threshold", type=float, default=0.5)
    parser.add_argument("--max-iterations", type=int, default=5)
    parser.add_argument("--holdout", type=float, default=0.4)
    parser.add_argument("--model", default=None)
    parser.add_argument("--apply", action="store_true", help="Apply best description to SKILL.md")
    parser.add_argument("--output", default=None, help="Write combined result JSON to this path")
    args = parser.parse_args()

    skill_path = Path(args.skill_path).resolve()
    eval_set = load_eval_set(Path(args.eval_set).resolve())
    name, description, _ = parse_skill_md(skill_path)

    baseline = run_eval(
        eval_set=eval_set,
        skill_name=name,
        description=description,
        num_workers=args.num_workers,
        timeout=args.timeout,
        project_root=find_project_root(skill_path),
        runs_per_query=args.runs_per_query,
        trigger_threshold=args.trigger_threshold,
        model=args.model,
    )

    optimized = run_loop(
        eval_set=eval_set,
        skill_path=skill_path,
        description_override=None,
        num_workers=args.num_workers,
        timeout=args.timeout,
        max_iterations=args.max_iterations,
        runs_per_query=args.runs_per_query,
        trigger_threshold=args.trigger_threshold,
        holdout=args.holdout,
        model=args.model,
    )

    if args.apply:
        update_skill_description(skill_path, optimized["best_description"])

    result = {
        "skill_name": name,
        "baseline": baseline,
        "optimized": optimized,
        "applied": bool(args.apply),
    }

    payload = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(payload + "\n", encoding="utf-8")
    else:
        print(payload)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
