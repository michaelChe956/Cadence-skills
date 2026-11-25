# routing-conformance Specification

## Purpose
规定如何验证初始化后的客户端遵守项目工作流。验证覆盖 OpenSpec 原生指令、工作包与实施计划的双向追溯、人工确认与送审时序，以及旧项目升级后的配置保留和重复运行结果。

## Requirements

### Requirement: OpenSpec 配置必须冗余职责和 artifact 边界
系统 SHALL 在 `openspec/config.yaml` 的公共 `context` 中声明 OpenSpec 管契约、Superpowers 管行为，并 SHALL 为 proposal、design、specs 和 tasks 配置各自的产物边界规则。

#### Scenario: 生成 design artifact
- **WHEN** Agent 创建或更新 OpenSpec design
- **THEN** OpenSpec 指令包含将 已通过门禁的 Design 架构、边界和权衡持久化的规则
- **AND** design 不承担精确文件级实施步骤

#### Scenario: 生成 tasks artifact
- **WHEN** Agent 创建或更新 OpenSpec tasks
- **THEN** tasks 只包含可跟踪的高层工作包
- **AND** 精确文件、命令、测试与提交步骤留给 Superpowers Plan

### Requirement: OpenSpec 配置不得使用无效的 apply artifact 规则
系统 MUST 只对当前 schema 的有效 artifact ID 配置规则，并 MUST NOT 将特殊命令 `apply` 当作 `rules.apply` artifact。

#### Scenario: 直接获取 apply 指令
- **WHEN** Agent 执行 `/opsx:apply` 或等价的 OpenSpec apply 流程
- **THEN** Plan 门禁来自 L0、L1 以及 apply 读取的 design/tasks 契约
- **AND** `openspec/config.yaml` 不包含无效的 `rules.apply`

### Requirement: OpenSpec 工作包与 Superpowers Plan 必须可追溯
系统 MUST 在同一阶段编写 change 与 Plan。工作包与 Plan 步骤 SHALL 双向引用，并能定位到 change、requirement 和 scenario。

#### Scenario: writing-plans 展开工作包
- **WHEN** Design 双审已通过且所需人工确认已满足，change 已有可引用的 requirement、scenario 和工作包编号
- **THEN** 立即调用 `writing-plans`，在 `cadence/plans/` 展开文件、接口、实施顺序和验证方法，草稿可在 Design 边界内相互校正

#### Scenario: Plan 与 OpenSpec 冲突
- **WHEN** Plan 的细化导致 change 与 Plan 出现分歧
- **THEN** 在已审 Design 边界内联合修订草稿，涉及 Design 范围、架构或验收边界变化时返回 Design 阶段

#### Scenario: 同版联合送审
- **WHEN** change 和 Plan 均完整，`openspec validate <change-id> --strict` 通过且每个工作包与 Plan 可以双向追溯
- **THEN** 将两份产物作为同一版本一次联合双审，按委托和人工决定继续

#### Scenario: 路径变更的恢复
- **WHEN** 联合双审后的修订只改变测试路径，契约和场景映射保持一致
- **THEN** 恢复时接受代理协议规定的接地侧复核记录，沿用原一致性结论

#### Scenario: 文本修订的签收
- **WHEN** 只修正错字或链接且语义一致
- **THEN** 集成人核验实际差异及链接目标后记录最终版本，恢复时沿用该记录

#### Scenario: 授权语义变更
- **WHEN** 送审后修改授权语义
- **THEN** 按代理协议核对两侧的复核结果。超出已确认 Design 边界时先回 Design 阶段，再按新边界准备联合包

#### Scenario: 直接 apply 时联合包未就绪
- **WHEN** 恢复时仅有 change、该 change 严格校验失败或双向追溯缺失
- **THEN** 回联合编写补 Plan、修正 change 或补齐映射，重新校验后再联合送审，实施保持阻塞

### Requirement: 路由目标和版本必须通过静态检查

系统 MUST 提供可重复的静态检查，确认 L0 引用的规则文件与 Skill 名称存在、`CLAUDE.md` 和 `AGENTS.md` 的路由版本一致、L1 规范源与生成副本一致，并且 OpenSpec 配置只使用有效 artifact 规则键。系统还 MUST 提供直接驱动 rule-config 脚本执行体的可执行生命周期测试，证明同版本幂等、内容漂移归档后权威覆盖、双入口备份屏障、候选 YAML 解析与结构预检和原子发布失败关闭；该测试 SHALL 通过脚本 CLI 断言真实文件系统结果与 JSON 报告字段，不得再以独立参考模型模拟 Skill 行为。

#### Scenario: 入口引用不存在的 Skill

- **WHEN** L0 引用当前项目应已安装但实际不存在的 Superpowers Skill
- **THEN** 静态检查失败并报告入口文件、任务信号和缺失名称

#### Scenario: OpenSpec 包含 rules.apply

- **WHEN** `openspec/config.yaml` 将 `apply` 配置为 artifact 规则键
- **THEN** 静态检查失败并指出 `apply` 是特殊命令而非有效 artifact

#### Scenario: 受管生命周期失败关闭

- **WHEN** 测试夹具模拟 L0/L1 备份失败、候选结构预检失败或原子发布失败
- **THEN** 脚本执行体 MUST 返回非零状态并保持目标文件运行前后哈希一致
- **AND** 测试报告 MUST 记录场景、退出状态和运行前后 SHA-256

#### Scenario: 不可解析或不兼容的既有配置归档后替换

- **WHEN** 测试夹具模拟既有 `openspec/config.yaml` YAML 不可解析或目标字段类型冲突
- **THEN** 脚本执行体 MUST 先将原文件归档到 `cadence/legacy/`，归档成功后以模板原子替换并正常完成
- **AND** 归档失败时 MUST 返回非零状态且目标文件保持运行前后哈希一致

### Requirement: 必须验证跨客户端关键场景
系统 SHALL 对 Claude Code、Kimi Code 与 Codex 执行新功能、Bug、直接 apply、上下文恢复、纯问答和完工声明场景验证，并 MUST 记录原生 Skill 调用事件、首个用户可见路由回执、Skill 正文与仓库工具调用顺序、门禁结果和无关正文误加载项。最终自然路由门禁使用的提示词 SHALL NOT 直接补入“Skill 前静默”“先调用后回执”等待验证顺序；除纯概念问答只要求全局 `using-superpowers` 外，每个场景的全部必调 Skill 都 MUST 通过客户端原生机制实际调用。Claude/Kimi 仅普通读取 `SKILL.md`、输出名称、复述流程或声称已加载 SHALL 判定失败；Codex 必须记录从平台 Skill 目录显式选择、首段用途公告、全文读取对应 `SKILL.md`，并确认全文读取前没有仓库操作。

#### Scenario: Kimi Code 漏调 brainstorming
- **WHEN** Kimi Code 在新功能场景中未调用 brainstorming 就准备创建 OpenSpec 或实现文件
- **THEN** 场景验证判定失败
- **AND** 失败映射到 AGENTS L0 或完整协作规则的修复位置

#### Scenario: Claude Code 上下文恢复
- **WHEN** Claude Code 在 compact 或 resume 后继续已有 change
- **THEN** 它重新识别 change、Plan、当前阶段和必调 Skill
- **AND** 不因之前已经路由过而跳过门禁

#### Scenario: Codex 纯问答
- **WHEN** Codex 只回答不涉及仓库操作的概念问题
- **THEN** 它只原生调用全局 `using-superpowers`，不输出仓库路由回执
- **AND** 它不加载仓库规则、其他无关 Skill、实现、文档写入或完成验证正文
- **AND** 场景验证不把合理的轻量行为判定为失败

#### Scenario: 完工声明
- **WHEN** 任一客户端准备声称修改完成、Bug 已修复或测试通过
- **THEN** 它调用 verification-before-completion 并读取新鲜验证证据
- **AND** 缺少证据时拒绝完成声明

### Requirement: 验证结果必须可审计
系统 MUST 记录客户端、场景、期望阶段、期望规则与 Skill、实际路由、门禁结果、误加载项和结论，并 SHALL 将失败项映射到 L0、L1、L2 或具体 OpenSpec artifact 的修复位置。

#### Scenario: 直接 apply 越过 Plan
- **WHEN** 任一客户端在缺少 Plan、送审版联合双审结论或最终交付版相对送审版的差异核验记录时继续执行 OpenSpec 工作包
- **THEN** 验证记录判定失败
- **AND** 明确指出是入口路由、协作规则还是 artifacts 中的 Plan 门禁未生效

### Requirement: 配置升级精确迁移旧工作流条款
系统 MUST 仅在所属字段迁移已知框架的完整 context 行与完整 artifact 规则项。用户 context、额外规则、扩展字段、独立覆盖规则和提交开关保留。

#### Scenario: 旧项目混入用户配置
- **WHEN** 项目重跑正常初始化且含可识别的旧框架条款和部分文字相似的用户规则
- **THEN** 原文件经备份后发布唯一的新框架流程，近似用户规则及其他字段保留

#### Scenario: 再次初始化
- **WHEN** 同一版本再次运行
- **THEN** 已发布内容和文件写入时间保持一致，新增备份为零
