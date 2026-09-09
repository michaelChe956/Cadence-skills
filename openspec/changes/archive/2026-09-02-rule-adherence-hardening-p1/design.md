# Design: rule-adherence-hardening-p1

> 完整设计依据与证据链见 `cadence/designs/2026-09-02_方案设计_规则遵循强化第一期_v1.0.md`（维护者已批准）；本文仅固化架构边界与关键决策。

## Context

- 四端探针实验证实：L0 内容四端均进上下文，但 Claude Code 剥离 HTML 注释（版本标记不可见）、Codex 不读 `.claude/rules/`（②③类规则内容为 0）、全部约束无运行时强制。
- 规则模板体系与受管区块机制（L0 v1→v3 权威覆盖、dry-run/apply 两阶段、备份到 cadence/legacy/）已是成熟基础设施，本设计在其上扩展而非另建。
- 维护者已拍板：CI 双车道（PR 不跑真实 CLI）、harness 分级保护、deny+链文本常驻规则正文（非 ask）、Codex 自动内联（A+）、pi 子代理 MCP 本期不做。

## Goals / Non-Goals

**Goals:**
- 规则元数据成为唯一事实源，按 harness 分级投影（Claude Code=deny 权限、Codex/Kimi=AGENTS.md 内联、诊断层=--verify）
- 修复两个加载缺陷（版本标记不可见、Codex 规则内容缺失）与一个可达性盲区（子代理 MCP）
- 全增量应用：业务项目 update → dry-run/apply → verify，无 breaking change

**Non-Goals:**
- PreToolUse 时序门禁（攻①，切片 2，要点已记录于设计文档 §12）
- pi 项目扩展 tool_call 拦截器、Cursor hooks 复用（切片 2）
- eval 体系与 CI 夜间车道（目标 B，独立 change 并行立项）
- pi 子代理 MCP frontmatter 配方（明确不做，降级为规避策略）

## Decisions

| # | 决策 | 理由与备选 |
|---|---|---|
| D1 | 元数据格式：规则模板受管注释区三字段（preferred/fallback/when） | 备选 frontmatter 被否——模板正文为正文型 Markdown，受管注释与既有 cadence-managed 机制同构；本期只消费 fallback/when，扩展点留白 |
| D2 | 权限层用 deny+链文本常驻规则正文，不用 ask | 维护者期望"规则说了算、零人工"；ask 版把强制成本转为人肉点击；Claude Code 原生 deny 只回通用文案（issue #87153），优先级链文本（preferred→次选→兜底出口）随规则正文（.claude/rules/ 与 AGENTS.md 内联区块）常驻上下文，模型被拦后查链自动改道；备选 ask 仅作观察期回退预案 |
| D3 | 拒绝理由与拦截集合同源渲染 | 规则改 → apply → 拦截与理由同步变；避免出现"拦 A 提示 B"的漂移 |
| D4 | settings.json 只做区块级受管（`cadence-managed:permission-gate` 标记） | settings.json 含用户自定义内容，整文件覆盖违背既有"框架权威全覆盖"仅适用于纯框架文件的边界；与 L0 区块机制同构 |
| D5 | Codex 内联走生成器模式（A+），源=rules 目录 | 官方无 AGENTS.md 外加载机制（源码级确认）；社区主流即"片段源→生成+drift 校验"；备选 Skills 按需加载被否（遵循率低于常驻注入） |
| D6 | 内联预算 60 行硬上限 | Codex `project_doc_max_bytes` 默认 32KiB 且沿链共享；60 行压缩版+pi/Kimi 重复 1.5KB 已获维护者接受 |
| D7 | --verify 区分"未生成"与"漂移" | 防止未用过投影的新项目被误报漂移 |
| D8 | L0 v4 用"注释标记+可见文本行"双轨 | 注释供脚本、文本供模型；不动既有标记协议，升级链复用 |

## Risks / Trade-offs

| 风险 | 对策 |
|---|---|
| deny 边角场景模型反复撞墙 | 链式理由写全出口；`CADENCE_BYPASS=1` 写进理由末尾；观察期迭代文案（理由是生成物，改元数据即改文案） |
| settings.json 合并破坏用户内容 | 区块级受管+并集+显式 allow 不降级+无法安全合并保守跳过并报告；TDD 专项用例 |
| 内联区块膨胀 | 60 行硬上限+优先级截断+省略标注+verify 行数告警 |
| 三端子代理继承类版本 bug 导致探针误报 | 探针失败仅告警不阻断，输出各端排查指引 |
| no-interrupt 静默决策 | 全部新写入沿用既有规范：解析失败先备份、集合合并、冲突保守跳过+报告 |

## Failure Handling / Migration

- apply 前置 dry-run 预览全部写入；写入前备份到 `cadence/legacy/<时间戳>/`；失败保持原样（原子写语义沿用）。
- 旧项目迁移：v3 L0 → v4 走既有确定性升级；权限与内联区块首次生成，`--verify` 报"未生成"提示 apply，不误报。
- 撤销路径：`--remove-permission-gate` 整体移除权限区块；内联区块随下次 apply 重算或手动删除标记区块。
