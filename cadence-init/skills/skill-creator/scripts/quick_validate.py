#!/usr/bin/env python3
"""Quick validator for Claude Code skill folders."""

from __future__ import annotations

import re
import sys
from pathlib import Path

NAME_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]{0,39}$")


def _extract_frontmatter(skill_md: str) -> dict[str, str]:
    lines = skill_md.splitlines()
    if len(lines) < 3 or lines[0].strip() != "---":
        raise ValueError("SKILL.md must start with YAML frontmatter (---)")

    end_idx = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end_idx = i
            break
    if end_idx is None:
        raise ValueError("SKILL.md frontmatter is not closed with ---")

    fields: dict[str, str] = {}
    for line in lines[1:end_idx]:
        if ":" not in line:
            continue
        key, val = line.split(":", 1)
        fields[key.strip()] = val.strip().strip('"').strip("'")
    return fields


def validate_skill(skill_dir: Path) -> tuple[bool, str]:
    if not skill_dir.exists() or not skill_dir.is_dir():
        return False, f"Skill directory not found: {skill_dir}"

    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        return False, "Missing SKILL.md"

    try:
        frontmatter = _extract_frontmatter(skill_md.read_text(encoding="utf-8"))
    except ValueError as exc:
        return False, str(exc)

    name = frontmatter.get("name", "")
    description = frontmatter.get("description", "")

    if not name:
        return False, "Frontmatter missing 'name'"
    if name != skill_dir.name:
        return False, f"Frontmatter name '{name}' must match directory '{skill_dir.name}'"
    if not NAME_PATTERN.match(name):
        return False, "Invalid name format"

    if not description:
        return False, "Frontmatter missing 'description'"
    if len(description) > 1024:
        return False, "Description is too long (max 1024 characters)"

    return True, "Skill is valid"


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python skills/skill-creator/scripts/quick_validate.py <skill-directory>")
        return 1

    valid, msg = validate_skill(Path(sys.argv[1]).resolve())
    print(msg)
    return 0 if valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
