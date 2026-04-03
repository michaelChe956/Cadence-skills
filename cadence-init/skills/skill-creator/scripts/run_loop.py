#!/usr/bin/env python3
"""Run description optimization loop for a skill."""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

from improve_description import improve_description
from run_eval import find_project_root, run_eval
from utils import load_eval_set, parse_skill_md, update_skill_description


def split_eval_set(eval_set: list[dict], holdout: float, seed: int = 42) -> tuple[list[dict], list[dict]]:
    random.seed(seed)
    positives = [e for e in eval_set if e["should_trigger"]]
    negatives = [e for e in eval_set if not e["should_trigger"]]

    random.shuffle(positives)
    random.shuffle(negatives)

    n_pos_test = max(1, int(len(positives) * holdout)) if positives else 0
    n_neg_test = max(1, int(len(negatives) * holdout)) if negatives else 0

    test_set = positives[:n_pos_test] + negatives[:n_neg_test]
    train_set = positives[n_pos_test:] + negatives[n_neg_test:]

    if not train_set:
        train_set = test_set
    return train_set, test_set


def run_loop(
    eval_set: list[dict],
    skill_path: Path,
    description_override: str | None,
    num_workers: int,
    timeout: int,
    max_iterations: int,
    runs_per_query: int,
    trigger_threshold: float,
    holdout: float,
    model: str | None,
) -> dict:
    project_root = find_project_root(skill_path)
    name, original_description, content = parse_skill_md(skill_path)
    current_description = description_override or original_description

    if holdout > 0:
        train_set, test_set = split_eval_set(eval_set, holdout)
    else:
        train_set, test_set = eval_set, []

    history = []
    exit_reason = "max_iterations"

    for iteration in range(1, max_iterations + 1):
        all_set = train_set + test_set
        all_res = run_eval(
            eval_set=all_set,
            skill_name=name,
            description=current_description,
            num_workers=num_workers,
            timeout=timeout,
            project_root=project_root,
            runs_per_query=runs_per_query,
            trigger_threshold=trigger_threshold,
            model=model,
        )

        train_queries = {x["query"] for x in train_set}
        train_results = [r for r in all_res["results"] if r["query"] in train_queries]
        test_results = [r for r in all_res["results"] if r["query"] not in train_queries]

        train_passed = sum(1 for r in train_results if r["pass"])
        test_passed = sum(1 for r in test_results if r["pass"])

        history.append(
            {
                "iteration": iteration,
                "description": current_description,
                "train_passed": train_passed,
                "train_total": len(train_results),
                "train_results": train_results,
                "test_passed": test_passed if test_set else None,
                "test_total": len(test_results) if test_set else None,
                "test_results": test_results if test_set else None,
            }
        )

        if train_passed == len(train_results):
            exit_reason = f"all_train_passed_at_{iteration}"
            break

        if iteration == max_iterations:
            break

        blinded_history = [{k: v for k, v in h.items() if not k.startswith("test_")} for h in history]
        current_description = improve_description(
            skill_name=name,
            skill_content=content,
            current_description=current_description,
            eval_results={
                "results": train_results,
                "summary": {
                    "passed": train_passed,
                    "failed": len(train_results) - train_passed,
                    "total": len(train_results),
                },
            },
            history=blinded_history,
            model=model,
        )

    if test_set:
        best = max(history, key=lambda h: h.get("test_passed") or 0)
        best_score = f"{best.get('test_passed', 0)}/{best.get('test_total', 0)}"
    else:
        best = max(history, key=lambda h: h.get("train_passed", 0))
        best_score = f"{best.get('train_passed', 0)}/{best.get('train_total', 0)}"

    return {
        "skill_name": name,
        "original_description": original_description,
        "best_description": best["description"],
        "best_score": best_score,
        "iterations_run": len(history),
        "exit_reason": exit_reason,
        "holdout": holdout,
        "train_size": len(train_set),
        "test_size": len(test_set),
        "history": history,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run eval + improve loop")
    parser.add_argument("--eval-set", required=True)
    parser.add_argument("--skill-path", required=True)
    parser.add_argument("--description", default=None)
    parser.add_argument("--num-workers", type=int, default=10)
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--max-iterations", type=int, default=5)
    parser.add_argument("--runs-per-query", type=int, default=3)
    parser.add_argument("--trigger-threshold", type=float, default=0.5)
    parser.add_argument("--holdout", type=float, default=0.4)
    parser.add_argument("--model", default=None, help="Model passed to `claude -p`")
    parser.add_argument("--output", default=None, help="Output JSON path")
    parser.add_argument("--apply", action="store_true", help="Apply best_description to SKILL.md")
    args = parser.parse_args()

    eval_set = load_eval_set(Path(args.eval_set).resolve())
    skill_path = Path(args.skill_path).resolve()

    result = run_loop(
        eval_set=eval_set,
        skill_path=skill_path,
        description_override=args.description,
        num_workers=args.num_workers,
        timeout=args.timeout,
        max_iterations=args.max_iterations,
        runs_per_query=args.runs_per_query,
        trigger_threshold=args.trigger_threshold,
        holdout=args.holdout,
        model=args.model,
    )

    if args.apply:
        update_skill_description(skill_path, result["best_description"])

    payload = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(payload + "\n", encoding="utf-8")
    else:
        print(payload)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
