# 计划文档：pre-check 与 rule-config 增量支持

**日期**: 2026-06-26
**版本**: v1.0
**目标分支**: feat-b-0626
**关联文档**: `cadence/plans/2026-06-26_计划文档_ast-grep集成与代码阅读规则配置_v1.0.md`

---

## 背景

`pre-check` 与 `rule-config` 是 Cadence 初始化流程中的两个核心命令：

- `pre-check`：检查并安装项目所需工具（npx、uvx、serena、playwright-cli、ast-grep 等）。
- `rule-config`：为用户项目创建 `.claude/rules/` 规则文件，并在 `CLAUDE.md` / `AGENTS.md` 中写入规则摘要引用。

随着框架持续迭代，这两个命令会不断增加新的检查项和规则。如果它们只支持“首次全量初始化”，老项目在新版框架发布后将无法平滑升级。因此需要明确并补全它们的**增量支持**策略。

## 目标

1. 明确 `pre-check` 的增量运行策略：重复运行只补齐缺失项，不破坏已配置环境。
2. 明确 `rule-config` 的增量运行策略：重复运行只新增/更新缺失的规则文件和摘要引用，不重复写入或破坏已有内容。
3. 在两个命令的文档中补充“增量运行”说明，确保执行者和用户都能预期行为。

## 当前状态

### pre-check

- 当前流程是“检查 → 安装 → 验证”模式，天然具备幂等性。
- 但文档中没有明确说明“可以重复运行”“只补装缺失工具”。

### rule-config

- 当前文档主要面向首次初始化，未明确以下场景：
  - `.claude/rules/` 已存在时是否覆盖？
  - `CLAUDE.md` / `AGENTS.md` 中已有规则摘要时如何追加新规则？
  - 可选规则（代码阅读、Playwright）再次运行时是重新询问还是保持原选择？

## 设计详情

### 1. pre-check 增量策略

**核心原则**：幂等检查，只补缺失，不重复安装已存在工具。

#### 1.1 增量行为

| 场景 | 行为 |
|------|------|
| 工具已安装 | 报告已安装，跳过安装步骤 |
| 工具未安装 | 自动安装，安装后验证 |
| 工具版本过旧 | 当前版本不强制升级，仅报告当前版本；如需升级，后续由专门命令处理 |
| 重复运行 | 每个工具独立检查，只处理缺失项 |

#### 1.2 文档补充

在 `cadence-init/commands/pre-check.md` 和 `cadence-init/skills/pre-check/SKILL.md` 中增加“增量运行”章节：

```markdown
## 增量运行

`/pre-check` 支持重复执行。已安装的工具会直接跳过，只会为缺失的工具执行安装。

典型场景：
- 新增 `ast-grep` 后，老项目重新运行 `/pre-check` 会自动补齐 ast-grep，而不会影响已有的 npx、uvx、serena、playwright-cli 配置。
```

### 2. rule-config 增量策略

**核心原则**：只新增缺失项，不覆盖用户已确认的内容；更新前必须告知用户变更范围。

#### 2.1 规则文件增量

对于 `.claude/rules/` 下的每个规则文件：

| 场景 | 行为 |
|------|------|
| 文件不存在 | 从模板根路径读取并创建 |
| 文件已存在 | **不自动覆盖**，向用户报告差异并询问是否更新 |
| 新增规则模板（如新增的 `code-reading.md`） | 自动检测到缺失，询问用户是否需要新增 |

**建议命令**：

```bash
# 检查目标规则文件是否存在
for rule in README.md language.md document-storage.md markdown-format.md serena-usage.md mcp-servers.md code-usage.md code-reading.md playwright.md; do
  if [ -e ".claude/rules/$rule" ]; then
    echo "已存在: .claude/rules/$rule"
  else
    echo "缺失: .claude/rules/$rule"
  fi
done
```

#### 2.2 CLAUDE.md / AGENTS.md 摘要增量

写入前应先读取现有文件，识别缺失的规则摘要行：

| 场景 | 行为 |
|------|------|
| 摘要行已存在 | 跳过，不重复写入 |
| 摘要行缺失 | 追加到对应章节 |
| 规则编号冲突 | 按最新规范重新编号并提示用户 |

**实现建议**：

- 使用 `grep` 或文本匹配检查每条规则摘要是否已存在。
- 如果 `CLAUDE.md` 中没有 `## 强制规则` 章节，按首次初始化流程创建。
- 如果已有章节，仅追加缺失的 `### N. xxx` 条目。

#### 2.3 可选规则增量处理

对于代码阅读规则、Playwright 规则等可选步骤：

| 场景 | 行为 |
|------|------|
| 用户此前已启用 | 检查规则文件是否存在，缺失则补齐；不再重复询问 |
| 用户此前未启用 | 作为新增可选项再次询问 |
| 无法判断用户历史选择 | 默认按新增项询问 |

**判断依据**：

- 检查 `.claude/rules/code-reading.md` 或 `.claude/rules/playwright.md` 是否存在。
- 检查 `CLAUDE.md` / `AGENTS.md` 中是否已有对应规则摘要。

#### 2.4 文档补充

在 `cadence-init/commands/rule-config.md` 中新增“增量运行”章节：

```markdown
## 增量运行

`/cadence:init:rule-config` 支持在已初始化项目中重复执行：

- 已存在的规则文件不会自动覆盖，除非用户明确同意。
- `CLAUDE.md` / `AGENTS.md` 中已存在的规则摘要不会重复写入。
- 新增的框架规则（如 `code-reading.md`）会被检测为缺失项，询问用户是否添加。
- 可选规则（代码阅读、Playwright）根据当前项目是否已启用决定行为。

建议在新版 Cadence 发布或框架规则更新后重新运行 `/cadence:init:rule-config`，以补齐新增规则。
```

## 修改范围

| 操作 | 文件路径 |
|---|---|
| 修改 | `cadence-init/skills/pre-check/SKILL.md` |
| 修改 | `cadence-init/commands/pre-check.md` |
| 修改 | `cadence-init/commands/rule-config.md` |

## 实施步骤

1. 在 `pre-check` 两份文档中增加“增量运行”说明。
2. 在 `rule-config.md` 中增加“增量运行”说明，细化规则文件、摘要引用、可选规则的增量处理逻辑。
3. 验证新增章节与现有流程不冲突。
4. 提交并推送。

## 与 ast-grep 集成的关系

本次 ast-grep 集成完成后，`pre-check` 会新增 ast-grep 检查项，`rule-config` 会新增 `code-reading.md` 规则。增量支持策略确保：

- 老项目重新运行 `/pre-check` 时，只会自动安装 ast-grep，不影响其他工具。
- 老项目重新运行 `/cadence:init:rule-config` 时，会被询问是否新增 `code-reading.md` 规则，而不会因为覆盖已有规则文件造成意外变更。
