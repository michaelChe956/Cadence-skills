# Specification: mcp-host-lane

## Purpose

以「模拟用户方式」观测三个 bigmodel HTTP MCP（web-search-prime/web-reader/zread）在五端（claude/codex/pi/kimi/omp）的真实可用性，结果进透视表且不污染端健康度。

## ADDED Requirements

### Requirement: R1: 判定态词表

车道 SHALL 定义五态判定：`PASS`（transcript 存在非错误 `mcp__<server>__` 调用）、`CALL_FAIL`（存在失败调用尝试=挂载后调不动）、`NOT_MOUNTED`（挂载清单无该 server=客户端不挂载此类型）、`SETUP_BLOCKED`（授权/信任未过或 transcript 缺失）、`INFRA_FAIL`（进程异常或前置门未过，不入表）。全部非门禁。

#### Scenario: codex 兼容性问题呈现

- **WHEN** codex 会话挂载 server 且调用失败（如 Transport channel closed）
- **THEN** 判定 `CALL_FAIL`，错误签名随记录落盘，矩阵显示 ⚙

#### Scenario: 客户端不挂载此类型

- **WHEN** 某端挂载清单（会话首条消息的枚举输出）不含目标 server
- **THEN** 判定 `NOT_MOUNTED`，矩阵显示 ⊘，不进健康度分母

### Requirement: R2: 网络前置门

每轮执行前 SHALL 对三个端点跑 curl 全序列（initialize→session→initialized，真实 key）：任一不过则整轮记 `ENV_FAIL` 且不入透视表——网络层问题不得冒充兼容性结论。

#### Scenario: 端点故障整轮隔离

- **WHEN** 前置门 curl 非 200 或无有效 JSON-RPC 响应
- **THEN** 本轮零记录入表，运行输出标注 ENV_FAIL 与失败端点

### Requirement: R3: 忠实度四维

车道 SHALL 满足：①配置=用户真实配置零改写（不预置/不合成任何 server 块）②挂载=各端自发发现（以会话内挂载清单为证）③交互=纯自然语言探针（禁注入工具调用）④会话=PTY 交互式（禁 headless `-p`）。

#### Scenario: 不改写用户配置

- **WHEN** 车道运行前后
- **THEN** 用户各端配置文件与运行前 diff 为零

### Requirement: R4: 探针执行与记录

`run_user_mcp_probe` SHALL：真实 HOME+用户项目 cwd 起五端 PTY 会话→首条消息固化挂载清单→依次输入 M1/M2/M3 探针原话→复用五端 adapter 解析宿主 transcript→按 R1 五态判定→落 schema 1.0 记录（`run_id` 前缀 `host-<agent>-`）。

#### Scenario: 首轮复现基准签名

- **WHEN** 首轮五端实测
- **THEN** codex 三探针 `CALL_FAIL`、其余四端 `PASS`（或带原因的 `SETUP_BLOCKED`/`NOT_MOUNTED`），与用户本机交互式实测一致

### Requirement: R5: 路由分流

`night.py` SHALL 将 M 组路由至宿主车道；P/R/D 组 docker 夜测行为不变；M 组不进常规夜测循环（按需触发）。

#### Scenario: M 组不进 docker 车道

- **WHEN** 以 M 组探针调用夜测入口
- **THEN** 不创建 docker 容器，执行宿主车道并产出 host- 前缀记录

### Requirement: R6: 透视呈现

`report_matrix` SHALL 以独立分组「M 组（HTTP MCP 兼容 · 宿主车道）」渲染五态（✅/⚙/⊘/⛔），且五态均不计入端健康度分母。

#### Scenario: 健康度不受 M 组影响

- **WHEN** M 组存在 CALL_FAIL 记录
- **THEN** 总览各端通过率分母不含 M 组记录
