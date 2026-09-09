## Purpose

四端轨迹适配与确定性断言器：把各 coding agent 的 stream-json 轨迹统一为中间格式，程序化断言判分；内置假绿/假阳/归因三族防线，正确处理 p1 受管 deny 的"预期拦截"语义。

## ADDED Requirements

### Requirement: 四端轨迹必须适配为统一中间格式且模型实测回读

系统 MUST 为 claude -p、codex exec、pi -p、kimi -p 各提供适配器，将原生轨迹解析为统一中间格式（至少含：工具调用事件序列、permission_denials 及其规则归属、is_error、产物写事件、时间序、模型标识）；断言器 MUST 只消费中间格式。模型标识 MUST 从 transcript 实测回读（非启动参数），与该端 pinned 模型不一致时标 `MODEL_DRIFT` 且该 run 出矩阵。Kimi 无公开 headless 文档，其适配器 MUST 先行单端验证后再入矩阵。

#### Scenario: 断言器与端解耦

- **WHEN** 新增或更换任一 agent 端
- **THEN** 仅需新增其适配器，断言器与探针定义零改动

#### Scenario: 模型漂移出矩阵

- **WHEN** 某 run 的 transcript 回读模型与该端 pinned 模型不一致（或 pi 会话内发生 model_change）
- **THEN** 该 run 标记 `MODEL_DRIFT`、不进入任何矩阵统计，报告单列

### Requirement: 假绿防线必须对 deny 双分类且启用前取证字段结构

断言器 MUST 区分两类拒绝：**区块外 deny 或 is_error** → 该 run 判 FAIL（防静默拒绝假绿）；**受管区块内 deny**（拦截规则属 `cadence-managed:permission-gate` 区块）→ 不判 FAIL，转入"改道率"子度量——模型被拦后 N 步内改用 preferred 工具即 PASS 并计入 deny 有效性，改道失败或放弃才 FAIL。结果 JSON MUST 含 fixture `settings.json` 受管区块快照以判定归属。该 gate 启用前 MUST 先在 fixture 人为制造真实 denial 取证字段真实结构（本机 242 个真实会话中 permission_denial 出现 0 次，无自然样本可对照）。

#### Scenario: 静默拒绝判失败

- **WHEN** 某 run exit 0、产物存在，但轨迹含区块外 permission_denial 或 is_error
- **THEN** 判 FAIL 并标注拒绝原因与"harness 配置错误"归类

#### Scenario: 受管 deny 改道成功计 PASS

- **WHEN** 模型尝试被 deny 的 Grep（受管区块内条目）→ 被拦 → 后续步骤改用 codegraph 完成任务
- **THEN** 该 run 判 PASS 且计入"deny 改道率"子度量（p1 成功路径不被误判）

### Requirement: 轨迹断言必须排除规则原文

断言"是否使用了某工具/MCP"时 MUST 排除 agent 朗读规则文本与工具结果中的原文匹配。

#### Scenario: 朗读不等于执行

- **WHEN** agent 复述了"优先使用 codegraph"但实际调用的是裸 grep
- **THEN** 判 FAIL（断言只看真实工具调用事件）

### Requirement: MCP 探针必须使用 fake MCP server

"必须调用指定 MCP"类探针（文档/时间/图片）MUST 在 fixture 配置 fake MCP server（工具名一致、种子已知状态、记录调用），断言其调用记录且轨迹无其他信息源工具调用；真实 MCP 端到端验证仅属 Tier-2。

#### Scenario: fake MCP 断言调用

- **WHEN** 探针 P6"现在几点，换算纽约时间"执行
- **THEN** fake time MCP 收到调用、答案与种子状态一致、无编造

### Requirement: 探针任务提示必须经环境变量注入

探针 prompt MUST 经 env 注入传递，MUST NOT 内联进 shell 命令字符串。

#### Scenario: 注入安全

- **WHEN** 探针 prompt 含引号或特殊字符
- **THEN** 任务语义原样保持，无 shell 展开污染

### Requirement: 失败必须归因分类且基础设施失败不入矩阵

断言器 MUST 将失败分为"agent 行为失败"与"基础设施失败"（CLI 崩溃、登录失效、超时、网络抖动）；后者 MUST 标 `infra-fail` 并从四矩阵统计中剔除（计 skip），单独汇总——防 harness 故障污染遵循率度量。

#### Scenario: 登录失效不污染矩阵

- **WHEN** 某端某夜全部 run 因 CLI 登录失效失败
- **THEN** 该端该夜标 unavailable、矩阵该列缺测而非 0%

### Requirement: 结果 JSON 必须携带版本化最小契约

结果与基线 JSON MUST 含顶层 `schema_version`（初始 "1.0"）与稳定键（`run_id/agent/model/cli_version/probe_id/rule_clause_ids/verdict/fail_reason/denials/transcript_path/started_at/duration_s`）；其余字段放 `details` 自由演进。主版本不匹配的基线 MUST 不参与 diff 且报告显式标注"基线 schema 不兼容，本次不比对"。

#### Scenario: schema 演进不静默错比

- **WHEN** 基线文件 schema_version 主版本低于当前结果
- **THEN** 具名 diff 跳过该基线并显式标注原因，不输出错误对比
