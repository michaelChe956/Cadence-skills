# CLAUDE.md

本文件为 Claude Code (claude.ai/code) 在此仓库中工作提供指导。

<!-- cadence-managed:openspec-superpowers-routing:v1:start -->
## OpenSpec 与 Superpowers 任务路由（强制）

> 仅当任务需要仓库读取、命令、OpenSpec、写入、完成声明或其他仓库操作时，必须先路由、再读规则、再调 Skill、最后执行。

| 任务或阶段信号 | 必读规则 | 必调 Superpowers Skill | 门禁 |
|---|---|---|---|
| 会话开始且任务需要仓库操作，或 resume/clear/compact 后恢复仓库任务 | `openspec-superpowers-workflow.md` | `using-superpowers` | 第一段先输出完整路由回执，回执前禁止仓库勘察 |
| 新功能、行为变化、方案讨论 | 协作规则；产物相关文档规则 | `brainstorming` | 设计确认后写入 OpenSpec |
| OpenSpec 书面契约获批 | 协作规则、文档规则 | `writing-plans` | Plan 写入 `cadence/plans/` |
| 读代码、架构摸底、影响面分析 | `code-reading.md` | 按任务选择 | 摸底完成后重新路由 |
| Bug、测试失败、异常行为 | `code-usage.md` | `systematic-debugging` | 根因确认后才进入 TDD |
| `/opsx:apply` 或恢复实施 | 协作规则、代码规则 | `executing-plans` 或 `subagent-driven-development` | 无已确认 Plan 则停止 |
| 写代码、修 Bug、重构 | `code-usage.md` | `test-driven-development` | 先失败测试，后实现 |
| 写 Markdown 或 Cadence 产物 | `document-storage.md`、`markdown-format.md` | 按阶段选择 | 遵守目录和命名 |
| 联网、图片、浏览器自动化 | `mcp-servers.md` 或专项规则 | 按任务选择 | 不加载无关工具正文 |
| 声称完成、修复或通过 | 协作规则 | `verification-before-completion` | 必须读取新鲜证据 |
| 实施与验证均完成 | 协作规则 | `requesting-code-review` | 审查通过后勾选工作包并 sync/archive |
| OpenSpec 已归档 | 协作规则 | `finishing-a-development-branch` | 选择分支集成方式 |

阶段切换必须重新路由：新仓库任务、讨论、分析或只读调查转为创建/修改文件、契约获批、apply 前、resume/clear/compact 后、完工声明前。
需要仓库读取、命令、OpenSpec、写入、完成声明或其他仓库操作时，第一段响应必须先完整输出：`工作流路由：阶段=...；Change=...；Plan=...；必调 Skill=...`；回执前禁止读取、搜索、列出或推断仓库文件、目录、change 状态或 Plan。
纯概念问答必须直接回答，不输出路由回执，不加载无关规则或 Skill 正文；一旦转为仓库操作，必须先重新路由。
需要仓库勘察的新功能或行为变化，回执必须先于 change、Plan、目录或文件勘察，必调 Skill 至少列出 `using-superpowers`、`brainstorming`；澄清问题不得替代回执。
失败关闭：必调 Skill 未加载则停止；强制 OpenSpec 未确认则不规划；已有 change 无 Plan 则不实施；契约变化先更新 OpenSpec；无验证证据不得声称完成。
<!-- cadence-managed:openspec-superpowers-routing:v1:end -->

## 强制规则

> **🔴 必须遵守 - 无例外**
> 详细规则见 `.claude/rules/` 目录下的各规则文件。
> 用户自定义规则见 `cadence/project-rules/` 目录。

### 1. 语言规则
- **必须使用中文回答** → 详见 `.claude/rules/language.md`

### 2. 代码使用规则
- **非必要不编写代码**（Skills 项目特殊规定） → 详见 `.claude/rules/code-usage.md`

### 3. 文档存储规则
- **Cadence 产物文档必须存放在 `cadence` 目录下；Claude Code 框架规则保留在 `.claude/rules` 目录下** → 详见 `.claude/rules/document-storage.md`

### 4. Markdown 格式规则
- **代码块嵌套使用 4 反引号/3 反引号** → 详见 `.claude/rules/markdown-format.md`

### 5. MCP Server 使用规则
- **各 MCP 工具的使用规范** → 详见 `.claude/rules/mcp-servers.md`

### 6. 项目个性化规则（强制规则）
- **用户自定义规则只能存放在 `cadence/project-rules/` 目录**
- 禁止在 `rules/` 目录中添加用户自定义规则
- 禁止直接修改 `rules/` 目录下的框架内置规则文件
- 详见 `cadence/project-rules/README.md`

### 7. Playwright CLI 使用规则
- **浏览器自动化工具规范** → 详见 `.claude/rules/playwright.md`

### 8. 代码阅读规则
- **大范围检索使用 CodeGraph，精确结构阅读优先使用 ast-grep outline** → 详见 `.claude/rules/code-reading.md`

## 项目信息
