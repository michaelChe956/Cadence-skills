# Design: MCP 图片识别路由规则引入与 CodeGraph 规则按项目类型分发修复

## Context

完整技术论证见已批准的主设计文档：`cadence/designs/2026-08-27_技术方案_MCP图片识别路由与CodeGraph按类型分发修复_v1.0.md`（行为矩阵、实现铁律、缓存 schema、风险表以其为准）。本文件仅记录 change 内的技术决策边界。

现状约束：仓库内已有 `code-usage-coding.md`/`code-usage-noncoding.md` → `code-usage.md` 的双来源单选成熟先例（脚本常量、S3 选择、drift、归档迁移、测试全套）；`--enable-codegraph` 契约由 `it-s8-codegraph-explicit-enable` 锁定；no-interrupt 的类型裁决集中于 `_compute_final_project_type()`。

## Goals / Non-Goals

**Goals:**

- non-coding 项目从物理上不再收到含 CodeGraph 要求的规则正文（模板级隔离，不依赖 Agent 自觉）
- 图片识别获得统一路由：原生优先、探测前置、task-scope 状态复用、双 provider 无固定优先级
- 消灭受管规则文件的双写者（mcp-configuration 旧追加流程）
- 文案、入口摘要、S8 判断三者共用同一最终 project_type 信号

**Non-Goals:**

- 不废除 `--enable-codegraph` 显式例外（用户显式覆盖能力保留）
- 不改 no-interrupt 类型裁决逻辑（一行不动）
- 不自动清理历史 `.codegraph/` 目录（可能是合法显式产物；本 worktree 现场 `.codegraph/` 由人工一次性删除）
- 不调整受管落地文件总数（维持 7 个）

## Decisions

| # | 决策 | 备选与否决理由 |
|---|---|---|
| D-1 | **X+Y 组合**：code-reading 双来源单选（Y）+ mcp-servers.md CodeGraph 小节条件化（X） | 仅 X：文档项目仍收代码说明书，依赖 agent 自我豁免。仅 Y：non-coding+显式启用场景无指引出口 |
| D-2 | 双来源信号 = 最终 `plan["project_type"]` | detected_type：普通模式 CLI 提升场景会复刻文案/工具割裂（今日缺陷的结构镜像） |
| D-3 | 可用性状态放 `cadence/cache/mcp-availability/<task-scope-id>.json`，每 scope 一文件 | `cadence/reports/`：document-storage 定义为进度报告，语义错位；`.cadence/`：新增第二命名空间治理成本；单一固定 json：并发覆盖+跨任务误信旧状态 |
| D-4 | 落地名恒定 `code-reading.md`，来源不落地 | 与 code-usage 契约一致，L0 引用不分叉零悬空 |
| D-5 | 入口第 7 条摘要照 RULE2_TEXT_* 先例做渲染期双文案 | 仅改正文：非 coding 项目入口仍暗示代码工具链 |
| D-6 | 原单文件模板移除（非保留） | 保留会形成第三事实源；完备性检查加入两份新来源保证失败关闭 |

## Risks / Trade-offs

- [混合仓库类型表达不完美] → no-code 版保留 ast-grep 单辅助文件窄例外 + 指引"实质转编码重跑 rule-config"
- [旁路信号复发] → 铁律写入 spec MUST + 测试断言 template_source 断言来源一致性
- [缓存泄密] → schema 白名单字段 + 静态测试断言安全关键词
- [旧期望大面积失效] → 仅精确更新与新契约对应的期望值；no-interrupt/权威覆盖/备份屏障红线不放宽
- [S3/S4 时序悬空] → locate_templates 完备清单纳入两份新来源，失败关闭

## Migration Plan

新装项目无感；既有项目重跑 rule-config 时按当前类型权威覆盖 code-reading.md（既有归档屏障兜底）；根副本随本 change 同步更新一次。回滚即 revert 本 change 分支。

## Open Questions

无——三项关键决策（方向/D1/D2）已获用户确认。
