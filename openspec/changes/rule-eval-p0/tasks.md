# Tasks: rule-eval-p0

> 高层工作包；精确文件、命令、测试与提交步骤由 Plan（cadence/plans/）展开。每包映射 delta specs 的 requirement。

## 1. 骨架与 fixture（eval-pipeline）

- [ ] 1.1 eval 目录骨架 + fixture 生成器（四变体：全新 / 已初始化 v3 / 已配 MCP+codegraph / **未安装 Cadence 对照组**；临时目录+用户级配置隔离或快照标注）
- [ ] 1.2 阶段一安装流水线 runner：四 command 依序调用 + 每步产物断言表 + `--verify` 消费（TDD：断言器单测用 mock 轨迹）
- [ ] 1.3 幂等双跑检查（含 gate 过渡写入第三遍稳态测试）
- [ ] 1.4 对照组执行与"规则边际效应"差值报告

## 2. 轨迹适配与断言器（eval-trajectory-scoring）

- [ ] 2.1 统一中间格式定义（含模型回读字段）+ claude 适配器
- [ ] 2.2 codex / pi 适配器；kimi 适配器先行单端验证
- [ ] 2.4 确定性断言器：事件/产物/时间序；**deny 双分类 gate（读 settings.json 受管区块快照判归属→改道率子度量）**；排除规则原文；**失败归因分类（infra-fail 出矩阵）**；**启用前 fixture 人造真实 denial 取证字段结构**
- [ ] 2.5 fake MCP server（time/context7/图片）+ fixture 配置注入
- [ ] 2.6 结果 JSON schema_version 最小契约 + 兼容性测试

## 3. 探针集（eval-pipeline）

- [ ] 3.1 8 探针定义（env 注入；P1 靶子含 ls/find 漫游检测）+ **条款 ID 绑定**（与 p1 元数据同源）
- [ ] 3.2 探针题库轮换机制

## 4. 车道与报告（eval-ci-matrix）

- [ ] 4.1 运行器工程面：断点续跑、多层熔断（无成本信号时轮次/时长代理）、**每端模型 pin+CLI 版本锁+MODEL_DRIFT 出矩阵**、transcript 分级保留
- [ ] 4.2 Tier-0 workflow（静态+断言器自测+mock 冒烟+**离线重跑 job**；路径过滤触发）
- [ ] 4.3 Tier-1 夜间 workflow（self-hosted 标签路由；**分夜轮转调度表、2 runs、滚动 7 夜聚合**；**端级降级+连续 3 夜告警**；mock 自检前置；云端探活防 runner 排队超时）
- [ ] 4.4 四矩阵 + **双键基线具名 diff**（条款×探针 / 探针×端）+ 基线治理（仅维护者提交生效）
- [ ] 4.5 self-hosted runner 注册文档与告警
- [ ] 4.6 **审计表**：四端离线解析扫既有 session（复用适配器），输出 cadence/reports/eval/audit/（不入 git、不进 gate）

## 5. 收尾

- [ ] 5.1 首轮基线建立（含对照组首轮对照；维护者提交基线文件生效）
- [ ] 5.2 端到端演练：连续 7 夜跑通，四矩阵+审计表+双键 diff 齐全
