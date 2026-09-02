# Design: rule-eval-p0

> 完整设计与证据见 `cadence/designs/2026-09-02_方案设计_eval体系_四skill安装效果测试_v1.0.md` 与 `cadence/analysis-docs/2026-09-02_eval体系设计调研证据/skills执行级测试业内调研.md`；本文固化架构边界与关键决策。

## Context

- 维护者以直接 command 调用使用 4 个 skill，不测触发识别；核心诉求是四个度量：规则遵循、MCP 实际使用、弱模型保证度、跨端一致性。
- 业内无"slash command 执行后产物断言"与"多端规则遵循矩阵"先例（本体系为增量）；10 条已验证防线来自 Backgrind/claudemd-check/cae/jarvy/agenteval 等一手来源。
- p1 正在实施中；首轮基线可在 p1 合入后建立（亦可先跑 pre-p1 对照）。

## Goals / Non-Goals

**Goals:** 独立 eval 子系统（两阶段流水线 + 四端适配 + 确定性断言 + 三级车道 + 四矩阵报告），不动 install.sh/rule-config/各 SKILL.md 正文。

**Non-Goals:** 触发识别测试；其余 10 个 skill 入集；judge 进夜间车道（仅 Tier-2 可选）；外部 eval 平台；p1 实施；Kimi 之外的端补文档。

## Decisions

| # | 决策 | 理由与备选 |
|---|---|---|
| R1 | 只测安装效果，不做触发测试 | 维护者直接 command 调用；触发 eval（skill-creator 模式）被明确排除 |
| R2 | 两阶段流水线（安装断言→行为探针） | 装得对≠用得对；阶段二直接回答四个度量问题 |
| R3 | 确定性判分为主，judge 仅 Tier-2 | 零 flaky 可进车道；judge 有成本且 flaky，只做低频补充 |
| R4 | 夜间 self-hosted runner | 复用本机已登录四端与订阅，边际成本≈0，密钥不出本机；备选云端 Secrets 被否（四端 CLI 云端登录态别扭+月费） |
| R5 | 假绿防线为硬性要求（gate permission_denials/is_error） | Backgrind 实测：dontAsk 被拒 exit 0 假绿，空跑比干活还贵；不 gate 则全体系数字失真 |
| R6 | fake MCP 替代真实 MCP 端点做探针 | 免网络波动污染矩阵；agenteval 先例；真实端到端归 Tier-2 |
| R7 | 基线具名 diff 报告形态 | claudemd-check 先例；`▼ 探针@端: A%→B%` 直接可读，红灯只对超阈值降级 |
| R8 | 断点续跑 + 多层熔断 + 模型/CLI 双 pin | cae/Backgrind 工程先例；防中断重跑烧钱与默认模型漂移 |
| R9 | 纯新增文件，不改既有车道 | Tier-0 为新增 job；避免与 p1 的 CI 决策（D1）冲突 |
| R10 | 假绿 gate 双分类（受管 deny→改道率；区块外→FAIL） | 维护者拍板点1；否则 p1 成功路径被判失败、四矩阵反向 |
| R11 | 模型口径=每端 pin 其当前配置模型（四端各不相同） | 维护者 2026-09-02 裁定：测真实使用形态，接受端×模型混合效应；MODEL_DRIFT 实测回读核验仍强制 |
| R12 | Tier-1 首轮砍量级：分夜轮转+2 runs+滚动 7 夜聚合 | 维护者拍板点3；实测 median 2.5min×208 会话=10-20h 串行超窗；单夜信噪比下降以 7 夜聚合补 |
| R13 | 加"未安装 Cadence"对照组+既有 session 审计表 | 维护者拍板点4；对照组是规则有效性唯一证明；审计表复用适配器边际+0.5d，不进 gate 不入 git |
| R14 | 结果 JSON schema_version 最小契约+基线双键（条款×探针 / 探针×端） | oracle §2 b/e；条款 ID 与 p1 元数据同源，红灯可直接定位规则文件 |

## Risks / Trade-offs

| 风险 | 对策 |
|---|---|
| Kimi headless 无先例文档 | R1 适配器先行单端验证再入矩阵（spec 已锁） |
| self-hosted 离线/配额耗尽 | skip 语义不红灯 + 次日补跑（断点续跑兜底） |
| harness 自身 bug 污染矩阵 | mock 冒烟车道前置（Tier-0 内） |
| 多 run 成本 | 矩阵量级固定（192 会话/夜）+ 熔断；吃订阅配额 |
| fixture 过拟合 | 三变体轮换 + 题库可换 + 临时目录隔离 |
| p1 未合入导致阶段一断言（v4/区块）暂红 | 基线策略：首轮基线在 p1 合入后建立；pre-p1 对照跑单独标记不进基线 |

## Failure Handling / Migration

- 任一端适配器失败：该端标记 unavailable，矩阵继续（其余端不受阻）；连续 3 夜失败的端在报告置顶告警。
- 基线更新：仅维护者显式提交基线文件后生效；夜间报告只对比不自动改基线。
- 回滚：eval 为纯新增子系统，删除目录与 workflow 即完全移除，无迁移负担。
