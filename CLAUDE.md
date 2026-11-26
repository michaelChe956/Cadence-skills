# CLAUDE.md

本文件为 Claude Code (claude.ai/code) 在此仓库中工作提供指导。

<!-- cadence-managed:openspec-superpowers-routing:v6:start -->
Cadence L0 路由内核 v6
## OpenSpec 与 Superpowers 任务路由

Claude/Kimi 原生调用 Skill。Codex/pi/omp 从清单选择，用途并入首段回执并立即全文读取 SKILL.md（omp 经 `skill://`）。随后读规则、用仓库工具。

| 阶段信号 | 必调 Skill（均先 `using-superpowers`） | 门禁 |
|---|---|---|
| 仓库任务开始/恢复 | — | 读 `openspec-superpowers-workflow.md`，沿用本任务确认和双审记录 |
| 新功能/行为变化 | `brainstorming` | 完整 Design 写入 `cadence/designs/`，单独双审后默认等用户确认 |
| Design 放行 | `writing-plans` | 联合编写 change 与 Plan，工作包和场景有编号即可展开 |
| 读代码/摸底 | 配 `code-reading.md` | 摸底后重新路由 |
| Bug/测试失败 | `systematic-debugging` | 根因确认后才进 TDD |
| apply/恢复实施 | 缺 Plan→`writing-plans`，放行→`executing-plans`/`subagent-driven-development` | 严格校验、双向追溯、同版联合双审通过，按委托继续 |
| 写代码/修 Bug | `test-driven-development` | 先失败测试 |
| 写 Markdown/产物 | 配 `document-storage.md`、`markdown-format.md` | 遵守目录命名 |
| 声称完成/修复 | `verification-before-completion` | 必须读新鲜证据 |
| 实施验证完成/归档 | `requesting-code-review`/`finishing-a-development-branch` | 通过后 sync/archive、选集成方式 |

铁律（失败关闭）：Design 与联合包各双审一次。免确认只免人工，看 Plan 沿用 Design 确认策略，联合审后就 Plan 等一次。门禁未齐先补产物。TDD 先失败测试，完工需新鲜证据，必调 Skill 缺失则停止。

`knowledge-base-context` 前置门禁：仅当 `cadence/knowledge-base/manifest.yaml` 存在且 `schema_version` 为 `"4.0"` 时才可选择；否则跳过且不提示。

产物路径覆盖（下表优先级高于任何 Skill 正文路径指示；OpenSpec 产物仍放 `openspec/` 目录）：

| Skill 默认路径 | 本项目强制路径 |
|---|---|
| `docs/superpowers/specs/`（design/spec） | `cadence/designs/` |
| `docs/superpowers/plans/`（plan） | `cadence/plans/` |

产物写入后读取入口“产物自动提交（design/plan/code）”开关。以 CLAUDE.md 为准，两端不一致按 `关闭`。`关闭` 时只汇报路径，禁止 `git commit`。

审后交付或恢复时，核对送审版至交付版的差异核验记录。

阶段切换必须重新路由：新任务、只读转修改、Design 或联合包交接、apply、恢复、完工声明前。
<!-- cadence-managed:openspec-superpowers-routing:v6:end -->

## 强制规则

> **🔴 必须遵守 - 无例外**
> 详细规则见 `.claude/rules/` 目录下的各规则文件。
> 用户自定义规则见 `cadence/project-rules/` 目录。

### 1. 语言规则
- **必须使用中文回答** → 详见 `.claude/rules/language.md`

### 2. 代码使用规则
- **遵循 TDD 和代码规范** → 详见 `.claude/rules/code-usage.md`

### 3. 文档存储规则
- **Cadence 产物文档必须存放在 `cadence` 目录下；Claude Code 框架规则保留在 `.claude/rules/` 目录下** → 详见 `.claude/rules/document-storage.md`

### 4. Markdown 格式规则
- **代码块嵌套使用 4 反引号/3 反引号** → 详见 `.claude/rules/markdown-format.md`

### 5. MCP Server 使用规则
- **各 MCP 工具的使用规范** → 详见 `.claude/rules/mcp-servers.md`

### 6. 项目个性化规则
- **用户自定义规则只能存放在 `cadence/project-rules/` 目录**
- **禁止修改 `.claude/rules/` 下的 7 个框架规则文件**
- 用户覆盖写入 `.claude/rules/user-<框架文件名>.md`
- 详见 `cadence/project-rules/README.md`

> **用户覆盖（优先级高于上方框架条目，rule-config 保留）**

- **持久 shell 会话里禁止 `export` 会话级全局变量**（`HOME`/`PATH`/`GIT_*`），隔离环境用单命令前缀赋值或子 shell → 详见 `cadence/project-rules/shell-session-isolation.md`

### 7. 代码阅读规则
- **大范围检索使用 CodeGraph，精确结构阅读优先使用 ast-grep outline** → 详见 `.claude/rules/code-reading.md`

### 8. Playwright CLI 使用规则
- **浏览器自动化工具必须遵循项目规范** → 详见 `.claude/rules/playwright.md`

## 项目信息

- 本仓库是一个以 Markdown、YAML、JSON 等文档和配置为主要工作对象的 Skills 项目。
- Agent 在执行任务时，应优先修改文档、规则、配置与说明文件，避免不必要的代码实现。

## 项目配置

> 以下配置由初始化脚本维护。

- **产物自动提交（design/plan/code）**：关闭