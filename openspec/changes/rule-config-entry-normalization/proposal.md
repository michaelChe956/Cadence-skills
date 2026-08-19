# Proposal: rule-config-entry-normalization

## Why

使用当前 skills 初始化项目后，入口文件与 Superpowers 工作流存在三个已证实的问题：(1) 已存在非 Cadence 风格入口文件时，`_ensure_summary_lines` 无 `## 强制规则` 章节直接返回，AGENTS.md 缺失强制规则 1-7，CLAUDE.md 残留已退役规则（Serena）且编号错乱，双入口技术栈检测不一致；(2) Superpowers Skill 正文硬编码的默认产物路径（`docs/superpowers/specs/` 等）压过项目文档存放规则；(3) Superpowers 写完 design/plan 后自动 `git commit`，无项目级开关。

## What Changes

- **入口文件规范化合并**：`_ensure_summary_lines` 重写为规范化算法——以 `CANONICAL_RULES` 单一事实源权威渲染 `## 强制规则` 章节（无章节则创建）、按显式退役清单 `RETIRED_RULE_FILES` 删除失效引用、重排编号、用户内容保留并报告；移除全文级规则 2 文案替换；修正 `_insert_l0_block` 无章节分支的插入位置（H1+简介之后，而非文件末尾）。
- **L0 内核升级 v1 → v2**：新增产物路径映射覆盖表（`docs/superpowers/specs/` → `cadence/designs/`、`docs/superpowers/plans/` → `cadence/plans/`，优先级高于 Skill 正文）与"产物自动提交"开关条款；脚本完成 v1→v2 确定性 upgrade 接线（当前未支持，v1 对 v2 源误判 drift）；补齐迁移不变量（升级后区块唯一、混合标记处理、重复区块归并）。
- **产物自动提交开关**：入口文件 `## 项目配置` 新增 `- **产物自动提交（design/plan）**：关闭`，默认关闭、保留用户手改值、非法值按关闭处理并报告。
- **warnings 报告契约**：报告 JSON 新增顶层 `warnings` 数组（6 个错误码），不影响 `overall`，dry-run/apply/no-interrupt 三态一致。
- **同步更新**：`merge-semantics.md` SM 表重写（SM-01~05，合计 62→64）、L0 表当前版本表述、`document-storage.md` 映射表、`SKILL.md` 与 `skill-clause-map.md` 对账、`verify-managed-lifecycle.sh` marker。

## Capabilities

### New Capabilities

- `entry-file-normalization`：入口文件 `## 强制规则` 章节的权威清单、规范化算法（创建/分类/重建/保留）、退役引用清理、用户内容保留与 warnings 行为。
- `superpowers-artifact-governance`：Superpowers 产物路径映射覆盖（含跨源一致性）与产物自动提交开关的写入、读取与取值语义。

### Modified Capabilities

- `managed-rule-lifecycle`：L0 版本化升级要求扩展——v1→v2 确定性 upgrade、升级后区块唯一性、混合标记与重复区块处理；入口语义等价要求扩展——双入口技术栈一致性与规范化章节等价。
- `rule-config-scripted-execution`：合并确定性实现扩展——规范化整理动作两模式同动作；JSON 报告扩展——`warnings` 顶层字段契约。

## Impact

- 代码：`cadence-init/skills/rule-config/scripts/rule-config.py`（规范化、L0 接线、开关、warnings、BASE 渲染）。
- 规范源与规则：`references/rules/agent-routing-kernel.md`（v2）、`references/rules/document-storage.md`、`references/merge-semantics.md`。
- 测试与对账：`tests/test_rule_config.py`（新增约 30 用例 + L0 marker 版本参数化）、`tests/skill-clause-map.md`、`tests/verify-managed-lifecycle.sh`、`SKILL.md`。
- 行为兼容性：已安装 v1 的项目重跑 rule-config 时 L0 确定性升级为 v2（不再落入用户决策）；含 Serena 残留的入口文件被清理；规范化只整理 `## 强制规则` 章节，章节外用户内容逐字保留。
- 非目标：不改全局 Superpowers Skill 本体；不动 `openspec/` 产物结构；不做 design/plan 分开开关。

## 设计文档

已通过两轮独立评审（deepseek-v4-pro、gpt-5.6-terra，均为"修改后批准"且修正已闭合）：`cadence/designs/2026-08-13_技术方案_rule-config入口规范化与产物覆盖及提交开关_v1.0.md`（v1.2）。
