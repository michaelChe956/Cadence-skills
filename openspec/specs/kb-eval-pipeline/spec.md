# kb-eval-pipeline Specification

## Purpose
KnowledgeBase 技能体系的自动化回归测试能力：fixture 资产与埋点契约、三层确定性断言器与自测、阶段化容器流水线与断点续跑、车道分层与触发、调优回路与断言红线。

## Requirements
### Requirement: fixture 资产与埋点契约

`evals/kb/fixtures/standard/` MUST 作为 git 管理的 fixture 资产存在，包含 3 个 Spring Boot 服务、1 个 Vue3 前端与 4 表 DDL，且埋点 F1–F10 齐全：组合诉求样本（a 查用户基本信息 + b 查账户信息 + api-scope 诉求行）、JOIN_KEY 同名陷阱（同名字段映射不同表且一侧断链）、订单状态机（枚举+迁移+测试断言）、消息生产/消费与定时任务、明文密码与内部 IP、寄生业务规则（表注释与 Controller 注释）、带业务意图的 git 历史、product.md 两变体（variant-full/variant-min）、破坏性变更模拟（删除输入 API 端点）与配套五文件变更包、基线后未声明代码改动。每个埋点 MUST 在 fixture 的埋点说明中登记其目标机制与对应具名断言编号。

#### Scenario: fixture 完整性检查通过

- **WHEN** Tier-0 运行 fixture 完整性检查
- **THEN** F1–F10 埋点文件全部存在且与埋点说明登记一致，两变体可生成

#### Scenario: 埋点缺失即红

- **WHEN** 任一埋点文件被删除或与登记不符
- **THEN** fixture 完整性检查失败并指出缺失项

### Requirement: 三层断言器与自测

`evals/kb/assertions/` MUST 提供三层确定性断言：结构不变量（矩阵六列、词表枚举、图边数==矩阵行数、documents 计数一致、节序符合模板等，不依赖产物具体内容）；具名实体期望（F1–F10 对照表：如 `CAP-USER-ALL-INFO` 存在且 proposed、JOIN_KEY 行待确认、寄生迁移原文保留）；反例断言（产物无明文敏感值、api/pages 阶段产物无横向边、无断链 verified、ai-draft 不被当 confirmed 引用）。断言器 MUST 附故意损坏样本目录并在自测中断言其全部判红；断言 MUST 只读产物文件与 transcript 工具调用记录，MUST NOT 依赖 agent 自述。

#### Scenario: 结构断言对合法产物判绿

- **WHEN** 对按契约生成的样本产物运行 tier0
- **THEN** 全部结构不变量通过

#### Scenario: 断言器自测防假绿

- **WHEN** 对故意损坏样本运行三层断言器
- **THEN** 三层断言全部判红并命中预期断言；任一断言未命中即视为断言器失效，自测不通过

### Requirement: 阶段化流水线与断点续跑

kb-eval MUST 以独立容器考场运行（自有 Dockerfile 与镜像 tag，不与既有夜测 docker 共用镜像/入口/结果目录；CLI 于容器启动时安装当日正式版，不预装不锁版本；认证从宿主机复制注入）。容器内编排器 MUST 实现：fixture 拷贝至工程根、git 两步历史（修复意图提交含真实 diff）、配置快照导出至容器内只读目录并按固定算法计算指纹、user-input 渲染（按变体注入）、skills 与断言器拷入。阶段 A 按固定顺序执行（bootstrap→base-info→api→pages→overview→global-validation），每阶段一次 coding agent headless 调用（prompt 含阶段边界与预算约束），随后在容器内运行该阶段断言子集（早期阶段不得断言后期产物），失败即停该端。results MUST 记录每阶段状态、transcript 与用量并支持同容器断点续跑（已成功阶段跳过）；报告 MUST 含通过矩阵（stages+probes）、对基线具名 diff 与失败 transcript 路径，落盘到独立结果目录。阶段 B 探针集 MUST 含九个：机制探针四个（组合查询、规则检索、变更更新、漂移分级）与真实任务探针五个（字段变更 Coding、规则冲突 Debug、新支付方式影响评估、跨域导出方案设计、漂移改动 Review），每个探针 MUST 有可执行断言（对输出文本断言具名实体/规则引用/分级词，或对产物文件断言）。宿主机 MUST 提供独立入口（选择端与变体、构建/复用镜像），与夜测入口互不影响；支持 `--fast` 模式（核心阶段+组合探针）。

#### Scenario: 阶段失败即停

- **WHEN** api 阶段断言失败
- **THEN** 流水线停止、transcript 留存、results.json 记录 api 为失败；重跑时已完成阶段被跳过

#### Scenario: 断点续跑

- **WHEN** results.json 已记录前三阶段成功且产物完整
- **THEN** 重跑从 pages 阶段继续，不重复执行已完成阶段

#### Scenario: 阶段断言不越界

- **WHEN** bootstrap 阶段执行 mark-stage-done
- **THEN** 只运行该阶段断言子集（输入/manifest 结构与敏感反例），不断言 CAP/RULE 等后续产物

#### Scenario: 探针断言可执行

- **WHEN** P1 组合查询探针完成
- **THEN** 对输出文本的具名断言（引用 CAP 与两输入端点、JOIN_KEY 待确认显式指出）程序化判定并计入通过矩阵

### Requirement: 车道分层与触发

Tier-0（结构校验+断言器自测+fixture 完整性，$0）MUST 可独立运行且不调用任何 LLM；Tier-1（fixture 全链）MUST 手动触发；报告路径与车道语义 MUST 与 rule-eval-p0 约定对齐（`cadence/reports/eval/<日期>/`）。首期 MUST 不接入 PR 工作流（PR 车道接入为后续项，本变更仅保证 Tier-0 具备零成本可接入性）。

#### Scenario: Tier-0 零 LLM 运行

- **WHEN** 在无 API 凭据环境运行 Tier-0
- **THEN** 全部检查完成且无任何模型调用

#### Scenario: Tier-1 手动触发

- **WHEN** 维护者执行独立入口（如 `run.py --agent claude --variant full`，宿主机侧起独立容器考场）
- **THEN** 容器内全链自动完成并产出评分报告；夜测入口与结果目录不受影响

### Requirement: 调优回路与断言红线

失败 MUST 四分类处理：skill 文本缺陷→经 OpenSpec 小变更修复后重跑受影响阶段；断言缺陷→修改期望 MUST 附设计评审记录（防"改答案凑通过"）；fixture 缺陷→修埋点并更新埋点说明；agent 遵循问题→记录为 skill 措辞强化项。断言期望 MUST NOT 因"agent 做不到"而放松——做不到即 skill 缺陷。

#### Scenario: skill 缺陷走变更修复

- **WHEN** 失败归因为 skill 文本缺陷
- **THEN** 修复走 OpenSpec 小变更，修复后仅重跑受影响阶段

#### Scenario: 断言放松被拒绝

- **WHEN** 有人提议因 agent 无法满足而放宽具名断言
- **THEN** 该提议被红线规则拒绝，问题转 skill 缺陷处理
