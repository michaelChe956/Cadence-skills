# Design: rule-config-entry-normalization

## Context

完整技术方案（含根因、算法步骤、边界语义、测试清单）已经两轮独立评审闭合，见 `cadence/designs/2026-08-13_技术方案_rule-config入口规范化与产物覆盖及提交开关_v1.0.md`（v1.2，下称"技术方案"）。本文件只记录关键决策与权衡；Why 见 proposal.md。

现状约束：`rule-config.py` 单一脚本 3700 行，dry-run/apply 两阶段；L0 版本常量硬编码 v1，旧版检测仅枚举 v0；`_ensure_summary_lines` 为追加式补全；报告骨架无 `warnings` 字段；既有 160 个 unittest + `verify-managed-lifecycle.sh` 集成脚本 + `merge-semantics.md`/`skill-clause-map.md` 条款对账（合计 62 行）。

## Goals / Non-Goals

**Goals:**
- 入口文件 `## 强制规则` 章节权威化：单一事实源渲染、缺失创建、退役清理、重排编号、用户内容保留。
- L0 v1→v2 确定性升级与迁移不变量（唯一区块、混合标记、重复归并）。
- 产物路径覆盖表三源一致（内核/document-storage/脚本常量）与自动提交开关。
- 统一 `warnings` 报告契约。

**Non-Goals:**
- 不改全局 Superpowers Skill 本体；不动 `openspec/` 产物结构；不做 design/plan 分开开关；不做"文件不存在即删"的泛化判定；不搬移章节外用户内容。

## Decisions

1. **规范化合并而非权威覆盖**（用户确认）：保留入口用户内容，仅规范化 `## 强制规则` 章节。备选"整体以 BASE 重建"会摧毁项目自有 KB 内容，否决。
2. **规则层覆盖而非改写 Skill**（用户确认）：路径映射与提交开关写入 L0 内核（v2）+ document-storage.md，利用"用户指令优先于 Skill"声明。备选"安装时改写本地 Skill 副本"在 Skill 升级后失效，否决。
3. **顺序矛盾的解法是修正 L0 插入位置**：`_insert_l0_block` 无章节分支从"追加文件末尾"改为"H1+首个简介段落之后"（兑现 docstring 原承诺），新章节紧随 L0。备选"搬移用户内容到章节后"违反章节外逐字保留，否决。
4. **规则 6 身份用内容 marker**：以 `cadence/project-rules/` 引用识别（两类旧文案块均含此行），不依赖易变的标题文本。
5. **失效清理用显式退役清单** `RETIRED_RULE_FILES`：避免误删用户前瞻引用；清单随框架规则退役手工维护。
6. **规则 2 全文替换移除**：规则 2 由章节内权威渲染产出；原全文 `str.replace` 会破坏章节外用户内容。
7. **开关存于入口文件 `## 项目配置`**（用户确认）：默认 `关闭`，仅精确值 `开启` 启用，非法值保留原文按关闭处理；独立于 `tech_stack` 空值提前返回；读取顺序 CLAUDE.md 优先、AGENTS.md 兜底，不一致按关闭。备选放 `openspec/config.yaml` 离 Agent 视线更远，否决。
8. **warnings 独立顶层字段**：不改变 `overall` 语义与 conflicts/decisions 机制；6 个错误码枚举；dry-run/apply/no-interrupt 三态一致。

## Risks / Trade-offs

- [规范化误判用户内容] → 分类仅依赖规则文件名/显式 marker/退役清单三类确定性判定，其余一律按用户内容保留 + warning；17 个专项用例兜底。
- [L0 v2 升级影响既有 v1 项目] → 升级走确定性 upgrade 而非 drift，避免既有项目重跑时落入用户决策；升级前受 L0 备份屏障保护；混合标记/重复区块有明确归并语义。
- [多文件版本/计数对账遗漏] → 影响面全清单（§4.4）点名 merge-semantics L0 表、测试 marker 常量版本参数化、verify-managed-lifecycle.sh、SKILL.md 与 clause-map 计数 62→64；测试断言三源映射表逐字一致。
- [技术栈双入口不一致根因未明] → 实施先行任务：写复现测试定位（疑似 skip 分支或旧版本运行混合），再修复；若根因超出预案（如需改动检测逻辑本身），回到本设计追加决策。

## Migration Plan

- 对使用方：无需手工迁移；重跑 `rule-config`（普通或 no-interrupt）即完成 L0 v1→v2 升级、Serena 清理、开关与映射表落地。既有产物不自动搬移（`docs/superpowers/` 旧产物由用户自行处理）。
- 回滚：全部写入经 `cadence/legacy/` 归档 + `atomic_write`，失败保持原样；回滚即恢复归档副本。
- 本仓库自身：框架规范源修改后，从规范源同步本仓库 `.claude/rules/` 副本与入口 L0（按 managed-rule-lifecycle 现行同步要求）。

## Open Questions

无（两轮评审已闭合全部影响 spec/方案/任务拆分的问题）。
