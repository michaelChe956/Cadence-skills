# KnowledgeBase Skill 选择前置门禁 实施 Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为 `knowledge-base-context` Skill 增加"选择前门禁"，使未启用 KnowledgeBase 的项目不再误选该 Skill，且不影响已启用 KnowledgeBase 的使用者。

**Architecture:** 三层门禁载体：Skill frontmatter description（选择时刻生效，主门禁）→ L0 路由内核模板 + 本仓库入口受管块（会话开始生效，二次防线）→ 项目规则文件（文档化兜底）。纯文档变更，无代码实现。

**Tech Stack:** Markdown、YAML frontmatter、OpenSpec。

**关联契约：** Change `gate-knowledge-base-context-selection`（`openspec/changes/gate-knowledge-base-context-selection/`）；Requirement 见 `specs/knowledge-base-context-gating/spec.md`。

## Global Constraints

- 本仓库为非 Coding 项目：非必要不编写代码；验证只用 `grep`/`diff` 等只读命令。
- `knowledge-base-context` Skill 正文与异常处理表 **不得修改**（仅 frontmatter description 一行）。
- L0 受管块版本标记 `cadence-managed:openspec-superpowers-routing:v1` **不得变更**；受管块外内容 **不得修改**。
- 内核模板、`CLAUDE.md`、`AGENTS.md` 三处门禁句 **必须逐字一致**。
- 禁止使用 `sed -i` 等批量改写入口文件；使用精确文本替换。
- 提交信息使用中文，遵循仓库既有提交风格（先 `git log --oneline -5` 查看）。

---

### Task 1: Skill description 主门禁（对应 OpenSpec 工作包 1 / Requirement "Skill description 选择前置门禁"）

**Files:**
- Modify: `cadence-init/skills/knowledge-base-context/SKILL.md:3`

**Interfaces:**
- Consumes: 无
- Produces: description 门禁句，供 Task 4 一致性验证比对

- [ ] **Step 1: 修改前快照**

Run: `md5sum cadence-init/skills/knowledge-base-context/SKILL.md && git diff --stat`
Expected: 记录当前哈希；工作区该文件无未提交修改

- [ ] **Step 2: 追加门禁句**

将第 3 行 description 整行替换为（仅在引号内末尾追加，其余逐字不动）：

```yaml
description: "MUST use when an agent is about to perform project-specific 需求澄清、Design、Plan、Coding、Testing、Review 或 Debug work and an existing Schema 4.0 KnowledgeBase must ground the task context. 选择前置门禁：仅当 cadence/knowledge-base/manifest.yaml 存在且 schema_version 为 '4.0' 时才可选择本 Skill；Manifest 缺失或 Schema 非 4.0 时不得选择、调用或读取本 Skill，按普通流程继续，不输出知识库相关提示，不引导 knowledge-base-bootstrap。"
```

- [ ] **Step 3: 验证仅 description 一行变化**

Run: `git diff cadence-init/skills/knowledge-base-context/SKILL.md`
Expected: diff 仅含第 3 行一处修改；正文零改动

- [ ] **Step 4: 验证 YAML frontmatter 可解析**

Run: `python3 -c "import yaml,sys; d=yaml.safe_load(open('cadence-init/skills/knowledge-base-context/SKILL.md').read().split('---')[1]); assert '选择前置门禁' in d['description']; print('OK')"`
Expected: `OK`

- [ ] **Step 5: Commit**

```bash
git add cadence-init/skills/knowledge-base-context/SKILL.md
git commit -m "feat(knowledge-base-context): description 增加选择前置门禁"
```

---

### Task 2: L0 路由层门禁（对应 OpenSpec 工作包 2 / Requirement "L0 路由内核门禁"）

**Files:**
- Modify: `cadence-init/skills/rule-config/references/rules/agent-routing-kernel.md`
- Modify: `CLAUDE.md`（仅 L0 受管块内）
- Modify: `AGENTS.md`（仅 L0 受管块内）

**Interfaces:**
- Consumes: 无
- Produces: 三处逐字一致的门禁句，供 Task 4 验证

统一门禁句（三处逐字一致，作为独立段落）：

```markdown
`knowledge-base-context` 选择前置门禁：仅当只读确认 `cadence/knowledge-base/manifest.yaml` 存在且 `schema_version` 为 `"4.0"` 时才可选择；Manifest 缺失或版本不符时不得选择、调用或读取该 Skill，不输出知识库相关提示，按普通流程继续。
```

插入位置：三个文件中均在 L0 受管块内、路由表之后、段落 `阶段切换必须重新路由：` 之前。

- [ ] **Step 1: 修改内核模板**

在 `agent-routing-kernel.md` 中定位路由表结束行（`| OpenSpec 已归档 | ... |` 表格末行）之后、`阶段切换必须重新路由：` 段落之前，插入门禁句段落（前后各留一个空行）。

- [ ] **Step 2: 同步 CLAUDE.md 受管块**

在 `CLAUDE.md` 的 `cadence-managed:openspec-superpowers-routing:v1` 标记对内，同一相对位置逐字插入同一门禁句。

- [ ] **Step 3: 同步 AGENTS.md 受管块**

在 `AGENTS.md` 的同一标记对内，同一相对位置逐字插入同一门禁句。

- [ ] **Step 4: 验证三处门禁句逐字一致**

Run: `grep -h 'knowledge-base-context` 选择前置门禁' cadence-init/skills/rule-config/references/rules/agent-routing-kernel.md CLAUDE.md AGENTS.md | sort -u | wc -l`

（注意：必须使用单引号，门禁句中的反引号在双引号内会触发命令替换）
Expected: `1`（三处逐字一致，去重后仅一行）

- [ ] **Step 5: 验证块外内容与版本标记未变**

Run: `git diff CLAUDE.md AGENTS.md | grep -E "^[+-]" | grep -vE "^[+-]{3}" | grep -v "选择前置门禁" | grep -vE "^[+-]$"`
Expected: 无输出（除新增门禁句及相邻空行外无其他改动）；`grep -c "cadence-managed:openspec-superpowers-routing:v1" CLAUDE.md AGENTS.md` 结果与修改前一致（各 2 个标记）

- [ ] **Step 6: Commit**

```bash
git add cadence-init/skills/rule-config/references/rules/agent-routing-kernel.md CLAUDE.md AGENTS.md
git commit -m "feat(rule-config): L0 路由内核增加 knowledge-base-context 选择前置门禁"
```

---

### Task 3: 项目规则文档化兜底（对应 OpenSpec 工作包 3 / Requirement "项目规则文档化兜底"）

**Files:**
- Create: `cadence/project-rules/knowledge-base-gating.md`
- Modify: `cadence/project-rules/README.md`（文件说明一节）

**Interfaces:**
- Consumes: 无
- Produces: 无

- [ ] **Step 1: 新建规则文件**

创建 `cadence/project-rules/knowledge-base-gating.md`，内容：

```markdown
# KnowledgeBase Skill 选择门禁

在选择 `knowledge-base-context` 前，先只读检查
`cadence/knowledge-base/manifest.yaml`：

- 文件不存在，或 `schema_version` 不等于 `"4.0"`：不得选择、调用或读取
  `knowledge-base-context` Skill；按普通代码阅读、调试或实现流程继续。
- 文件存在且 `schema_version: "4.0"`：任务涉及需求澄清、设计、计划、编码、测试、
  审查或调试时，必须调用 `knowledge-base-context` Skill。
- 不得因为 Manifest 缺失而调用该 Skill 后再以"缺少 Schema"为由阻断普通仓库任务。

## 异常处理的正确解读

`knowledge-base-context` Skill 正文的"Manifest 缺失则停止"仅适用于：已确认
需要知识库、或用户显式手动调用该 Skill 时，发现知识库损坏或丢失的异常处理；
不得用于"项目根本没有启用知识库"的普通任务。
```

- [ ] **Step 2: 登记 README**

在 `cadence/project-rules/README.md` 的"## 📁 文件说明"一节末尾追加：

```markdown
### knowledge-base-gating.md
`knowledge-base-context` Skill 的选择前置门禁：Manifest 缺失或 Schema 非 4.0 时
不得选择该 Skill；并说明 Skill 异常处理的正确解读。
```

- [ ] **Step 3: 验证文件存在且可检索**

Run: `grep -l "knowledge-base-gating" cadence/project-rules/README.md && grep -c "schema_version" cadence/project-rules/knowledge-base-gating.md`
Expected: 输出 README 路径；计数 ≥ 2

- [ ] **Step 4: Commit**

```bash
git add cadence/project-rules/knowledge-base-gating.md cadence/project-rules/README.md
git commit -m "docs(project-rules): 新增 knowledge-base-context 选择门禁规则"
```

---

### Task 4: 整体验证（对应 OpenSpec 工作包 4）

**Files:**
- 无修改，仅只读验证

**Interfaces:**
- Consumes: Task 1 的 description 门禁句、Task 2 的三处门禁句、Task 3 的规则文件
- Produces: 无

- [ ] **Step 1: 四处载体语义一致性检索**

Run: `grep -rn "选择前置门禁" cadence-init/skills/knowledge-base-context/SKILL.md cadence-init/skills/rule-config/references/rules/agent-routing-kernel.md CLAUDE.md AGENTS.md cadence/project-rules/knowledge-base-gating.md | wc -l`
Expected: `5`（五处载体均含门禁；README 登记不含该短语属预期）

- [ ] **Step 2: Skill 正文零改动确认**

Run: `git show $(git log --format=%H --grep='description 增加选择前置门禁' -1) -- cadence-init/skills/knowledge-base-context/SKILL.md | grep -cE "^[+-][^+-]"`
Expected: `2`（Task 1 提交中该文件仅 description 一行增删）

- [ ] **Step 3: 受管块标记完整性**

Run: `grep -c "cadence-managed:openspec-superpowers-routing:v1" CLAUDE.md AGENTS.md cadence-init/skills/rule-config/references/rules/agent-routing-kernel.md`
Expected: 各输出 `2`、`2`、`2`（开始/结束标记成对）

- [ ] **Step 4: 模拟无 Manifest 项目的门禁判定**

Run: `test ! -f cadence/knowledge-base/manifest.yaml && echo "本仓库无 Manifest：按门禁不得选择 knowledge-base-context"`
Expected: 输出该提示（本仓库自身即无 Manifest 场景，验证门禁判定条件可执行）

- [ ] **Step 5: 最终提交状态检查**

Run: `git status --short && git log --oneline -4`
Expected: 工作区干净；3 个 Task 提交按序在列
