# codex-skill-root-layout

统一 Codex 用户技能根布局（扁平 `~/.codex/skills/<skill>`），补齐投影入口可读性校验与 Codex 技能根完整性扫描，并修复下游断链永久残留的清理缺口。

- 安装器：`install.sh`（Codex 层常量、旧嵌套层迁移、所有权判定、可读性校验、根扫描）
- pre-check：`superpowers-links` 扁平化 + `verify` 四层可解析性复核
- 契约：`network-skill-install`、`pre-check-scripted-execution`（增量已并入主规范）
- 计划：`cadence/plans/2026-11-09_计划_实施_Codex技能根布局统一与清单可读性校验_v1.0.md`
