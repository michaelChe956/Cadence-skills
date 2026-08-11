# knowledge-base-context Skill

## 概述

`knowledge-base-context` 是现有 Schema 4.0 KnowledgeBase 的任务消费入口。

当用户进行需求澄清、Design、Plan、Coding、Testing、Review 或 Debug 时，它先从当前任务出发，分别读取知识库语义、当前代码、数据模型和配置快照，生成最小任务上下文包，再将控制权交回当前 Agent 继续用户原始任务。

该 Skill 不负责初始化或更新 KnowledgeBase。

## 使用前提

目标项目必须存在：

```text
cadence/knowledge-base/manifest.yaml
```

并且 Manifest 包含：

```yaml
schema_version: "4.0"
```

Skill 还会读取 Manifest 中的工程范围、数据模型来源、配置授权快照、最近处理变更包和 Git 基线。Manifest 缺失、版本不是 4.0 或缺少任务所需授权时，Skill 会停止，不回退为全仓分析。

## Schema 4.0 输入目录

用户输入根目录为：

```text
cadence/knowledge-base/user-input/
├── base-info.md
├── project-scope.md
├── data-model-scope.md
├── database-ddl.sql
├── configuration-scope.md
├── middleware-scope.md
├── api-scope.md
└── page-scope.md
```

`base-info.md` 是唯一入口。六个领域分别声明 `全量`、`指定` 或 `不适用`；数据模型可使用 DDL、迁移、Entity、Mapper、SQL 或人工资料，配置则使用外部不可变快照及其授权指纹。

增量更新包位于：

```text
cadence/knowledge-base/user-input/updates/CHANGE-*/
├── change-summary.md
├── code-change.md
├── database-change.md
├── configuration-change.md
└── verification.md
```

Context 只按任务关系读取最近处理包，或读取用户明确点名的未处理包；不会自动扫描全部更新包，也不会登记或处理变更包。

## 如何使用

### 自然语言自动触发

项目已建立 Schema 4.0 KnowledgeBase，且项目规则已由 `knowledge-base-overview` 接入后，可直接提出任务：

```text
帮我澄清订单取消需求的数据能力、字段限制和环境开关。
```

```text
设计库存预占方案，需要结合表结构、数据源和 Feature Flag。
```

```text
评审当前 MR、数据库文档、配置文档和变更包是否一致。
```

```text
定位订单导出在测试环境超时的问题，已知订单表和超时配置键。
```

Agent 应先使用 `knowledge-base-context` 获取任务上下文，再继续原始工作。

### Claude Code 手动调用

```text
/cadence-init:knowledge-base-context 定位订单导出在测试环境超时的问题
```

### Codex 手动调用

```text
$knowledge-base-context 定位订单导出在测试环境超时的问题
```

`agents/openai.yaml` 只提供 Codex 展示名称和默认提示，不负责安装或触发注册。

## 七类固定任务画像

每次任务选择一个主画像，最多附加两个辅助画像。

| 画像 | Schema 4.0 上下文重点 |
|------|-----------------------|
| 需求澄清 | 已有数据能力、字段约束、环境开关和系统边界 |
| Design | 表结构、数据源、Profile、Feature Flag、架构和风险 |
| Plan | Mapper/SQL、字段映射、配置键、目标环境、步骤和验证入口 |
| Coding | 数据库映射、配置生效链路、调用链、边界条件和相关测试 |
| Testing | Fixture、数据库约束、测试配置、Profile 和环境差异 |
| Review | MR、数据库变化、配置变化、完整变更包和验证记录一致性 |
| Debug | 配置快照、生效条件、数据源路由、SQL、字段状态和最近变更包 |

组合任务示例：

- 实现接口并补测试：`Coding + Testing`
- 评审设计是否可实施：`Review + Design`
- 排查问题并准备修复计划：`Debug + Plan`

画像是固定集合，不支持用户新增或动态注册画像。

## Schema 4.0 Manifest

Manifest 是 KnowledgeBase 的目录卡、授权范围、证据基线和增量状态文件，不是数据库 Schema。

Context 必读区域：

| 区域 | 用途 |
|------|------|
| `scope.projects` | 工程和仓库范围 |
| `scope.data_models` | 数据库、Schema、逻辑表和排除范围 |
| `scope.configurations` | 环境、服务和配置文件授权范围 |
| `evidence.data_model_sources` | DDL、迁移、Entity、Mapper、SQL 和人工资料状态 |
| `evidence.configuration_snapshots.baseline` | 当前配置快照、外部目录、环境、发布批次、授权指纹和可审计范围摘要 |
| `update.last_change_package` | 最近处理变更包 |
| `update.processed_packages` | 已进入 KnowledgeBase 基线的变更包 |
| `git.repositories` | 仓库、分支和 Git 基线 |

Manifest 不负责自然语言自动触发，也不授权 Agent 扫描范围外工程、数据模型、配置目录或变更包。

## 四类渐进检索

四条路径独立、同等重要：

```text
知识库语义：README → 领域索引 → 稳定 ID → 关系矩阵
当前代码：任务对象 → 文件/符号 → 调用链 → 测试
数据模型：TABLE → 字段级模型 → Mapper/SQL/Entity → DDL/迁移
配置：服务/配置组 → 配置键 → 当前快照文件 → 绑定代码 → 生效条件
```

每次任务都检查表和配置关系：

```text
PAGE → API → SERVICE/MODULE → TABLE / 数据源 / 配置组 / 配置键
```

- 有直接关系：只读取相关表、字段、SQL、配置组、配置键和快照文件。
- 无直接表关系：记录后停止数据模型方向，不扫描全部表。
- 无直接配置关系：记录后停止配置方向，不扫描全部配置包或快照目录。

页面任务必须先沿 `PAGE → API → SERVICE/MODULE`，再检查表和配置关系。

## 数据模型证据

字段级表文档位于 `cadence/knowledge-base/data-models/`，可关联字段、索引、约束、分片、Mapper、SQL、Entity、读写服务和来源状态。

DDL 缺失不会自动阻断。Skill 会继续使用字段级文档、迁移、Mapper、SQL 和 Entity；无法确认的真实类型、默认值、可空性、索引或外键标记为 `数据模型证据缺失` 或 `待确认`，不会从代码补造。

## 配置快照证据

服务配置文档位于 `cadence/knowledge-base/configurations/`，当前实际配置来自 Manifest 授权的外部不可变快照。

任务依赖实际配置时，Skill 会先验证：

- 配置范围包含目标环境、服务和文件。
- `evidence.configuration_snapshots.baseline.fingerprint` 存在并符合授权基线。
- `scope_summary`、纳入文件数量或清单摘要、服务摘要和文件规则摘要完整且与授权一致。
- 同一快照标识没有映射到不同环境或不同外部目录。
- 外部目录存在、可读、只读使用且没有越界或变化。
- 目标配置键可定位到来源文件、绑定代码和生效条件。

配置为 `不适用` 时记录原因并停止配置方向，不要求基线或外部目录。配置目录失效、授权指纹失配、范围摘要冲突、快照标识映射冲突或快照变化时，如果任务依赖实际配置，任务上下文状态为 `阻断`。Skill 不会连接远程配置中心补取。

配置键存在不等于已生效。必须结合环境、Profile、覆盖顺序、条件装配、绑定代码和实际调用判断。敏感配置只返回键、用途、状态和绑定位置，值写为 `<redacted>`。

## 变更包与 Git 基线

Skill 每次读取 `last_change_package`、`processed_packages` 和 Git 基线，但只展开与任务直接相关的包和 Git 差异。

- 最近处理包与任务无关：记录“无直接关系”后停止，不扫描全部包。
- 任务相关文件在基线后变化：标记 `基线漂移`。
- 用户点名未处理变更包：读取该包五份文档并标记 `基线漂移`，说明尚未纳入 KnowledgeBase；不修改 Manifest。
- Review：必须核对 MR、数据库文档、配置文档、完整变更包和验证记录。
- Debug：必须同时检查配置生效条件、数据源路由、SQL、字段状态和相关变更包。

## 证据与冲突

证据矩阵固定为：

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

当前代码描述当前行为，KnowledgeBase 保留业务语义，数据模型来源约束结构事实，授权配置快照描述目标环境的配置状态。冲突会改变任务方向时，Skill 保留各侧证据并询问用户。

## 输出内容

任务上下文包固定包含：

1. 任务识别
2. 任务理解
3. 核心实体
4. 四类证据矩阵
5. 关系与影响面
6. 数据模型上下文
7. 配置上下文
8. 相关变更包
9. 画像专属上下文
10. 约束与现有模式
11. 冲突、缺口与待确认项
12. 下游使用建议
13. 就绪状态

| 就绪状态 | 含义 |
|----------|------|
| `就绪` | 关键上下文完整，没有影响方向的未决冲突 |
| `有条件就绪` | 存在非阻断缺口，可以在明确假设下继续 |
| `阻断` | 范围或实体无效、关键冲突改变方向，或任务依赖的实际配置不可验证 |

## 持久化规则

默认只在当前会话使用任务上下文，不创建文件。

只有用户明确要求复用、交接或审计时，才保存到：

```text
cadence/knowledge-base/task-contexts/
YYYY-MM-DD_任务上下文_任务名称_v1.0.md
```

任务快照不是新的事实知识库，不自动加入 Manifest，也不自动更新领域文档。

## 完整使用流程

```text
1. 用户填写 Schema 4.0 的六领域输入和配置快照授权
2. 执行 knowledge-base-bootstrap
3. Bootstrap 生成 Manifest 4.0、字段级数据模型和服务配置文档
4. knowledge-base-overview 接入项目使用规则
5. 用户提出需求、设计、计划、编码、测试、评审或调试任务
6. knowledge-base-context 沿四类证据路径获取最小上下文
7. 当前 Agent 继续用户原始任务
8. 项目事实变化后，用户显式指定完整变更包执行 knowledge-base-update
```

## 常见问题

### Q: 没有 Manifest 可以直接扫描源码吗

不可以。Manifest 缺失或版本不是 4.0 时，Skill 会停止并引导执行 `knowledge-base-bootstrap`，不会回退为无范围的全仓扫描。

### Q: 每次都会扫描所有表和配置吗

不会。每次都会检查任务与表、配置的直接关系，但无直接关系时会记录后停止对应方向。只有确认直接关系后，才读取相关逻辑表、字段、服务配置和目标快照文件。

### Q: 没有 DDL 是否会阻断

不会自动阻断。只要字段级文档、迁移、Mapper、SQL、Entity 或人工资料提供了有效结构证据，就会继续；不能确认的数据库属性标记为 `数据模型证据缺失` 或 `待确认`。

### Q: 配置目录不可用时怎么办

如果任务依赖目标环境的实际配置，则立即阻断，不从远程配置中心补取。如果任务与配置无直接关系，则记录后停止配置方向，不读取外部目录。

### Q: 会输出密码、Token 或内部地址吗

不会。敏感配置只返回配置键、用途、状态和绑定位置，值统一写为 `<redacted>`。

### Q: 用户点名尚未处理的变更包怎么办

Skill 会读取该包五份强制文档，标记 `基线漂移`，并说明它尚未纳入 `processed_packages`；不会替用户处理变更包或修改 Manifest。

### Q: Review 和 Debug 有什么额外检查

Review 必须对照 MR、数据库文档、配置文档、完整变更包和验证记录。Debug 必须检查目标环境配置快照、生效条件、数据源路由、SQL、字段状态和相关变更包。

### Q: 自动触发后会不会只返回上下文，不继续开发

不会。该 Skill 是前置上下文阶段。完成后调用方必须继续原始任务，除非用户明确只要求加载、整理或保存上下文。

## 相关 Skills

- `knowledge-base-bootstrap`：校验六领域输入并初始化 Schema 4.0 KnowledgeBase。
- `knowledge-base-base-info`：生成基础信息、字段级数据模型和服务配置文档。
- `knowledge-base-api`：分析对外能力和工程内对内能力。
- `knowledge-base-pages`：分析页面、路由、权限和 REST API 关联。
- `knowledge-base-overview`：生成知识库入口、关系导航和项目使用规则。
- `knowledge-base-update`：使用用户显式指定的完整变更包幂等更新 Schema 4.0 KnowledgeBase。

## 技术细节

- [Skill 定义](../../cadence-init/skills/knowledge-base-context/SKILL.md)
- [渐进读取指南](../../cadence-init/skills/knowledge-base-context/references/progressive-retrieval-guide.md)
- [任务画像](../../cadence-init/skills/knowledge-base-context/references/task-profiles.md)
- [完整案例](../../cadence-init/skills/knowledge-base-context/references/demo.md)
