# Tasks: rule-eval-p0

> 高层工作包；精确文件、命令、测试与提交步骤由 Plan（cadence/plans/）展开。每包映射 delta specs 的 requirement。

## 1. 骨架与 fixture（eval-pipeline）

- [ ] 1.1 eval 目录骨架 + fixture 生成器（三变体：全新/已初始化 v3/已配 MCP+codegraph，临时目录隔离生成）
- [ ] 1.2 阶段一安装流水线 runner：headless 依序调用四 command + 每步产物断言表（TDD：断言器单测用 mock 轨迹）
- [ ] 1.3 幂等双跑检查（含"gate 过渡写入"第三遍稳态语义测试）

## 2. 轨迹适配与断言器（eval-trajectory-scoring）

- [ ] 2.1 统一中间格式定义 + claude 适配器（stream-json）
- [ ] 2.2 codex / pi 适配器
- [ ] 2.3 kimi 适配器（先行单端验证后入矩阵）
- [ ] 2.4 确定性断言器：事件匹配 + 产物 + 时间序；假绿 gate（permission_denials/is_error）；排除规则原文匹配
- [ ] 2.5 fake MCP server（time/context7/图片三探针用）+ fixture 配置注入

## 3. 探针集（eval-pipeline）

- [ ] 3.1 8 个探针定义（P1-P8，env 注入 prompt）+ 各自断言规则绑定
- [ ] 3.2 探针题库轮换机制（可更换变体）

## 4. 车道与报告（eval-ci-matrix）

- [ ] 4.1 运行器工程面：断点续跑、多层成本熔断、模型/CLI 双 pin、transcript 留存
- [ ] 4.2 Tier-0 workflow（云端 PR：静态+断言器自测+mock 冒烟；路径过滤触发）
- [ ] 4.3 Tier-1 夜间 workflow（self-hosted 标签路由、矩阵调度、多 run 均值+容差、skip 降级语义）
- [ ] 4.4 四张度量矩阵 + 基线具名 diff 报告生成（`cadence/reports/eval/<日期>/`）
- [ ] 4.5 self-hosted runner 注册文档与告警（维护者一次性操作指引）

## 5. 收尾

- [ ] 5.1 首轮基线建立（p1 合入后执行；pre-p1 对照单独标记）
- [ ] 5.2 端到端演练：手动触发 Tier-1 全矩阵跑通一夜，报告四矩阵齐全
