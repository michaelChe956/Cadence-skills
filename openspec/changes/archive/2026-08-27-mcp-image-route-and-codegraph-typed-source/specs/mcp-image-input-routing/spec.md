# mcp-image-input-routing Specification

## Purpose

定义图片输入任务的统一路由决策与 MCP 可用性状态管理：模型原生多模态能力优先，无法直接识图时才使用智普或 MiniMax MCP，调用前探测并按任务范围持久化状态，两供应商无固定优先级；同时约束 MCP 使用规则的单一来源，防止规则文件被多写者漂移。

## ADDED Requirements

### Requirement: 图片输入必须先经模型能力路由
Agent 处理图片输入时 MUST 先判断当前模型能否直接访问并理解该图片：能直接访问且理解的 MUST 使用模型原生能力处理，MUST NOT 为识图目的调用 MCP 服务；不能直接访问（文本模型或图片不可达）的 SHALL 进入 MCP 备选路径。路由判断 MUST 基于当前客户端的实际图片暴露行为而非模型品牌推断，无法确认原生能力时视为需要 MCP 路径。MCP 规则文件中智普与 MiniMax 小节的排列顺序 MUST NOT 被解读为服务优先级。

#### Scenario: 多模态模型优先使用原生能力
- **WHEN** 当前模型能直接访问并理解目标图片
- **THEN** Agent MUST 使用模型自身能力完成识别
- **AND** Agent SHALL NOT 因 MCP 已配置而改用 MCP 识图

#### Scenario: 无原生能力进入 MCP 路径
- **WHEN** 当前模型为纯文本模型、无法确认原生能力、或图片无法直接提供给模型
- **THEN** Agent MAY 依后续探测状态选择可用的 MCP 图片理解服务

### Requirement: MCP 图片工具调用前必须探测并记录可用性状态
Agent 在调用任何 MCP 图片理解服务前 MUST 确认该服务的可用性：客户端能发现对应 server 且其图片工具可见。首次确认结果 MUST 以机器可读记录持久化到 `cadence/cache/mcp-availability/<task-scope-id>.json`（该目录 MUST 在 `.gitignore` 中排除）。同一任务范围内每个 provider 至多探测一次；已记录 available 的 provider MUST NOT 重复探测，已记录 unavailable 的 provider MUST NOT 在同一任务范围内无条件重试。记录损坏、schema 版本不识别或 scope 不匹配的一律视为 unknown 并允许重新探测。用户要求重检、MCP 配置变更或客户端重连后，既有记录 MUST 视为失效。

#### Scenario: 首次识图任务逐 provider 探测一次
- **WHEN** 任务范围内尚无某 provider 的状态记录且需要 MCP 路径
- **THEN** Agent 对该 provider 执行一次可用性确认并将结果写入任务范围内的缓存文件
- **AND** 智普与 MiniMax 的状态 MUST 分别独立记录，SHALL NOT 合并为单一总状态

#### Scenario: 已有状态不重复探测
- **WHEN** 同一任务范围内目标 provider 已有明确状态记录
- **THEN** Agent MUST 直接依据该记录行动：available 则调用、unavailable 则跳过该 provider
- **AND** SHALL NOT 对同一 provider 发起第二次探测

#### Scenario: 不可用不得无限重试
- **WHEN** 某 provider 的当前任务范围为 unavailable 或本次调用失败
- **THEN** Agent SHALL NOT 在同一任务范围内对该 provider 反复重试
- **AND** 另一 provider 可用时 MAY 改用它完成识图

#### Scenario: 缓存失效条件触发重新探测
- **WHEN** 状态文件损坏、schema 版本不被识别、scope 不匹配，或发生配置变更/重连/用户显式重检
- **THEN** 相关 provider 的有效状态 MUST 视为 unknown
- **AND** 允许按首探流程重新确认并覆写记录

### Requirement: 双 MCP 服务之间无固定优先级
智普与 MiniMax 两个 MCP 图片理解服务之间 MUST NOT 设立固定默认顺序：两者均可用时应依据任务适配性或用户指定选择，仅一个可用时使用可用者，全部不可用时应如实报告而不伪装完成识图。自动执行中的探测或尝试顺序仅为执行次序，SHALL NOT 被表述或理解为供应商优先级。

#### Scenario: 双可用按任务适配任选
- **WHEN** 两个 provider 在当前任务范围内均为 available
- **THEN** Agent 按任务适配性或用户指定任选其一
- **AND** 行为与说明中 MUST NOT 出现固定的"先某家后另一家"约定

#### Scenario: 全部不可用如实报告
- **WHEN** 需要 MCP 路径且两个 provider 在当前任务范围内均为 unavailable
- **THEN** Agent MUST 明确报告识图未能完成及原因
- **AND** SHALL NOT 输出未经真实识别的猜测内容冒充结果

### Requirement: 可用性状态记录必须安全且结构固定
状态记录 MUST 仅包含固定白名单字段（scope 标识、生成时间、provider 名称、status 三态 `unknown`/`available`/`unavailable`、探测时间、方式与原因），MUST NOT 记录 API Key、Authorization 凭据、原始错误响应正文、图片内容或敏感 URL。记录 MUST 放置于 `cadence/cache/mcp-availability/` 目录下并 MUST NOT 提交到版本控制。

#### Scenario: 状态文件不含敏感信息
- **WHEN** 任一 provider 的可用性记录被写入或更新
- **THEN** 文件内容 MUST 限于白名单字段
- **AND** 文件路径 MUST 位于 `.gitignore` 排除的缓存目录内

### Requirement: 受管 MCP 规则必须保持单一来源
`.claude/rules/mcp-servers.md` 的内容来源 MUST 唯一为 rule-config 权威模板。MCP 配置类 Skill MUST NOT 向该受管文件追加、拼接或覆盖任何规则章节，其职责 MUST 限于 `.mcp.json`、Codex 配置等客户端配置文件的创建与交接以及指向 canonical 规则的引用。图片识别路由语义 MUST 以落地后的 `.claude/rules/mcp-servers.md` 为唯一权威表述处。

#### Scenario: 配置流程不写受管规则文件
- **WHEN** MCP 配置技能在项目中执行配置交接
- **THEN** 其 SHALL NOT 修改 `.claude/rules/mcp-servers.md`
- **AND** 涉及图片识别或 MCP 使用规则的问题 MUST 引用落地的 canonical 规则文件而非自身内嵌副本
