# 组合能力索引

## 元数据

| 项目 | 内容 |
|------|------|
| 证据基线 | 1f867b9fcdf95f2e11808454898f333d7d512e90（分支 master） |
| 分析时间 | 2026-09-20（overview 阶段生成） |
| 输入来源 | `user-input/api-scope.md:19-21` 能力组合诉求表；`interfaces/README.md` 能力组合诉求核实结论 |
| 计数摘要 | proposed 1、verified 0、retired 0 |
| 通道结论 | 用户诉求通道生成 1 个 CAP；已有实现通道未发现聚合端点（无 `implementation_api_ids`） |

> 本索引只保存稳定 ID、状态与导航；输入契约、编排、JOIN_KEY 证据与实现关联见各 CAP 文档。

## CAP 清单

| CAP 稳定 ID | 名称 | 状态 | 输入 API | 明细 |
|-------------|------|------|----------|------|
| CAP-user-full-info | 全部用户信息 | proposed | `API-user-basic`、`API-account-query` | [`CAP-user-full-info`](CAP-user-full-info.md) |

## 通道说明与限制

- 用户诉求通道：诉求行来源能力已由 api 阶段核实存在且契约锚点齐备，故生成 CAP 实体；`JOIN_KEY`（`userId`）端到端映射未闭合，CAP 与 `JOIN_KEY` 边均按`待确认`处理（Q-M3、Q-M5、Q-M9）。
- 已有实现通道：全量接口扫描未发现由多个能力聚合而成的端点，`implementation_api_ids` 为空，组合状态只能为 `proposed`。
- 会话推导的组合候选不生成实体；`全部用户信息` 不得默认视为涵盖敏感字段（见 `CAP-user-full-info.md` 第 2、5 节，Q-M13）。
- 对外暴露属性唯一权威是用户 `api-scope` 清单；`proposed` 或未来的 `verified` 都不等于对外已暴露。

