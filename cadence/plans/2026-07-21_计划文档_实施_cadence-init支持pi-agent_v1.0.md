# cadence-init 支持 pi coding agent 实施 Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让 cadence-init 的 pre-check / mcp-configuration / rule-config 三个 Skill 一等支持 pi coding agent（Superpowers 软链、OpenSpec 工具、MCP 接入、路由规则行为约定）。

**Architecture:** 纯 Markdown 文档变更。pre-check 增加 `~/.pi/agent/skills` 第四软链目标、`--tools` 追加 pi、新增 pi-mcp-adapter 条件检查；mcp-configuration 说明 pi 经 pi-mcp-adapter 直读 `.mcp.json`；rule-config 规则模板补 pi 客户端行为约定。

**Tech Stack:** Markdown Skill 文档、OpenSpec change `add-pi-agent-support`、bash 验证命令。

**关联契约：** OpenSpec change `openspec/changes/add-pi-agent-support/`（proposal/design/specs/tasks 已获批）。

## Global Constraints

- 产品实现改动范围仅限 `cadence-init/`；允许同步维护本 Change 的 `openspec/changes/add-pi-agent-support/` 契约、tasks 与本 Plan。禁止触碰 `cadence-workflow/`、根 `AGENTS.md` / `CLAUDE.md` 与根目录 `install-offline.sh/.bat`。
- 不新增任何脚本/代码文件，仅修改 Markdown。
- 软链目标目录为 `~/.pi/agent/skills`（不是 `~/.pi/skills`）。
- OpenSpec 新项目初始化命令为 `openspec init --tools claude,codex,pi`（需 openspec ≥ 1.4.1）；已有配置但缺少 pi 产物时先执行 `openspec init --tools pi`，再执行 `openspec update`；已有 pi 产物时直接执行 `openspec update`。
- pi MCP 方案：全局 `pi install npm:pi-mcp-adapter`，直读项目 `.mcp.json`；不引入 `.pi/mcp.json`，不在 `.gitignore` 新增条目。
- 每个 Task 结束后单独 commit，提交信息风格沿用仓库（如 `docs(cadence-init): ...`），使用中文描述。
- 编辑使用精确字符串替换；`old` 文本必须在原文件中唯一。

---

### Task 1: pre-check — Superpowers 软链增加 pi 目标（工作包 1）

**Files:**
- Modify: `cadence-init/skills/pre-check/SKILL.md`

**Interfaces:**
- Consumes: 无
- Produces: 四层软链目录约定（`~/.agents/skills`、`~/.codex/skills/skills`、`~/.claude/skills`、`~/.pi/agent/skills`），供 Task 3 新增步骤引用同一份目录约定表

- [ ] **Step 1: 运行失败验证（确认现状不含 pi）**

```bash
cd cadence-init/skills/pre-check
grep -c '\.pi/agent/skills' SKILL.md
```

Expected: 输出 `0`（当前无任何 pi 软链描述）

- [ ] **Step 2: 更新 no-interrupt 完成条件与快速参考表（三层→四层）**

精确替换 1：

```
old: | Superpowers | 来源目录和三层 Skills 软链验证成功 | 立即终止 |
new: | Superpowers | 来源目录和四层 Skills 软链验证成功 | 立即终止 |
```

精确替换 2：

```
old: | **6. Superpowers** | `~/.agents/superpowers/skills` | 三层软链同步完成 | 在线 clone；失败时提示离线复制 |
new: | **6. Superpowers** | `~/.agents/superpowers/skills` | 四层软链同步完成 | 在线 clone；失败时提示离线复制 |
```

精确替换 3（no-interrupt Superpowers 处理第 1 条）：

```
old: 1. 先验证 `~/.agents/superpowers/skills`；有效时按现有同步逻辑完成三层软链。
new: 1. 先验证 `~/.agents/superpowers/skills`；有效时按现有同步逻辑完成四层软链。
```

- [ ] **Step 3: 更新增量运行典型场景**

精确替换：

```
old: - 框架新增 Superpowers 后，老项目重新运行 `/pre-check`，只会更新或识别 `~/.agents/superpowers`，补齐 `~/.agents/skills`、`~/.codex/skills/skills`、`~/.claude/skills` 的软链。
new: - 框架新增 Superpowers 后，老项目重新运行 `/pre-check`，只会更新或识别 `~/.agents/superpowers`，补齐 `~/.agents/skills`、`~/.codex/skills/skills`、`~/.claude/skills`、`~/.pi/agent/skills` 的软链。
```

- [ ] **Step 4: 目录约定表增加 pi 行**

精确替换：

```
old: | Codex 目标目录 | `~/.codex/skills/skills` |
| Claude Code 目标目录 | `~/.claude/skills` |
new: | Codex 目标目录 | `~/.codex/skills/skills` |
| Claude Code 目标目录 | `~/.claude/skills` |
| pi 目标目录 | `~/.pi/agent/skills` |
```

- [ ] **Step 5: 软链同步逻辑增加第 5 步并重编号**

精确替换整个有序列表：

```
old:
1. 确保 `~/.agents/skills`、`~/.codex/skills/skills`、`~/.claude/skills` 存在。
2. 将 `~/.agents/superpowers/skills/*` 逐项软链到 `~/.agents/skills`。
3. 将 `~/.agents/skills/*` 中指向 Superpowers 的软链逐项软链到 `~/.codex/skills/skills`。
4. 将 `~/.agents/skills/*` 中指向 Superpowers 的软链逐项软链到 `~/.claude/skills`。
5. 已存在正确软链：跳过。
6. 已存在旧软链但指向不同 Superpowers 来源：更新软链。
7. 已存在同名非软链文件或目录：跳过并警告，不覆盖。
8. 清理失效软链时，只清理指向 `~/.agents/superpowers/skills` 或 `~/.agents/skills` 中 Superpowers 条目的失效链接，不能删除 OpenSpec、Cadence 或用户自定义 skills。

new:
1. 确保 `~/.agents/skills`、`~/.codex/skills/skills`、`~/.claude/skills`、`~/.pi/agent/skills` 存在。
2. 将 `~/.agents/superpowers/skills/*` 逐项软链到 `~/.agents/skills`。
3. 将 `~/.agents/skills/*` 中指向 Superpowers 的软链逐项软链到 `~/.codex/skills/skills`。
4. 将 `~/.agents/skills/*` 中指向 Superpowers 的软链逐项软链到 `~/.claude/skills`。
5. 将 `~/.agents/skills/*` 中指向 Superpowers 的软链逐项软链到 `~/.pi/agent/skills`。
6. 已存在正确软链：跳过。
7. 已存在旧软链但指向不同 Superpowers 来源：更新软链。
8. 已存在同名非软链文件或目录：跳过并警告，不覆盖。
9. 清理失效软链时，只清理指向 `~/.agents/superpowers/skills` 或 `~/.agents/skills` 中 Superpowers 条目的失效链接，不能删除 OpenSpec、Cadence 或用户自定义 skills。

> 说明：pi 原生也会读取 `~/.agents/skills`，此处显式软链到 `~/.pi/agent/skills` 是为了与 Claude Code/Codex 保持一致的显式布局，便于统一检查、更新与失效清理。
```

- [ ] **Step 6: 验证命令增加 pi 目录**

精确替换：

```
old:
test -d "$HOME/.agents/superpowers/skills"
test -d "$HOME/.agents/skills"
test -d "$HOME/.codex/skills/skills"
test -d "$HOME/.claude/skills"

new:
test -d "$HOME/.agents/superpowers/skills"
test -d "$HOME/.agents/skills"
test -d "$HOME/.codex/skills/skills"
test -d "$HOME/.claude/skills"
test -d "$HOME/.pi/agent/skills"
```

- [ ] **Step 7: 验证修改生效**

```bash
cd cadence-init/skills/pre-check
grep -c '\.pi/agent/skills' SKILL.md   # 期望 >= 5
grep -c '四层' SKILL.md                # 期望 = 2
grep -n '三层' SKILL.md                # 期望无输出
```

Expected: 前两条计数达标，第三条无输出。

- [ ] **Step 8: Commit**

```bash
git add cadence-init/skills/pre-check/SKILL.md
git commit -m "docs(cadence-init): pre-check Superpowers 软链增加 pi 目标目录"
```

---

### Task 2: pre-check — OpenSpec 增加 pi（工作包 2）

**Files:**
- Modify: `cadence-init/skills/pre-check/SKILL.md`

**Interfaces:**
- Consumes: 无
- Produces: OpenSpec 三客户端初始化命令与验证命令

- [ ] **Step 1: 运行失败验证**

```bash
cd cadence-init/skills/pre-check
grep -c 'claude,codex,pi' SKILL.md   # 期望 0
```

- [ ] **Step 2: 初始化命令块更新**

精确替换：

```
old:
# 当前项目尚未存在 openspec/config.yaml 时
openspec init --tools claude,codex

new:
# 当前项目尚未存在 openspec/config.yaml 时
openspec init --tools claude,codex,pi
```

- [ ] **Step 3: 增量要求更新（命令、产物结构、版本要求）**

精确替换：

```
old:
- 如果 `openspec/config.yaml` 不存在，执行 `openspec init --tools claude,codex`。
- 如果 `openspec/config.yaml` 已存在，不重新初始化，执行 `openspec update` 补齐或刷新指令文件。
- OpenSpec 生成的 Claude Code 和 Codex 目录结构不同，不能混用：
  - Claude Code：`.claude/commands/opsx/`、`.claude/skills/openspec-*`
  - Codex：`.codex/skills/openspec-*`

new:
- 如果 `openspec/config.yaml` 不存在，执行 `openspec init --tools claude,codex,pi`。
- 如果 `openspec/config.yaml` 已存在且缺少 `.pi` 产物，先执行 `openspec init --tools pi`；确认 `.pi/skills` 恰有 5 个 `openspec-*` 目录且 `.pi/prompts` 恰有 5 个 `opsx-*.md` 文件后，再执行 `openspec update`。
- 如果 `openspec/config.yaml` 已存在且 pi 产物已存在，直接执行 `openspec update`。
- `openspec update` 只刷新已初始化的工具产物，不能单独为未选择过 pi 的老项目新增 `.pi` 产物。
- OpenSpec 生成的 Claude Code、Codex 和 pi 目录结构不同，不能混用：
  - Claude Code：`.claude/commands/opsx/`、`.claude/skills/openspec-*`
  - Codex：`.codex/skills/openspec-*`
  - pi：`.pi/prompts/opsx-*`、`.pi/skills/openspec-*`
- `--tools pi` 需要 OpenSpec CLI >= 1.4.1；`/pre-check` 的安装命令始终安装 `@fission-ai/openspec@latest`，版本不足时先升级 CLI。
```

- [ ] **Step 4: 验证命令增加 pi 产物**

精确替换：

```
old:
test -f openspec/config.yaml
test -f .codex/skills/openspec-propose/SKILL.md
test -f .claude/commands/opsx/propose.md -o -f .claude/skills/openspec-propose/SKILL.md

new:
test -f openspec/config.yaml
test -f .codex/skills/openspec-propose/SKILL.md
test -f .claude/commands/opsx/propose.md -o -f .claude/skills/openspec-propose/SKILL.md
test -f .pi/skills/openspec-propose/SKILL.md
```

- [ ] **Step 5: 增量运行典型场景更新**

精确替换：

```
old: - 框架新增 OpenSpec 后，老项目重新运行 `/pre-check`，只会安装 CLI、执行 `openspec init` 或 `openspec update`，补齐 `.codex` / `.claude` / `.pi` 指令文件。
new: - 框架新增 OpenSpec pi 支持后，老项目重新运行 `/pre-check`：若缺少 `.pi` 产物，先执行 `openspec init --tools pi`，再执行 `openspec update`；若 pi 产物已存在，则直接执行 `openspec update`。新项目仍执行 `openspec init --tools claude,codex,pi`。
```

- [ ] **Step 6: 验证修改生效**

```bash
cd cadence-init/skills/pre-check
grep -c 'claude,codex,pi' SKILL.md              # 期望 = 2
grep -c '.pi/skills/openspec-propose' SKILL.md  # 期望 = 1
grep -n 'claude,codex$' SKILL.md                # 期望无输出（无残留旧命令）
```

- [ ] **Step 7: Commit**

```bash
git add cadence-init/skills/pre-check/SKILL.md
git commit -m "docs(cadence-init): pre-check OpenSpec 初始化增加 pi 工具"
```

---

### Task 3: pre-check — 新增 pi MCP Adapter 条件检查（工作包 3）

**Files:**
- Modify: `cadence-init/skills/pre-check/SKILL.md`

**Interfaces:**
- Consumes: Task 1 的目录约定表位置（新增步骤位于步骤 6 之后）
- Produces: "步骤 7：检查 pi MCP Adapter" 章节，供 mcp-configuration（Task 4）引用

- [ ] **Step 1: 运行失败验证**

```bash
cd cadence-init/skills/pre-check
grep -c 'pi-mcp-adapter' SKILL.md   # 期望 0
```

- [ ] **Step 2: 在步骤 6 之后、API Key 提醒之前插入新章节**

锚点：`### 默认步骤：API Key 占位配置提醒`（在该行之前插入以下内容，保留原锚点行不变）：

````markdown
### 步骤 7：检查 pi MCP Adapter（条件检查）

> 条件项：仅在检测到 pi 环境时执行；未检测到 pi 环境时跳过且不算失败（语义同 Playwright 的条件跳过，不违反 no-interrupt 完成门槛）。

**触发条件（满足任一即执行检查）**：

```bash
pi --version
test -d "$HOME/.pi/agent"
```

**就绪判定（满足任一即视为已安装）**：

```bash
test -d "$HOME/.pi/agent/npm/node_modules/pi-mcp-adapter"
pi list | grep pi-mcp-adapter
```

**安装命令**：

```bash
pi install npm:pi-mcp-adapter
```

**行为（中文输出）**：
- 未检测到 pi 环境：报告 "✓ 未检测到 pi 环境，跳过 pi MCP Adapter 检查"，继续后续步骤
- 已安装：报告 "✓ pi-mcp-adapter 已安装"
- 未安装：报告 "正在安装 pi-mcp-adapter..."，执行安装命令，完成后按就绪判定验证并报告 "✓ pi-mcp-adapter 安装成功"
- 安装失败：普通模式报告失败原因与手动命令 `pi install npm:pi-mcp-adapter`；no-interrupt 模式立即终止并给出恢复建议，不得宣称初始化成功

**说明**：

- **用途**：pi 官方不提供原生 MCP 支持。pi-mcp-adapter 是第三方 pi 扩展，安装后直接读取项目 `.mcp.json`（含 HTTP 类型 server），使 pi 获得与 `.mcp.json` 一致的 MCP 能力。
- **安装位置**：使用 `pi install npm:pi-mcp-adapter` 全局安装并写入 `~/.pi/agent/settings.json`；实际包目录为 `~/.pi/agent/npm/node_modules/pi-mcp-adapter`，可执行文件软链为 `~/.pi/agent/npm/node_modules/.bin/pi-mcp-adapter`；一次安装对所有项目生效。
- **增量要求**：已安装时跳过；pi 环境不存在时不安装、不报错、不影响其他检查结果。
- **版本策略**：不锁定版本，与框架对 npx/uvx 等工具的"安装稳定版本"策略一致；如该包不可用，报告并提示用户可自行选择其他 pi MCP 扩展。

````

- [ ] **Step 3: no-interrupt 强制完成策略表增加条件行**

精确替换：

```
old: | Superpowers | 来源目录和四层 Skills 软链验证成功 | 立即终止 |
| Playwright | 仅用户明确要求时安装和验证 | 未要求时允许跳过 |
new: | Superpowers | 来源目录和四层 Skills 软链验证成功 | 立即终止 |
| pi MCP Adapter | 条件项：检测到 pi 环境时 adapter 安装并验证成功；未检测到 pi 环境时跳过 | pi 存在但安装失败：立即终止 |
| Playwright | 仅用户明确要求时安装和验证 | 未要求时允许跳过 |
```

- [ ] **Step 4: 快速参考表增加行**

精确替换：

```
old: | **可选. playwright-cli** | 用户明确要求时检查 `playwright-cli --help` | 输出帮助信息 | 自动全局安装并安装 skills |
new: | **7. pi MCP Adapter（条件）** | `pi --version` 或 `~/.pi/agent`；`pi list` 含 `pi-mcp-adapter` 或 `~/.pi/agent/npm/node_modules/pi-mcp-adapter` 存在 | 检测到 pi 时 adapter 已安装；无 pi 时跳过 | 检测到 pi 且缺失时执行 `pi install npm:pi-mcp-adapter` |
| **可选. playwright-cli** | 用户明确要求时检查 `playwright-cli --help` | 输出帮助信息 | 自动全局安装并安装 skills |
```

- [ ] **Step 5: 常见错误表增加行**

精确替换：

```
old: | **playwright-cli 安装失败** | Node.js/npm 不可用或网络问题 | 仅在用户明确要求 Playwright 时报告，并提供手动安装命令 |
new: | **pi-mcp-adapter 安装失败** | pi 不可用或网络问题 | 手动执行 `pi install npm:pi-mcp-adapter`，或修复 pi 环境后重新运行 `/pre-check` |
| **playwright-cli 安装失败** | Node.js/npm 不可用或网络问题 | 仅在用户明确要求 Playwright 时报告，并提供手动安装命令 |
```

- [ ] **Step 6: 检查流程图增加 pi MCP 节点**

精确替换：

```
old:
    optional_playwright [label="用户明确要求时安装 Playwright", shape=box];
    remind_apikey [label="默认展示 API Key 占位提醒"];

new:
    check_pi_mcp [label="检测到 pi 环境?", shape=diamond];
    install_pi_mcp [label="检查/安装 pi-mcp-adapter"];
    skip_pi_mcp [label="跳过 pi MCP Adapter 检查"];
    optional_playwright [label="用户明确要求时安装 Playwright", shape=box];
    remind_apikey [label="默认展示 API Key 占位提醒"];
```

精确替换：

```
old:
    sync_superpowers -> superpowers_done;
    superpowers_done -> optional_playwright;

new:
    sync_superpowers -> superpowers_done;
    superpowers_done -> check_pi_mcp;
    check_pi_mcp -> install_pi_mcp [label="是"];
    check_pi_mcp -> skip_pi_mcp [label="否"];
    install_pi_mcp -> optional_playwright;
    skip_pi_mcp -> optional_playwright;
```

- [ ] **Step 7: 验证修改生效**

```bash
cd cadence-init/skills/pre-check
grep -c 'pi-mcp-adapter' SKILL.md        # 期望 >= 8
grep -c '步骤 7：检查 pi MCP Adapter' SKILL.md  # 期望 = 1
grep -c 'check_pi_mcp' SKILL.md          # 期望 = 4
```

- [ ] **Step 8: Commit**

```bash
git add cadence-init/skills/pre-check/SKILL.md
git commit -m "docs(cadence-init): pre-check 新增 pi-mcp-adapter 条件检查"
```

---

### Task 4: mcp-configuration — pi 消费方式说明（工作包 4）

**Files:**
- Modify: `cadence-init/skills/mcp-configuration/SKILL.md`

**Interfaces:**
- Consumes: Task 3 的 pre-check 步骤 7（引用其安装职责）
- Produces: 三客户端 MCP 对比表与 pi 说明章节

- [ ] **Step 1: 运行失败验证**

```bash
cd cadence-init/skills/mcp-configuration
grep -c 'pi-mcp-adapter' SKILL.md   # 期望 0
```

- [ ] **Step 2: 概述补充 pi**

精确替换：

```
old: 配置 MCP 服务器：创建 `.mcp.json` 配置文件、同步 Codex `.codex/config.toml`，并添加 MCP 使用规则到 CLAUDE.md。默认不需要人工交互即可完成基础 MCP 初始化。
new: 配置 MCP 服务器：创建 `.mcp.json` 配置文件、同步 Codex `.codex/config.toml`，并添加 MCP 使用规则到 CLAUDE.md。pi 无原生 MCP，由 `/pre-check` 全局安装的 pi-mcp-adapter 扩展直接读取 `.mcp.json`（含 HTTP 类型 server），无需同步第二份配置。默认不需要人工交互即可完成基础 MCP 初始化。
```

- [ ] **Step 3: 按实际章节顺序更新检查清单**

精确替换：

```
old: 6. **配置 .gitignore** — 添加 `.worktrees/`、`.mcp.json` 和 `.codex/config.toml` 到 .gitignore
7. **pi MCP 说明** — 说明 pi 经 pi-mcp-adapter 直接读取 `.mcp.json`（含 HTTP server），不维护第二份配置
new: 6. **pi MCP 说明** — 说明 pi 经 pi-mcp-adapter 直接读取 `.mcp.json`（含 HTTP server），不维护第二份配置
7. **配置 .gitignore** — 添加 `.worktrees/`、`.mcp.json` 和 `.codex/config.toml` 到 .gitignore
```

> 实际正文沿用已批准架构：`### 7. pi MCP 说明`、`### 8. 配置 .gitignore`。检查清单是七项任务，因此以“第 6 项 pi、第 7 项 gitignore”表达执行顺序，不要求清单编号与正文标题编号完全相同。

- [ ] **Step 4: 三客户端对比表扩展**

精确替换整个对比表：

```
old:
| 特征 | Claude Code (`.mcp.json`) | Codex (`.codex/config.toml`) |
|------|--------------------------|------------------------------|
| 格式 | JSON | TOML |
| 服务器定义 | `"mcpServers": { "name": {...} }` | `[mcp_servers.name]` |
| 传输类型 | `"type": "stdio"` / `"type": "http"` | 仅 stdio（有 `command`），**HTTP 类型不支持** |
| 环境变量 | `"env": { "KEY": "value" }` | `env = { "KEY" = "value" }` |
| HTTP 头 | `"headers": { "Authorization": "..." }` | `http_headers = { "Authorization" = "..." }` |
| type 字段 | 必须显式声明 | 不需要（自动推断） |

new:
| 特征 | Claude Code (`.mcp.json`) | Codex (`.codex/config.toml`) | pi（pi-mcp-adapter） |
|------|--------------------------|------------------------------|----------------------|
| 格式 | JSON | TOML | 复用 `.mcp.json`（JSON），无第二份配置 |
| 服务器定义 | `"mcpServers": { "name": {...} }` | `[mcp_servers.name]` | 同 `.mcp.json` |
| 传输类型 | `"type": "stdio"` / `"type": "http"` | 仅 stdio（有 `command`），**HTTP 类型不支持** | stdio 与 HTTP 均支持 |
| 环境变量 | `"env": { "KEY": "value" }` | `env = { "KEY" = "value" }` | 同 `.mcp.json` |
| HTTP 头 | `"headers": { "Authorization": "..." }` | `http_headers = { "Authorization" = "..." }` | 同 `.mcp.json` |
| type 字段 | 必须显式声明 | 不需要（自动推断） | 同 `.mcp.json` |
```

- [ ] **Step 5: 新增 pi 章节并将 .gitignore 章节重编号为 8**

精确替换（在 `### 7. 配置 .gitignore` 标题处插入新章节并改编号）：

```
old: ### 7. 配置 .gitignore
new: ### 7. pi MCP 说明

> **无需同步步骤** — pi 不维护第二份客户端配置文件。

- pi 官方不提供原生 MCP 支持；MCP 能力由第三方扩展 pi-mcp-adapter 提供，该扩展由 `/pre-check` 步骤 7 全局安装。
- pi-mcp-adapter 直接读取项目根目录 `.mcp.json`；本 Skill 维护的 `.mcp.json` 即 pi 的 MCP 配置来源，无需执行任何同步。
- 与 Codex 不同，pi-mcp-adapter 支持 HTTP 类型 server：智普的 `web-search-prime`、`web-reader`、`zread` 在 pi 下可用。
- `.gitignore` 无需新增条目：pi 复用的 `.mcp.json` 已在忽略清单内。

**pi 侧验证方式**：pi 会话中输入 `/mcp`（由 adapter 提供）查看 server 列表与连接状态。

### 8. 配置 .gitignore
```

- [ ] **Step 6: .gitignore 说明表补充 pi 无新增条目**

精确替换：

```
old: | `.codex/config.toml` | Codex CLI 项目级 MCP 配置 | 包含本地 MCP 路径和 API Key 占位符，不应提交 |
new: | `.codex/config.toml` | Codex CLI 项目级 MCP 配置 | 包含本地 MCP 路径和 API Key 占位符，不应提交 |

> pi 复用 `.mcp.json`（pi-mcp-adapter 直读），`.gitignore` 无需为 pi 新增条目。
```

- [ ] **Step 7: 验证修改生效**

```bash
cd cadence-init/skills/mcp-configuration
grep -c 'pi-mcp-adapter' SKILL.md          # 期望 >= 6
grep -c '### 7. pi MCP 说明' SKILL.md      # 期望 = 1
grep -c '### 8. 配置 .gitignore' SKILL.md  # 期望 = 1
grep -n '### 7. 配置 .gitignore' SKILL.md  # 期望无输出
```

- [ ] **Step 8: Commit**

```bash
git add cadence-init/skills/mcp-configuration/SKILL.md
git commit -m "docs(cadence-init): mcp-configuration 增加 pi MCP 消费方式说明"
```

---

### Task 5: rule-config — 规则模板补 pi 行为约定（工作包 5）

**Files:**
- Modify: `cadence-init/skills/rule-config/references/rules/agent-routing-kernel.md`
- Modify: `cadence-init/skills/rule-config/references/rules/openspec-superpowers-workflow.md`
- Modify: `cadence-init/skills/rule-config/references/rules/mcp-servers.md`
- Modify: `cadence-init/skills/rule-config/SKILL.md`

**Interfaces:**
- Consumes: 无
- Produces: 含 pi 约定的 L0 路由区块模板（将来经 rule-config 写入各项目 AGENTS.md/CLAUDE.md）

- [ ] **Step 1: 运行失败验证**

```bash
cd cadence-init/skills/rule-config
grep -c 'pi' references/rules/agent-routing-kernel.md   # 记录基线（不含 pi 客户端约定）
grep -n 'Codex 与 pi\|Codex/pi\|pi 与 Codex' references/rules/*.md   # 期望无输出
```

- [ ] **Step 2: agent-routing-kernel.md — 仓库操作路由段补 pi**

精确替换：

```
old: 需要仓库操作时：Claude/Kimi 必须把全部 Skill 调用及失败重试作为连续工具事件；首个调用前、事件之间和重试前均保持用户可见输出静默，禁止输出“我先调用 Skill”等引导句；随后第一段输出 `工作流路由：阶段=...；Change=...；Plan=...；必调 Skill=...`。Codex 先显式选择 Skill，将用途并入首段回执，随后立即全文读取 Skill。Skill 调用完成后才读取仓库规则和使用仓库工具。
new: 需要仓库操作时：Claude/Kimi 必须把全部 Skill 调用及失败重试作为连续工具事件；首个调用前、事件之间和重试前均保持用户可见输出静默，禁止输出“我先调用 Skill”等引导句；随后第一段输出 `工作流路由：阶段=...；Change=...；Plan=...；必调 Skill=...`。Codex 先显式选择 Skill，将用途并入首段回执，随后立即全文读取 Skill。pi 与 Codex 同类：从 Skill 清单显式选择 Skill，将用途并入首段回执，随后立即全文读取对应 SKILL.md 作为调用，Skill 未读完前不得读取仓库规则或使用仓库工具。Skill 调用完成后才读取仓库规则和使用仓库工具。
```

- [ ] **Step 3: agent-routing-kernel.md — 纯概念问答段补 pi**

精确替换：

```
old: 纯概念问答只调用全局 `using-superpowers` 后直接回答，不输出仓库路由回执，不加载仓库规则或其他无关 Skill；Codex 可先输出 Skill 用途公告。一旦转为仓库操作，必须重新路由。
new: 纯概念问答只调用全局 `using-superpowers` 后直接回答，不输出仓库路由回执，不加载仓库规则或其他无关 Skill；Codex/pi 可先输出 Skill 用途公告。一旦转为仓库操作，必须重新路由。
```

- [ ] **Step 4: agent-routing-kernel.md — Skill 参数与失败重试段补 pi**

精确替换：

```
old: Claude/Kimi 的 Skill 参数使用表中不带命名空间的原名；调用失败必须按客户端已注册清单重试，未成功加载则失败关闭。
new: Claude/Kimi 的 Skill 参数使用表中不带命名空间的原名；pi 以全文读取对应 SKILL.md 作为 Skill 调用；调用失败必须按客户端已注册清单重试，未成功加载则失败关闭。
```

- [ ] **Step 5: openspec-superpowers-workflow.md — 阶段重路由段补 pi**

精确替换：

```
old: Codex 的平台约束允许“从 Skill 目录显式选择 → 将 Skill 用途并入首个路由回执 → 立即全文读取对应 `SKILL.md` → 读取仓库规则 → 使用仓库工具”；Skill 正文未读完前不得进行仓库操作。
new: Codex 与 pi 的平台约束允许“从 Skill 清单显式选择 → 将 Skill 用途并入首个路由回执 → 立即全文读取对应 `SKILL.md` → 读取仓库规则 → 使用仓库工具”；Skill 正文未读完前不得进行仓库操作。
```

- [ ] **Step 6: mcp-servers.md — 三处客户端表述**

精确替换 1：

```
old: 2. 直接在客户端粘贴图片无法调用此 MCP（Claude Code 除外）
new: 2. 直接在客户端粘贴图片无法调用此 MCP（Claude Code 除外；pi 经 pi-mcp-adapter 调用时同样需通过本地路径指定图片）
```

精确替换 2：

```
old: 2. 验证配置：进入 Claude Code 后输入 `/mcp`，能看到 `web_search` 和 `understand_image` 说明配置成功
new: 2. 验证配置：在 Claude Code 或 pi 中输入 `/mcp`（pi 的 `/mcp` 由 pi-mcp-adapter 提供），能看到 `web_search` 和 `understand_image` 说明配置成功
```

精确替换 3：

```
old: > 1. 请自行前往对应平台获取 API Key，不要将真实密钥告诉 Claude Code
new: > 1. 请自行前往对应平台获取 API Key，不要将真实密钥告诉 AI 客户端（Claude Code、Codex、pi 等）
```

- [ ] **Step 7: rule-config/SKILL.md — codegraph 配置范围注明 pi**

精确替换：

```
old: - `--target=claude,codex`：只支持 Claude Code 和 Codex。
new: - `--target=claude,codex`：只支持 Claude Code 和 Codex，不支持 pi；pi 无原生 MCP，只要 `.mcp.json` 包含 codegraph server，pi 即可经 pi-mcp-adapter 直接使用，无需额外动作。
```

- [ ] **Step 8: 验证修改生效**

```bash
cd cadence-init/skills/rule-config
grep -c 'pi 与 Codex 同类' references/rules/agent-routing-kernel.md     # 期望 = 1
grep -c 'Codex/pi 可先输出' references/rules/agent-routing-kernel.md    # 期望 = 1
grep -c 'Codex 与 pi 的平台约束' references/rules/openspec-superpowers-workflow.md  # 期望 = 1
grep -c 'pi-mcp-adapter' references/rules/mcp-servers.md                # 期望 = 2
grep -c '不支持 pi' SKILL.md                                            # 期望 = 1
```

- [ ] **Step 9: Commit**

```bash
git add cadence-init/skills/rule-config/
git commit -m "docs(cadence-init): rule-config 规则模板补充 pi 客户端行为约定"
```

---

### Task 6: 整体验证（工作包 6）

**Files:**
- Modify: `openspec/changes/add-pi-agent-support/tasks.md`（仅在全部实现与验证完成后确认复选框）

**Interfaces:**
- Consumes: Task 1-5 的全部改动
- Produces: 验证证据

- [ ] **Step 1: 运行 rule-config 受管区块生命周期测试**

```bash
cd cadence-init/skills/rule-config
bash tests/verify-managed-lifecycle.sh
```

Expected: 临时 detached worktree 中恢复归档 fixture、仅同步该临时 worktree 的根入口受管区块后，输出 `SUMMARY pass=15 fail=0`；主工作树根入口仍为非目标。

- [ ] **Step 2: 对照本机环境核对文档描述**

```bash
# 软链形态：~/.pi/agent/skills 下应为指向 ~/.agents/skills 的软链
ls -la ~/.pi/agent/skills/brainstorming

# 老项目迁移实测：先初始化 claude,codex
TMP_DIR="$(mktemp -d)"
cd "$TMP_DIR"
openspec init --tools claude,codex
openspec update
test ! -e .pi
openspec init --tools pi
# 此时应有 5 个 skills 与 5 个 prompts
SKILLS="$(find .pi/skills -mindepth 1 -maxdepth 1 -type d -name 'openspec-*' | wc -l | tr -d ' ')"
PROMPTS="$(find .pi/prompts -mindepth 1 -maxdepth 1 -type f -name 'opsx-*.md' | wc -l | tr -d ' ')"
printf 'PI_SKILLS=%s\nPI_PROMPTS=%s\n' "$SKILLS" "$PROMPTS"
test "$SKILLS" = 5
test "$PROMPTS" = 5
openspec update

# 全局 adapter
pi list
test -d "$HOME/.pi/agent/npm/node_modules/pi-mcp-adapter"
VERSION="$(node -p "require(process.env.HOME + '/.pi/agent/npm/node_modules/pi-mcp-adapter/package.json').version")"
printf 'ADAPTER_VERSION=%s\n' "$VERSION"
test -n "$VERSION"
grep -n 'npm:pi-mcp-adapter' "$HOME/.pi/agent/settings.json"
test -L "$HOME/.pi/agent/npm/node_modules/.bin/pi-mcp-adapter"
```

Expected: `openspec update` 单独执行后没有 `.pi`；`openspec init --tools pi` 后恰有 5 个 skills 与 5 个 prompts，随后 update 成功；`pi list` 含 `npm:pi-mcp-adapter`；实际包目录与可执行软链存在；settings packages 含 `npm:pi-mcp-adapter`；版本输出非空。本次全局安装的新鲜证据为 `2.11.0`，但产品策略不锁定版本。

- [ ] **Step 3: OpenSpec change 校验与任务勾选**

```bash
openspec validate add-pi-agent-support
```

Expected: `Change 'add-pi-agent-support' is valid`

随后在 `openspec/changes/add-pi-agent-support/tasks.md` 勾选 1.1-6.2 全部工作包（验证通过后）。

- [ ] **Step 4: Commit**

```bash
git add openspec/changes/add-pi-agent-support/tasks.md
git commit -m "docs(openspec): add-pi-agent-support 工作包全部完成"
```

---

## Self-Review 记录

- **Spec 覆盖**：5 条 requirement → Task 1（软链）、Task 2（OpenSpec）、Task 3（adapter 检查）、Task 4（MCP 文档）、Task 5（路由规则），一一映射，无缺口。
- **Placeholder 扫描**：所有编辑均给出完整 old/new 文本，无 TBD/TODO。
- **一致性**：`~/.pi/agent/skills`、pi-mcp-adapter、`claude,codex,pi` 等关键字符串在各 Task 间一致。
