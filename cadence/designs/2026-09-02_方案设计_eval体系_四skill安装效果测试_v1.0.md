# 方案设计：eval 体系——四 skill 安装效果测试（rule-eval-p0）

- **日期**：2026-09-02
- **状态**：设计第三版获维护者认可 + 业内调研增补定稿，待审阅本文后转 OpenSpec
- **估算**：6–8 人日
- **证据**：`cadence/analysis-docs/2026-09-02_eval体系设计调研证据/skills执行级测试业内调研.md`（claudemd-check/Backgrind/cae/Harbor/skillgrade/agenteval 等 17 项来源）

## 1. 背景与诉求

维护者的四个问题，即本 eval 的四个度量目标：

1. **规则有没有正确执行**（安装后 agent 真的遵守分发规则吗）
2. **MCP 有没有正确使用**（该调 MCP 的场景实际调了吗）
3. **弱模型使用效果是否可保证**
4. **不同 coding agent 之间差异是不是不大**

约束与范围：

- 使用方式 = **直接 command 调用**（aria 或人工），不测触发识别；
- 测试对象只有 4 个 skill：`/pre-check`、`/rule-config`、`/mcp-configuration`、`/project-rules-examples`；其余 skill 后续逐个优化时再入集（架构上即加条目）；
- `project-analysis` 为 legacy 待废弃，不入集且负例设计不指向它；
- p1（rule-adherence-hardening-p1）正在实施中，本体系首轮基线在 p1 合入后建立，亦可先跑 pre-p1 基线做对照。

## 2. 已锁定决策

| # | 决策 |
|---|---|
| E1 | 不做触发识别测试；只测安装效果（两阶段流水线） |
| E2 | 夜间车道 self-hosted runner（本机注册，复用已登录四端与订阅，密钥不出本机） |
| E3 | 分层判分：确定性断言为主；LLM-judge（Agent-as-a-Judge）仅 Tier-2 手动/周度可选 |
| E4 | PR 车道零真实 CLI 调用（继承 p1 的 D1）：静态检查 + 断言器自测 + mock 冒烟 |
| E5 | 弱模型必入矩阵（日常场景即弱模型） |
| E6 | 业内增补 10 条全量并入（见 §6） |

## 3. 架构：两阶段流水线

```
fixture 项目（三变体：全新空项目 / 已初始化v3 / 已配 .mcp.json+codegraph）
   │
   ├─ 阶段一：安装效果 —— headless 依序直接调用四 command
   │    /pre-check → /rule-config → /mcp-configuration → /project-rules-examples
   │    断言：每步产物核对表 + p1 --verify exit 0 + 幂等双跑 byte-identical
   │
   └─ 阶段二：安装后行为效果 —— 在装好的 fixture 发 8 个行为探针
        判分：stream-json 轨迹 → 四端适配器 → 统一中间格式 → 断言器
        度量：遵循率矩阵 / MCP 使用率 / 弱模型保证度 / 跨端一致性
```

## 4. 阶段一：安装断言表（节选，全表在实施 Plan 展开）

| 步 | 断言（全部确定性） |
|---|---|
| pre-check | 诊断报告产出；项目文件零改动（git diff 空） |
| rule-config（全新） | `.claude/rules/` 7 文件 ✓、L0 v4 区块 ✓、settings.json permission-gate 区块 ✓（p1 后）、AGENTS.md codex-rules-inline 区块 ✓（p1 后）、`--verify` exit 0 |
| rule-config（v3 升级） | v3→v4 确定性升级、备份进 cadence/legacy/、区块外逐字不变 |
| mcp-configuration | `.mcp.json` 合法且含预期 server、`.codex/config.toml` 同步一致、`.gitignore` 精确行 |
| project-rules-examples | `cadence/project-rules/` 就位、**未**写 `.claude/rules/` |
| 幂等（E6-2） | 同一 fixture 连跑两遍安装，workspace diff byte-identical（jarvy 先例） |

## 5. 阶段二：行为探针任务集（初始 8 个）

| 探针 | 任务 | 断言（轨迹+产物+时间序） | 回答哪问 |
|---|---|---|---|
| P1 检索 | "梳理订单模块从入口到落库的调用链" | 轨迹含 codegraph/ast-grep；无大范围裸 grep | ①规则② |
| P2 文档 | "查 React Server Components 官方最新用法" | Context7 调用；无 WebSearch（已配置时） | ②MCP |
| P3 时序 | "给用户表加个最后登录时间字段" | 首个 Edit 前 openspec/changes 或 cadence/plans 已有产物 | ①规则①（p1 前预期红，切片 2 后转绿） |
| P4 语言 | 任意任务 | 输出中文 | 通用 |
| P5 产物 | "写个部署方案文档" | cadence/ 正确子目录 + 命名规范 | 通用 |
| P6 时间 | "现在几点，换算纽约时间" | time MCP 调用 | ②MCP |
| P7 图片 | "分析这张报错截图" | 智普/MiniMax 图片 MCP 路径 | ②MCP |
| P8 幂等 | 重跑 /rule-config | 产物不变、备份生成 | 安装效果 |

注：P2/P6/P7 的 fixture 配置指向 **fake MCP server**（E6-9，工具名与真实一致、种子状态+调用记录），断言其调用记录而非真实网络；真实 MCP 端到端验证属 Tier-2 手动车道。

## 6. 业内增补（10 条，全部并入）

| # | 增补 | 归属环节 | 来源 |
|---|---|---|---|
| 1 | 判分必须 gate `permission_denials` 与 `is_error`——dontAsk 被拒的 run 会 exit 0 假绿（实测空跑 $0.383 比修 bug 还贵） | 断言器 | Backgrind |
| 2 | 阶段一幂等双跑快照（同 fixture 两遍、byte-identical） | 阶段一 | jarvy |
| 3 | transcript 全量留存 + 断点续跑（results JSON 已存在即跳过） | 运行器 | cae + 官方 SessionStore |
| 4 | mock/免费冒烟车道前置——先证明 harness 自身无误再进付费矩阵 | 车道 | cae/skillgrade |
| 5 | 多层成本熔断：`--max-turns` + timeout + 累计成本上限 | 运行器 | Backgrind/cae |
| 6 | transcript 断言排除规则原文与工具结果文本（防"朗读了规则"假阳） | 断言器 | claudemd-check |
| 7 | probe prompt 经 env 注入不内联 shell（防注入/转义污染） | 运行器 | Backgrind |
| 8 | 遵循率对已提交基线具名 diff（`▼ P1检索@Codex: 100%→60%` 红灯） | 报告 | claudemd-check |
| 9 | "必须用指定 MCP"探针用 fake MCP server（种子状态+调用记录断言，免真实网络波动） | 阶段二 | agenteval |
| 10 | 模型与 CLI 版本双 pin（`--model` 显式 + 版本锁文件，防默认模型漂移） | 运行器 | Backgrind/cae |

## 7. 度量输出（四张矩阵 = 四个问题的答案）

1. **规则遵循率矩阵**：探针 × agent × model 通过率（多 run 均值）
2. **MCP 使用率**：P2/P6/P7 各端通过率
3. **弱模型保证度**：强弱模型通过率差值
4. **跨端一致性**：四端通过率极差与方差

版本对比：pre-p1 基线 → p1 后 → （切片 2 后 P3 转绿）——**提升百分比从这张对比表来**。

报告形态：`cadence/reports/eval/<日期>/`（json + md 矩阵 + 具名 diff + 失败 transcript 路径回放）。

## 8. 车道矩阵

| 车道 | 内容 | 跑在哪 | 触发 | 成本 |
|---|---|---|---|---|
| Tier-0 | 静态检查 + 断言器自测 + mock 冒烟 | 云端 | PR（路径过滤） | $0 |
| Tier-1 | 阶段一安装流水线（4 端 × 2 模型 = 16 次，全新 fixture 主变体；v3 升级变体仅 2 端验证）+ 阶段二 8 探针 × 4 端 × 2 模型 × 3 runs（=192 行为会话） | self-hosted | 夜间 cron | 吃订阅配额，边际≈$0；多层熔断兜底 |
| Tier-2 | 四端 × 弱模型 + judge 过程评审 | self-hosted | 手动/周度 | judge ~$5–15/次 |

## 9. 风险与对策

| 风险 | 对策 |
|---|---|
| self-hosted 离线/配额耗尽 | skip 语义 + 次日补跑 + 配额告警；断点续跑（E6-3） |
| 四端 stream-json 格式差异 | 适配器各自封装统一中间格式；Kimi 无先例文档，先行单端验证 |
| harness 自身 bug 污染结果 | mock 冒烟车道前置（E6-4） |
| flaky | 多 run 均值 + 容差阈值；具名 diff 只对超阈值的降级红灯 |
| fixture 泄漏/过拟合 | 三变体轮换 + 定期换题库 |
| 假绿 | E6-1 强制 gate + 幂等双跑 + 排除规则原文断言 |

## 10. 非目标

- 触发识别测试（明确不做）；
- 其余 10 个 skill 入集（后续逐个优化时）；
- judge 进 PR/夜间车道（仅 Tier-2）；
- 外部 eval 平台引入（promptfoo/LangSmith 等）；
- p1 实施本身。

## 11. 估算

fixture 三变体 1d + 安装断言与幂等双跑 0.5d + 探针集与断言器（含 gate/排除原文/env 注入）2d + 四端轨迹适配器 1.5d + fake MCP 0.5d + mock 冒烟 0.5d + CI 编排（断点续跑/熔断/具名 diff 报告）1d ≈ **6–8 人日**。
