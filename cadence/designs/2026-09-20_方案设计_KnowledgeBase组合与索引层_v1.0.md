# 方案设计：KnowledgeBase 组合与索引层（第二批 2b）

- 日期：2026-09-20
- 版本：v1.0
- 状态：待评审
- 关联：第一批（矩阵契约/词表）、2a（业务知识输入面）均已实施；四 Agent 讨论 Max 组合层方案（含自我修正）+ DS/GLM 边表方案收敛

## 1. 背景与动机

担忧 5（横向能力组合）的直接对症层。前两批已完成前置：词表横向类型已定义（禁写状态）、矩阵契约就绪、business/ 域与条目状态协议可用。本批交付：

1. **CAP-* 组合能力层**：`capabilities/` 目录承载"a 接口 + b 接口 → 对外新能力"的编排描述（输入 API/连接键/编排方式/输出契约/失败一致性策略），用户诉求驱动、证据支撑、不自动枚举。
2. **evidence/relation-graph.yaml 派生边表**：矩阵的机读投影（确定性派生、每节点带 source span），让精确种子直取与一跳邻域不依赖多级 README——同时改善担忧 3 的导航开销。
3. **context 漂移分级与组合传播**：任务命中组合时其输入 API 的漂移向上传播；关键失效判阻断。
4. **Update 横向重算 + 锚点复核**：横向失效可自动发现（输入 API 删除 → 组合标待确认）；受影响实体的证据锚点复核。

## 2. 范围（四项）

| # | 改动 | 类型 |
|---|------|------|
| 1 | `capabilities/` 域 + CAP 模板 + api-scope 诉求表 + 词表横向启用 | 新实体域 |
| 2 | `evidence/relation-graph.yaml` 派生边表 + global-validation 等值校验 | 派生产物 |
| 3 | context：relation-graph 消费 + 漂移分级 + 组合传播 | 检索强化 |
| 4 | update：横向重算 + 锚点复核 | 更新强化 |

## 3. 非目标

- 组合的自动发现/枚举（a×b 笛卡尔积明确禁止；会话级候选不落库）
- 运行时编排执行（组合文档是数据描述，不可执行、不接受脚本）
- FLOW/RULE 与 CAP 的自动关联（人工建立链接）
- 总测试（结构化校验脚本）在本批实施完成后单独执行（用户指示：都做完再测试）
- 不触碰：原子写入、幂等、脱敏、初始化状态机、非推测铁律、ai-draft/confirmed 协议

## 4. 详细设计

### 4.1 CAP-* 组合能力层

**目录与登记**：`cadence/knowledge-base/capabilities/`（README.md 索引 + `CAP-*.md`）；bootstrap 固定输出树/检测集合/固定产物三处同步；Manifest 增 `documents.capabilities`。

**输入（用户权威）**：`user-input/api-scope.md` 模板增"能力组合诉求"表：

```markdown
## 能力组合诉求（可选）

| 目标能力名 | 期望输出字段 | 来源能力 ID | 连接键 | 声明依据 |
|-----------|-------------|------------|--------|----------|
```

**组合文档模板**（`knowledge-base-overview/assets/capability-composition-template.md`，骨架沿用 Max 方案）：

- 元数据：`CAP-*` ID、条目状态（`proposed / verified / retired`，与 ai-draft/confirmed 正交：proposed≈设计已确认未实现，verified≈有实现证据）、来源（用户诉求/已有实现）
- 目的与非目标（intent，明确"全部用户信息"的字段边界，不默认涵盖敏感字段）
- 输入能力清单：step、api_id、required、request_mapping、contract_ref（指向接口主文件参数报文锚点）
- 编排与字段映射：pattern 白名单（parallel_join / sequential）、join_key、output_mapping（命名空间合并，禁覆盖）、failure_policy（fail_whole / partial）
- 输出契约：字段集与允许公开范围
- 约束与鉴权：identity_mapping、tenant_isolation、external_permission（逐项证据或待确认）
- 实现关联：implementation_api_ids（实际聚合端点 API-*；为空 = 未实现，状态恒 proposed）
- 证据与待确认

**JOIN_KEY 证据纪律**（铁律，复用 api §7.1）：两个输入 API 的连接键字段必须各自经"API 模型 → SERVICE/MODULE → Mapper/SQL → TABLE 字段"逐跳映射到同一表字段；字段同名不构成关联依据；任一跳缺失 → JOIN_KEY 边标待确认、组合不得 verified。

**生成职责**（两通道，缺一不生成持久实体）：

1. 用户诉求通道：api-scope 声明组合诉求 → API Skill 核实输入 API 存在性、契约、鉴权与 JOIN_KEY 证据 → Overview 在 overview 阶段生成/更新 CAP 文档（状态 proposed）。
2. 已有实现通道：工程内发现聚合端点（调用多个能力的对外 API）→ API 正常生成该端点 API 文档 → Overview 依其调用链反向建立 CAP 并关联 implementation_api_ids（可 verified）。

会话中 Agent 推导的组合候选**只进会话输出与待确认清单，不生成实体**。

**接口索引导航**：`interfaces/README.md` 增第三分区"能力组合"（仅 ID/名称/状态/明细链接，导航性质）；对外属性仍以用户 api-scope 清单为权威——CAP verified ≠ 对外已暴露。

### 4.2 evidence/relation-graph.yaml 派生边表

**形态**（DS 方案收敛）：

```yaml
schema: kb-relation-graph/1.0
derived_from: evidence/traceability-matrix.md   # 唯一真相源
nodes:
  - { id: API-internal-order-export, kind: api, label: 创建导出任务, status: 已暴露, doc: interfaces/xxx.md }
edges:
  - { type: READS, from: API-internal-order-export, to: TABLE-order, evidence: services/order/OrderMapper.java:88 }
```

- **严格派生**：与矩阵在同一次原子写入中重建受影响条目；禁止手工编辑；冲突以矩阵与领域文档为准。
- **节点**：全部已登记稳定 ID 实体（含 EVENT/JOB/RULE/FLOW/CAP）；**边**：矩阵全部行；每边保留 source span（证据位置）。
- **生产者**：base-info 首建骨架；api/pages/overview（含 business/capabilities）与 update 在各自原子写入中同步重建对应条目。
- **等值校验**（global-validation 新增第 6 项，复刻键数核对模式）：图边数 == 矩阵数据行数；图节点 ID 集 == Manifest 各 documents 域与矩阵两端 ID 并集；任一不符判 `failed`。
- **词表横向启用**：relation-types.md 横向 3 类标注由"第二批启用，本批禁止写入"改为"已启用（2b）"，枚举开放；组合层是横向边唯一合法写入方（经 Overview 生成、用户诉求或实现证据支撑）。

### 4.3 context 消费与漂移分级

- **精确种子直取优先走图**：第 2 层精确种子直取时优先在 relation-graph.yaml 命中节点（取 doc 与一跳 edges），图缺失或不命中再回退 README 链（记录降级原因）——与 2a 已落地的直取分支衔接。
- **组合命中检查**：任务种子命中 CAP 时，必须读取其输入 API 的契约锚点与 JOIN_KEY 证据，并执行漂移检查。
- **漂移分级**（细化既有 `基线漂移` 状态，不新增状态枚举）：
  - 普通漂移：相关代码变化但关键结论（契约字段/鉴权/连接键映射）未证伪 → 有条件就绪，记录漂移明细。
  - 关键失效：输入 API 删除/废弃、契约字段或鉴权变化影响任务结论、JOIN_KEY 证据跳失效 → 阻断，输出失效明细与建议（修正依赖或 Update）。
- 不新增落盘出口：漂移默认在十三节内；用户要求保存走既有 `task-contexts/`。

### 4.4 Update 横向重算与锚点复核

- **横向重算**：影响链命中 `COMPOSES`/`JOIN_KEY`/`PROVIDES_FIELD` 边时必须重算——输入 API 被删除或转 `已废弃` → 关联 CAP 标 `待确认` 或 `retired`，不留断链 verified；JOIN_KEY 证据跳失效 → CAP 降 `proposed` 并登记待确认。
- **锚点复核**：Update 更新受影响实体文档时，必须复核文档内证据锚点（文件:行号）在当前提交仍可定位；失效锚点登记待确认（"待重锚"），不静默保留。
- 上述与 relation-graph 重建在同一原子提交内。

## 5. 验收标准

1. `capabilities/` 与模板存在；api-scope 模板含诉求表；三份固定产物清单副本含 `capabilities/`；`documents.capabilities` 存在。
2. relation-graph.yaml 契约文档化（严格派生+等值校验）；global-validation 第 6 项存在；词表横向 3 类改标"已启用（2b）"。
3. context：图优先直取+降级留痕、组合命中检查、漂移分级（普通/关键失效）均落地；无新增状态枚举、无新增落盘出口。
4. update：横向重算（删除/废弃→CAP 失效）与锚点复核落地；与图重建原子提交。
5. 不变量零改动（阶段枚举/状态机/幂等/脱敏/非推测）；无组合自动枚举路径。

## 6. 测试计划（本批实施完成后统一执行，用户指示）

结构化校验脚本（一次性，不进仓库）：词表闭合与批次标注、三个新模板表格列数、manifest 模板 YAML 合法性与新键、input-contract/api-scope 模板 YAML 块可解析、三份固定产物清单副本一致、relation-graph 等值规则自洽（边数定义可机械判定）。

## 7. 风险与对策

| 风险 | 对策 |
|------|------|
| relation-graph 与矩阵漂移（第二真相源） | 严格派生 + 同一次原子写入 + global-validation 等值校验（复刻配置指纹三重相等模式） |
| CAP 候选堆积 | 只有用户诉求/已有实现两通道生成；proposed/retired 状态进 business-README 式计数摘要 |
| 横向类型解禁后误用 | 唯一合法写入方是组合层（Overview 通道），api/pages 写入行仍限纵向枚举——词表分域授权 |
| 组合被当作对外暴露事实 | CAP verified ≠ 已暴露；对外属性唯一权威仍是 api-scope 用户清单 |
