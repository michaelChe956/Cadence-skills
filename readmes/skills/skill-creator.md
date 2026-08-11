# skill-creator Skill

## 概述

`skill-creator` 是 Skill 创建与维护工具，支持从自然语言需求出发，完成 Skill 的创建、校验、打包与优化。  
推荐优先使用“自然语言驱动”方式，Python 脚本作为可选自动化方案。

## 如何单独使用

### 命令调用

```bash
/skill-creator
```

### 自动触发

当用户出现以下意图时建议触发：

- “帮我做一个 Skill”
- “我想把这套流程做成可复用 Skill”
- “把这份 markdown 变成 Skill”
- “帮我优化现有 Skill 的 description”

## 具体使用案例

### 案例 1：自然语言创建项目级 Skill（推荐）

**用户输入**：

```text
请帮我创建一个项目级 skill，名字叫 pdd-question。
用途是处理拼多多售后问答，输入是问题描述和订单号，
输出是标准答复和可执行下一步。
要求中文输出，先给结论后给步骤。
```

**执行流程**：

1. 🎯 **确认目标与边界**
   - 明确 Skill 的目标、触发条件、输入输出、约束
   - 补齐缺失信息（例如是否项目级或全局级）

2. 🧱 **生成 Skill 结构**
   - 创建 Skill 目录与 `SKILL.md`
   - 填写用途、触发场景、执行步骤、注意事项

3. ✅ **快速校验**
   - 检查结构完整性
   - 检查说明是否可执行、是否与用户目标一致

4. 📦 **可选打包与优化**
   - 需要发布时打包成 `.skill`
   - 需要提升召回时优化 description

### 案例 2：导入现有 markdown 为 Skill

**用户输入**：

```text
把 .claude/pdd-question.md 转成当前项目可用的 skill。
```

**执行流程**：

1. 读取源 markdown
2. 转换为 `SKILL.md` 标准结构
3. 写入 `.claude/skills/<skill-name>/`
4. 运行校验并给出结果

### 案例 3：优化已有 Skill 的 description

**用户输入**：

```text
这个 skill 触发不准，帮我优化 description 提升召回准确率。
```

**执行流程**：

1. 分析当前 description 问题
2. 结合样例集进行多轮优化
3. 输出优化前后差异与建议


## 结果产物

- 技能目录：`skills/my-new-skill/`
- 项目级技能目录：`.claude/skills/my-new-skill/`
- 全局技能目录：`~/.claude/skills/my-new-skill/`
- 分发包：`dist/my-new-skill.skill`
- 优化结果（可选）：`--output` 指定的 JSON 文件

## 最佳实践

### 1. 先自然语言，后自动化

先把目标说清楚，再决定是否进入脚本流水线。

### 2. 明确输入输出契约

Skill 写得准不准，取决于输入输出是否定义清晰。

### 3. 保持单一职责

一个 Skill 尽量只做一类事情，避免“大而全”。

### 4. 小步优化 description

先保证可用，再基于真实案例持续优化召回与命中。

## 常见问题

### Q: 一定要会 Python 才能用 skill-creator 吗？

A: 不需要。推荐方式是自然语言驱动，Python 只是可选自动化能力。

### Q: project 和 global 应该怎么选？

A:
- `project`：仅当前项目使用，推荐默认选项
- `global`：多个项目复用同一 Skill 时使用

### Q: 如何判断一个 Skill 是否写得好？

A: 至少满足三点：
- 触发条件清晰
- 输入输出明确
- 执行步骤可落地、可验证

## 相关 Skills

- **cadencing** - 项目初始化

## 技术细节

完整脚本参数、目录结构和进阶用法请参考：  
[skills/skill-creator/SKILL.md](../../cadence-init/skills/skill-creator/SKILL.md)
