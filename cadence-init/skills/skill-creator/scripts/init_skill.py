#!/usr/bin/env python3
"""Initialize a Claude Code skill scaffold."""

from __future__ import annotations

import re
import sys
from pathlib import Path

NAME_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]{0,39}$")

SKILL_TEMPLATE = """---
name: {skill_name}
description: Use this skill for [TODO: specific scenarios]. This skill helps with [TODO: core capability].
---

# {skill_title}

## Overview

[TODO] Describe what this skill does and when to use it.

## Workflow

1. Understand the user's goal and constraints.
2. Choose the most suitable approach for the task.
3. Produce output in the expected format.
4. Verify the result before returning.

## Output Contract

- Keep output concise and actionable.
- Include assumptions when context is missing.
- Provide next steps only when useful.

## References

- Read `references/guide.md` when domain rules are needed.
- Use scripts in `scripts/` for deterministic work.
"""

REFERENCE_TEMPLATE = """# {skill_title} Reference

Add stable reference content here:
- Domain rules
- Input/output schemas
- Edge cases
"""

SCRIPT_TEMPLATE = '''#!/usr/bin/env python3
"""Example helper script for {skill_name}."""


def main() -> None:
    print("Replace this script with deterministic helper logic.")


if __name__ == "__main__":
    main()
'''


def _title_from_name(skill_name: str) -> str:
    return " ".join(part.capitalize() for part in skill_name.split("-"))


def _validate_name(skill_name: str) -> None:
    if not NAME_PATTERN.match(skill_name):
        raise ValueError(
            "Invalid skill name. Use lowercase letters, digits, and hyphens only; max length is 40."
        )


def init_skill(skill_name: str, skills_root: Path) -> Path:
    _validate_name(skill_name)

    skill_dir = skills_root / skill_name
    if skill_dir.exists():
        raise FileExistsError(f"Skill already exists: {skill_dir}")

    skill_dir.mkdir(parents=True, exist_ok=False)
    (skill_dir / "scripts").mkdir()
    (skill_dir / "references").mkdir()
    (skill_dir / "assets").mkdir()

    skill_title = _title_from_name(skill_name)
    (skill_dir / "SKILL.md").write_text(
        SKILL_TEMPLATE.format(skill_name=skill_name, skill_title=skill_title),
        encoding="utf-8",
    )
    (skill_dir / "references" / "guide.md").write_text(
        REFERENCE_TEMPLATE.format(skill_title=skill_title),
        encoding="utf-8",
    )

    script_path = skill_dir / "scripts" / "example.py"
    script_path.write_text(SCRIPT_TEMPLATE.format(skill_name=skill_name), encoding="utf-8")
    script_path.chmod(0o755)

    (skill_dir / "assets" / "README.txt").write_text(
        "Put templates, icons, or static files used by this skill here.\n",
        encoding="utf-8",
    )

    return skill_dir


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python skills/skill-creator/scripts/init_skill.py <skill-name> [skills-root]")
        return 1

    skill_name = sys.argv[1].strip()
    skills_root = (
        Path(sys.argv[2]).resolve()
        if len(sys.argv) >= 3
        else (Path(__file__).resolve().parents[2] / "skills")
    )

    try:
        skill_dir = init_skill(skill_name, skills_root)
    except (ValueError, FileExistsError) as exc:
        print(f"Error: {exc}")
        return 1

    print(f"Skill initialized: {skill_dir}")
    print("Next: edit SKILL.md, then run quick_validate.py and package_skill.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
