# Eval Ci Matrix Specification

## Purpose
三级车道编排、夜间矩阵、基线治理与运行器工程面：把流水线接入 CI（PR 零真实 CLI、夜间 self-hosted、手动 Tier-2），产出四张度量矩阵与双键基线具名 diff，并以审计表利用既有真实 session。

## Requirements

### Requirement: 三级车道必须隔离真实 CLI 且夜间前置自检

Tier-0（PR，云端）MUST 零真实 agent CLI 调用：静态检查、断言器自测、mock 冒烟，以及对留存真实 transcript 的**离线重跑 job**（断言器对历史轨迹重判并 diff 判定，防断言器自身回归）。真实 CLI 仅 Tier-1（夜间 self-hosted）与 Tier-2（手动）。Tier-1 job MUST 在进入付费矩阵前先行 mock 自检通过。PR 车道 MUST 仅对 eval 与 skill 文件路径变更触发。

#### Scenario: PR 不跑真实 agent

- **WHEN** PR 触发 CI
- **THEN** Tier-0 无任何 claude/codex/pi/kimi 进程调用，但包含离线重跑 job

#### Scenario: 断言器回归被离线重跑抓住

- **WHEN** 断言器逻辑修改后对历史 transcript 重跑出现判定翻转
- **THEN** 离线重跑 job 红灯并列出翻转的 run

### Requirement: 夜间矩阵必须按调度表执行并滚动聚合

Tier-1 按调度表执行（首版，可按实测时长调整）：**阶段一**安装流水线=全新变体 × 4 端 × 各端 pinned 模型；v3 升级变体=降频（每周 × 2 端）；**阶段二**探针=8 探针分夜轮转（奇数夜 P1/P3/P5/P7，偶数夜 P2/P4/P6/P8）× 4 端 × 各端 pinned 模型 × 2 runs；**对照组**=每夜 4 个规则探针 × 轮换 2 端。模型口径：每端使用其当前配置模型并 pin（版本锁；维护者 2026-09-02 裁定：四端模型各不相同、接受端×模型混合效应，跨端一致性度量即"各端实际配置下的差异"）。四张矩阵 MUST 以滚动 7 夜聚合产出；判定取多 run 均值+容差，缺测组合 MUST 在报告显式表达而非判红。

#### Scenario: 分夜轮转

- **WHEN** 奇数夜 Tier-1 执行
- **THEN** 仅跑 P1/P3/P5/P7 组合，其余探针该夜缺测并在矩阵标注

#### Scenario: 滚动聚合矩阵

- **WHEN** 第 7 夜运行结束
- **THEN** 四矩阵按近 7 夜数据聚合产出，单夜缺测不产生红灯

### Requirement: 报告必须输出四矩阵、双键基线 diff 与基线治理

每夜 MUST 产出：规则遵循率矩阵（探针×端）、MCP 使用率、弱模型保证度（强弱差值，按端内比较）、跨端一致性（各端 pinned 配置口径的极差与方差）；基线 diff MUST 支持双视图——探针×端 与 规则条款×探针（条款 ID 与 p1 元数据同源，定位"改哪条规则"）；具名降级（形如 `▼ P1检索@Codex: 100%→60%`）超阈值红灯。基线文件 MUST 仅在维护者显式提交后生效，夜间只对比不改基线；审计表输出至 `cadence/reports/eval/audit/` MUST NOT 入 git。

#### Scenario: 具名降级红灯

- **WHEN** 某条款×探针组合较基线跌幅超阈值
- **THEN** workflow 失败并标名该组合前后值与所属规则文件

#### Scenario: 基线不被夜间覆盖

- **WHEN** 夜间运行产生新均值
- **THEN** 基线文件内容不变，报告仅给 diff 建议

### Requirement: 运行器必须具备续跑、熔断、双 pin 与保留策略

运行器 MUST 断点续跑（结果存在即跳过）；MUST 多层熔断（轮次上限+超时+累计成本上限；订阅计费无 per-run 成本信号时以轮次/时长为代理）；MUST 双 pin（`--model` 显式指定该端配置模型 + CLI 版本锁）；transcript 留存策略：失败 run 全量保留，通过 run 保留中间格式+摘要、原始轨迹 N 夜后清理。

#### Scenario: 断点续跑

- **WHEN** 夜间运行中断后重启
- **THEN** 已完成组合跳过，仅补缺失部分

#### Scenario: 保留策略

- **WHEN** 通过 run 的原始 transcript 超过保留窗口
- **THEN** 清理原始文件，保留中间格式与结果 JSON

### Requirement: 端级与 runner 级不可用必须无阻塞降级

self-hosted 离线或配额耗尽时 workflow MUST skip 结束不误红；任一端适配器失败 MUST 标 unavailable 且其余端继续；连续 3 夜失败的端 MUST 在报告置顶告警。GitHub Actions runner 离线时 job 排队超时问题 MUST 以云端探活→条件触发类机制规避。

#### Scenario: 端级失败不阻塞

- **WHEN** Kimi 适配器某夜全部 infra-fail
- **THEN** 其余三端矩阵正常产出，Kimi 列标 unavailable 并计入连续失败计数

#### Scenario: 机器关机夜间跳过

- **WHEN** cron 触发时无 self-hosted runner 在线
- **THEN** workflow 标记 skipped 结束，主干 CI 不受影响

### Requirement: 必须提供既有 session 审计表（第五张观测表）

系统 MUST 复用四端适配器的离线解析能力扫描本机既有 session 存量（claude/codex/pi/kimi 会话目录），产出审计观测表：真实生产分布下的工具使用形态、模型标签分布、规则相关行为频次。审计表 MUST 仅作观测参考：不进 gate、不入基线、不入 git（含业务项目路径与任务内容），且 MUST NOT 替代受控探针（样本非受控）。

#### Scenario: 审计修正探针设计

- **WHEN** 审计发现真实违规形态与探针断言靶子不符（如漫游式探测）
- **THEN** 该发现进入探针题库迭代输入，审计表本身不产生红灯

### Requirement: Docker 夜测考场必须五端覆盖 omp

Tier-1 夜测考场 MUST 将 oh-my-pi(omp)作为第五端纳入,与既有四端同构:

- 考场容器 MUST 能运行 omp 无头会话(`omp -p`):二进制以 ELF 复制方式进入容器(与 kimi 同模式),凭据以最小集(provider 配置自含凭据文件与用户配置)注入;
- stage1 四命令安装流水线 MUST 对 omp 同跑,omp 端安装效果本身即被验收;
- 既有 P1-P8 全部探针 MUST 对 omp 同跑(夜测矩阵整体五端化,而非仅新增探针);
- 结果透视的端维度 MUST 含 omp(端×探针矩阵、合计行、轮次/均时),omp 基线首轮建立,首轮允许低于四端历史基线且透视可见;
- omp 考场不可用(容器化失败)时 MUST 无阻塞降级为四端矩阵,降级事实 MUST 有机器可读载体:omp 端 run 记录(schema 1.0 JSON)落盘并携带 `degrade` 字段说明原因,透视汇总检测到该字段时在输出中打印降级注记;不得阻塞其余端执行(延续既有端级降级语义)。

依赖注记:omp 在未落地规则桥(Change A 框架部分)的项目上跑规则遵循探针必然大面积失败(omp 遮蔽机制下规则与 L0 全盲),故本能力 MUST 与框架改造同 change 落地或在其后启用 omp 探针。

#### Scenario: omp 列出现在夜测透视

- **WHEN** 五端夜测完成并运行透视汇总
- **THEN** 端×探针矩阵包含 omp 列,P1-P8 各行有 omp 成功率/均时/轮次
- **AND** 基线对比对 omp 列按首轮基线执行

#### Scenario: omp 考场故障不拖垮四端

- **WHEN** omp 容器化或无头会话在夜测中失败
- **THEN** 四端矩阵照常执行并产出透视
- **AND** 透视中 omp 列标注考场降级原因

### Requirement: Docker 夜测评分必须消费探针断言 spec

Docker 夜测(`eval/docker/night.py`)的探针评分 MUST 消费探针定义中的 `assertions` 列表:对 `text_contains`/`text_lacks` 逐条以最终输出文本判定;既有 P 组探针的既有评分语义 MUST NOT 改变。探针定义含断言而无分支时 MUST NOT 默认 PASS——不存在「无条件通过」路径(防假绿)。

#### Scenario: 断言不满足判 FAIL

- **WHEN** R1 探针输出不含任何索引锚点
- **THEN** 该探针判定 FAIL 而非 PASS

### Requirement: stage1 确定性断言必须落盘为夜测记录并入透视

stage1 确定性断言结果 MUST 以 schema 1.0 run 记录落盘(如 `probe_id="stage1"`),任一断言失败 MUST 使该记录为 FAIL 并出现在透视矩阵;不得只存在于 stdout。

#### Scenario: stage1 断言失败进入透视

- **WHEN** 测试项目缺一个应有软链且夜测完成
- **THEN** 透视矩阵出现 stage1 行的 FAIL 条目,可定位到 `omp.symlinks`
