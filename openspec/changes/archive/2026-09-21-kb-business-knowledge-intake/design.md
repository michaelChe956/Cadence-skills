# Design

## 关联

完整设计已确认并持久化于 `cadence/designs/2026-09-20_方案设计_KnowledgeBase业务知识输入面_v1.0.md`；本文件记录契约层架构边界与权衡。

## 边界与决策

### 可选输入，不抬门槛

- 业务知识证据三源与 product.md 全部可选：缺省时初始化行为与既有路径完全一致，business/ 生成带"未提供"说明的 README 即合法。
- 不新增第七领域、不加初始化阶段：business/ 生成落在现有 overview 阶段内，`coverage.initialization` 阶段枚举不变（沿用第一批"一次变更不动状态机"原则；Max 组合层方案中自我修正的同一结论）。

### 证据分层与条目状态

- 证据可信度排序：用户权威输入（product.md/用户资料/会话确认）> 当前 HEAD 可定位证据（代码/测试/ADR，`文件:行号`）> ref 型证据（git 历史，`文件:行号@<commit>`）。
- `confirmed` 需"可定位证据 + 用户权威输入"双条件之一组合且无来源冲突；ref 型证据与纯代码推断只能出 `ai-draft`。这化解"不推测"铁律与自动化覆盖的矛盾（IBM wca4z 生产级同构：AI 生成打标、人工核准后转正）。
- ai-draft 是合法状态不是缺陷：登记 open-questions 计数但不阻断 global-validation；堆积风险由四级计数可视化。

### business/ 域所有权

- Owner：`knowledge-base-overview`（综合已有领域文档与用户资料，不重新扫描源码——API/表文档已完成取证）；模板放 overview assets。
- 源优先级：用户资料与 product.md > 测试断言 > ADR > 既有文档寄生规则（迁移不删原文，只追加链接）> git 历史意图（仅 ai-draft）。
- 流程封顶解除方式：README 保持 3–5 条导航摘要（token 纪律不变），实体层不设限但逐条挂证据——把"封顶"从产物层挪到导航层。
- RULE↔RULE 关联用文档内链接不进矩阵，防止边爆炸。

### 词表扩展与第一批衔接

- 纵向新增 `INVOLVES`（FLOW/RULE/JOB → 实体）、`PRODUCES`/`CONSUMES`（SERVICE/MODULE ↔ EVENT），横向 3 类仍禁写（2b 启用）。
- global-validation 检查 5 的枚举以 `relation-types.md` 文件为准（不硬编码清单），词表扩展自动进入检查范围。
- 词表自身的"新增类型必须经 Update 变更包"规则与本变更的授权关系：本变更是经用户确认的 OpenSpec 契约，等效授权一次词表纵向扩展。

### EVENT/JOB 落点

- ID 生成归 `knowledge-base-api`（能力发现与主文件在此），base-info §8 清单补登记义务；overview §5 既有引用自此闭合。

## 失败处理

| 失败 | 处理 |
|------|------|
| 证据路径越界 / git range 不可解析 | 停止该证据源 + 待确认，不阻断其他领域 |
| 规则/流程证据不足 | 不生成实体，进待确认清单（沿用"不用推测补齐"） |
| ai-draft 条目被当事实引用 | context 输出门禁强制标注，违反即输出门禁不过 |
| 寄生规则迁移冲突 | 原文保留 + 链接，冲突写来源冲突待确认 |

## 兼容性

- Schema 保持 4.0；存量消费项目无 Schema 4.0 实例，无迁移。
- 全部新输入可选：不声明任何新章节的项目，六个 Skill 的行为与第一批完成后完全一致。
- 不触碰：原子写入、变更包幂等、敏感脱敏、非可信输入边界、初始化状态机。

## 权衡记录

| 备选 | 弃用原因 |
|------|---------|
| 新增第七领域 + 新阶段（business-knowledge 阶段） | 动 `coverage.initialization` 枚举与状态机，违反最小扩展原则；overview 阶段内生成已满足依赖顺序（领域文档先于综合） |
| business/ 挂 base-info 生成 | base-info 不读 API/页面/测试语义，综合职责天然在 overview；且 base-info 已有重载（配置指纹门禁） |
| 术语关系进矩阵边 | 术语↔实体关系量大且低价值，glossary 两列即可承载，避免矩阵膨胀 |
| git 历史默认启用 | 成本高且证据可信度最低（ref 型），默认 false 由用户显式开启 |
