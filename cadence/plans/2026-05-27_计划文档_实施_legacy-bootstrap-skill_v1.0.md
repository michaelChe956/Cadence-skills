# legacy-bootstrap skill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 `cadence-init` 插件中新增 `legacy-bootstrap` command 与 skill，用 repomix 对当前本地 legacy 项目进行标准化 bootstrap，并把项目认知沉淀到 `cadence/` 与入口文档中。

**Architecture:** 该实现是文档型插件能力，不编写脚本或业务代码。`commands/legacy-bootstrap.md` 作为用户显式入口，`skills/legacy-bootstrap/SKILL.md` 承载完整 SOP；skill 默认使用 `npx repomix@latest`，分析当前打开的本地项目，并要求更新目标项目 `CLAUDE.md` 与 `AGENTS.md`。

**Tech Stack:** Markdown、Claude Code Skill frontmatter、Cadence plugin directory conventions、Repomix CLI。

---

## File Structure

- Create: `cadence-init/skills/legacy-bootstrap/SKILL.md`
  - 负责完整 legacy bootstrap SOP。
  - 包含 frontmatter、使用场景、检查清单、流程、repomix 参数策略、Cadence 产物模板、`CLAUDE.md` / `AGENTS.md` 更新策略、错误处理和完成汇报。
- Create: `cadence-init/commands/legacy-bootstrap.md`
  - 负责命令入口说明。
  - 通过 frontmatter 指向 `legacy-bootstrap` skill。
  - 简述输入、流程、输出和使用约束。
- Modify: no existing source files
  - 不修改 `cadence-init/.claude-plugin/plugin.json`，因为现有插件 manifest 不逐项枚举 command 或 skill。
  - 不修改 `.claude/rules/`，该目录是框架规则目录。

## Task 1: Create legacy-bootstrap Skill

**Files:**

- Create: `cadence-init/skills/legacy-bootstrap/SKILL.md`

- [ ] **Step 1: Create skill directory**

Run:

```bash
mkdir -p cadence-init/skills/legacy-bootstrap
```

Expected:

```text
Directory cadence-init/skills/legacy-bootstrap exists.
```

- [ ] **Step 2: Create `SKILL.md` with frontmatter and overview**

Create `cadence-init/skills/legacy-bootstrap/SKILL.md` with this opening structure:

````markdown
---
name: legacy-bootstrap
description: "使用 repomix 对当前本地 legacy 项目进行 bootstrap，生成 Cadence 项目认知文档，并更新 CLAUDE.md 与 AGENTS.md 渐进式加载入口"
disable-model-invocation: true
---

# Legacy Bootstrap

## 概述

使用 `npx repomix@latest` 汇总当前本地 legacy 项目上下文，分析项目结构、架构、模块、依赖、风险和未知项，并将结果沉淀到目标项目的 `cadence/` 目录。

该 skill 属于 `cadence-init` 插件，面向已经在 Claude Code 或 Codex 中打开的本地 clone 项目。

## 核心原则

- 只处理当前打开的本地项目，不 clone 远程仓库。
- 默认使用 `npx repomix@latest`。
- 所有认知产物写入 `cadence/`，不生成 `.ai/`。
- 产物生成完成后必须更新 `CLAUDE.md` 与 `AGENTS.md`。
- 不直接重构业务代码。
- 不把未知业务事实写成确定结论。
- `--skill-generate` 只作为结构参考，不作为主流程。
````

- [ ] **Step 3: Add usage conditions and checklist**

Append this section to `SKILL.md`:

````markdown
## 何时使用

使用本 skill：

- 用户要求对 legacy 项目进行初始化认知。
- 用户要求使用 repomix bootstrap 当前项目。
- 用户要求生成项目架构、模块、风险、构建测试画像等 Cadence 认知文档。
- Agent 进入一个本地历史项目，需要在需求、设计或修改代码前建立项目认知。

不要使用本 skill：

- 当前项目是全新空项目。
- 用户只要求查看少量文件。
- 用户明确要求不生成 Cadence 文档。
- 用户要求分析远程 GitHub 仓库但当前没有本地 clone。

## 检查清单

你必须为以下每个项目创建任务并按顺序完成：

1. **读取目标项目规则** - 读取 `CLAUDE.md`、`AGENTS.md` 和 `.claude/rules/` 中的相关规则。
2. **确认执行模式** - 询问用户选择标准模式、深度模式或轻量降级模式。
3. **执行 repomix** - 使用 `npx repomix@latest` 生成当前项目上下文。
4. **参考 skill-generate** - 仅把 repomix `--skill-generate` 作为结构参考。
5. **分析项目认知** - 从 repomix 输出中提取架构、模块、依赖、风险和未知项。
6. **生成 Cadence 产物** - 按文档类型写入 `cadence/` 对应目录。
7. **更新入口文档** - 更新 `CLAUDE.md` 与 `AGENTS.md` 的渐进式认知加载区域。
8. **输出 bootstrap 摘要** - 汇报生成文件、已确认事实、未知项和建议下一步。
````

- [ ] **Step 4: Add mode selection workflow**

Append this section:

````markdown
## 执行模式

启动后必须询问用户选择模式：

| 模式 | 默认 | 说明 |
|------|------|------|
| 标准模式 | 是 | 生成项目级 bootstrap 认知文档 |
| 深度模式 | 否 | 在标准模式基础上，按核心模块或领域继续拆分文档 |
| 轻量模式 | 否 | 仅在项目过大、时间有限或 repomix 输出不可处理时降级使用 |

默认推荐标准模式。如果用户选择深度模式，应生成更多模块级、领域级和风险级文档。如果 repomix 输出过大或时间有限，可以建议降级到轻量模式。
````

- [ ] **Step 5: Add detailed process**

Append this section:

````markdown
## 处理流程

### 1. 读取目标项目规则

优先读取：

- `CLAUDE.md`
- `AGENTS.md`
- `.claude/rules/document-storage.md`
- `.claude/rules/markdown-format.md`
- `.claude/rules/code-usage.md`
- `cadence/project-rules/README.md`

如果目标项目没有 Cadence 规则，使用以下默认约定：

- 认知产物统一放入 `cadence/`。
- 按文档类型分配到 `analysis-docs`、`architecture`、`docs`、`models`、`plans`、`reports` 等目录。
- 文件名使用 `YYYY-MM-DD_文档类型_文档名称_v1.0.md`。

### 2. 执行 repomix

默认命令：

```bash
npx repomix@latest --output cadence/analysis-docs/YYYY-MM-DD_分析资料_repomix-output_v1.0.xml
```

如果项目较大，优先使用：

- `--compress`
- `--include`
- `--ignore`
- `--split-output`
- `--token-count-tree`
- `--include-logs`
- `--include-diffs`

如果 `npx` 不可用，提示用户先执行 `/pre-check` 或安装 Node.js/npx。

如果 repomix 执行失败，记录失败原因和建议重试命令，不继续编造分析文档。

### 3. 参考 repomix skill-generate

repomix 的 `--skill-generate` 是实验能力，只能作为结构参考。

可以参考：

- 目录组织。
- 触发描述。
- 上下文拆分方式。
- 将代码库认知封装为 Agent 入口的表达方式。

不能执行以下操作：

- 不能直接把 `--skill-generate` 输出作为最终 `legacy-bootstrap` skill。
- 不能直接把 `--skill-generate` 输出作为目标项目的 Cadence 认知产物。
- 不能把实验能力设为默认主流程。

### 4. 分析项目认知

分析重点：

- 技术栈与运行环境。
- 顶层目录结构。
- 模块边界。
- 核心业务域。
- 依赖关系与调用方向。
- 数据模型与持久化线索。
- 构建、测试、格式化和检查命令。
- 风险区域与遗留陷阱。
- 未确认信息。

所有不确定内容必须标记为：

- `UNKNOWN`
- `TODO`
- `NEED_CONFIRMATION`
````

- [ ] **Step 6: Add Cadence output contract**

Append this section:

````markdown
## Cadence 产物

所有产物必须写入目标项目 `cadence/` 目录，不生成 `.ai/`。

### 标准模式产物

| 路径 | 内容 |
|------|------|
| `cadence/analysis-docs/YYYY-MM-DD_分析报告_Legacy项目Bootstrap_v1.0.md` | bootstrap 总报告 |
| `cadence/architecture/YYYY-MM-DD_架构文档_系统总览_v1.0.md` | 系统架构总览 |
| `cadence/architecture/YYYY-MM-DD_架构文档_模块地图_v1.0.md` | 模块边界与模块关系 |
| `cadence/docs/YYYY-MM-DD_开发文档_构建测试画像_v1.0.md` | 构建、测试、检查命令画像 |
| `cadence/models/YYYY-MM-DD_数据模型_领域与数据初稿_v1.0.md` | 数据模型与领域概念初稿 |
| `cadence/docs/YYYY-MM-DD_约束文档_风险区域与遗留陷阱_v1.0.md` | 高风险区域、耦合点、遗留陷阱 |
| `cadence/docs/YYYY-MM-DD_术语表_业务与技术术语_v1.0.md` | 术语表 |
| `cadence/plans/YYYY-MM-DD_计划文档_Legacy后续调研_v1.0.md` | 后续调研计划 |

### 深度模式额外产物

| 路径 | 内容 |
|------|------|
| `cadence/architecture/YYYY-MM-DD_架构文档_<模块名>模块分析_v1.0.md` | 关键模块级分析 |
| `cadence/models/YYYY-MM-DD_数据模型_<领域名>领域模型_v1.0.md` | 核心领域模型 |
| `cadence/analysis-docs/YYYY-MM-DD_分析报告_<模块名>风险分析_v1.0.md` | 模块级风险分析 |
| `cadence/plans/YYYY-MM-DD_计划文档_<领域名>后续调研_v1.0.md` | 领域级后续调研计划 |

如果某类信息没有足够证据，不生成空洞文档。在 bootstrap 总报告中说明未生成原因。
````

- [ ] **Step 7: Add CLAUDE.md and AGENTS.md update contract**

Append this section:

````markdown
## 更新 CLAUDE.md 与 AGENTS.md

产物生成完成后，必须更新目标项目的 `CLAUDE.md` 与 `AGENTS.md`。

更新方式不是复制完整分析内容，而是新增“Legacy 项目认知”或“渐进式项目认知加载”区域，指向 `cadence/` 下的入口文档和任务相关文档。

推荐结构：

```markdown
## Legacy 项目认知

本项目已完成 Legacy Bootstrap。后续执行任务前，应按任务类型渐进式读取 `cadence/` 下的项目认知文档。

### 首选入口

- `cadence/analysis-docs/...Legacy项目Bootstrap...md`
- `cadence/architecture/...系统总览...md`
- `cadence/architecture/...模块地图...md`

### 修改代码前必须读取

- `cadence/docs/...风险区域与遗留陷阱...md`
- `cadence/docs/...构建测试画像...md`
- 与当前任务相关的模块、领域或风险分析文档

### 使用规则

- 不确定内容以文档中的 `UNKNOWN`、`TODO`、`NEED_CONFIRMATION` 标记为准。
- 不得把 bootstrap 初稿视为绝对事实。
- 如发现文档与代码不一致，应优先相信当前代码，并更新对应 Cadence 文档。
```

`CLAUDE.md` 面向 Claude Code，`AGENTS.md` 面向 Codex 和其他通用 Agent。两者内容应保持一致，但措辞可以分别适配。

如果目标项目缺少 `CLAUDE.md` 或 `AGENTS.md`，按 Cadence 初始化规则提示或创建对应入口文件。
````

- [ ] **Step 8: Add error handling and final output**

Append this section:

````markdown
## 错误处理

| 场景 | 处理方式 |
|------|----------|
| 当前目录不是项目根目录 | 提醒用户确认当前工作目录，不继续执行 |
| `npx` 不可用 | 提示执行 `/pre-check` 或安装 Node.js/npx |
| repomix 执行失败 | 记录失败原因和重试命令，不编造分析 |
| repomix 输出过大 | 建议使用 `--compress`、`--include`、`--ignore`、`--split-output` |
| `cadence/` 不存在 | 按需创建对应子目录 |
| `CLAUDE.md` 或 `AGENTS.md` 不存在 | 提示或创建入口文件 |
| 信息证据不足 | 标记 `UNKNOWN`、`TODO` 或 `NEED_CONFIRMATION` |

## 完成汇报

完成后必须汇报：

- repomix 输出文件路径。
- 生成的 Cadence 文档列表。
- 更新的入口文档列表。
- 已确认事实摘要。
- `UNKNOWN` / `TODO` / `NEED_CONFIRMATION` 摘要。
- 建议下一步。
````

- [ ] **Step 9: Verify skill file content**

Run:

```bash
test -f cadence-init/skills/legacy-bootstrap/SKILL.md
rg -n "^name: legacy-bootstrap|npx repomix@latest|CLAUDE.md|AGENTS.md|--skill-generate|cadence/" cadence-init/skills/legacy-bootstrap/SKILL.md
```

Expected:

```text
The file exists.
The rg output includes all searched concepts.
```

- [ ] **Step 10: Commit skill file**

Run:

```bash
git add cadence-init/skills/legacy-bootstrap/SKILL.md
git commit -m "feat: add legacy bootstrap skill"
```

Expected:

```text
Commit created with cadence-init/skills/legacy-bootstrap/SKILL.md.
```

## Task 2: Create legacy-bootstrap Command

**Files:**

- Create: `cadence-init/commands/legacy-bootstrap.md`

- [ ] **Step 1: Create command file**

Create `cadence-init/commands/legacy-bootstrap.md`:

````markdown
---
skill: legacy-bootstrap
---

# /legacy-bootstrap - Legacy 项目 Bootstrap

调用 `legacy-bootstrap` skill，使用 repomix 对当前本地 legacy 项目进行初始化认知分析。

## 使用场景

- 当前 Claude Code 或 Codex 已打开一个本地 clone 的 legacy 项目。
- 需要在需求、设计或修改代码前建立项目认知。
- 需要生成可版本化的 Cadence 项目认知文档。
- 需要让 `CLAUDE.md` 与 `AGENTS.md` 渐进式引用这些认知文档。

## 功能

执行以下流程：

1. 读取当前项目规则和入口文档。
2. 询问用户选择标准模式、深度模式或轻量降级模式。
3. 使用 `npx repomix@latest` 生成项目上下文。
4. 参考 repomix 实验性 `--skill-generate` 的结构思路，但不作为主流程。
5. 分析项目架构、模块、依赖、风险、数据模型、构建测试画像和未知项。
6. 将认知产物写入 `cadence/` 下的对应目录。
7. 更新 `CLAUDE.md` 与 `AGENTS.md` 的渐进式项目认知加载区域。
8. 输出 bootstrap 摘要和建议下一步。

## 输出

默认生成或更新：

- `cadence/analysis-docs/`
- `cadence/architecture/`
- `cadence/docs/`
- `cadence/models/`
- `cadence/plans/`
- `CLAUDE.md`
- `AGENTS.md`

## 约束

- 只处理当前打开的本地项目。
- 不 clone 远程仓库。
- 不生成 `.ai/`。
- 不直接重构业务代码。
- 不编造未知业务事实。
- repomix `--skill-generate` 仅作为参考。

## 相关命令

- `/pre-check` - 检查 npx 等基础工具
- `/cadence:init:project-analysis` - 基础项目结构分析
- `/cadence:init:rule-config` - 初始化项目规则
````

- [ ] **Step 2: Verify command file**

Run:

```bash
test -f cadence-init/commands/legacy-bootstrap.md
rg -n "^skill: legacy-bootstrap|npx repomix@latest|--skill-generate|CLAUDE.md|AGENTS.md|cadence/" cadence-init/commands/legacy-bootstrap.md
```

Expected:

```text
The file exists.
The rg output includes the skill binding and core behavior.
```

- [ ] **Step 3: Commit command file**

Run:

```bash
git add cadence-init/commands/legacy-bootstrap.md
git commit -m "feat: add legacy bootstrap command"
```

Expected:

```text
Commit created with cadence-init/commands/legacy-bootstrap.md.
```

## Task 3: Validate Plugin Consistency

**Files:**

- Read: `cadence-init/.claude-plugin/plugin.json`
- Read: `cadence-init/skills/legacy-bootstrap/SKILL.md`
- Read: `cadence-init/commands/legacy-bootstrap.md`

- [ ] **Step 1: Check plugin manifest does not require explicit registration**

Run:

```bash
sed -n '1,160p' cadence-init/.claude-plugin/plugin.json
```

Expected:

```text
The manifest describes cadence-init plugin metadata and does not enumerate individual commands or skills.
```

- [ ] **Step 2: Check frontmatter and command binding**

Run:

```bash
sed -n '1,20p' cadence-init/skills/legacy-bootstrap/SKILL.md
sed -n '1,20p' cadence-init/commands/legacy-bootstrap.md
```

Expected:

```text
SKILL.md frontmatter includes name: legacy-bootstrap.
command frontmatter includes skill: legacy-bootstrap.
```

- [ ] **Step 3: Check prohibited outputs are excluded**

Run:

```bash
rg -n "生成 `.ai/`|作为主流程|远程 GitHub 仓库作为输入|clone 远程" cadence-init/skills/legacy-bootstrap/SKILL.md cadence-init/commands/legacy-bootstrap.md
```

Expected:

```text
Matches only appear in negative constraints, not as required behavior.
```

- [ ] **Step 4: Check required outputs are included**

Run:

```bash
rg -n "cadence/analysis-docs|cadence/architecture|cadence/docs|cadence/models|cadence/plans|CLAUDE.md|AGENTS.md" cadence-init/skills/legacy-bootstrap/SKILL.md cadence-init/commands/legacy-bootstrap.md
```

Expected:

```text
All required Cadence directories and entrance documents are referenced.
```

- [ ] **Step 5: Check git status**

Run:

```bash
git status --short --branch
```

Expected:

```text
Current branch is legacy-bootstrap-skill-design.
Working tree is clean after the task commits.
```

## Task 4: Final Review and PR Preparation

**Files:**

- Read: `cadence/designs/2026-05-27_方案设计_legacy-bootstrap-skill_v1.0.md`
- Read: `cadence-init/skills/legacy-bootstrap/SKILL.md`
- Read: `cadence-init/commands/legacy-bootstrap.md`

- [ ] **Step 1: Review implementation against design**

Run:

```bash
rg -n "legacy-bootstrap|npx repomix@latest|--skill-generate|CLAUDE.md|AGENTS.md|cadence/" cadence/designs/2026-05-27_方案设计_legacy-bootstrap-skill_v1.0.md cadence-init/skills/legacy-bootstrap/SKILL.md cadence-init/commands/legacy-bootstrap.md
```

Expected:

```text
Design, skill, and command all reference the same core behavior.
```

- [ ] **Step 2: Review final commit history**

Run:

```bash
git log --oneline --decorate main..HEAD
```

Expected:

```text
Branch contains design commits and implementation commits only.
```

- [ ] **Step 3: Push branch when ready**

Run:

```bash
git push -u origin legacy-bootstrap-skill-design
```

Expected:

```text
Branch pushed to origin and ready for PR.
```

- [ ] **Step 4: Create PR**

Run:

```bash
gh pr create --base main --head legacy-bootstrap-skill-design --title "Add legacy bootstrap skill" --body "Adds a cadence-init legacy-bootstrap command and skill for repomix-based legacy project bootstrap."
```

Expected:

```text
GitHub PR URL is returned.
```

## Self-Review

- Spec coverage: covered command path, skill path, local project input, `npx repomix@latest`, standard/deep/light modes, Cadence output directories, `CLAUDE.md` / `AGENTS.md` update, `--skill-generate` reference boundary, and no `.ai/` output.
- Placeholder scan: the plan uses the marker string `TODO` only because the approved design requires that generated uncertainty markers include `TODO`; it is not a placeholder in this implementation plan.
- Scope check: the plan is focused on one plugin feature and does not require decomposition.
- Type consistency: no code APIs or function signatures are introduced.
