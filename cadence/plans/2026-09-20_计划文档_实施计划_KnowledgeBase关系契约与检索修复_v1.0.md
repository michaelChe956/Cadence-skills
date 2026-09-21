# KnowledgeBase 关系契约与检索修复 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为 Schema 4.0 KnowledgeBase 落地追溯矩阵格式契约、关系类型闭合词表、检索精确种子直取与漂移字段激活（第一批基建，4 项改动）。

**Architecture:** 纯 Skill/模板文档变更，无代码、无运行时。两个新 assets 归 `knowledge-base-base-info` 所有，api/pages/bootstrap/context/overview 交叉引用；global-validation 新增矩阵机械检查；不触碰原子写入、幂等、脱敏、初始化状态机。

**Tech Stack:** Markdown Skill 文件与 assets 模板；openspec CLI 校验。

**Spec:** `openspec/changes/kb-matrix-contract-and-retrieval-fix/`（proposal/specs/design/tasks）；设计文档 `cadence/designs/2026-09-20_方案设计_KnowledgeBase关系契约与检索修复_v1.0.md`。

## Global Constraints

- 全部产物中文；遵循 markdown-format 规则（嵌套代码块外层 4 反引号、内层 3 反引号）。
- **禁止 `git commit`**：本项目"产物自动提交（design/plan/code）"开关为**关闭**，每个任务结束只汇报改动路径。
- Schema 保持 4.0：无新初始化阶段、无新顶层目录、无 Manifest 顶层域变更。
- 不修改 `.claude/rules/` 框架内置规则；不修改 `cadence/project-rules/`。
- 每个任务完成后用指定检查命令验证（本仓库无测试框架，机械文本检查即验证）。

---

## 问题与解决对照

背景：本计划处理的问题来自四 Agent 架构讨论（oracle 裁决与三项结构性发现）及三路业内调研。本节说明每个提出的问题在本计划中由哪个任务解决，以及明确不在本批解决的问题去向。

### 本计划解决的问题

| 提出的问题 | 本计划如何解决 | 落点 |
|-----------|---------------|------|
| 结构缺陷①：`evidence/traceability-matrix.md` 被 4 个 Skill 写入、被检索链读取，但全仓库零格式契约，同一关系可能写成多种形状，检索链最后一跳无法机械核对 | 六列模板作为唯一格式契约；base-info §8 升级为强制模板落盘；api/pages 写入处引用模板；global-validation 新增矩阵机械检查兜底（表头六列 + 关系类型 ∈ 词表，任一不符判 `failed`） | Task 1（模板）、Task 2（§8 门禁）、Task 3（下游引用）、Task 4（验收检查） |
| 结构缺陷②（部分）：关系类型无闭合词表，横向边（能力组合 `COMPOSES`/`JOIN_KEY`、字段域 `PROVIDES_FIELD`）在全体系无处定义 | 11 类型闭合词表一次定全：纵向 8 类启用并给出与 base-info §8 原表述的映射；横向 3 类定义但标注"第二批启用"、本批禁止写入；词表外类型拒写并登记待确认 | Task 1（词表）、Task 2（枚举门禁）、Task 4（枚举检查） |
| 结构缺陷③：检索指南内部矛盾——第 1 层"种子精度优先" vs 第 2 层"索引优先"，精确种子仍被强制读总入口与领域索引（每任务固定 token 浪费） | 第 2 层新增精确种子直取分支：精确稳定 ID/文件路径/Method+Path 直取实体主文件、跳过两级索引，直取与回退均强制留痕；context §2 同步，矛盾消除 | Task 5 |
| 担忧4（部分）：知识库陈旧度不可见——表模板"证据基线/最后核验时间"字段闲置，无任何 Skill 要求填写或消费 | 表模板两字段改必填并加说明；base-info §4 填写义务 + 完成条件非空校验；overview 在 README 暴露知识库 Git 基线与各领域最后核验时间，Agent 无需逐文档翻查 | Task 2（义务+校验）、Task 6（模板与暴露） |

### 本计划不解决、留给第二批的问题（边界声明）

| 提出的问题 | 为何不在本批 | 第二批落点 |
|-----------|-------------|-----------|
| 担忧1：业务规则/状态流转无一等实体（寄生正文）、流程封顶 3-5 条、错误码无目录 | 属新增实体类型（`RULE-*`/`FLOW-*`）与输入面扩展（测试/ADR/git 证据源、product.md、AI 草稿协议），超出基建范围 | 第二批业务知识输入面 |
| 担忧3（深层）：种子→ID 解析与一跳导航压在多个 README 与单一矩阵上，导航/审计负载未分离 | 精确种子直取只消除固定开销的一部分；单点承载需要派生边表 | 第二批 `index/entities.yaml` |
| 担忧4（深层）：漂移信号不沉淀、不聚合、无提醒 | 本批只做陈旧度可见性（纯产物层）；漂移出口需改 context 行为，按"一次变更动一个 Skill"原则后置 | 第二批（与 CAP/边表同批动 context） |
| 担忧5：横向能力组合无实体无表达（a+b → 全部用户信息类需求） | 本批只定义词表横向类型（定义不启用）；`CAP-*` 实体、接口索引第三分区、用户诉求确认、写入期闭包属能力组合层 | 第二批 CAP 组合层 |
| 结构缺陷②（剩余）：`EVENT`/`JOB` 稳定 ID 无命名空间/生成规则/落盘定义 | 需与消息/任务能力深化一起设计，单独定义无消费方 | 第二批 |

---

### Task 1: 新增矩阵模板与关系词表 assets

**Files:**
- Create: `cadence-init/skills/knowledge-base-base-info/assets/traceability-matrix-template.md`
- Create: `cadence-init/skills/knowledge-base-base-info/assets/relation-types.md`

**Interfaces:**
- Produces: 六列矩阵契约（后续 Task 2/3/4 引用）；11 类型闭合词表（8 纵向启用 + 3 横向"第二批启用"）。

- [x] **Step 1: 写入 traceability-matrix-template.md（完整内容如下）**

```markdown
# 追溯矩阵模板

> Owner：knowledge-base-base-info。本文件是 `evidence/traceability-matrix.md` 的唯一格式契约；knowledge-base-api、knowledge-base-pages、knowledge-base-overview 追加矩阵行时必须遵循同一结构。

## 表头（固定六列）

| 来源稳定 ID | 关系类型 | 目标稳定 ID | 关系证据（文件:行号） | 证据状态 | 详情链接 |
|------------|----------|------------|----------------------|----------|----------|

## 示例行

| 来源稳定 ID | 关系类型 | 目标稳定 ID | 关系证据（文件:行号） | 证据状态 | 详情链接 |
|------------|----------|------------|----------------------|----------|----------|
| SERVICE-order-service | CONTAINS | MODULE-order-core | services/SERVICE-order-service.md#模块与入口 | 已确认 | services/SERVICE-order-service.md |
| API-internal-order-export | READS | TABLE-order | services/order/OrderMapper.java:88 | 已确认 | interfaces/API-internal-order-export.md#7.1 |
| TABLE-user | CONSUMED_BY | API-USER-BASIC-QUERY | data-models/TABLE-user.md#8 | 已确认 | data-models/TABLE-user.md |

## 规则

1. `关系类型` 只允许取 `relation-types.md` 词表枚举值；不命中词表的关系不得写入矩阵，登记 `open-questions.md` 待确认。
2. `证据状态` 只允许 `已确认`、`来源冲突`、`待确认`。
3. `关系证据` 必须可定位（文件:行号）；`详情链接` 指向承载该关系的领域文档锚点。
4. 行按来源稳定 ID 字典序排列，同源行按关系类型分组；追加行保持排序，不重排既有行。
5. 同一（来源, 关系类型, 目标）三元组只保留一行；证据冲突时保留一行，证据状态写 `来源冲突`，证据位置列出全部来源。
```

- [x] **Step 2: 写入 relation-types.md（完整内容如下）**

```markdown
# 关系类型词表

> Owner：knowledge-base-base-info。写入 `evidence/traceability-matrix.md` 的关系类型闭合枚举。新增类型必须经 `knowledge-base-update` 变更包并同步本文件，不得私自扩展。

## 使用规则

- 写入矩阵的关系类型只允许取本词表枚举值；不命中的关系不得写入，登记待确认。
- 方向原则：与既有领域文档链路方向一致——调用/访问链取"消费方 → 提供方"（如 API → SERVICE/MODULE → TABLE）；表文档反查关联保持原方向 TABLE → API/PAGE。

## 纵向类型（第一批启用）

| 类型 | 语义 | 源 → 目标 | 对应 base-info §8 原表述 |
|------|------|-----------|--------------------------|
| `CONTAINS` | 服务包含模块 | SERVICE → MODULE | 服务 → 模块 |
| `READS` | 读取逻辑表 | SERVICE/MODULE、API → TABLE | 模块 → 逻辑表 / 逻辑表 → 读服务 |
| `WRITES` | 写入逻辑表 | SERVICE/MODULE、API → TABLE | 模块 → 逻辑表 / 逻辑表 → 写服务 |
| `MAPS_TO` | 逻辑表与 Entity/Mapper/SQL 映射 | TABLE → 代码符号位置 | 逻辑表 → Entity、Mapper 与 SQL |
| `CONSUMED_BY` | 逻辑表被 API/页面消费 | TABLE → API/PAGE | 逻辑表 → API 与页面 |
| `BINDS` | 配置组绑定数据源或分片规则 | CONFIGURATION → 数据源/分片规则 | 配置组 → 数据源或分片规则 |
| `DEPENDS_ON` | 服务/模块依赖中间件 | SERVICE/MODULE → MIDDLEWARE | SERVICE/MODULE → MIDDLEWARE |
| `IMPLEMENTED_BY` | 横切机制落位于配置与实现位置 | 横切机制 → CONFIGURATION/代码位置 | 横切机制 → 配置与实现位置 |

## 横向类型（第二批启用，本批禁止写入）

| 类型 | 语义 | 源 → 目标 | 启用批次 |
|------|------|-----------|----------|
| `COMPOSES` | 组合能力由既有 API 组成 | CAPABILITY → API | 第二批（能力组合层） |
| `JOIN_KEY` | 两个 API 的输出字段经同一表字段可关联 | API ↔ API | 第二批（能力组合层） |
| `PROVIDES_FIELD` | API 提供某字段域 | API → 字段域 | 第二批（字段域反向索引） |

第一批（变更 kb-matrix-contract-and-retrieval-fix）范围内，初始化与 Update 之外的任何写入不得使用横向类型；横向类型仅作为定义存在。
```

- [x] **Step 3: 验证**

用 grep 检查两个文件：
- `relation-types.md` 含 11 个类型名（`CONTAINS`、`READS`、`WRITES`、`MAPS_TO`、`CONSUMED_BY`、`BINDS`、`DEPENDS_ON`、`IMPLEMENTED_BY`、`COMPOSES`、`JOIN_KEY`、`PROVIDES_FIELD`），且含"第二批启用"。
- `traceability-matrix-template.md` 表头含六列名且规则含"不命中词表"。

- [x] **Step 4: 汇报路径（不提交 git）**

### Task 2: base-info SKILL.md 升级（模板落盘 + 词表门禁 + 漂移字段）

**Files:**
- Modify: `cadence-init/skills/knowledge-base-base-info/SKILL.md`

**Interfaces:**
- Consumes: Task 1 的两个 assets。
- Produces: §8 模板落盘义务 + 词表枚举门禁（Task 3/4 引用）；完成条件两字段非空校验。

- [x] **Step 1: 必读资源节新增两行**

定位 `## 必读资源` 节（现有列表以 "- 需要查看证据降级与冲突示例时读取 `references/demo.md`。" 结尾），在 `references/demo.md` 行之前插入：

```markdown
- 生成或更新关系矩阵前读取 `assets/traceability-matrix-template.md` 与 `assets/relation-types.md`。
```

- [x] **Step 2: §8 关系建立改为模板落盘 + 词表门禁**

定位 `### 8. 建立关系与证据` 节。当前结尾行为：

```markdown
详细来源写入 `cadence/knowledge-base/evidence/source-index.md`，关系写入 `cadence/knowledge-base/evidence/traceability-matrix.md`。
```

替换为：

```markdown
详细来源写入 `cadence/knowledge-base/evidence/source-index.md`，关系写入 `cadence/knowledge-base/evidence/traceability-matrix.md`。

矩阵落盘与词表门禁：

1. 关系行一律按 `assets/traceability-matrix-template.md` 的六列结构写入，证据状态只允许 `已确认`、`来源冲突`、`待确认`。
2. 关系类型只允许取 `assets/relation-types.md` 词表枚举值；不命中词表的关系不得写入矩阵，登记 `open-questions.md` 待确认。
3. 横向类型（`COMPOSES`、`JOIN_KEY`、`PROVIDES_FIELD`）在第二批启用前禁止写入。
```

（上文 8 类关系清单原文保留不动，作为语义类别说明；类型映射见词表文件。）

- [x] **Step 3: §4 数据模型流程补字段填写义务**

定位 `### 4. 生成字段级数据模型` 的步骤 4（"生成 `data-models/README.md`、每数据库或 Schema 的 `README.md`、每张逻辑表的字段级文档。"），在该行后追加一条步骤：

```markdown
5. 生成或更新每张逻辑表文档时，填写元数据 `证据基线`（本次分析的 Git 基线提交）与 `最后核验时间`（本次分析日期）；两字段为必填，为空视为文档不完整。
```

- [x] **Step 4: 完成条件新增两处校验**

定位 `## 降级与完成条件` 节中行 "- 每张逻辑表都有字段清单、证据状态、证据位置、读写服务以及已发现的 Mapper/SQL 映射。"，在其后追加：

```markdown
- 每张逻辑表文档元数据的 `证据基线` 与 `最后核验时间` 非空。
- 关系矩阵按 `assets/traceability-matrix-template.md` 六列结构生成，全部关系类型属于 `assets/relation-types.md` 词表枚举。
```

- [x] **Step 5: 验证**

grep `SKILL.md`：
- `traceability-matrix-template` 出现 ≥2 处（必读资源 + §8）。
- `relation-types` 出现 ≥2 处（必读资源 + §8/完成条件）。
- `最后核验时间` 出现 ≥2 处（§4 + 完成条件）。

- [x] **Step 6: 汇报路径（不提交 git）**

### Task 3: api/pages 矩阵写入引用模板

**Files:**
- Modify: `cadence-init/skills/knowledge-base-api/SKILL.md`（§7 更新清单）
- Modify: `cadence-init/skills/knowledge-base-pages/SKILL.md`（§9 输出清单）

**Interfaces:**
- Consumes: Task 1 模板。

- [x] **Step 1: api SKILL.md 更新清单行加注**

定位 `### 7. 更新关系与进度` 下 "- 更新：" 列表中的行：

```markdown
- `evidence/traceability-matrix.md`
```

替换为：

```markdown
- `evidence/traceability-matrix.md`（按 `knowledge-base-base-info` 的 `assets/traceability-matrix-template.md` 六列格式追加行，关系类型只允许词表枚举值）
```

- [x] **Step 2: pages SKILL.md 输出清单行加注**

定位 `### 9. 输出` 生成或更新列表中的行：

```markdown
- `cadence/knowledge-base/evidence/traceability-matrix.md`
```

替换为：

```markdown
- `cadence/knowledge-base/evidence/traceability-matrix.md`（按 `knowledge-base-base-info` 的 `assets/traceability-matrix-template.md` 六列格式追加行，关系类型只允许词表枚举值）
```

- [x] **Step 3: 验证**

两个 SKILL.md 各 grep 到 1 处 `traceability-matrix-template`，且原文行未被破坏（该清单其余行不变）。

- [x] **Step 4: 汇报路径（不提交 git）**

### Task 4: bootstrap global-validation 第 5 项

**Files:**
- Modify: `cadence-init/skills/knowledge-base-bootstrap/SKILL.md`（global-validation 内容完整性检查）

**Interfaces:**
- Consumes: Task 1 模板与词表。

- [x] **Step 1: 追加检查项 5**

定位 `## 安全与完成条件` 中内容完整性检查列表（现有 4 项，第 4 项为 "模板节结构符合性：……自创节结构判 `failed`。"），在第 4 项后追加：

```markdown
  5. 追溯矩阵符合性：`evidence/traceability-matrix.md` 存在时，表头列数与列名等于 `knowledge-base-base-info` 的 `assets/traceability-matrix-template.md` 六列，逐行关系类型属于 `assets/relation-types.md` 词表枚举；任一不符判 `failed`。
```

- [x] **Step 2: 验证**

grep bootstrap SKILL.md：`追溯矩阵符合性` 出现 1 处；检查列表序号 1–5 连续。

- [x] **Step 3: 汇报路径（不提交 git）**

### Task 5: 检索精确种子直取

**Files:**
- Modify: `cadence-init/skills/knowledge-base-context/references/progressive-retrieval-guide.md`（第 2 层）
- Modify: `cadence-init/skills/knowledge-base-context/SKILL.md`（§2）

**Interfaces:**
- Produces: "精确种子直取"分支术语（供检索指南与 SKILL.md 互相引用）。

- [x] **Step 1: 指南第 2 层插入直取分支并重排序号**

定位 `### 第 2 层：知识库语义路径`。当前步骤 1–3 为：

```markdown
1. 从总入口和相关领域索引定位候选稳定 ID。
2. 只读取候选实体主文件，不批量加载同目录文档。
3. 从关系矩阵取得 PAGE、API、SERVICE/MODULE、TABLE、配置组和变更历史的一跳关系。
```

替换为：

```markdown
1. 种子已含精确稳定 ID、精确文件路径或 Method+Path 时，直接定位该实体主文件读取，跳过总入口与领域索引；在本层证据摘要记录"精确种子直取"与种子值。实体文档缺失或候选无法唯一定位时，回退本层完整路径并记录回退原因。
2. 从总入口和相关领域索引定位候选稳定 ID。
3. 只读取候选实体主文件，不批量加载同目录文档。
4. 从关系矩阵取得 PAGE、API、SERVICE/MODULE、TABLE、配置组和变更历史的一跳关系。
```

- [x] **Step 2: context SKILL.md §2 同步**

定位 `## 工作流程` 下 `### 2. 建立四类渐进证据路径` 的四行路径代码块之后的段落（"知识库语义回答"系统如何定义"；……"），在该段落末尾追加一句：

```markdown
知识库语义路径支持精确种子直取：种子为精确稳定 ID、文件路径或 Method+Path 时直接定位实体主文件并跳过总入口与领域索引，直取与回退均须留痕（见 `references/progressive-retrieval-guide.md` 第 2 层）。
```

- [x] **Step 3: 验证**

- grep 指南：`精确种子直取` 出现 ≥1 处；第 2 层步骤号 1–4 连续。
- grep context SKILL.md：`精确种子直取` 出现 1 处。
- 指南第 1 层优先级行（"精确路径或稳定 ID > Method + Path …"）保持原样——第 2 层新步骤 1 与其一致，矛盾消除。

- [x] **Step 4: 汇报路径（不提交 git）**

### Task 6: 表模板字段必填 + overview 陈旧度暴露

**Files:**
- Modify: `cadence-init/skills/knowledge-base-base-info/assets/table-data-model-template.md`（§1 元数据）
- Modify: `cadence-init/skills/knowledge-base-overview/SKILL.md`（§1 与完成条件）
- Modify: `cadence-init/skills/knowledge-base-overview/assets/project-overview-template.md`（文档元数据）

**Interfaces:**
- Consumes: Task 2 Step 3/4 的字段义务。

- [x] **Step 1: 表模板两字段标注必填并加说明**

定位 §1 元数据表：

```markdown
| 证据基线 |  |
| 最后核验时间 |  |
```

替换为：

```markdown
| 证据基线（必填） |  |
| 最后核验时间（必填） |  |
```

并在 §1 表格后（`## 2. 业务含义` 之前）插入：

```markdown
> `证据基线`（本次分析 Git 基线提交）与 `最后核验时间`（本次分析日期）为必填字段；为空视为文档不完整，阶段不得完成。
```

- [x] **Step 2: overview SKILL.md §1 增加陈旧度暴露要求**

定位 `### 1. 汇总项目边界`，其列表末项为 "- 当前分析分支、基线和覆盖范围：" 之后（该节末尾）追加一行：

```markdown
- 知识库 Git 基线与各领域最后核验时间（各领域取该领域文档元数据中的最大核验时间）。
```

- [x] **Step 2b: overview SKILL.md §7 README 内容列举同步**

定位 `### 7. 生成知识库入口` 中的句子：

```markdown
`README.md` 作为 Coding Agent 首选入口，保持短小，只提供项目摘要、读取顺序、覆盖范围和一级导航，不复制字段清单、全部配置键或领域文档正文。
```

替换为：

```markdown
`README.md` 作为 Coding Agent 首选入口，保持短小，只提供项目摘要、读取顺序、覆盖范围、一级导航和陈旧度摘要（知识库 Git 基线与各领域最后核验时间），不复制字段清单、全部配置键或领域文档正文。
```


- [x] **Step 3: overview 模板元数据增行**

定位 `project-overview-template.md` 文档元数据列表（"- 生成时间：" 至 "- 未覆盖范围："），在 "- 未覆盖范围：" 后追加：

```markdown
- 各领域最后核验时间：{{领域: 日期；取各领域文档元数据最大值}}
```

- [x] **Step 4: overview 完成条件增校验**

定位 `## 完成条件` 首行 "- Coding Agent 能从 README 导航到全部适用的核心文档；……"，在其后追加：

```markdown
- README 暴露知识库 Git 基线与各领域最后核验时间，数据取自各领域文档元数据，不逐文档复制明细。
```

- [x] **Step 5: 验证**

- grep 表模板：`（必填）` 2 处、`为空视为文档不完整` 1 处。
- grep overview SKILL.md：`最后核验时间` ≥2 处（§1 + 完成条件）。
- grep overview 模板：`各领域最后核验时间` 1 处。

- [x] **Step 6: 汇报路径（不提交 git）**

### Task 7: 变更验证

**Files:**
- 无新改动；只读核对。

**Interfaces:**
- Consumes: Task 1–6 全部产出。

- [x] **Step 1: 机械核对（grep 逐项）**

1. 词表 11 类型 + "第二批启用"（Task 1）。
2. base-info：模板/词表引用 ≥2 处、`最后核验时间` ≥2 处（Task 2）。
3. api/pages 各 1 处模板引用（Task 3）。
4. bootstrap：`追溯矩阵符合性` + 序号 1–5（Task 4）。
5. 指南 + context：`精确种子直取`（Task 5）。
6. 表模板 `（必填）`、overview `最后核验时间`（Task 6）。

- [x] **Step 2: 契约核对**

- `openspec validate "kb-matrix-contract-and-retrieval-fix"` 通过。
- 对照设计文档 §5 验收标准 5 条逐条打勾（在验证汇报中列出）。
- 确认无 Schema bump、无初始化状态机字段改动、无 `.claude/rules/` 与 `cadence/project-rules/` 改动（`git status` 目视确认改动仅落在 cadence-init/skills/knowledge-base-*/ 与 openspec/changes/、cadence/designs/、cadence/plans/）。

- [x] **Step 3: 输出验证汇报（不提交 git）**

汇报：全部改动路径清单 + 每条验收标准的核对结果 + openspec validate 输出。
