# KnowledgeBase 组合与索引层（2b）实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 落地 CAP 组合能力层（两通道生成）、evidence/relation-graph.yaml 派生边表与等值校验、context 图消费+漂移分级、update 横向重算+锚点复核；词表横向 3 类解禁。

**Architecture:** 纯 Skill/模板文档变更。capabilities/ 为可选域（空目录合法）；图是矩阵投影非真相源（严格派生+原子重建+等值校验）；横向类型唯一写入方为组合层。

**Tech Stack:** Markdown/YAML；openspec CLI。

**Spec:** `openspec/changes/kb-composition-and-index-layer/`；设计文档 `cadence/designs/2026-09-20_方案设计_KnowledgeBase组合与索引层_v1.0.md`。

## Global Constraints

- 全部产物中文；嵌套代码块外层 4 反引号、内层 3 反引号。
- **禁止 `git commit`**；每任务结束只汇报路径。
- Schema 4.0 不变；阶段枚举/状态机不变；ai-draft/confirmed 协议不动；无组合自动枚举路径。
- 每任务完成用指定 grep 验证；Task 6 总验证；**统一测试（结构化校验脚本）在 Task 6 后执行**（用户指示：都做完再测试）。

---

### Task 1: CAP 域与模板 + 诉求表

**Files:**
- Create: `cadence-init/skills/knowledge-base-overview/assets/capability-composition-template.md`
- Modify: `cadence-init/skills/knowledge-base-bootstrap/user-input/api-scope.md`（诉求表）
- Modify: `cadence-init/skills/knowledge-base-bootstrap/SKILL.md`（输出树+固定产物+global-validation 无关）
- Modify: `cadence-init/skills/knowledge-base-bootstrap/references/input-contract.md`（检测集合+输出契约）
- Modify: `cadence-init/skills/knowledge-base-bootstrap/assets/manifest-template.yaml`（documents.capabilities）

- [x] **Step 1: 新增 capability-composition-template.md（完整内容）**

````markdown
# {{组合能力名称}}

## 1. 元数据

| 项目 | 内容 |
|------|------|
| 组合稳定 ID | CAP-{{业务名}} |
| 状态 | proposed / verified / retired |
| 来源 | 用户诉求（api-scope）/ 已有聚合端点 |
| 声明依据 | {{api-scope 诉求行 / 聚合端点 API ID}} |

> `proposed`=设计已确认未实现；`verified`=有实现证据（implementation_api_ids 非空）；`retired`=已退役。`verified` 不等于对外已暴露——对外属性唯一权威是用户 api-scope 清单。会话推导的组合候选不得生成本实体。

## 2. 目的与非目标

{{组合解决什么业务问题；明确不覆盖什么（"全部用户信息"必须收敛为明确字段清单，不默认涵盖敏感字段）}}

## 3. 输入能力清单

| step | api_id | required | request_mapping | contract_ref |
|------|--------|----------|-----------------|--------------|
| | | | | ../interfaces/…_参数与报文.md#… |

## 4. 编排与字段映射

- pattern：parallel_join / sequential（白名单，二选一）
- join_key：{{字段}}（两侧必须各自逐跳映射到同一 TABLE 字段，见第 7 节证据）
- output_mapping：命名空间合并（如 profile: / accounts:），禁覆盖同名字段
- failure_policy：fail_whole / partial

## 5. 输出契约

| 字段 | 来源 | 允许公开 |
|------|------|----------|

## 6. 约束与鉴权

| 约束 | 结论 | 证据 |
|------|------|------|
| identity_mapping | | |
| tenant_isolation | | |
| external_permission | | |

## 7. 连接键证据（JOIN_KEY 纪律）

| 输入 API | 连接键字段 | 映射链（API 模型→SERVICE/MODULE→Mapper/SQL→TABLE 字段） | 证据锚点 |
|----------|-----------|--------------------------------------------------------|----------|

> 字段同名不构成关联依据；任一跳缺失或待确认 → JOIN_KEY 标待确认，本组合不得 `verified`。

## 8. 实现关联

implementation_api_ids：{{实际聚合端点 API-*；为空=未实现，状态恒 proposed}}

## 9. 证据与待确认
````

- [x] **Step 2: api-scope.md 模板增诉求表**

定位"## 能力类型参考"节之前（"## 对外能力清单"表格之后）插入：

```markdown
## 能力组合诉求（可选）

> 组合能力实体的用户权威输入：声明后由 knowledge-base-api 核实输入契约与连接键证据、knowledge-base-overview 生成 CAP 实体。未声明时不生成组合实体。

| 目标能力名 | 期望输出字段 | 来源能力 ID | 连接键 | 声明依据 |
|-----------|-------------|------------|--------|----------|
```

- [x] **Step 3: bootstrap 三副本 + 输出契约 + manifest**

- SKILL.md 固定输出树 `├── business/` 行后加 `├── capabilities/`。
- SKILL.md 第 2 步固定产物清单 `` `business/` `` 后加 `` `capabilities/` ``。
- input-contract.md 检测集合 `` `business/` `` 后加 `` `capabilities/` ``。
- input-contract.md 输出契约 "- 业务域文档（规则卡、流程文档）登记到 `documents.business`。" 行后加：

```markdown
- `capabilities/` 始终保留并生成 `README.md`；无组合诉求且无聚合端点时以`未提供`说明占位。
- 组合能力文档登记到 `documents.capabilities`。
- `evidence/relation-graph.yaml` 与追溯矩阵在同一次原子写入中重建受影响条目（严格派生，禁止手工编辑）。
```

- manifest-template.yaml `documents:` 域 `business: []` 后加 `  capabilities: []`。

- [x] **Step 4: 验证**

grep：模板含 `CAP-`/`proposed`/`JOIN_KEY 纪律`；api-scope 含诉求表头；bootstrap 两副本+输出树+检测集合含 `capabilities/`；manifest 含 `capabilities: []`。

- [x] **Step 5: 汇报路径（不提交 git）**

### Task 2: overview CAP 生成职责 + api 核实职责 + 词表解禁

**Files:**
- Modify: `cadence-init/skills/knowledge-base-overview/SKILL.md`（5 处）
- Modify: `cadence-init/skills/knowledge-base-api/SKILL.md`（3 处）
- Modify: `cadence-init/skills/knowledge-base-base-info/assets/relation-types.md`（2 处）
- Modify: `cadence-init/skills/knowledge-base-base-info/SKILL.md`（1 处：图首建）
- Modify: `cadence-init/skills/knowledge-base-api/SKILL.md`、`knowledge-base-pages/SKILL.md` 写入行措辞（横向解禁同步）

- [x] **Step 1: overview 必读资源与前置**

必读资源 "- 生成业务规则卡时使用…" 行后加：

```markdown
- 生成组合能力文档时使用 `assets/capability-composition-template.md`。
```

前置输入 "- Manifest `evidence.business_knowledge_sources`…" 行后加：

```markdown
- `user-input/api-scope.md` 的"能力组合诉求"表（可选）与 `interfaces/README.md`"能力组合"分区
```

- [x] **Step 2: 新增 §4.6 生成组合能力层（插在 §4.5 之后、§5 之前）**

```markdown
### 4.6 生成组合能力层（capabilities/）

1. 读取 api-scope"能力组合诉求"表与 api 阶段核实的聚合端点结果；两者皆无时只生成 `capabilities/README.md`（记`未提供`）并跳过以下步骤。
2. 用户诉求通道：诉求行的来源能力 ID 均已由 api 核实存在且契约锚点齐备时，按模板生成 `CAP-*.md`（状态 proposed），登记 `CAP --COMPOSES--> API` 边；JOIN_KEY 证据不完整时边与组合均标待确认。
3. 已有实现通道：api 发现的聚合端点（其主文件已登记实际调用的多个能力）反向建立 CAP，关联 implementation_api_ids，映射链齐备时可 verified。
4. 会话推导的组合候选不生成实体，只进会话输出与待确认清单。
5. 生成 `capabilities/README.md`：CAP 清单（ID、名称、状态、输入 API、明细链接）与 proposed/verified/retired 计数。
6. `interfaces/README.md` 增"能力组合"分区（仅导航字段：ID/名称/状态/明细链接），由本节同批写入。
```

- [x] **Step 3: overview §7 输出、§9 登记、完成条件**

- §7 输出清单 business 两行后加：

```markdown
- `cadence/knowledge-base/capabilities/README.md` 与 `capabilities/CAP-*.md`（有诉求或聚合端点时）
```

- §9 登记列表 "- 业务域文档…" 行后加：

```markdown
- 组合能力文档登记到 `documents.capabilities`
```

- 完成条件 "- business/ 域已生成…" 行后加：

```markdown
- capabilities/ 域已按两通道规则生成：CAP 文档含状态机、输入清单、JOIN_KEY 证据与实现关联；无诉求且无聚合端点时仅有`未提供`README；接口索引"能力组合"分区与 CAP 文档一致。
```

- [x] **Step 4: api 核实职责**

api SKILL.md §3 EVENT/JOB 段（2a 新增段）后追加一段：

```markdown
api-scope 声明"能力组合诉求"时，api 阶段必须核实每个来源能力 ID 的存在性、契约锚点（参数报文文件位置）、鉴权要求，并按 JOIN_KEY 纪律核实连接键字段的端到端映射链（复用本节字段映射证据口径）；核实结果供 overview 生成 CAP 使用，api 不生成组合实体。发现工程内聚合端点（单个 API 实现调用多个既有能力）时，在该端点主文件登记其聚合的能力 ID 清单，供 overview 反向建立 CAP。
```

- [x] **Step 5: 词表横向解禁**

- relation-types.md 横向节标题 "## 横向类型（第二批启用，本批禁止写入）" 改为 "## 横向类型（已启用（2b），唯一写入方为组合层）"。
- 末句 "第一批（变更 kb-matrix-contract-and-retrieval-fix）范围内，任何写入（含初始化与 Update）不得使用横向类型；横向类型仅作为定义存在，待第二批能力组合层启用后开放。" 替换为：

```markdown
自 2b（变更 kb-composition-and-index-layer）起横向类型启用，唯一合法写入方是组合层（knowledge-base-overview 生成 CAP 的通道）；api 与 pages 阶段的矩阵写入仍限纵向类型，写入横向边必须被拒绝并登记待确认。
```

- api/pages 矩阵写入行（"横向类型 `COMPOSES`/`JOIN_KEY`/`PROVIDES_FIELD` 第二批启用前禁止写入"）替换为 "横向类型仅由组合层（knowledge-base-overview 通道）写入，本阶段仍限纵向类型"。两个文件同步。

- [x] **Step 6: base-info 图首建**

base-info SKILL.md §8 "矩阵落盘与词表门禁" 列表第 3 条（横向禁写条，已被 Step 5 语义覆盖）替换为第 4 条新增规则后形成：

```markdown
3. 横向类型（`COMPOSES`、`JOIN_KEY`、`PROVIDES_FIELD`）自 2b 起启用，唯一合法写入方为组合层（knowledge-base-overview）；base-info 仍只写纵向类型。
4. base-info 首次建立矩阵时同步首建 `evidence/relation-graph.yaml`（矩阵的机读投影，严格派生：与矩阵同批写入、禁止手工编辑、每边保留证据位置）；后续领域与 Update 的矩阵写入必须同批重建图的对应条目。
```

- [x] **Step 7: 验证**

grep：overview 含 `capability-composition-template`、`4.6 生成组合能力层`、`documents.capabilities`；api 含 `能力组合诉求`；词表含 `已启用（2b）`/`唯一写入方`；base-info 含 `relation-graph.yaml`；api/pages 写入行含 `仅由组合层`。

- [x] **Step 8: 汇报路径（不提交 git）**

### Task 3: global-validation 第 6 项 + 领域图重建义务

**Files:**
- Modify: `cadence-init/skills/knowledge-base-bootstrap/SKILL.md`（检查 6）
- Modify: `cadence-init/skills/knowledge-base-api/SKILL.md`、`knowledge-base-pages/SKILL.md`（更新清单增图）

- [x] **Step 1: 检查项 6**

bootstrap 检查 5 行后追加：

```markdown
  6. 关系图等值：`evidence/relation-graph.yaml` 存在时，图边数等于 `evidence/traceability-matrix.md` 数据行数，图节点 ID 集等于 Manifest 各 documents 域登记实体与矩阵两端 ID 的并集；任一不符判 `failed`。
```

- [x] **Step 2: api/pages 更新清单增图行**

api §7 与 pages §9 的矩阵写入行（Task 2 Step 5 已改写的那行）后各加一行：

```markdown
- `evidence/relation-graph.yaml`（与矩阵同一次原子写入重建受影响条目，禁止手工编辑）
```

- [x] **Step 3: 验证**

grep：bootstrap 含 `关系图等值`；api/pages 各含 1 处 `relation-graph.yaml` 更新行。

- [x] **Step 4: 汇报路径（不提交 git）**

### Task 4: context 图消费与漂移分级

**Files:**
- Modify: `cadence-init/skills/knowledge-base-context/references/progressive-retrieval-guide.md`（2 处）
- Modify: `cadence-init/skills/knowledge-base-context/SKILL.md`（2 处）

- [x] **Step 1: guide 第 2 层直取优先走图**

第 2 层步骤 1（"种子已含精确稳定 ID…"）替换为：

```markdown
1. 种子已含精确稳定 ID、精确文件路径或 Method+Path 时，优先在 `evidence/relation-graph.yaml` 命中节点（读取 doc 引用与一跳边，含横向边）；图缺失或不命中时直接定位该实体主文件读取。两种直取均跳过总入口与领域索引，并在本层证据摘要记录直取方式与种子值。实体文档缺失或候选无法唯一定位时，回退本层完整路径并记录回退原因。
```

- [x] **Step 2: guide 第 6 层漂移分级**

第 6 层列表后追加一段：

```markdown
漂移分级：普通漂移——相关代码变化但契约字段、鉴权、连接键映射未被证伪，判`有条件就绪`并记录漂移明细；关键失效——任务引用实体被删除或转`已废弃`、契约字段或鉴权变化影响任务结论、组合的 JOIN_KEY 证据跳失效，判`阻断`并输出失效明细与修正建议（修正依赖或执行 Update）。种子命中 `CAP-*` 时，必须读取其输入 API 的契约锚点与 JOIN_KEY 证据执行上述检查。漂移结论默认保留在十三节内；用户要求保存时走既有 `task-contexts/` 路径，不新增落盘出口。
```

- [x] **Step 3: context SKILL.md §2 与 §4 同步**

- §2 直取说明句（"知识库语义路径支持精确种子直取：…"）替换为：

```markdown
知识库语义路径支持精确种子直取：优先在 `evidence/relation-graph.yaml` 命中节点取 doc 与一跳边，图缺失或不命中时直取实体主文件，均跳过总入口与领域索引；直取与回退均须留痕（见 `references/progressive-retrieval-guide.md` 第 2 层）。
```

- §4 基线漂移节（"- 对任务相关文件和符号比较 Manifest Git 基线与当前提交…"列表后）追加：

```markdown
漂移按指南第 6 层分级执行：普通漂移判`有条件就绪`，关键失效（实体删除/废弃、契约或鉴权变化、JOIN_KEY 证据跳失效）判`阻断`；种子命中 CAP 时检查其全部输入 API。
```

- [x] **Step 4: 验证**

grep：guide 含 `relation-graph.yaml`（第 2 层）与 `漂移分级`；context 含 `relation-graph.yaml` 与 `关键失效`。

- [x] **Step 5: 汇报路径（不提交 git）**

### Task 5: update 横向重算与锚点复核

**Files:**
- Modify: `cadence-init/skills/knowledge-base-update/SKILL.md`（2 处）

- [x] **Step 1: §3 影响链后加横向重算规则**

"对数据库、配置、中间件和领域资料使用同一稳定 ID 与关系矩阵。…" 段后追加：

```markdown
横向重算：影响链命中 `COMPOSES`/`JOIN_KEY`/`PROVIDES_FIELD` 边时必须重算——输入 API 被删除或转`已废弃`时，关联 CAP 标`待确认`或 `retired`，不保留断链 `verified`；JOIN_KEY 证据跳失效时 CAP 降 `proposed` 并登记待确认。横向重算与 `evidence/relation-graph.yaml` 对应条目重建在同一原子提交。
```

- [x] **Step 2: §4 实体清单后加锚点复核**

"- 业务知识条目转正：…" 行后追加：

```markdown
- 证据锚点复核：更新受影响实体文档时，必须复核文档内证据锚点（文件:行号）在当前提交可定位；失效锚点登记"待重锚"待确认，不静默保留。
```

- [x] **Step 3: 验证**

grep：update 含 `横向重算` 与 `待重锚`。

- [x] **Step 4: 汇报路径（不提交 git）**

### Task 6: 变更验证 + 统一测试

- [x] **Step 1: 机械核对**

Task 1–5 全部 grep 项重跑；`openspec validate "kb-composition-and-index-layer"`；设计验收标准 5 条逐条打勾；不变量零改动（阶段枚举/状态机/横向写入方限定/api-pages 纵向限权）；`git status` 范围核查。

- [x] **Step 2: 统一测试（结构化校验脚本，一次性不进仓库）**

脚本断言（覆盖三批全部改动）：
1. relation-types 枚举闭合：纵向 11 + 横向 3，无重复；横向含"已启用（2b）"与唯一写入方。
2. 三个模板（matrix/rule-card/flow/composition 四个）表格列数与表头一致。
3. manifest-template.yaml 为合法 YAML 且含 business_knowledge_sources/business/capabilities 键。
4. input-contract.md 内嵌 YAML 块可解析。
5. 固定产物清单三副本（SKILL.md:56 / input-contract 检测集合 / 输出树）集合相等。
6. relation-graph 等值规则可机械判定（脚本模拟：随机生成矩阵行 → 校验等值定义无歧义）。

- [x] **Step 3: 输出验证与测试汇报（不提交 git）**
