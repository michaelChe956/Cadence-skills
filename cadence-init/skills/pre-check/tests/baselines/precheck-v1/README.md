# pre-check v1 旧实现基线

## 采集边界

- 采集日期：2026-09-04
- 旧脚本：`cadence-init/skills/pre-check/scripts/pre-check.sh`
- 旧脚本 SHA-256：`8df737f9ad31c2dee6eabfcb773bca6a1d911be03ddefe8be5c54904409862e7`
- 旧 `SKILL.md`：`cadence-init/skills/pre-check/SKILL.md`
- 旧 `SKILL.md` SHA-256：`0dd1971a6af9ef8c0c762534ecb94038246800d7697abacab63ba40a71e3c886`
- 隔离根目录：仓库外临时目录（本次为 `/tmp/precheck-baseline.F6o4VO`，脚本结束自动删除）
- 真实 HOME、真实 API Key、真实网络：均未使用

## Fixture 配置

- 项目根：临时 `project/`，预置四端 OpenSpec 投影：Claude/Codex、Pi 的 5 个 skill + 5 个 prompt、Kimi 的 5 个 skill。
- 项目非目标 sentinel：`project-sentinel.txt`。
- Superpowers：临时 `home/.agents/superpowers/` 有效 Git worktree；`origin` 为同一临时目录内的 bare remote，分支为 `main`，HEAD 为 `ab37d3595e065d4c3f6d80be8234e762bb00e26e`。
- 软链：`~/.agents/skills`、`~/.codex/skills/skills`、`~/.claude/skills`、`~/.pi/agent/skills` 各预置 14 条直连 Superpowers 源的软链。
- HOME 非目标 sentinel：`home-sentinel.txt`。
- fake CLI：`npx 10.9.0`、`uvx 0.4.0`、`ast-grep 0.40.0`、`codegraph 0.8.0`、`openspec 1.2.0`；fake `pi list` 报告 `pi-mcp-adapter`。

## 运行命令

`HOME=<isolated-home> PATH=<fake-bin>:$PATH bash <absolute-pre-check.sh> run --no-interrupt`，cwd 为隔离项目根。
旧脚本 stdout 保存为临时报告并未写入快照；stderr、临时目录和测试日志均排除。

## 快照格式与排除项

- 文件：`file <scope> <relative-path> <sha256>`。
- 软链：`link <layer> <name> readlink=<原始 readlink> resolved=<最终绝对目标>`。
- Git：`git origin ...`、`git branch ...`、`git head ...`。
- 排除：各 Git 元数据目录、报告、临时目录、时间戳备份和测试日志；非目标项目/HOME 条目保留。

## 目标白名单与冻结口径

后续兼容性测试必须复用同一 fixture 配置与同一快照器。四端 OpenSpec 投影、Superpowers Git 和四层软链是已预置的完成态，旧脚本首跑预期为零写入且 `overall=success`；后续实现首跑以此基线做 1:1 对照。四端投影目标白名单为：`.claude/commands/opsx/`、`.claude/skills/openspec-*`、`.agents/skills/openspec-*`、`.pi/skills/`、`.pi/prompts/`、`.kimi-code/skills/`；HOME 侧白名单为 Superpowers 源目录和上述四层软链。不得以新实现快照覆盖本基线；如与审核结论冲突，保留证据并在 Task 8 标注差异原因。

## Task 8 对照前的绝对路径规范化

`tree.txt` 中的 `readlink`、`resolved` 与 `git origin` 会包含每次 `mktemp` 生成的随机隔离根前缀，不能直接进行跨次文本 diff。Task 8 在对照前必须使用同一规范化函数，将本次 fixture 的隔离根整体替换为 `<ISOLATION_ROOT>`，一次覆盖 `project/`、`home/` 和 `remote.git/` 三处，再比较基线与 old/new 快照；替换只针对这个已知隔离根前缀，不改动相对路径、哈希或其他内容。Python 测试复用 `helpers/fixture.py` 的 `normalize_snapshot_text` / `normalize_snapshot_file`；Bash 采集器提供同名 `normalize_snapshot_file`，可按 `normalize_snapshot_file <source> <destination> <isolation-root>` 调用。
