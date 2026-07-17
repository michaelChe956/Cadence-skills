---
name: knowledge-base-base-info
description: "Use when Codex 需要为 Java 与 Vue/React 存量项目生成可追溯的基础信息、字段级数据模型、配置快照知识与开发指南。"
---

# KnowledgeBase 基础信息

## 概述

在 Manifest 4.0 授权范围内，从工程、结构证据、配置快照和用户资料建立基础事实模型。代码、数据模型和配置是同级的一级证据。固定生成基础信息、开发指南、字段级数据模型文档、配置总索引和范围内每个服务的配置文档。

## 必读资源

- 执行分析前读取 `references/java-bs-analysis-guide.md`。
- 基础信息使用 `assets/base-information-template.md`。
- 开发指南使用 `assets/development-guide-template.md`。
- 数据模型依次使用 `assets/data-model-index-template.md`、`assets/schema-data-model-template.md` 和 `assets/table-data-model-template.md`。
- 配置知识依次使用 `assets/configuration-index-template.md` 和 `assets/service-configuration-template.md`。
- 需要查看证据降级与冲突示例时读取 `references/demo.md`。

## 前置输入

1. 读取 `cadence/knowledge-base/manifest.yaml`，只接受 `schema_version: "4.0"`。Manifest 缺失或版本不是 4.0 时停止，并引导重新执行 `knowledge-base-bootstrap`；不读取、兼容或迁移其他版本。
2. 以 `scope.projects` 和 `scope.data_models` 作为工程与数据模型的唯一授权范围，不重新解释原始输入或扩大扫描范围。
3. 从 `evidence.data_model_sources` 读取 DDL、迁移、Entity、Mapper、SQL 和人工资料清单。
4. 以 `scope.configurations` 作为配置领域的唯一授权范围，从 `evidence.configuration_snapshots.baseline` 读取最终快照指纹和来源元数据；不得重新解释输入、扩大服务或文件范围。配置为 `全量` 或 `指定` 时，`evidence.configuration_snapshots.baseline.fingerprint` 缺失或为空必须停止，且不得读取配置内容。

## 强制规则

- 分析前读取项目规则；重要叙述事实继续区分代码、DDL、配置、用户资料、合理推断和来源冲突，字段清单则只使用本节规定的证据状态。
- `cadence/knowledge-base/data-models/` 始终保留并生成 `README.md`。数据模型为 `不适用` 时，在总索引记录状态和原因，不扫描逻辑表。
- `cadence/knowledge-base/configurations/` 始终保留并生成 `README.md`。配置为 `不适用` 时，在总索引记录状态和原因，不读取配置快照；配置为 `全量` 或 `指定` 时，为配置范围内每个服务固定生成一个配置文档，即使未发现配置键也记录缺失与待确认项。
- 数据模型为 `全量` 或 `指定` 时，每张纳入范围的逻辑表必须有一个字段级文档；每个数据库或 Schema 必须有一个索引。
- 一张逻辑表只对应一个文档。物理分片仅记录命名、路由和范围规则，不为每个物理分片重复生成业务表文档。
- 禁止用单个 `data-model-overview.md` 或 `base-information.md` 摘要代替 `data-models/README.md`、Schema 索引和字段级逻辑表文档。
- 合并 DDL、迁移、Entity、Mapper、SQL、配置和用户资料；来源冲突不得擅自裁决。
- 原始配置快照是外部不可变证据，只读且不得复制进 KnowledgeBase。不得写入、重命名、删除、格式化快照文件，也不得跟随符号链接、挂载点或外部引用越过授权目录。
- 读取配置内容前按 Manifest 4.0 输入契约首次计算最终快照指纹，并与非空的 `evidence.configuration_snapshots.baseline.fingerprint` 比较；不一致时立即停止，不得读取配置内容。
- 配置分析结束时再次计算最终快照指纹。写入任何配置结论前必须满足 `首次计算指纹 == 分析结束指纹 == evidence.configuration_snapshots.baseline.fingerprint`；任一比较不一致或目录内容变化时立即停止，不得写入配置结论。
- 没有 DDL 时仍生成字段级文档，但不得把代码映射当成实际数据库结构，不得推断实际索引、默认值、主外键、唯一约束或可空性。
- 字段清单的证据状态只允许 `DDL 已确认`、`迁移已确认`、`代码可推导`、`用户提供`、`来源冲突`、`待确认`。
- 同名字段不能单独证明外键或表关系；只有显式约束、明确 ORM 映射、SQL 连接语义或用户资料可以作为关系证据，并保留来源。
- 为数据库、Schema、逻辑表、服务、API、页面和配置组生成稳定 ID，并用稳定 ID 建立关系。
- Properties、YAML、运行时 XML、Nginx 配置和缓存文件属于配置证据；Mapper XML 归入数据模型；日志配置归入可观测性。
- 部署、发布和启动脚本只作为配置来源、加载顺序与部署方式的只读证据，禁止执行，不能把脚本内容当作已生效配置。
- 相同内容的配置文件合并分析并记录全部适用服务、环境、Profile 和来源位置。同名但内容或适用范围不同的文件不得合并。
- 内容哈希只允许在当前运行中临时用于识别相同内容文件，不得写入 KnowledgeBase。Manifest 的 `evidence.configuration_snapshots` 只保存 Manifest 4.0 输入契约定义的最终快照指纹。
- 默认排除 `.idea`、`.gitkeep`、空文件和明确历史备份；无法判断是否为历史文件时标记 `待确认`，不得直接纳入当前基线。
- 密码、Token、AccessKey、Secret、密钥、私钥、完整连接串、内部域名、IP 和 URL 等敏感配置只记录键、用途和值类型，实际值统一写为 `<redacted>`。不确定是否敏感时按敏感信息处理，不得保存敏感值哈希或其他可关联的确定性衍生物。
- 测试、Mock、示例和生成代码必须单独标记，不能作为生产结构的唯一确认依据。
- 不得连接任何数据库、查询数据库结构或访问在线元数据；数据库事实只能来自 Manifest 授权的只读 DDL、迁移、代码、配置和人工资料。
- 不运行应用、数据库迁移、部署脚本、生产脚本或远程配置读取。

## 工作流程

### 1. 建立范围与工程基线

- 确认仓库、服务、模块、前后端入口和生成代码目录。
- 记录 Manifest 基线、Git 提交、纳入范围、排除范围和未覆盖对象。
- 为仓库、服务和模块生成稳定 ID，例如 `REPO-commerce`、`SERVICE-order-service` 和 `MODULE-order-core`。

### 2. 分析技术栈与工程方式

- 从构建文件、锁文件、插件、配置和实际调用确认 Java、前端、数据访问、迁移、测试与构建工具。
- 无法确认的版本写 `unknown` 或待确认，不选择近似版本。
- 只记录有项目资料支持的构建、启动和验证命令。

### 3. 生成字段级数据模型

1. 按 `scope.data_models` 识别数据库、Schema 和逻辑表，以 `evidence.data_model_sources` 为结构证据清单。
2. 按分析指南合并 DDL、迁移、Entity、Mapper、SQL、配置和用户资料，逐字段记录已知属性、代码映射、证据状态和证据位置。
3. 为每张逻辑表生成稳定 ID，例如 `TABLE-order`，并只生成一个逻辑表文档。
4. 生成 `data-models/README.md`、每数据库或 Schema 的 `README.md`、每张逻辑表的字段级文档。
5. 将所有数据模型文档登记到 Manifest 的 `documents.data_models`，将冲突和未覆盖范围写入 `open-questions.md`。

### 4. 生成配置快照知识

1. 按 `scope.configurations` 识别当前基线、环境、发布批次、服务范围和文件规则，并从 `evidence.configuration_snapshots.baseline` 读取来源元数据与授权指纹。配置为 `全量` 或 `指定` 时，先确认 `fingerprint` 存在且非空；缺失或为空时停止。
2. 在读取配置内容前首次计算最终快照指纹，并与 `evidence.configuration_snapshots.baseline.fingerprint` 比较。只有两者相等时，才在授权的外部不可变快照中分类和读取配置文件；不复制快照或访问远程配置源。
3. 按分析指南区分配置证据、Mapper XML、日志配置、脚本证据和默认排除项。相同内容文件仅在当前运行中用临时哈希去重，合并后保留全部适用服务、环境、Profile 与来源。
4. 逐服务记录配置来源与加载顺序、Profile、配置键、代码绑定、生效条件、数据源、分片、中间件和外部系统关系；来源冲突不得擅自裁决。
5. 所有敏感值和敏感内部地址统一写为 `<redacted>`，不保留敏感值哈希。配置键状态只允许 `存在`、`新增`、`删除`、`修改`、`缺失`、`来源冲突`、`待确认`。
6. 分析结束后再次计算最终快照指纹。只有满足 `首次计算指纹 == 分析结束指纹 == evidence.configuration_snapshots.baseline.fingerprint` 时，才生成 `configurations/README.md` 和范围内每个服务的配置文档，并登记到 Manifest 的 `documents.configurations`。

代码、数据模型与配置分别生成自己的一级文档；Mapper XML 转交数据模型文档，配置文档只保留它与逻辑表、数据源或分片规则的关系，不复制字段清单。

### 5. 分析中间件与横切机制

- 在授权范围内记录中间件用途、配置组和装配状态。
- 梳理认证、事务、缓存、幂等、重试、异常、审计和可观测性，并关联配置与实现位置。
- 依赖声明只能证明可能使用，必须结合配置、装配和调用证据判断实际使用。

### 6. 生成开发指南

- 从构建文件、脚本、CI 和项目文档整理环境、构建顺序、启动依赖、测试、静态检查和迁移入口。
- 只记录能从项目资料确认的命令，不为缺失脚本创造虚假命令，也不执行生产或迁移脚本。

### 7. 建立关系与证据

至少建立：

- 服务 → 模块
- 模块 → 逻辑表
- 逻辑表 → Entity、Mapper 与 SQL
- 逻辑表 → 读服务与写服务
- 逻辑表 → API 与页面
- 配置组 → 数据源或分片规则
- 横切机制 → 配置与实现位置

详细来源写入 `cadence/knowledge-base/evidence/source-index.md`，关系写入 `cadence/knowledge-base/evidence/traceability-matrix.md`。

### 8. 输出

生成或更新：

- `cadence/knowledge-base/base-information.md`
- `cadence/knowledge-base/development-guide.md`
- `cadence/knowledge-base/data-models/README.md`
- `cadence/knowledge-base/data-models/<数据库或 Schema 稳定 ID>/README.md`
- `cadence/knowledge-base/data-models/<数据库或 Schema 稳定 ID>/<逻辑表稳定 ID>.md`
- `cadence/knowledge-base/configurations/README.md`
- `cadence/knowledge-base/configurations/<服务稳定 ID>.md`
- `cadence/knowledge-base/evidence/source-index.md`
- `cadence/knowledge-base/evidence/traceability-matrix.md`
- `cadence/knowledge-base/manifest.yaml`
- `cadence/knowledge-base/open-questions.md`

`base-information.md` 的数据模型和配置章节只保存摘要与导航，不复制每张逻辑表的完整字段清单或每个服务的配置键清单。

## 异常与停止规则

- 配置为 `全量` 或 `指定` 时，`evidence.configuration_snapshots.baseline.fingerprint` 缺失或为空，必须在读取配置内容前停止。
- 首次计算指纹与 Manifest 授权指纹不一致，必须在读取配置内容前停止。
- 分析结束指纹与首次计算指纹或 Manifest 授权指纹任一不一致，必须在写入配置结论前停止；不得生成或更新配置总索引、服务配置文档、Base Info 配置摘要、开发指南配置基线或 `documents.configurations`。
- 不得用重新计算的指纹覆盖 Manifest 授权指纹来绕过校验。停止时只报告缺失项或不一致项及影响，不输出部分配置结论。

## 降级与完成条件

- 缺少 DDL 时，依据 Entity、Mapper、SQL、迁移和人工资料生成文档；字段未知属性写 `待确认`，并明确完整性限制。
- 缺少中间件或生产配置时，只记录可定位候选和已知环境，不把依赖或开发配置升级为生产事实。
- 数据模型总索引、所有适用的 Schema 索引和每张逻辑表文档均已生成，链接可达。
- 配置总索引和范围内每个服务的配置文档均已生成，链接可达；配置为 `不适用` 时总索引已记录原因。
- 配置为 `全量` 或 `指定` 时，`evidence.configuration_snapshots.baseline.fingerprint` 存在且非空，并满足 `首次计算指纹 == 分析结束指纹 == evidence.configuration_snapshots.baseline.fingerprint`。Manifest 只保存授权的最终快照指纹和来源元数据；KnowledgeBase 未保存重复文件哈希、敏感值哈希或原始快照副本。
- 每张逻辑表都有字段清单、证据状态、证据位置、读写服务以及已发现的 Mapper/SQL 映射。
- 实际索引、默认值和数据库约束只有在证据支持时记录；来源冲突和未覆盖对象已进入待确认项。
- API、页面、服务、配置和逻辑表通过稳定 ID 关联；分片物理表没有被重复建模。
- 开发指南中的命令均有来源，配置变更验证方式不执行部署、发布或启动脚本，全部输出未包含明文敏感值和敏感内部地址。
