# knowledge-base-context Skill

## 概述

`knowledge-base-context` 是现有 Schema 4.0 KnowledgeBase 的任务消费入口。用户进行需求澄清、Design、Plan、Coding、Testing、Review 或 Debug 时，它沿知识库语义、当前代码、数据模型和配置四条证据路径生成最小任务上下文，再将控制权交回当前 Agent。

该 Skill 不负责初始化或更新 KnowledgeBase，也不代替下游开发工作。

## 使用前提

目标项目必须存在：

```text
cadence/knowledge-base/manifest.yaml
```

且其中包含：

```yaml
schema_version: "4.0"
```

Manifest 还必须提供工程范围、数据模型来源、配置快照授权、最近变更包和 Git 基线。缺失、版本不符或授权不足时停止，不回退为全仓扫描。

## Schema 4.0 输入目录

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

更新包位于目标项目的 `cadence/knowledge-base/user-input/updates/CHANGE-*/`。Context 只读取与任务直接相关的最近处理包或用户明确点名的未处理包，不自动扫描全部更新包，也不处理变更包。

## 如何使用

### 自然语言自动触发

目标项目已有 Schema 4.0 KnowledgeBase 且项目规则已接入时，可直接提出任务，例如：

```text
设计库存预占方案，需要结合表结构、数据源和 Feature Flag。
```

```text
定位订单导出在测试环境超时的问题，已知订单表和超时配置键。
```

调用方应先获取任务上下文，再继续用户原始任务。

### Claude Code 手动调用（/knowledge-base-context）

```text
/knowledge-base-context 定位订单导出在测试环境超时的问题
```

### Codex/pi/Kimi Code 手动调用（裸 skill 名）

使用裸 Skill 名并附带任务描述：

```text
knowledge-base-context 定位订单导出在测试环境超时的问题
```

上述消费路径是目标项目的 `cadence/knowledge-base/` 产物目录；仓库源定义位于 `cadence-init/skills/knowledge-base-context/`，两者不是同一目录。

## 七类固定任务画像

每次选择一个主画像，最多附加两个辅助画像：

| 画像 | 重点 |
| --- | --- |
| 需求澄清 | 数据能力、字段约束、环境开关和系统边界 |
| Design | 表结构、数据源、Profile、Feature Flag、架构和风险 |
| Plan | Mapper/SQL、字段映射、配置键、目标环境、验证入口 |
| Coding | 数据库映射、配置生效链路、调用链、边界和测试 |
| Testing | Fixture、数据库约束、测试配置、Profile 和环境差异 |
| Review | MR、数据库变化、配置变化、完整变更包和验证记录 |
| Debug | 配置快照、生效条件、数据源路由、SQL、字段状态和变更包 |

画像是固定集合，不支持动态注册。

## Schema 4.0 Manifest

Manifest 是知识库目录卡、授权范围、证据基线和增量状态文件，不是数据库 Schema。Context 必读：

- `scope.projects`：工程和仓库范围。
- `scope.data_models`：数据库、逻辑表和排除范围。
- `scope.configurations`：环境、服务和配置文件授权。
- `evidence.data_model_sources`：DDL、迁移、Entity、Mapper、SQL 和人工资料状态。
- `evidence.configuration_snapshots.baseline`：快照、环境、目录、指纹和审计范围。
- `update.last_change_package`、`update.processed_packages`：变更包状态。
- `git.repositories`：仓库、分支和 Git 基线。

Manifest 不授权扫描范围外工程、数据模型、配置目录或变更包。

## 四类渐进检索

```text
知识库语义：README → 领域索引 → 稳定 ID → 关系矩阵
当前代码：任务对象 → 文件/符号 → 调用链 → 测试
数据模型：TABLE → 字段级模型 → Mapper/SQL/Entity → DDL/迁移
配置：服务/配置组 → 配置键 → 当前快照文件 → 绑定代码 → 生效条件
```

每次检查：

```text
PAGE → API → SERVICE/MODULE → TABLE / 数据源 / 配置组 / 配置键
```

有直接关系才继续读取相关证据；无直接关系则记录后停止对应方向，不扫描全部表或配置包。

## 数据模型证据

字段级文档位于目标项目 `cadence/knowledge-base/data-models/`，可关联字段、索引、约束、分片、Mapper、SQL、Entity、读写服务和来源状态。没有 DDL 不会自动阻断；无法确认的类型、默认值、可空性、索引或外键标记为“数据模型证据缺失”或“待确认”，不会从代码补造。

## 配置快照证据

服务配置文档位于目标项目 `cadence/knowledge-base/configurations/`，实际配置来自 Manifest 授权的外部不可变快照。使用前验证范围、指纹、摘要、目录可读性、快照映射和目标配置键来源。配置证据失效时，依赖实际配置的任务状态为“阻断”，不连接远程配置中心补取。敏感值统一写为 `<redacted>`。

## 变更包与 Git 基线

Context 检查 `last_change_package`、`processed_packages` 和 Git 基线，只展开与任务直接相关的内容。用户点名未处理包时读取其五份文档并标记“基线漂移”，不修改 Manifest。Review 必须核对 MR、数据库文档、配置文档、完整变更包和验证记录；Debug 必须检查配置生效条件、数据源路由、SQL、字段状态和相关变更包。

## 证据与冲突

证据矩阵固定记录 KnowledgeBase、当前代码、DDL/数据模型证据、配置快照证据、状态和任务影响。状态包括“一致”“KnowledgeBase 缺失”“代码缺失”“数据模型证据缺失”“配置证据缺失”“基线漂移”“来源冲突”“待确认”。冲突改变任务方向时，保留各侧证据并询问用户。

## 输出内容

任务上下文包包含任务识别、任务理解、核心实体、四类证据矩阵、关系与影响面、数据模型上下文、配置上下文、相关变更包、画像专属上下文、约束与现有模式、冲突与缺口、下游使用建议和就绪状态。

| 状态 | 含义 |
| --- | --- |
| `就绪` | 关键上下文完整且无影响方向的未决冲突 |
| `有条件就绪` | 存在非阻断缺口，可在假设下继续 |
| `阻断` | 范围或实体无效、关键冲突改变方向，或实际配置不可验证 |

## 持久化规则

默认只在当前会话返回上下文，不创建文件。用户明确要求复用、交接或审计时，才保存到目标项目：

```text
cadence/knowledge-base/task-contexts/
YYYY-MM-DD_任务上下文_任务名称_v1.0.md
```

任务快照不是新事实知识库，不加入 Manifest，也不自动更新领域文档。

## 完整使用流程

```text
1. 填写 Schema 4.0 六领域输入和配置快照授权
2. 执行 knowledge-base-bootstrap
3. 生成 Manifest、数据模型和服务配置文档
4. 由 knowledge-base-overview 接入项目规则
5. 提出需求、设计、计划、编码、测试、评审或调试任务
6. 执行 knowledge-base-context 获取最小上下文
7. 当前 Agent 继续原始任务
8. 事实变化后用完整变更包执行 knowledge-base-update
```

## 常见问题

### Q：没有 Manifest 可以直接扫描源码吗？

不可以。Manifest 缺失或不是 4.0 时停止，不回退为无范围全仓扫描。

### Q：每次都会扫描所有表和配置吗？

不会。只有确认任务存在直接关系后，才读取相关证据。

### Q：配置目录不可用怎么办？

依赖实际配置时立即阻断，不从远程配置中心补取；无直接关系时记录后停止配置方向。

### Q：会输出密码或内部地址吗？

不会。敏感配置只返回键、用途、状态和绑定位置，值写为 `<redacted>`。

### Q：Context 只返回上下文，不继续开发吗？

不会。完成上下文阶段后，调用方继续用户原始任务，除非用户明确只要求加载、整理或保存上下文。

## 相关 Skills

- `knowledge-base-bootstrap`：校验输入并初始化 Schema 4.0 KnowledgeBase。
- `knowledge-base-base-info`：生成基础信息、数据模型和服务配置文档。
- `knowledge-base-api`：分析 API 与集成能力。
- `knowledge-base-pages`：分析页面及其关系。
- `knowledge-base-overview`：生成知识库入口和项目规则。
- `knowledge-base-update`：使用完整变更包增量更新知识库。

## 技术细节

- [Skill 定义](../../cadence-init/skills/knowledge-base-context/SKILL.md)
- [渐进读取指南](../../cadence-init/skills/knowledge-base-context/references/progressive-retrieval-guide.md)
- [任务画像](../../cadence-init/skills/knowledge-base-context/references/task-profiles.md)
- [完整案例](../../cadence-init/skills/knowledge-base-context/references/demo.md)
