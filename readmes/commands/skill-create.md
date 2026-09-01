# /skill-creator - Skill 创建与优化

## 定位：这不是独立 Command

`skill-creator` 是 `cadence-init` 提供的实际 Skill，不是独立 Command，也不需要单独注册入口。它属于 Cadence 的 14 个 Skills，安装路径由根 README 介绍的 `install.sh` 提供。

## 常见场景

- 从自然语言需求创建新 Skill。
- 将现有 Markdown 整理为 `SKILL.md`。
- 校验 Skill front matter、目录结构和调用契约。
- 优化 Skill description 的触发准确性。
- 按需打包 Skill 供团队复用。

## 对应 Skill

- 名称：`skill-creator`
- 源路径：`cadence-init/skills/skill-creator/`
- 定义文件：[`cadence-init/skills/skill-creator/SKILL.md`](../../cadence-init/skills/skill-creator/SKILL.md)

## 调用示例

直接使用裸 Skill 名：

```text
/skill-creator
```

调用时补充目标名称、用途、触发条件、输入输出、适用范围和目标目录。例如：

```text
请使用 /skill-creator 创建一个用于订单售后问答的项目级 Skill，说明输入、输出和触发条件。
```

## 详细文档

- [skill-creator Skill 使用指南](../skills/skill-creator.md)
- [完整 Skills 导航](../skills/README.md)
- [根 README 的网络安装章节](../../README.md#安装-cadence-skills)
