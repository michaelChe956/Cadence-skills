## Purpose

四端轨迹适配与确定性断言器：把各 coding agent 的 stream-json 轨迹统一为中间格式，并以程序化断言判分，内置假绿与假阳两族防线。

## ADDED Requirements

### Requirement: 四端轨迹必须适配为统一中间格式

系统 MUST 为 claude -p、codex exec、pi -p、kimi -p 各提供一个适配器，将各自的原生轨迹输出（stream-json/等价物）解析为统一中间格式（至少含：工具调用事件序列、permission_denials、is_error、产物写事件、时间序）；断言器 MUST 只消费中间格式。Kimi 无公开 headless 文档，其适配器 MUST 先行单端验证后再入矩阵。

#### Scenario: 断言器与端解耦

- **WHEN** 新增或更换任一 agent 端
- **THEN** 仅需新增其适配器，断言器与探针定义零改动

### Requirement: 判分必须强制假绿防线

断言器 MUST gate 每次运行的 `permission_denials` 与 `is_error`：任一非空/为真即判该 run 失败，即使 exit code 为 0 且产物断言通过（防 dontAsk 静默拒绝导致的假绿，Backgrind 实测先例）。

#### Scenario: 静默拒绝判失败

- **WHEN** 某 run exit 0、产物存在，但轨迹含 permission_denial
- **THEN** 判分结果为 FAIL 并在报告中标注拒绝原因

### Requirement: 轨迹断言必须排除规则原文

断言"是否使用了某工具/MCP"时 MUST 排除 agent 朗读规则文本与工具结果中的原文匹配（防止"复述了规则"被误判为"执行了规则"的假阳）。

#### Scenario: 朗读不等于执行

- **WHEN** agent 在输出中复述了"优先使用 codegraph"但实际调用的是裸 grep
- **THEN** 该 run 判 FAIL（断言只看真实工具调用事件）

### Requirement: MCP 探针必须使用 fake MCP server

"必须调用指定 MCP"类探针（文档/时间/图片）MUST 在 fixture 中配置 fake MCP server（工具名与真实一致、种子已知状态、记录调用），断言其调用记录而非真实网络端点；真实 MCP 的端到端验证仅属 Tier-2 手动车道。

#### Scenario: fake MCP 断言调用

- **WHEN** 探针 P6"现在几点，换算纽约时间"执行
- **THEN** 断言 fake time MCP 收到调用且 agent 未改用其他通道编造答案

### Requirement: 探针任务提示必须经环境变量注入

探针 prompt MUST 经 env 注入传递给 headless CLI，MUST NOT 内联进 shell 命令字符串（防注入与引号转义污染探针语义）。

#### Scenario: 注入安全

- **WHEN** 探针 prompt 含引号或特殊字符
- **THEN** 任务语义保持原样，无 shell 展开污染
