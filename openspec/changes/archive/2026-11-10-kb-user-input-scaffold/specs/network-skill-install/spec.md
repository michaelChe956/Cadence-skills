# network-skill-install 规格增量

## MODIFIED Requirements

### Requirement: 三层软链同步

install/更新完成后，对仓库 `cadence-init/skills/` 下每个含 `SKILL.md` 的 skill，install.sh MUST 保证三层软链：`~/.agents/skills/<skill>` 指向仓库内该 skill 目录；`~/.claude/skills/<skill>` 与 `~/.codex/skills/<skill>` 指向 `~/.agents/skills/<skill>`。Codex 用户技能层 MUST 为扁平布局（`$CODEX_HOME/skills/<skill>/SKILL.md`），MUST NOT 使用 `~/.codex/skills/skills/<skill>` 嵌套布局。安装完成输出 MUST 给出 Claude Code、pi、Codex、Kimi Code 四类 agent 的 skill 消费路径与可见性验证方式，并 MUST 区分 Codex 用户层与系统层。

#### Scenario: 全新安装后三层软链齐全

- **WHEN** 在无任何历史安装的环境中完成 install.sh
- **THEN** 15 个 skill 在三层目录中均有软链，且各层软链按上述指向解析到真实文件，Codex 层条目直接位于 `~/.codex/skills/<skill>` 下

#### Scenario: 完成输出覆盖四类 agent

- **WHEN** 安装成功结束
- **THEN** 输出包含 Claude Code（`~/.claude/skills`）、pi 与 Codex 与 Kimi Code（`~/.agents/skills`，Codex 另含 `~/.codex/skills`）的路径与验证命令，并区分 Codex 用户层（`~/.codex/skills`）与系统层（`~/.codex/skills/.system`）

### Requirement: 发布验证分层

install.sh 交付前 MUST 通过自动化门禁：shellcheck 静态检查零告警；以隔离 HOME 运行的安装/重复安装/非 git 目录/卸载/第三方投影链共存全流程测试；以及 15 个 skill × 三层的链接解析矩阵（使用含第三方形状软链的回归 fixture）。真实环境中 Claude Code、pi、Codex、Kimi Code 四类 agent 的可见性冒烟为 SHOULD 级一次性人工验证：发布前 SHOULD 补跑并留档，跳过时 MUST 在变更记录中书面豁免。

#### Scenario: 隔离环境全流程测试通过

- **WHEN** 以隔离 HOME 依次执行安装、重复安装、非 git 目录场景、卸载与第三方投影链共存场景
- **THEN** 各场景行为符合本 spec，且不触碰真实用户目录

#### Scenario: 链接解析矩阵通过

- **WHEN** 在含第三方形状软链的隔离 fixture 上完成安装
- **THEN** 15 个 skill 在三层均可解析到 `SKILL.md`，且第三方形状软链全部存活

#### Scenario: 四类 agent 可见性验证

- **WHEN** 在真实环境完成安装后分别运行四类 agent 的 skill 列举
- **THEN** Claude Code、pi、Codex、Kimi Code 均能发现 `pre-check` 等 cadence-init skills（该验证为 SHOULD，豁免须留档）