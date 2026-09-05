## Why

现有 pre-check 在一次真实运行中耗时 6m38s，22 次调用中约 97.65%（模型等待时间）消耗在临场编程、状态探测与重试，而非机械执行。将既有实施固化为确定性的五阶段脚本编排与 SKILL.md 三步契约，可把稳定验收线统一收敛到 ≤120s（不区分冷热启动），同时保留原有产物与交互语义；本变更为 2026-09-04~05 已完成实施后的追溯性契约补建。

## What Changes

- 新增 pre-check 脚本化执行能力：在一次脚本调用内按 base-tools、openspec、superpowers-git、superpowers-links、verify 五阶段串行编排，并输出可断言的 `phases[]` 报告。
- 固化 `phases[]` 报告 schema、阶段计时、结果/动作/计数、错误及 Git 元数据，并保留既有 `steps[]` 向后兼容。
- 将 SKILL.md 收敛为“定位绝对路径、项目根一次调用、读取报告并呈现”三步契约，禁止模型临场编排，工具调用上限为 5。
- 固化统一性能验收线 ≤120s；240s 仅用于网络异常熔断并判定为基础设施失败。
- 固化普通冲突、no-interrupt 冲突、失败快返、只读 verify、幂等重跑与 `precheck-v2` 1:1 基线 diff 守卫语义。
- 不修改 `init-skill-sequencing`、`kimi-code-support` 现有 MUST；其 O-1 张力作为独立后续任务处理。

## Capabilities

### New Capabilities

- `pre-check-scripted-execution`: 提供 pre-check 五阶段确定性编排、三步 SKILL 契约、结构化阶段报告、冲突/失败语义、性能与幂等验收能力。

### Modified Capabilities

- 无。现有 capabilities 的 MUST 要求不在本变更中修改。

## Impact

- 影响 `cadence-init/skills/pre-check/scripts/pre-check.sh`、对应 `SKILL.md`、fixture/单元与集成验收及 eval 断言；影响 pre-check 的结构化报告消费方。
- 新增 OpenSpec 主 spec `openspec/specs/pre-check-scripted-execution/spec.md`，由本 change 的 ADDED delta 同步生成。
- 不引入新运行时依赖；脚本继续遵循 Bash 3.2 兼容约束，既有 `steps[]` 和人工 fallback/Playwright opt-in 等边界保持不变。
