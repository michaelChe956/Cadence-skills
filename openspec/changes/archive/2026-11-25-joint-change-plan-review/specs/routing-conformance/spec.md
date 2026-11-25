## MODIFIED Requirements

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

#### Scenario: 直接 apply 时联合包未就绪
- **WHEN** 恢复时仅有 change、该 change 严格校验失败或双向追溯缺失
- **THEN** 回联合编写补 Plan、修正 change 或补齐映射，重新校验后再联合送审，实施保持阻塞

### Requirement: 验证结果必须可审计
系统 MUST 记录客户端、场景、期望阶段、期望规则与 Skill、实际路由、门禁结果、误加载项和结论，并 SHALL 将失败项映射到 L0、L1、L2 或具体 OpenSpec artifact 的修复位置。

#### Scenario: 直接 apply 越过 Plan
- **WHEN** 任一客户端在当前联合包缺少 Plan 或同版联合双审通过证据时继续执行 OpenSpec 工作包
- **THEN** 验证记录判定失败
- **AND** 明确指出是入口路由、协作规则还是 artifacts 中的 Plan 门禁未生效

## ADDED Requirements

### Requirement: 配置升级精确迁移旧工作流条款
系统 MUST 仅在所属字段迁移已知框架的完整 context 行与完整 artifact 规则项。用户 context、额外规则、扩展字段、独立覆盖规则和提交开关保留。

#### Scenario: 旧项目混入用户配置
- **WHEN** 项目重跑正常初始化且含可识别的旧框架条款和部分文字相似的用户规则
- **THEN** 原文件经备份后发布唯一的新框架流程，近似用户规则及其他字段保留

#### Scenario: 再次初始化
- **WHEN** 同一版本再次运行
- **THEN** 已发布内容和文件写入时间保持一致，新增备份为零
