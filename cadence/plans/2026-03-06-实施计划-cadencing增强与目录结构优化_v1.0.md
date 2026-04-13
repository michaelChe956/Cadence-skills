# 实施计划：Cadencing Skill 增强与目录结构优化

**计划信息**
- **计划编号**：PLAN-2026-03-06-001
- **创建日期**：2026-03-06
- **版本**：v1.0
- **负责人**：Claude
- **关联设计**：DES-2026-03-06-001

## 执行摘要

本计划将增强 cadencing skill，优化项目目录结构，并为用户提供定制化能力。包含 11 个任务，预计 3-4 小时完成。

## 前置条件

- [x] 设计文档已创建并提交
- [ ] 代码库处于干净状态（无未提交的更改）
- [ ] Git 分支：在 main 分支上工作

## 任务清单

### 任务 1：更新 cadencing skill - 添加步骤 2.5（项目分析）

**目标**：在步骤 2 之后添加项目分析功能

**文件**：`/Users/michaelche/Documents/git-folder/github-folder/Cadence-skills/skills/cadencing/SKILL.md`

**具体步骤**：

1. 在 "## 检查清单" 部分，在步骤 2 之后插入新步骤 2.5：

```markdown
1. **前置条件检查** — 检查 npx、uvx、serena 路径
2. **Claude Code 初始化** — 调用 `/init` 命令，验证 CLAUDE.md 已创建
2.5. **项目分析** — 分析项目结构、依赖、Git 历史，生成摘要文档
3. **添加语言规则** — 配置强制中文响应
```

2. 在 "## 处理流程" 部分，在 "### 强制规则配置" 之前添加新章节：

```markdown
### 项目分析（步骤 2.5）

**分析流程**：

**1. 收集项目信息**
```bash
# 统计文件和目录数量
find . -type f -not -path '*/\.*' | wc -l  # 文件数
find . -type d -not -path '*/\.*' | wc -l  # 目录数

# 识别主要编程语言
find . -name "*.py" -o -name "*.js" -o -name "*.ts" -o -name "*.java" | head -20

# 检测项目类型
ls -la | grep -E "package.json|requirements.txt|pom.xml|go.mod"
```

**2. 分析目录结构**
```bash
# 获取主要目录
find . -maxdepth 2 -type d -not -path '*/\.*' | head -20
```

**3. 分析依赖关系**
- 读取 package.json（前端项目）
- 读取 requirements.txt（Python 项目）
- 读取 pom.xml（Java 项目）

**4. 分析 Git 历史**
```bash
# 最近 10 条提交
git log --oneline -10

# 提交统计
git log --oneline --since="30 days ago" | wc -l
```

**5. 生成分析报告**

**文件路径**：`.claude/analysis-docs/YYYY-MM-DD_分析报告_项目初始化摘要_v1.0.md`

**文件内容模板**：
```markdown
# 项目初始化分析摘要

**生成时间**：[当前时间]
**项目路径**：[项目路径]

## 1. 项目基本信息

- **项目类型**：[前端/后端/全栈/其他]
- **主要语言**：[语言列表]
- **项目规模**：
  - 文件总数：[数量]
  - 目录总数：[数量]
  - 估算代码行数：[数量]

## 2. 目录结构

```
[主要目录树]
```

**目录说明**：
- `src/`：[说明]
- `tests/`：[说明]

## 3. 依赖关系

**主要依赖**：
- [依赖名称]：[版本]

## 4. 主要模块

- **模块 1**：[说明]
- **模块 2**：[说明]

## 5. Git 历史

**最近提交**：
```
[最近 10 条提交]
```

**提交统计**：
- 最近 30 天提交数：[数量]

## 6. 下一步建议

[基于分析的建议]
```

**错误处理**：
- 如果不是 Git 仓库，跳过 Git 历史分析
- 如果文件过多（>10000），显示进度提示
- 超时限制：30 秒
```

**验收标准**：
- [ ] 检查清单包含步骤 2.5
- [ ] 处理流程包含完整的项目分析章节
- [ ] 包含所有必需的 bash 命令
- [ ] 包含完整的文件内容模板

**提交信息**：
```bash
git add skills/cadencing/SKILL.md
git commit -m "feat(cadencing): 添加步骤 2.5 - 项目分析功能

- 在初始化后分析项目结构、依赖和 Git 历史
- 生成分析报告到 analysis-docs/ 目录
- 为后续开发提供项目概览

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

### 任务 2：更新 cadencing skill - 添加步骤 11（个性化规则示例）

**目标**：在步骤 10 之后添加创建个性化规则示例的功能

**文件**：`/Users/michaelche/Documents/git-folder/github-folder/Cadence-skills/skills/cadencing/SKILL.md`

**具体步骤**：

1. 在 "## 检查清单" 部分，在步骤 10 之后添加步骤 11：

```markdown
10. **创建目录结构** — 创建 `.claude/` 子目录
11. **创建个性化规则示例** — 在 `project-rules/` 中创建示例模板和规范
```

2. 在 "### 目录结构创建" 之后添加新章节：

```markdown
### 创建个性化规则示例（步骤 11）

**创建目录结构**：
```
.claude/project-rules/
├── README.md                          # 使用说明
└── examples/                           # 示例目录
    ├── requirement-template.md        # 需求文档模板
    ├── design-template.md             # 设计文档模板
    ├── coding-standards.md            # 代码开发规范
    └── test-standards.md              # 测试规范
```

**创建 README.md**：

**文件路径**：`.claude/project-rules/README.md`

**文件内容**：
```markdown
# 项目个性化规则文档

## 📖 目录说明

本目录用于存放项目个性化的规则文档，包括模板、规范、约定等。

## 🎯 使用方法

### 步骤 1：浏览示例

查看 `examples/` 目录中的示例文件，了解可以定制的内容。

### 步骤 2：创建您的规则

1. 复制 `examples/` 中的模板到本目录
2. 根据您的项目需求修改内容
3. 重命名为合适的文件名（不含 `examples/` 前缀）

### 步骤 3：在 CLAUDE.md 中启用

在项目根目录的 `CLAUDE.md` 中添加规则，指导 Claude 使用您的定制文档。

**示例：**

\`\`\`markdown
## 项目个性化规则

### 需求文档格式
使用 \`.claude/project-rules/requirement-template.md\` 作为需求文档格式，
不要使用 requirement skill 中的通用格式。

### 设计文档格式
使用 \`.claude/project-rules/design-template.md\` 作为设计文档模板。

### 代码开发规范
所有代码开发必须遵循 \`.claude/project-rules/coding-standards.md\` 中的规范。
\`\`\`

## 📁 文件说明

### requirement-template.md
需求文档模板，定义需求文档的格式和内容结构。

### design-template.md
设计文档模板，定义设计文档的格式和内容结构。

### coding-standards.md
代码开发规范，包括命名规范、代码风格、注释规范等。

### test-standards.md
测试规范，包括测试覆盖率要求、测试类型要求、测试命名规范等。

## 💡 提示

- 只创建您需要的规则文档，不必全部创建
- 规则文档可以根据项目需求随时调整
- 在 CLAUDE.md 中明确说明何时使用哪个规则文档

## 📝 示例文件

所有示例文件都在 `examples/` 目录中，包含详细的注释和说明。
```

**创建示例文件**：

所有示例文件的完整内容见设计文档 8.1 节。

**说明**：
- 示例文件包含详细注释
- 提供完整的模板结构
- 不自动启用，仅作参考
- 用户需要主动修改和启用
```

**验收标准**：
- [ ] 检查清单包含步骤 11
- [ ] 处理流程包含完整的创建规则示例章节
- [ ] 包含 README.md 的完整内容
- [ ] 引用设计文档中的示例文件内容

**提交信息**：
```bash
git add skills/cadencing/SKILL.md
git commit -m "feat(cadencing): 添加步骤 11 - 创建个性化规则示例

- 在 project-rules/ 目录创建示例模板
- 包含需求、设计、代码、测试规范示例
- 提供详细的使用说明和注释
- 用户可选择性启用

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

### 任务 3：更新 cadencing skill - 更新目录结构创建

**目标**：更新步骤 10 的目录结构，包含新增和重命名的目录

**文件**：`/Users/michaelche/Documents/git-folder/github-folder/Cadence-skills/skills/cadencing/SKILL.md`

**具体步骤**：

1. 在 "### 目录结构创建" 部分，更新目录结构：

**原内容**：
```markdown
### 目录结构创建

```
.claude/
├── docs/           # 需求文档
├── designs/        # 设计文档
├── readmes/        # README 文档
├── modao/          # 界面原型
├── model/          # 数据模型
├── architecture/   # 架构文档
├── notes/          # 开发笔记
├── analysis/       # 分析报告
└── logs/           # 开发日志
```
```

**新内容**：
```markdown
### 目录结构创建（步骤 10）

**创建以下目录结构**：

```
.claude/
├── prds/                   # 概要需求文档（新增）
├── analysis-docs/          # 分析报告（重命名自 analysis）
├── docs/                   # 详细需求文档
├── designs/                # 设计文档
├── designs-reviews/        # 设计评审（新增）
├── plans/                  # 计划文档
├── readmes/                # README 文档
├── modaos/                 # 界面原型（重命名自 modao）
├── models/                 # 数据模型（重命名自 model）
├── architecture/           # 架构文档
├── notes/                  # 开发笔记
├── logs/                   # 开发日志
└── reports/                # 进度报告（新增）
```

**目录用途说明**：

| 目录 | 用途 | 说明 |
|------|------|------|
| `prds/` | 概要需求 | @brainstorming skill 生成的早期需求方案 |
| `analysis-docs/` | 分析报告 | @analyze skill 生成的代码分析、调研报告 |
| `docs/` | 详细需求 | @requirement skill 生成的详细需求文档 |
| `designs/` | 设计文档 | @design skill 生成的技术方案、架构设计 |
| `designs-reviews/` | 设计评审 | @design-review skill 的评审文档 |
| `plans/` | 计划文档 | @plan skill 生成的实施计划 |
| `reports/` | 进度报告 | @report skill 生成的开发进度报告 |
| `project-rules/` | 个性化规则 | 用户定制的模板和规范（步骤 11 创建） |

**创建命令**：
```bash
mkdir -p .claude/{prds,analysis-docs,docs,designs,designs-reviews,plans,readmes,modaos,models,architecture,notes,logs,reports,project-rules/examples}
```
```

**验收标准**：
- [ ] 目录结构包含所有新增目录
- [ ] 目录结构包含所有重命名目录
- [ ] 包含目录用途说明表格
- [ ] 包含正确的创建命令

**提交信息**：
```bash
git add skills/cadencing/SKILL.md
git commit -m "feat(cadencing): 更新目录结构 - 新增和重命名目录

新增目录：
- prds/：概要需求文档
- designs-reviews/：设计评审
- reports/：进度报告
- project-rules/：个性化规则

重命名目录：
- analysis/ → analysis-docs/
- modao/ → modaos/
- model/ → models/

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

### 任务 4：更新 brainstorming skill - 明确输出路径

**目标**：在 brainstorming skill 中明确输出到 `.claude/prds/` 目录

**文件**：`/Users/michaelche/Documents/git-folder/github-folder/Cadence-skills/skills/brainstorming/SKILL.md`

**具体步骤**：

1. 在 "## After the Design" 部分的 "**Documentation:**" 下，找到设计文档保存路径的描述

2. 更新为：
```markdown
**Documentation:**
- Write the validated design to `.claude/prds/YYYY-MM-DD-<topic>-design.md`
- Use elements-of-style:writing-clearly-and-concisely skill if available
- Commit the design document to git
```

**验收标准**：
- [ ] 设计文档保存路径更新为 `.claude/prds/`
- [ ] 文件命名格式明确

**提交信息**：
```bash
git add skills/brainstorming/SKILL.md
git commit -m "feat(brainstorming): 明确输出路径为 .claude/prds/

- 概要需求文档保存到 prds/ 目录
- 与详细需求文档（docs/）区分

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

### 任务 5：更新 design-review skill - 明确输出路径

**目标**：在 design-review skill 中明确输出到 `.claude/designs-reviews/` 目录

**文件**：`/Users/michaelche/Documents/git-folder/github-folder/Cadence-skills/skills/design-review/SKILL.md`

**具体步骤**：

1. 查找设计评审文档的保存路径描述

2. 添加或更新为：
```markdown
**输出路径**：`.claude/designs-reviews/YYYY-MM-DD_设计评审_[设计名称]_v1.0.md`
```

**验收标准**：
- [ ] 设计评审文档保存路径明确为 `.claude/designs-reviews/`
- [ ] 文件命名格式符合规范

**提交信息**：
```bash
git add skills/design-review/SKILL.md
git commit -m "feat(design-review): 明确输出路径为 .claude/designs-reviews/

- 设计评审文档保存到 designs-reviews/ 目录
- 便于区分设计文档和评审文档

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

### 任务 6：更新 analyze skill - 调整输出路径

**目标**：将 analyze skill 的输出路径从 `analysis/` 更新为 `analysis-docs/`

**文件**：`/Users/michaelche/Documents/git-folder/github-folder/Cadence-skills/skills/analyze/SKILL.md`

**具体步骤**：

1. 查找所有 `.claude/analysis/` 路径

2. 替换为 `.claude/analysis-docs/`

3. 更新文件命名示例（如果有）

**验收标准**：
- [ ] 所有 `analysis/` 路径更新为 `analysis-docs/`
- [ ] 文件命名格式保持一致

**提交信息**：
```bash
git add skills/analyze/SKILL.md
git commit -m "feat(analyze): 调整输出路径为 .claude/analysis-docs/

- 统一命名风格，避免与通用词汇冲突
- 保持与其他文档目录的一致性

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

### 任务 7：更新 report skill - 确认输出路径

**目标**：确认 report skill 的输出路径为 `.claude/reports/`

**文件**：`/Users/michaelche/Documents/git-folder/github-folder/Cadence-skills/skills/report/SKILL.md`

**具体步骤**：

1. 查找报告文档的保存路径描述

2. 确认路径为 `.claude/reports/`

3. 如果需要，更新文件命名格式为：`YYYY-MM-DD_开发报告_[项目名]_v1.0.md`

**验收标准**：
- [ ] 进度报告文档保存路径确认为 `.claude/reports/`
- [ ] 文件命名格式符合规范

**提交信息**：
```bash
git add skills/report/SKILL.md
git commit -m "docs(report): 确认输出路径为 .claude/reports/

- 进度报告保存到 reports/ 目录
- 更新文件命名规范说明

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

### 任务 8：更新 CLAUDE.md - 文档分类存储规范

**目标**：更新文档分类存储规范表格，反映新的目录结构

**文件**：`/Users/michaelche/Documents/git-folder/github-folder/Cadence-skills/CLAUDE.md`

**具体步骤**：

1. 在 "#### 文档分类存储规范" 部分，找到表格

2. 更新表格为：

```markdown
| 文档类型 | 存储路径 | 说明 |
|---------|---------|------|
| **计划文档** | **`.claude/plans/`** | **项目计划、开发计划、发布计划（🔴 强制路径）** |
| **概要需求** | **`.claude/prds/`** | **brainstorm skill 生成的概要需求方案（🔴 新增）** |
| 需求文档 | `.claude/docs/` | requirement skill 生成的详细需求文档 |
| 方案设计 | `.claude/designs/` | 技术方案、架构设计、API设计 |
| **设计评审** | **`.claude/designs-reviews/`** | **设计评审文档（🔴 新增）** |
| **分析报告** | **`.claude/analysis-docs/`** | **代码分析、调研报告、性能分析（🔴 路径调整）** |
| **进度报告** | **`.claude/reports/`** | **开发进度报告、阶段总结（🔴 新增）** |
| **个性化规则** | **`.claude/project-rules/`** | **项目个性化模板和规范（🔴 新增）** |
| **README文档** | **见下方详细规则** | **项目说明、安装指南、使用文档（🔴 特殊规则）** |
| 页面原型 | `.claude/modaos/` | 墨刀/Figma 原型截图、设计稿 |
| 数据模型 | `.claude/models/` | 数据库表模型、ER图、schema |
| 架构文档 | `.claude/architecture/` | 系统架构分析、技术选型 |
| 开发笔记 | `.claude/notes/` | 临时记录、开发心得、TODO |
| 开发日志 | `.claude/logs/` | 问题追踪、Bug记录、开发进度 |
```

**验收标准**：
- [ ] 表格包含所有新增的文档类型
- [ ] 路径调整标记清晰
- [ ] 新增内容有 🔴 标记

**提交信息**：
```bash
git add CLAUDE.md
git commit -m "docs(CLAUDE.md): 更新文档分类存储规范

新增文档类型：
- 概要需求（prds/）
- 设计评审（designs-reviews/）
- 进度报告（reports/）
- 个性化规则（project-rules/）

路径调整：
- analysis/ → analysis-docs/

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

### 任务 9：更新 CLAUDE.md - 添加个性化规则章节

**目标**：在 CLAUDE.md 中添加项目个性化规则的使用说明

**文件**：`/Users/michaelche/Documents/git-folder/github-folder/Cadence-skills/CLAUDE.md`

**具体步骤**：

1. 在 "### 5. Serena 使用规则" 之后，添加新章节：

```markdown
### 6. 项目个性化规则

> **🔴 定制化能力**

- **规则目录**：`.claude/project-rules/`
- **使用方法**：
  1. 查看项目初始化时创建的示例文件（`examples/` 目录）
  2. 根据需要复制和修改示例文件到 `project-rules/` 目录
  3. 在本文件（CLAUDE.md）中添加规则，指导 Claude 使用您的定制文档

**示例规则**：

```markdown
## 项目个性化规则（示例）

> 以下是使用示例，默认不启用。
> 如果您创建了自定义规则，可以取消注释或添加类似规则：

<!--
### 需求文档格式
使用 `.claude/project-rules/requirement-template.md` 作为需求文档格式，
不要使用 requirement skill 中的通用格式。

### 设计文档格式
使用 `.claude/project-rules/design-template.md` 作为设计文档模板。

### 代码开发规范
所有代码开发必须遵循 `.claude/project-rules/coding-standards.md` 中的规范。
-->
```

**说明**：
- 个性化规则由用户主动启用
- Claude Code 会自动遵循 CLAUDE.md 中的规则
- 示例文件仅作参考，不强制使用
- 用户可以根据项目需求自由定制规则内容
```

2. 更新后续章节的编号（如果有）

**验收标准**：
- [ ] 新增章节内容完整
- [ ] 包含清晰的使用说明
- [ ] 包含示例规则（注释状态）
- [ ] 章节编号正确

**提交信息**：
```bash
git add CLAUDE.md
git commit -m "docs(CLAUDE.md): 添加项目个性化规则章节

- 说明如何使用 project-rules/ 目录
- 提供示例规则（注释状态，不自动启用）
- 引导用户根据需求定制规则

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

### 任务 10：创建示例文件 - project-rules 目录

**目标**：创建 project-rules/ 目录及所有示例文件

**目录**：`.claude/project-rules/`

**具体步骤**：

1. 创建 README.md（内容见任务 2）

2. 创建 examples/ 目录

3. 创建以下示例文件（完整内容见设计文档 8.1 节）：
   - requirement-template.md
   - design-template.md
   - coding-standards.md
   - test-standards.md

**注意**：这些文件在项目根目录初始化时由 cadencing skill 创建，本任务是在本项目中创建示例，供参考。

**验收标准**：
- [ ] 目录结构正确
- [ ] README.md 内容完整
- [ ] 所有示例文件创建完成
- [ ] 文件内容包含详细注释

**提交信息**：
```bash
git add .claude/project-rules/
git commit -m "docs(project-rules): 创建个性化规则示例文件

- 添加 README.md 使用说明
- 添加需求文档模板示例
- 添加设计文档模板示例
- 添加代码开发规范示例
- 添加测试规范示例

所有示例包含详细注释，供用户参考定制。

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

### 任务 11：测试和验证

**目标**：测试所有修改，确保功能正常

**测试步骤**：

1. **测试目录结构创建**
```bash
# 创建测试目录
mkdir -p /tmp/test-cadencing
cd /tmp/test-cadencing

# 初始化 Git（必须）
git init
git config user.email "test@example.com"
git config user.name "Test User"

# 手动执行目录创建命令
mkdir -p .claude/{prds,analysis-docs,docs,designs,designs-reviews,plans,readmes,modaos,models,architecture,notes,logs,reports,project-rules/examples}

# 验证目录存在
ls -la .claude/
```

预期输出：所有目录都存在

2. **测试 skills 路径更新**
- 阅读每个更新的 skill 文件
- 确认路径引用正确
- 确认文件命名格式一致

3. **测试 CLAUDE.md 更新**
```bash
# 在测试目录创建 CLAUDE.md
# 复制相关章节，验证格式正确
```

4. **清理测试**
```bash
rm -rf /tmp/test-cadencing
```

**验收标准**：
- [ ] 目录创建命令执行成功
- [ ] 所有 skills 文件路径正确
- [ ] CLAUDE.md 格式正确
- [ ] 无遗留的测试文件

**提交信息**：
```bash
git add -A
git commit -m "test: 完成功能测试和验证

- 测试目录结构创建
- 验证 skills 路径更新
- 验证 CLAUDE.md 格式
- 清理测试文件

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## 执行顺序

**推荐的执行顺序**：

1. **任务 1-3**：修改 cadencing skill（核心功能）
2. **任务 4-7**：修改其他 skills（路径调整）
3. **任务 8-9**：更新 CLAUDE.md（文档规范）
4. **任务 10**：创建示例文件
5. **任务 11**：测试和验证

**依赖关系**：
- 任务 1-3 可以并行执行
- 任务 4-7 可以并行执行
- 任务 8-9 可以并行执行
- 任务 10 依赖任务 2（示例文件内容）
- 任务 11 必须最后执行

## 回滚计划

如果出现问题，执行以下回滚步骤：

```bash
# 查看提交历史
git log --oneline

# 回滚到指定提交
git reset --hard [commit-hash]

# 或者回滚最近的 N 个提交
git reset --hard HEAD~N
```

## 成功标准

- [ ] 所有 11 个任务完成
- [ ] 所有提交信息格式正确
- [ ] 所有文件路径引用正确
- [ ] 测试通过，无错误
- [ ] 代码库处于干净状态

## 预计时间

- **任务 1-3**：60-90 分钟
- **任务 4-7**：30-45 分钟
- **任务 8-9**：30-45 分钟
- **任务 10**：60-90 分钟
- **任务 11**：15-30 分钟

**总计**：195-300 分钟（3.25-5 小时）

## 注意事项

1. **必须按顺序执行**：任务之间有依赖关系
2. **频繁提交**：每完成一个任务立即提交
3. **测试充分**：不要跳过测试任务
4. **保持专注**：一次只做一个任务
5. **遇到问题**：立即记录并寻求帮助

## 完成检查清单

- [ ] 所有任务完成
- [ ] 所有测试通过
- [ ] 代码已提交到 main 分支
- [ ] 文档已更新
- [ ] 无遗留的 TODO 或注释
- [ ] 代码库干净（无未提交的更改）
