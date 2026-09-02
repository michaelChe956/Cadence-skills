# Proposal: rule-eval-p0

## Why

维护者对 Cadence 分发链路的四个核心问题目前没有任何可测量的答案：**①安装后规则有没有被正确执行；②MCP 有没有在应调用的场景被实际调用；③弱模型效果是否可保证；④不同 coding agent 之间差异是否足够小**。p1（rule-adherence-hardening-p1）即将交付强制面与 `--verify`，但"违规率到底多少、p1 之后降了多少"没有测量体系——本 change 补上这把尺子。

业内调研（`cadence/analysis-docs/2026-09-02_eval体系设计调研证据/skills执行级测试业内调研.md`）确认：**无任何公开项目做"slash command 执行后产物断言"或"多端规则遵循矩阵"**，本体系为增量；同时吸收了 10 条已验证的业内防线（假绿 gate、幂等双跑、fake MCP、成本熔断等）。

## What Changes

新建独立的 eval 子系统（不动 install.sh / rule-config.py / 各 skill 正文）：

- **两阶段流水线**：阶段一在 fixture 项目上 headless 依序直接调用 `/pre-check → /rule-config → /mcp-configuration → /project-rules-examples` 并做产物断言 + `--verify` + 幂等双跑；阶段二在装好的 fixture 里发 8 个行为探针任务，从轨迹断言规则遵循；
- **四端轨迹适配器**：claude -p / codex exec / pi -p / kimi -p 的 stream-json 各自封装为统一中间格式；
- **确定性断言器**：事件匹配 + 产物检查 + 时间序检查，强制 gate `permission_denials`/`is_error`（防假绿），断言排除规则原文（防假阳），MCP 探针用 fake MCP server；
- **三级车道与报告**：Tier-0 PR（零真实 CLI，mock 冒烟）、Tier-1 夜间 self-hosted 矩阵（8 探针 × 4 端 × 强弱模型 × 多 run）、Tier-2 手动（+可选 judge）；四张度量矩阵（遵循率 / MCP 使用率 / 弱模型保证度 / 跨端一致性）+ 对已提交基线的具名 diff 红灯；
- **假绿防线双分类**：受管 deny 转改道率子度量（p1 成功路径不误判）、区块外 deny 判 FAIL、基础设施失败单独归因不入矩阵；启用前 fixture 取证真实 denial 字段结构；
- **"未安装 Cadence"对照组**（第四 fixture 变体，量化规则边际效应）与**既有 session 审计表**（第五张观测表，不进 gate、不入 git）；
- **运行器工程面**：断点续跑、多层成本熔断、每端 pin 当前配置模型（维护者裁定：四端模型各异，跨端一致性=实际配置口径）、CLI 版本锁、结果 JSON schema 版本化、transcript 分级保留、端级/runner 级降级、Tier-1 分夜轮转与滚动 7 夜聚合矩阵。

范围限定：只测 4 个 skill（`pre-check`/`rule-config`/`mcp-configuration`/`project-rules-examples`）；不做触发识别测试（维护者直接 command 调用）；`project-analysis` 为 legacy 待废弃，不入集。

完整设计：`cadence/designs/2026-09-02_方案设计_eval体系_四skill安装效果测试_v1.0.md`（维护者已批准）。

## Capabilities

### New Capabilities

- `eval-pipeline`: 两阶段测试流水线——fixture 变体、四 command 安装断言、幂等双跑与 8 个行为探针
- `eval-trajectory-scoring`: 四端轨迹适配、统一中间格式与确定性断言器（假绿防线、fake MCP、排除规则原文）
- `eval-ci-matrix`: 三级车道编排、夜间矩阵、基线具名 diff 报告与运行器工程面（熔断/续跑/版本 pin）

### Modified Capabilities

（无——纯新增子系统，消费 p1 的 `--verify` 退出码作为断言原语，不修改其契约）

## Impact

- **新增文件**（全部位于 `cadence-init/skills/` 外的新目录或 eval 专属目录，实施 Plan 定精确路径）：fixture 生成器、四端适配器、断言器、探针定义集、运行器与 workflow（夜间 self-hosted）、基线文件
- **不改动**：install.sh、软链层、rule-config.py、各 SKILL.md 正文、现有 CI 车道（Tier-0 为新增 job 而非改写）
- **运行前提**：self-hosted runner 需本机注册（维护者操作，一次性）；四端 CLI 已登录
- **成本**：Tier-1 吃现有订阅配额（边际≈$0，多层熔断兜底）；Tier-2 judge ~$5–15/次（可选）
- **非目标**：其余 10 个 skill 入集、触发识别测试、judge 进夜间车道、外部 eval 平台引入、p1 实施本身
