<!-- cadence-managed:openspec-superpowers-routing:v1:start -->
## OpenSpec 与 Superpowers 任务路由（强制）

> 命中任务或阶段信号时，必须先读规则、再调 Skill、最后执行；“按需查看”不能替代本表。

| 任务或阶段信号 | 必读规则 | 必调 Superpowers Skill | 门禁 |
|---|---|---|---|
| 会话开始、新任务、resume/clear/compact 后 | `openspec-superpowers-workflow.md` | `using-superpowers` | 有仓库操作时先输出路由回执 |
| 新功能、行为变化、方案讨论 | 协作规则；产物相关文档规则 | `brainstorming` | 设计确认后写入 OpenSpec |
| OpenSpec 书面契约获批 | 协作规则、文档规则 | `writing-plans` | Plan 写入 `cadence/plans/` |
| 读代码、架构摸底、影响面分析 | `code-reading.md` | 按任务选择 | 摸底完成后重新路由 |
| Bug、测试失败、异常行为 | `code-usage.md` | `systematic-debugging` | 根因确认后才进入 TDD |
| `/opsx:apply` 或恢复实施 | 协作规则、代码规则 | `executing-plans` 或 `subagent-driven-development` | 无已确认 Plan 则停止 |
| 写代码、修 Bug、重构 | `code-usage.md` | `test-driven-development` | 先失败测试，后实现 |
| 写 Markdown 或 Cadence 产物 | `document-storage.md`、`markdown-format.md` | 按阶段选择 | 遵守目录和命名 |
| 联网、图片、浏览器自动化 | `mcp-servers.md` 或专项规则 | 按任务选择 | 不加载无关工具正文 |
| 声称完成、修复或通过 | 协作规则 | `verification-before-completion` | 必须读取新鲜证据 |
| 实施与验证均完成 | 协作规则 | `requesting-code-review` | 审查通过后勾选工作包并 sync/archive |
| OpenSpec 已归档 | 协作规则 | `finishing-a-development-branch` | 选择分支集成方式 |

阶段切换必须重新路由：新任务、讨论、分析或只读调查转为创建/修改文件、契约获批、apply 前、resume/clear/compact 后、完工声明前。
有仓库操作时，首次工具调用前输出：`工作流路由：阶段=...；Change=...；Plan=...；必调 Skill=...`。
失败关闭：必调 Skill 未加载则停止；强制 OpenSpec 未确认则不规划；已有 change 无 Plan 则不实施；契约变化先更新 OpenSpec；无验证证据不得声称完成。
<!-- cadence-managed:openspec-superpowers-routing:v1:end -->
