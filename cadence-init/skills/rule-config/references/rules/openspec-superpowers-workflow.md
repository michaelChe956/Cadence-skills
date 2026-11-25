---
description: OpenSpec×Superpowers 协作流程——会话路由与阶段门禁
paths:
  # 行为路由桶占位：本规则经 L0 路由必读，不依赖路径自动注入
  - "**/*.zz-cadence-behavioral"
---
<!-- cadence-framework-rule:openspec-superpowers-workflow:v2 -->
# OpenSpec 与 Superpowers 协作规则

## 职责与适用范围

新功能、行为、公共接口或数据变化、跨模块重构、架构或验收边界变化须用 OpenSpec。纯问答、只读调查和无语义文档修正可豁免。恢复明确契约的小型 Bug 可直接按 `systematic-debugging`、TDD 和验证处理。阈值无法判断时说明具体分歧。

Cadence 定义阶段、产物、送审条件、人工确认和恢复。两次双审的选角、派工、审查与复核方式遵循 `cadence-subagents-config`。OpenSpec proposal 记录动机、范围、非目标，design 承接架构边界与权衡，specs 定义行为与验收场景，tasks 记录高层工作包。Superpowers 提供各阶段的方法。

## 阶段与放行条件

1. **完整 Design 独立双审。** 用 `brainstorming` 明确范围、架构和验收边界，写入 `cadence/designs/`。只送这一版完整 Design，双审通过后默认等待用户确认。已满足当前版确认或用户明确免确认，进入联合编写。
2. **联合编写 change 与 Plan。** 在 `openspec/changes/<change-id>/` 形成可引用的 requirement、scenario 和编号工作包后，立即调用 `writing-plans`。Plan 写在 `cadence/plans/`，细化文件、接口、实施顺序、命令及验证方法。工作包指向对应 Plan 步骤和验收场景，Plan 步骤回指 change、工作包、requirement、scenario。在已审 Design 边界内，两份草稿可相互校正，中间无需单独批准契约。
3. **同版联合双审。** 确认 change 与 Plan 全部就绪，实际运行 `openspec validate <change-id> --strict` 并取得成功结果，逐项核对双向追溯。两份产物组成同一版本的审查包，一次送审。双审均通过后，按任务原委托继续。委托实施时用 `executing-plans` 或 `subagent-driven-development` 执行，写实现前调用 `test-driven-development`。只委托出方案时交付 Design、change 与 Plan。
4. **实施收尾。** 完成声明前调用 `verification-before-completion` 并读取新鲜验证证据，然后用 `requesting-code-review` 审查。通过后标记工作包，按 OpenSpec sync/archive 收尾，再用 `finishing-a-development-branch` 选择集成方式。

## 人工确认与任务记录

本项目的确认与交接规则优先于各 Skill 默认的人工签发、Plan 交接或再次选择实施方式的提示。默认只问一次，位置在 Design 双审通过后。用户的实际指令按任务和版本记录：

| 用户决定 | 下一步 |
|---|---|
| “Design 没问题，继续” | 当前版 Design 已确认，双审通过即可联合编写。 |
| “这次不用确认，直接继续” | 跳过本任务剩余人工确认，Design 双审与联合双审照常执行。 |
| “Plan 写完给我确认” | 保留当前 Design 确认策略。Design 已确认或用户明确免除后联合编写，在联合双审通过后就 Plan 等一次。 |

在现有 Design、Plan 或任务交接记录中写明委托（实施或方案）、最近的显式确认策略、已询问/已确认的阶段、送审文件清单、送审版本、双方结论和最终交付版本。后来的明确决定更新其适用的剩余确认点。用修订号或内容摘要标识实际受审的内容，交接记录可以独立于被审正文。

## apply 与会话恢复

任务开始、阶段切换、`/opsx:apply`、resume/clear/compact 后重新读取当前产物与交接记录。OpenSpec 原生 `ready` 表示 change 自身的产物已齐。执行其工作包前，按以下顺序选择最早未满足的项目门禁，从记录回读已通过双审的送审版、已核验差异和人工决定，定位当前交付版本。

- Design 不完整或缺少该版通过证据，先补 Design 或完成独立双审。当前版 Design 尚未确认且无明确免除时，等待该版 Design 的答复。用户要求查看 Plan 时也适用这道门禁。已经得到的答复只消费一次。
- 仅有 change 或缺 Plan，回联合编写用 `writing-plans` 补 Plan。change 不全或严格校验失败，补 change 并重跑该 change 的严格校验。追溯不全，补齐映射。以上情况均保持实施阻塞。
- 两份产物齐备且首次送审条件满足时，在同一送审版上完成联合双审。对审后的修订，检查最终交付版相对送审版的全部差异是否已按 `cadence-subagents-config` 的代理协议核验。记录前后版本、差异、受影响的结论、核验人及结果。阻断项关闭且差异均有记录后签收，恢复时沿用已有核验，只补缺失的证据。
- 涉及 change 或工作包映射的修订须保持最终版严格校验通过、双向可追溯。超出已确认 Design 的范围、架构或验收边界时先返回 Design 阶段。
- 联合双审通过后，只在显式要求看 Plan 且尚未答复时等待一次。其余按委托实施或交付。

## 客户端调用

每项任务先调用 `using-superpowers`。需要仓库操作时选择当前阶段必调 Skill，在首个用户可见段落给出阶段、change、Plan、Skill 及用途，随后读取规则和使用仓库工具。Claude/Kimi 使用原生调用，Codex/pi/omp 从清单选择并全文读取对应 Skill。纯概念问答只调 `using-superpowers`，直接回答。必调 Skill 不可用时停止并报告。如缺完成证据，先加载验证纪律，再执行验证或说明仍待验证的内容。
