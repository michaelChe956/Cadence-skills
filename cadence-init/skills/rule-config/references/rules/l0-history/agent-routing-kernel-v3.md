<!-- cadence-managed:openspec-superpowers-routing:v3:start -->
## OpenSpec 与 Superpowers 任务路由

Skill 调用：Claude/Kimi 原生调用；Codex/pi 清单选择后将用途并入首段回执，并立即全文读取对应 SKILL.md。首段输出路由回执；Skill 调用后才读仓库规则或用仓库工具。

| 阶段信号 | 必调 Skill（均先 `using-superpowers`） | 门禁 |
|---|---|---|
| 仓库任务开始/恢复 | — | 首段输出回执；流程见 `openspec-superpowers-workflow.md` |
| 新功能/行为变化 | `brainstorming` | 设计确认后写入 OpenSpec |
| 契约获批 | `writing-plans` | Plan 写入 `cadence/plans/` |
| 读代码/摸底 | 配 `code-reading.md` | 摸底后重新路由 |
| Bug/测试失败 | `systematic-debugging` | 根因确认后才进 TDD |
| apply/恢复实施 | 无 Plan→`writing-plans`；有→`executing-plans`/`subagent-driven-development` | 无 Plan 则停止 |
| 写代码/修 Bug | `test-driven-development` | 先失败测试 |
| 写 Markdown/产物 | 配 `document-storage.md`、`markdown-format.md` | 遵守目录命名 |
| 声称完成/修复 | `verification-before-completion` | 必须读新鲜证据 |
| 实施验证完成/归档 | `requesting-code-review`/`finishing-a-development-branch` | 通过后 sync/archive、选集成方式 |

铁律（失败关闭）：达 OpenSpec 阈值（新行为/公共契约/验收边界变化）先 brainstorming→OpenSpec；无已确认 Plan 不改实现；TDD 先失败测试；无新鲜证据不声称完成；必调 Skill 缺失则停止。

`knowledge-base-context` 前置门禁：仅当 `cadence/knowledge-base/manifest.yaml` 存在且 `schema_version` 为 `"4.0"` 时才可选择；否则跳过且不提示。

产物路径覆盖（下表优先级高于任何 Skill 正文路径指示；OpenSpec 产物仍放 `openspec/` 目录）：

| Skill 默认路径 | 本项目强制路径 |
|---|---|
| `docs/superpowers/specs/`（design/spec） | `cadence/designs/` |
| `docs/superpowers/plans/`（plan） | `cadence/plans/` |

产物自动提交开关：完成 design/plan 文档或实现类产物（代码、测试、配置）写入后读取入口“产物自动提交（design/plan/code）”开关，`关闭` 时禁止 `git commit`、只汇报路径；CLAUDE.md 为准、不一致按 `关闭`。

阶段切换必须重新路由：新任务、只读转修改、契约获批、apply 前、上下文恢复后、完工声明前。
<!-- cadence-managed:openspec-superpowers-routing:v3:end -->
