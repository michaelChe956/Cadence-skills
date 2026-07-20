## Context

`/pre-check` 已在目标业务项目中安装 OpenSpec 与 Superpowers，Cadence 的五个初始化命令也已生成项目入口、规则目录和 OpenSpec 配置。本变更不解决安装问题，而是解决规则发现和流程协同问题。

当前入口文件只列出规则分类并要求 Agent“按需查看”。这对 Claude Code、Kimi Code 等不稳定执行渐进加载的 Agent 不够明确：它们可能在开始写代码前没有读取代码规则，在方案设计前没有调用 brainstorming，或者直接执行 `/opsx:apply` 而没有 Superpowers Plan。仅把详细规则放在独立文件中并不能保证 Agent 知道何时加载它。

本设计接受一个现实边界：纯规则无法像外部状态机一样绝对控制模型，但可以通过常驻短指令、阶段重复门禁、契约冗余和失败关闭，把“依赖 Agent 自觉发现”改为“多个必经位置重复给出同一约束”。

## Goals / Non-Goals

**Goals:**

- 明确 OpenSpec 与 Superpowers 的职责边界和唯一推荐协作顺序。
- 让关键路由在 `CLAUDE.md` 与 `AGENTS.md` 中常驻，而详细规则按触发加载。
- 在新任务、阶段切换、上下文恢复和完工前强制重新路由，降低一次漏载导致后续全程失控的概率。
- 让 OpenSpec 产物保持契约粒度，让 Superpowers Plan 保持实施粒度，并建立双向可追溯关系。
- 让已完成 Cadence 初始化的业务项目通过重新运行 `rule-config` 获得新版规则，不覆盖项目自定义内容。
- 为 Claude Code、Kimi Code 与 Codex 提供语义等价、可验证的规则行为。

**Non-Goals:**

- 不安装、升级或检测 OpenSpec 与 Superpowers；该职责属于 `/pre-check`。
- 不使用 `cadence-workflow`，不新增 Hook、插件、守护进程或“是否读过文件”的状态机。
- 不修改 OpenSpec 或 Superpowers 上游 Skill 的实现。
- 不要求所有任务都创建 OpenSpec change 或详细 Plan。
- 不拆分现有 MCP 规则，不重写无关规则和 Skill。
- 不让 OpenSpec 的默认命令替代 Superpowers brainstorming、writing-plans、TDD 或验证流程。

## Decisions

### 1. OpenSpec 管契约，Superpowers 管行为

两者不是串联的两套完整流程，而是同一工作流的两个正交层面：

| 关注点 | 权威来源 |
|---|---|
| Why、目标、范围、非目标 | OpenSpec proposal |
| 架构决策、边界、权衡 | OpenSpec design |
| MUST/SHALL 要求与验收场景 | OpenSpec specs |
| 可跟踪的高层工作包 | OpenSpec tasks |
| 探索需求与澄清方案 | Superpowers brainstorming |
| 精确文件、步骤、命令、测试与提交策略 | Superpowers writing-plans 生成的 Plan |
| 调试、TDD、执行、审查与验证方法 | 对应 Superpowers Skills |
| 分支合并、PR 或清理选择 | Superpowers finishing-a-development-branch |

OpenSpec artifacts 是 brainstorming 确认结果的持久化契约。`openspec-propose` 不作为 brainstorming 的替代步骤，也不允许跳过用户对设计和书面契约的审阅。

### 2. 采用 L0、L1、L2 三层防漏载结构

```text
┌──────────────────────────────────────────────────────┐
│ L0 常驻路由内核：CLAUDE.md / AGENTS.md               │
│ 任务信号、阶段重路由、路由回执、失败关闭             │
└───────────────────────┬──────────────────────────────┘
                        │ 命中后加载
                        ▼
┌──────────────────────────────────────────────────────┐
│ L1 完整协作规则：                                    │
│ .claude/rules/openspec-superpowers-workflow.md       │
│ 职责、流程、冲突裁决、豁免、契约变更与完成顺序       │
└───────────────────────┬──────────────────────────────┘
                        │ 生成和约束
                        ▼
┌──────────────────────────────────────────────────────┐
│ L2 OpenSpec 契约冗余：openspec/config.yaml + artifacts│
│ artifact 边界、高层 tasks、Plan 门禁与可追溯要求     │
└──────────────────────────────────────────────────────┘
```

L0 解决“Agent 不知道该加载什么”，L1 解决“加载后不知道完整流程”，L2 解决“Agent 从 `/opsx:*` 直接进入时缺少协作边界”。三层有意重复少量关键约束，详细内容只在 L1 和对应 Skill 中出现。

### 3. L0 必须直接内嵌动作型路由，不能只放文件链接

`rule-config` 在 `CLAUDE.md` 与 `AGENTS.md` 中维护约 20～30 行的版本化受管区块。建议语义如下，具体措辞可按客户端适配，但不得减少门禁：

| 任务或阶段信号 | 先读规则 | 必调 Superpowers Skill | 后续门禁 |
|---|---|---|---|
| 会话开始、新任务、resume/clear/compact 后 | 协作规则 | `using-superpowers` | 输出路由回执后再使用仓库工具 |
| 新功能、行为变更、方案讨论 | 协作规则；需要产物时读文档规则 | `brainstorming` | 设计确认后持久化到 OpenSpec |
| OpenSpec 书面契约获批 | 协作规则、文档规则 | `writing-plans` | Plan 必须写入 `cadence/plans/` |
| 读代码、架构摸底、影响面分析 | `code-reading.md` | 按任务需要选择 | 完成摸底后重新判断当前阶段 |
| Bug、测试失败、异常行为 | `code-usage.md` | `systematic-debugging` | 确认根因后才进入 TDD 与修改 |
| `/opsx:apply` 或恢复实施 | 协作规则、代码规则 | `executing-plans` 或 `subagent-driven-development` | 无已确认 Plan 则停止实施 |
| 写代码、修 Bug、重构 | `code-usage.md` | `test-driven-development` | 先写失败测试，再写实现 |
| 写 Markdown 或 Cadence 产物 | `document-storage.md`、`markdown-format.md` | 按当前阶段选择 | 遵守目录和命名规则 |
| 联网搜索、图片理解、浏览器自动化 | `mcp-servers.md` 或专项规则 | 按任务需要选择 | 不加载无关工具正文 |
| 声称完成、修复或通过 | 协作规则 | `verification-before-completion` | 必须读取新鲜验证证据 |
| 实施与验证均完成 | 协作规则 | `requesting-code-review` | 审查通过后勾选工作包并执行 OpenSpec sync/archive |
| OpenSpec 已归档，准备集成分支 | 协作规则 | `finishing-a-development-branch` | 选择合并、PR、保留或清理方式 |

对于需要读取仓库、创建或修改文件、调用 `/opsx:*`、执行命令或声称完成的任务，Agent 在首次工具调用前必须输出一行路由回执：

```text
工作流路由：阶段=<探索|契约|计划|实施|验证|收尾>；Change=<名称或无>；Plan=<路径或无>；必调 Skill=<名称>
```

纯概念问答不要求输出回执，也不应为了满足路由而加载无关规则。

### 4. 阶段切换必须重新路由，并采用失败关闭

以下时点不能沿用之前的隐含判断，必须重新检查 L0：

1. 新会话或新任务开始。
2. 从讨论、分析转为创建或修改文件。
3. brainstorming 设计确认并准备写入 OpenSpec。
4. OpenSpec 书面契约获批并准备规划。
5. `/opsx:apply`、恢复实施或切换工作包之前。
6. resume、clear、compact 或上下文明显丢失之后。
7. 声称完成、修复、通过或准备归档之前。

失败关闭规则如下：

- 必调 Skill 未加载或不可用时停止当前阶段，报告缺失项，不得用普通回答模拟 Skill。
- 达到 OpenSpec 强制阈值但 change 未确认时，不得进入实施规划。
- 已存在 OpenSpec change 的多步实施没有已确认 Plan 时，不得编辑实现文件或执行 `/opsx:apply` 的工作包。
- 发现实施将改变范围、架构边界或验收标准时，停止实施，先更新 OpenSpec 并重新获得确认，再更新 Plan。
- 没有与完成声明对应的新鲜验证证据时，不得声称完成、修复或测试通过。

### 5. 使用明确阈值避免流程过重

| 任务类型 | OpenSpec | Superpowers |
|---|---|---|
| 纯问答、解释、只读调查 | 不要求 | `using-superpowers`；按信号加载阅读或调试 Skill |
| 错别字、排版、无语义文档修正 | 不要求 | 按文档规则执行；完成前验证 |
| 恢复已有明确契约的小型 Bug | 默认不要求新 change | `systematic-debugging` → TDD → 验证 |
| 新功能、行为变化、公共接口或数据变化 | 必须 | brainstorming → writing-plans → 实施与验证 |
| 跨模块重构、架构或验收边界变化 | 必须 | brainstorming → writing-plans → 实施与验证 |
| 已存在 OpenSpec change 的后续实施 | 使用现有 change | 必须先有与 change 对齐的 Plan |

用户可以明确要求对某个轻量任务使用 OpenSpec；但 Agent 不得自行豁免已经达到强制阈值的变更。无法判断是否达到阈值时，停止并向用户说明分歧点。

### 6. OpenSpec 与 Superpowers 的标准流程

```text
using-superpowers
        │
        ▼
brainstorming ──用户确认设计──▶ 写入 OpenSpec proposal/design/specs/tasks
                                      │
                                      ▼
                              用户审阅书面契约
                                      │
                                      ▼
                              writing-plans
                                      │
                                      ▼
                       cadence/plans/<实施计划>.md
                                      │
                     ┌────────────────┴────────────────┐
                     ▼                                 ▼
             systematic-debugging             executing-plans 或
              （Bug/异常时）                subagent-driven-development
                     │                                 │
                     └──────────────┬──────────────────┘
                                    ▼
                         test-driven-development
                                    │
                                    ▼
                    requesting-code-review + verification
                                    │
                                    ▼
                 勾选 OpenSpec 工作包 → sync/archive → 分支收尾
```

brainstorming 已确认的内容必须落入 OpenSpec，而不是只保留在聊天记录。OpenSpec `tasks.md` 只保存高层工作包；Plan 保存精确文件、操作步骤、命令、测试和提交建议。Plan 必须引用 OpenSpec change、工作包编号和相关 requirement，且只能展开契约，不能改写契约。

### 7. L1 是完整协作规则的框架规范源

新增规范源：

```text
cadence-init/skills/rule-config/references/rules/
└── openspec-superpowers-workflow.md
```

`rule-config` 将它生成到业务项目：

```text
.claude/rules/openspec-superpowers-workflow.md
```

该规则包含职责边界、完整流程、阶段门禁、冲突裁决、OpenSpec 与 Plan 映射、实施中契约变更、完成归档顺序和轻量豁免。`CLAUDE.md`、`AGENTS.md` 中的 L0 只保留强制索引，不复制长篇解释。

框架规范源先修改，当前仓库的 `.claude/rules/` 仅作为生成副本同步；不得把框架变更只写入当前副本。

### 8. L2 使用 OpenSpec 支持的配置点，不虚构 `rules.apply`

在 `openspec/config.yaml` 中：

- `context` 重复 OpenSpec 管契约、Superpowers 管行为，以及 Plan 不能重定义契约的原则。
- `rules.proposal` 强制记录目标、范围与非目标。
- `rules.design` 强制持久化 brainstorming 已确认的架构与边界决策。
- `rules.specs` 强制使用可验收的 MUST/SHALL 场景。
- `rules.tasks` 强制只生成高层工作包，并要求可映射到后续 Plan。

经当前 OpenSpec 1.3.1 行为确认，`apply` 是特殊命令而不是 schema artifact，`config.yaml` 不支持有效的 `rules.apply`。因此不得添加该字段。直接 `/opsx:apply` 的门禁由 L0、L1，以及 apply 必须读取的 `design.md` 与 `tasks.md` 中的 Plan 约束共同提供。

### 9. 冲突按关注点裁决

| 冲突类型 | 处理方式 |
|---|---|
| 范围、需求、验收冲突 | 以 OpenSpec proposal/specs 为准 |
| 架构边界冲突 | 以 OpenSpec design 为准 |
| 文件、命令、测试和实施顺序冲突 | 以已确认的 Superpowers Plan 为准，但不得越过 OpenSpec |
| 调试、TDD、审查和验证方法冲突 | 以对应 Superpowers Skill 为准 |
| OpenSpec 默认命令提示与项目协作规则冲突 | 以项目协作规则为准 |
| 用户当前明确指令与既有产物冲突 | 停止并指出需要更新的权威产物，不能静默覆盖 |
| 无法判断冲突类别 | 停止并询问用户 |

### 10. 版本化受管内容支持已有项目升级

`rule-config` 为 L0 使用稳定开始标记、结束标记和版本号，只替换受管区块，保留区块外项目内容。L1 文件属于 Cadence 框架规则，包含框架版本标识；识别到旧版框架文件时更新到新版，发现无法识别的本地改动时先备份并报告，不静默覆盖。

已执行过五个初始化命令的业务项目在获得新版 Cadence 规则后，只需重新运行 `rule-config` 即可补齐或升级 L0、L1 和 OpenSpec 配置受管内容。该过程不重复安装 OpenSpec 或 Superpowers。

### 11. 验证关注路由结果，不假装证明模型“真的读过”

静态验证确认：

- L0 在 `CLAUDE.md` 与 `AGENTS.md` 中语义等价且版本一致。
- L0 引用的规则文件和 Superpowers Skill 名称存在。
- L1 规范源与当前生成副本一致。
- `openspec/config.yaml` 只使用有效 artifact 规则键。
- OpenSpec tasks 保持高层粒度，Plan 具有 change、task、requirement 映射。

场景验证至少覆盖 Claude Code、Kimi Code 与 Codex 的新功能、Bug、直接 apply、上下文恢复、纯问答和完工声明。验证记录 Agent 的路由回执、实际加载项、是否越过门禁和是否误加载无关正文。

## Risks / Trade-offs

- [纯规则不能提供运行时绝对强制] → 在入口、完整规则和 OpenSpec 产物三个必经位置冗余关键门禁，并对越过门禁采用明确的停止指令。
- [常驻路由过长会损害渐进式披露] → L0 只保留任务信号、阶段门禁和失败关闭，目标控制在约 20～30 行，不放正文和示例。
- [重复规则可能漂移] → L1 作为完整规范源，L0 作为受管索引，使用版本标识和静态一致性检查。
- [轻量豁免被 Agent 滥用] → 用任务类型表定义允许豁免的边界；新行为、公共契约和跨模块变化始终要求 OpenSpec。
- [OpenSpec 产物和 Plan 内容重复] → tasks 只写高层工作包，Plan 只写实施细节，通过编号引用而非复制全文。
- [不同客户端的 Skill 调用语法不同] → 允许平台语法适配，但要求任务信号、阶段顺序和失败关闭语义一致。

## Migration Plan

1. 先在 `cadence-init/skills/rule-config/references/rules/` 增加 L1 规范源，并在 `rule-config` 中定义 L0 受管区块和升级规则。
2. 为 `openspec/config.yaml` 定义公共上下文和 proposal、design、specs、tasks 的 artifact 规则模板。
3. 从规范源同步当前仓库的 `CLAUDE.md`、`AGENTS.md` 与 `.claude/rules/` 框架副本。
4. 更新相关说明，明确已初始化业务项目通过重新运行 `rule-config` 升级规则。
5. 执行静态检查和三客户端场景验证；验证通过后再发布给业务项目使用。

回滚时恢复上一版本 L0 受管区块、L1 框架规则和 OpenSpec 配置受管内容；区块外项目说明与 `cadence/project-rules/` 不受影响。

## Open Questions

- L0 最终文案需在实施计划阶段按实际入口模板压缩，目标是保持完整门禁的同时不超过约 30 行。
- 跨客户端场景验证先采用人工可审计记录；只有现有命令无法稳定完成静态检查时，才另行说明新增验证脚本的必要性。
