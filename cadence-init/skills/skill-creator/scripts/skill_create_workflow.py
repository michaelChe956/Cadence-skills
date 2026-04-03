#!/usr/bin/env python3
"""One-shot workflow for creating and preparing a skill for Claude Code."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from init_skill import init_skill
from package_skill import package_skill
from quick_validate import validate_skill


def run_cmd(cmd: list[str]) -> None:
    result = subprocess.run(cmd, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(cmd)}")


def ask_bool(prompt: str, default: bool = False) -> bool:
    suffix = "[Y/n]" if default else "[y/N]"
    answer = input(f"{prompt} {suffix} ").strip().lower()
    if not answer:
        return default
    return answer in {"y", "yes"}


def collect_interactive_args(args: argparse.Namespace, repo_root: Path) -> argparse.Namespace:
    if not args.skill_name:
        args.skill_name = input("Skill name (e.g. api-doc-audit): ").strip()
    if not args.skill_name:
        raise ValueError("skill-name is required")

    if not args.target:
        use_project = ask_bool("Install as PROJECT skill (.claude/skills in current project)?", default=True)
        if use_project:
            args.target = "project"
        else:
            use_global = ask_bool("Install as Claude Code GLOBAL skill (~/.claude/skills)?", default=False)
            args.target = "global" if use_global else "repo"

    if not args.package and not args.optimize:
        args.package = ask_bool("Package .skill file?", default=True)
        args.optimize = ask_bool("Run description optimization?", default=False)

    if args.optimize and not args.eval_set:
        default_eval = (
            repo_root / "skills" / "skill-creator" / "scripts" / "examples" / "eval_set.sample.json"
        )
        use_default = ask_bool(f"Use default eval set: {default_eval} ?", default=True)
        args.eval_set = str(default_eval) if use_default else input("Eval set path: ").strip()

    if args.optimize and not args.apply:
        args.apply = ask_bool("Apply best description to SKILL.md?", default=True)

    return args


def ensure_frontmatter(skill_name: str, content: str) -> str:
    if content.lstrip().startswith("---"):
        return content if content.endswith("\n") else content + "\n"
    synthesized = (
        f"---\n"
        f"name: {skill_name}\n"
        f"description: Use this skill for {skill_name} related tasks.\n"
        f"---\n\n"
    )
    merged = synthesized + content.lstrip()
    return merged if merged.endswith("\n") else merged + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Create, validate, package, and optionally optimize a skill")
    parser.add_argument("--skill-name", required=False, help="Skill directory/name, e.g. api-doc-audit")
    parser.add_argument(
        "--target",
        choices=["repo", "project", "global"],
        default=None,
        help="Install target. repo=./skills, project=./.claude/skills, global=~/.claude/skills",
    )
    parser.add_argument("--skills-root", default=None, help="Skills root directory (default: repo/skills)")
    parser.add_argument(
        "--source-md",
        default=None,
        help="Optional markdown source file to import as SKILL.md (auto-adds frontmatter if missing)",
    )
    parser.add_argument("--output-dir", default="dist", help="Directory for packaged .skill output")
    parser.add_argument("--package", action="store_true", help="Package the skill into .skill")
    parser.add_argument("--optimize", action="store_true", help="Run description optimization loop")
    parser.add_argument("--eval-set", default=None, help="Eval set JSON path used by optimization")
    parser.add_argument("--max-iterations", type=int, default=5)
    parser.add_argument("--runs-per-query", type=int, default=3)
    parser.add_argument("--num-workers", type=int, default=10)
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--trigger-threshold", type=float, default=0.5)
    parser.add_argument("--holdout", type=float, default=0.4)
    parser.add_argument("--model", default=None)
    parser.add_argument("--apply", action="store_true", help="Apply best description after optimization")
    parser.add_argument("--opt-output", default=None, help="Output path for optimization JSON")
    parser.add_argument("--interactive", action="store_true", help="Interactive wizard mode")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[2]
    if args.interactive:
        args = collect_interactive_args(args, repo_root)
    elif not args.skill_name:
        parser.error("--skill-name is required unless --interactive is used")
    if not args.target:
        args.target = "repo"

    default_repo_root = repo_root / "skills"
    default_project_root = repo_root / ".claude" / "skills"
    default_global_root = Path.home() / ".claude" / "skills"
    if args.skills_root:
        skills_root = Path(args.skills_root).expanduser().resolve()
    else:
        if args.target == "global":
            skills_root = default_global_root
        elif args.target == "project":
            skills_root = default_project_root
        else:
            skills_root = default_repo_root
    skill_dir = skills_root / args.skill_name

    result: dict[str, object] = {
        "skill_name": args.skill_name,
        "target": args.target,
        "skills_root": str(skills_root),
        "skill_path": str(skill_dir),
        "created": False,
        "validated": False,
        "packaged": False,
        "package_path": None,
        "optimized": False,
        "optimization_output": None,
    }

    if not skill_dir.exists():
        created_path = init_skill(args.skill_name, skills_root)
        result["created"] = True
        result["skill_path"] = str(created_path)

    if args.source_md:
        src = Path(args.source_md).expanduser().resolve()
        if not src.exists():
            raise FileNotFoundError(f"source markdown not found: {src}")
        imported = ensure_frontmatter(args.skill_name, src.read_text(encoding="utf-8"))
        (skill_dir / "SKILL.md").write_text(imported, encoding="utf-8")
        result["imported_source"] = str(src)

    valid, msg = validate_skill(skill_dir)
    if not valid:
        print(msg)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 1
    result["validated"] = True

    if args.package:
        package_out = package_skill(skill_dir, Path(args.output_dir).resolve())
        result["packaged"] = True
        result["package_path"] = str(package_out)

    if args.optimize:
        eval_set = args.eval_set or str(
            repo_root / "skills" / "skill-creator" / "scripts" / "examples" / "eval_set.sample.json"
        )
        opt_output = args.opt_output or str(Path("/tmp") / f"{args.skill_name}-optimize.json")

        cmd = [
            sys.executable,
            str(repo_root / "skills" / "skill-creator" / "scripts" / "optimize_description.py"),
            "--eval-set",
            eval_set,
            "--skill-path",
            str(skill_dir),
            "--max-iterations",
            str(args.max_iterations),
            "--runs-per-query",
            str(args.runs_per_query),
            "--num-workers",
            str(args.num_workers),
            "--timeout",
            str(args.timeout),
            "--trigger-threshold",
            str(args.trigger_threshold),
            "--holdout",
            str(args.holdout),
            "--output",
            opt_output,
        ]
        if args.model:
            cmd.extend(["--model", args.model])
        if args.apply:
            cmd.append("--apply")

        run_cmd(cmd)
        result["optimized"] = True
        result["optimization_output"] = opt_output

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
