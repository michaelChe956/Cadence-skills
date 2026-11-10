# Tasks

## 1. 新 Skill：knowledge-base-user-input

- [x] 1.1 创建 `cadence-init/skills/knowledge-base-user-input/SKILL.md`：前置门禁（已有输入、知识库已存在、项目类型、只读边界）、9 文件固定输出、生成规则、生成后自检、确认清单交付（对应「生成前置门禁（既有输入与既有知识库）」「生成前置门禁（项目形态与只读边界）」「九文件结构与状态取值」「生成后自检与确认清单交付」）
- [x] 1.2 编写 `references/evidence-mapping.md`：六领域 + DDL + product 的只读证据探测方法与证据位置要求（对应「只读证据采集」「领域文件的证据登记规则」）
- [x] 1.3 编写 `references/demo.md`：无前端、无 DDL、配置无法锁定、已有输入、知识库已完成等边界场景（对应「生成前置门禁」「九文件结构与状态取值」）
- [x] 1.4 编写 `agents/openai.yaml`：界面显示名、短描述与默认提示

## 2. Bootstrap 集成

- [x] 2.1 在 `knowledge-base-bootstrap/SKILL.md` 的输入缺失处理处增加草稿生成指引，并明确 bootstrap 不代替用户填写、不消费未确认草稿（对应「草稿与 Bootstrap 的边界」）

## 3. 文档

- [x] 3.1 更新 `README.md`：skill 数量 14→15、KnowledgeBase skills 表新增一行、初始化流程补充草稿步骤
- [x] 3.2 更新 `readmes/skills/README.md`：总数、分类表与快速导航新增条目
- [x] 3.3 新增 `readmes/skills/knowledge-base-user-input.md` 使用指南

## 4. 测试与门禁

- [x] 4.1 `evals/kb/assertions/tier0.py` 增加断言：新 Skill 目录与 frontmatter 名称一致；其声明的 9 个文件名与 `knowledge-base-bootstrap/user-input/` 实际模板一一对应；与 bootstrap SKILL.md「固定输入」树一致
- [x] 4.2 在 `evals/kb/fixtures/standard/` 试跑草稿生成流程，按输入契约校验 9 个文件（状态枚举、结构证据、资料链接、不适用原因、敏感信息、模板表头、证据路径）：68 项检查全部通过
- [x] 4.3 运行 skill 结构校验脚本与 tier0 断言，记录输出（`Skill is valid`；`[tier0] PASS 21 FAIL 0`）

## 5. 规格同步

- [x] 5.1 `network-skill-install` 规格中 skill 数量口径 14→15