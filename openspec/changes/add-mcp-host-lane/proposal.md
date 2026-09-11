# Proposal: HTTP MCP 五端兼容性观测体系（宿主交互车道）

## Why

三个 bigmodel HTTP MCP（web-search-prime/web-reader/zread）的五端可用性需要可复现的观测。容器内合成配置的四轮实测证明该路径测出的是 harness 伪影（占位 key/headless 挂载差异/最小 HOME 三层失真），而非产品真相。基准事实（用户本机交互式实测）：仅 codex 因客户端×网关兼容性问题不可用，其余四端可用。

## What Changes

- 新增**宿主交互车道** `run_user_mcp_probe`：真实 HOME、用户项目 cwd、五端 PTY 交互会话（禁 headless `-p`），M 组（M1/M2/M3）探针从 docker 车道迁出
- 忠实度四维标准：配置零改写 / 挂载自发（挂载清单先行）/ 纯自然语言探针 / curl 全序列前置门（不过=ENV_FAIL 整轮不入表）
- 判定态五态词表（全部非门禁）：PASS / CALL_FAIL / NOT_MOUNTED / SETUP_BLOCKED / INFRA_FAIL
- report_matrix 增设「M 组（HTTP MCP 兼容 · 宿主车道）」独立分组与五态符号；不计端健康度分母
- 结果记录沿用 schema 1.0，run_id 前缀 `host-<agent>-` 区分车道

## Impact

- 新增文件：eval 侧宿主车道入口/PTY 驱动/前置门；report_matrix 五态渲染
- 修改：night.py 仅做 M 组路由分流；docker 车道 M 记录不回填
- 不动：P/R/D 组 docker 夜测行为；评分链既有资产复用（transcript→adapter→assertor require_ok）
- 不处理 codex×bigmodel 兼容性本身（只测清楚，不修复）

设计全文：`cadence/designs/2026-09-11_方案设计_HTTP_MCP五端兼容性观测体系宿主车道_v1.0.md`
