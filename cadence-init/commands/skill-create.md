---
skill: skill-creator
---

# /skill-create - Skill 创建与优化

调用 `skill-creator` skill，创建或维护 Claude Code 可直接使用的 skills。

## 使用场景

- 新建 skill（初始化目录与模板）
- 修改现有 skill（重写流程、补充 references/scripts）
- 校验 skill 结构与 frontmatter
- 打包 `.skill` 供 marketplace/离线分发
- 评测并优化 description 触发率

## 调用方式

```bash
/skill-create
```

## 推荐执行模板

```bash
# 交互式向导（推荐新手）
python skills/skill-creator/scripts/skill_create_workflow.py --interactive

# 直接创建当前项目可用的 Claude Code Skill（推荐）
python skills/skill-creator/scripts/skill_create_workflow.py \
  --skill-name my-new-skill \
  --target project

# 直接创建 Claude Code 全局 Skill
python skills/skill-creator/scripts/skill_create_workflow.py \
  --skill-name my-new-skill \
  --target global

# 把现有 markdown 一步导入为项目级 Skill
python skills/skill-creator/scripts/skill_create_workflow.py \
  --skill-name pdd-question \
  --target project \
  --source-md .claude/pdd-question.md

# 把现有 markdown 一步导入为全局 Skill
python skills/skill-creator/scripts/skill_create_workflow.py \
  --skill-name pdd-question \
  --target global \
  --source-md .claude/pdd-question.md

# 只创建 + 校验（不打包）
python skills/skill-creator/scripts/skill_create_workflow.py \
  --skill-name my-new-skill

# 创建 + 打包
python skills/skill-creator/scripts/skill_create_workflow.py \
  --skill-name my-new-skill \
  --package \
  --output-dir dist

# 创建 + 打包 + 触发率优化（并写回 description）
python skills/skill-creator/scripts/skill_create_workflow.py \
  --skill-name my-new-skill \
  --target project \
  --package \
  --optimize \
  --eval-set skills/skill-creator/scripts/examples/eval_set.skill-creator.20.json \
  --max-iterations 5 \
  --runs-per-query 3 \
  --apply
```

## Skill 生效说明

- 当使用 `--target project` 时，Skill 会写入 `.claude/skills/<skill-name>/SKILL.md`
- 当使用 `--target global` 时，Skill 会写入 `~/.claude/skills/<skill-name>/SKILL.md`
- 未显式指定时，非交互模式默认仍为仓库内 `skills/<skill-name>/`

## 详细文档

查看完整 Skill 文档：[skill-creator/SKILL.md](../skills/skill-creator/SKILL.md)
