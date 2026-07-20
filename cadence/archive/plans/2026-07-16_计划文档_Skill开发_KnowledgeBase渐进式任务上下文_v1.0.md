# KnowledgeBase 渐进式任务上下文 Skill 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:executing-plans` to implement this plan task-by-task. Independent agents may be used for baseline and forward validation when the runtime supports them. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 `cadence-init` 中新增同时支持 Claude Code 与 Codex 的 `knowledge-base-context` Skill，从自然语言任务出发，双轨读取 Schema 3.0 KnowledgeBase 与当前源码并生成最小任务上下文包。

**Architecture:** Skill 使用 Frontmatter Description 完成七类任务画像的自动触发，使用 `/cadence-init:knowledge-base-context` 与 `$knowledge-base-context` 支持双端手动触发。核心工作流只负责画像识别、Manifest 校验、双轨种子读取、一跳关系扩展、画像定向深化、证据对照和上下文输出；不调用 `cadence-workflow`，完成后把上下文交回调用方继续原始任务。

**Tech Stack:** Markdown、YAML、JSON、现有 Skill 校验脚本、ripgrep、jq、Git。

## Global Constraints

- 所有响应和文档使用中文，源码标识和协议名保留原文。
- 新 Skill 位于 `cadence-init/skills/knowledge-base-context/`，目录结构与现有 KnowledgeBase Skills 一致。
- 固定支持需求澄清、Design、Plan、Coding、Testing、Review、Debug 七类画像，不设计扩展机制。
- KnowledgeBase 与源码、DDL、配置每次都同时参与，不存在主从或降级关系。
- Manifest 只承担 Schema、范围和基线职责，不参与 Skill 触发。
- 默认不写任务上下文文件，只有用户明确要求时才保存。
- 不增加脚本或无关文件；按用户后续确认增加独立 Skill README，并更新现有 README 导航。
- 不修改、不调用、不依赖 `cadence-workflow`。
- 设计依据：`cadence/designs/2026-07-16_技术方案_KnowledgeBase渐进式任务上下文Skill_v1.0.md`。

---

### Task 1: 核对现有脚手架并建立失败基线

**Files:**

- Modify scaffold: `cadence-init/skills/knowledge-base-context/`
- Delete scaffold placeholders: `scripts/example.py`、`references/guide.md`、`assets/README.txt`

**Interfaces:**

- Consumes: 已生成的标准 Skill 脚手架。
- Produces: 无占位内容的可编辑 Skill 目录。

- [ ] **Step 1: 运行占位失败基线**

Run:

```bash
rg -n "T[D]O|Replace this|Add stable reference|Put templates" cadence-init/skills/knowledge-base-context
```

Expected: 找到脚手架占位内容，证明正式行为尚未实现。

- [ ] **Step 2: 运行集成失败基线**

Run:

```bash
rg -n "knowledge-base-context" cadence-init/skills/knowledge-base-overview/assets/knowledge-base-usage-template.md cadence-init/skills/knowledge-base-overview/references/rules-integration-guide.md
```

Expected: exit code `1`，证明现有项目规则尚未接入新 Skill。

- [ ] **Step 3: 删除脚手架占位内容**

使用 `apply_patch` 删除：

```text
cadence-init/skills/knowledge-base-context/scripts/example.py
cadence-init/skills/knowledge-base-context/references/guide.md
cadence-init/skills/knowledge-base-context/assets/README.txt
```

删除空 `scripts/` 目录，保留 `references/` 与 `assets/`。

### Task 2: 编写核心 SKILL 与 Codex 元数据

**Files:**

- Modify: `cadence-init/skills/knowledge-base-context/SKILL.md`
- Create: `cadence-init/skills/knowledge-base-context/agents/openai.yaml`

**Interfaces:**

- Consumes: Manifest 3.0、KnowledgeBase 文档、当前源码、七类画像定义。
- Produces: 自动触发描述、双轨渐进读取流程、固定输出契约和 Codex 手动入口。

- [ ] **Step 1: 编写 Frontmatter 与职责边界**

Frontmatter：

```yaml
---
name: knowledge-base-context
description: "Use before any project-specific 需求澄清、Design/技术设计、Plan/实施计划、Coding/编码、Testing/测试、Review/评审或 Debug/调试 task when Schema 3.0 KnowledgeBase exists and the task must be grounded in both KnowledgeBase and current source code, DDL, and configuration; also use when the user asks to load, retrieve, or organize project KnowledgeBase context."
---
```

正文明确只负责任务上下文前置阶段，不调用 `cadence-workflow`；上下文完成后交回调用方继续原始任务。

- [ ] **Step 2: 编写核心工作流**

SKILL.md 包含：

```text
前置校验
→ 任务画像识别
→ KnowledgeBase 与源码双轨种子获取
→ 一跳关系扩展
→ 画像定向深化
→ 双轨证据对照
→ 最小任务上下文包
```

写明 Manifest 缺失、Schema 错误、同名实体、基线漂移、双轨冲突、范围越界和敏感配置处理。

- [ ] **Step 3: 编写资源路由与交互规则**

SKILL.md 直接链接：

```text
references/progressive-retrieval-guide.md
references/task-profiles.md
references/demo.md
assets/task-context-template.md
```

Claude Code 使用 `AskUserQuestion`；Codex 使用 `request_user_input`；工具不可用时使用普通文本提问。

- [ ] **Step 4: 创建 Codex 元数据**

```yaml
interface:
  display_name: "KnowledgeBase 任务上下文"
  short_description: "从 KnowledgeBase 与源码渐进获取当前任务所需上下文"
  default_prompt: "使用 $knowledge-base-context 识别当前任务画像，同时读取 Schema 3.0 KnowledgeBase 与相关源码，生成最小任务上下文包。"
```

- [ ] **Step 5: 运行基础校验**

Run: `python3 cadence-init/skills/skill-creator/scripts/quick_validate.py cadence-init/skills/knowledge-base-context`

Expected: `Skill is valid`。

### Task 3: 编写渐进读取、任务画像、模板和案例

**Files:**

- Create: `cadence-init/skills/knowledge-base-context/references/progressive-retrieval-guide.md`
- Create: `cadence-init/skills/knowledge-base-context/references/task-profiles.md`
- Create: `cadence-init/skills/knowledge-base-context/references/demo.md`
- Create: `cadence-init/skills/knowledge-base-context/assets/task-context-template.md`

**Interfaces:**

- Consumes: Task 2 的核心工作流与固定七类画像。
- Produces: 可按需加载的一层引用资源和持久化任务快照模板。

- [ ] **Step 1: 编写渐进读取指南**

包含第 0～6 层共七层读取算法、双轨种子、稳定 ID 与源码符号映射、一跳扩展、画像深化、基线漂移、冲突矩阵和停止条件。固定证据状态为：`一致`、`KnowledgeBase 缺失`、`源码缺失`、`基线漂移`、`来源冲突`、`待确认`。

- [ ] **Step 2: 编写七类任务画像**

为需求澄清、Design、Plan、Coding、Testing、Review、Debug 定义识别信号、KnowledgeBase 必读内容、源码必读内容、专属输出、扩展条件和停止条件。一个主画像最多附加两个辅助画像。

- [ ] **Step 3: 编写任务上下文模板**

固定十节：任务识别、任务理解、核心实体、双轨证据矩阵、关系与影响面、画像专属上下文、约束与现有模式、冲突缺口与待确认项、下游使用建议、就绪状态。

- [ ] **Step 4: 编写综合案例**

使用虚构订单导出任务展示 Coding + Testing，包含 Manifest 基线漂移、页面 → API → Service → Table/对象存储关系、一致项、冲突项和 `有条件就绪` 状态。

- [ ] **Step 5: 验证资源完整性**

Run:

```bash
for file in progressive-retrieval-guide.md task-profiles.md demo.md; do test -f "cadence-init/skills/knowledge-base-context/references/$file"; done
test -f cadence-init/skills/knowledge-base-context/assets/task-context-template.md
```

Expected: exit code `0`。

### Task 4: 接入项目级规则和双端使用说明

**Files:**

- Modify: `cadence-init/skills/knowledge-base-overview/assets/knowledge-base-usage-template.md`
- Modify: `cadence-init/skills/knowledge-base-overview/references/rules-integration-guide.md`
- Modify: `cadence-init/skills/knowledge-base-overview/SKILL.md`
- Modify: `cadence-init/.claude-plugin/plugin.json`
- Modify: `.claude-plugin/marketplace.json`

**Interfaces:**

- Consumes: 新 Skill 名称与双端调用方式。
- Produces: 项目自动触发指引、手动入口和更新后的插件元数据。

- [ ] **Step 1: 更新 KnowledgeBase 使用规则模板**

增加：七类任务先使用 `knowledge-base-context`，同时读取 KnowledgeBase 与相关源码。保留现有读取顺序和增量更新规则。

- [ ] **Step 2: 更新规则接入指南**

明确自动触发依赖 Skill Description，Manifest 不参与触发；手动入口：Claude Code `/cadence-init:knowledge-base-context`，Codex 在 Skill 已安装或被项目发现后使用 `$knowledge-base-context`。

- [ ] **Step 3: 更新插件元数据**

将 `cadence-init/.claude-plugin/plugin.json` 和 `.claude-plugin/marketplace.json` 中的 `cadence-init` 版本从 `0.0.2` 更新为 `0.0.3`。插件描述补充“KnowledgeBase 渐进式任务上下文消费能力”，关键字增加 `context`。

- [ ] **Step 4: 验证插件 JSON**

Run:

```bash
jq -e '.version == "0.0.3" and (.keywords | index("context") != null)' cadence-init/.claude-plugin/plugin.json
jq -e '.plugins[] | select(.name == "cadence-init") | .version == "0.0.3"' .claude-plugin/marketplace.json
```

Expected: `true`。

### Task 5: 完成触发、行为和回归验证

**Files:**

- Verify: `cadence-init/skills/knowledge-base-context/**`
- Verify: `cadence-init/skills/knowledge-base-overview/**`
- Verify: `cadence-init/.claude-plugin/plugin.json`

**Interfaces:**

- Consumes: Tasks 1-4 的全部产物。
- Produces: 可提交的 Skill 目录和验证证据。

- [ ] **Step 1: 验证七类自动触发词覆盖**

Run: `rg -n "需求澄清|设计|计划|编码|测试|评审|调试" cadence-init/skills/knowledge-base-context/SKILL.md`

- [ ] **Step 2: 验证双端手动入口**

Run:

```bash
rg -n "/cadence-init:knowledge-base-context|\$knowledge-base-context" cadence-init/skills/knowledge-base-context cadence-init/skills/knowledge-base-overview
```

- [ ] **Step 3: 验证双轨读取和 Manifest 边界**

Run:

```bash
rg -n "同等重要|双轨|Manifest.*不参与.*触发|schema_version|baseline_commit" cadence-init/skills/knowledge-base-context
```

- [ ] **Step 4: 验证无占位与无冗余文件**

Run:

```bash
rg -n "T[D]O|T[B]D|Replace this|Add stable reference|Put templates" cadence-init/skills/knowledge-base-context
find cadence-init/skills/knowledge-base-context -type f -print | sort
```

Expected: `rg` exit code `1`；文件清单只包含 6 个设计批准的 Skill 文件。

- [ ] **Step 5: 验证未修改 cadence-workflow**

Run:

```bash
git diff --name-only -- cadence-workflow
```

Expected: 无输出。

- [ ] **Step 6: 运行最终结构与格式检查**

Run:

```bash
python3 cadence-init/skills/skill-creator/scripts/quick_validate.py cadence-init/skills/knowledge-base-context
git diff --check
```

Expected: `Skill is valid`，格式检查 exit code `0`。

- [ ] **Step 7: 检查完整 Diff**

Run:

```bash
git status --short
git diff --stat
git diff
```

Expected: 只有新 Skill、KnowledgeBase 使用规则、规则接入指南、插件元数据、本设计修正和本计划发生变化。

- [ ] **Step 8: 验证 Claude Code 真实发现、自动触发和手动入口**

在包含 Schema 3.0 Manifest、KnowledgeBase 使用规则和最小源码的隔离临时项目中加载本地插件：

```bash
REPO_ROOT="$(git rev-parse --show-toplevel)"
cd /private/tmp/kb-context-claude
claude -p '当前项目已有 Schema 3.0 KnowledgeBase。实现订单导出并补异常测试。只列出开始处理前会按顺序使用的所有适用 Skills，不执行任务，不修改文件。' --plugin-dir "$REPO_ROOT/cadence-init" --add-dir "$REPO_ROOT/cadence-init" --output-format stream-json --verbose --include-partial-messages --permission-mode dontAsk
```

Expected:

- 初始化事件的 Skills 和 Slash Commands 包含 `cadence-init:knowledge-base-context`。
- 结果将 `knowledge-base-context` 作为第一个业务前置 Skill。
- 识别 `Coding` 主画像和 `Testing` 辅助画像。
- 明确上下文完成后继续实现与补测，不在上下文包处结束。

- [ ] **Step 9: 验证 Codex 真实自动触发和手动入口**

将 Skill 安装到隔离临时项目的 `.codex/skills/knowledge-base-context/` 后运行：

```bash
REPO_ROOT="$(git rev-parse --show-toplevel)"
mkdir -p /private/tmp/kb-context-codex/.codex/skills
cp -R "$REPO_ROOT/cadence-init/skills/knowledge-base-context" /private/tmp/kb-context-codex/.codex/skills/knowledge-base-context
codex exec -C /private/tmp/kb-context-codex --ephemeral --sandbox read-only --json '$knowledge-base-context 只确认你是否成功读取了这个 Skill，并返回它规定的 Claude Code 与 Codex 手动入口；不要执行其他任务。'
codex exec -C /private/tmp/kb-context-codex --ephemeral --sandbox read-only --json '实现订单导出并补异常测试。只列出开始处理前会按顺序使用的所有适用 Skills，不要执行任务，不要修改文件。'
```

Expected:

- 手动调用读取 Skill，并返回 `/cadence-init:knowledge-base-context` 与 `$knowledge-base-context`。
- 自然语言调用在通用元 Skill 后、其他开发 Skill 前选择 `knowledge-base-context`。
- 负例“解释 Java Stream 语法”“初始化 KnowledgeBase”“润色文本”不选择本 Skill。

### Task 6: 提交并推送

**Files:**

- Commit all files from Tasks 1-5.

- [ ] **Step 1: 暂存实现文件**

Run:

```bash
git add cadence-init/skills/knowledge-base-context cadence-init/skills/knowledge-base-overview/SKILL.md cadence-init/skills/knowledge-base-overview/assets/knowledge-base-usage-template.md cadence-init/skills/knowledge-base-overview/references/rules-integration-guide.md cadence-init/.claude-plugin/plugin.json .claude-plugin/marketplace.json cadence/plans/2026-07-16_计划文档_Skill开发_KnowledgeBase渐进式任务上下文_v1.0.md
git add cadence/designs/2026-07-16_技术方案_KnowledgeBase渐进式任务上下文Skill_v1.0.md
```

- [ ] **Step 2: 核对 staged diff**

Run:

```bash
git diff --cached --check
git diff --cached --stat
```

- [ ] **Step 3: 提交**

Run: `git commit -m "feat: 新增 KnowledgeBase 渐进式任务上下文 Skill"`

- [ ] **Step 4: 推送**

Run: `git push`

- [ ] **Step 5: 验证同步状态**

Run:

```bash
git status --short --branch
git log -1 --oneline --decorate
```

Expected: 工作区干净，`HEAD` 与 `origin/main` 指向同一提交。

### Task 7: 补充 KnowledgeBase Context README

**Files:**

- Create: `readmes/skills/knowledge-base-context.md`
- Modify: `readmes/skills/README.md`
- Modify: `README.md`

**Interfaces:**

- Consumes: `knowledge-base-context`、`knowledge-base-bootstrap`、Manifest 3.0 输入契约和双端真实调用方式。
- Produces: 面向使用者的独立指南，以及根 README 和 Skills 导航入口。

- [ ] **Step 1: 编写独立 Skill 使用文档**

文档固定包含：

1. Skill 定位与非目标。
2. 自动触发前提和七类画像。
3. Claude Code `/cadence-init:knowledge-base-context` 与 Codex `$knowledge-base-context` 手动入口。
4. Schema 3.0 Manifest 的用途、自动生成方式和用户输入责任。
5. KnowledgeBase 与源码、DDL、配置双轨读取流程。
6. 固定十节输出、就绪状态和默认不持久化规则。
7. Coding + Testing、Review、Debug 使用案例。
8. 常见问题、升级说明和相关 Skills。

- [ ] **Step 2: 更新 Skills README 导航**

增加 KnowledgeBase Skills 分类和“从现有项目知识开始任务”的快速导航，链接到 `knowledge-base-context.md`。不重写已有 Cadence Workflow 分类。

- [ ] **Step 3: 更新根 README**

在 `cadence-init` 能力说明中增加 KnowledgeBase 初始化与任务上下文消费说明，并增加独立指南链接。明确 Manifest 由 Bootstrap 自动生成，用户只维护 `cadence/knowledge-base/user-input/`。

- [ ] **Step 4: 验证文档一致性**

Run:

```bash
test -f readmes/skills/knowledge-base-context.md
rg -n "knowledge-base-context|Schema 3.0 Manifest|/cadence-init:knowledge-base-context|\$knowledge-base-context" README.md readmes/skills/README.md readmes/skills/knowledge-base-context.md
rg -n "base-info.md|manifest.yaml|KnowledgeBase 与源码、DDL、配置" readmes/skills/knowledge-base-context.md
git diff --check
```

Expected: 独立文档存在，双端入口、Manifest 自动生成、用户输入责任、双轨读取和导航链接均可检索，格式检查通过。

### Task 8: 提交并推送 README

**Files:**

- Commit: `README.md`
- Commit: `readmes/skills/README.md`
- Commit: `readmes/skills/knowledge-base-context.md`
- Commit: `cadence/plans/2026-07-16_计划文档_Skill开发_KnowledgeBase渐进式任务上下文_v1.0.md`

- [ ] **Step 1: 暂存 README 变更**

Run:

```bash
git add README.md readmes/skills/README.md readmes/skills/knowledge-base-context.md cadence/plans/2026-07-16_计划文档_Skill开发_KnowledgeBase渐进式任务上下文_v1.0.md
```

- [ ] **Step 2: 核对 staged diff**

Run:

```bash
git diff --cached --check
git diff --cached --stat
git diff --cached --name-status
```

Expected: 只有根 README、Skills README、独立 Skill README 和本计划发生变化。

- [ ] **Step 3: 提交并推送**

Run:

```bash
git commit -m "docs: 补充 KnowledgeBase 任务上下文使用指南"
git push
```

- [ ] **Step 4: 验证同步状态**

Run:

```bash
git status --short --branch
git rev-parse HEAD
git rev-parse origin/main
```

Expected: 工作区干净，`HEAD` 与 `origin/main` 指向同一提交。
