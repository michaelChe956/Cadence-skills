# 方案设计：KnowledgeBase 关系契约与检索修复（第一批）

- 日期：2026-09-20
- 版本：v1.0
- 状态：待评审
- 关联：四 Agent 架构讨论（oracle/max-task/glm53-task/ds-task）+ 三路业内调研（R1/R2/R3）结论

## 1. 背景与动机

KnowledgeBase Schema 4.0 体系存在三处已核实的基础缺陷，阻碍后续所有优化（组合能力层、业务知识输入面、派生索引）：

1. `evidence/traceability-matrix.md` 被 base-info/api/pages/overview 四个 Skill 写入、被 context 检索链当作一层读取，但全仓库无任何格式契约——同一关系在不同 Skill 手里可能写成不同形状，检索链最后一跳无法机械核对。
2. 检索指南 `progressive-retrieval-guide.md` 内部矛盾：第 1 层规定"种子精度优先"（精确路径或稳定 ID > Method+Path > 业务术语），第 2 层却强制"从总入口和领域索引定位候选稳定 ID"——精确种子仍被强制两次索引读取，构成每任务固定 token 消耗。
3. `table-data-model-template.md` §1 的"证据基线"与"最后核验时间"字段闲置，无任何 Skill 要求填写或消费；知识库陈旧度不可见。

本批为纯基建修复：定义契约、消除矛盾、激活字段，不引入新实体类型、不改动任何现有不变量。

## 2. 范围

| # | 改动 | 类型 |
|---|------|------|
| 1 | 新增矩阵格式模板 + base-info §8 升级为强制规则 | 新产物 + 规则强化 |
| 2 | 新增关系类型闭合词表（纵向 8 + 横向 3，横向标注第二批启用） | 新产物 |
| 3 | 检索指南精确种子直取分支 + context §2 同步 | 矛盾修复 |
| 4 | 表模板漂移字段必填 + overview 暴露陈旧度摘要 | 字段激活 |

## 3. 非目标

- `CAP-*` 组合能力实体、`JOIN_KEY` 等横向边的**消费**（第二批）
- 派生边表 `index/entities.yaml`、context 漂移出口、业务知识输入面（测试/ADR/git 证据源、product.md、AI 草稿协议、`RULE-*`/`FLOW-*`）（第二批）
- `EVENT`/`JOB` 稳定 ID 命名空间定义（第二批，随消息/任务能力深化一起）
- Schema 版本变更：保持 4.0 兼容增量，无新初始化阶段，无新顶层目录
- 不改动：原子写入、变更包幂等、敏感脱敏、初始化状态不变量门禁

## 4. 详细设计

### 4.1 矩阵格式模板

新文件：`cadence-init/skills/knowledge-base-base-info/assets/traceability-matrix-template.md`

Owner 为 base-info（第一个建立关系矩阵的 Skill），其余 Skill 交叉引用。列结构固定六列：

```text
| 来源稳定 ID | 关系类型 | 目标稳定 ID | 关系证据（文件:行号） | 证据状态 | 详情链接 |
```

- 行形状复用既有惯例（`data-model-index-template.md` 的关系行、表文档 §8 关联行均已是"关系 + 证据 + 状态"三件套）。
- `关系类型` 只允许取关系词表（4.2）枚举值。
- `证据状态` 沿用现有枚举：`已确认 / 来源冲突 / 待确认`。
- `详情链接` 指向承载该关系的领域文档锚点（如接口主文件 §7.1）。
- 矩阵按来源稳定 ID 字典序排列，同源行按关系类型分组；追加新行时保持排序，不重排既有行。

配套规则改动：

- `knowledge-base-base-info/SKILL.md` §8："至少建立"的 8 类关系清单升级为"按 `assets/traceability-matrix-template.md` 格式写入 `evidence/traceability-matrix.md`"，并增加强制规则："关系类型只允许取 `assets/relation-types.md` 词表枚举值，不命中词表即写入失败并登记待确认"。
- `knowledge-base-api/SKILL.md` §7 与 `knowledge-base-pages/SKILL.md` 更新清单中 `evidence/traceability-matrix.md` 处，补一句"按 base-info 矩阵模板格式追加"。
- `knowledge-base-bootstrap/SKILL.md` global-validation 内容完整性检查新增第 5 项：矩阵存在时，表头列数与列名等于模板六列、逐行关系类型取值 ∈ 词表枚举；任一不符判 `failed`。

### 4.2 关系类型词表

新文件：`cadence-init/skills/knowledge-base-base-info/assets/relation-types.md`

闭合枚举，每值给出：类型名、语义、方向、允许的（源类型，目标类型）、证据要求、启用批次。方向原则：与既有领域文档链路方向保持一致——调用/访问链取"消费方 → 提供方"（如 API → SERVICE/MODULE → TABLE）；表文档 §8 的反查关联保持原方向 TABLE → API/PAGE（`CONSUMED_BY`）。

纵向 8 类（本批启用，对应 base-info §8 现有关系）：

| 类型 | 语义 | 源 → 目标 |
|------|------|-----------|
| `CONTAINS` | 服务包含模块 | SERVICE → MODULE |
| `READS` | 读取逻辑表 | SERVICE/MODULE、API → TABLE |
| `WRITES` | 写入逻辑表 | SERVICE/MODULE、API → TABLE |
| `MAPS_TO` | 逻辑表与 Entity/Mapper/SQL 代码符号映射 | TABLE → 代码符号位置 |
| `CONSUMED_BY` | 逻辑表被 API/页面消费（表文档 §8 关联行的矩阵化表达） | TABLE → API/PAGE |
| `BINDS` | 配置组绑定数据源或分片规则 | CONFIGURATION → 数据源/分片规则 |
| `DEPENDS_ON` | 服务/模块依赖中间件 | SERVICE/MODULE → MIDDLEWARE |
| `IMPLEMENTED_BY` | 横切机制落位于配置与实现位置 | 横切机制 → CONFIGURATION/代码位置 |

横向 3 类（本批**定义不启用**，标注"第二批启用"，消费者为 CAP 组合层与字段域反向索引）：

| 类型 | 语义 | 源 → 目标 |
|------|------|-----------|
| `COMPOSES` | 组合能力由既有 API 组成 | CAPABILITY → API |
| `JOIN_KEY` | 两个 API 的输出字段经同一表字段可关联 | API ↔ API |
| `PROVIDES_FIELD` | API 提供某字段域 | API → 字段域 |

词表闭合但可版本化：新增类型必须走 `knowledge-base-update` 变更包，并同步更新本文件枚举。

### 4.3 检索指南矛盾修复

`cadence-init/skills/knowledge-base-context/references/progressive-retrieval-guide.md` 第 2 层步骤 1 前插入分支：

> 种子已含精确稳定 ID、精确文件路径或 Method+Path 时，直接定位该实体主文件读取并进入表/配置关系检查，跳过总入口与领域索引读取；在本层证据摘要中记录"精确种子直取"与种子值。候选无法唯一定位时回退完整索引路径。

`knowledge-base-context/SKILL.md` §2 知识库语义路径行同步加注"（精确种子可直取实体，见检索指南第 2 层）"。

与第 1 层优先级表对齐后，指南内部不再存在"精度优先 vs 索引优先"矛盾。

### 4.4 漂移字段激活

- `cadence-init/skills/knowledge-base-base-info/assets/table-data-model-template.md` §1 元数据：`证据基线`、`最后核验时间` 从可选改为必填（生成或经 Update 触达该表时填写）。
- `knowledge-base-base-info/SKILL.md` 完成条件增加："每张逻辑表文档元数据的证据基线与最后核验时间非空"。
- `knowledge-base-overview/SKILL.md`：README 项目边界（§1）与覆盖范围处暴露"知识库 Git 基线 + 各领域最后核验时间"（各领域取该领域文档元数据中的最大核验时间）。
- `cadence-init/skills/knowledge-base-overview/assets/project-overview-template.md` 增加对应占位行。

不新增自动失效机制：Update 仍是唯一刷新入口，本项只让陈旧度可见。

## 5. 验收标准

1. 两个新 assets 文件存在；词表为闭合枚举且横向 3 类带"第二批启用"标注。
2. base-info §8 含模板落盘与词表枚举强制规则；api/pages 矩阵写入处引用模板；bootstrap global-validation 含矩阵格式机械检查。
3. 检索指南第 1、2 层不再矛盾；context §2 同步。
4. 表模板两字段必填；base-info 完成条件含非空校验；overview 模板与 SKILL.md 含陈旧度暴露。
5. 全部改动不触碰原子写入、幂等、脱敏、初始化状态机；无 Schema 版本 bump、无新阶段。

## 6. 风险与对策

| 风险 | 对策 |
|------|------|
| 词表类型命名与现有文档表述不完全一致（如"逻辑表→读写服务"被拆为 READS/WRITES 有向边） | 评审时逐类确认；语义映射表写入词表文件，保证旧表述可追溯 |
| global-validation 新检查对旧格式矩阵误判 | 本仓库无存量知识库实例；模板随检查项同批发布，初始化即按新格式生成 |
| 精确种子直取减少留痕 | 强制在本层证据摘要记录跳过理由与种子值，维持输出门禁 |

## 7. 后续（第二批预告，不在本批）

业务知识输入面（测试/ADR/git 证据源、product.md、AI 草稿→人核准协议、RULE-*/FLOW-* 实体）、CAP-* 组合能力层、派生边表 `index/entities.yaml`、context 漂移出口、EVENT/JOB ID 定义。
