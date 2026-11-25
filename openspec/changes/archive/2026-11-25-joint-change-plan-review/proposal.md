# 初始化项目的设计确认与联合送审

## Why

现行入口要求先签发 OpenSpec 契约，再编写实施 Plan。这增加了人工等待，也让彼此依赖的草稿分开审阅。按整行追加的配置升级还会保留旧门禁。

## What Changes

- 完整 Design 独立双审，默认在此确认一次。联合编写 change 与 Plan，完成严格校验和追溯后同版联合双审。
- 按任务记录人工决定、委托和审查版本，供直接 apply 和会话恢复使用。
- 通过 `rule-config` 同步升级入口、完整规则和 OpenSpec 配置，保留用户规则与提交开关。

## Capabilities

### Modified Capabilities

- `progressive-context-routing` 定义阶段、确认、交付与恢复。
- `routing-conformance` 定义工作包追溯、联合送审和配置升级验收。
- `managed-rule-lifecycle` 定义新入口版本和旧工作流规则的识别。

## Impact

影响 rule-config 的生成源、现行项目投影、规格和验证。代理选角、派工与复核方式归 `cadence-subagents-config`。采用已通过双审并由用户确认的 [Design](../../../../cadence/designs/2026-11-25_方案设计_初始化项目工作流联合送审_v1.0.md)。
