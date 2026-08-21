<!-- cadence-framework-rule:openspec-superpowers-workflow:v1 -->
# OpenSpec 与 Superpowers 协作规则

## 一、职责边界
- OpenSpec 是契约层：proposal 管 Why、范围和非目标；design 管架构边界和权衡；specs 管 MUST/SHALL 验收场景；tasks 只管高层工作包。
- Superpowers 是行为层：brainstorming 管探索；writing-plans 管精确实施 Plan；调试、TDD、执行、审查、验证和分支收尾由对应 Skill 负责。
- OpenSpec artifacts 是 brainstorming 确认结果的持久化契约；`openspec-propose` 不能替代 brainstorming。

## 二、标准流程
1. 任何任务先调用 `using-superpowers`；需要仓库操作时，再调用当前阶段全部必调 Skill。客户端差异：Claude/Kimi 原生调用；Codex/pi 从清单选择后全文读取 `SKILL.md`。
2. 调用后首个用户可见段落输出阶段、Change、Plan 和必调 Skill 路由回执，回执后方可读取规则并使用仓库工具。新功能、行为变化或架构变化必含 `brainstorming`。
3. 用户确认设计后，将结论写入 OpenSpec proposal、design、specs、tasks。
4. 用户审阅 OpenSpec 契约后，下一 Skill 必须是 `writing-plans`。
5. Plan 写入 `cadence/plans/`，并引用 change、工作包编号和 requirement。
6. 实施用 `executing-plans` 或 `subagent-driven-development`；Bug 先 `systematic-debugging`；写实现前调 `test-driven-development`。
7. 完成声明前调 `verification-before-completion`；实施与验证完成后调 `requesting-code-review`；审查通过后勾选工作包并执行 OpenSpec sync/archive；最后调 `finishing-a-development-branch`。

## 三、失败关闭（可判定门禁）
- 无 Plan 的 apply：先 `using-superpowers` 与 `writing-plans`。
- 无验证证据的完成声明：先调 `using-superpowers` 与 `verification-before-completion`，再拒绝声明；调用不等于执行验证命令。
- 必调 Skill 缺失或不可用：停止并报告，不得模拟已执行。
- 达到强制阈值但契约未确认：不得规划或实施。
- 已有 change 的多步实施没有已确认 Plan：不得修改实现文件或执行工作包。
- 实施发现范围、架构或验收变化：停止，先更新并重新确认 OpenSpec，再更新 Plan。

## 四、OpenSpec 强制阈值与豁免
- 新功能、行为变化、公共接口或数据变化、跨模块重构、架构或验收变化必须使用 OpenSpec。
- 纯问答、只读调查、无语义文档修正可不使用 OpenSpec。
- 恢复已有明确契约的小型 Bug 默认不建新 change，但仍必须 systematic-debugging、TDD 和验证。
- 无法判断是否达到阈值时停止并向用户说明分歧点。
- 纯概念问答只调 `using-superpowers` 后直接回答，不输出仓库路由回执，不加载仓库规则或其他无关 Skill。

## 五、tasks 与 Plan 的边界
- OpenSpec tasks 只写高层、可验收工作包；Plan 写精确文件、步骤、命令、测试和提交建议。
- Plan 只能展开 OpenSpec，不得修改范围、架构边界或验收标准；实施步骤必须可追溯到 change、task 和 requirement。

## 六、冲突裁决与禁止事项
- 范围、需求、验收以 proposal/specs 为准；架构边界以 design 为准；文件、命令、测试与实施顺序以已确认 Plan 为准（不得越过 OpenSpec）；调试、TDD、审查、验证方法以对应 Skill 为准。
- 不依赖 legacy 工作流插件、Hook 或阅读状态机；不添加无效 `rules.apply`；框架规则不入 `cadence/project-rules/`，用户自定义规则不入 `.claude/rules/`。
