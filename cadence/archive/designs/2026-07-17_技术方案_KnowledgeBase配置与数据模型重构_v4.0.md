# KnowledgeBase 配置与数据模型重构技术方案

## 文档元数据

- 文档类型：技术方案
- 版本：v4.0
- 日期：2026-07-17
- 状态：已确认，待实施计划
- 适用范围：`cadence-init/skills/knowledge-base-*`
- 目标 Schema：KnowledgeBase Schema 4.0

## 1. 背景

当前 KnowledgeBase 设计存在两个核心问题：

1. 配置虽然会被 `knowledge-base-base-info` 扫描，但没有作为与代码、数据模型同级的显式输入进入 Bootstrap 输入契约和 Manifest，无法稳定表达配置环境、发布批次、服务范围和快照差异。
2. `data-models/` 缺少固定的字段级产物契约，生成结果容易退化为表名或关系摘要。Coding Agent 日常查询字段、索引、映射和影响面时仍需回到 DDL，无法把 KnowledgeBase 作为可检索的数据模型快照使用。

实际配置样本是按发布批次生成的测试环境配置快照，包含大量 Properties、YAML、XML、Nginx、Mapper、部署脚本和重复文件，同时含有密码、连接串、AccessKey 等敏感配置。因此不能把整个配置包复制进 KnowledgeBase，也不能把它当成普通源码目录无差别扫描。

本方案不考虑任何既有 KnowledgeBase、旧 Manifest 或旧 Schema 的兼容与迁移。所有相关 Skills 按全新的 Schema 4.0 重新设计。

## 2. 目标

### 2.1 核心目标

1. 将配置提升为与工程代码、数据模型同级的一级输入和一级证据。
2. 将 DDL 调整为可选的数据模型结构证据，不再要求用户持续同步完整 DDL。
3. 固定生成可日常检索的字段级数据模型文档。
4. 使用不可变配置发布快照建立配置基线，并支持新旧快照差异更新。
5. 强制 `knowledge-base-update` 消费用户显式提供的完整变更包，不允许仅凭 Git Diff 猜测更新范围。
6. 扩展 `knowledge-base-context`，使其围绕任务渐进检索代码、数据模型、DDL/迁移和配置快照证据。
7. 保证所有结论可定位、可追溯、可区分事实、推断、冲突和待确认项。

### 2.2 非目标

- 不连接数据库、配置中心、中间件或远程环境。
- 不执行数据库迁移、发布脚本或部署操作。
- 不保存密码、Token、AccessKey、私钥、完整连接串或敏感内部地址。
- 不把原始源码、完整 DDL 或完整配置快照复制进 KnowledgeBase。
- 不兼容、不迁移 Schema 3.0 或其他旧版知识库。
- 不在本次设计中拆分新的 `knowledge-base-configuration` 或 `knowledge-base-data-models` Skill。

## 3. 设计原则

1. **显式输入优先**：范围、环境、快照和变更目的必须由用户显式声明。
2. **多源合并**：数据模型由 DDL、迁移、Entity、Mapper、SQL、配置和用户资料共同构建。
3. **快照而非副本**：配置包作为外部不可变快照引用，KnowledgeBase 只保存脱敏后的结构化知识。
4. **强制变更包**：Update 必须先通过变更包校验，代码和目录扫描只能验证输入，不能替代输入。
5. **渐进检索**：Context 必须检查数据模型和配置关系，但只深入任务所需的最小充分范围。
6. **逻辑实体优先**：数据模型以逻辑表为核心，不为每个物理分片重复生成表文档。
7. **冲突不静默**：用户文档、代码、DDL/迁移和配置快照不一致时保留各方证据。
8. **敏感值最小化**：只记录配置键、用途、类型、状态、绑定位置和必要的非敏感语义。
9. **幂等可审计**：相同变更包重复执行不得产生重复内容，所有更新必须关联变更包标识。

## 4. Schema 4.0 目录

```text
cadence/knowledge-base/
├── user-input/
│   ├── base-info.md
│   ├── project-scope.md
│   ├── data-model-scope.md
│   ├── database-ddl.sql
│   ├── configuration-scope.md
│   ├── middleware-scope.md
│   ├── api-scope.md
│   ├── page-scope.md
│   └── updates/
│       └── CHANGE-变更标识/
│           ├── change-summary.md
│           ├── code-change.md
│           ├── database-change.md
│           ├── configuration-change.md
│           ├── verification.md
│           └── attachments/
├── input-inventory.md
├── manifest.yaml
├── README.md
├── base-information.md
├── development-guide.md
├── interfaces/
├── pages/
├── services/
├── data-models/
├── configurations/
├── evidence/
│   ├── source-index.md
│   └── traceability-matrix.md
├── domain-glossary.md
├── open-questions.md
└── change-history.md
```

约束：

- `database-ddl.sql` 是可选证据文件，不是 Bootstrap 强制输入。
- `data-models/` 和 `configurations/` 是固定领域目录，不再按项目大小决定是否生成。
- `updates/` 中每个目录代表一次独立、不可变的用户变更输入。
- 原始配置快照保留在用户指定的外部目录，不复制进 `cadence/knowledge-base/`。

## 5. Bootstrap 输入契约

### 5.1 唯一入口

`cadence/knowledge-base/user-input/base-info.md` 仍是 Bootstrap 的唯一入口，但必须声明六个一级领域：

1. 工程信息。
2. 数据模型。
3. 配置。
4. 中间件。
5. 接口。
6. 页面。

每个领域只允许以下状态：

| 状态 | 行为 |
|------|------|
| 全量 | 在工程和输入范围内分析该领域的全部对象 |
| 指定 | 只分析引用文件明确列出的对象 |
| 不适用 | 跳过该领域，并要求填写原因 |

状态为全量或指定时，引用文件必须存在。指定范围不得为空。不适用必须有明确原因。

### 5.2 工程输入

`project-scope.md` 登记：

- 工程稳定标识。
- 本地路径。
- 仓库和分支。
- 工程类型。
- 纳入状态。
- 服务、前端应用、公共依赖、配置工程等角色。

### 5.3 数据模型输入

`data-model-scope.md` 是数据模型的强制范围文件，必须登记：

- 数据库类型。
- 数据库或实例逻辑标识。
- Schema。
- 业务域或服务范围。
- 分库分表说明。
- 可用证据类型及路径。
- DDL 是否提供及其环境、导出时间。
- 迁移文件、Entity、Mapper、SQL 和人工资料的来源。
- 明确排除的 Schema 或表。

数据模型状态不是不适用时，至少必须存在一种可定位的结构证据。DDL 可以缺失，但不能在完全没有 DDL、迁移、Entity、Mapper、SQL 或人工结构资料时声称生成了数据模型。

### 5.4 配置输入

`configuration-scope.md` 是配置领域的强制范围文件，按不可变发布快照登记：

- 快照标识。
- 环境。
- 发布批次。
- 外部目录。
- 生成或获取时间。
- 快照指纹和文件清单摘要。
- 纳入服务。
- 包含规则。
- 排除规则。
- 配置中心、ConfigMap、文件包或其他来源类型。
- 敏感信息说明。
- 当前基线快照。

同一快照标识不得指向两个不同目录或两个不同环境。外部目录必须在执行时可读。

### 5.5 其他领域输入

- `middleware-scope.md`：中间件及已知使用范围。
- `api-scope.md`：全部对外能力和本次执行范围。
- `page-scope.md`：前端应用、页面、路由、菜单和权限范围。

## 6. Manifest 4.0 契约

Manifest 是解析后范围、证据基线和增量状态的唯一机器可读来源。

```yaml
schema_version: "4.0"
generator:
  skill: knowledge-base-bootstrap
  version: "4.0"
generated_at: ""
git:
  repositories: []
input:
  root: cadence/knowledge-base/user-input
  base_info: cadence/knowledge-base/user-input/base-info.md
  inventory: cadence/knowledge-base/input-inventory.md
scope:
  projects: {}
  data_models: {}
  configurations: {}
  middleware: {}
  api: {}
  pages: {}
evidence:
  code: {}
  data_model_sources: {}
  configuration_snapshots: {}
update:
  last_change_package: {}
  processed_packages: []
documents:
  core: []
  interfaces: []
  pages: []
  services: []
  data_models: []
  configurations: []
coverage: {}
open_questions:
  blocking: 0
  high: 0
  medium: 0
  low: 0
```

要求：

- Bootstrap、Base Info、Overview、Update 和 Context 只接受 `schema_version: "4.0"`。
- 非 4.0 时立即停止并引导使用新版 Bootstrap。
- 不实现旧 Manifest 字段映射、目录迁移或自动升级。
- `configuration_snapshots` 必须记录当前基线快照的环境、发布批次、外部路径、快照指纹和范围摘要。
- `processed_packages` 必须足以识别同一变更包是否已经处理。

## 7. 字段级数据模型

### 7.1 固定输出

```text
data-models/
├── README.md
└── 数据库_Schema/
    ├── README.md
    ├── TABLE-稳定标识_逻辑表名.md
    └── ...
```

### 7.2 总索引

`data-models/README.md` 必须包含：

- 数据库与 Schema 导航。
- 业务域、服务和数据源映射。
- 逻辑表清单。
- 表关系导航。
- 分库分表摘要。
- 模型覆盖率。
- 证据新鲜度。
- 来源冲突摘要。

每个数据库或 Schema 的 `README.md` 必须包含该范围内的表索引、主要关系、读写服务和未覆盖对象。

### 7.3 逻辑表文档

每张逻辑表必须拥有独立文档，至少包含：

1. 稳定 ID、表名、Schema、业务含义和状态。
2. 字段名、类型、可空、默认值、主键、字段含义。
3. 索引、唯一约束、外键和其他约束。
4. 逻辑表、物理表、分片键和物理表规则。
5. Entity、Mapper、JPA/MyBatis 映射和 SQL 使用位置。
6. 读取服务、写入服务、关联 API 和页面。
7. 租户、软删除、审计、版本号等特殊字段。
8. 每项事实的证据来源、可信度和冲突状态。
9. 最近一次相关变更包和更新时间。

字段证据状态固定为：

- `DDL 已确认`
- `迁移已确认`
- `代码可推导`
- `用户提供`
- `来源冲突`
- `待确认`

没有显式外键时，不得仅凭字段同名断言表关系。

### 7.4 多源合并顺序

数据模型分析必须同时考虑：

1. DDL 和迁移文件。
2. Entity、Mapper、JPA/MyBatis 映射和 SQL。
3. 配置快照中的数据源、Schema、路由和分片规则。
4. 用户提供的数据模型资料。

顺序仅代表优先定位方式，不代表高优先级来源可以静默覆盖低优先级来源。来源不一致时保留双方并登记冲突。

### 7.5 DDL 缺失

DDL 缺失时仍允许生成字段级模型，但必须：

- 标明未获得数据库实际结构快照。
- 对字段逐项标记代码可推导或待确认。
- 不根据 Entity 单独断言实际默认值、索引、触发器或数据库约束。
- 在 Overview 和待确认项中记录模型完整性限制。

## 8. 配置知识库

### 8.1 固定输出

```text
configurations/
├── README.md
└── SERVICE-服务标识_配置.md
```

`base-information.md` 负责配置体系摘要，`configurations/` 负责可检索明细。

### 8.2 基础信息配置摘要

`base-information.md` 的配置章节必须包含：

- 配置来源、环境和当前基线快照。
- 配置中心、配置文件、环境变量及覆盖顺序。
- Profile 与服务映射。
- 数据源、缓存、消息、任务、网关和外部系统等配置组。
- 敏感配置策略。
- 高风险来源冲突。
- 配置领域索引链接。

### 8.3 服务配置文档

每个服务配置文档必须记录：

- 配置键。
- 用途和值类型。
- 环境和来源文件。
- 代码绑定类、`@Value`、条件装配或调用位置。
- 配置组及影响能力。
- 敏感级别。
- 当前状态。
- 最近相关配置变更包。

配置状态固定为：

- `存在`
- `新增`
- `删除`
- `修改`
- `缺失`
- `来源冲突`
- `待确认`

### 8.4 配置包分类

对发布配置快照中的文件按以下规则分类：

| 类型 | 处理方式 |
|------|----------|
| Properties、YAML、运行时 XML、Nginx、缓存配置 | 配置证据 |
| Mapper XML | 数据模型和数据访问证据 |
| 部署脚本 | 部署与配置加载链路证据 |
| 日志配置 | 可观测性配置证据 |
| `.idea`、`.gitkeep`、空文件 | 默认排除 |
| 明确的历史备份文件 | 默认排除，除非范围文件显式纳入 |
| 内容完全相同的文件 | 合并分析并记录适用服务 |

### 8.5 敏感信息

密码、Token、AccessKey、Secret、私钥、完整连接串、内部地址和其他敏感值不得写入 KnowledgeBase。

允许记录：

- 配置键。
- 用途。
- 值类型。
- 是否存在。
- 是否发生变化。
- 绑定位置。
- 脱敏后的系统类型或目标类别。

敏感值统一展示为 `<redacted>`。不得为了差异跟踪保存可被离线枚举的敏感值哈希。

## 9. 强制变更包

### 9.1 入口

每次执行 `knowledge-base-update` 必须显式指定：

```text
cadence/knowledge-base/user-input/updates/CHANGE-变更标识/
```

不得自动选择某个目录，不得在未指定变更包时仅根据 Git Diff 执行更新。

目标项目缺少变更包或必填文档时，必须同时返回：

- 目标项目应补齐的 `cadence/knowledge-base/user-input/updates/CHANGE-变更标识/` 路径。
- 插件内的 `cadence-init/skills/knowledge-base-update/user-input/change-package/` 模板路径。
- 缺失文件、缺失字段及其对更新范围的影响。

### 9.2 必填文件

每个变更包必须包含五份文档。

#### change-summary.md

必须记录：

- 变更标识。
- 变更目的。
- 目标环境。
- 涉及服务。
- 业务影响。
- 风险。
- API、页面、中间件、数据模型和配置的领域变更矩阵。

#### code-change.md

代码有变更时必须记录：

- Merge Request 地址或编号。
- 源分支和目标分支。
- 起止提交。
- 修改工程、文件和符号范围。
- 代码变更说明。

没有代码变更时必须明确声明无变更并填写判断依据。

#### database-change.md

必须记录：

- 是否存在数据库变更。
- DDL 或迁移文件路径。
- 涉及数据库、Schema、逻辑表、字段、索引和约束。
- 预期上线状态。
- 兼容和回滚说明。

没有数据库变更时必须明确声明无变更并填写判断依据。

#### configuration-change.md

必须记录：

- 是否存在配置变更。
- 基线快照和目标快照。
- 环境和发布批次。
- 快照外部目录。
- 快照指纹和纳入文件范围。
- 涉及服务和配置组。
- 已知新增、删除、修改和迁移项。

没有配置变更时仍必须提供快照信息和判断依据。

#### verification.md

必须记录：

- 已执行测试。
- 发布或环境验证。
- 数据兼容验证。
- 配置生效验证。
- 回滚方式。
- 尚未验证的项目及风险。

### 9.3 校验规则

以下任一条件成立时停止更新：

- 未指定变更包路径。
- 任一必填文档不存在。
- 必填字段为空。
- 无变更声明没有判断依据。
- 代码有变更但缺少 MR 和本地可验证提交范围。
- 配置基线和目标快照环境不一致。
- 配置快照目录不可访问。
- 数据库变更对象无法映射到数据模型范围。
- 变更范围超出 Manifest 授权工程或领域。

Git Diff、代码扫描、迁移文件读取和配置快照比较只用于验证变更包。扫描结果不得替代用户输入。

## 10. knowledge-base-update 流程

```text
指定变更包
→ 校验五份必填文档
→ 校验 Manifest 4.0 和当前分支
→ 验证 MR 与本地提交范围
→ 验证数据库变更资料
→ 对比配置基线与目标快照
→ 建立变更实体和稳定 ID 映射
→ 更新受影响文档
→ 更新证据、历史和 Manifest
```

### 10.1 数据模型更新

- 不要求完整 DDL。
- 根据 `database-change.md`、迁移文件、Entity、Mapper、SQL 和配置变化更新受影响逻辑表。
- 代码字段变化但数据库文档声明无变更时，只更新代码映射并登记来源冲突。
- 数据源、Schema、路由或分片配置变化时，更新对应数据模型关系。

### 10.2 配置更新

- 使用 `configuration-change.md` 中的基线和目标快照。
- 按相对路径和配置键识别新增、删除、修改和移动。
- 内容相同的重复文件合并比较。
- 结合代码 MR 验证配置绑定和条件装配。
- 用户声明无配置变更但快照存在差异时登记来源冲突。

### 10.3 幂等

变更包通过以下信息识别：

- 变更标识。
- 五份必填文档的内容状态。
- 代码提交范围。
- 配置快照标识。

相同变更包重复执行不得重复追加历史、重复生成文档或重复更新相同实体。

## 11. knowledge-base-context 渐进检索

### 11.1 四类证据路径

```text
知识库语义
README → 领域索引 → 稳定 ID → 关系矩阵

当前代码
任务对象 → 文件/符号 → 调用链 → 测试

数据模型
TABLE 稳定 ID → 字段级模型 → Mapper/SQL/Entity → DDL/迁移证据

配置
服务/配置组 → 配置键 → 当前快照文件 → 绑定代码 → 生效条件
```

四类路径都必须参与相关性检查，但不得无差别全量读取。

### 11.2 检索步骤

1. 从任务提取业务词、页面、API、服务、逻辑表、字段、配置键、环境和错误信息。
2. 从 KnowledgeBase 索引定位稳定 ID 和直接关系。
3. 检查直接关联的数据表和配置组。
4. 存在关联时读取字段级表文档和服务配置文档。
5. 定位当前 Mapper、SQL、Entity、迁移、DDL、配置快照文件和绑定代码。
6. 画像必需信息不足时再扩展下一跳。
7. 达到任务最小充分上下文后停止。

### 11.3 Manifest 输入

Context 必须从 Manifest 读取：

- 工程和领域范围。
- 数据模型来源状态。
- 当前配置基线快照及环境。
- 配置快照外部目录。
- 最近处理的变更包。
- KnowledgeBase Git 基线和当前代码提交。

任务显式点名某个变更包时，Context 还必须读取该变更包并判断是否已经处理。

### 11.4 任务画像要求

| 画像 | 数据模型与配置检查 |
|------|--------------------|
| 需求澄清 | 现有数据能力、字段约束、环境开关 |
| Design | 表结构、字段约束、数据源、Profile、Feature Flag |
| Plan | Mapper/SQL、字段映射、配置键、绑定类、目标环境 |
| Coding | 修改入口、数据库映射、配置生效链路、相关测试 |
| Testing | Fixture、数据库约束、测试配置、环境差异 |
| Review | MR、数据库变更、配置变更和变更包一致性 |
| Debug | 当前配置快照、生效条件、数据源路由、SQL 和字段状态 |

页面任务仍需沿 PAGE → API → SERVICE/MODULE 关系检查直接关联的数据表和配置。

### 11.5 证据矩阵

Context 输出中的关键结论使用以下结构：

| 结论 | KnowledgeBase | 当前代码 | DDL/数据模型证据 | 配置快照证据 | 状态 | 任务影响 |
|------|---------------|----------|------------------|--------------|------|----------|

状态固定为：

- `一致`
- `KnowledgeBase 缺失`
- `代码缺失`
- `数据模型证据缺失`
- `配置证据缺失`
- `基线漂移`
- `来源冲突`
- `待确认`

## 12. Overview 与导航

`knowledge-base-overview` 必须把数据模型和配置作为一级导航：

- 项目入口链接到 `data-models/README.md`。
- 项目入口链接到 `configurations/README.md`。
- 核心流程可包含 PAGE → API → SERVICE/MODULE → TABLE → CONFIGURATION/MIDDLEWARE。
- 常见修改场景必须说明应读取的表文档、配置文档和最近变更包。
- 不在根文档重复粘贴全部字段或配置键。

## 13. 证据与冲突规则

### 13.1 证据标签

重要结论使用：

- `[代码事实]`
- `[DDL事实]`
- `[迁移事实]`
- `[配置快照事实]`
- `[用户提供]`
- `[合理推断]`
- `[来源冲突]`

### 13.2 冲突处理

| 场景 | 处理方式 |
|------|----------|
| DDL 与 Entity 不一致 | 分别记录数据库结构和代码映射，不覆盖 |
| 数据库文档声明无变更但代码映射变化 | 更新代码映射，数据库结构标记冲突 |
| 配置文档声明无变更但快照有差异 | 记录实际差异和来源冲突 |
| MR 范围与本地提交不一致 | 阻断代码更新 |
| 配置快照环境不一致 | 阻断快照比较 |
| KnowledgeBase 基线落后于已处理变更包 | 标记基线漂移并要求更新 |

## 14. 异常处理

| 异常 | 处理 |
|------|------|
| Manifest 缺失或非 4.0 | 停止并引导新版 Bootstrap |
| `configuration-scope.md` 缺失 | Bootstrap 停止并返回模板路径 |
| DDL 缺失但存在其他结构证据 | 继续并标明完整性限制 |
| 数据模型没有任何结构证据 | 停止或要求声明不适用 |
| 配置快照路径失效 | 配置分析停止 |
| Context 任务依赖实际配置但快照不可访问 | 返回阻断 |
| Context 没有 DDL | 使用字段级模型、迁移和代码证据继续 |
| 敏感值可能进入输出 | 停止输出并要求脱敏 |
| 指定范围为空或越权 | 停止并报告范围问题 |

## 15. Skill 职责调整

### 15.1 knowledge-base-bootstrap

- 校验六个一级领域。
- 解析数据模型多源范围和配置快照范围。
- 生成 Manifest 4.0。
- 初始化固定的 `data-models/` 和 `configurations/` 目录。

### 15.2 knowledge-base-base-info

- 生成项目、技术栈、服务、数据、配置、中间件和开发方式基础事实。
- 固定生成字段级数据模型和服务配置文档。
- 维护相应证据索引和关系矩阵。

### 15.3 knowledge-base-update

- 强制消费指定变更包。
- 验证 MR、数据库变更和配置快照差异。
- 只更新受影响实体和文档。

### 15.4 knowledge-base-context

- 使用四类证据路径渐进检索。
- 每次检查数据模型和配置关系。
- 不修改 KnowledgeBase 或用户输入。

### 15.5 knowledge-base-overview

- 提供数据模型和配置一级导航。
- 在核心流程和常见修改场景中纳入 TABLE 与 CONFIGURATION。

### 15.6 knowledge-base-api 与 knowledge-base-pages

- 继续消费 Manifest 范围。
- API 和页面文档关联字段级表文档及配置实体。
- 不自行扩大数据模型或配置范围。

## 16. 模板与参考资源

实施时需要新增或调整：

- `data-model-scope.md` 输入模板。
- `configuration-scope.md` 输入模板。
- `cadence-init/skills/knowledge-base-update/user-input/change-package/` 下的五份强制变更包模板。
- Manifest 4.0 模板。
- 输入解析清单模板。
- 数据模型总索引模板。
- Schema 索引模板。
- 逻辑表文档模板。
- 配置总索引模板。
- 服务配置文档模板。
- Base Info 配置摘要模板。
- Update、Context、Overview 的 Demo 和参考指南。
- KnowledgeBase 使用说明。

## 17. 验收场景

1. 无 DDL，但可从 Entity、Mapper 和 SQL 生成字段级模型。
2. DDL 与代码字段不一致，双方证据均保留。
3. 使用按发布批次生成的测试环境配置包建立配置基线。
4. 配置快照包含大量重复文件，结果不重复生成。
5. 配置快照包含密码和 AccessKey，KnowledgeBase 不出现明文值。
6. Update 未指定变更包时必须停止。
7. Update 缺少任一必填文档时必须停止。
8. 五份文档齐全，部分领域明确无变更且有依据时允许更新。
9. 用户声明无配置变更但快照存在差异时生成来源冲突。
10. 代码字段变化但数据库文档声明无变更时不伪造数据库变更。
11. Context 从 API 渐进追踪到服务、表字段、配置键和当前快照来源。
12. Context 在配置目录失效且任务依赖实际配置时返回阻断。
13. Overview 能导航到字段级数据模型和服务配置文档。
14. Mapper XML 被识别为数据访问证据而不是普通配置文件。
15. 重复执行相同变更包不会重复写入历史。
16. 非 Schema 4.0 的 Manifest 被所有相关 Skills 拒绝。

## 18. 完成标准

- Bootstrap 输入契约包含六个一级领域。
- 配置和数据模型在 Manifest 中拥有独立范围与证据状态。
- DDL 是可选证据而不是持续维护要求。
- 每个逻辑表具有字段级文档。
- 每个纳入范围的服务具有配置明细或明确无配置结论。
- Update 只能通过完整变更包启动。
- Context 能渐进定位字段、DDL/迁移、配置键、快照文件和绑定代码。
- Overview 能导航到数据模型和配置领域。
- 敏感值不会进入知识库。
- 相同变更包重复执行保持幂等。
- 不包含任何旧 Schema 兼容或迁移逻辑。

## 19. 已确认决策

1. 采用整体输入契约与领域产物升级，不拆分新的领域 Skill。
2. DDL 为可选初始化和校验证据。
3. 数据模型固定生成总索引和每逻辑表字段级文档。
4. 配置使用外部不可变发布快照，不复制原始配置包。
5. 新配置快照通过与上一快照比较完成增量更新。
6. Update 必须显式指定包含五份必填文档的变更包。
7. 无变更是有效状态，但必须显式声明并提供判断依据。
8. Context 必须渐进检查数据模型和配置关系。
9. 完全按 Schema 4.0 重新开发，不兼容任何现有 KnowledgeBase。
