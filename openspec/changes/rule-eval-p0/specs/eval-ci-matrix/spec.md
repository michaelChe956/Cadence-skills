## Purpose

三级车道编排、夜间矩阵与报告：把流水线接入 CI（PR 零真实 CLI、夜间 self-hosted、手动 Tier-2），产出四张度量矩阵与基线具名 diff。

## ADDED Requirements

### Requirement: 三级车道必须隔离真实 CLI 调用

Tier-0（PR 车道，云端）MUST 零真实 agent CLI 调用，仅静态检查、断言器自测与 mock 冒烟；真实 CLI 仅允许在 Tier-1（夜间，self-hosted runner 标签路由）与 Tier-2（手动/周度）执行。PR 车道 MUST 仅对 eval 相关与 skill 文件路径变更触发。

#### Scenario: PR 不跑真实 agent

- **WHEN** PR 触发 CI
- **THEN** Tier-0 job 无任何 claude/codex/pi/kimi 进程调用

### Requirement: 夜间矩阵必须覆盖强弱模型并多 run 判定

Tier-1 MUST 执行矩阵：阶段一安装流水线（4 端 × 2 模型，主 fixture 变体）+ 阶段二探针（8 探针 × 4 端 × 强弱 2 模型 × ≥3 runs）；判定 MUST 取多 run 均值并配容差阈值，MUST NOT 以单次 pass/fail 做门禁；弱模型 MUST 在矩阵内。

#### Scenario: 多 run 均值判定

- **WHEN** 某探针某组合 3 runs 中 1 次失败
- **THEN** 按均值+容差判定该组合通过，单次失败仅入报告不红灯

### Requirement: 报告必须输出四张矩阵与基线具名 diff

每夜运行 MUST 产出：规则遵循率矩阵（探针×端×模型）、MCP 使用率、弱模型保证度（强弱差值）、跨端一致性（极差与方差）；并 MUST 与已提交基线做具名 diff（形如 `▼ P1检索@Codex: 100%→60%`），低于阈值时 CI 红灯；报告 MUST 含失败样本 transcript 路径供回放。

#### Scenario: 具名降级红灯

- **WHEN** 某探针某端通过率较基线跌幅超阈值（默认 5%）
- **THEN** workflow 失败并在报告中标名该组合的前后值

### Requirement: 运行器必须具备断点续跑、成本熔断与版本 pin

运行器 MUST 支持断点续跑（结果 JSON 已存在的组合跳过）；MUST 具备多层成本熔断（单 run 轮次上限 + 超时 + 累计成本上限）；MUST 双 pin 模型（`--model` 显式指定）与各端 CLI 版本（版本锁文件），防默认漂移；每 run 的 transcript 与结果 MUST 全量留存。

#### Scenario: 断点续跑

- **WHEN** 夜间运行中断后重启
- **THEN** 已完成组合跳过，仅补跑缺失部分

#### Scenario: 成本熔断

- **WHEN** 累计成本达到上限或某 run 超时
- **THEN** 该 run 终止计费、标记 skipped，矩阵其余部分继续

### Requirement: self-hosted 不可用必须无阻塞降级

self-hosted runner 离线或订阅配额耗尽时，夜间 workflow MUST 以 skip 语义结束（不阻塞主干、不误报红灯），并留告警记录供次日补跑。

#### Scenario: 机器关机夜间跳过

- **WHEN** 夜间 cron 触发时无 self-hosted runner 在线
- **THEN** workflow 标记 skipped 结束，主干 CI 状态不受影响
