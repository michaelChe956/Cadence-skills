# Design

## 1. 事实基线（codex-cli 0.167.0 实测）

用隔离 `CODEX_HOME` 跑 `codex debug prompt-input`，逐条验证：

| 探针 | 布局 | 清单渲染 | 结论 |
|---|---|---|---|
| A | `<CODEX_HOME>/skills/a-skill/SKILL.md` | `r1/a-skill/SKILL.md` | 根下一层即可发现 |
| B | `<CODEX_HOME>/skills/skills/b-skill/SKILL.md` | `r1/skills/b-skill/SKILL.md` | 递归发现，路径按根相对渲染（多一层 = 多一个“命名空间”段） |
| E | `<CODEX_HOME>/skills/superpowers/e-skill/SKILL.md` | `r1/superpowers/e-skill/SKILL.md` | 命名空间目录形态与插件层同构 |
| D | 断链 `<CODEX_HOME>/skills/skills/d-skill` | 不出现 | 断链入口整体跳过，不进清单 |
| 插件 | `codex plugin add superpowers@openai-api-curated` | 根 = `<CODEX_HOME>/plugins/cache/<marketplace>/superpowers/<rev>/skills` | 插件技能不在 `~/.codex/skills/<plugin>`，官方插件目录与用户技能目录分离 |

真实 `~/.codex/skills` 的构成（Codex 自带 + 本机实况）：`.system/`（Codex 内置系统技能，含 `skill-creator`/`skill-installer`/`imagegen`/`openai-docs`）、`skills/`（Cadence 投影层）。Codex 同时扫描 `~/.agents/skills`，同一 canonical 文件只注入一次（实测 `~/.codex/skills/skills/*` 与 `~/.agents/skills/*` 指向同一文件时，清单只出现后者）。

**推论**：本次故障条目 `r0/superpowers/using-superpowers/SKILL.md` 的形态 = “Codex 根下一个命名空间目录”，Cadence 从不创建这种目录（`git log -S".codex/skills/superpowers"` 全历史无命中）；它是插件/遗留目录，且其下条目在清单生成时可读、之后失效（断链），Codex 才会在清单里留下一个解析不到的路径。Cadence 的义务因此是：**自己投影的每个入口都必须可读，并对根下不可读入口给出可执行告警**。

## 2. 架构边界

- **目录职责**
  - `~/.agents/skills/<skill>`：共享层，指向仓库 `~/.agents/Cadence-skills/cadence-init/skills/<skill>`。四端（Claude Code / pi / Codex / Kimi Code）的通用消费面。
  - `~/.claude/skills/<skill>`：Claude Code 层，指向共享层。
  - `~/.codex/skills/<skill>`：Codex 用户层，指向共享层。**扁平**，与 `~/.codex/skills/.system/<skill>` 同构。
  - `~/.pi/agent/skills/<skill>`：pi 层，由 `/pre-check` 的 superpowers-links 阶段管理（Superpowers 来源直连，不经共享层）。
- **不归本变更管理**：`~/.codex/skills/.system`（Codex 内置，随 Codex 升级）、`<CODEX_HOME>/plugins/cache/**`（Codex 插件缓存）、`~/.codex/skills` 下任何非本机制托管的目录。安装器只读扫描并告警，绝不删除。
- **命名冲突**：`~/.codex/skills/<name>` 与插件命名空间目录同名时，安装器把该目录视为非托管对象 → 告警跳过（不覆盖）。仓库技能名（`pre-check`/`skill-creator`/`knowledge-base-*`/…）当前与已知插件 id（`superpowers`/`game-studio`/…）无重叠。

## 3. 所有权证明与清理口径

| 层 | 判定为“本机制托管”的条件 | 清理时机 |
|---|---|---|
| 共享层 | `readlink` 精确等于 `~/.agents/Cadence-skills/cadence-init/skills/<name>` | 名字已不在仓库源集合 → 清理 |
| Claude 层 / Codex 层 | `readlink` 精确等于 `~/.agents/skills/<name>` **且**共享层同名条目通过所有权证明 | 同上 |
| Claude 层 / Codex 层（新增分支） | `readlink` 精确等于 `~/.agents/skills/<name>` **且**共享层不存在同名条目 | 清理（共享层已无该名 → 目标必然不存在，属本机制遗留投影） |
| 任何其他 | 不满足以上 | 不动，告警 + 手动命令 |

新增分支不触碰第三方投影链：第三方投影链的定义是“共享层存在同名条目、指向第三方目录”，此时共享层条目存在 → 走原判定 → 存活（与既有 spec 场景一致）。

## 4. 迁移策略

1. 安装时先按新布局（`~/.codex/skills/<name>`）规划链接动作。
2. 再扫描旧层 `~/.codex/skills/skills/`：其中 `readlink` 等于 `~/.agents/skills/<name>` 的受管链接迁到新层；旧层中非受管条目（普通文件/目录/第三方链）保留并告警。
3. 旧层迁空后，仅当该目录为空（不含任何条目）才删除目录本身；否则保留并告警（可能含插件目录或用户文件）。
4. 迁移与新链接创建都走既有原子替换语义（临时链 + `mv -T`，BSD 回退 `ln -sfn`）。

## 5. 失败处理

- 校验阶段发现的不可读入口：
  - 所有权可证明 → 重建链接（`CREATE`/`REPLACE` 语义），并在报告中标记为“已修复”。
  - 所有权不可证明 → `WARN-MANUAL`，输出 `readlink` 目标与手动命令，**不导致安装失败**（与既有冲突保护口径一致：告警跳过不判失败）。
- Codex 根完整性扫描发现的非托管不可读入口 → 只告警，列出绝对路径与 `readlink` 目标，附 `rm -i -- <path>` 手动命令；不自动删除（可能是插件缓存失效的中间态，用户需自行确认）。

## 6. 权衡

- **为什么不用 `~/.codex/skills/skills` 续用**：实测 Codex 递归发现它，但清单路径多一层且与插件命名空间同形；官方约定与 Codex 自身 `.system` 层都是一层。统一后“清单里的路径 = 磁盘上真实可读的路径”的判定规则不再有歧义。
- **为什么不直接删掉 Codex 兼容层**：老版本 Codex 只读 `~/.codex/skills`；保留扁平兼容层即可覆盖，无需保留嵌套层。
- **为什么校验阶段不判安装失败**：安装器是投影器，不拥有用户目录的全部所有权；不可读且无法证明归属的条目属于环境问题，判失败会阻断其余 skill 的安装。报告与告警承担可见性。
