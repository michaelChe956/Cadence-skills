# AGENTS.md

本文件为 Codex 及其他 AI Agents 在此仓库中工作提供指导。

<!-- cadence-managed:openspec-superpowers-routing:v2:start -->
## OpenSpec 与 Superpowers 任务路由（强制）

> 先通过客户端原生机制选择 `using-superpowers` 与当前阶段必调 Skill；首个用户可见段落输出路由回执；Skill 调用完成后才允许读取仓库规则或使用仓库工具。

| 任务或阶段信号 | 必读规则 | 必调 Superpowers Skill | 门禁 |
|---|---|---|---|
| 会话开始且任务需要仓库操作，或 resume/clear/compact 后恢复仓库任务 | `openspec-superpowers-workflow.md` | `using-superpowers` | 原生调用 Skill 后，第一段输出完整路由回执 |
| 新功能、行为变化、方案讨论 | 协作规则；产物相关文档规则 | `using-superpowers` → `brainstorming` | 设计确认后写入 OpenSpec |
| OpenSpec 书面契约获批 | 协作规则、文档规则 | `using-superpowers` → `writing-plans` | Plan 写入 `cadence/plans/` |
| 读代码、架构摸底、影响面分析 | `code-reading.md` | `using-superpowers` → 按任务选择 | 摸底完成后重新路由 |
| Bug、测试失败、异常行为 | `code-usage.md` | `using-superpowers` → `systematic-debugging` | 根因确认后才进入 TDD |
| `/opsx:apply` 或恢复实施 | 协作规则、代码规则 | 无 Plan：`using-superpowers` → `writing-plans`；有 Plan：→ `executing-plans` 或 `subagent-driven-development` | 无已确认 Plan 则停止 |
| 写代码、修 Bug、重构 | `code-usage.md` | `using-superpowers` → `test-driven-development` | 先失败测试，后实现 |
| 写 Markdown 或 Cadence 产物 | `document-storage.md`、`markdown-format.md` | `using-superpowers` → 按阶段选择 | 遵守目录和命名 |
| 联网、图片、浏览器自动化 | `mcp-servers.md` 或专项规则 | `using-superpowers` → 按任务选择 | 不加载无关工具正文 |
| 声称完成、修复或通过 | 协作规则 | `using-superpowers` → `verification-before-completion` | 必须读取新鲜证据 |
| 实施与验证均完成 | 协作规则 | `using-superpowers` → `requesting-code-review` | 审查通过后勾选工作包并 sync/archive |
| OpenSpec 已归档 | 协作规则 | `using-superpowers` → `finishing-a-development-branch` | 选择分支集成方式 |

`knowledge-base-context` 选择前置门禁：仅当只读确认 `cadence/knowledge-base/manifest.yaml` 存在且 `schema_version` 为 `"4.0"` 时才可选择；Manifest 缺失或版本不符时不得选择、调用或读取该 Skill，不输出知识库相关提示，按普通流程继续。

阶段切换必须重新路由：新仓库任务、讨论、分析或只读调查转为创建/修改文件、契约获批、apply 前、resume/clear/compact 后、完工声明前。
需要仓库操作时：Claude/Kimi 必须把全部 Skill 调用及失败重试作为连续工具事件；首个调用前、事件之间和重试前均保持用户可见输出静默，禁止输出“我先调用 Skill”等引导句；随后第一段输出 `工作流路由：阶段=...；Change=...；Plan=...；必调 Skill=...`。Codex 先显式选择 Skill，将用途并入首段回执，随后立即全文读取 Skill。pi 与 Codex 同类：从 Skill 清单显式选择 Skill，将用途并入首段回执，随后立即全文读取对应 SKILL.md 作为调用，Skill 未读完前不得读取仓库规则或使用仓库工具。Skill 调用完成后才读取仓库规则和使用仓库工具。
纯概念问答只调用全局 `using-superpowers` 后直接回答，不输出仓库路由回执，不加载仓库规则或其他无关 Skill；Codex/pi 可先输出 Skill 用途公告。一旦转为仓库操作，必须重新路由。
需要仓库勘察的新功能或行为变化，必须先原生调用 `using-superpowers`、`brainstorming`，再输出回执；回执必须先于 change、Plan、目录或文件勘察，澄清问题不得替代回执。
Claude/Kimi 的 Skill 参数使用表中不带命名空间的原名；pi 以全文读取对应 SKILL.md 作为 Skill 调用；调用失败必须按客户端已注册清单重试，未成功加载则失败关闭。
失败关闭本身也属于当前阶段动作，不能用“只判断/只拒绝”豁免 Skill：无 Plan 时先调用 `using-superpowers`、`writing-plans` 再拒绝 apply；即使禁止运行验证命令，也必须先调用 `using-superpowers`、`verification-before-completion` 加载验证纪律，再拒绝无证据完成声明；其他必调 Skill 未加载则停止。
<!-- cadence-managed:openspec-superpowers-routing:v2:end -->

## 强制规则

> **必须遵守 - 无例外**
> 详细规则见 `.claude/rules/` 目录下的各规则文件。
> 用户自定义规则见 `cadence/project-rules/` 目录。

### 1. 语言规则
- **必须使用中文回答** → 详见 `.claude/rules/language.md`

### 2. 代码使用规则
- **非必要不编写代码**（Skills 项目特殊规定） → 详见 `.claude/rules/code-usage.md`
- 如确实需要编写脚本、验证工具或自动化代码，必须先说明必要性与用途。

### 3. 文档存储规则
- **Cadence 产物文档必须存放在 `cadence` 目录下；Claude Code 框架规则保留在 `.claude/rules` 目录下** → 详见 `.claude/rules/document-storage.md`
- 本文件 `AGENTS.md` 作为仓库根目录的代理入口说明文件，按用户要求放置于项目根目录。

### 4. Markdown 格式规则
- **Markdown 编写必须遵循项目格式规范** → 详见 `.claude/rules/markdown-format.md`

### 5. MCP Server 与工具使用规则
- **各 MCP 工具及相关自动化工具的使用必须遵循项目规范** → 详见 `.claude/rules/mcp-servers.md`

### 6. 项目个性化规则
- **用户自定义规则只能存放在 `cadence/project-rules/` 目录**
- 禁止在 `.claude/rules/` 目录中添加用户自定义规则
- 禁止直接修改 `.claude/rules/` 目录下的框架内置规则文件
- 详见 `cadence/project-rules/README.md`

### 7. Playwright CLI 使用规则
- **浏览器自动化工具必须遵循项目规范** → 详见 `.claude/rules/playwright.md`

### 8. 代码阅读规则
- **大范围检索使用 CodeGraph，精确结构阅读优先使用 ast-grep outline** → 详见 `.claude/rules/code-reading.md`

## 与 CLAUDE.md 的关系

- 用户在当前任务中的明确指令优先级最高。
- `CLAUDE.md` 面向 Claude Code。
- `AGENTS.md` 面向 Codex 及其他通用 AI Agents。
- 两者如有表述差异，应优先遵循本仓库中的实际规则文件，即 `.claude/rules/` 与 `cadence/project-rules/`。

## 项目信息

- 本仓库是一个以 Markdown、YAML、JSON 等文档和配置为主要工作对象的 Skills 项目。
- Agent 在执行任务时，应优先修改文档、规则、配置与说明文件，避免不必要的代码实现。

## Agent 执行要求

- 开始任务前，应先读取 `CLAUDE.md`，并按需查看 `.claude/rules/` 与 `cadence/project-rules/` 中的相关规则文件。
- 修改文档时，应优先沿用现有目录结构、命名规范与 Markdown 格式约定。
- 未经用户明确要求，不得直接修改 `.claude/rules/` 目录下的框架内置规则文件。
