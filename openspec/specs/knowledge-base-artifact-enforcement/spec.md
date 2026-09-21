# knowledge-base-artifact-enforcement Specification

## Purpose
TBD - created by archiving change 2026-07-21-enforce-knowledge-base-artifact-completeness. Update Purpose after archive.
## Requirements
### Requirement: 请求响应能力必须同时生成主文件与参数报文配套文件

`knowledge-base-api` MUST 要求范围内每个请求响应能力同时存在能力主文件与 `{标识}_{接口名称}_{API名称}_参数与报文.md` 配套文件，且 `interfaces/README.md` 索引的"参数与报文"列链接可导航到实际文件；缺失任一时 MUST NOT 把 `api` 阶段标记为完成。消息、文件、任务等非请求响应能力 MUST NOT 创建空配套文件。

#### Scenario: 请求响应能力只生成主文件

- **WHEN** 范围内某 REST/RPC 同步能力只生成了主文件而未生成配套参数与报文文件
- **THEN** `api` 阶段完成判定失败
- **AND** 缺失项进入待确认清单

#### Scenario: 非请求响应能力

- **WHEN** 能力类型为消息、文件或定时任务
- **THEN** 只生成主文件
- **AND** 不存在空配套文件时完成判定不受影响

### Requirement: API 文档必须遵循模板节结构并执行输出前模板对照自检

`knowledge-base-api` MUST 要求能力主文件遵循 `assets/api-capabilities-template.md` 的 11 节结构（节序齐全，无内容节按规则填写`未提供`、`未发现`或`不适用`），配套文件遵循 `assets/api-parameters-message-template.md` 的 5 节结构；每个文件落盘前 MUST 逐节与 assets 模板对照自检，禁止用自创节结构替代模板。

#### Scenario: 主文件使用自创节结构

- **WHEN** 接口主文件的节结构不是模板规定的 11 节
- **THEN** 模板对照自检不通过
- **AND** 该文件不得落盘为最终产物

### Requirement: interfaces 索引必须同时包含对外与对内分区

`knowledge-base-api` MUST 要求 `interfaces/README.md` 在任何执行模式下同时存在"对外能力"与"对内能力"两个分区；无对内盘点结果时 MUST 在对内分区写明"未盘点"及原因（执行模式），禁止整块缺失。

#### Scenario: 指定模式未盘点对内能力

- **WHEN** 以指定模式完成 API 阶段且未分析任何对内能力
- **THEN** 索引对内分区存在并注明未盘点原因
- **AND** 索引缺少对内分区时完成判定失败

### Requirement: API 技能必须提供页面链路模式消费候选清单

`knowledge-base-api` MUST 提供第三执行模式"页面链路模式"：`interfaces/README.md` 对内分区存在 `API-CANDIDATE-*` 清单时，按 `references/demo_对内REST.md` 与 `references/demo_对内REST_参数与报文.md` 的格式逐条深挖清单内对内 REST，生成正式接口文档、升级为稳定 API ID 并回写索引；该模式 MUST NOT 扩大为全量对内盘点，MUST NOT 分析清单外能力。

#### Scenario: 候选清单升级为正式文档

- **WHEN** 对内分区存在 pages 登记的候选条目
- **THEN** api 逐条核实 Controller、路由、服务调用链与数据副作用
- **AND** 生成符合对内 REST 模板的主文件与配套参数报文文件，候选升级为稳定 API ID

#### Scenario: 候选无法唯一映射

- **WHEN** 候选条目无法定位唯一后端实现
- **THEN** 保持候选状态并进入待确认清单
- **AND** 不凭名称相似度补造正式接口

### Requirement: 服务配置文档的配置键清单必须逐键完整且键数可核对

`knowledge-base-base-info` MUST 要求每个服务配置文档遵循 `assets/service-configuration-template.md` 的 10 节结构，且第 4 节配置键清单逐键完整：清单行数等于来源文件实际键数（按 Skill 既有去重与合并口径，相同内容文件合并时按全集计）；元数据 MUST 同时记录`来源文件键数`与`文档收录键数`供机械比对，不一致时 MUST NOT 完成 `base-info` 阶段。

#### Scenario: 文档收录键数少于来源文件键数

- **WHEN** 来源配置文件有 587 个唯一键而文档清单只收录 27 个
- **THEN** 键数核对失败
- **AND** `base-info` 阶段不得完成，先查明遗漏原因

### Requirement: 配置脱敏不得省略配置键

`knowledge-base-base-info` MUST 明确脱敏对象是值而不是键：敏感配置的键名、用途、值类型与敏感级别 MUST 逐键列出，仅值写 `<redacted>`；MUST NOT 以敏感为由整条省略配置键或只写敏感键总数。

#### Scenario: 敏感键只写总数

- **WHEN** 服务配置文档对 41 个敏感键只记录"共 41 个敏感键"而未逐键列出
- **THEN** 完成判定失败
- **AND** 必须补齐逐键条目（值仍为 `<redacted>`）

### Requirement: pages 指定模式必须按对象粒度分流并逐路由深挖点名路由

`knowledge-base-pages` MUST 区分 Manifest `scope.pages.selected` 条目的粒度：应用级条目走应用概览路径；路由/菜单级条目 MUST 逐路由深挖——菜单到路由的定位 MUST 记录证据（文件+行号），无法唯一匹配时列候选并询问；每条点名路由 MUST 生成 `PAGE-*` 页面实体、`ROUTE-*` 路由实体与单页面文档（含模板第 3 节与 4.1~4.5 节），且页面全部请求（含经 Store/Hook/封装的间接调用）逐条追踪到 Method+标准 Path。只产出应用级概览 MUST 视为未完成。

#### Scenario: 用户点名菜单但只产出应用概览

- **WHEN** selected 含菜单级条目而产物只有应用级概览、无单页面文档
- **THEN** `pages` 阶段完成判定失败

#### Scenario: 菜单无法唯一定位路由

- **WHEN** 菜单名称或 ID 对应多个候选路由或无匹配
- **THEN** 列出候选并向用户提问澄清
- **AND** 不凭名称猜测路由

### Requirement: 页面文档的 API 引用不得为零链接

`knowledge-base-pages` MUST 要求页面文档中每个页面到 API 的引用要么是 `../interfaces/` 下可导航的稳定 API ID 链接，要么是已登记的 `API-CANDIDATE-*` 条目链接；页面文档 API 引用为零链接时 MUST NOT 完成 `pages` 阶段。

#### Scenario: 页面文档无任何 API 链接

- **WHEN** 范围内页面文档既没有接口主文件链接也没有候选条目链接
- **THEN** 完成判定失败

### Requirement: pages 对 interfaces 索引的候选登记必须遵守最小授权与固定格式

`knowledge-base-pages` MUST 只在 `interfaces/README.md` 的"对内能力"分区追加候选表，这是 pages 唯一获准写 `interfaces/` 的位置；候选条目 MUST 固定包含七字段：候选 ID、HTTP Method、标准 Path（合并 baseURL/代理/网关重写）、前端应用、调用位置（文件+行号）、请求封装链、来源 PAGE/ROUTE ID；该格式 MUST 与 `knowledge-base-api` 页面链路模式的消费格式逐字段一致。

#### Scenario: 页面调用未登记的 REST

- **WHEN** 深挖发现页面调用了索引中不存在的 REST
- **THEN** 按七字段格式在对内分区登记 `API-CANDIDATE-*`
- **AND** 页面文档链接该候选条目，不补造正式接口主文件链接

### Requirement: context 四条证据路径必须逐层输出证据摘要

`knowledge-base-context` MUST 把四条证据路径改为逐层硬门禁：每层输出本层证据摘要（来源、精确位置、本层结论、停止原因）后才允许进入下一层；默认只扩展一跳，扩跳 MUST 记录触发理由；四条路径各自 MUST 有证据或停止原因，禁止留白方向。

#### Scenario: 某条路径未留证据摘要

- **WHEN** 上下文包中某条路径既无证据摘要也无停止原因
- **THEN** 上下文包输出门禁不通过

### Requirement: context 上下文包必须通过输出门禁

`knowledge-base-context` MUST 在输出前自检：十三节输出契约逐节必填（无内容节写明`无直接关系`或`证据缺失+原因`，不得省略整节）；每个关键结论 MUST 挂稳定 ID + 精确文件/行号或显式状态枚举；就绪状态 MUST 按硬性条件清单判定，满足阻断条件时 MUST 判`阻断`。

#### Scenario: 结论无证据载体

- **WHEN** 上下文包中某关键结论没有稳定 ID、文件位置或状态枚举
- **THEN** 输出门禁不通过，结论不得出现在上下文包中

### Requirement: context 输出前必须执行准确性自查

`knowledge-base-context` MUST 在输出前执行四步复核并留痕：引用的每个稳定 ID 读文件确认存在；Method+Path、表名、字段名、配置键与来源逐字一致；候选无法唯一匹配时列出候选清单；证据矩阵每行结论必须含状态列且只使用规定状态枚举。

#### Scenario: 引用不存在的稳定 ID

- **WHEN** 上下文包引用的稳定 ID 无法解析到实际文件
- **THEN** 准确性自查不通过
- **AND** 该引用必须修正或标记待确认后才能输出

### Requirement: global-validation 必须执行内容完整性检查

`knowledge-base-bootstrap` 的 global-validation MUST 在现有检查基础上新增四项内容完整性检查，任一不过 MUST 判 `failed` 并保持 `status: in_progress`、空 `completed_at`：（1）API 领域适用时每个请求响应能力主文件存在配套 `_参数与报文.md` 且索引含对外/对内双分区；（2）配置全量/指定时每个服务配置文档的`来源文件键数`等于`文档收录键数`；（3）Pages 适用且含路由/菜单级条目时每条点名路由存在 `PAGE-*`+`ROUTE-*` 实体与单页面文档且页面文档 API 引用非零链接；（4）接口主文件 11 节、参数报文 5 节、配置文档 10 节、页面文档含第 3/4 节的节序符合性。

#### Scenario: 旧产物在新验收下判 failed

- **WHEN** 对缺失配套参数报文、配置键数不等、无 PAGE 实体、对内分区缺失、接口主文件非 11 节的 KnowledgeBase 执行新版 global-validation
- **THEN** 验收判 `failed`
- **AND** 报告逐条列出上述缺失项

### Requirement: 技能修复必须通过回溯验收与可判定性验证

本变更完成后 MUST 执行三重验证：用新版 global-validation 清单对已知缺陷产物（`/tmp/knowledge-base-3`）执行回溯验收，`failed` 报告 MUST 命中全部五类已知缺口；新增完成条件逐条可机械判定；api 与 pages 两侧候选清单契约逐字段一致。

#### Scenario: 回溯验收漏报已知缺口

- **WHEN** 回溯验收报告未命中任一已知缺口
- **THEN** 验收清单判定为仍不完整
- **AND** 修订清单后重新执行回溯验收

<!-- synced from change kb-matrix-contract-and-retrieval-fix -->
### Requirement: 追溯矩阵格式契约

`knowledge-base-base-info` MUST 按 `assets/traceability-matrix-template.md` 的固定六列结构（来源稳定 ID、关系类型、目标稳定 ID、关系证据(文件:行号)、证据状态、详情链接）写入 `evidence/traceability-matrix.md`；证据状态 MUST 只允许 `已确认`、`来源冲突`、`待确认`。`knowledge-base-api` 与 `knowledge-base-pages` 追加矩阵行时 MUST 遵循同一模板格式。

#### Scenario: base-info 按模板建立关系矩阵

- **WHEN** `knowledge-base-base-info` 执行 §8 关系建立
- **THEN** `evidence/traceability-matrix.md` 表头为模板六列，每行关系均带可定位证据（文件:行号）与证据状态

#### Scenario: 下游领域追加矩阵行

- **WHEN** `knowledge-base-api` 或 `knowledge-base-pages` 更新清单触达 `evidence/traceability-matrix.md`
- **THEN** 追加行与既有表头列结构一致，不产生第二种行形状

### Requirement: 关系类型闭合词表

`knowledge-base-base-info` MUST 提供 `assets/relation-types.md` 闭合枚举词表；写入矩阵的关系类型 MUST 取词表枚举值，不命中词表时 MUST 拒绝写入该行并登记待确认项。词表 MUST 含纵向 8 类（`CONTAINS`、`READS`、`WRITES`、`MAPS_TO`、`CONSUMED_BY`、`BINDS`、`DEPENDS_ON`、`IMPLEMENTED_BY`）与横向 3 类（`COMPOSES`、`JOIN_KEY`、`PROVIDES_FIELD`）；横向 3 类 MUST 标注"已启用（2b）"，且 MUST 限定组合层（Overview 通道）为其唯一合法写入方，`knowledge-base-api` 与 `knowledge-base-pages` 的矩阵写入行 MUST 仍限定纵向类型。新增关系类型 MUST 经 `knowledge-base-update` 变更包并同步词表文件。

#### Scenario: 词表外类型被拒绝

- **WHEN** 领域 Skill 尝试写入关系类型不在词表枚举内的矩阵行
- **THEN** 该行不被写入，对应关系进入 `open-questions.md` 待确认

#### Scenario: 横向类型在第一批不可用

- **WHEN** `knowledge-base-api` 或 `knowledge-base-pages`（第一批写入方）尝试写入 `COMPOSES`/`JOIN_KEY`/`PROVIDES_FIELD` 边
- **THEN** 写入被拒绝并登记待确认；横向边只能由组合层（Overview 通道）生成

### Requirement: global-validation 矩阵机械检查

`knowledge-base-bootstrap` 的 global-validation 内容完整性检查 MUST 新增第 5 项：`evidence/traceability-matrix.md` 存在时，表头列数与列名 MUST 等于模板六列，逐行关系类型 MUST 属于词表枚举；任一不符 MUST 判 `failed` 并保持 `status: in_progress` 与空 `completed_at`。

#### Scenario: 矩阵格式不合格阻断验收

- **WHEN** global-validation 发现矩阵表头非六列或存在词表外关系类型
- **THEN** 验收判 `failed`，只报告缺失项，不删除产物

### Requirement: 检索精确种子直取

`knowledge-base-context` 的渐进检索 MUST 支持精确种子直取：种子已含精确稳定 ID、精确文件路径或 Method+Path 时，MUST 直接定位该实体主文件并跳过总入口与领域索引读取，且 MUST 在本层证据摘要中记录"精确种子直取"与种子值；候选无法唯一定位时 MUST 回退完整索引路径。`references/progressive-retrieval-guide.md` 第 2 层与 `knowledge-base-context/SKILL.md` §2 MUST 保持一致，不得再出现"种子精度优先"与"索引优先"的矛盾。

#### Scenario: 精确种子跳过索引层

- **WHEN** 任务种子是精确稳定 ID（如 `API-internal-order-export`）
- **THEN** 知识库语义路径直接读取该实体主文件与一跳关系，不读总入口 README 与领域索引，证据摘要含直取留痕

#### Scenario: 直取失败回退

- **WHEN** 精确种子对应的实体文档缺失或无法唯一定位
- **THEN** 回退"总入口 → 铆域索引 → 稳定 ID"完整路径并记录回退原因

### Requirement: 漂移字段激活与陈旧度暴露

`knowledge-base-base-info` 的表文档模板 §1 元数据中`证据基线`与`最后核验时间` MUST 为必填，base-info 完成条件 MUST 校验两字段非空。`knowledge-base-overview` MUST 在 README 覆盖范围处暴露知识库 Git 基线与各领域最后核验时间（取该领域文档元数据最大核验时间）。本变更 MUST NOT 引入自动失效或自动更新机制；`knowledge-base-update` 变更包仍是唯一刷新入口。

#### Scenario: 表文档缺漂移字段不得完成阶段

- **WHEN** 范围内任一逻辑表文档的`证据基线`或`最后核验时间`为空
- **THEN** base-info 完成条件不满足，阶段不得标记完成

#### Scenario: 陈旧度对 Agent 可见

- **WHEN** Coding Agent 读取知识库 README
- **THEN** 可见知识库 Git 基线与各领域最后核验时间，无需逐文档翻查元数据

<!-- synced from change kb-deleted-entity-tombstone -->
### Requirement: 删除实体的墓碑表示

`knowledge-base-update` 删除实体时 MUST 采用墓碑保留制：实体的稳定 ID MUST 保持原样（MUST NOT 附加"（已删除）"等任何注记）；追溯矩阵中涉及该实体的历史行 MUST 原位保留，`关系类型` 不变，`证据状态` MUST 写 `已失效`，`关系证据` 列 MAY 追加删除提交；`evidence/relation-graph.yaml` MUST 保留该实体的墓碑节点（id/kind/label/doc 不变，`status: deleted`）及其全部失效边。证据状态枚举 MUST 扩为 `已确认 / 来源冲突 / 待确认 / 已失效`，其中 `已失效` 仅允许由 Update 删除流程产生，初始化阶段 MUST NOT 使用。等值校验口径不变：图边数等于矩阵全部数据行数（含已失效行）、图节点集包含矩阵两端（含墓碑节点）。

#### Scenario: 删除输入 API 后矩阵与图保持一致

- **WHEN** Update 删除 API-account-query（CAP 的输入 API）
- **THEN** 矩阵保留其历史行且 ID 无注记、证据状态为 `已失效`；图保留其墓碑节点与失效边；等值校验通过

#### Scenario: 初始化不得使用已失效

- **WHEN** 任一初始化领域 Skill 写入矩阵
- **THEN** 证据状态只允许 `已确认 / 来源冲突 / 待确认`，出现 `已失效` 判违规

#### Scenario: ID 注记被拒绝

- **WHEN** 更新后的矩阵行 ID 含"（已删除）"等注记
- **THEN** 违反稳定 ID 不可变规则，global-validation 判失败
