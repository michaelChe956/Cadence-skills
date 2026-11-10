# Proposal

## Why

在真实存量项目 `test-center-java` 上试跑 `knowledge-base-user-input` 时暴露三处规则缺口：

1. **模板已复制但未填写时被门禁挡住。** 该项目的 `cadence/knowledge-base/user-input/` 下 9 个文件与插件模板逐字相同（`diff` 验证全部一致），即“模板已复制、尚未填写”。原门禁判定为“9 个文件全部存在 → 停止并引导 bootstrap”，而这正是最常见的真实状态——用户照模板复制完就没再动了。Skill 在最该发挥作用的场景直接停摆。

2. **规划能力与已实现能力没有区分规则。** 项目内 `docs/issue-003-公告管理升级.md` 规划了分类 CRUD、详情、编辑、删除、置顶、分页筛选，代码中只实现了列表与创建。原规则只说“列全探测到的入口”，没说“文档里的规划能力怎么办”，存在把规划项当成已实现能力登记的风险。

3. **端口是否属敏感地址没有口径。** 首版把服务端口按敏感内部地址处理，导致工程范围文件里的服务标识被抹掉；实际契约列的是“内部域名、IP、URL”，端口只是服务标识的一部分。

## What Changes

- 前置门禁 1 增加“已填写输入 / 未填写模板占位”的判定：模板占位视为输入尚未准备，允许生成草稿覆盖并报告被覆盖文件；已填写文件仍不覆盖。
- api-scope 生成规则增加：规划或需求文档中尚未实现的能力不计入已实现清单，只登记为规划项待裁决，且不因此把领域判为不适用。
- 敏感信息规则明确：服务监听端口可作为服务标识保留，带主机部分的地址按敏感内部地址处理。
- `references/demo.md` 补 3 个场景，`readmes/skills/knowledge-base-user-input.md` 更新使用前提。

## Capabilities

### Modified Capabilities

- `knowledge-base-user-input-scaffold`: 生成前置门禁（模板占位判定）、敏感信息与草稿标记（端口口径）、新增“规划能力与实现现状的区分”。

## Impact

- `cadence-init/skills/knowledge-base-user-input/SKILL.md`、`references/evidence-mapping.md`、`references/demo.md`。
- `readmes/skills/knowledge-base-user-input.md`。
- 主 spec `knowledge-base-user-input-scaffold`。
- 无 **BREAKING** 契约变更：既有门禁、状态枚举与固定产物边界不变，只放宽“未填写模板占位”这一种情形。