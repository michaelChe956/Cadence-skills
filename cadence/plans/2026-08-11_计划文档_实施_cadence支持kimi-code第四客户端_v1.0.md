# Cadence 支持 Kimi Code 第四客户端实施 Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让 cadence-init 的 pre-check / mcp-configuration / rule-config 三 skill 完整支持 Kimi Code 作为第四客户端：OpenSpec 产物四客户端补齐、MCP 原生复用根目录 `.mcp.json`、项目类型扫描剪枝 `.kimi-code`、README 表述同步。

**Architecture:** 改动收敛在三个 skill 的文档与一处脚本常量内：pre-check 步骤 5 从三客户端扩为四客户端（`openspec init --tools claude,codex,pi,kimi`，按缺失客户端增量补齐 kimi）；mcp-configuration 仅补文档（Kimi Code 原生三层加载 MCP 配置，直接复用根目录 `.mcp.json`，不生成第二份配置）；rule-config 在 `PRUNE_DIRS` 常量与 SKILL.md find 块同步加 `.kimi-code`（受 `assert_bounded_source_scan_contract` 双向断言）。Superpowers 四层软链不变（`~/.agents/skills` 通用层已被 Kimi 扫描）。路由规则模板已含 "Claude/Kimi" 表述，不改。

**Tech Stack:** Markdown（SKILL.md/README）、Python 3（rule-config.py 常量）、Shell（pre-check.sh 注释、verify-managed-lifecycle.sh harness）、OpenSpec CLI（>= 1.7.0 生成 `.kimi-code/skills/`）。

**契约映射：** 本 Plan 只展开 `openspec/changes/support-kimi-code/tasks.md` 的 6 组工作包，不重定义范围、架构或验收。验收 Scenario 以 `specs/kimi-code-support/spec.md` 与 `specs/init-skill-sequencing/spec.md`（delta）为准。

## Global Constraints

- 本仓库根目录 `AGENTS.md` 与 `.claude/rules/` 为受管文件，本次**不改动**（路由规则模板 `agent-routing-kernel.md` / `openspec-superpowers-workflow.md` 已含 "Claude/Kimi"，保持不变）。
- `install-offline.sh/.bat`、`.claude-plugin/` 与 Claude Code 插件打包**不改动**（与客户端支持无关）。
- Superpowers 软链层数与逻辑**不改动**（Kimi 经 `~/.agents/skills` 通用层消费，不新增 `~/.kimi-code/skills` 软链目标）。
- mcp-configuration **不生成 `.kimi-code/mcp.json` 副本**、**不新增 `.gitignore` 条目**（Kimi 原生读取根目录 `.mcp.json`；`.mcp.json` 已在忽略清单）。
- OpenSpec 版本注记：`--tools kimi` 生成 `.kimi-code/skills/` 需要 OpenSpec CLI >= **1.7.0**（1.4.0 起支持 kimi 但产物路径为旧 `.kimi/skills/`；1.7.0 起改为 `.kimi-code/` 并自动迁移旧 `.kimi` 配置）。pre-check 脚本始终安装 `@fission-ai/openspec@latest`，版本不足按既有升级逻辑处理。
- 所有文档中文；Markdown 遵循 `.claude/rules/markdown-format.md`。
- 每个 Task 结束独立提交，提交信息遵循仓库既有风格（`feat(pre-check):` / `docs(mcp-configuration):` / `fix(rule-config):` / `docs(readme):`）。

---

### Task 1: pre-check SKILL.md —— OpenSpec 四客户端产物（契约工作包 1.1–1.6）

**Files:**
- Modify: `cadence-init/skills/pre-check/SKILL.md`

**Interfaces:**
- Consumes: 无（纯文档编排）。
- Produces: `openspec init --tools claude,codex,pi,kimi` 四客户端命令与 kimi 就绪判定口径，供 Task 6 端到端验证引用。

- [ ] **Step 1: 更新 no-interrupt 强制完成策略表（第 44 行）**

将：
```
| OpenSpec 三客户端产物 | claude/codex/pi 三客户端目标指令文件验证成功（`openspec/config.yaml` 缺失不算失败，仅提示由 rule-config 创建） | 立即终止 |
```
改为：
```
| OpenSpec 四客户端产物 | claude/codex/pi/kimi 四客户端目标指令文件验证成功（`openspec/config.yaml` 缺失不算失败，仅提示由 rule-config 创建） | 立即终止 |
```

- [ ] **Step 2: 更新增量运行示例（第 127 行）**

在现有"框架新增 OpenSpec pi 支持后…"段落后追加 kimi 段落，并把新项目命令改为四客户端：
```
- 框架新增 OpenSpec kimi 支持后，老项目重新运行 `/pre-check`：缺少 `.kimi-code` 产物时先执行 `openspec init --tools kimi`，再执行 `openspec update`；若 kimi 产物已存在，则直接执行 `openspec update`。新项目或四客户端产物均缺失时执行 `openspec init --tools claude,codex,pi,kimi`。
```
并将原文"新项目或三客户端产物均缺失时执行 `openspec init --tools claude,codex,pi`"改为四客户端命令。

- [ ] **Step 3: 更新检查流程图 label（第 143 行）**

`openspec_clients [label="步骤 5：OpenSpec 三客户端产物补齐"];` → `openspec_clients [label="步骤 5：OpenSpec 四客户端产物补齐"];`

- [ ] **Step 4: 更新快速参考表（第 167 行）**

`| **5. OpenSpec** | 脚本报告 `openspec` 项 + 三客户端产物状态 | ... | 按缺失客户端 `init --tools <缺失客户端>` 后 `update` |`
→ 将"三客户端产物状态"改为"四客户端产物状态"。

- [ ] **Step 5: 更新步骤 0 判定规则（第 226 行）**

`...继续步骤 5 的 OpenSpec 三客户端检查与步骤 6 的 Superpowers 同步。` → `...继续步骤 5 的 OpenSpec 四客户端检查与步骤 6 的 Superpowers 同步。`

- [ ] **Step 6: 更新步骤 5 标题与行为说明（第 266–275 行）**

- 标题：`### 步骤 5：检查 OpenSpec 三客户端产物` → `### 步骤 5：检查 OpenSpec 四客户端产物`
- 三处"三客户端产物检查"（第 271、272、275 行）→ "四客户端产物检查"
- 第 271 行"继续本节三客户端产物检查"与第 272 行"本节仅在 CLI 就绪后执行三客户端产物检查"同步替换。

- [ ] **Step 7: 更新初始化与更新命令（第 282–288 行）**

```bash
# 四客户端产物均缺失（新项目）
cd "<PROJECT_ROOT>" && openspec init --tools claude,codex,pi,kimi

# 仅 kimi 产物缺失
cd "<PROJECT_ROOT>" && openspec init --tools kimi && openspec update

# 仅 pi 产物缺失
cd "<PROJECT_ROOT>" && openspec init --tools pi && openspec update

# 四客户端产物齐全
cd "<PROJECT_ROOT>" && openspec update
```

- [ ] **Step 8: 更新增量要求表与验证命令（第 294–315 行）**

- 表头"按 claude、codex、pi 三客户端分别检测指令产物存在性" → "按 claude、codex、pi、kimi 四客户端分别检测指令产物存在性"。
- 表中新增 kimi 行：
```
| kimi | `.kimi-code/skills/` 下存在 5 个 `openspec-*` 目录 |
```
- 第 302 行"存在缺失客户端：…（如 `claude,codex,pi`、`pi`）"补充 `kimi` 示例。
- 第 303 行"三客户端产物均齐全" → "四客户端产物均齐全"。
- 产物结构说明补充：
```
  - Kimi Code：`.kimi-code/skills/openspec-*`（无 commands/adapter，仅 5 个 skill）
```
- 验证命令追加：
```bash
cd "<PROJECT_ROOT>" && test -f .kimi-code/skills/openspec-propose/SKILL.md
cd "<PROJECT_ROOT>" && test "$(find .kimi-code/skills -mindepth 1 -maxdepth 1 -type d -name 'openspec-*' | wc -l | tr -d ' ')" = 5
```

- [ ] **Step 9: 补充版本注记（步骤 5 尾部）**

在 `--tools pi 需要 OpenSpec CLI >= 1.4.1` 注记附近追加：
```
- `--tools kimi` 需要 OpenSpec CLI >= 1.7.0（生成 `.kimi-code/skills/`；1.4.0 起支持 kimi 但路径为旧 `.kimi/skills/`，1.7.0 起改用 `.kimi-code/` 并自动迁移旧 `.kimi` 配置）；步骤 0 脚本始终安装 `@fission-ai/openspec@latest`，版本不足时先回到步骤 0 升级 CLI。
```
确认既有 `--tools pi 需要 OpenSpec CLI >= 1.4.1` 注记原样保留。

- [ ] **Step 10: 验证（grep 断言无残留"三客户端"）**

```bash
cd /home/michaelche/workspace/github/Cadence-skills
# 应无输出（0 命中）
grep -n "三客户端" cadence-init/skills/pre-check/SKILL.md
# 应命中 4 处及以上
grep -c "claude,codex,pi,kimi" cadence-init/skills/pre-check/SKILL.md
# 应命中 kimi 就绪判定与验证命令
grep -n "kimi" cadence-init/skills/pre-check/SKILL.md
```
预期：`grep "三客户端"` 无命中；`claude,codex,pi,kimi` 至少 2 处；`kimi` 覆盖就绪判定表、增量表、验证命令、版本注记。

- [ ] **Step 11: Commit**

```bash
cd /home/michaelche/workspace/github/Cadence-skills
git add cadence-init/skills/pre-check/SKILL.md
git commit -m "feat(pre-check): OpenSpec 客户端产物扩为四客户端（claude/codex/pi/kimi）"
```

---

### Task 2: pre-check —— 脚本注释 + Superpowers 覆盖说明（契约工作包 1.7、2.1）

**Files:**
- Modify: `cadence-init/skills/pre-check/scripts/pre-check.sh`（第 4 行注释）
- Modify: `cadence-init/skills/pre-check/SKILL.md`（步骤 6 Superpowers 目录约定）

**Interfaces:**
- Consumes: Task 1 已确立四客户端口径。
- Produces: "Kimi 经 `~/.agents/skills` 通用层消费、无额外同步层"的文档口径，供 Task 3/5 复用表述。

- [ ] **Step 1: 更新 pre-check.sh 头部职责注释（第 4 行）**

将：
```
# 不处理 Superpowers 软链、OpenSpec 三客户端产物、Playwright、API Key（由 SKILL.md 处理）。
```
改为：
```
# 不处理 Superpowers 软链、OpenSpec 四客户端产物、Playwright、API Key（由 SKILL.md 处理）。
```
（仅注释，无逻辑改动。）

- [ ] **Step 2: 在 SKILL.md 步骤 6 目录约定表后追加说明**

在步骤 6 的"目录约定"表下方追加：
```
> 说明：Kimi Code 扫描用户级通用目录 `~/.agents/skills`（superpowers 软链第 2 层即此目录），经该层直接获得 Superpowers skills，无需新增 `~/.kimi-code/skills` 软链目标；`~/.kimi-code/skills` 是 Kimi 专属用户 skills 目录，不放通用 superpowers。
```

- [ ] **Step 3: 验证**

```bash
cd /home/michaelche/workspace/github/Cadence-skills
grep -n "四客户端产物" cadence-init/skills/pre-check/scripts/pre-check.sh
grep -n "Kimi Code 扫描用户级通用目录" cadence-init/skills/pre-check/SKILL.md
# 确认 SKILL.md 步骤 6 目录约定表不含 ~/.kimi-code/skills 软链目标
grep -c "\.kimi-code/skills" cadence-init/skills/pre-check/SKILL.md
```
预期：脚本注释命中 1 处；SKILL.md 说明命中 1 处；`.kimi-code/skills` 仅出现在说明文字（不含"软链目标"表述）。

- [ ] **Step 4: Commit**

```bash
cd /home/michaelche/workspace/github/Cadence-skills
git add cadence-init/skills/pre-check/scripts/pre-check.sh cadence-init/skills/pre-check/SKILL.md
git commit -m "docs(pre-check): Superpowers 覆盖 Kimi 说明 + 脚本职责注释四客户端"
```

---

### Task 3: mcp-configuration —— Kimi 复用根目录 `.mcp.json`（契约工作包 3.1–3.4）

**Files:**
- Modify: `cadence-init/skills/mcp-configuration/SKILL.md`

**Interfaces:**
- Consumes: Task 2 的"Kimi 经通用层消费"表述风格。
- Produces: 客户端格式差异表 Kimi 列 + Kimi MCP 说明节，供 Task 5 README 同步引用。

- [ ] **Step 1: 更新概述（第 11 行）**

在现有概述段落后追加一句：
```
Kimi Code 原生读取项目根 `.mcp.json`（三层加载：`~/.kimi-code/mcp.json` → `<项目根>/.mcp.json` → `<cwd>/.kimi-code/mcp.json`，后者覆盖前者），本 Skill 维护的 `.mcp.json` 即 Kimi 的 MCP 配置来源，无需同步第二份配置。
```

- [ ] **Step 2: 更新检查清单（第 110 行区域）**

在清单第 6 项"pi MCP 说明"后追加：
```
7. **Kimi MCP 说明** — 说明 Kimi Code 原生读取项目根 `.mcp.json`（含 stdio/HTTP/SSE），不维护第二份配置
8. **配置 .gitignore** — 添加 `.worktrees/`、`.mcp.json` 和 `.codex/config.toml` 到 .gitignore（Kimi 复用 `.mcp.json`，无需新增条目）
```
（原"7. 配置 .gitignore"编号顺延为 8。）

- [ ] **Step 3: 更新客户端格式差异表（第 562 行）**

表头 `**Claude Code、Codex 与 pi 格式差异**` → `**Claude Code、Codex、pi 与 Kimi Code 格式差异**`，表体追加一列并补一行：

| 特征 | Claude Code (`.mcp.json`) | Codex (`.codex/config.toml`) | pi（pi-mcp-adapter） | Kimi Code（原生） |
|------|--------------------------|------------------------------|----------------------|-------------------|
| 格式 | JSON | TOML | 复用 `.mcp.json`（JSON），无第二份配置 | 复用根目录 `.mcp.json`（JSON），无第二份配置 |
| 服务器定义 | `"mcpServers": { "name": {...} }` | `[mcp_servers.name]` | 同 `.mcp.json` | 同 `.mcp.json` |
| 传输类型 | `"type": "stdio"` / `"type": "http"` | 仅 stdio（有 `command`），**HTTP 类型不支持** | stdio 与 HTTP 均支持 | stdio / HTTP / SSE 均支持 |
| 环境变量 | `"env": { "KEY": "value" }` | `env = { "KEY" = "value" }` | 同 `.mcp.json` | 同 `.mcp.json` |
| HTTP 头 | `"headers": { "Authorization": "..." }` | `http_headers = { "Authorization" = "..." }` | 同 `.mcp.json` | 同 `.mcp.json` |
| type 字段 | 必须显式声明 | 不需要（自动推断） | 同 `.mcp.json` | 不需要（按 `command`/`url` 自动推断） |

> 说明：Kimi 的 schema 为非严格解析，`.mcp.json` 中 pi 扩展的 `directTools` 等未知字段会被静默忽略，无需为 Kimi 剥离。

- [ ] **Step 4: 新增 "### 7.5 Kimi Code MCP 说明" 节（插在 pi 节之后、.gitignore 节之前）**

```markdown
### 7.5 Kimi Code MCP 说明

> **无需同步步骤** — Kimi Code 不维护第二份 MCP 配置文件。

- Kimi Code 原生支持 MCP（stdio / HTTP / SSE 三种传输），直接读取项目根目录 `.mcp.json`（源码三层加载：`~/.kimi-code/mcp.json` → `<项目根>/.mcp.json` → `<cwd>/.kimi-code/mcp.json`，后者覆盖前者）。
- 本 Skill 维护的 `.mcp.json` 即 Kimi 的 MCP 配置来源：智普的 `web-search-prime`、`web-reader`、`zread`（HTTP）与 `zai-mcp-server`、MiniMax（stdio）在 Kimi 下均可用，无需任何同步。
- `.mcp.json` 中的 `directTools` 等 pi 扩展字段对 Kimi 无害（非严格 schema 静默忽略）。
- `.gitignore` 无需新增条目：Kimi 复用的 `.mcp.json` 已在忽略清单内。

**Kimi 侧验证方式**：Kimi Code 会话中输入 `/mcp` 查看 server 连接状态，输入 `/mcp-config` 交互式新增/编辑/删除 server。
```

- [ ] **Step 5: 验证**

```bash
cd /home/michaelche/workspace/github/Cadence-skills
grep -n "Kimi Code MCP 说明\|Kimi Code（原生）\|kimi-code/mcp.json" cadence-init/skills/mcp-configuration/SKILL.md
# 确认全文没有"为 Kimi 生成 .kimi-code/mcp.json 副本"或"追加 .kimi-code/mcp.json"类指令
grep -n "追加 .kimi-code/mcp.json" cadence-init/skills/mcp-configuration/SKILL.md
```
预期：Kimi 说明节、格式差异表 Kimi 列、三层加载说明均命中；`追加 .kimi-code/mcp.json` 无命中。

- [ ] **Step 6: Commit**

```bash
cd /home/michaelche/workspace/github/Cadence-skills
git add cadence-init/skills/mcp-configuration/SKILL.md
git commit -m "docs(mcp-configuration): Kimi Code 原生复用根目录 .mcp.json"
```

---

### Task 4: rule-config —— 项目类型扫描剪枝 `.kimi-code`（契约工作包 4.1–4.3）

**Files:**
- Modify: `cadence-init/skills/rule-config/scripts/rule-config.py`（`PRUNE_DIRS` 常量，约 351–372 行）
- Modify: `cadence-init/skills/rule-config/SKILL.md`（有界扫描 find 块，第 85–86 行）
- Test: `cadence-init/skills/rule-config/tests/verify-managed-lifecycle.sh`（`assert_bounded_source_scan_contract` 双向断言，自动覆盖）

**Interfaces:**
- Consumes: 无。
- Produces: `PRUNE_DIRS` 含 `.kimi-code`，且与 SKILL.md find 块双向一致（harness 断言强制）。

- [ ] **Step 1: 在 `rule-config.py` 的 `PRUNE_DIRS` 增加 `.kimi-code`**

在 `PRUNE_DIRS` 列表的 `".pi",` 行之后插入 `".kimi-code",`：
```python
PRUNE_DIRS = [
    ".git",
    ".claude",
    ".claude-plugin",
    ".codex",
    ".pi",
    ".kimi-code",
    ".codegraph",
    "cadence-init",
    "Cadence-skills",
    "node_modules",
    "vendor",
    "venv",
    ".venv",
    "env",
    ".env",
    "dist",
    "build",
    "coverage",
    ".next",
    "target",
    "__pycache__",
]
```

- [ ] **Step 2: 在 SKILL.md 有界扫描 find 块同步增加 `-o -name .kimi-code`**

将第 85 行：
```
  \( -type d \( -name .git -o -name .claude -o -name .claude-plugin -o -name .codex -o -name .pi -o -name .codegraph -o -name cadence-init -o -name Cadence-skills \
```
改为：
```
  \( -type d \( -name .git -o -name .claude -o -name .claude-plugin -o -name .codex -o -name .pi -o -name .kimi-code -o -name .codegraph -o -name cadence-init -o -name Cadence-skills \
```
（其余行不动；SKILL.md 注释"与脚本 `PRUNE_DIRS` 常量逐项一致，不得增删"保持原样。）

- [ ] **Step 3: 运行单元测试确认无回归**

```bash
cd /home/michaelche/workspace/github/Cadence-skills/cadence-init/skills/rule-config/tests
python3 -m unittest test_rule_config -v 2>&1 | tail -5
```
预期：全部测试通过（含 `ut-detect_project-bounded-scan / S1a-01` 剪枝用例）。

- [ ] **Step 4: 运行 harness 双向断言**

```bash
cd /home/michaelche/workspace/github/Cadence-skills/cadence-init/skills/rule-config/tests
bash verify-managed-lifecycle.sh 2>&1 | tail -15
```
预期：`assert_bounded_source_scan_contract` 通过（脚本 `PRUNE_DIRS` 与 SKILL.md find 剪枝清单逐项一致），整体 exit 0。

- [ ] **Step 5: Commit**

```bash
cd /home/michaelche/workspace/github/Cadence-skills
git add cadence-init/skills/rule-config/scripts/rule-config.py cadence-init/skills/rule-config/SKILL.md
git commit -m "fix(rule-config): 项目类型扫描剪枝 .kimi-code 客户端目录"
```

---

### Task 5: README 与文档四客户端表述（契约工作包 5.1–5.3）

**Files:**
- Modify: `README.md`

**Interfaces:**
- Consumes: Task 1 的四客户端口径、Task 3 的 Kimi MCP 说明。
- Produces: 对外文档四客户端口径，供最终验收对照。

- [ ] **Step 1: 更新 skills 表格 `/pre-check` 行（第 217 行）**

将 `OpenSpec 检查范围为 CLI 与 `claude,codex,pi` 三客户端指令产物` → `OpenSpec 检查范围为 CLI 与 `claude,codex,pi,kimi` 四客户端指令产物`。

- [ ] **Step 2: 更新 no-interrupt 表格 `/pre-check` 行（第 320 行）**

`OpenSpec（CLI 与三客户端指令产物；...）` → `OpenSpec（CLI 与四客户端指令产物；...）`。

- [ ] **Step 3: 更新职责边界说明（第 338 行）**

`/pre-check` 负责 OpenSpec CLI 与三客户端指令产物 → 四客户端指令产物。

- [ ] **Step 4: 更新初始化特性列表（第 368 行）**

`OpenSpec 检查 CLI 与 `claude,codex,pi` 三客户端指令产物` → `OpenSpec 检查 CLI 与 `claude,codex,pi,kimi` 四客户端指令产物`。

- [ ] **Step 5: 更新客户端支持说明（第 519 行）**

`同时支持 Claude Code、Codex 与 pi 三类客户端的环境初始化` → `同时支持 Claude Code、Codex、pi 与 Kimi Code 四类客户端的环境初始化`。

- [ ] **Step 6: 更新 `/mcp-configuration` 行（第 220 行）**

在现有描述后追加 `Kimi Code 原生复用根目录 `.mcp.json`（含 HTTP server），不维护第二份配置`。

- [ ] **Step 7: 验证**

```bash
cd /home/michaelche/workspace/github/Cadence-skills
# 应无输出（0 命中）
grep -n "三客户端" README.md
# 应命中 4 处
grep -c "四客户端" README.md
grep -n "Kimi Code" README.md | head
```
预期：`三客户端` 无残留；`四客户端` 至少 4 处；Kimi Code 说明覆盖 skills 表格与支持说明。

- [ ] **Step 8: Commit**

```bash
cd /home/michaelche/workspace/github/Cadence-skills
git add README.md
git commit -m "docs(readme): 客户端支持扩为四客户端并补充 Kimi Code 说明"
```

---

### Task 6: 端到端验证（契约工作包 6.1–6.3）

**Files:**
- 临时目录（验证用，不入库）：`/tmp/kimi-e2e-XXXXXX`

**Interfaces:**
- Consumes: Task 1–5 全部产物。
- Produces: 四客户端产物、`.mcp.json` Kimi 消费、PRUNE_DIRS 无回归的新鲜证据。

- [ ] **Step 1: 临时项目验证 OpenSpec 四客户端产物**

```bash
cd /tmp && rm -rf kimi-e2e && mkdir kimi-e2e && cd kimi-e2e
git init -q && openspec init --tools claude,codex,pi,kimi 2>&1 | tail -5
# 验证四客户端产物
test -f .claude/commands/opsx/propose.md -o -f .claude/skills/openspec-propose/SKILL.md
test -d .agents/skills/openspec-propose
test -f .pi/skills/openspec-propose/SKILL.md
test -f .kimi-code/skills/openspec-propose/SKILL.md
test "$(find .kimi-code/skills -mindepth 1 -maxdepth 1 -type d -name 'openspec-*' | wc -l | tr -d ' ')" = 5
echo "E2E-OK"
```
预期：`openspec init` 成功输出 "Created: Kimi Code / 5 skills in .kimi-code/"；四个 `test` 全部通过，输出 `E2E-OK`。

- [ ] **Step 2: 增量补齐验证（老项目缺 kimi）**

```bash
cd /tmp && rm -rf kimi-incremental && mkdir kimi-incremental && cd kimi-incremental
git init -q && openspec init --tools claude,codex,pi 2>&1 | tail -2
# 模拟老项目：无 .kimi-code，验证仅 init kimi 后 update
openspec init --tools kimi 2>&1 | tail -3
openspec update 2>&1 | tail -2
test -f .kimi-code/skills/openspec-propose/SKILL.md && echo "INCR-OK"
```
预期：老项目仅执行 `init --tools kimi` + `update` 后补齐 `.kimi-code/skills/openspec-*`，输出 `INCR-OK`。

- [ ] **Step 3: rule-config 测试套件与 harness 全量回归**

```bash
cd /home/michaelche/workspace/github/Cadence-skills/cadence-init/skills/rule-config/tests
python3 -m unittest test_rule_config -v 2>&1 | tail -3
bash verify-managed-lifecycle.sh 2>&1 | tail -3
```
预期：unittest 全部通过；harness exit 0（含 `assert_bounded_source_scan_contract`）。

- [ ] **Step 4: mcp-configuration 冒烟（Kimi 消费 `.mcp.json`）**

```bash
cd /tmp/kimi-e2e
# 构造与 mcp-configuration 产物一致的根目录 .mcp.json（含 stdio + HTTP）
cat > .mcp.json <<'EOF'
{
  "mcpServers": {
    "time": { "command": "uvx", "args": ["mcp-server-time", "--local-timezone=Asia/Shanghai"] },
    "web-search-prime": { "type": "http", "url": "https://open.bigmodel.cn/api/mcp/web_search_prime/mcp", "headers": { "Authorization": "Bearer your_zhipu_api_key" } }
  }
}
EOF
# 确认 README/SKILL 文档口径：Kimi 复用此文件，无需第二份配置
grep -n "Kimi Code 原生读取项目根" /home/michaelche/workspace/github/Cadence-skills/cadence-init/skills/mcp-configuration/SKILL.md
grep -n "直接读取项目根目录" /home/michaelche/workspace/github/Cadence-skills/cadence-init/skills/mcp-configuration/SKILL.md
```
预期：mcp-configuration SKILL.md 存在 Kimi 复用 `.mcp.json` 的口径说明；临时项目无需生成 `.kimi-code/mcp.json`。

- [ ] **Step 5: 清理临时目录并核对提交历史**

```bash
rm -rf /tmp/kimi-e2e /tmp/kimi-incremental /tmp/openspec-repo
cd /home/michaelche/workspace/github/Cadence-skills
git log --oneline -6
git status --short
```
预期：5 个功能提交（Task 1–5）按序出现在 `git log`；`git status` 干净（无未提交改动；`openspec/changes/support-kimi-code/` 为本 change 规划产物，按仓库流程在归档前保留）。

---

## 验收对照（spec → task）

| spec 需求（kimi-code-support / init-skill-sequencing delta） | 覆盖 Task |
|---|---|
| OpenSpec 初始化包含 kimi 工具（四客户端 init、增量补齐、就绪判定、验证命令） | Task 1、Task 6 Step 1–2 |
| Superpowers 说明 kimi 消费方式（不加层、`~/.agents/skills` 覆盖） | Task 2 |
| MCP 配置说明 kimi 消费方式（复用根目录 `.mcp.json`、不生成副本、gitignore 不加条目） | Task 3、Task 6 Step 4 |
| 项目类型扫描剪枝 kimi 目录（PRUNE_DIRS + find 块双向一致） | Task 4、Task 6 Step 3 |
| README 与文档四客户端表述 | Task 5 |
| init-skill-sequencing：完成门槛/增量补齐/硬门槛/README 口径四客户端 | Task 1、Task 5 |
