# rule-config 命令改造实施计划

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 改造 rule-config 命令，实现三大目标：1) 项目类型检测三态支持；2) 文档目录迁移到 .cadence/；3) CLAUDE.md 和 AGENTS.md 路径引用更新

**Architecture:** 这是一个纯文档改造项目，涉及 cadence-init 和 cadence-workflow 两个插件中的 markdown 文件更新。改动分为 7 个 chunk，按依赖顺序执行。

**Tech Stack:** Markdown 文档编辑、Glob 文件搜索

---

## Chunk 1: 模板文件更新

更新 cadence-init/references/ 下的模板文件，这些是 rule-config 命令执行时复制的源文件。

**文件：**
- Modify: `cadence-init/references/rules/document-storage.md`
- Modify: `cadence-init/references/rules/README.md`
- Modify: `cadence-init/references/project-rules/README.md`
- Modify: `cadence-init/references/project-rules/CLAUDE-RULE.md`

---

### Task 1: 更新 document-storage.md 模板

**Files:**
- Modify: `cadence-init/references/rules/document-storage.md`

- [ ] **Step 1: 读取当前 document-storage.md 内容**

路径：`cadence-init/references/rules/document-storage.md`

- [ ] **Step 2: 更新路径映射表中的所有 .claude/ 文档路径为 .cadence/**

需更新的路径（全部在"文档分类存储规范"表格和"路径映射"章节）：

| 旧路径 | 新路径 |
|--------|--------|
| `.claude/plans/` | `.cadence/plans/` |
| `.claude/prds/` | `.cadence/prds/` |
| `.claude/docs/` | `.cadence/docs/` |
| `.claude/designs/` | `.cadence/designs/` |
| `.claude/designs-reviews/` | `.cadence/designs-reviews/` |
| `.claude/analysis-docs/` | `.cadence/analysis-docs/` |
| `.claude/reports/` | `.cadence/reports/` |
| `.claude/readmes/` | `.cadence/readmes/` |
| `.claude/modaos/` | `.cadence/modaos/` |
| `.claude/models/` | `.cadence/models/` |
| `.claude/architecture/` | `.cadence/architecture/` |
| `.claude/notes/` | `.cadence/notes/` |
| `.claude/logs/` | `.cadence/logs/` |
| `.claude/project-rules/` | `.cadence/project-rules/` |

**注意**：`.claude/rules/` 保持不变（如路径映射表中有此引用则不改）。

- [ ] **Step 3: 更新路径映射（跨平台）表格中的路径示例**

将表格中的 `.claude/docs/` 等改为 `.cadence/docs/`。

- [ ] **Step 4: 更新"禁止行为"章节中的路径**

确认"禁止在以下位置创建文档"中不包含 `.cadence/` 目录。

- [ ] **Step 5: 更新 README 文档存储规则章节中的示例路径**

确保所有示例中的 `.claude/` 文档目录改为 `.cadence/`。

- [ ] **Step 6: Commit**

```bash
git add cadence-init/references/rules/document-storage.md
git commit -m "refactor: 更新 document-storage 模板，文档路径改为 .cadence/

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

### Task 2: 更新 rules/README.md 模板

**Files:**
- Modify: `cadence-init/references/rules/README.md`

- [ ] **Step 1: 读取当前 rules/README.md**

- [ ] **Step 2: 更新 `.claude/project-rules/` 引用为 `.cadence/project-rules/`**

涉及内容：
- 第 23 行："用户自定义规则应放在 `.claude/project-rules/` 目录" → `.cadence/project-rules/`
- 第 36 行："用户自定义规则：`.claude/project-rules/`" → `.cadence/project-rules/`

**注意**：`.claude/rules/` 保持不变（Claude Code 内置约定）。

- [ ] **Step 3: Commit**

```bash
git add cadence-init/references/rules/README.md
git commit -m "refactor: 更新 rules README，project-rules 路径改为 .cadence/

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

### Task 3: 更新 project-rules/README.md 模板

**Files:**
- Modify: `cadence-init/references/project-rules/README.md`

- [ ] **Step 1: 读取当前 project-rules/README.md**

- [ ] **Step 2: 更新所有 .claude/project-rules/ 引用为 .cadence/project-rules/**

涉及内容：
- 标题章节修改
- "规则目录"行
- "修改权限"章节中的路径引用

- [ ] **Step 3: Commit**

```bash
git add cadence-init/references/project-rules/README.md
git commit -m "refactor: 更新 project-rules README，路径改为 .cadence/

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

### Task 4: 更新 project-rules/CLAUDE-RULE.md 模板

**Files:**
- Modify: `cadence-init/references/project-rules/CLAUDE-RULE.md`

- [ ] **Step 1: 读取当前 CLAUDE-RULE.md**

- [ ] **Step 2: 更新所有 .claude/project-rules/ 引用为 .cadence/project-rules/**

- [ ] **Step 3: Commit**

```bash
git add cadence-init/references/project-rules/CLAUDE-RULE.md
git commit -m "refactor: 更新 CLAUDE-RULE 模板，路径改为 .cadence/

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Chunk 2: CLAUDE.md 和 AGENTS.md 更新

**文件：**
- Modify: `CLAUDE.md`
- Modify: `AGENTS.md`

---

### Task 5: 更新 CLAUDE.md 规则引用

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: 读取当前 CLAUDE.md**

- [ ] **Step 2: 更新规则 3（文档存储规则）的路径引用**

旧：
```markdown
### 3. 文档存储规则
- **所有文档必须存放在 `.claude` 目录下** → 详见 `.claude/rules/document-storage.md`
```

新：
```markdown
### 3. 文档存储规则
- **所有文档必须存放在 `.cadence` 目录下** → 详见 `.claude/rules/document-storage.md`
```

- [ ] **Step 3: 更新规则 7（项目个性化规则）的路径引用**

旧：
```markdown
### 7. 项目个性化规则（强制规则）
- **用户自定义规则只能存放在 `.claude/project-rules/` 目录**
- 禁止在 `rules/` 目录中添加用户自定义规则
- 禁止直接修改 `rules/` 目录下的框架内置规则文件
- 详见 `.claude/project-rules/README.md`
```

新：
```markdown
### 7. 项目个性化规则（强制规则）
- **用户自定义规则只能存放在 `.cadence/project-rules/` 目录**
- 禁止在 `rules/` 目录中添加用户自定义规则
- 禁止直接修改 `rules/` 目录下的框架内置规则文件
- 详见 `.cadence/project-rules/README.md`
```

**注意**：其他规则引用（1、4、5、6、8）保持 `.claude/rules/` 不变。规则 2（代码使用规则）保持不变。

- [ ] **Step 4: Commit**

```bash
git add CLAUDE.md
git commit -m "refactor: 更新 CLAUDE.md，文档路径改为 .cadence/

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

### Task 6: 更新 AGENTS.md 规则引用

**Files:**
- Modify: `AGENTS.md`

- [ ] **Step 1: 读取当前 AGENTS.md**

- [ ] **Step 2: 更新规则 3（文档存储规则）的路径引用**

旧：
```markdown
### 3. 文档存储规则
- **除本文件 `AGENTS.md` 外，所有文档必须存放在 `.claude` 目录下** → 详见 `.claude/rules/document-storage.md`
- 本文件 `AGENTS.md` 作为仓库根目录的代理入口说明文件，按用户要求放置于项目根目录。
```

新：
```markdown
### 3. 文档存储规则
- **除本文件 `AGENTS.md` 外，所有文档必须存放在 `.cadence` 目录下** → 详见 `.claude/rules/document-storage.md`
- 本文件 `AGENTS.md` 作为仓库根目录的代理入口说明文件，按用户要求放置于项目根目录。
```

- [ ] **Step 3: 更新规则 7（项目个性化规则）的路径引用**

旧：
```markdown
### 7. 项目个性化规则
- **用户自定义规则只能存放在 `.claude/project-rules/` 目录**
- 禁止在 `.claude/rules/` 目录中添加用户自定义规则
- 禁止直接修改 `.claude/rules/` 目录下的框架内置规则文件
- 详见 `.claude/project-rules/README.md`
```

新：
```markdown
### 7. 项目个性化规则
- **用户自定义规则只能存放在 `.cadence/project-rules/` 目录**
- 禁止在 `.claude/rules/` 目录中添加用户自定义规则
- 禁止直接修改 `.claude/rules/` 目录下的框架内置规则文件
- 详见 `.cadence/project-rules/README.md`
```

**注意**：其他规则引用（1、4、5、6、8）保持 `.claude/rules/` 不变。

- [ ] **Step 4: Commit**

```bash
git add AGENTS.md
git commit -m "refactor: 更新 AGENTS.md，文档路径改为 .cadence/

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Chunk 3: rule-config 命令核心更新

**文件：**
- Modify: `cadence-init/commands/rule-config.md`

---

### Task 7: 重构 rule-config.md 命令流程

**Files:**
- Modify: `cadence-init/commands/rule-config.md`

- [ ] **Step 1: 读取当前 rule-config.md 完整内容**

- [ ] **Step 2: 在"检查清单"部分新增步骤 0（.cadence 迁移检测）**

在现有的检查清单 1-6 之前新增：

```markdown
0. **新增前置步骤：.cadence 迁移检测** — 检测并处理文档目录迁移（详见"步骤 0：.cadence 迁移检测"章节）
```

- [ ] **Step 3: 在"处理流程"部分新增"步骤 0：.cadence 迁移检测"章节**

新增完整的处理流程说明，包括：
- 情况 A/B/C 的判断逻辑
- 迁移确认询问
- gitignore 询问
- 引用更新说明

具体内容见设计文档改动点 2。

- [ ] **Step 4: 更新"步骤 1a：项目类型检测"为三态检测**

修改当前步骤 1a，改为三态检测：
- 有代码文件 → Coding 项目
- 无代码文件 → 进入步骤 0b 询问用户
- 全新空目录 → 进入步骤 0b 询问用户

- [ ] **Step 5: 新增"步骤 0b：项目类型询问"**

在步骤 1a 之后（如检测为无代码文件）插入此步骤，向用户展示三个选项：
1. Coding 项目
2. 非 Coding 项目
3. 跳过

- [ ] **Step 6: 更新"步骤 5：目录结构创建"**

删除 `.claude/` 下的业务目录创建命令，改为创建 `.cadence/` 目录结构：

旧：
```bash
mkdir -p .claude/{rules,prds,analysis-docs,docs,designs,designs-reviews,plans,readmes,modaos,models,architecture,notes,logs,reports,project-rules/examples}
```

新：
```bash
# .cadence/ 目录结构创建
mkdir -p .cadence/{project-rules/examples,prds,analysis-docs,docs,designs,designs-reviews,plans,readmes,modaos,models,architecture,notes,logs,reports}
```

**注意**：`.claude/rules/` 的创建在步骤 1c 中已处理（保持不变）。

- [ ] **Step 7: 更新"核心原则"章节中的目录引用**

确认"规则分离"原则中的目录引用与新结构一致。

- [ ] **Step 8: Commit**

```bash
git add cadence-init/commands/rule-config.md
git commit -m "feat: 重构 rule-config 命令流程，新增 .cadence 迁移和三态检测

- 新增步骤 0：.cadence 迁移检测（情况 A/B/C 判断）
- 项目类型检测改为三态（ Coding/非Coding/跳过）
- 目录结构创建改为 .cadence/ 而非 .claude/ 业务目录

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Chunk 4: cadence-init 其他命令文件更新

**文件：**
- Modify: `cadence-init/commands/project-rules-examples.md`
- Modify: `cadence-init/commands/project-analysis.md`

---

### Task 8: 更新 project-rules-examples.md

**Files:**
- Modify: `cadence-init/commands/project-rules-examples.md`

- [ ] **Step 1: 读取 project-rules-examples.md**

- [ ] **Step 2: 搜索文件中所有 `.claude/project-rules/` 引用，替换为 `.cadence/project-rules/`**

使用 Grep 搜索确认所有引用点：
```bash
grep -n "\.claude/project-rules" cadence-init/commands/project-rules-examples.md
```

- [ ] **Step 3: Commit**

```bash
git add cadence-init/commands/project-rules-examples.md
git commit -m "refactor: 更新 project-rules-examples 命令，路径改为 .cadence/

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

### Task 9: 更新 project-analysis.md

**Files:**
- Modify: `cadence-init/commands/project-analysis.md`

- [ ] **Step 1: 读取 project-analysis.md**

- [ ] **Step 2: 搜索文件中所有 `.claude/analysis-docs/` 引用，替换为 `.cadence/analysis-docs/`**

使用 Grep 搜索确认所有引用点：
```bash
grep -n "\.claude/analysis-docs" cadence-init/commands/project-analysis.md
```

- [ ] **Step 3: Commit**

```bash
git add cadence-init/commands/project-analysis.md
git commit -m "refactor: 更新 project-analysis 命令，路径改为 .cadence/

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Chunk 5: cadence-workflow Skills 路径更新

**文件（共 13 个 SKILL.md）：**
- Modify: `cadence-workflow/skills/brainstorming/SKILL.md`
- Modify: `cadence-workflow/skills/analyze/SKILL.md`
- Modify: `cadence-workflow/skills/requirement/SKILL.md`
- Modify: `cadence-workflow/skills/design/SKILL.md`
- Modify: `cadence-workflow/skills/design-review/SKILL.md`
- Modify: `cadence-workflow/skills/plan/SKILL.md`
- Modify: `cadence-workflow/skills/full-flow/SKILL.md`
- Modify: `cadence-workflow/skills/quick-flow/SKILL.md`
- Modify: `cadence-workflow/skills/exploration-flow/SKILL.md`
- Modify: `cadence-workflow/skills/checkpoint/SKILL.md`
- Modify: `cadence-workflow/skills/status/SKILL.md`
- Modify: `cadence-workflow/skills/resume/SKILL.md`
- Modify: `cadence-workflow/skills/report/SKILL.md`

---

### Task 10: 更新所有 cadence-workflow/skills 中的文档路径

**Files:**
- Modify: 见上方列表

- [ ] **Step 1: 使用 Grep 搜索确认所有需要更新的文件中的 .claude/ 文档路径**

在执行更新前，先搜索每个文件中的 `.claude/` 引用（排除 `.claude/rules/`）：

```bash
# 搜索 brainstorming/SKILL.md
grep -n "\.claude/prds\|\.claude/plans\|\.claude/designs\|\.claude/docs\|\.claude/analysis-docs\|\.claude/reports\|\.claude/readmes\|\.claude/designs-reviews" cadence-workflow/skills/brainstorming/SKILL.md
```

对每个文件执行类似搜索，确认需要改动的位置。

- [ ] **Step 2: 按设计文档改动点 6 中的表格，逐个更新每个 SKILL.md**

使用 `replace_all: true` 对每个文件执行批量替换：
- `.claude/prds/` → `.cadence/prds/`
- `.claude/plans/` → `.cadence/plans/`
- `.claude/designs/` → `.cadence/designs/`
- `.claude/designs-reviews/` → `.cadence/designs-reviews/`
- `.claude/docs/` → `.cadence/docs/`
- `.claude/analysis-docs/` → `.cadence/analysis-docs/`
- `.claude/reports/` → `.cadence/reports/`
- `.claude/readmes/` → `.cadence/readmes/`

**注意**：`.claude/rules/` 不在替换范围内。

- [ ] **Step 3: Commit 所有变更**

```bash
git add cadence-workflow/skills/brainstorming/SKILL.md \
        cadence-workflow/skills/analyze/SKILL.md \
        cadence-workflow/skills/requirement/SKILL.md \
        cadence-workflow/skills/design/SKILL.md \
        cadence-workflow/skills/design-review/SKILL.md \
        cadence-workflow/skills/plan/SKILL.md \
        cadence-workflow/skills/full-flow/SKILL.md \
        cadence-workflow/skills/quick-flow/SKILL.md \
        cadence-workflow/skills/exploration-flow/SKILL.md \
        cadence-workflow/skills/checkpoint/SKILL.md \
        cadence-workflow/skills/status/SKILL.md \
        cadence-workflow/skills/resume/SKILL.md \
        cadence-workflow/skills/report/SKILL.md
git commit -m "refactor: 更新所有 cadence-workflow skills，文档路径改为 .cadence/

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Chunk 6: cadence-workflow Commands 路径更新

**文件（共 5 个 .md）：**
- Modify: `cadence-workflow/commands/full-flow.md`
- Modify: `cadence-workflow/commands/quick-flow.md`
- Modify: `cadence-workflow/commands/plan.md`
- Modify: `cadence-workflow/commands/design.md`
- Modify: `cadence-workflow/commands/design-review.md`

---

### Task 11: 更新所有 cadence-workflow/commands 中的文档路径

**Files:**
- Modify: 见上方列表

- [ ] **Step 1: 使用 Grep 搜索确认所有需要更新的文件中的 .claude/ 文档路径**

```bash
# 搜索 full-flow.md
grep -n "\.claude/prds\|\.claude/plans\|\.claude/designs\|\.claude/docs\|\.claude/analysis-docs" cadence-workflow/commands/full-flow.md
```

对每个文件执行类似搜索。

- [ ] **Step 2: 按设计文档改动点 6 中的表格，逐个更新每个 .md 文件**

使用批量替换模式：
- `.claude/prds/` → `.cadence/prds/`
- `.claude/plans/` → `.cadence/plans/`
- `.claude/designs/` → `.cadence/designs/`
- `.claude/designs-reviews/` → `.cadence/designs-reviews/`
- `.claude/docs/` → `.cadence/docs/`
- `.claude/analysis-docs/` → `.cadence/analysis-docs/`
- `.claude/reports/` → `.cadence/reports/`
- `.claude/readmes/` → `.cadence/readmes/`

- [ ] **Step 3: Commit**

```bash
git add cadence-workflow/commands/full-flow.md \
        cadence-workflow/commands/quick-flow.md \
        cadence-workflow/commands/plan.md \
        cadence-workflow/commands/design.md \
        cadence-workflow/commands/design-review.md
git commit -m "refactor: 更新所有 cadence-workflow commands，文档路径改为 .cadence/

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Chunk 7: readmes/skills 路径更新

**文件（共 6 个 .md）：**
- Modify: `readmes/skills/brainstorming.md`
- Modify: `readmes/skills/checkpoint.md`
- Modify: `readmes/skills/exploration-flow.md`
- Modify: `readmes/skills/full-flow.md`
- Modify: `readmes/skills/quick-flow.md`
- Modify: `readmes/skills/report.md`

---

### Task 12: 更新所有 readmes/skills 中的文档路径

**Files:**
- Modify: 见上方列表

- [ ] **Step 1: 使用 Grep 搜索确认每个文件中的 .claude/ 文档路径**

```bash
# 搜索 brainstorming.md
grep -n "\.claude/" readmes/skills/brainstorming.md
```

**注意**：排除 `.claude/rules/`（保留），只更新业务文档路径。

- [ ] **Step 2: 按设计文档改动点 6 中的表格，逐个更新每个 .md 文件**

使用批量替换模式（只替换业务文档路径，rules 除外）。

- [ ] **Step 3: Commit**

```bash
git add readmes/skills/brainstorming.md \
        readmes/skills/checkpoint.md \
        readmes/skills/exploration-flow.md \
        readmes/skills/full-flow.md \
        readmes/skills/quick-flow.md \
        readmes/skills/report.md
git commit -m "refactor: 更新所有 readmes/skills，文档路径改为 .cadence/

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Chunk 8: 收尾检查

### Task 13: 全局搜索确认无遗漏

- [ ] **Step 1: 全局搜索确认所有 .claude/ 业务文档路径已迁移**

```bash
# 搜索所有 .claude/ 路径（排除 rules/ 和插件目录）
grep -rn "\.claude/prds\|\.claude/plans\|\.claude/designs\|\.claude/docs\|\.claude/analysis-docs\|\.claude/reports\|\.claude/readmes\|\.claude/modaos\|\.claude/models\|\.claude/architecture\|\.claude/notes\|\.claude/logs\|\.claude/project-rules" \
  --include="*.md" \
  cadence-init/ cadence-workflow/ readmes/ CLAUDE.md AGENTS.md 2>/dev/null || echo "无遗漏"
```

**注意**：
- `.cadence/` 不在搜索范围内，已迁移
- install-offline.sh/bat 中的 `$HOME/.claude/plugins/` 是插件目录，不是业务文档路径，无需更新

- [ ] **Step 2: 确认 marketplace.json 是否需要更新**

```bash
grep -n "\.claude/" .claude-plugin/marketplace.json
```

如果 marketplace.json 中有 `.claude/` 业务文档路径引用，按同样规则更新。

- [ ] **Step 3: 最终 commit（所有未提交变更）**

```bash
git status
git add -A
git commit -m "chore: 完成 rule-config 命令改造，所有文档路径迁移到 .cadence/

实施内容：
- 模板文件更新（document-storage、project-rules）
- CLAUDE.md 和 AGENTS.md 路径引用更新
- rule-config 命令流程重组（三态检测 + .cadence 迁移）
- cadence-workflow skills/commands 路径更新
- readmes/skills 路径更新

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## 实施依赖关系

```
Chunk 1 (模板文件)
    ↓
Chunk 2 (CLAUDE.md, AGENTS.md)
    ↓
Chunk 3 (rule-config.md) ← 这是核心，依赖 Chunk 1 的模板更新
    ↓
Chunk 4 (cadence-init 其他命令)
    ↓
Chunk 5 (cadence-workflow skills)
    ↓
Chunk 6 (cadence-workflow commands)
    ↓
Chunk 7 (readmes/skills)
    ↓
Chunk 8 (收尾检查)
```

**注意**：Chunk 5-7 可以并行执行（相互无依赖），但必须在 Chunk 3 之后执行（因为 rule-config.md 是其他文件的模板来源）。
