# Tasks

> 高层工作包；精确文件、命令与实施顺序由 writing-plans 写入 `cadence/plans/`。

## WP1 新增矩阵模板与关系词表 [R1 矩阵格式契约, R2 关系类型闭合词表]

新增 `cadence-init/skills/knowledge-base-base-info/assets/traceability-matrix-template.md`（六列表头 + 示例行 + 排序规则）与 `assets/relation-types.md`（11 类闭合枚举，纵向 8 类含语义/方向/允许类型对/证据要求，横向 3 类标注"第二批启用"，含旧表述语义映射表）。

验收：两个文件存在；词表枚举闭合；横向类型带批次标注。

## WP2 base-info SKILL.md 升级 [R1, R2, R5 漂移字段激活]

§8 关系清单升级为按模板落盘 + 词表枚举门禁（不命中即拒写 + 待确认）；完成条件新增表文档元数据`证据基线`/`最后核验时间`非空校验。

验收：§8 含模板与词表强制规则；完成条件含两字段非空。

## WP3 api/pages 矩阵写入引用模板 [R1]

`knowledge-base-api/SKILL.md` §7 与 `knowledge-base-pages/SKILL.md` 更新清单中 `evidence/traceability-matrix.md` 处补模板格式引用。

验收：两处写入义务均指向 base-info 模板。

## WP4 bootstrap global-validation 第 5 项 [R3 矩阵机械检查]

`knowledge-base-bootstrap/SKILL.md` global-validation 内容完整性检查新增矩阵格式检查（表头六列 + 逐行关系类型 ∈ 词表，任一不符判 `failed`）。

验收：检查项措辞与现有第 1–4 项同构，失败处理沿用现有规则。

## WP5 检索精确种子直取 [R4]

`knowledge-base-context/references/progressive-retrieval-guide.md` 第 2 层插入精确种子直取分支（含直取留痕与回退规则）；`knowledge-base-context/SKILL.md` §2 同步加注。

验收：第 1 层与第 2 层不再矛盾；直取留痕要求明确。

## WP6 表模板必填与 overview 陈旧度暴露 [R5]

`table-data-model-template.md` §1 两字段改必填；`knowledge-base-overview/SKILL.md` 与 `assets/project-overview-template.md` 增加知识库 Git 基线与各领域最后核验时间暴露。

验收：模板字段标注必填；overview 有对应暴露要求与占位。

## WP7 变更验证 [全部]

对照设计文档验收标准逐项核对 6 个 Skill 目录的改动；`openspec validate --change kb-matrix-contract-and-retrieval-fix` 通过；确认无 Schema bump、无初始化状态机改动。

验收：验收标准 5 条全部满足并有核对记录。
