# CodeGraph 集成与 Serena 检查方案设计

> 日期：2026-06-29 | 版本：v1.0 | 状态：待实施

## 1. 背景与目标

### 1.1 背景

当前 `cadence-init` 已完成上一轮环境与规则改造：

1. `/pre-check` 已去掉 Serena，并已增加 `ast-grep` 检查与安装。
2. `/rule-config` 已增加 `code-reading.md` 规则模板，并能同步生成 `CLAUDE.md` 与 `AGENTS.md` 摘要引用。
3. `/mcp-configuration` 已支持将 MCP 配置同步到 Codex 的 `.codex/config.toml`。

本次需求是在现有基础上引入 CodeGraph：

1. `/pre-check` 增加 CodeGraph 安装。
2. `/rule-config` 增加 CodeGraph 的项目化初始化。
3. 同步 Claude Code 与 Codex 的规则、MCP 配置和使用限制。
4. 确认 `cadence-skills init` 中是否仍有 Serena 使用。

### 1.2 目标

1. 在 `/pre-check` 中增加 CodeGraph 检查、安装、验证流程，安装命令固定为：

```bash
npm i -g @colbymchenry/codegraph
```

2. 在 `/rule-config` 中增加 CodeGraph 项目级初始化：

```bash
codegraph install --target=claude,codex --location=local --yes
codegraph init
```

3. 只支持 Claude Code 和 Codex，且只进行当前项目安装，不写入全局 Agent 配置。
4. 增加代码检索规则：
   - 大范围检索、架构理解、调用链、影响面分析优先使用 CodeGraph。
   - 精确检索、单文件结构阅读、符号大纲优先使用 `ast-grep outline`。
   - `ast-grep` 与 CodeGraph 结果冲突时，以 `ast-grep outline` 为准。
5. 去掉当前项目 Serena MCP 使用的检查结论：`cadence-init/` 当前已无 Serena 残留。
6. 明确 `/pre-check` 与 `/rule-config` 必须支持反复增量执行，老项目重新运行时只补齐新增能力，不重复安装、不覆盖已确认配置。

## 2. 参考文档结论

| 文档 | 结论 |
|------|------|
| CodeGraph Quickstart | `npm i -g @colbymchenry/codegraph` 可安装 CLI；`codegraph install` 只接入 Agent，不索引代码；`codegraph init` 创建 `.codegraph/` 并建图 |
| CodeGraph Installation | `codegraph install` 支持 `--target`、`--location`、`--yes`；`--location=local` 表示项目级安装 |
| CodeGraph Configuration | 项目数据存放在项目根目录 `.codegraph/`；可选 `codegraph.json` 用于团队共享配置 |
| CodeGraph MCP Server | MCP 服务命令为 `codegraph serve --mcp`；默认工具为 `codegraph_explore` |
| CodeGraph CLI | `codegraph version` 可用于版本验证；`codegraph explore` 是 `codegraph_explore` MCP 工具的 CLI 等价入口 |

参考链接：

- <https://colbymchenry.github.io/codegraph/getting-started/quickstart/>
- <https://colbymchenry.github.io/codegraph/getting-started/installation/>
- <https://colbymchenry.github.io/codegraph/getting-started/configuration/>
- <https://colbymchenry.github.io/codegraph/reference/mcp-server/>
- <https://colbymchenry.github.io/codegraph/reference/cli/>

## 3. 当前项目进度

### 3.1 Worktree 状态

| 项 | 状态 |
|----|------|
| 工作目录 | `.worktrees/feat-b-0629` |
| 分支 | `feat-b-0629` |
| 远端 | 已推送并跟踪 `origin/feat-b-0629` |
| OpenSpec | 仅存在 `openspec/config.yaml`，无 `openspec/changes` 目录 |
| 当前改动 | 写入本方案前无未提交改动 |

### 3.2 已完成基础

| 模块 | 当前状态 |
|------|----------|
| `cadence-init/skills/pre-check/SKILL.md` | 已包含 `npx`、`uvx`、`playwright-cli`、`ast-grep` 四项基础检查 |
| `cadence-init/commands/pre-check.md` | 已包含 `ast-grep` 安装章节 |
| `cadence-init/commands/rule-config.md` | 已包含 `code-reading.md` 配置、`CLAUDE.md` 与 `AGENTS.md` 同步 |
| `cadence-init/references/rules/code-reading.md` | 已存在 `ast-grep outline` 代码阅读规则 |
| `cadence-init/commands/mcp-configuration.md` | 已支持 Codex `.codex/config.toml` 同步 |
| `cadence-init/references/rules/mcp-servers.md` | 已无 Serena MCP 章节 |

### 3.3 Serena 检查结论

在 `cadence-init/` 范围内执行以下检索：

```bash
rg -n "serena|Serena|\\.serena|mcp__serena" cadence-init
```

结果为空。

结论：`cadence-skills init` 当前没有 Serena 使用残留。

仍存在 Serena 的范围：

| 范围 | 状态 | 本次处理建议 |
|------|------|--------------|
| `cadence-workflow/skills/` | 多个 workflow skill 仍依赖 Serena memory 或 Serena MCP 文案 | 不纳入本次 CodeGraph 初始化改造 |
| `cadence-workflow/commands/` | 部分 command 文档仍提及 Serena | 不纳入本次 CodeGraph 初始化改造 |
| `readmes/skills/` | 多篇说明文档仍提及 Serena | 后续按 workflow 去 Serena 独立处理 |
| `cadence/plans/`、`cadence/docs/`、`cadence/designs/`、`cadence/analysis/` | 历史文档提及 Serena | 保留历史记录，不修改 |

## 4. 设计决策

| 决策项 | 选择 | 理由 |
|--------|------|------|
| 安装方式 | `npm i -g @colbymchenry/codegraph` | 用户明确指定，且官方支持 npm 全局安装 |
| 版本检查命令 | `codegraph version` | 官方 CLI 文档列出该命令，并支持 `--version` |
| Agent 接入方式 | `codegraph install --target=claude,codex --location=local --yes` | 精确限定 Claude Code 与 Codex，且只写当前项目配置 |
| 项目初始化方式 | `codegraph init` | 官方定义为创建 `.codegraph/` 并构建完整图 |
| MCP 配置主路径 | 优先使用 `codegraph install` 自动写入 | 避免手写配置与官方安装器行为不一致 |
| MCP 配置兜底 | 在 `mcp-configuration.md` 中提供手动配置片段 | 便于安装器失败或需要人工修复时处理 |
| `.codegraph/` | 加入 `.gitignore` | 该目录保存本地 SQLite 索引，不应提交 |
| `codegraph.json` | 不加入 `.gitignore` | 这是可共享的项目配置文件，应允许团队提交 |
| 与 `ast-grep` 的关系 | 大范围用 CodeGraph，精确结构用 `ast-grep outline` | 两者职责不同，冲突时以结构化大纲工具为准 |
| 增量执行模型 | `/pre-check` 按工具粒度补齐；`/rule-config` 按规则/配置/初始化状态补齐 | 支持已初始化项目升级到新版 Cadence，例如只补 CodeGraph |

## 5. 改动范围

| 操作 | 文件 |
|------|------|
| 修改 | `cadence-init/skills/pre-check/SKILL.md` |
| 修改 | `cadence-init/commands/pre-check.md` |
| 修改 | `cadence-init/commands/rule-config.md` |
| 修改 | `cadence-init/commands/mcp-configuration.md` |
| 修改 | `cadence-init/references/rules/code-reading.md` |
| 修改 | `cadence-init/references/rules/mcp-servers.md` |
| 修改 | `.claude/rules/code-reading.md` |
| 修改 | `.claude/rules/mcp-servers.md` |
| 修改 | `CLAUDE.md` |
| 修改 | `AGENTS.md` |

不纳入本次范围：

1. 不重构 `cadence-workflow/skills/` 中的 Serena memory 体系。
2. 不批量修改 `readmes/skills/` 的 Serena 历史说明。
3. 不修改历史方案、计划、分析文档中的 Serena 记录。

## 6. 详细设计

### 6.1 `/pre-check` 增加 CodeGraph

#### 6.1.1 检查流程调整

当前基础检查为：

```text
检查 npx → 检查 uvx → 检查 playwright-cli → 检查 ast-grep → API Key 提醒（可选） → 完成
```

调整为：

```text
检查 npx → 检查 uvx → 检查 playwright-cli → 检查 ast-grep → 检查 codegraph → API Key 提醒（可选） → 完成
```

#### 6.1.2 命令定义

| 阶段 | 命令 | 成功标志 | 失败处理 |
|------|------|----------|----------|
| 检查 | `codegraph version` | 输出版本号 | 执行安装 |
| 安装 | `npm i -g @colbymchenry/codegraph` | npm 命令成功退出 | 提示用户手动执行安装命令 |
| 验证 | `codegraph version` | 输出版本号 | 报告 CodeGraph 安装失败 |

#### 6.1.3 文档调整点

`cadence-init/skills/pre-check/SKILL.md`：

1. 强制规则从“四个基础检查”改为“五个基础检查”。
2. 流程图在 `check_ast_grep` 后增加 `check_codegraph`。
3. 快速参考表增加 CodeGraph 行。
4. 实施步骤增加“步骤 5：检查 CodeGraph”，API Key 顺延为步骤 6。
5. 常见错误表增加 CodeGraph 安装失败处理。
6. 增量运行章节增加“框架新增 CodeGraph 后，老项目重新运行 `/pre-check` 只补齐 CodeGraph”。

`cadence-init/commands/pre-check.md`：

1. 功能列表新增 CodeGraph。
2. 新增“CodeGraph 安装”章节。
3. 检查流程更新为包含 CodeGraph。
4. 强制规则新增 CodeGraph 安装失败手动命令。

#### 6.1.4 增量行为定义

`/pre-check` 不是一次性初始化命令，必须允许用户在已执行过 `/pre-check` 的项目中再次运行。

典型场景：

```text
老项目已完成 npx / uvx / playwright-cli / ast-grep 检查
        ↓
Cadence 新版本增加 CodeGraph
        ↓
用户重新运行 /pre-check
        ↓
只检查并安装缺失的 CodeGraph，其他已安装工具直接跳过
```

执行规则：

| 场景 | 行为 |
|------|------|
| 工具已安装 | 输出当前版本或已安装状态，跳过安装 |
| 工具未安装 | 执行对应安装命令，安装后验证 |
| 单个工具安装失败 | 报告该工具失败并给出手动命令，不重装其他已就绪工具 |
| 重复运行 | 每个工具独立检查，结果不依赖是否首次运行 |
| 新增工具上线 | 老项目重新运行 `/pre-check` 时只补齐新增工具 |

对 CodeGraph 的增量要求：

1. 如果 `codegraph version` 成功，报告 CodeGraph 已安装并跳过。
2. 如果 `codegraph version` 失败，执行 `npm i -g @colbymchenry/codegraph`。
3. 安装完成后只验证 CodeGraph，不重新安装其他工具。

### 6.2 `/rule-config` 增加 CodeGraph 初始化

#### 6.2.1 新增步骤位置

建议在现有“代码阅读规则配置”之后、“Playwright Skills 规则配置”之前增加 CodeGraph 初始化步骤。

调整后的后半段流程：

```text
7. cadence gitignore 决策
8. 代码阅读规则配置
9. CodeGraph 项目初始化
10. Playwright Skills 规则配置
```

#### 6.2.2 启用条件

| 项目类型 | 默认行为 |
|----------|----------|
| Coding 项目 | 默认建议启用 CodeGraph |
| 非 Coding 项目 | 默认跳过，仅提示“非 Coding 项目默认跳过 CodeGraph 初始化” |
| 用户手动要求 | 即使未检测到源代码，也可启用 |

#### 6.2.3 初始化命令

在用户确认启用后，于项目根目录执行：

```bash
codegraph install --target=claude,codex --location=local --yes
codegraph init
```

执行后验证：

```bash
test -d .codegraph && codegraph status
```

#### 6.2.4 已存在状态处理

| 场景 | 行为 |
|------|------|
| `.codegraph/` 不存在 | 执行完整初始化 |
| `.codegraph/` 已存在 | 运行 `codegraph status`，报告已初始化 |
| Agent 配置已存在 | 不覆盖用户配置，报告已有配置并保留 |
| `codegraph install` 失败 | 提供手动配置兜底方案 |
| `codegraph init` 失败 | 提示用户确认项目是否包含 CodeGraph 支持的语言或是否需排除大型目录 |

#### 6.2.5 `.gitignore` 规则

如果启用 CodeGraph，应确保 `.gitignore` 包含：

```gitignore
# CodeGraph 本地索引
.codegraph/
```

不应忽略：

```gitignore
codegraph.json
```

原因：`codegraph.json` 用于排除已提交的大型目录、自定义扩展名、嵌套仓库等配置，属于团队可共享配置。

#### 6.2.6 增量行为定义

`/rule-config` 也必须支持在已初始化项目中反复运行，用于补齐新版 Cadence 新增的规则、配置和项目初始化步骤。

典型场景：

```text
老项目已经生成 .claude/rules、CLAUDE.md、AGENTS.md
        ↓
Cadence 新版本增加 CodeGraph 规则与初始化
        ↓
用户重新运行 /rule-config
        ↓
只补 CodeGraph 相关规则、摘要、.gitignore 和项目初始化，不覆盖已有规则全文
```

执行规则：

| 检查对象 | 已存在时 | 缺失时 |
|----------|----------|--------|
| `.claude/rules/code-reading.md` | 不自动覆盖，检查是否缺少 CodeGraph 段落并询问是否更新 | 从模板创建 |
| `.claude/rules/mcp-servers.md` | 不自动覆盖，检查是否缺少 CodeGraph MCP 章节并询问是否追加 | 从模板创建 |
| `CLAUDE.md` / `AGENTS.md` 摘要 | 已有 CodeGraph/代码阅读摘要则跳过 | 追加或更新对应摘要 |
| `.codegraph/` | 视为已初始化，运行 `codegraph status` 报告状态 | 询问用户后执行 `codegraph init` |
| Claude/Codex MCP 配置 | 已有 CodeGraph server 时跳过 | 通过 `codegraph install --target=claude,codex --location=local --yes` 补齐 |
| `.gitignore` | 已含 `.codegraph/` 时跳过 | 追加 `.codegraph/` |

覆盖原则：

1. 不直接覆盖用户已经存在的规则文件。
2. 如果模板内容发生变化，先展示差异或说明变更范围，再询问是否更新。
3. 可自动追加明显缺失且低风险的条目，例如 `.gitignore` 中的 `.codegraph/`。
4. 对 `CLAUDE.md` 和 `AGENTS.md` 只做摘要级补齐，避免重写用户手工维护内容。

### 6.3 MCP 配置同步

#### 6.3.1 主路径

`/rule-config` 中通过以下命令完成 Claude Code 和 Codex 的项目级接入：

```bash
codegraph install --target=claude,codex --location=local --yes
```

该命令会按官方安装器逻辑写入对应 Agent 配置与指令片段。

#### 6.3.2 兜底手动配置

在 `cadence-init/commands/mcp-configuration.md` 中补充 CodeGraph 手动配置说明，供安装器失败或用户需要人工修复时使用。

Claude Code `.mcp.json`：

```json
{
  "mcpServers": {
    "codegraph": {
      "type": "stdio",
      "command": "codegraph",
      "args": ["serve", "--mcp"]
    }
  }
}
```

Codex `.codex/config.toml`：

```toml
[mcp_servers.codegraph]
command = "codegraph"
args = ["serve", "--mcp"]
```

#### 6.3.3 Codex 同步规则

1. CodeGraph 是 stdio MCP，可同步到 Codex。
2. 同步时不需要 HTTP 特殊处理。
3. 如果 `.codex/config.toml` 已有 `[mcp_servers.codegraph]`，不自动覆盖，先询问用户。
4. `.codex/` 仍保持 `.gitignore`，因为该目录可能包含本地配置和 API Key 占位符。

### 6.4 规则文件同步

#### 6.4.1 `code-reading.md` 新规则

在 `cadence-init/references/rules/code-reading.md` 与 `.claude/rules/code-reading.md` 中增加 CodeGraph 与 `ast-grep` 的职责边界：

```markdown
### CodeGraph 与 ast-grep 分工

- **大范围检索优先使用 CodeGraph**：架构理解、调用链分析、影响面分析、跨文件符号关系、功能流向追踪等场景，优先使用 CodeGraph 或 `codegraph explore`。
- **精确检索优先使用 `ast-grep outline`**：单文件结构阅读、符号定义定位、导入导出查看、类/函数成员大纲、局部实现精读前的结构化扫描，优先使用 `ast-grep outline`。
- **冲突处理**：如果 CodeGraph 与 `ast-grep outline` 结果冲突，以 `ast-grep outline` 的结构化大纲结果为准，再通过定向文件阅读确认。
```

#### 6.4.2 `mcp-servers.md` 新规则

在 `cadence-init/references/rules/mcp-servers.md` 与 `.claude/rules/mcp-servers.md` 中增加 CodeGraph MCP 章节：

````markdown
### CodeGraph MCP

**用途**：基于项目代码图进行大范围代码检索、架构理解、调用链分析和影响面分析。

**触发场景**：
- 需要理解某个功能跨文件如何工作
- 需要分析调用链、依赖关系或影响面
- 需要进行大范围代码检索
- 需要回答“某功能从入口到落点如何流转”

**使用规则**：
1. 项目必须先执行 `codegraph init`，存在 `.codegraph/` 后 CodeGraph MCP 才提供工具。
2. 大范围检索优先使用 CodeGraph。
3. 精确结构阅读优先使用 `ast-grep outline`。
4. `ast-grep` 与 CodeGraph 结果冲突时，以 `ast-grep` 为准。

**手动服务命令**：
```bash
codegraph serve --mcp
```
````

### 6.5 `CLAUDE.md` 与 `AGENTS.md` 同步

在现有“代码阅读规则”摘要中增加 CodeGraph 表述，避免新增独立规则编号造成编号 churn。

建议改为：

```markdown
### 8. 代码阅读规则
- **大范围检索使用 CodeGraph，精确结构阅读优先使用 `ast-grep outline`** → 详见 `.claude/rules/code-reading.md`
```

`AGENTS.md` 同步使用同样表述。

## 7. 增量运行策略（核心要求）

`/pre-check` 与 `/rule-config` 必须按增量命令设计，而不是仅面向首次初始化。

核心原则：

1. **可重复执行**：用户可以在任意已初始化项目中再次运行命令。
2. **只补缺失项**：新版 Cadence 新增能力后，老项目重新运行命令只补齐新增内容。
3. **不破坏已有配置**：不重复安装已就绪工具，不覆盖用户已确认或手工修改的规则。
4. **每项独立判断**：某一项失败不应导致其他已就绪项被重复处理。
5. **执行前报告变更范围**：尤其是 `/rule-config`，写入前应告知本次会新增或更新哪些文件。

### 7.1 `/pre-check`

`/pre-check` 的增量粒度是“工具”。每次运行都逐项检查工具状态。

| 场景 | 行为 |
|------|------|
| 老项目已执行过 `/pre-check`，新版新增 CodeGraph | 重新运行后只补装 CodeGraph |
| npx / uvx / playwright-cli / ast-grep 已安装 | 报告已安装并跳过 |
| CodeGraph 已安装 | 报告版本并跳过安装 |
| CodeGraph 未安装 | 执行 `npm i -g @colbymchenry/codegraph` |
| 安装后验证失败 | 报告失败并给出手动安装命令 |
| 重复运行多次 | 输出检查结果，不重复安装已存在工具 |

用户体验示例：

```text
✓ npx 已安装，跳过
✓ uvx 已安装，跳过
✓ playwright-cli 已安装，跳过
✓ ast-grep 已安装，跳过
正在安装 CodeGraph...
✓ CodeGraph 安装成功
```

### 7.2 `/rule-config`

`/rule-config` 的增量粒度是“规则文件、入口摘要、MCP 配置、项目初始化状态”。

| 场景 | 行为 |
|------|------|
| 老项目已执行过 `/rule-config`，新版新增 CodeGraph | 重新运行后只补 CodeGraph 相关规则、摘要、MCP 配置和 `.codegraph/` 初始化 |
| 基础规则文件已存在 | 不自动覆盖，仅检查是否需要追加 CodeGraph 段落 |
| `.codegraph/` 已存在 | 报告已初始化，不重复 `codegraph init` |
| `.codegraph/` 不存在 | 询问是否初始化 |
| CodeGraph 规则文件已存在 | 检查摘要是否缺失，不自动覆盖规则全文 |
| `CLAUDE.md` / `AGENTS.md` 已有 CodeGraph 标记片段 | 不重复写入 |
| Codex/Claude 已有 CodeGraph MCP server | 跳过，不重复写入 |
| `.gitignore` 已包含 `.codegraph/` | 跳过 |

用户体验示例：

```text
检测到项目已存在 .claude/rules 与 AGENTS.md。
本次仅发现缺失项：
- CodeGraph 代码阅读规则段落
- CodeGraph MCP 规则段落
- .codegraph/ 本地索引目录
- .gitignore 中的 .codegraph/

确认后只写入上述缺失项，不覆盖已有规则文件。
```

## 8. 实施步骤

1. 修改 `/pre-check` 文档：
   - 更新 `cadence-init/skills/pre-check/SKILL.md`
   - 更新 `cadence-init/commands/pre-check.md`

2. 修改 `/rule-config` 文档：
   - 增加 CodeGraph 项目初始化步骤
   - 更新检查清单编号
   - 更新增量运行说明
   - 更新 `.gitignore` 处理规则

3. 修改 MCP 配置文档：
   - 在 `cadence-init/commands/mcp-configuration.md` 中增加 CodeGraph 手动配置兜底
   - 确认 Codex 同步配置包含 `[mcp_servers.codegraph]`

4. 修改规则模板与当前项目规则：
   - 更新 `cadence-init/references/rules/code-reading.md`
   - 更新 `cadence-init/references/rules/mcp-servers.md`
   - 更新 `.claude/rules/code-reading.md`
   - 更新 `.claude/rules/mcp-servers.md`

5. 同步入口文件：
   - 更新 `CLAUDE.md` 的代码阅读规则摘要
   - 更新 `AGENTS.md` 的代码阅读规则摘要

6. 验证：
   - 检查 Markdown 格式
   - 检查规则编号一致性
   - 检查 `cadence-init/` 中 Serena 仍无残留
   - 检查 CodeGraph 关键命令均出现

## 9. 验证清单

实施后执行：

```bash
rg -n "codegraph|CodeGraph|\\.codegraph|@colbymchenry/codegraph" cadence-init .claude CLAUDE.md AGENTS.md
rg -n "serena|Serena|\\.serena|mcp__serena" cadence-init
rg -n "大范围检索|精确检索|ast-grep outline" cadence-init/references/rules .claude/rules CLAUDE.md AGENTS.md
```

人工检查：

1. `/pre-check` 基础检查数量是否统一为五项。
2. `/rule-config` 步骤编号是否连续。
3. CodeGraph 初始化是否明确限定 `--target=claude,codex --location=local`。
4. `.codegraph/` 是否被忽略，`codegraph.json` 是否未被忽略。
5. `ast-grep` 与 CodeGraph 冲突处理是否明确。

## 10. 风险与处理

| 风险 | 影响 | 处理 |
|------|------|------|
| `codegraph install` 修改 `CLAUDE.md` / `AGENTS.md` 的 marker 片段 | 可能与 Cadence 摘要规则重复 | 文档中要求检测已有片段，不重复写入 |
| CodeGraph 建图时间较长 | 大型项目初始化耗时 | 提示用户可先配置 `codegraph.json` 排除大型已提交目录 |
| `.codegraph/` 被误提交 | 本地 SQLite 索引进入版本库 | `/rule-config` 初始化后写入 `.gitignore` |
| Codex 配置重复 | `.codex/config.toml` 中出现重复 server | 写入前检查 `[mcp_servers.codegraph]` |
| CodeGraph 与 `ast-grep` 结论不一致 | Agent 判断不稳定 | 明确以 `ast-grep outline` 为准，再定向精读确认 |

## 11. 待确认事项

1. 本次实施是否严格限定在 `cadence-init`、规则模板、当前项目入口规则，不处理 `cadence-workflow/` 与 `readmes/skills/` 的 Serena 文案。
2. 是否允许 `/rule-config` 直接执行 `codegraph init` 完成建图，还是只写入命令说明并由用户手动执行。
3. 是否需要在 `mcp-configuration.md` 的基础 MCP 配置中默认包含 CodeGraph，还是仅作为 `/rule-config` 项目初始化后的兜底说明。

## 12. 推荐结论

推荐按以下策略实施：

1. `/pre-check` 负责安装 CodeGraph CLI。
2. `/rule-config` 负责项目级 `codegraph install` 与 `codegraph init`。
3. `/mcp-configuration` 只补充手动兜底配置，不把 CodeGraph 纳入原有基础 MCP 模板的必选项。
4. 代码阅读规则统一表达为“大范围检索用 CodeGraph，精确结构阅读用 `ast-grep outline`，冲突时以 `ast-grep` 为准”。
5. 本次不处理 `cadence-workflow/` 和 `readmes/skills/` 中的 Serena 依赖，避免扩大为工作流持久化机制重构。
