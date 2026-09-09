# pre-check v2 真实 OpenSpec 投影基线

## 采集边界

- 采集日期：2026-09-05
- v2 来源：以 `27e87e2` 旧脚本为行为基准，修正 fixture 为真实 OpenSpec 形态后重新采集。
- v1 作废原因：旧 fixture 使用 brainstorm.md、write-plan.md、execute.md、review.md、verify.md 旧命名，掩盖严格 OpenSpec 投影门槛；controller 于 2026-09-05 依据 oracle 终审 ruling 要求废弃该虚构形态。
- 网络口径勘误：v1 基线采集时（2026-09-04，用当时的新实现脚本）因采集器未设 `CADENCE_TEST_GIT_CANDIDATES`，回退真实网络候选 `https://github.com/obra/superpowers`（fetch SSL 失败约 90s）；v1 README“真实网络未使用”陈述失真，此为 v1 作废原因之一。v2 采集（`27e87e2` 旧脚本 + 本地 bare remote）无任何网络路径。本条为人工勘误；防覆盖守卫仅阻止采集器覆盖既有基线，不禁止人工勘误。
- 本次 v2 在隔离环境重采，使用 `.pi/skills/openspec-*/SKILL.md`、`.pi/prompts/opsx-*.md` 与 `.kimi-code/skills/openspec-*/SKILL.md` 真实布局
- 旧脚本：`cadence-init/skills/pre-check/scripts/pre-check.sh`
- 旧脚本 SHA-256：`8df737f9ad31c2dee6eabfcb773bca6a1d911be03ddefe8be5c54904409862e7`
- 旧 `SKILL.md`：`cadence-init/skills/pre-check/SKILL.md`
- 旧 `SKILL.md` SHA-256：`3d5d0f1b0010ed4b1a6b4570fdf4cfdc7ca296951b217a60eaca2f4f2b8a5c4c`
- 隔离根目录：仓库外临时目录（本次为 `/tmp/precheck-baseline.6DuGHL`，脚本结束自动删除）
- 真实 HOME、真实 API Key、真实网络：均未使用

## Fixture 配置

- 项目根：临时 `project/`，预置四端 OpenSpec 投影：Claude/Codex、Pi 的 5 个 `openspec-*/SKILL.md` + 5 个 `opsx-*.md`、Kimi 的 5 个 `openspec-*/SKILL.md`。
- 项目非目标 sentinel：`project-sentinel.txt`。
- Superpowers：临时 `home/.agents/superpowers/` 有效 Git worktree；`origin` 为同一临时目录内的 bare remote，分支为 `main`，HEAD 为 `abb4ed1440491a276b9ca0eab7194bd3f92514b2`。
- 软链：`~/.agents/skills`、`~/.codex/skills/skills`、`~/.claude/skills`、`~/.pi/agent/skills` 各预置 14 条直连 Superpowers 源的软链。
- HOME 非目标 sentinel：`home-sentinel.txt`。
- fake CLI：`npx 10.9.0`、`uvx 0.4.0`、`ast-grep 0.40.0`、`codegraph 0.8.0`、`openspec 1.2.0`；fake `pi list` 报告 `pi-mcp-adapter`。

## 运行命令

`HOME=<isolated-home> PATH=<fake-bin>:$PATH CADENCE_TEST_GIT_CANDIDATES=<local-bare-remote> bash <absolute-pre-check.sh> run --no-interrupt`，cwd 为隔离项目根。
旧脚本 stdout 保存为临时报告并未写入快照；stderr、临时目录和测试日志均排除。

## 快照格式与排除项

- 文件：`file <scope> <relative-path> <sha256>`。
- 软链：`link <layer> <name> readlink=<原始 readlink> resolved=<最终绝对目标>`。
- Git：`git origin ...`、`git branch ...`、`git head ...`。
- 排除：各 Git 元数据目录、报告、临时目录、时间戳备份和测试日志；非目标项目/HOME 条目保留。

## 目标白名单与冻结口径

后续兼容性测试必须复用同一 fixture 配置与同一快照器。四端 OpenSpec 投影、Superpowers Git 和四层软链是已预置的完成态，首跑预期为零写入且 `overall=success`；后续实现首跑以 v2 基线做 1:1 对照。防覆盖守卫保留并对 v2 生效。
