# Codex Rules Inline Specification

## Purpose
Codex 只自动读 AGENTS.md 链、不读 `.claude/rules/` 目录（2026-09-02 实验证实），②③类规则内容从未进入其上下文。本能力把规则内容自动投影为 AGENTS.md 受管内联区块，让 Codex"能看见"规则。

## Requirements

### Requirement: apply 必须从规则源自动生成内联区块

`rule-config apply` MUST 以 `.claude/rules/*.md` 与工具元数据为唯一源，自动生成/覆盖业务项目 AGENTS.md 中 `cadence-managed:codex-rules-inline` 标记包裹的受管区块，内容为优先级声明与铁律的压缩版。维护者新增或修改规则后重跑 apply，区块 MUST 自动更新；全程 MUST NOT 要求维护者手工编辑该区块。

#### Scenario: 加规则零手动维护

- **WHEN** 维护者新增一个规则文件并重跑 `rule-config apply`
- **THEN** codex-rules-inline 区块自动包含新规则的压缩内容，无需手工编辑

#### Scenario: 只动受管区块

- **WHEN** apply 更新内联区块
- **THEN** AGENTS.md 区块外内容逐字不变

### Requirement: 内联区块必须受行数预算约束

内联区块 MUST 不超过 60 行；超预算时 MUST 按元数据优先级截断并在区块末尾标注省略。

#### Scenario: 预算截断

- **WHEN** 规则源压缩后超过 60 行
- **THEN** 区块截断至 60 行内并标注省略

### Requirement: 漂移检测必须区分未生成与漂移

`rule-config --verify` 对从未生成过内联区块的项目 MUST 报"未生成"并提示运行 apply，MUST NOT 报漂移；对区块存在但与源重算结果不一致的项目 MUST 报漂移。

#### Scenario: 未生成不误报

- **WHEN** 项目从未生成过内联区块且运行 `--verify`
- **THEN** 报告该项为"未生成"并提示运行 apply，不报漂移
