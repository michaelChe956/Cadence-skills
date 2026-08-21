# Proposal: slim-l0-routing-kernel-v3

## Why

rule-config 生成的 L0 路由内核（v2，5.2KB）与 L1 `openspec-superpowers-workflow.md`（5.2KB）复杂在错误的地方：近半篇幅是不可验证的姿态类条款（静默、引导句禁令、重试静默等），弱模型遵循率低；四客户端协议差异散落多个段落；且 L0 全文被注入为 outline/draft 生成的前置必读，挤占上下文预算。需将两份模板瘦身约 60-70%（L0 目标 ≤2KB），所有存量项目经现有 L0 版本升级机制（复用 v1→v2 先例）增量升级到 v3，不重装。

## What Changes

- **L0 模板重写为 v3**（≤2KB）：保留路由表（精简列宽、合并"必读规则"列）、四条铁律（无契约不规划实施、无 Plan 不改实现、TDD 先失败测试、无新鲜证据不声称完成）、产物路径覆盖表、产物自动提交开关、阶段切换重新路由（一句话）；四客户端差异收敛为 2-3 行中性调用说明（Claude/Kimi 原生调用；Codex/pi 清单选择后全文读取 SKILL.md）。
- **knowledge-base 门禁并入 v3 模板正文**（约 2-3 行），从 naruto 手写私有行变为标准内容。
- **删除**全部姿态类条款（静默/引导句/事件间隙/重试静默/"失败关闭不可豁免"表述），保留其背后的可判定门禁本身。
- **版本升级机制**：现 v2 模板全文逐字移入 `references/rules/l0-history/agent-routing-kernel-v2.md`；`L0_CURRENT_VERSION="v3"`，`L0_OLD_VERSIONS=["v2","v1","v0"]`，`L0_OLD_SOURCES` 增加 v2 条目；v2 漂移区块（含手加行）按现有 drift 语义权威覆盖到 v3，不改六态分类逻辑。
- **L1 workflow.md 同步瘦身**：保留职责边界、标准流程 7 步、可判定失败关闭、OpenSpec 强制阈值与豁免；删除每步内四客户端时序细节与姿态条款。L1 走 drift 权威覆盖，无版本迁移。
- **测试**：新增 v2→v3 升级五分类用例（逐字 v2、v2 漂移含手加行、v1、v0、无标记）；更新受模板全文逐字比对影响的既有用例。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `progressive-context-routing`: L0 路由内核的内容契约变化——姿态类条款从内核中移除，客户端调用差异收敛为中性短说明，KB 门禁行成为内核标准内容；路由表列结构简化。
- `managed-rule-lifecycle`: L0 当前版本由 v2 升为 v3，新增 v2 历史规范源与 v2→v3 升级路径；v2 漂移区块按 drift 权威覆盖升级（不新增停滞路径）；L1 规范源内容瘦身（drift 覆盖语义不变）。
- `knowledge-base-context-gating`: "L0 路由内核门禁"从项目手写行为升级为框架模板标准内容，v3 起所有新装与升级项目统一携带。

## Impact

- `cadence-init/skills/rule-config/references/rules/agent-routing-kernel.md`（重写为 v3）
- `cadence-init/skills/rule-config/references/rules/l0-history/agent-routing-kernel-v2.md`（新增历史源）
- `cadence-init/skills/rule-config/references/rules/openspec-superpowers-workflow.md`（瘦身）
- `cadence-init/skills/rule-config/scripts/rule-config.py`（版本常量、`L0_OLD_SOURCES`）
- `cadence-init/skills/rule-config/tests/test_rule_config.py`（新增/更新用例）
- 存量项目（如 naruto）经 rule-config dry-run + apply 增量升级，受管区块外内容不动。
- 不改 pre-check 的 superpowers 安装逻辑。
