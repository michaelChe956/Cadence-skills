# README no-interrupt 使用说明实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. 本任务在当前会话内执行，不使用子 Agent。

**Goal:** 在三个主要 README 入口中补充 `no-interrupt` 使用方法，并确保普通模式兼容性描述一致。

**Architecture:** 根 README 作为完整说明来源，提供参数语法和四个 Skill 行为对照表；命令指南与 Skills 指南只提供初始化示例、兼容性提醒和根 README 链接，减少重复内容。

**Tech Stack:** Markdown、`rg`、Git 差异检查。

## Global Constraints

- 不带参数时保持四个 Skill 原有逻辑。
- `no-interrupt` 与 `--no-interrupt` 等价。
- 严格模式无法自动完成时直接报错，不发起用户交互。
- 不修改四个 `SKILL.md` 的已实现语义。

---

### Task 1: 更新根 README

**Files:**

- Modify: `README.md`

- [x] 在“初始化 Skill 说明”后增加“强制无交互模式”章节。
- [x] 增加四条调用命令和 `--no-interrupt` 等价说明。
- [x] 增加四个 Skill 的严格模式行为对照表。
- [x] 明确不加参数保持原逻辑，严格模式失败直接终止。
- [x] 在初始化步骤中增加一组可选的全程强制无交互示例。

### Task 2: 更新命令指南

**Files:**

- Modify: `readmes/commands/README.md`

- [x] 在“新项目开始”组合后增加 `no-interrupt` 初始化命令组。
- [x] 说明普通模式不受影响、严格模式失败直接终止。
- [x] 链接根 README 的项目初始化章节获取完整行为差异。

### Task 3: 更新 Skills 指南

**Files:**

- Modify: `readmes/skills/README.md`

- [x] 在“新项目开发”场景后增加严格模式示例。
- [x] 说明参数仅适用于四个目标 Skill，不用于 `/project-analysis` 或 `/init`。
- [x] 链接根 README 的项目初始化章节。

### Task 4: 验证一致性

**Files:**

- Validate: `README.md`
- Validate: `readmes/commands/README.md`
- Validate: `readmes/skills/README.md`

- [x] 运行 `rg -n 'no-interrupt|--no-interrupt'`，确认三个 README 均有说明。
- [x] 检查三个 README 均包含“不加参数保持原逻辑”的语义。
- [x] 运行 `git diff --check`，确认无 Markdown 空白错误。
- [x] 检查 Git 状态，确认只包含设计、计划和三个 README 变更。
