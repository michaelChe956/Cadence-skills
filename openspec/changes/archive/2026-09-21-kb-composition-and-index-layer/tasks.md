# Tasks

> 高层工作包；精确文件、命令与实施顺序由 writing-plans 写入 `cadence/plans/`。

## WP1 CAP 域与模板 [R1 CAP 组合能力实体]

新增 `capabilities/` 到 bootstrap 四处清单（固定输入声明无、固定输出树/检测集合/固定产物三副本 + manifest documents.capabilities）；新增 overview `capability-composition-template.md`；api-scope 模板增"能力组合诉求"表；overview SKILL.md 增 CAP 生成职责（两通道、状态机、接口索引导航分区）。

验收：模板存在含状态机与实现关联；三副本一致含 capabilities/；诉求表存在。

## WP2 JOIN_KEY 证据与横向解禁 [R2 JOIN_KEY 证据纪律, R3 派生关系图]

api SKILL.md 增输入 API 契约/鉴权/JOIN_KEY 逐跳证据核实职责与索引"能力组合"分区写入格式；relation-types.md 横向 3 类改标"已启用（2b）"+唯一写入方限定；api/pages 矩阵写入行确权仍限纵向。

验收：JOIN_KEY 纪律措辞与 api §7.1 衔接；横向标注更新且写入方限定明确。

## WP3 relation-graph 派生边表 [R3]

input-contract/输出契约与 base-info SKILL.md 增图首建职责；各领域 Skill 原子写入义务同步（api/pages/overview/update 更新清单增图重建）；bootstrap global-validation 第 6 项等值校验。

验收：图契约（严格派生/derived_from/等值校验）三处一致；第 6 项存在。

## WP4 context 图消费与漂移分级 [R4]

progressive-retrieval-guide 与 context SKILL.md：图优先直取+降级留痕；组合命中检查；漂移分级（普通/关键失效判定清单）。

验收：直取分支含图路径；分级条件落成可操作清单；无新状态枚举。

## WP5 update 横向重算与锚点复核 [R5]

update SKILL.md：影响链横向重算（删除/废弃→CAP 失效）、锚点复核（失效登记待重锚）、与图重建原子提交。

验收：重算与复核规则存在且指向既有原子提交机制。

## WP6 变更验证 [全部]

机械核对 + `openspec validate`；对照设计验收标准 5 条；不变量零改动核查；随后执行统一测试（结构化校验脚本，见设计 §6）。

验收：验证汇报 + 测试脚本输出。
