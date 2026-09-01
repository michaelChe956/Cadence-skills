# skill-creator Skill

## 概述

`skill-creator` 用于从自然语言需求创建、校验、打包和优化 Skill。它支持新建 Skill、导入现有 Markdown、修复 front matter、检查触发描述和按需生成分发包。

## 如何单独使用

### /skill-creator 调用

直接使用裸 Skill 名：

```text
/skill-creator
```

请在调用时说明目标名称、用途、触发场景、输入输出、约束和目标目录。

### 自动触发

当用户提出以下意图时使用：

- 创建一个新的 Skill。
- 把一套流程做成可复用 Skill。
- 将 Markdown 转换为当前项目可用的 `SKILL.md`。
- 校验已有 Skill 的 front matter 或目录结构。
- 优化 Skill 的 description 以提高触发准确性。

## 具体使用案例

### 案例 1：自然语言创建项目级 Skill

用户可以这样描述：

```text
请使用 /skill-creator 创建一个项目级 Skill，名字叫 pdd-question。
用途是处理售后问答，输入是问题描述和订单号，输出是标准答复和下一步。
```

执行时先确认目标和边界，再生成目录与 `SKILL.md`，随后校验结构、调用契约和描述是否可执行。

### 案例 2：导入现有 Markdown

```text
请使用 /skill-creator 把 .claude/pdd-question.md 转成当前项目可用的 Skill。
```

流程是读取源文档、转换为标准 `SKILL.md`、写入目标 Skill 目录并执行校验。

### 案例 3：优化已有 description

```text
请使用 /skill-creator 优化这个 Skill 的 description，提高召回准确率。
```

流程是分析触发条件、结合真实样例比较优化前后效果，并输出差异和建议。

## 结果产物

- Skill 定义目录：`skills/<skill-name>/`。
- 项目级使用目录：`.claude/skills/<skill-name>/`。
- 个人级使用目录：`~/.claude/skills/<skill-name>/`。
- 分发包（可选）：`dist/<skill-name>.skill`。
- 优化结果（可选）：由输出参数指定的 JSON 文件。

本仓库内置 Skill 的源定义位于 `cadence-init/skills/skill-creator/`；仓库安装与 Agent 消费路径见根 README 的网络安装章节。

## 最佳实践

### 1. 先自然语言，后自动化

先说清楚目标、边界和使用方式，再决定是否执行脚本化工作流。

### 2. 明确输入输出契约

为 Skill 写清输入、输出、失败条件和验证方式，避免仅凭标题触发。

### 3. 保持单一职责

一个 Skill 尽量只处理一类稳定任务，复杂流程拆分为可组合步骤。

### 4. 小步优化 description

先保证行为正确，再基于真实案例持续优化 description 的召回和命中。

### 5. 保持源目录与名称一致

Skill 目录名必须与 front matter 的 `name` 相同，并且目录中包含 `SKILL.md`。

## 常见问题

### Q：一定要会 Python 才能用 `skill-creator` 吗？

不需要。推荐使用自然语言驱动，Python 仅作为可选自动化能力。

### Q：项目级和个人级应该怎么选？

项目级只对当前项目生效，适合项目规则和业务流程；个人级用于多个项目复用。选择后仍需确认对应 Agent 的消费路径。

### Q：如何判断一个 Skill 是否写得好？

至少应满足：触发条件清晰、输入输出明确、执行步骤可落地、失败情况可解释、结果可验证。

### Q：如何查看实际源文件？

仓库内定义文件为 `cadence-init/skills/skill-creator/SKILL.md`，该路径必须存在。

## 相关 Skills

- `pre-check`：检查开发环境和相关工具。
- `project-analysis`：分析项目结构与技术栈。
- `rule-config`：配置项目规则和目录结构。
- `project-rules-examples`：创建项目个性化规则模板。

## 技术细节

完整参数、目录约定和执行流程请参考：

- [仓库内 Skill 定义](../../cadence-init/skills/skill-creator/SKILL.md)
- [14 个 Skills 导航](README.md)
- [Commands 与 Skills 关系](../commands/skill-create.md)
