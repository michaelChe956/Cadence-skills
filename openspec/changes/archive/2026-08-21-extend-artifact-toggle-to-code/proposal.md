# Proposal: extend-artifact-toggle-to-code

## Why

现有“产物自动提交（design/plan）”开关只控制 design/plan 文档的 `git commit`，实现类产物（代码、测试、配置）的提交不受控；用户需要一个开关统管全部三类产物，且存量项目（开关已开）不能被静默降级。

## What Changes

- 开关改名“产物自动提交（design/plan/code）”：写入新入口时使用新名；存量旧名开关行按**身份迁移**识别为同一开关，替换为新名并保留原值（`开启`→`开启`），确定性升级、不留旧行、不发 warning。
- 读取语义扩展：开关为 `关闭` 时禁止 `git commit` 的对象从 design/plan 扩为 design/plan/code 全部产物（实现类改动：代码、测试、配置）；CLAUDE.md 为准、AGENTS.md 兜底、不一致按 `关闭`（不变）。
- L0 v3 内核模板开关句同步为新名 + 实现类产物表述（v3 模板逐字变化，存量 v3 项目走既有 drift 权威覆盖，不升 v4）。
- 文档同步：`document-storage.md`、rule-config SKILL.md、`merge-semantics.md` 中开关引用文案。
- 测试：旧名→新名迁移保值、非法值、缺失默认关、旧名+新名并存去重；harness 开关用例基准更新；L0 模板断言更新。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `superpowers-artifact-governance`: 开关名称与控制范围变化（design/plan → design/plan/code），新增旧名身份迁移保值场景。
- `rule-config-scripted-execution`: 入口 `## 项目配置` 章节维护的开关名变化。

## Impact

- `cadence-init/skills/rule-config/scripts/rule-config.py`（开关写入/识别/迁移逻辑）
- `cadence-init/skills/rule-config/references/rules/agent-routing-kernel.md`（L0 v3 开关句）
- `cadence-init/skills/rule-config/references/rules/document-storage.md`、`SKILL.md`、`references/merge-semantics.md`
- `cadence-init/skills/rule-config/tests/test_rule_config.py`、`tests/verify-managed-lifecycle.sh`
- 本仓库与存量项目入口文件（下次 apply 时迁移）
