---
name: skill-creator
description: Use this skill whenever the user asks to create, modify, validate, package, or optimize Claude Code skills in this repository or marketplace. Always use it for requests about SKILL.md authoring, skill scaffold generation, trigger evals, or .skill packaging.
---

# Skill Creator

## Overview

Create and maintain Claude Code skills that can be installed through the Cadence marketplace and used directly in Claude Code.

## When To Use

Use this skill when the user asks to:
- create a new skill
- edit an existing skill
- validate skill frontmatter or structure
- package a skill into `.skill`
- evaluate or optimize skill description trigger behavior

## Repository Contract

- Skill directories live in `skills/<skill-name>/`
- Every skill must contain `SKILL.md`
- `name` in frontmatter must equal directory name
- Optional directories: `scripts/`, `references/`, `assets/`
- For project-local Claude Code usage, prefer `.claude/skills/<skill-name>/SKILL.md`
- Use `~/.claude/skills/<skill-name>/SKILL.md` only when the skill should be shared across projects

## Execution Workflow

0. One-shot workflow (recommended in most cases):
```bash
python skills/skill-creator/scripts/skill_create_workflow.py --skill-name <skill-name> --package --optimize --apply
```

0b. One-shot workflow for project-local Claude Code skill (preferred for direct usage in the current project):
```bash
python skills/skill-creator/scripts/skill_create_workflow.py --skill-name <skill-name> --target project
```

0c. One-shot workflow for Claude Code GLOBAL skill:
```bash
python skills/skill-creator/scripts/skill_create_workflow.py --skill-name <skill-name> --target global
```

1. Scaffold a new skill:
```bash
python skills/skill-creator/scripts/init_skill.py <skill-name>
```

2. Validate structure:
```bash
python skills/skill-creator/scripts/quick_validate.py skills/<skill-name>
```

3. Package distributable file:
```bash
python skills/skill-creator/scripts/package_skill.py skills/<skill-name> dist
```

4. Evaluate current description trigger quality:
```bash
python skills/skill-creator/scripts/run_eval.py --eval-set <eval-set.json> --skill-path skills/<skill-name>
```

5. Optimize description in loop:
```bash
python skills/skill-creator/scripts/run_loop.py --eval-set <eval-set.json> --skill-path skills/<skill-name> --max-iterations 5 --apply
```

6. One-shot optimization (recommended):
```bash
python skills/skill-creator/scripts/optimize_description.py --eval-set <eval-set.json> --skill-path skills/<skill-name> --max-iterations 5 --apply
```

## Output Requirements

When completing a skill task, always report:
- target skill path
- validation result
- package path (if generated)
- eval/optimization output path (if generated)
