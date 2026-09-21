# Proposal

## Why

三批 KB 变更（矩阵契约/业务知识输入面/组合与索引层）已实施，验证现状是静态结构断言（26 项）+ 两轮人工评审，**行为正确性零测试**——skill 文本改动后无法回归全链（bootstrap→…→update）是否可执行、产物是否满足契约、机制（组合/寄生迁移/横向重算/漂移分级）是否真实生效。本变更建立常规自动化测试体系（kb-eval）：fixture 项目 + 三层确定性断言器 + 阶段化流水线，架构对齐 rule-eval-p0 但资产独立先行。

## What Changes

- **fixture 标准版全埋点**（`evals/kb/fixtures/standard/`，git 资产）：3 个 Spring Boot 服务 + Vue3 前端 + 4 表 DDL，埋点 F1–F10 每条映射具名断言（a+b 组合全链、JOIN_KEY 同名陷阱、订单状态机、EVENT/JOB、明文密码脱敏、寄生规则迁移、ref 型证据、product.md 两变体、破坏性变更+变更包、漂移分级）；两变体（variant-full / variant-min）。
- **断言器三层**（`evals/kb/assertions/`）：`tier0.py` 结构不变量（26 项正式化+扩充）；`named.py` 具名实体期望（F1–F10 对照表）；`negative.py` 反例断言（无明文敏感值、api/pages 产物无横向边、无断链 verified、ai-draft 不被当 confirmed 引用）。**断言器自测**：对故意损坏样本目录必须全部红（防断言器失效假绿）。
- **runner 流水线**（`evals/kb/runner/run.py`）：fixture→/tmp 干净副本（git 基线标签）→ 写 user-input（含变体注入）→ 阶段 A 六阶段逐阶段执行+断言（失败即停留 transcript；`results.json` 断点续跑与 `coverage.initialization` 状态机双保险）→ 阶段 B 四探针（组合查询/规则检索/变更更新/漂移分级）→ 报告到 `cadence/reports/eval/<日期>/kb/`（通过矩阵+具名 diff+失败 transcript 回放）。熔断：`--max-turns`/timeout/累计成本上限；单阶段可重跑（`--stage api`）。
- **车道矩阵**：Tier-0（$0：结构校验+断言器自测+fixture 完整性，PR 车道路径过滤 `cadence-init/skills/knowledge-base-*`）；Tier-1（手动触发全链，估 $2–5/轮）；Tier-2（LLM-judge 产物质量，可选）。
- **调优接口**：失败分类四类（skill 文本缺陷→OpenSpec 小变更修复后重跑受影响阶段；断言缺陷→修期望需设计评审；fixture 缺陷→修埋点；agent 遵循→记录强化）。红线：断言只许因"期望错了"而改，不许因"agent 做不到"而放松。
- **非确定性对策**：断言只断不变量+具名锚点+反例；幂等双跑改为结构不变量双跑；判分不依赖 agent 自述（只读产物文件与 transcript 工具调用记录）。

无 **BREAKING** 变更：纯新增 `evals/kb/` 目录与报告产物，不触碰任何 skill 行为、不触碰 cadence-init/（除将来 Tier-0 接 PR 车道的工作流配置，属后续项）。

## Capabilities

### New Capabilities

- `kb-eval-pipeline`: KnowledgeBase skill 体系的自动化回归测试——fixture 资产与埋点契约、三层断言器与自测、阶段化流水线与断点续跑、车道分层与触发、调优回路与断言红线。

### Modified Capabilities

（无）

## Impact

- 新增 `evals/kb/`（fixtures/assertions/runner/probes 四目录，约 fixture 60–80 文件 + Python 断言器/runner 4–6 文件）。
- 报告产物路径 `cadence/reports/eval/<日期>/kb/`（运行时生成）。
- 不修改 `cadence-init/skills/`（首期零改动；首轮跑出的 skill 缺陷另行走小变更）。
- 依赖：执行端为 headless agent 会话（首期单端）；Python 3 + PyYAML。
- 设计文档：`cadence/designs/2026-09-20_方案设计_KnowledgeBase自动化测试体系_v1.0.md`（已确认）。
