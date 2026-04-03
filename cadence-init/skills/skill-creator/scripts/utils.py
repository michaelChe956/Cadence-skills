#!/usr/bin/env python3
"""Shared utilities for skill creator scripts."""

from __future__ import annotations

import json
from pathlib import Path


def parse_skill_md(skill_dir: Path) -> tuple[str, str, str]:
    """Return (name, description, full_content) from SKILL.md frontmatter."""
    skill_md = skill_dir / "SKILL.md"
    content = skill_md.read_text(encoding="utf-8")
    lines = content.splitlines()

    if not lines or lines[0].strip() != "---":
        raise ValueError("SKILL.md missing frontmatter opening '---'")

    end_idx = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end_idx = i
            break
    if end_idx is None:
        raise ValueError("SKILL.md missing frontmatter closing '---'")

    name = ""
    description = ""
    fm = lines[1:end_idx]
    i = 0
    while i < len(fm):
        line = fm[i]
        if line.startswith("name:"):
            name = line.split(":", 1)[1].strip().strip('"').strip("'")
        elif line.startswith("description:"):
            raw = line.split(":", 1)[1].strip()
            if raw in ("|", ">", "|-", ">-"):
                multi = []
                i += 1
                while i < len(fm) and (fm[i].startswith("  ") or fm[i].startswith("\t")):
                    multi.append(fm[i].strip())
                    i += 1
                description = " ".join(multi).strip()
                continue
            description = raw.strip('"').strip("'")
        i += 1

    return name, description, content


def _quote_yaml_scalar(value: str) -> str:
    escaped = value.replace('"', '\\"')
    return f'"{escaped}"'


def update_skill_description(skill_dir: Path, new_description: str) -> None:
    """Update description in SKILL.md frontmatter."""
    skill_md = skill_dir / "SKILL.md"
    content = skill_md.read_text(encoding="utf-8")
    lines = content.splitlines()

    if not lines or lines[0].strip() != "---":
        raise ValueError("SKILL.md missing frontmatter")

    end_idx = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end_idx = i
            break
    if end_idx is None:
        raise ValueError("SKILL.md frontmatter not closed")

    replaced = False
    for i in range(1, end_idx):
        if lines[i].startswith("description:"):
            lines[i] = f"description: {_quote_yaml_scalar(new_description.strip())}"
            replaced = True
            break

    if not replaced:
        lines.insert(end_idx, f"description: {_quote_yaml_scalar(new_description.strip())}")

    skill_md.write_text("\n".join(lines) + "\n", encoding="utf-8")


def load_eval_set(eval_set_path: Path) -> list[dict]:
    """Load eval set JSON with schema: [{query, should_trigger}, ...]."""
    payload = json.loads(eval_set_path.read_text(encoding="utf-8"))

    if not isinstance(payload, list):
        raise ValueError("eval-set must be a JSON array")

    normalized: list[dict] = []
    for i, item in enumerate(payload):
        if not isinstance(item, dict):
            raise ValueError(f"eval item {i} must be an object")
        query = item.get("query")
        should_trigger = item.get("should_trigger")
        if not isinstance(query, str) or not query.strip():
            raise ValueError(f"eval item {i} has invalid query")
        if not isinstance(should_trigger, bool):
            raise ValueError(f"eval item {i} has invalid should_trigger")
        normalized.append({"query": query.strip(), "should_trigger": should_trigger})

    return normalized
