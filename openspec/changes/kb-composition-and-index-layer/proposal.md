# Proposal

## Why

担忧 5（横向能力组合："a 接口查用户基本信息 + b 接口查用户账户信息 → 对外提供全部用户信息"类需求）在前两批只完成了前置（词表横向类型定义禁写、矩阵契约、条目状态协议）。本变更交付对症层：CAP 组合能力实体、矩阵的机读派生边表（同时改善精确种子直取的导航开销）、context 漂移分级与组合传播、Update 横向失效重算——横向失效自此可自动发现。

## What Changes

- **CAP-* 组合能力层**：新增 `capabilities/` 域（README + CAP-*.md）与 `capability-composition-template.md`（元数据/目的与非目标/输入能力清单/编排与字段映射（pattern 白名单）/输出契约/约束与鉴权/实现关联/证据）；`api-scope.md` 模板增"能力组合诉求"表（用户权威）；状态机 `proposed / verified / retired` 与 ai-draft/confirmed 正交；生成只有两通道（用户诉求、已有聚合端点反向建立），会话候选永不落库；`interfaces/README.md` 增"能力组合"分区仅作导航；Manifest 增 `documents.capabilities`。
- **JOIN_KEY 证据纪律**：连接键字段必须两侧各自经"API 模型 → SERVICE/MODULE → Mapper/SQL → TABLE 字段"逐跳映射到同一表字段，字段同名不构成依据，任一跳缺失 → JOIN_KEY 标待确认且组合不得 verified。
- **evidence/relation-graph.yaml 派生边表**：矩阵的唯一机读投影——严格派生（同一次原子写入重建、禁止手工编辑）、节点含全部稳定 ID 实体、每边保留 source span；global-validation 新增第 6 项等值校验（图边数 == 矩阵数据行数、节点 ID 集 == Manifest 登记 ∪ 矩阵两端）。
- **词表横向解禁**：`relation-types.md` 横向 3 类（COMPOSES/JOIN_KEY/PROVIDES_FIELD）改标"已启用（2b）"，唯一合法写入方为组合层（Overview 通道）；api/pages 写入行仍限纵向枚举。
- **context 消费与漂移分级**：精确种子直取优先命中 relation-graph（图缺失降级 README 链并留痕）；种子命中 CAP 时必须检查输入 API 契约与 JOIN_KEY 证据漂移；漂移分级——普通漂移判有条件就绪，关键失效（输入 API 删除/废弃、契约字段或鉴权变化、JOIN_KEY 证据跳失效）判阻断；不新增状态枚举、不新增落盘出口。
- **Update 横向重算与锚点复核**：影响链命中横向边必须重算（输入 API 删除或转 `已废弃` → 关联 CAP 标待确认或 retired，不留断链 verified）；更新受影响实体时复核文档内证据锚点在当前提交可定位，失效登记"待重锚"待确认；与 relation-graph 重建同一原子提交。

无 **BREAKING** 变更：Schema 保持 4.0、阶段枚举不变、能力组合为可选域（无诉求且无聚合端点时空目录合法）；不触碰原子写入、幂等、脱敏、非推测铁律、ai-draft/confirmed 协议。

## Capabilities

### New Capabilities

- `knowledge-base-composition`: 组合能力层与派生索引——CAP 实体/诉求输入/JOIN_KEY 证据纪律、relation-graph 派生边表与等值校验、词表横向启用边界、context 图消费与漂移分级、Update 横向重算与锚点复核。

### Modified Capabilities

（无）

## Impact

- `cadence-init/skills/knowledge-base-bootstrap/`：SKILL.md（固定输入/输出树/检测集合/固定产物四副本扩 capabilities/ 与 relation-graph）、global-validation 第 6 项、`manifest-template.yaml`（documents.capabilities）、`user-input/api-scope.md`（诉求表）。
- `cadence-init/skills/knowledge-base-overview/`：SKILL.md（CAP 生成职责/两通道/接口索引分区/登记）、`assets/capability-composition-template.md`（新增）。
- `cadence-init/skills/knowledge-base-api/SKILL.md`：输入 API 契约/鉴权/JOIN_KEY 证据核实职责、索引第三分区写入格式。
- `cadence-init/skills/knowledge-base-context/SKILL.md` 与 `references/progressive-retrieval-guide.md`：图优先直取+降级留痕、组合命中检查、漂移分级。
- `cadence-init/skills/knowledge-base-update/SKILL.md`：横向重算、锚点复核。
- `cadence-init/skills/knowledge-base-base-info/assets/relation-types.md`：横向 3 类解禁标注与写入方限定。
- `cadence-init/skills/knowledge-base-base-info/SKILL.md`：relation-graph 首建职责。
- 设计文档：`cadence/designs/2026-09-20_方案设计_KnowledgeBase组合与索引层_v1.0.md`（已确认）。
