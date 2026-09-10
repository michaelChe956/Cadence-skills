# CI 触发门禁（CI Trigger Gating）

> **目的**：CI 只为「会影响安装、Skills、规则与测试代码的变更」付费；纯文档变更不触发任何工作流，节省公共与 self-hosted runner 资源。
> **背景**：2026-09-10 五端文档口径修正（README/readmes 四类→五端）触发了完整 CI，属于纯文档改动的无效消耗。此后以工作流 paths 过滤为机制保障，本规则为语义约定。

## 🔴 快速判断表（先查这里）

| 变更内容 | 触发 CI？ | 机制 |
|---------|----------|------|
| `install.sh`、`tests/**`、`eval/**`、`.github/workflows/**`（代码/测试/编排） | ✅ 触发 | ci.yml / eval.yml paths |
| `cadence-init/**`（Skills 源：SKILL.md、references、scripts、规则模板） | ✅ 触发 | ci.yml paths（eval.yml 另按其清单） |
| `.claude/rules/**`（框架规则） | ✅ 触发 | ci.yml paths |
| 文档：`README.md`、`readmes/**`、`cadence/**`（designs/plans/reports/analysis-docs 等）、`openspec/**`、`CLAUDE.md`、`AGENTS.md`、`LICENSE` | ❌ 不触发 | 不在 paths 集合内 |
| `.codex/**`、`.pi/**`、`.claude/skills/**` 等 OpenSpec/客户端投影目录 | ❌ 不触发 | CI 不消费投影；源头变更经 `cadence-init/**` 覆盖 |

**记忆口诀：动「安装脚本、Skills 源、规则、测试与编排代码」必触发；动「说明文字」不触发。**

## 机制（以工作流声明为准，本表是语义摘要）

- `ci.yml`（ShellCheck / 隔离集成测试 / 13×3 链接矩阵 / rule-config pytest）：push 与 pull_request 均带 paths 过滤，触发集合 = `install.sh`、`tests/**`、`cadence-init/**`、`.claude/rules/**`、`.github/workflows/ci.yml`。
- `eval.yml`（Tier-0 单测 / Tier-1 五端 Docker 夜测）：既有 paths 过滤（`eval/**`、四个初始化 Skill 目录、工作流自身），本规则不改变它。

## 提交约定

1. **文档变更独立成提交**：混合提交（文档 + 触发集内文件）会整体触发 CI，属预期行为；想省资源就先拆提交。
2. **触发集内文件变更但确需跳过 CI**（如本次「文档 + 工作流过滤规则」一并落地）：commit message 末尾加 `[skip ci]`——GitHub 原生跳过该 push/PR 的**所有**工作流。
3. **`[skip ci]` 慎用**：它会连代码验证一起跳过，只允许在「跳过有书面理由」时使用（如纯文档、或变更已由本地等价验证覆盖）；跳过事实写入提交说明。

## 触发集合维护

- 新增「CI 实际消费的输入目录」（如未来 ci.yml 开始测 `eval/**`）→ 同步改 `ci.yml` paths 并回填本表。
- 本规则与 `real-machine-gating.md` 正交：触发 CI 的变更仍按真机门禁判断是否需要真机实测。
