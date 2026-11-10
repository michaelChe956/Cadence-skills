# Tasks

## 1. Skill 规则修订

- [x] 1.1 `SKILL.md` 前置门禁 1 增加“已填写输入 / 未填写模板占位”判定与覆盖报告要求（对应「生成前置门禁（既有输入与既有知识库）」）
- [x] 1.2 `SKILL.md` api-scope 规则增加“规划文档能力不计入已实现清单”（对应「规划能力与实现现状的区分」）
- [x] 1.3 `SKILL.md` 敏感信息规则明确端口与带主机地址的区分（对应「敏感信息与草稿标记」）

## 2. 参考与文档

- [x] 2.1 `references/evidence-mapping.md`：api-scope 规划能力规则、工程范围端口口径、页面无路由库口径
- [x] 2.2 `references/demo.md`：新增“模板占位未填写”“规划文档能力未实现”场景
- [x] 2.3 `readmes/skills/knowledge-base-user-input.md`：使用前提补充模板占位判定

## 3. 验证

- [x] 3.1 在 `test-center-java` 上按修订后规则生成草稿，输入契约校验 59 项全过
- [x] 3.2 tier0 结构断言与 skill 结构校验复跑通过