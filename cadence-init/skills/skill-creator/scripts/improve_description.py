#!/usr/bin/env python3
"""Improve a skill description based on eval results using `claude -p`."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
from pathlib import Path

from utils import parse_skill_md


def _call_claude(prompt: str, model: str | None, timeout: int = 300) -> str:
    cmd = ["claude", "-p", "--output-format", "text"]
    if model:
        cmd.extend(["--model", model])

    env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}
    result = subprocess.run(
        cmd,
        input=prompt,
        capture_output=True,
        text=True,
        env=env,
        timeout=timeout,
    )
    if result.returncode != 0:
        raise RuntimeError(f"claude -p failed: {result.stderr}")
    return result.stdout.strip()


def improve_description(
    skill_name: str,
    skill_content: str,
    current_description: str,
    eval_results: dict,
    history: list[dict],
    model: str | None,
) -> str:
    failures = [r for r in eval_results.get("results", []) if not r.get("pass")]

    prompt = f"""You are optimizing a Claude Code skill description.

Skill name: {skill_name}
Current description:
{current_description}

Recent failures:
{json.dumps(failures, ensure_ascii=False, indent=2)}

History:
{json.dumps(history[-5:], ensure_ascii=False, indent=2)}

SKILL.md content:
{skill_content}

Task:
Return ONLY a new single-line description that improves trigger precision and recall.
Rules:
- Mention when to use the skill and typical user wording/context.
- Avoid hype and vague claims.
- Max length 300 chars.
- No markdown, no code block, no extra commentary.
"""

    improved = _call_claude(prompt, model=model)
    improved = improved.strip().strip('"').strip("'")
    if not improved:
        return current_description
    if len(improved) > 300:
        return improved[:300].rstrip()
    return improved


def main() -> int:
    parser = argparse.ArgumentParser(description="Improve skill description")
    parser.add_argument("--eval-results", required=True, help="Path to run_eval output json")
    parser.add_argument("--skill-path", required=True)
    parser.add_argument("--history", default=None, help="Optional history json")
    parser.add_argument("--model", default=None)
    args = parser.parse_args()

    eval_results = json.loads(Path(args.eval_results).read_text(encoding="utf-8"))
    history = []
    if args.history:
        history = json.loads(Path(args.history).read_text(encoding="utf-8"))

    skill_path = Path(args.skill_path).resolve()
    name, description, content = parse_skill_md(skill_path)
    print(
        improve_description(
            skill_name=name,
            skill_content=content,
            current_description=description,
            eval_results=eval_results,
            history=history,
            model=args.model,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
