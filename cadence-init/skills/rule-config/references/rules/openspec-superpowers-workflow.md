<!-- cadence-framework-rule:openspec-superpowers-workflow:v1 -->
# OpenSpec 与 Superpowers 协作规则

## 一、职责边界
- OpenSpec 是契约层：proposal 管 Why、范围和非目标；design 管架构边界和权衡；specs 管 MUST/SHALL 验收场景；tasks 只管高层工作包。
- Superpowers 是行为层：brainstorming 管探索；writing-plans 管精确实施 Plan；调试、TDD、执行、审查、验证和分支收尾由对应 Skill 负责。
- OpenSpec artifacts 是 brainstorming 确认结果的持久化契约；`openspec-propose` 不能替代 brainstorming。

## 二、标准流程
1. 新任务先调用 `using-superpowers` 并按 L0 路由。
2. 新功能、行为变化或架构变化先调用 `brainstorming`。
3. 用户确认设计后，将结论写入 OpenSpec proposal、design、specs、tasks。
4. 用户审阅 OpenSpec 书面契约后，下一 Skill 必须是 `writing-plans`。
5. Plan 必须写入 `cadence/plans/`，并引用 change、工作包编号和 requirement。
6. 实施使用 `executing-plans` 或 `subagent-driven-development`；Bug 先 `systematic-debugging`；写实现前调用 `test-driven-development`。
7. 完成声明前调用 `verification-before-completion`；审查通过后勾选工作包并执行 OpenSpec sync/archive；最后调用 `finishing-a-development-branch`。

## 三、阶段重路由
在新任务、讨论转写入、brainstorming 设计确认、OpenSpec 契约获批、`/opsx:apply` 前、resume/clear/compact 后、完工声明前重新读取 L0。需要仓库操作时，在首次工具调用前输出包含阶段、Change、Plan 和必调 Skill 的路由回执。

## 四、失败关闭
- 必调 Skill 未加载或不可用：停止并报告，不得模拟已经执行。
- 达到 OpenSpec 强制阈值但契约未确认：不得规划或实施。
- 已存在 change 的多步实施没有已确认 Plan：不得修改实现文件或执行工作包。
- 实施发现范围、架构或验收变化：停止，先更新并重新确认 OpenSpec，再更新 Plan。
- 没有新鲜验证证据：不得声称完成、修复或测试通过。

## 五、OpenSpec 强制阈值与豁免
- 新功能、行为变化、公共接口或数据变化、跨模块重构、架构或验收变化必须使用 OpenSpec。
- 纯问答、只读调查、无语义文档修正可以不使用 OpenSpec。
- 恢复已有明确契约的小型 Bug 默认不创建新 change，但仍必须 systematic-debugging、TDD 和验证。
- 无法判断是否达到阈值时停止并向用户说明分歧点。

## 六、tasks 与 Plan 的边界
- OpenSpec tasks 只写高层、可验收工作包。
- Superpowers Plan 写精确文件、操作步骤、命令、测试和提交建议。
- Plan 只能展开 OpenSpec，不能修改范围、架构边界或验收标准。
- 实施步骤必须可以追溯到 change、task 和 requirement。

## 七、冲突裁决
- 范围、需求和验收以 OpenSpec proposal/specs 为准。
- 架构边界以 OpenSpec design 为准。
- 文件、命令、测试和实施顺序以已确认 Plan 为准，但不得越过 OpenSpec。
- 调试、TDD、审查和验证方法以对应 Superpowers Skill 为准。
- OpenSpec 默认提示与项目协作规则冲突时，以项目协作规则为准。
- 用户当前明确指令与既有契约冲突时停止，先更新权威产物。

## 八、禁止事项
- 不依赖 `cadence-workflow`、Hook、插件或阅读状态机。
- 不添加无效的 OpenSpec `rules.apply`。
- 不把框架规则写入 `cadence/project-rules/`，也不把用户自定义规则写入 `.claude/rules/`。
