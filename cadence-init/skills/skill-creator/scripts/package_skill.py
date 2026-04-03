#!/usr/bin/env python3
"""Package a skill directory into a .skill zip archive."""

from __future__ import annotations

import fnmatch
import sys
import zipfile
from pathlib import Path

from quick_validate import validate_skill

EXCLUDE_DIRS = {"__pycache__", "node_modules", ".git"}
EXCLUDE_FILES = {".DS_Store"}
EXCLUDE_GLOBS = {"*.pyc"}
ROOT_EXCLUDE_DIRS = {"evals"}


def should_exclude(arcname: Path) -> bool:
    parts = arcname.parts
    if any(part in EXCLUDE_DIRS for part in parts):
        return True
    if len(parts) > 1 and parts[1] in ROOT_EXCLUDE_DIRS:
        return True
    if arcname.name in EXCLUDE_FILES:
        return True
    return any(fnmatch.fnmatch(arcname.name, pat) for pat in EXCLUDE_GLOBS)


def package_skill(skill_dir: Path, output_dir: Path | None = None) -> Path:
    valid, msg = validate_skill(skill_dir)
    if not valid:
        raise ValueError(msg)

    output_root = output_dir.resolve() if output_dir else Path.cwd()
    output_root.mkdir(parents=True, exist_ok=True)

    out_file = output_root / f"{skill_dir.name}.skill"
    with zipfile.ZipFile(out_file, "w", zipfile.ZIP_DEFLATED) as zf:
        for file_path in skill_dir.rglob("*"):
            if not file_path.is_file():
                continue
            arcname = file_path.relative_to(skill_dir.parent)
            if should_exclude(arcname):
                continue
            zf.write(file_path, arcname)

    return out_file


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python skills/skill-creator/scripts/package_skill.py <skill-directory> [output-directory]")
        return 1

    skill_dir = Path(sys.argv[1]).resolve()
    output_dir = Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else None

    try:
        out_file = package_skill(skill_dir, output_dir)
    except ValueError as exc:
        print(f"Error: {exc}")
        return 1

    print(f"Packaged: {out_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
