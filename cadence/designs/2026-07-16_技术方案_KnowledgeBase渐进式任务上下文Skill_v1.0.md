# KnowledgeBase 渐进式任务上下文 Skill 技术方案

## 1. 背景

现有 KnowledgeBase Skills 负责初始化、分析和增量维护项目知识，已经形成 Schema 3.0、稳定实体 ID、领域索引、关系矩阵、证据索引和待确认项。当前缺少一个独立的消费层：当用户通过自然语言提出需求澄清、设计、计划、编码、测试、评审或调试任务时，Coding Agent 仍需要自行决定读取哪些知识库文档和哪些源码，容易出现一次加载过多、遗漏关键关系、只信知识库或只看源码等问题。

新增 `knowledge-base-context` Skill，负责从用户任务出发，同时读取 KnowledgeBase 与当前源码，按任务需要渐进扩展知识范围，最终生成最小任务上下文包。

该 Skill 属于 `cadence-init`，与 `cadence-workflow` 没有依赖、调用或流程关系。它不执行需求、设计、计划、编码、测试、评审或调试，只为这些任务提供经过组织和校验的项目上下文。

## 2. 目标

- 支持 Claude Code 与 Codex 使用同一套 Skill 内容。
- 支持自然语言自动触发和显式手动触发。
- 固定支持需求澄清、Design、Plan、Coding、Testing、Review、Debug 七类任务画像。
- KnowledgeBase 与源码、DDL、配置作为同等重要的两条证据路径。
- 从用户任务种子开始逐层获取知识，不默认加载整个知识库或全仓源码。
- 输出可供任意下游 Agent 消费的最小任务上下文包。
- 默认只注入当前会话，用户明确要求时才保存任务快照。
- 识别 KnowledgeBase 与当前源码之间的冲突、漂移和证据缺口。

## 3. 非目标

- 不调用或依赖 `cadence-workflow` 中的任何 Skill、Command、Hook 或流程状态。
- 不规定用户必须按需求、设计、计划、编码、测试的顺序工作。
- 不生成需求文档、技术方案、实施计划、业务代码或测试代码。
- 不自动更新 KnowledgeBase；需要更新时只报告漂移并建议使用 `knowledge-base-update`。
- 不在 Manifest 缺失时回退成普通全仓分析。
- 不建立自定义画像、画像插件或运行时画像注册机制。
- 不自动持久化每次任务上下文，避免形成第二套易过期知识库。

## 4. 与现有 cadence-init 保持一致

### 4.1 Skill 目录

新增目录：

```text
cadence-init/skills/knowledge-base-context/
├── SKILL.md
├── agents/
│   └── openai.yaml
├── references/
│   ├── progressive-retrieval-guide.md
│   ├── task-profiles.md
│   └── demo.md
└── assets/
    └── task-context-template.md
```

职责划分：

- `SKILL.md`：触发条件、核心工作流、强制规则、停止条件和输出要求。
- `agents/openai.yaml`：Codex 展示信息和默认手动调用提示词。
- `progressive-retrieval-guide.md`：双轨读取、实体扩展、冲突处理和停止判断。
- `task-profiles.md`：七类固定画像的读取重点和输出字段。
- `demo.md`：一个综合任务上下文包案例。
- `task-context-template.md`：用户明确要求保存时使用的输出模板。

首版不增加脚本。任务画像识别、源码结构、工具可用性和项目形态差异较大，适合由 Skill 规则约束，而不是固化为脆弱脚本。

### 4.2 现有集成点

需要同步更新：

- `knowledge-base-overview/assets/knowledge-base-usage-template.md`：要求七类任务先使用 `knowledge-base-context` 获取上下文。
- `knowledge-base-overview/references/rules-integration-guide.md`：说明 Claude Code 与 Codex 的手动调用方式。
- `cadence-init/.claude-plugin/plugin.json`：描述中补充 KnowledgeBase 消费能力，并按仓库发布规则更新版本。

不新增显式 Skill 注册表。沿用当前插件对 `cadence-init/skills/*/SKILL.md` 的发现方式。

## 5. Claude Code 与 Codex 触发

### 5.1 自动触发

自动触发依赖 `SKILL.md` Frontmatter 中的 `description`，不依赖 Hook、Manifest 或 `cadence-workflow`。

建议描述：

```yaml
---
name: knowledge-base-context
description: "Use when 当前项目存在 Schema 3.0 KnowledgeBase，且用户正在进行需求澄清、功能或技术设计、实施计划、编码、测试、评审或调试，需要从 KnowledgeBase 与源码、DDL、配置中渐进获取任务相关上下文；也用于用户明确要求加载、获取或整理项目 KnowledgeBase 上下文。"
---
```

自然语言触发场景至少覆盖：

- “帮我澄清这个需求在当前系统中的边界。”
- “设计订单取消功能，需要结合现有系统。”
- “给这个改动制定实施计划。”
- “实现订单导出接口。”
- “补充这个接口的异常和回归测试。”
- “评审当前变更是否遗漏调用方。”
- “定位订单状态没有更新的问题。”

以下场景不自动触发：

- 与当前项目无关的通用知识问答。
- KnowledgeBase 初始化、重建或增量维护。
- 只要求解释某种语言或框架语法。
- 不需要当前项目上下文的纯文本处理任务。

自动选择 Skill 属于 Claude Code 与 Codex 的模型化匹配能力，无法通过 Hook 保证每次强制触发。通过精准 Description、项目级 KnowledgeBase 使用规则和触发评测共同提高稳定性，不引入会强制污染所有会话的全局 Hook。

### 5.2 手动触发

- Claude Code：`/knowledge-base-context`
- Codex：`$knowledge-base-context`

Codex `agents/openai.yaml` 建议内容：

```yaml
interface:
  display_name: "KnowledgeBase 任务上下文"
  short_description: "从 KnowledgeBase 与源码渐进获取当前任务所需上下文"
  default_prompt: "使用 $knowledge-base-context 识别当前任务画像，同时读取 Schema 3.0 KnowledgeBase 与相关源码，生成最小任务上下文包。"
```

## 6. Manifest 的职责

`cadence/knowledge-base/manifest.yaml` 不参与 Skill 触发。Skill 触发后，Manifest 作为知识库目录卡和基线说明，提供：

- Schema 版本。
- KnowledgeBase 生成 Skill 与版本。
- 用户允许分析的工程范围。
- 数据库、API、页面和中间件范围。
- 用户输入来源。
- KnowledgeBase Git 分支和基线提交。
- 已生成文档、覆盖情况和待确认项数量。

执行关系：

```text
自然语言或手动调用命中 Skill
→ 读取 Manifest
→ 校验 Schema、工程范围和 KnowledgeBase 基线
→ 同时读取 KnowledgeBase 与当前源码
→ 生成任务上下文包
```

Manifest 不替代 KnowledgeBase 内容，也不替代源码。Manifest 缺失或 Schema 不是 `3.0` 时停止，报告缺失原因并引导使用 `knowledge-base-bootstrap`。

当前 Git 提交晚于 Manifest 基线时继续读取当前源码，同时在上下文包中标记基线漂移。受影响实体已经发生变化时，记录 KnowledgeBase 结论与当前实现的差异，不静默选择一方。

## 7. 固定任务画像

首版固定支持七类画像，不设计扩展机制。每次任务选择一个主画像，允许附加最多两个辅助画像。

| 画像 | KnowledgeBase 读取重点 | 源码读取重点 | 专属输出 |
|------|------------------------|--------------|----------|
| 需求澄清 | 概览、术语、页面、对外能力、现有流程、待确认项 | 状态枚举、校验、入口和业务分支 | 已有能力、边界、业务规则、冲突和澄清问题 |
| Design | 服务、API、数据模型、中间件、横切机制、关系矩阵 | 架构、接口实现、配置装配、扩展点和技术约束 | 现状架构、可复用能力、约束、影响面和设计风险 |
| Plan | 关系矩阵、开发指南、变更历史和领域文档 | 文件与符号依赖、测试入口、构建结构和修改边界 | 变更单元、依赖顺序、文件范围、风险和验证入口 |
| Coding | 精确实体、API 报文、表结构和证据索引 | 类、方法、SQL、配置、调用链和测试 | 精确修改入口、现有模式、边界条件和验证命令 |
| Testing | API 报文、分支、错误码、数据约束和开发指南 | 测试框架、已有测试、Fixture、Mock、异常和边界实现 | 测试场景、数据准备、断言依据、回归范围和命令 |
| Review | 需求实体、关系矩阵、变更历史和知识库约束 | Git Diff、修改符号、调用方、测试和配置变化 | 需求符合度、遗漏影响、回归风险、证据缺口和知识库漂移 |
| Debug | 核心流程、错误码、中间件、状态流转和待确认项 | 失败路径、日志位置、开关、异常、并发和数据访问 | 症状事实、调用路径、候选根因、验证入口和冲突证据 |

主辅画像示例：

- 实现接口并补测试：Coding + Testing。
- 评审设计是否可实施：Review + Design。
- 定位问题并准备修复计划：Debug + Plan。

无法判断主画像，或不同画像会导致读取范围显著不同时，使用 Claude Code `AskUserQuestion` 或 Codex `request_user_input`。工具不可用时使用普通文本提问。

## 8. 渐进式双轨读取

### 8.1 第 0 层：前置校验

读取当前项目规则、Manifest、Git 分支、当前提交和工作区状态。确认 Schema 3.0 和工程范围。

### 8.2 第 1 层：任务识别

从用户请求提取：

- 主画像和辅助画像。
- 业务关键词与术语。
- 已知页面、API、服务、表、配置、文件和错误信息。
- 用户明确限制的工程和范围。
- 期望交付物，仅用于决定知识深度，不执行该交付物。

### 8.3 第 2 层：双轨种子获取

同时开始两条路径：

```text
KnowledgeBase 路径
README → Manifest → 领域索引 → 稳定 ID → 关系矩阵

源码路径
用户点名对象 → 文件/符号/路由/配置检索 → 当前实现入口
```

两条路径同等重要，任何一条都不是另一条的降级方案。

### 8.4 第 3 层：一跳关系扩展

围绕种子实体读取直接相关内容：

- 页面 → API。
- API → Service。
- Service → 表、中间件和外部系统。
- 表 → Mapper、Entity、DDL。
- 配置 → 装配、开关和调用位置。
- 测试 → 被测符号、Fixture 和执行入口。

默认只扩展一跳，不沿公共工具类、通用异常、日志和框架基础设施无限传播。

### 8.5 第 4 层：画像定向深化

根据主画像和辅助画像检查专属输出字段。字段缺少关键证据时扩展下一跳；字段已经满足时停止对应方向的读取。

### 8.6 第 5 层：双轨对照

对每项关键结论记录：

- KnowledgeBase 稳定 ID、结论和文档位置。
- 当前源码、DDL或配置证据。
- Manifest 基线和当前 Git 提交。
- 一致、KnowledgeBase 缺失、源码缺失或冲突状态。
- 对当前任务的影响。

当前实现行为以当前提交中的源码、DDL和有效配置记录；业务语义与预期保留 KnowledgeBase 和用户资料定义。两者不一致时明确写成“文档意图与当前实现不一致”，不自动覆盖任何一方。

### 8.7 第 6 层：停止条件

满足以下条件即停止读取：

- 任务边界和目标实体已确定。
- 入口、直接依赖和主要影响面已覆盖。
- 主辅画像要求的上下文字段已有证据。
- 关键冲突、漂移和缺口已经显式记录。
- 继续扩展只会进入公共基础设施或无关业务。

## 9. 工具与代码阅读策略

保持当前仓库规则：

- 大范围实体关系和调用影响优先使用可用的 CodeGraph。
- 精确类、方法、路由和配置结构优先使用 `ast-grep outline`。
- 已知名称、稳定 ID、路径和配置键使用文本检索与定向读取。
- 结构化工具不可用时降级为 `rg` 定位候选，再读取相关文件。
- 不因工具不可用扩大为无边界全仓读取。

Skill 不要求特定 MCP，不连接数据库、中间件、配置中心或远程环境。

## 10. 任务上下文包

默认输出到当前会话，固定包含：

1. 任务识别。
2. 任务理解。
3. 核心实体。
4. 双轨证据矩阵。
5. 关系与影响面。
6. 画像专属上下文。
7. 约束与现有模式。
8. 冲突、缺口与待确认项。
9. 下游使用建议。
10. 就绪状态。

核心表格：

| 结论 | KnowledgeBase 证据 | 源码/DDL/配置证据 | 状态 | 对任务影响 |
|------|--------------------|-------------------|------|------------|

就绪状态：

- `就绪`：完成当前画像所需的关键上下文，没有影响方向的未决冲突。
- `有条件就绪`：存在非阻断缺口，能够在明确假设下继续。
- `阻断`：缺少关键业务规则、目标实体无法确定或冲突会改变任务方向。

Skill 不输出完整源码副本，也不复制整个 KnowledgeBase 文档。使用摘要、稳定 ID、精确文件或符号位置和必要的短片段组织上下文。

## 11. 持久化规则

默认不写文件。用户明确要求复用、交接或审计时，保存到：

```text
cadence/knowledge-base/task-contexts/
YYYY-MM-DD_任务上下文_任务名称_v1.0.md
```

持久化文件是当前分支和提交下的任务快照，必须记录：

- 任务请求。
- 主辅画像。
- Manifest 基线。
- 当前 Git 提交。
- 读取范围。
- 证据与冲突。
- 生成时间。

任务快照不是新的事实知识库，不自动加入 Manifest，不自动反向更新领域文档。发现 KnowledgeBase 漂移时只报告并建议执行 `knowledge-base-update`。

## 12. 异常与冲突处理

| 情况 | 行为 |
|------|------|
| Manifest 缺失或 Schema 不是 3.0 | 停止，报告缺失路径，指向 `knowledge-base-bootstrap` |
| Manifest 声明领域不适用 | 不读取该领域，记录限制 |
| KnowledgeBase 文档缺失 | 继续读取相关源码，同时标记知识库缺口 |
| 源码路径失效 | 使用稳定 ID、关系矩阵和文本检索定位候选，无法确认时记录冲突 |
| KnowledgeBase 与源码冲突 | 同时保留两侧证据；影响方向时询问用户 |
| 当前提交晚于基线 | 标记知识库漂移，重点核对受影响实体 |
| 同名实体无法唯一匹配 | 列出候选并询问用户，不按名称猜测 |
| 继续扩展将超出 Manifest 范围 | 停止并说明需要新的用户授权范围 |
| 工作区存在未提交修改 | 将其视为当前源码状态，不清理、不覆盖、不恢复 |
| 敏感配置 | 只记录键、用途和值类型，实际值使用 `<redacted>` |

## 13. 自动交互规则

Skill 自动完成画像识别、种子获取、一跳扩展和上下文组织，不在每一步重复确认。

只有以下情况询问用户：

- 多个目标实体无法消歧。
- KnowledgeBase 与源码冲突会改变任务方向。
- 缺少关键业务规则，无法形成可靠上下文。
- 用户请求范围与 Manifest 授权范围冲突。

Claude Code 使用 `AskUserQuestion`；Codex 工具可用时使用 `request_user_input`；工具不可用时使用普通文本提问。

## 14. 验证方案

### 14.1 结构验证

- `SKILL.md` Frontmatter 名称与目录一致。
- Description 长度和格式符合 Skill 规范。
- `agents/openai.yaml` 与 SKILL 的名称、能力和默认提示一致。
- 所有引用资源存在且从 `SKILL.md` 一层可达。
- 不存在对 `cadence-workflow` 的调用、依赖或文件修改；允许在边界声明中明确说明两者无关。

### 14.2 自动触发验证

分别为 Claude Code 和 Codex 准备以下评测：

- 七类画像各至少两个自然语言正例。
- 显式提到 KnowledgeBase 的正例。
- 通用知识问答、KnowledgeBase 初始化和无项目上下文文本任务的负例。
- 同时包含 Coding + Testing、Review + Design、Debug + Plan 的组合画像用例。

成功标准：

- 正例能够选择 `knowledge-base-context`。
- 负例不会选择该 Skill。
- 组合任务识别一个主画像和不超过两个辅助画像。

### 14.3 手动触发验证

- Claude Code `/knowledge-base-context` 能读取 Skill。
- Codex `$knowledge-base-context` 能读取 Skill。
- Codex Skill 列表展示 `agents/openai.yaml` 中的名称和描述。

### 14.4 行为验证

使用至少以下场景验证：

1. KnowledgeBase 与源码一致，输出高可信度证据矩阵。
2. 当前源码晚于 Manifest 基线，输出漂移提示。
3. KnowledgeBase 与源码冲突，保留双侧证据而不静默覆盖。
4. 页面、API、服务和表形成完整一跳关系后停止。
5. 公共工具类存在大量调用方时不无限扩展。
6. Manifest 缺失时停止并引导 Bootstrap。
7. 用户明确要求保存时按项目文档命名规则生成任务快照。

### 14.5 回归验证

- 现有六个 KnowledgeBase Skills 的触发和职责不变。
- `knowledge-base-overview` 仍只负责生成入口、导航和项目规则。
- `knowledge-base-update` 仍独占 KnowledgeBase 增量维护职责。
- `cadence-workflow` 文件和行为没有变化。

## 15. 验收标准

- Claude Code 和 Codex 均支持自然语言自动触发。
- Claude Code 和 Codex 均支持对应的手动调用方式。
- 七类固定画像均能生成对应的专属上下文。
- KnowledgeBase 与源码在每次任务中同时参与，不存在主从或降级关系。
- 读取范围能够从种子实体渐进扩展，并在信息充分时停止。
- 输出包含稳定 ID、精确源码位置、双轨证据、冲突和就绪状态。
- 默认不产生任务文件；明确要求时生成符合命名规则的任务快照。
- Manifest 只承担 Schema、范围和基线职责，不参与 Skill 触发。
- 新 Skill 不依赖、不调用、不修改 `cadence-workflow`。
