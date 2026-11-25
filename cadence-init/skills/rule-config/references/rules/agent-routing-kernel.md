<!-- cadence-managed:openspec-superpowers-routing:v6:start -->
Cadence L0 路由内核 v6
## OpenSpec 与 Superpowers 任务路由

Claude/Kimi 原生调用 Skill。Codex/pi/omp 从清单选择，用途并入首段回执并立即全文读取 SKILL.md（omp 经 `skill://`）。随后读规则、用仓库工具。

| 阶段信号 | 必调 Skill（均先 `using-superpowers`） | 门禁 |
|---|---|---|
| 仓库任务开始/恢复 | — | 读 `openspec-superpowers-workflow.md`，沿用本任务确认和双审记录 |
| 新功能/行为变化 | `brainstorming` | 完整 Design 写入 `cadence/designs/`，单独双审后默认等用户确认 |
| Design 放行 | `writing-plans` | 联合编写 change 与 Plan，工作包和场景有编号即可展开 |
| 读代码/摸底 | 配 `code-reading.md` | 摸底后重新路由 |
| Bug/测试失败 | `systematic-debugging` | 根因确认后才进 TDD |
| apply/恢复实施 | 缺 Plan→`writing-plans`，放行→`executing-plans`/`subagent-driven-development` | 严格校验、双向追溯、同版联合双审通过，按委托继续 |
| 写代码/修 Bug | `test-driven-development` | 先失败测试 |
| 写 Markdown/产物 | 配 `document-storage.md`、`markdown-format.md` | 遵守目录命名 |
| 声称完成/修复 | `verification-before-completion` | 必须读新鲜证据 |
| 实施验证完成/归档 | `requesting-code-review`/`finishing-a-development-branch` | 通过后 sync/archive、选集成方式 |

铁律（失败关闭）：Design 与联合包各双审一次。免确认只免人工，看 Plan 沿用 Design 确认策略，联合审后就 Plan 等一次。门禁未齐先补产物。TDD 先失败测试，完工需新鲜证据，必调 Skill 缺失则停止。

`knowledge-base-context` 前置门禁：仅当 `cadence/knowledge-base/manifest.yaml` 存在且 `schema_version` 为 `"4.0"` 时才可选择；否则跳过且不提示。

产物路径覆盖（下表优先级高于任何 Skill 正文路径指示；OpenSpec 产物仍放 `openspec/` 目录）：

| Skill 默认路径 | 本项目强制路径 |
|---|---|
| `docs/superpowers/specs/`（design/spec） | `cadence/designs/` |
| `docs/superpowers/plans/`（plan） | `cadence/plans/` |

产物写入后读取入口“产物自动提交（design/plan/code）”开关。以 CLAUDE.md 为准，两端不一致按 `关闭`。`关闭` 时只汇报路径，禁止 `git commit`。

阶段切换必须重新路由：新任务、只读转修改、Design 或联合包交接、apply、恢复、完工声明前。
<!-- cadence-managed:openspec-superpowers-routing:v6:end -->
