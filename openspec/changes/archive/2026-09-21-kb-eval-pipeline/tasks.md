# Tasks

> 高层工作包；精确文件、命令与实施顺序由 writing-plans 写入 `cadence/plans/`。

## WP1 fixture 标准版全埋点 [R1 fixture 资产与埋点契约]

`evals/kb/fixtures/standard/`：3 服务 + Vue3 + 4 表 DDL + 埋点 F1–F10 + 两变体声明 + 埋点说明（埋点→机制→断言编号对照表）+ F9 变更包五文件。

验收：fixture 完整性检查脚本通过；埋点说明与文件一一对应。

## WP2 断言器三层 + 自测样本 [R2 三层断言器与自测]

`assertions/tier0.py`（26 项正式化+扩充）、`named.py`（F1–F10 对照）、`negative.py`（反例）、`fixtures-broken/` 损坏样本 + 自测入口。

验收：对合法样本全绿、对损坏样本全红、退出码正确。

## WP3 runner 阶段化流水线 [R3 阶段化流水线与断点续跑]

`runner/run.py`：副本生成、user-input 注入、阶段 A 调度+断言+results.json 断点续跑、阶段 B 四探针、熔断、报告输出。

验收：--stage 单阶段可跑；断点续跑跳过已完成阶段；熔断生效。

## WP4 探针集 [R3]

四探针 prompt + 期望 + 断言绑定（组合查询/规则检索/变更更新/漂移分级）。

验收：每探针有独立断言且不依赖 agent 自述。

## WP5 首轮 Tier-1 跑通与调优 [R5 调优回路与断言红线]

执行 `--variant full` 全链；失败四分类处理（预期 2–3 处 skill 缺陷走小变更）；产出首轮基线报告。

验收：全链通过或失败全部归因并处理；基线 results.json 入档。
