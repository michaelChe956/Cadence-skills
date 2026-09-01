# Cadence Commands 使用指南

## 说明：Commands 与 Skills 的关系

Cadence 当前不提供独立的 Command 文件。项目能力由 `cadence-init` 下的 Skills 提供，Skill 名称就是调用入口；Commands 文档目录仅用于说明如何找到和使用这些 Skills。

`skill-creator` 是实际存在的 Skill，直接调用 `/skill-creator`，不是独立 Command。安装仓库、三层软链和四类 Agent 的消费路径以根 README 的网络安装章节为准。

## 可直接调用的 Skills

以下是常用的裸名调用示例：

- `/pre-check`：检查开发环境和工具。
- `/project-analysis`：分析项目结构、技术栈和依赖。
- `/rule-config`：配置项目规则和 Cadence 产物目录。
- `/knowledge-base-bootstrap`：初始化 Schema 4.0 KnowledgeBase。
- `/knowledge-base-context`：按任务获取最小知识库上下文。
- `/knowledge-base-update`：依据完整变更包更新知识库。
- `/skill-creator`：创建、校验、打包或优化 Skill。

完整的 14 个 Skill 清单见 [Skills 使用指南](../skills/README.md)。

## 相关资源

- [Skills 使用指南](../skills/README.md)
- [项目 README 的网络安装章节](../../README.md#安装-cadence-skills)
- [skill-creator 使用指南](../skills/skill-creator.md)

## 获取帮助

- 问题反馈：https://github.com/michaelChe956/Cadence-skills/issues
- 文档问题：提交 Issue 或 Pull Request，并附上使用的 Agent、Skill 名称和复现步骤。
