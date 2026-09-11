# Design: HTTP MCP 宿主车道

> 决策源：oracle（测量有效性）+ ter-task（五端机制与工程落地）研究，用户 2026-09-11 拍板合并方案。
> 设计全文见 `cadence/designs/2026-09-11_方案设计_HTTP_MCP五端兼容性观测体系宿主车道_v1.0.md`（v1.0，用户已确认）。

## 核心决策索引

1. **主线=宿主交互车道**（ter 方案）：真实 HOME + 用户项目 cwd + PTY 交互；不采纳 oracle 方案 B（容器全量快照，快照漂移与 headless 校准成本无必要）
2. **忠实度四维**（oracle 标准）：配置零改写、挂载自发、自然语言驱动、curl 前置门——每维一条可检查证据
3. **五态判定**（非门禁）：PASS / CALL_FAIL(⚙ 挂了调不动) / NOT_MOUNTED(⊘ 客户端不挂载) / SETUP_BLOCKED(⛔ 授权或转录缺失) / INFRA_FAIL(❌ 不入表)
4. **M 组迁出 docker 车道**：容器 M 记录已清；P/R/D 行为不变
5. **复用资产**：五端 adapter（omp 复用 pi）、assertor require_ok、SESSION_GLOBS 宿主版定位、report_matrix NOT_MOUNTED 分母豁免机制

## 派生约束

- PTY 会话每端硬超时 6 分钟；首轮 claude 项目 MCP 批准为一次性人工点
- `run_id` 前缀 `host-<agent>-`；结果落 schema 1.0 同目录结构
- M 组不进常规夜测循环，按需触发
