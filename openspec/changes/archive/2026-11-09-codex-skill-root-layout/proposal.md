# Proposal

## Why

Codex 运行时注入的 skills 清单里出现**指向不存在文件的入口**：`r0 = ~/.codex/skills`，条目却渲染为 `r0/superpowers/using-superpowers/SKILL.md`，而真实文件在 `~/.codex/skills/skills/using-superpowers/SKILL.md`（→ `~/.agents/skills/using-superpowers`）。读清单的 agent 按注入路径读文件必然先失败一次，再靠兜底探测才找到真实位置。

用 codex-cli 0.167.0 实测（本机 `codex debug prompt-input`）确认了三条决定性事实：

1. **Codex 的技能根是递归发现的**，一个技能 = 根下任意层级中含可读 `SKILL.md` 的目录；清单里的路径按“发现它的那个根”相对渲染。
2. **断链入口会被整体跳过**，不会进入清单——所以清单里出现“路径不存在”的条目，必然来自一个**当时可读、之后失效**的目录（典型：指向插件缓存的链接在缓存被清理后失效）。
3. **Cadence 自己的 Codex 投影层 `~/.codex/skills/skills/<skill>` 不是 Codex 的官方约定**：Codex 官方用户技能位是 `$CODEX_HOME/skills/<skill>/SKILL.md`（Codex 自身的系统技能也放在 `$CODEX_HOME/skills/.system/<skill>/SKILL.md`，同样只有一层）。多出来的 `skills/` 一层在清单里表现为一个“名为 skills 的命名空间”，与插件命名空间目录（例如 `~/.codex/skills/superpowers/`）长得一样，正是本次误判的直接来源。

同时暴露三个仓库侧缺陷：

- 投影链任一环断链（如 `~/.codex/skills/skills/project-analysis`）时，安装器不做任何可读性校验，清单里的入口可能指向不存在的文件。
- 共享层同名条目一旦先被删除，下游 Claude/Codex 层的同名牌就无法再通过所有权证明，永久残留为断链。
- 仓库已移除 skill（如 `project-analysis`）在三层的清理依赖“共享层仍存在且指向仓库源”，任一环先失效就留下永久残留。

本变更把 Codex 用户技能根统一到官方扁平布局，并给安装链路补上可读性校验与遗留清理，使“清单里的每个入口都可读”成为安装器的可验证义务。

## What Changes

- **Codex 用户技能根统一为 `~/.codex/skills`（扁平）**：`~/.codex/skills/<skill>` → `~/.agents/skills/<skill>`，与 Codex 官方约定及其 `.system` 层一致；共享层 `~/.agents/skills` 与 Claude 层 `~/.claude/skills` 不变。
- **旧嵌套层迁移**：安装时把 `~/.codex/skills/skills/<skill>` 的受管链接迁到 `~/.codex/skills/<skill>`；旧目录仅在迁空且不再含受管链接时删除。
- **新增可读性校验阶段**：安装/更新后校验各层每个受管条目的 `SKILL.md` 可读；不可读且所有权可证明 → 重建链接；不可证明 → 告警并给出手动命令，不静默失败。
- **新增 Codex 根完整性扫描**：枚举 `~/.codex/skills` 下所有入口（含嵌套命名空间目录），凡 `SKILL.md` 不可读即告警列出路径与 `readlink` 目标（不自动删除非本机制托管的目录）。
- **孤儿清理加固**：共享层同名条目已不存在时，下游层 `readlink` 精确等于 `~/.agents/skills/<name>` 的链判定为本机制遗留投影并清理；共享层条目仍在时行为不变（第三方投影链继续存活）。
- **skill-creator 双版本口径写进文档**：Codex 系统版（`~/.codex/skills/.system/skill-creator`，随 Codex 升级）与仓库版（`~/.agents/skills/skill-creator` → 投影到 `~/.codex/skills/skill-creator`）同时进入清单且不互相遮蔽，文档给出选用约定。

## Capabilities

### Modified Capabilities

- `network-skill-install`: 三层软链同步的 Codex 层路径、所有权证明与孤儿清理口径、新增可读性校验与 Codex 根完整性扫描要求。
- `pre-check-scripted-execution`: superpowers-links 阶段的 Codex 层目标目录与链接可解析性校验口径。

### New Capabilities

（无）

## Impact

- `install.sh`：Codex 根常量、迁移动作、所有权判定、清理口径、新增校验与扫描阶段、安装完成输出路径。
- `cadence-init/skills/pre-check/scripts/pre-check.sh`：superpowers-links 阶段的 Codex 层目录与校验。
- 测试：`tests/test-install.sh`、pre-check 集成测试与基线快照、CI 链接矩阵 fixture 的 Codex 根。
- 文档：`README.md`、`readmes/` 目录约定表、Cadence 知识文档目录约定表。
- 行为变更：已安装机器下次运行 `install.sh` 或 `/pre-check` 时，Codex 投影层从 `~/.codex/skills/skills/` 迁到 `~/.codex/skills/`；仓库技能名与 Codex 插件 id 无重叠，不覆盖 `~/.codex/skills/.system` 或插件目录。
- 无 **BREAKING** 契约变更：三层所有权证明的严格性不放宽（第三方投影链仍必须存活），仅对“共享层条目已不存在”的下游残留新增一条判定分支。
