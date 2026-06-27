# 移除 Serena MCP 使用方案

## 一、目标

1. `[/pre-check]` skill 去掉 Serena MCP 的使用。
2. 当前项目（Cadence-skills 仓库本身）去掉 Serena 的 MCP 使用。
3. 梳理 `cadence-skills init` 中仍使用 Serena 的位置，供决策者判断是否一并移除。

## 二、当前工作区状态

- Worktree 分支：`feat-b-0627`（已从 `main` 拉取并推送到远端 `origin/feat-b-0627`）。
- Worktree 路径：`.worktrees/feat-b-0627/`。
- 当前分支状态：干净，无未提交改动。

## 三、现状梳理

### 3.1 当前项目（Cadence-skills 仓库）中的 Serena 使用

| 类别 | 文件 | 使用方式 | 影响程度 |
|------|------|----------|----------|
| **框架规则** | `.claude/rules/serena-usage.md` | 完整规则文件，规定 Serena 禁止分析 `.git/` 目录 | 高 |
| **框架规则** | `.claude/rules/mcp-servers.md` | 包含 "Serena MCP" 章节（用途、触发场景、常用命令） | 高 |
| **框架规则** | `.claude/rules/README.md` | 文件列表列出 `serena-usage.md` | 中 |
| **入口配置** | `CLAUDE.md` | 强制规则第 5 条 "Serena 使用规则" 引用 `.claude/rules/serena-usage.md` | 高 |
| **入口配置** | `AGENTS.md` | 强制规则第 5 条 "仓库分析规则" 引用 `.claude/rules/serena-usage.md` | 高 |
| **根说明** | `README.md` | 多处描述 Serena（初始化步骤、analyze skill、最佳实践、技术亮点） | 中 |
| **Git 忽略** | `.gitignore` | 包含 `.serena/` 目录排除项 | 中 |
| **工作流 Skill** | `cadence-workflow/skills/cad-load/SKILL.md` | 要求 Serena MCP 可用、检查 `.serena` 目录、激活 Serena 项目、保存会话记录 | 高 |
| **工作流 Skill** | `cadence-workflow/skills/status/SKILL.md` | 主数据源为 Serena memory，调用 `mcp__serena__read_memory` | 高 |
| **工作流 Skill** | `cadence-workflow/skills/checkpoint/SKILL.md` | 检查点保存到 Serena memory，调用 `mcp__serena__write_memory/read_memory/delete_memory` | 高 |
| **工作流 Skill** | `cadence-workflow/skills/data-cleanup/SKILL.md` | 基于 Serena memory 生命周期策略归档/删除数据 | 高 |
| **工作流 Skill** | `cadence-workflow/skills/version-migration/SKILL.md` | 使用 Serena memory 保存迁移后的数据 | 高 |
| **工作流 Skill** | `cadence-workflow/skills/resume/SKILL.md` | 依赖 Serena 恢复进度上下文 | 高 |
| **工作流 Skill** | `cadence-workflow/skills/report/SKILL.md` | 依赖 Serena 数据生成报告 | 高 |
| **工作流 Skill** | `cadence-workflow/skills/analyze/SKILL.md` | 使用 Serena MCP 分析代码库 | 高 |
| **工作流 Skill** | `cadence-workflow/skills/quick-flow/SKILL.md` | 流程中包含 analyze / checkpoint 等依赖 Serena 的节点 | 高 |
| **工作流 Skill** | `cadence-workflow/skills/full-flow/SKILL.md` | 同上 | 高 |
| **工作流 Skill** | `cadence-workflow/skills/exploration-flow/SKILL.md` | 同上 | 高 |
| **工作流 Skill** | `cadence-workflow/skills/design/SKILL.md` | 可能引用 Serena 作为分析输入 | 中 |
| **工作流 Skill** | `cadence-workflow/skills/design-review/SKILL.md` | 可能引用 Serena 数据 | 中 |
| **工作流 Skill** | `cadence-workflow/skills/subagent-development/SKILL.md` | 可能引用 Serena 上下文 | 中 |
| **工作流 Command** | `cadence-workflow/commands/cad-load.md` | 错误示例包含 `.serena` 目录 | 中 |
| **工作流 Command** | `cadence-workflow/commands/data-cleanup.md` | 对应 data-cleanup skill | 中 |
| **工作流 Command** | `cadence-workflow/commands/data-validation.md` | 可能涉及 Serena 数据验证 | 低 |
| **辅助工具** | `cadence-workflow/skills/transaction-utils/SKILL.md` | 可能涉及 Serena memory 事务 | 中 |
| **辅助工具** | `cadence-workflow/skills/lock-utils/SKILL.md` | 可能涉及 Serena memory 锁 | 中 |
| **历史产物** | `cadence/plans/`、`cadence/designs/`、`cadence/analysis/` 下多篇文档 | 记录中提及 Serena | 低（历史文档） |

### 3.2 cadence-skills init 中的 Serena 使用

| 文件 | 使用方式 | 影响程度 |
|------|----------|----------|
| `cadence-init/skills/pre-check/SKILL.md` | 步骤 3 为 "serena 项目目录确认"，强制规则要求完成五个基础检查（含 serena），流程图、表格、实施步骤均围绕 serena 配置展开 | 高 |
| `cadence-init/commands/pre-check.md` | 同上，作为命令说明文档 | 高 |
| `cadence-init/commands/rule-config.md` | 将 `serena-usage.md` 从 references/rules 复制到 `.claude/rules/`，并在 CLAUDE.md / AGENTS.md 中添加 "Serena 使用规则" 摘要 | 高 |
| `cadence-init/commands/mcp-configuration.md` | 在 `.mcp.json` 和 `.codex/config.toml` 中配置 serena MCP；在 `.gitignore` 中添加 `.serena/` | 高 |
| `cadence-init/references/rules/serena-usage.md` | 框架规则模板，初始化时复制到用户项目 | 高 |
| `cadence-init/references/rules/README.md` | 文件列表列出 `serena-usage.md` | 中 |
| `cadence-init/references/rules/mcp-servers.md` | 模板中包含 Serena MCP 章节 | 高 |

### 3.3 readmes 中的 Serena 使用

`readmes/skills/` 下的多个 skill 说明文档（`report.md`、`full-flow.md`、`checkpoint.md`、`version-migration.md`、`data-validation.md`、`data-cleanup.md`、`status.md`、`resume.md`、`cad-load.md`、`README.md`）均引用了 Serena，属于当前项目的文档层，需与对应 skill 同步更新。

## 四、范围界定

根据需求，本次需处理的范围为：

1. **`cadence-init/skills/pre-check/SKILL.md` 与 `cadence-init/commands/pre-check.md`**：去掉 Serena MCP 相关检查与配置步骤。
2. **当前项目（Cadence-skills 仓库）**：去掉 Serena MCP 规则、配置引用、初始化说明中的 Serena 内容。
3. **`cadence-init` 其余文件**：先梳理并列出（见 3.2），由决策者判断是否一并移除。

## 五、冲突点与待决策事项

### 5.1 框架规则修改冲突

`AGENTS.md` 与 `CLAUDE.md` 均规定：

> 禁止直接修改 `.claude/rules/` 目录下的框架内置规则文件。

但需求 2 要求去掉当前项目的 Serena MCP 使用，必然涉及：

- 删除 `.claude/rules/serena-usage.md`
- 从 `.claude/rules/mcp-servers.md` 中移除 Serena MCP 章节
- 更新 `.claude/rules/README.md` 文件列表

**决策点**：是否在本次需求中一并删除/修改 `.claude/rules/` 下的框架内置规则？

- 若保留该规则，则当前项目仍会向使用者提示 Serena 使用规范，"去掉 Serena MCP 使用" 不彻底。
- 若删除该规则，则违反现有 `AGENTS.md` / `CLAUDE.md` 的框架规则保护条款，需要同步更新 `AGENTS.md` / `CLAUDE.md` 中的相关摘要。

### 5.2 cadence-workflow 深度依赖 Serena

cadence-workflow 的多个核心 skill（`cad-load`、`status`、`checkpoint`、`data-cleanup`、`version-migration`、`resume`、`report`、`analyze` 等）以 Serena memory 作为主要持久化与状态同步机制。

**决策点**：当前项目去掉 Serena 时，是否同步改造 cadence-workflow？

- **选项 A（轻量）**：仅删除规则、配置、初始化说明层面的 Serena 引用，保留 cadence-workflow 代码/文档中对 Serena 的调用。Cadence-skills 仓库自身不再配置 Serena，但 skill 内容仍保留 Serena 能力供其他项目使用。
- **选项 B（彻底）**：同步移除 cadence-workflow 中所有 Serena 依赖，需重新设计持久化/状态同步机制，工作量大。
- **选项 C（折中）**：保留 skill 功能但将 Serena 改为可选/回退机制，不强制依赖 Serena。

建议本次先按 **选项 A** 执行，聚焦规则与配置层面的去 Serena 化；cadence-workflow 的功能层改造作为后续独立任务。

### 5.3 cadence-init 中是否完全删除 Serena 模板

`cadence-init/references/rules/serena-usage.md` 和 `cadence-init/references/rules/mcp-servers.md` 中的 Serena 章节，是初始化时写入用户项目的模板。

**决策点**：是否从 init 模板中彻底删除 Serena？

- 若删除，则新初始化项目不再包含 Serena 规则与 MCP 配置。
- 若保留，则与 "去掉 Serena MCP 使用" 的目标矛盾。

## 六、建议实施步骤

### 阶段 1：准备与范围确认

1. 在 `feat-b-0627` worktree 中完成所有修改。
2. 确认决策者对 5.1、5.2、5.3 的选择。

### 阶段 2：修改 cadence-init 的 pre-check

1. **`cadence-init/skills/pre-check/SKILL.md`**：
   - 删除 description 中的 "initializing serena project"。
   - 删除强制规则第 2 条中关于 serena 的强制完成要求。
   - 删除强制规则第 3 条 "serena 配置必须询问用户"。
   - 删除使用场景中的 "启动需要 serena 的开发任务"。
   - 删除增量运行示例中的 serena。
   - 删除检查流程图中的 `check_serena`、`user_choice`、`validate_serena`、`serena_found` 节点。
   - 删除快速参考表中的 serena 行。
   - 删除 "serena 默认目录" 表格。
   - 删除步骤 3（serena 项目目录确认）全部内容。
   - 更新步骤编号（原步骤 4/5/6 改为 3/4/5）。
   - 更新 "常见错误" 表中 serena 相关行。

2. **`cadence-init/commands/pre-check.md`**：
   - 删除功能列表中的 serena 检查项。
   - 删除 "serena github 地址" 章节。
   - 删除检查流程中的 serena 节点。
   - 删除增量运行中的 serena 描述。
   - 删除输出中的 "serena 项目路径配置"。
   - 删除强制规则中的 serena 要求。

### 阶段 3：修改当前项目的规则与配置引用

1. **`CLAUDE.md`**：
   - 删除 "### 5. Serena 使用规则" 及其引用行。
   - 后续规则编号重新调整。

2. **`AGENTS.md`**：
   - 删除 "### 5. 仓库分析规则" 及其引用行。
   - 后续规则编号重新调整。
   - 同时删除 "禁止直接修改 `.claude/rules/`" 的冲突条款，或明确本次为框架维护者授权修改。

3. **`.claude/rules/serena-usage.md`**：
   - 删除该文件（需决策者授权，因 AGENTS.md 原禁止修改框架规则）。

4. **`.claude/rules/mcp-servers.md`**：
   - 删除 "### Serena MCP" 整节。

5. **`.claude/rules/README.md`**：
   - 从文件列表中删除 `serena-usage.md` 行。

6. **`.gitignore`**：
   - 删除 `.serena/` 行（如后续不再使用 Serena）。

7. **`README.md`**：
   - 删除 "项目初始化" 步骤中 serena 相关描述。
   - 删除 "Skills 库" 中 analyze skill 的 "使用 Serena MCP 分析" 描述。
   - 删除 "最佳实践" 中 "利用 Serena MCP 进行存量分析" 章节。
   - 删除 "技术亮点" 中 "使用 Serena memory 实现跨会话持久化" 描述。

### 阶段 4：梳理并决策 cadence-init 其余 Serena 使用

保留以下文件暂不修改，等待决策者判断是否删除：

- `cadence-init/commands/rule-config.md`
- `cadence-init/commands/mcp-configuration.md`
- `cadence-init/references/rules/serena-usage.md`
- `cadence-init/references/rules/README.md`
- `cadence-init/references/rules/mcp-servers.md`

若决策者决定彻底去 Serena，则继续：

1. `cadence-init/commands/rule-config.md`：
   - 从规则文件复制表格中删除 `serena-usage.md` 行。
   - 从 CLAUDE.md / AGENTS.md 模板中删除 "Serena 使用规则" 摘要。
   - 从增量检测命令中删除 `serena-usage.md`。

2. `cadence-init/commands/mcp-configuration.md`：
   - 删除 MCP 使用规则中的 "Serena MCP" 章节。
   - 从 `.mcp.json` 模板中删除 `serena` server 配置。
   - 从 `.codex/config.toml` 模板中删除 `[mcp_servers.serena]` 配置。
   - 从 `.gitignore` 模板说明中删除 `.serena/`。
   - 更新 pre-check 调用处不再检查 serena。

3. `cadence-init/references/rules/serena-usage.md`：
   - 删除该文件。

4. `cadence-init/references/rules/README.md`：
   - 从文件列表中删除 `serena-usage.md`。

5. `cadence-init/references/rules/mcp-servers.md`：
   - 删除 "### Serena MCP" 整节。

### 阶段 5：验证

1. 使用 `grep -R "serena\|Serena\|\.serena"` 在目标范围内确认无残留。
2. 检查 `cadence-init/skills/pre-check/SKILL.md` 与 `cadence-init/commands/pre-check.md` 的步骤编号与流程图一致性。
3. 检查 `CLAUDE.md` 与 `AGENTS.md` 的规则编号连续性。
4. 提交并推送 `feat-b-0627` 分支。

## 七、风险说明

1. **规则引用断裂**：删除 `.claude/rules/serena-usage.md` 后，`CLAUDE.md` / `AGENTS.md` 中相关引用需同步删除，否则出现死引用。
2. **init 模板与用户项目不一致**：若 `cadence-init` 模板仍保留 Serena，但当前项目已删除，会导致 Cadence-skills 仓库自身规则与 init 输出规则不一致。
3. **cadence-workflow 功能失效风险**：若只删除规则层而不改造 workflow，新用户使用这些 skill 时会因缺少 Serena 而失败。需在文档中明确说明当前版本不再内置 Serena 支持，或保留可选机制。
4. **历史产物**：`cadence/plans/`、`cadence/designs/`、`cadence/analysis/` 中的历史文档提到 Serena 属于记录性质，不建议修改，避免破坏历史上下文。

## 八、建议决策顺序

1. 先确认是否修改 `.claude/rules/` 框架内置规则（推荐：是，否则需求 2 无法彻底完成）。
2. 再确认 cadence-workflow 中 Serena 依赖的处理方式（推荐：本次按选项 A 处理，后续单独改造）。
3. 最后确认是否从 `cadence-init` 模板中彻底删除 Serena（推荐：是，与 pre-check 去 Serena 保持一致）。
