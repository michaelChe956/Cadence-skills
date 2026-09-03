# Eval Pipeline Specification

## Purpose
两阶段测试流水线：对 4 个 skill 的"安装效果"做确定性验证——装得对不对（阶段一产物断言）与装完后规则是否真被遵守（阶段二行为探针），并以"未安装对照组"衡量规则的边际效应。

## Requirements

### Requirement: 安装流水线必须支持三类 fixture 变体并逐项断言产物

系统 MUST 提供 fixture 生成器，支持三变体：全新项目、已初始化（含 v3 L0，测升级链）、已配 `.mcp.json`+codegraph 的项目；每变体上 headless 依序直接调用四 command 并逐项断言（pre-check 诊断报告产出且零文件改动；rule-config 的 `.claude/rules/` 清单、L0 v4 区块、settings.json permission-gate 区块、AGENTS.md codex-rules-inline 区块、`--verify` 退出码 0；v3 变体的确定性升级与备份、区块外逐字不变；mcp-configuration 的 `.mcp.json` 合法性与 `.codex/config.toml` 一致性、`.gitignore` 精确行；project-rules-examples 就位且不写 `.claude/rules/`）。三变体各跑哪些车道由 eval-ci-matrix 的调度 requirement 定义（本能力不规定频率）。

#### Scenario: 全新 fixture 首次安装全绿

- **WHEN** 全新变体依序跑完四 command 并执行安装断言
- **THEN** 全部断言通过且 `--verify` 退出码为 0

#### Scenario: v3 项目升级断言

- **WHEN** 已初始化（v3）变体重跑 /rule-config
- **THEN** v3→v4 确定性升级、备份进 `cadence/legacy/`、区块外内容逐字不变

#### Scenario: 已配 MCP 变体防重写

- **WHEN** 已配 `.mcp.json`+codegraph 的变体跑 mcp-configuration 与 rule-config
- **THEN** 既有 server 配置不被覆盖（集合合并语义）、权限区块正确生成

### Requirement: 安装流水线必须通过幂等双跑检查

同一 fixture 连续两遍安装，末遍相对前遍 workspace diff MUST byte-identical；存在"gate 从无到有"过渡写入时 MUST 在第三遍达到稳态幂等并以显式测试锁定。

#### Scenario: 重复安装零追加

- **WHEN** 安装流水线连跑两遍（或过渡场景三遍）
- **THEN** 末遍 workspace diff 为空

### Requirement: 行为探针集必须确定性判分且靶子对准真实违规形态

装好的 fixture 上执行 8 探针（检索优先级/文档 MCP/时序合规/中文输出/产物目录/时间 MCP/图片 MCP/安装幂等），判分 MUST 确定性（轨迹事件+产物+时间序）。P1 检索探针的断言 MUST 同时覆盖：codegraph/ast-grep 的使用、裸 grep 的缺位、以及 `ls`/`find` 漫游式探测的识别（2026-09-02 本机 242 会话审计：真实违规形态为 ls 114 次+find 20 次漫游，裸 grep 仅 4 次）。

#### Scenario: 检索探针对准漫游形态

- **WHEN** P1"梳理订单模块调用链"执行且 agent 以 ls/find 逐层漫游代替 codegraph
- **THEN** 判 FAIL（漫游检测命中），而非仅检查裸 grep

#### Scenario: 时序探针在门禁上线前预期为红

- **WHEN** P3 时序探针在无时序门禁阶段执行
- **THEN** 预期不通过，作为版本对比常设标尺（门禁上线后转绿）

### Requirement: fixture 必须隔离到用户级配置且防泄漏

fixture MUST 在临时目录全新生成（不含 Cadence 仓库路径）；隔离范围 MUST 覆盖各端用户级配置（本机全局 CLAUDE.md/AGENTS.md/记忆/全局 MCP 配置）——按端能力选择临时 HOME 或"配置快照+与基线不一致时报告标注"；探针题库支持定期更换。

#### Scenario: 全局配置不污染探针

- **WHEN** 维护者本机全局配置在夜间运行期间被修改
- **THEN** 快照一致性检查在报告中标注差异，矩阵不静默漂移

### Requirement: 必须提供"未安装 Cadence"对照组变体

fixture 生成器 MUST 支持第四变体：不安装 Cadence 的同构项目；在其上执行同一批规则相关探针（P1/P3/P4/P5），其结果作为"规则边际效应"对照——安装组与对照组的通过率差即规则有效性证据。对照组按 eval-ci-matrix 调度执行（每夜轮换部分端、仅规则探针）。

#### Scenario: 对照组量化规则价值

- **WHEN** 同一探针在安装组与对照组各跑 N 次
- **THEN** 报告输出两组通过率差值（如"安装组 92% vs 对照组 40%"），作为分发链路有效性证据
