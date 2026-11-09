# network-skill-install Specification

## Purpose
定义仓库网络安装脚本 install.sh 的行为契约：镜像 clone、已装更新、三层软链、冲突保护、非 git 目录处理、卸载与旧 marketplace 残留提示，使 cadence-init 的 skills 可被 Claude Code、pi、Codex、Kimi Code 四类 coding agent 共同消费。

## Requirements

### Requirement: 镜像网络安装

install.sh MUST 按固定顺序尝试 3 个镜像 clone `https://github.com/michaelChe956/Cadence-skills.git` 到 `~/.agents/Cadence-skills`（顺序：ghfast.top 前缀 → gh-proxy.com 前缀 → mirror.ghproxy.com 前缀）；某一镜像 clone 成功 MUST 立即停止尝试。全部镜像失败 MUST 以明确错误退出，MUST NOT 使用直连 GitHub 兜底，MUST NOT 进入任何离线降级分支。

#### Scenario: 首个镜像可用时直接成功

- **WHEN** ghfast.top 镜像 clone 成功
- **THEN** 不再尝试后续镜像，安装继续进入软链同步阶段

#### Scenario: 全部镜像失败时报错退出

- **WHEN** 3 个镜像的 clone 全部失败
- **THEN** 脚本以非零退出码报错退出，输出已尝试的镜像清单，不创建或修改 `~/.agents/Cadence-skills`

### Requirement: 已安装时更新

`~/.agents/Cadence-skills` 已存在且为 git 仓库时，install.sh MUST 执行 `fetch --all` 后以 fast-forward 方式更新到远程默认分支；更新使用的 remote URL 不可达时 MUST 轮换为下一镜像地址重试。更新失败 MUST 给出可操作的错误信息。

#### Scenario: 已安装仓库正常更新

- **WHEN** `~/.agents/Cadence-skills` 已存在且为 git 仓库，且当前镜像可达
- **THEN** 仓库更新到远程最新提交，随后重新执行三层软链同步

#### Scenario: 更新时镜像不可达则轮换

- **WHEN** 当前 remote URL 拉取失败
- **THEN** 脚本将 remote 切换为镜像清单中的下一地址并重试，直至成功或清单耗尽后报错

### Requirement: 非 git 目录拒绝安装

目标目录已存在但不是 git 仓库时，install.sh MUST NOT 静默使用该目录，MUST NOT 自动删除；MUST 提示用户手动删除 `~/.agents/Cadence-skills` 后重新运行安装。

#### Scenario: 非 git 目录给出处理指引

- **WHEN** `~/.agents/Cadence-skills` 存在但缺少 git 元数据
- **THEN** 脚本输出删除该目录并重新运行的指引后以非零退出码退出，不改动该目录内容

### Requirement: 三层软链同步

install/更新完成后，对仓库 `cadence-init/skills/` 下每个含 `SKILL.md` 的 skill，install.sh MUST 保证三层软链：`~/.agents/skills/<skill>` 指向仓库内该 skill 目录；`~/.claude/skills/<skill>` 与 `~/.codex/skills/<skill>` 指向 `~/.agents/skills/<skill>`。Codex 用户技能层 MUST 为扁平布局（`$CODEX_HOME/skills/<skill>/SKILL.md`），MUST NOT 使用 `~/.codex/skills/skills/<skill>` 嵌套布局。安装完成输出 MUST 给出 Claude Code、pi、Codex、Kimi Code 四类 agent 的 skill 消费路径与可见性验证方式，并 MUST 区分 Codex 用户层与系统层。

#### Scenario: 全新安装后三层软链齐全

- **WHEN** 在无任何历史安装的环境中完成 install.sh
- **THEN** 14 个 skill 在三层目录中均有软链，且各层软链按上述指向解析到真实文件，Codex 层条目直接位于 `~/.codex/skills/<skill>` 下

#### Scenario: 完成输出覆盖四类 agent

- **WHEN** 安装成功结束
- **THEN** 输出包含 Claude Code（`~/.claude/skills`）、pi 与 Codex 与 Kimi Code（`~/.agents/skills`，Codex 另含 `~/.codex/skills`）的路径与验证命令，并区分 Codex 用户层（`~/.codex/skills`）与系统层（`~/.codex/skills/.system`）

### Requirement: 冲突保护与所有权证明

三层软链同步与卸载 MUST 使用同一套符号级所有权证明（基于 readlink 的精确比对，MUST NOT 以目标路径前缀作为所有权依据）：共享层条目仅当其链接目标精确等于 `~/.agents/Cadence-skills/cadence-init/skills/<skill>` 时视为本安装机制托管；Claude 层与 Codex 层条目仅当其链接目标精确等于 `~/.agents/skills/<skill>` 且该共享层条目本身通过所有权证明时视为托管。目标位置是普通文件、普通目录或无法通过所有权证明的软链（含指向共享层非 cadence 名称的第三方投影链）时 MUST NOT 覆盖、MUST NOT 删除，MUST 输出警告并跳过，且不因此判定安装失败；目标是通过所有权证明的托管软链且指向不符时 MUST 原子替换。仓库中已移除的 skill 的清理 MUST 先在共享层确定待清理 skill 名集合，再仅对该集合清理 Claude 层与 Codex 层中的对应条目；**共享层同名条目已不存在时**，下游层中 `readlink` 精确等于 `~/.agents/skills/<skill>` 的链 MUST 判定为遗留投影并清理（第三方投影链 MUST 保持存活）。无法证明所有权的 dangling 链 MUST 仅告警并给出手动清理命令。卸载（`--uninstall`）仅删除通过所有权证明的条目，`--delete-repo` 时才连同删除 `~/.agents/Cadence-skills`；用户其他文件 MUST NOT 被触碰。

#### Scenario: 用户普通文件不被覆盖

- **WHEN** `~/.claude/skills/pre-check` 已是用户自建的普通目录
- **THEN** 安装输出警告并跳过该条目，用户目录内容保持不变，其余 skill 正常安装

#### Scenario: 孤儿托管软链被清理

- **WHEN** 上一版本安装过的某 skill 已从仓库 `cadence-init/skills/` 移除
- **THEN** 三层目录中指向该 skill 的托管软链被删除，非托管条目不受影响

#### Scenario: 共享层缺失后的下游遗留投影被清理

- **WHEN** 共享层已不存在某 skill 条目，而 Claude 层或 Codex 层仍留有 `readlink` 精确等于 `~/.agents/skills/<skill>` 的链
- **THEN** 该链被清理，不再以断链形式长期残留

#### Scenario: 卸载保留用户文件

- **WHEN** 执行 `--uninstall` 且 `~/.agents/skills` 中存在用户自建条目
- **THEN** 仅通过所有权证明的托管软链被移除，用户自建条目与 `~/.agents/Cadence-skills` 仓库保持不变

#### Scenario: 第三方投影链在安装与卸载中均存活

- **WHEN** Claude 层与 Codex 层存在指向 `~/.agents/skills/<非 cadence 名>` 的合法第三方投影链（该共享层条目指向第三方目录），随后执行安装或 `--uninstall`
- **THEN** 这些第三方投影链全部保持不变，输出不含针对它们的删除记录

#### Scenario: 无法证明所有权的 dangling 链仅告警

- **WHEN** 某层存在链接目标前缀形似托管但无法通过所有权证明且已 dangling 的软链
- **THEN** 安装输出告警与手动清理命令，不删除该链

### Requirement: 旧 marketplace 残留提示

install.sh 运行时 MUST 检测旧安装残留：`~/.claude/plugins/marketplaces/cadence-skills-local` 目录与 `~/.claude/plugins/known_marketplaces.json` 中的 `cadence-skills-local` 键；检测到时 MUST 输出残留项与对应的手动清理命令，MUST NOT 自动删除目录或修改 JSON 文件。

#### Scenario: 检测到旧安装残留

- **WHEN** 环境中存在旧 marketplace 安装目录或 known_marketplaces.json 残留键
- **THEN** 脚本列出残留项、给出手动清理命令，安装流程本身继续正常完成

### Requirement: 预览模式

install.sh MUST 提供 `--dry-run`：按与真实安装相同的逻辑计算全部将执行的动作（将创建、将替换、将清理、将告警跳过）并输出，MUST NOT 执行任何网络拉取、文件创建、替换或删除。`--dry-run` 的输出计划 MUST 与随后真实执行的结果一致（除真实执行时的网络与远程状态因素外）。

#### Scenario: dry-run 零落盘

- **WHEN** 在任一环境执行 `--dry-run`
- **THEN** 退出码为 0，输出完整动作计划，且三层目录、仓库目录与所有软链在执行前后完全不变

#### Scenario: dry-run 计划与实装一致

- **WHEN** 同一环境先执行 `--dry-run` 再执行真实安装
- **THEN** 真实安装实际执行的动作集合与 dry-run 输出的计划一致，无计划外删除或替换

### Requirement: 发布验证分层

install.sh 交付前 MUST 通过自动化门禁：shellcheck 静态检查零告警；以隔离 HOME 运行的安装/重复安装/非 git 目录/卸载/第三方投影链共存全流程测试；以及 14 个 skill × 三层的链接解析矩阵（使用含第三方形状软链的回归 fixture）。真实环境中 Claude Code、pi、Codex、Kimi Code 四类 agent 的可见性冒烟为 SHOULD 级一次性人工验证：发布前 SHOULD 补跑并留档，跳过时 MUST 在变更记录中书面豁免。

#### Scenario: 隔离环境全流程测试通过

- **WHEN** 以隔离 HOME 依次执行安装、重复安装、非 git 目录场景、卸载与第三方投影链共存场景
- **THEN** 各场景行为符合本 spec，且不触碰真实用户目录

#### Scenario: 链接解析矩阵通过

- **WHEN** 在含第三方形状软链的隔离 fixture 上完成安装
- **THEN** 14 个 skill 在三层均可解析到 `SKILL.md`，且第三方形状软链全部存活

#### Scenario: 四类 agent 可见性验证

- **WHEN** 在真实环境完成安装后分别运行四类 agent 的 skill 列举
- **THEN** Claude Code、pi、Codex、Kimi Code 均能发现 `pre-check` 等 cadence-init skills（该验证为 SHOULD，豁免须留档）

### Requirement: Codex 旧嵌套层迁移

install.sh MUST 把旧布局 `~/.codex/skills/skills/<skill>` 中 `readlink` 精确等于 `~/.agents/skills/<skill>` 的受管链接迁移到新布局 `~/.codex/skills/<skill>`；迁移 MUST 复用既有原子替换语义，且 MUST 复用所有权证明——共享层同名条目已存在时，该条目自身必须通过所有权证明，否则旧条目 MUST 保留并告警。删除旧条目前 MUST 复核旧条目仍是指向共享层同名词的软链、新布局条目已建立且其 `SKILL.md` 可读，任一条件不满足时 MUST 保留旧条目并告警。旧层目录仅在迁移与孤儿清理完成后不再包含任何条目时 MUST 被删除；若仍含非托管条目（普通文件、目录、第三方链）MUST 保留并告警，MUST NOT 递归删除。

#### Scenario: 旧嵌套层受管链接被迁移

- **WHEN** 环境中存在旧布局的受管链接 `~/.codex/skills/skills/pre-check` → `~/.agents/skills/pre-check`
- **THEN** 新布局 `~/.codex/skills/pre-check` 被创建且可解析到 `SKILL.md`，旧层目录在迁空后被删除

#### Scenario: 旧嵌套层含非托管条目时保留并告警

- **WHEN** 旧层目录中存在非本机制托管的条目（普通文件、目录或第三方链）
- **THEN** 该条目保持原样，旧层目录被保留并输出告警

#### Scenario: 旧条目的共享层目标无法证明归属时保留

- **WHEN** 旧嵌套层条目指向共享层同名路径，但共享层该条目是用户普通目录或指向第三方目录的软链
- **THEN** 旧条目不被认领也不被删除，安装输出告警说明无法证明归属

#### Scenario: 新布局条目未建立成功时保留旧条目

- **WHEN** 迁移执行时扁平 Codex 层的同名条目未建立或其 `SKILL.md` 不可读
- **THEN** 旧嵌套层条目保留并输出告警，不删除可用入口

### Requirement: 投影入口可读性校验

install.sh MUST 在软链同步完成后校验各层每个受管条目的 `SKILL.md` 可读（可打开读取）。校验 MUST 覆盖共享层、Claude 层与 Codex 层。校验发现不可读条目时 MUST 区分两种情形：正确目标本身可读而链接目标不符时，MUST 以原子替换重建该链接；正确目标本身不可读（技能源 `SKILL.md` 缺失或不可读）时，MUST 告警说明根因并给出修复指引，MUST NOT 假称已修复。所有权不可证明时 MUST 输出告警与手动清理命令，MUST NOT 删除该条目，且 MUST NOT 因此判定安装失败。校验结果 MUST 在安装输出中体现。

#### Scenario: 断链受管入口被重建

- **WHEN** 某受管条目的链接目标与正确目标不符、导致 `SKILL.md` 不可读，且正确目标可读、所有权可证明
- **THEN** 该链接被原子替换为正确目标，校验后 `SKILL.md` 可读

#### Scenario: 技能源不可读时只报告根因

- **WHEN** 某 skill 的仓库源 `SKILL.md` 不可读，导致各层入口均不可读
- **THEN** 安装输出告警该技能源路径不可读并给出修复指引，不声称入口已恢复可读

#### Scenario: 不可读且无法证明归属的入口仅告警

- **WHEN** 某条目不可读且无法通过所有权证明归属
- **THEN** 安装输出告警与手动清理命令，条目保持原样，安装其余部分继续完成

### Requirement: Codex 技能根完整性扫描

install.sh MUST 只读扫描 `~/.codex/skills` 下的全部技能入口（含嵌套命名空间目录下的条目，深度至多两层），凡 `SKILL.md` 不可读的入口 MUST 输出告警，列出绝对路径与其 `readlink` 目标，并给出手动清理命令。扫描 MUST NOT 删除任何非本安装机制托管的目录或文件；`~/.codex/skills/.system` 与插件缓存目录 MUST NOT 被告警为异常（其内容由 Codex 自身管理）。

#### Scenario: 根下失效命名空间目录被告警

- **WHEN** `~/.codex/skills/superpowers/using-superpowers/SKILL.md` 不可读（链接目标已失效）
- **THEN** 安装输出告警该入口的绝对路径与 `readlink` 目标并给出手动清理命令，且不删除任何文件

#### Scenario: 系统技能目录不被误报

- **WHEN** `~/.codex/skills/.system` 下技能全部可读
- **THEN** 输出不含针对 `.system` 的告警
