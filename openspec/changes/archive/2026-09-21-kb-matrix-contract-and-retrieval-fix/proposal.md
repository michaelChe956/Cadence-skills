# Proposal

## Why

Schema 4.0 KnowledgeBase 的 `evidence/traceability-matrix.md` 被 base-info/api/pages/overview 四个 Skill 写入、被 context 检索链当作一层读取，却没有任何格式契约——同一关系在不同 Skill 手里可能写成不同形状，检索链最后一跳无法机械核对。同时检索指南存在内部矛盾（第 1 层"种子精度优先" vs 第 2 层"索引优先"，精确种子被强制两次零信息增量的索引读取），且表模板的"证据基线/最后核验时间"字段闲置、知识库陈旧度不可见。这三处基础缺陷是后续组合能力层（CAP-*）、字段域反向索引、派生边表的前置阻塞项。

## What Changes

- 新增 `knowledge-base-base-info/assets/traceability-matrix-template.md`：矩阵固定六列契约（来源稳定 ID / 关系类型 / 目标稳定 ID / 关系证据(文件:行号) / 证据状态 / 详情链接）。
- 新增 `knowledge-base-base-info/assets/relation-types.md`：闭合关系类型词表——纵向 8 类本批启用，横向 3 类（`COMPOSES`/`JOIN_KEY`/`PROVIDES_FIELD`）定义但标注"第二批启用"，初始化不得写入横向边。
- `knowledge-base-base-info/SKILL.md` §8 从散文关系清单升级为"按模板落盘 + 关系类型只允许取词表枚举值（不命中即写入失败并登记待确认）"；完成条件新增表文档元数据两字段非空校验。
- `knowledge-base-api/SKILL.md` 与 `knowledge-base-pages/SKILL.md` 的矩阵写入处补"按 base-info 矩阵模板格式追加"。
- `knowledge-base-bootstrap/SKILL.md` global-validation 内容完整性检查新增第 5 项：矩阵格式机械检查（表头六列 + 逐行关系类型 ∈ 词表）。
- `knowledge-base-context/references/progressive-retrieval-guide.md` 第 2 层新增精确种子直取分支（精确稳定 ID / 文件路径 / Method+Path 直取实体主文件，跳过总入口与领域索引，记录跳过理由），`knowledge-base-context/SKILL.md` §2 同步；消除与第 1 层优先级表的矛盾。
- 表模板"证据基线/最后核验时间"改为必填；`knowledge-base-overview` 在 README 覆盖范围处暴露知识库 Git 基线与各领域最后核验时间。不引入自动失效机制，Update 仍是唯一刷新入口。

无 **BREAKING** 变更：Schema 保持 4.0、无新初始化阶段、无新顶层目录；不触碰原子写入、变更包幂等、敏感脱敏、初始化状态不变量门禁。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `knowledge-base-artifact-enforcement`: 在现有 14 项 requirement 基础上新增 delta——矩阵模板与关系词表的强制落盘、global-validation 矩阵机械检查、context 精确种子直取分支、表文档漂移字段必填与 overview 陈旧度暴露。

## Impact

- `cadence-init/skills/knowledge-base-base-info/`：SKILL.md §8 与完成条件；新增 2 个 assets 文件。
- `cadence-init/skills/knowledge-base-api/SKILL.md`、`cadence-init/skills/knowledge-base-pages/SKILL.md`：矩阵写入处各补一句模板引用。
- `cadence-init/skills/knowledge-base-bootstrap/SKILL.md`：global-validation 新增第 5 项检查。
- `cadence-init/skills/knowledge-base-context/SKILL.md` 与 `references/progressive-retrieval-guide.md`：精确种子直取分支。
- `cadence-init/skills/knowledge-base-overview/SKILL.md` 与 `assets/project-overview-template.md`：陈旧度暴露。
- 设计文档：`cadence/designs/2026-09-20_方案设计_KnowledgeBase关系契约与检索修复_v1.0.md`（已确认）。
- 消费侧影响：新初始化的知识库按新契约生成矩阵；本仓库与消费项目当前无存量 Schema 4.0 实例，无迁移成本。
