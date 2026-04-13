# rule-config 命令改造设计

## 概述

改造 `cadence-init/commands/rule-config.md` 命令，实现三大目标：
1. 项目类型检测支持全新项目让用户选择
2. 文档目录从 `.claude/` 迁移到 `.cadence/`（`.claude/rules/` 保留）
3. CLAUDE.md 和 AGENTS.md 中的路径引用同步更新

---

## 最终目录结构

```
项目根目录/
├── .claude/
│   └── rules/                    # 唯一保留 — Claude Code 自动加载
│       ├── README.md
│       ├── language.md
│       ├── code-usage.md
│       ├── document-storage.md
│       ├── markdown-format.md
│       ├── serena-usage.md
│       ├── mcp-servers.md
│       └── playwright.md
├── .cadence/                     # Cadence 框架文档中心
│   ├── project-rules/            # 从 .claude/project-rules/ 迁入
│   │   ├── README.md
│   │   └── examples/
│   ├── prds/
│   ├── plans/
│   ├── designs/
│   ├── designs-reviews/
│   ├── docs/
│   ├── analysis-docs/
│   ├── readmes/
│   ├── modaos/
│   ├── models/
│   ├── architecture/
│   ├── notes/
│   ├── logs/
│   └── reports/
├── CLAUDE.md
├── AGENTS.md
└── ...
```

---

## 改动点 1：项目类型检测改为三态

### 当前行为

二态判断：Coding / 非 Coding。Glob 搜索无结果时自动判定为非 Coding。

### 新行为

三态判断：

| 检测结果 | 含义 | 处理方式 |
|---------|------|---------|
| 检测到代码文件 | Coding 项目 | 使用 `code-usage-coding.md` |
| 未检测到代码文件 | 待确认 | **询问用户**：Coding / 非 Coding |
| 全新空目录（无任何文件） | 新项目 | **询问用户**：Coding / 非 Coding / 跳过 |

### 实现步骤

**步骤 0（前置）：全新项目检测**

在步骤 1a（项目类型检测）之前，先检测目录是否为空：
- 执行 Glob 搜索 `*`（不含 `.*`）判断是否为空目录
- 如果为空，视为全新项目，向用户展示选项

**步骤 1a（修改）：三态检测**

```
使用 Glob 搜索常见源代码文件：
**/*.{java,js,ts,py,go,php,rs,rb,swift,kt,c,cpp,cs}

排除框架内部目录：
cadence-init/, Cadence-skills/, .claude-plugin/, node_modules/

排除后：
- 有匹配结果 → Coding 项目
- 无匹配结果 → 非 Coding 项目（进入步骤 0b 询问用户）
```

**步骤 0b（新增）：全新/待确认项目询问**

向用户展示：
```
检测到当前项目【不是 Coding 项目】（或为空目录）。
请选择项目类型：
1. Coding 项目 — 将使用代码开发规则（code-usage-coding.md）
2. 非 Coding 项目 — 使用非代码规则（code-usage-noncoding.md）
3. 跳过 — 不配置代码使用规则
```

---

## 改动点 2：.cadence 迁移流程（新增前置步骤）

### 处理流程

```
步骤 0（新增）：.cadence 迁移检测
│
├── 1. 检测 .claude/ 下是否存在需迁移的子目录
│   ├── 需迁移的目录：project-rules/, prds/, plans/, designs/,
│   │                 designs-reviews/, docs/, analysis-docs/,
│   │                 readmes/, modaos/, models/, architecture/,
│   │                 notes/, logs/, reports/
│   └── .claude/rules/ 不在迁移范围内
│
├── 2. 判断迁移状态
│   │
│   ├── 【情况 A】.cadence/ 已存在
│   │   └── 跳过迁移（避免覆盖已有数据），仅更新引用
│   │
│   ├── 【情况 B】.claude/ 下有需迁移目录，且 .cadence/ 不存在
│   │   ├── 提示用户：
│   │   │   "检测到现有文档是否迁移到 .cadence/？"
│   │   │   - 确认 → 执行迁移 + 更新所有引用
│   │   │   - 拒绝 → 保留原状，仅更新 document-storage 规则
│   │   └── 迁移后更新所有 workflow skills 中的路径引用
│   │
│   └── 【情况 C】.claude/ 下无需迁移目录，且 .cadence/ 不存在
│       └── 直接在 .cadence/ 创建新目录结构
│
├── 3. 迁移后操作
│   └── 询问用户：是否将 .cadence/ 加入 .gitignore
│       ├── 是 → 在 .gitignore 添加 `.cadence/`
│       └── 否 → 不做操作
│
└── 4. 更新 rules/document-storage.md 中的路径映射
    └── 将所有 .claude/ 文档路径改为 .cadence/
```

### 迁移操作明细

**目录迁移**：将以下目录从 `.claude/` 迁入 `.cadence/`

| 源路径 | 目标路径 |
|--------|---------|
| `.claude/project-rules/` | `.cadence/project-rules/` |
| `.claude/prds/` | `.cadence/prds/` |
| `.claude/plans/` | `.cadence/plans/` |
| `.claude/designs/` | `.cadence/designs/` |
| `.claude/designs-reviews/` | `.cadence/designs-reviews/` |
| `.claude/docs/` | `.cadence/docs/` |
| `.claude/analysis-docs/` | `.cadence/analysis-docs/` |
| `.claude/readmes/` | `.cadence/readmes/` |
| `.claude/modaos/` | `.cadence/modaos/` |
| `.claude/models/` | `.cadence/models/` |
| `.claude/architecture/` | `.cadence/architecture/` |
| `.claude/notes/` | `.cadence/notes/` |
| `.claude/logs/` | `.cadence/logs/` |
| `.claude/reports/` | `.cadence/reports/` |

**迁移后原目录处理**：删除原 `.claude/` 下的迁移目录

### 引用更新范围

迁移完成后，需更新以下文件中的路径引用：

| 文件类别 | 示例文件 | 更新的路径模式 |
|---------|---------|--------------|
| workflow skills | `brainstorming/SKILL.md` 等 | `.claude/prds/` → `.cadence/prds/` 等 |
| workflow commands | `full-flow.md` 等 | 同上 |
| readmes | `readmes/skills/*.md` | 同上 |
| 安装脚本 | `install-offline.sh` | 同上 |
| project-rules 示例 | `examples/*.md` | 同上 |

---

## 改动点 3：CLAUDE.md 引用更新

### 规则引用（保持 .claude/rules/ 不变）

以下规则的引用路径**保持不变**（因为 `.claude/rules/` 保留）：

```markdown
### 1. 语言规则
- **必须使用中文回答** → 详见 `.claude/rules/language.md`

### 4. Markdown 格式规则
- **代码块嵌套使用 4 反引号/3 反引号** → 详见 `.claude/rules/markdown-format.md`

### 5. Serena 使用规则
- **禁止分析 .git 目录** → 详见 `.claude/rules/serena-usage.md`

### 6. MCP Server 使用规则
- **各 MCP 工具的使用规范** → 详见 `.claude/rules/mcp-servers.md`

### 8. Playwright CLI 使用规则
- **浏览器自动化工具规范** → 详见 `.claude/rules/playwright.md`
```

### 文档路径引用（改为 .cadence/）

```markdown
### 3. 文档存储规则
- **所有文档必须存放在 `.cadence` 目录下** → 详见 `.claude/rules/document-storage.md`
```

### project-rules 引用（改为 .cadence/）

```markdown
### 7. 项目个性化规则（强制规则）
- **用户自定义规则只能存放在 `.cadence/project-rules/` 目录**
- 禁止在 `rules/` 目录中添加用户自定义规则
- 禁止直接修改 `rules/` 目录下的框架内置规则文件
- 详见 `.cadence/project-rules/README.md`
```

### 规则 2（代码使用规则）—— 保持不变

```markdown
### 2. 代码使用规则
- **Coding 项目**：`- **遵循 TDD 和代码规范** → 详见 .claude/rules/code-usage.md`
- **非 Coding 项目**：`- **非必要不编写代码** → 详见 .claude/rules/code-usage.md`
```

---

## 改动点 4：AGENTS.md 引用更新

### 规则引用（保持 .claude/rules/ 不变）

```markdown
### 1. 语言规则
- **必须使用中文回答** → 详见 `.claude/rules/language.md`

### 4. Markdown 格式规则
- **Markdown 编写必须遵循项目格式规范** → 详见 `.claude/rules/markdown-format.md`

### 5. 仓库分析规则
- **禁止分析 `.git` 目录** → 详见 `.claude/rules/serena-usage.md`

### 6. MCP Server 与工具使用规则
- **各 MCP 工具及相关自动化工具的使用必须遵循项目规范** → 详见 `.claude/rules/mcp-servers.md`

### 8. Playwright CLI 使用规则
- **浏览器自动化工具必须遵循项目规范** → 详见 `.claude/rules/playwright.md`
```

### 文档路径引用（改为 .cadence/）

```markdown
### 3. 文档存储规则
- **除本文件 `AGENTS.md` 外，所有文档必须存放在 `.cadence` 目录下** → 详见 `.claude/rules/document-storage.md`
- 本文件 `AGENTS.md` 作为仓库根目录的代理入口说明文件，按用户要求放置于项目根目录。
```

### project-rules 引用（改为 .cadence/）

```markdown
### 7. 项目个性化规则
- **用户自定义规则只能存放在 `.cadence/project-rules/` 目录**
- 禁止在 `.claude/rules/` 目录中添加用户自定义规则
- 禁止直接修改 `.claude/rules/` 目录下的框架内置规则文件
- 详见 `.cadence/project-rules/README.md`
```

---

## 改动点 5：模板文件更新

### cadence-init/references/rules/document-storage.md

将所有 `.claude/` 文档路径改为 `.cadence/`，`.claude/rules/` 保持不变：

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

注意：`document-storage.md` 模板本身的路径引用示例也要同步更新，否则 rule-config 命令复制时会带入旧路径。

### cadence-init/references/project-rules/README.md

```markdown
# 框架内置规则目录

## 目录说明

本目录存放 Cadence 框架的项目个性化规则文件。

## 文件列表

| 文件 | 内容概述 |
|------|---------|
| `README.md` | 本文件，项目个性化规则说明 |
| `examples/` | 示例文件：需求文档模板、设计文档模板、编码规范、测试规范 |

## 修改权限

- **仅框架维护者**可以修改 `.claude/rules/` 目录下的内置规则文件
- 用户自定义规则放在 `.cadence/project-rules/` 目录
- **禁止**用户直接修改 `.claude/rules/` 目录下的框架内置规则文件
```

### cadence-init/references/project-rules/CLAUDE-RULE.md

将 `.claude/project-rules/` 改为 `.cadence/project-rules/`。

### cadence-init/commands/project-rules-examples.md

创建目录从 `.claude/project-rules/examples/` 改为 `.cadence/project-rules/examples/`。

---

## 改动点 6：Workflow Skills 路径更新

所有 cadence-workflow skills 中引用的 `.claude/` 文档路径需同步更新为 `.cadence/`。

主要涉及文件：

| 文件 | 路径模式 |
|------|---------|
| `cadence-workflow/skills/brainstorming/SKILL.md` | `.claude/prds/` → `.cadence/prds/` |
| `cadence-workflow/skills/analyze/SKILL.md` | `.claude/analysis-docs/` → `.cadence/analysis-docs/` |
| `cadence-workflow/skills/requirement/SKILL.md` | `.claude/docs/` → `.cadence/docs/` |
| `cadence-workflow/skills/design/SKILL.md` | `.claude/designs/` → `.cadence/designs/` |
| `cadence-workflow/skills/design-review/SKILL.md` | `.claude/designs-reviews/` → `.cadence/designs-reviews/` |
| `cadence-workflow/skills/plan/SKILL.md` | `.claude/plans/` → `.cadence/plans/` |
| `cadence-workflow/skills/full-flow/SKILL.md` | 多个路径更新 |
| `cadence-workflow/skills/quick-flow/SKILL.md` | 多个路径更新 |
| `cadence-workflow/skills/exploration-flow/SKILL.md` | 多个路径更新 |
| `cadence-workflow/skills/checkpoint/SKILL.md` | `.claude/plans/` 等 |
| `cadence-workflow/skills/status/SKILL.md` | 同上 |
| `cadence-workflow/skills/resume/SKILL.md` | 同上 |
| `cadence-workflow/skills/report/SKILL.md` | `.claude/reports/` → `.cadence/reports/` |
| `cadence-workflow/commands/full-flow.md` | 多个路径更新 |
| `cadence-workflow/commands/plan.md` | 同上 |
| `cadence-workflow/commands/quick-flow.md` | 同上 |
| `readmes/skills/*.md` | 多个路径更新 |

---

## 改动点 7：rule-config 命令流程重组

### 新流程（新增步骤 0）

```
0. .cadence 迁移检测
   ├── 0a. 检测 .cadence/ 是否已存在
   ├── 0b. 如不存在，检测 .claude/ 下是否有需迁移目录
   ├── 0c. 询问用户迁移确认
   ├── 0d. 执行迁移 + 更新引用
   └── 0e. 询问 .cadence/.gitignore

1. 创建 rules 目录和规则文件
   ├── 1a. 项目类型检测（三态）
   ├── 1b. 定位模板目录
   ├── 1c. 创建 .claude/rules/ 目录
   └── 1d. 复制规则文件

2. 添加 CLAUDE.md 规则引用（路径已更新）

3. 包管理器规则（不变）

4. 技术栈检测（不变）

5. 目录结构创建
   └── 创建 .cadence/ 子目录（不再创建 .claude/ 下的业务目录）

6. Playwright Skills 规则配置（不变）
```

### 目录创建的变更（步骤 5）

旧：
```bash
mkdir -p .claude/{rules,prds,analysis-docs,docs,designs,designs-reviews,plans,readmes,modaos,models,architecture,notes,logs,reports,project-rules/examples}
```

新：
```bash
# rules 目录已在步骤 1c 创建，此处只需创建 .cadence/ 结构
mkdir -p .cadence/{project-rules/examples,prds,analysis-docs,docs,designs,designs-reviews,plans,readmes,modaos,models,architecture,notes,logs,reports}
```

---

## 实施检查清单

- [ ] 更新 `cadence-init/commands/rule-config.md`（流程重组）
- [ ] 更新 `cadence-init/references/rules/document-storage.md`（路径映射）
- [ ] 更新 `cadence-init/references/rules/README.md`（如需）
- [ ] 更新 `cadence-init/references/project-rules/README.md`（project-rules 路径）
- [ ] 更新 `cadence-init/references/project-rules/CLAUDE-RULE.md`（同上）
- [ ] 更新 `cadence-init/commands/project-rules-examples.md`（创建目录）
- [ ] 更新 `CLAUDE.md`（规则引用路径）
- [ ] 更新 `AGENTS.md`（规则引用路径）
- [ ] 更新所有 cadence-workflow skills 中的文档路径引用
- [ ] 更新所有 cadence-workflow commands 中的文档路径引用
- [ ] 更新 `readmes/skills/*.md` 中的文档路径引用
- [ ] 更新 `install-offline.sh` 中的路径引用
- [ ] 更新 `install-offline.bat` 中的路径引用
- [ ] 更新 `.claude-plugin/marketplace.json`（如有需要）
- [ ] 将本设计文档提交 git

---

## 回滚策略

如迁移过程中出现问题，可通过以下方式回滚：

1. **引用回滚**：将所有 `.cadence/` 路径改回 `.claude/`（不含 rules/）
2. **目录回滚**：将 `.cadence/` 下的内容移回 `.claude/`（如有备份）
3. **不迁移模式**：用户可选择不迁移，在 `.claude/` 下保留原状
