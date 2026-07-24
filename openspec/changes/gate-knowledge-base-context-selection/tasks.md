# Tasks: gate-knowledge-base-context-selection

## 1. Skill description 主门禁

- [ ] 1.1 在 `cadence-init/skills/knowledge-base-context/SKILL.md` frontmatter `description` 末尾追加选择前置门禁句，保持原有触发描述与正文不变

## 2. L0 路由层门禁

- [ ] 2.1 在 `cadence-init/skills/rule-config/references/rules/agent-routing-kernel.md` 路由表之后追加门禁句
- [ ] 2.2 将门禁句逐字同步进本仓库 `CLAUDE.md` 的 L0 受管块内
- [ ] 2.3 将门禁句逐字同步进本仓库 `AGENTS.md` 的 L0 受管块内
- [ ] 2.4 验证三处门禁句逐字一致、受管块版本标记未变、块外内容未改

## 3. 项目规则文档化兜底

- [ ] 3.1 新建 `cadence/project-rules/knowledge-base-gating.md`
- [ ] 3.2 在 `cadence/project-rules/README.md` 文件说明中登记该规则文件

## 4. 验证

- [ ] 4.1 全仓检索确认门禁句四处载体（description、内核模板、CLAUDE.md、AGENTS.md）语义一致且后三处逐字一致
- [ ] 4.2 确认 `knowledge-base-context` Skill 正文、异常处理表与受管块外内容无任何 diff
