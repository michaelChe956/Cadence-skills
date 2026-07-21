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

