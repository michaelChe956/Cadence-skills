#!/usr/bin/env python3
"""Run trigger evaluation for a skill description."""

from __future__ import annotations

import argparse
import json
import os
import select
import subprocess
import time
import uuid
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

from utils import load_eval_set, parse_skill_md


def find_project_root(start: Path | None = None) -> Path:
    current = (start or Path.cwd()).resolve()
    for parent in [current, *current.parents]:
        if (parent / ".claude").is_dir():
            return parent
    return current


def run_single_query(
    query: str,
    skill_name: str,
    skill_description: str,
    timeout: int,
    project_root: str,
    model: str | None,
) -> bool:
    project_root_path = Path(project_root)
    commands_dir = project_root_path / ".claude" / "commands"
    unique_id = uuid.uuid4().hex[:8]
    synthetic_name = f"{skill_name}-trigger-eval-{unique_id}"
    command_file = commands_dir / f"{synthetic_name}.md"

    commands_dir.mkdir(parents=True, exist_ok=True)
    indented_desc = "\n  ".join(skill_description.split("\n"))
    command_file.write_text(
        (
            "---\n"
            "description: |\n"
            f"  {indented_desc}\n"
            "---\n\n"
            f"# {skill_name}\n\n"
            f"This synthetic skill exists only for trigger evaluation: {skill_description}\n"
        ),
        encoding="utf-8",
    )

    cmd = [
        "claude",
        "-p",
        query,
        "--output-format",
        "stream-json",
        "--verbose",
        "--include-partial-messages",
    ]
    if model:
        cmd.extend(["--model", model])

    env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}

    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        cwd=str(project_root_path),
        env=env,
    )

    buffer = ""
    pending_tool = None
    partial_json = ""
    start_at = time.time()

    try:
        while time.time() - start_at < timeout:
            if process.poll() is not None:
                remaining = process.stdout.read() if process.stdout else b""
                if remaining:
                    buffer += remaining.decode("utf-8", errors="replace")
                break

            ready, _, _ = select.select([process.stdout], [], [], 1.0)
            if not ready:
                continue

            chunk = os.read(process.stdout.fileno(), 8192)
            if not chunk:
                break
            buffer += chunk.decode("utf-8", errors="replace")

            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                line = line.strip()
                if not line:
                    continue

                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue

                if event.get("type") == "stream_event":
                    se = event.get("event", {})
                    se_type = se.get("type", "")

                    if se_type == "content_block_start":
                        cb = se.get("content_block", {})
                        if cb.get("type") == "tool_use":
                            tool_name = cb.get("name", "")
                            if tool_name in ("Skill", "Read"):
                                pending_tool = tool_name
                                partial_json = ""
                            else:
                                return False

                    elif se_type == "content_block_delta" and pending_tool:
                        delta = se.get("delta", {})
                        if delta.get("type") == "input_json_delta":
                            partial_json += delta.get("partial_json", "")
                            if synthetic_name in partial_json:
                                return True

                    elif se_type in ("content_block_stop", "message_stop"):
                        if pending_tool:
                            return synthetic_name in partial_json
                        if se_type == "message_stop":
                            return False

                elif event.get("type") == "assistant":
                    message = event.get("message", {})
                    for c in message.get("content", []):
                        if c.get("type") != "tool_use":
                            continue
                        tool_name = c.get("name", "")
                        tool_input = c.get("input", {})
                        if tool_name == "Skill" and synthetic_name in str(tool_input):
                            return True
                        if tool_name == "Read" and synthetic_name in str(tool_input):
                            return True
                        return False

        return False
    finally:
        if process.poll() is None:
            process.kill()
            process.wait()
        if command_file.exists():
            command_file.unlink()


def run_eval(
    eval_set: list[dict],
    skill_name: str,
    description: str,
    num_workers: int,
    timeout: int,
    project_root: Path,
    runs_per_query: int,
    trigger_threshold: float,
    model: str | None,
) -> dict:
    futures = {}
    query_runs: dict[str, list[bool]] = {}
    query_expect: dict[str, bool] = {}

    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        for item in eval_set:
            query = item["query"]
            query_expect[query] = item["should_trigger"]
            query_runs.setdefault(query, [])
            for _ in range(runs_per_query):
                future = executor.submit(
                    run_single_query,
                    query,
                    skill_name,
                    description,
                    timeout,
                    str(project_root),
                    model,
                )
                futures[future] = query

        for future in as_completed(futures):
            query = futures[future]
            try:
                query_runs[query].append(bool(future.result()))
            except Exception:
                query_runs[query].append(False)

    results = []
    passed = 0
    for item in eval_set:
        query = item["query"]
        runs = query_runs[query]
        trigger_count = sum(1 for x in runs if x)
        rate = (trigger_count / len(runs)) if runs else 0.0
        expected = query_expect[query]
        inferred = rate >= trigger_threshold
        ok = inferred == expected
        if ok:
            passed += 1

        results.append(
            {
                "query": query,
                "should_trigger": expected,
                "runs": len(runs),
                "triggers": trigger_count,
                "trigger_rate": round(rate, 4),
                "threshold": trigger_threshold,
                "pass": ok,
            }
        )

    total = len(results)
    return {
        "results": results,
        "summary": {
            "passed": passed,
            "failed": total - passed,
            "total": total,
            "accuracy": round((passed / total), 4) if total else 0.0,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run trigger evaluation for a skill description")
    parser.add_argument("--eval-set", required=True, help="Path to eval set JSON file")
    parser.add_argument("--skill-path", required=True, help="Path to skill directory")
    parser.add_argument("--description", default=None, help="Override description")
    parser.add_argument("--num-workers", type=int, default=10)
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--runs-per-query", type=int, default=3)
    parser.add_argument("--trigger-threshold", type=float, default=0.5)
    parser.add_argument("--model", default=None, help="Model passed to `claude -p`")
    parser.add_argument("--output", default=None, help="Optional path for output JSON")
    args = parser.parse_args()

    eval_set = load_eval_set(Path(args.eval_set).resolve())
    skill_path = Path(args.skill_path).resolve()
    name, description, _ = parse_skill_md(skill_path)
    project_root = find_project_root(skill_path)

    output = run_eval(
        eval_set=eval_set,
        skill_name=name,
        description=args.description or description,
        num_workers=args.num_workers,
        timeout=args.timeout,
        project_root=project_root,
        runs_per_query=args.runs_per_query,
        trigger_threshold=args.trigger_threshold,
        model=args.model,
    )

    payload = json.dumps(output, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(payload + "\n", encoding="utf-8")
    else:
        print(payload)

    return 0 if output["summary"]["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
