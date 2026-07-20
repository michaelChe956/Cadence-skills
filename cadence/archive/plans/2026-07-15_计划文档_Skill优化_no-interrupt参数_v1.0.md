# no-interrupt 参数隔离实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. 本任务不使用子 Agent，各步骤在当前会话内执行并逐项验证。

**Goal:** 为四个初始化 Skill 增加显式、向后兼容的 `no-interrupt`/`--no-interrupt` 模式，不带参数时保持原逻辑。

**Architecture:** 每个 `SKILL.md` 保留现有普通模式章节，在前部增加统一的参数识别与模式分流契约，再为本 Skill 增加独立的严格分支。严格分支使用确定性安装、合并、备份和失败策略；普通模式原文及行为不改写。

**Tech Stack:** Markdown、YAML frontmatter、`rg`、现有 Skill 校验脚本、Git 差异检查。

## Global Constraints

- 不带 `no-interrupt` 或 `--no-interrupt` 时，四个 Skill 的当前行为必须保持不变。
- 参数按完整 token 匹配，不使用模糊包含匹配。
- `no-interrupt` 模式禁止调用 `AskUserQuestion`、`request_user_input` 或等价用户提问工具。
- 不新增辅助程序；本仓库以 Markdown 文档修改为主。
- 不修改 `.claude/rules/` 框架内置规则。
- 不收集或输出真实 API Key、Token、密码。

---

### Task 1: 固化 RED 基线与统一参数契约

**Files:**

- Reference: `cadence/designs/2026-07-15_技术方案_no-interrupt模式与冲突合并_v1.0.md`
- Modify: `cadence-init/skills/pre-check/SKILL.md`
- Modify: `cadence-init/skills/rule-config/SKILL.md`
- Modify: `cadence-init/skills/mcp-configuration/SKILL.md`
- Modify: `cadence-init/skills/project-rules-examples/SKILL.md`

**Interfaces:**

- Consumes: 用户命令参数 token。
- Produces: `普通模式` 或 `no-interrupt 模式` 两种互斥执行分支。

- [x] **Step 1: 记录参数支持缺失的 RED 结果**

运行：

```bash
rg -n 'no-interrupt|--no-interrupt' cadence-init/skills/pre-check/SKILL.md cadence-init/skills/rule-config/SKILL.md cadence-init/skills/mcp-configuration/SKILL.md cadence-init/skills/project-rules-examples/SKILL.md
```

预期：退出码为 1，证明四个 Skill 尚未定义参数。

- [x] **Step 2: 在每个 Skill 的概述后加入相同参数契约**

契约必须包含：

```markdown
## 参数模式

- 命令参数包含完整 token `no-interrupt` 或 `--no-interrupt`：进入强制无交互模式。
- 未携带上述参数：进入普通模式，完整遵循本 Skill 原有逻辑。
- 两种模式互斥；不得把强制无交互规则应用到普通模式。

### no-interrupt 通用规则

- 禁止调用用户提问工具、等待输入或使用超时默认值。
- 能自动处理的冲突按本 Skill 的严格策略处理。
- 无法完成强制结果时立即报错终止。
- 失败报告包含失败步骤、原因、已完成步骤和恢复建议。
```

- [x] **Step 3: 验证四个文件均包含参数契约**

运行：

```bash
rg -l '完整 token `no-interrupt` 或 `--no-interrupt`' cadence-init/skills/*/SKILL.md
```

预期：结果包含四个目标 Skill，且不要求修改其他 Skill。

### Task 2: 修改 pre-check 严格分支

**Files:**

- Modify: `cadence-init/skills/pre-check/SKILL.md`

**Interfaces:**

- Consumes: 参数模式判定、六个基础工具检查结果。
- Produces: 普通模式原行为，或严格模式的全部成功/立即失败结果。

- [x] **Step 1: 保留普通模式声明**

明确写入：现有“人工交互策略”“增量运行”“失败后继续其他检查”“同名非软链跳过”等内容只属于普通模式。

- [x] **Step 2: 增加 no-interrupt 强制安装表**

严格模式表必须定义：

| 项目 | 成功条件 | 失败动作 |
|------|----------|----------|
| npx | 版本命令成功 | 终止 |
| uvx | 版本命令成功 | 终止 |
| ast-grep | 版本命令成功 | 终止 |
| codegraph | 版本命令成功 | 终止 |
| OpenSpec | CLI 与项目指令文件验证成功 | 终止 |
| Superpowers | 来源目录与三层软链验证成功 | 终止 |
| Playwright | 仅用户明确要求时检查 | 未要求时允许跳过 |

- [x] **Step 3: 增加 Superpowers 严格失败流程**

严格模式按以下顺序执行：现有来源校验 → 在线安装或更新 → 固定离线目录校验。固定离线目录 `~/.agents/superpowers/skills` 无效时直接报错，不询问来源路径，不执行 API Key 提醒或后续 Skill。

- [x] **Step 4: 增加同名冲突备份规则**

同名非软链内容重命名为 `<原名称>.cadence-backup-YYYYMMDDHHMMSS`，然后创建正确目录或软链并验证；备份、创建或验证失败均终止，禁止删除原内容。

- [x] **Step 5: 验证普通模式文本仍存在且严格分支完整**

运行：

```bash
rg -n '普通模式|no-interrupt 模式|cadence-backup-YYYYMMDDHHMMSS|固定离线目录|立即终止' cadence-init/skills/pre-check/SKILL.md
```

预期：同时匹配普通模式兼容声明和严格分支规则。

### Task 3: 修改 rule-config 严格合并分支

**Files:**

- Modify: `cadence-init/skills/rule-config/SKILL.md`

**Interfaces:**

- Consumes: rule-config 模板、当前项目 Markdown 文件和历史目录检测结果。
- Produces: 普通模式原有跳过/迁移行为，或严格模式的权威模板合并结果。

- [x] **Step 1: 标记现有策略属于普通模式**

明确现有“不覆盖”“冲突跳过”“历史产物自动迁移”等规则在未携带参数时保持不变。

- [x] **Step 2: 增加 no-interrupt Markdown 合并契约**

严格分支定义：模板必需章节、规则路径和强制约束为权威；项目独有章节保留；同名章节模板在前、项目去重内容追加到“项目补充”；无法解析时备份为 `.cadence-backup-YYYYMMDDHHMMSS`，标准内容在前，原内容进入“原项目补充”。

- [x] **Step 3: 增加 CLAUDE.md/AGENTS.md 合并规则**

强制规则摘要和引用路径以 Skill 为准；项目技术栈、命令、业务规则及无关章节保留；语义等价条目去重。

- [x] **Step 4: 增加严格模式禁止迁移规则**

`no-interrupt` 模式只检测 `.claude/prds`、`.claude/docs`、`.claude/plans` 等历史目录并报告，不执行移动、目录合并或删除。普通模式继续执行现有步骤 6。

- [x] **Step 5: 验证模式隔离**

运行：

```bash
rg -n '普通模式.*历史产物迁移|no-interrupt.*不执行历史产物迁移|项目补充|原项目补充' cadence-init/skills/rule-config/SKILL.md
```

预期：普通模式迁移与严格模式禁止迁移同时存在。

### Task 4: 修改 mcp-configuration 严格合并分支

**Files:**

- Modify: `cadence-init/skills/mcp-configuration/SKILL.md`

**Interfaces:**

- Consumes: Skill 标准 MCP 配置、现有 JSON/TOML 配置。
- Produces: 普通模式原有补缺/跳过行为，或严格模式的 Server 集合深度合并结果。

- [x] **Step 1: 标记现有冲突策略属于普通模式**

明确同名不同配置时询问、保留或跳过的现有逻辑仅在未携带参数时使用。

- [x] **Step 2: 增加 no-interrupt Server 合并矩阵**

矩阵必须规定：Skill 缺失 Server 新增；项目额外 Server 保留；同名 Server 的 `type`、`command`、`url`、必要参数以 Skill 为准；项目独有环境变量、Header、扩展字段保留；参数数组以 Skill 必需参数为前缀并追加不重复项目参数。

- [x] **Step 3: 增加密钥占位符例外**

现有非占位值优先于 `your_zhipu_api_key`、`your_minimax_api_key` 等占位符；报告只显示键名和“已保留非占位值”，不得显示真实值。

- [x] **Step 4: 增加解析失败与备份规则**

JSON/TOML 解析失败时备份原文件并生成标准配置；能安全识别的内容恢复为项目补充，无法保证安全恢复时终止。`.gitignore` 使用集合合并并确保必需忽略项生效。

- [x] **Step 5: 验证模式隔离和密钥规则**

运行：

```bash
rg -n '普通模式|no-interrupt 模式|非占位值|不得显示真实值|参数数组|项目额外.*保留' cadence-init/skills/mcp-configuration/SKILL.md
```

预期：普通冲突策略仍在，严格合并规则齐全。

### Task 5: 修改 project-rules-examples 严格合并分支

**Files:**

- Modify: `cadence-init/skills/project-rules-examples/SKILL.md`

**Interfaces:**

- Consumes: 标准项目规则模板、现有项目规则文件和入口引用。
- Produces: 普通模式原有“存在则跳过”，或严格模式的模板骨架与项目事实合并结果。

- [x] **Step 1: 标记现有增量策略属于普通模式**

明确目标文件存在时跳过、不覆盖和冲突报告等现有规则不变。

- [x] **Step 2: 增加 no-interrupt 模板合并规则**

严格分支规定：模板必需章节、顺序、AI 执行规则和强制约束为权威；项目已填写的技术栈、调用链、契约、异常、日志和测试事实保留；真实内容可替换相应占位符；额外章节进入“项目补充”。

- [x] **Step 3: 增加解析失败和入口引用规则**

解析失败时备份原文件、生成标准模板并把原内容附加到“原项目补充”；CLAUDE.md/AGENTS.md 的项目规则引用路径以 Skill 为准，其他内容保留。

- [x] **Step 4: 验证普通模式与严格模式并存**

运行：

```bash
rg -n '普通模式|no-interrupt 模式|已存在.*跳过|真实内容.*占位符|项目补充|原项目补充' cadence-init/skills/project-rules-examples/SKILL.md
```

预期：不带参数的跳过逻辑未删除，严格分支不再跳过冲突文件。

### Task 6: 逐 Skill 验证与整体回归

**Files:**

- Validate: `cadence-init/skills/pre-check/SKILL.md`
- Validate: `cadence-init/skills/rule-config/SKILL.md`
- Validate: `cadence-init/skills/mcp-configuration/SKILL.md`
- Validate: `cadence-init/skills/project-rules-examples/SKILL.md`

**Interfaces:**

- Consumes: 四个修改后的 Skill。
- Produces: 格式、结构、参数隔离和语义检查结果。

- [x] **Step 1: 逐个运行 Skill 结构校验**

运行：

```bash
python cadence-init/skills/skill-creator/scripts/quick_validate.py cadence-init/skills/pre-check
python cadence-init/skills/skill-creator/scripts/quick_validate.py cadence-init/skills/rule-config
python cadence-init/skills/skill-creator/scripts/quick_validate.py cadence-init/skills/mcp-configuration
python cadence-init/skills/skill-creator/scripts/quick_validate.py cadence-init/skills/project-rules-examples
```

预期：四次校验均成功。

- [x] **Step 2: 检查参数隔离声明**

运行：

```bash
rg -n '未携带.*普通模式|不得把.*应用到普通模式' cadence-init/skills/pre-check/SKILL.md cadence-init/skills/rule-config/SKILL.md cadence-init/skills/mcp-configuration/SKILL.md cadence-init/skills/project-rules-examples/SKILL.md
```

预期：每个文件至少命中两项兼容声明。

- [x] **Step 3: 检查严格分支无用户交互**

人工逐段确认每个 `no-interrupt` 章节均明确禁止提问、等待和超时默认值，且严格分支没有引用普通模式的人工交互策略。

- [x] **Step 4: 检查 Markdown 与 Git 差异**

运行：

```bash
git diff --check
git diff --stat
git status --short
```

预期：无空白错误；变更只包含设计/计划文档和四个目标 `SKILL.md`。

- [x] **Step 5: 提交实现**

```bash
git add cadence-init/skills/pre-check/SKILL.md cadence-init/skills/rule-config/SKILL.md cadence-init/skills/mcp-configuration/SKILL.md cadence-init/skills/project-rules-examples/SKILL.md cadence/plans/2026-07-15_计划文档_Skill优化_no-interrupt参数_v1.0.md
git commit -m "feat: add isolated no-interrupt skill mode"
```
