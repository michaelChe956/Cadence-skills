# KnowledgeBase 规则接入指南

## 目录

- 规则层级
- 管理区块
- Skill 触发与调用
- 文件不存在
- 文件已存在
- 异常处理
- 内容边界

## 规则层级

遵循当前代理运行时的指令优先级。不得使用 KnowledgeBase 区块覆盖用户明确指令、上级 `AGENTS.md` 或目标项目已有规则。

详细 KnowledgeBase 使用规则放在：

```text
cadence/project-rules/knowledge-base-usage.md
```

`CLAUDE.md` 与 `AGENTS.md` 只保留入口和强制读取说明。

## Skill 触发与调用

项目规则要求需求澄清、Design、Plan、Coding、Testing、Review 和 Debug 七类任务先使用 `knowledge-base-context` 获取最小上下文。

- 自动触发依赖 `knowledge-base-context/SKILL.md` 的 Frontmatter Description。
- Claude Code 插件手动入口：`/cadence-init:knowledge-base-context`。
- Codex 在 Skill 已安装或被项目发现后使用手动入口：`$knowledge-base-context`。
- `agents/openai.yaml` 只提供 Codex 展示和默认提示元数据，不是触发注册表。
- `manifest.yaml` 只在 Skill 触发后提供 Schema、用户授权范围和知识库基线，不参与 Skill 发现或触发。
- Skill 同时读取 KnowledgeBase 与当前源码、DDL、配置，不把任一方作为另一方的替代。
- Skill 只负责原始任务的前置上下文阶段，不调用 `cadence-workflow`；上下文准备完成后，调用方继续用户原始任务。

已存在 Schema 3.0 KnowledgeBase 的项目升级到包含本 Skill 的插件版本后，应重新执行 `knowledge-base-overview` 刷新稳定管理区块；也可以在下一次 `knowledge-base-update` 编排 Overview 时完成刷新。不得直接覆盖管理区块外的人工规则。

## 管理区块

唯一标记：

```markdown
<!-- cadence-knowledge-base:start -->
...
<!-- cadence-knowledge-base:end -->
```

区块内可以更新，区块外不得修改。

## 文件不存在

创建最小文件：

```markdown
# AGENTS.md

<!-- cadence-knowledge-base:start -->
## 项目 KnowledgeBase

需求澄清、Design、Plan、Coding、Testing、Review 或 Debug 前，先使用 `knowledge-base-context` 获取最小任务上下文。
修改代码前读取 `cadence/knowledge-base/README.md`。
详细规则见 `cadence/project-rules/knowledge-base-usage.md`。
<!-- cadence-knowledge-base:end -->
```

`CLAUDE.md` 使用相同区块，不复制其他平台专属内容。

## 文件已存在

### 没有管理区块

保留原内容，在文件末尾追加一个空行和完整区块。

### 存在一个完整区块

只替换开始与结束标记之间的内容。

### 存在异常标记

以下情况不得自动修改：

- 只有开始标记
- 只有结束标记
- 多个开始或结束标记
- 区块嵌套
- 标记位于代码块中

记录问题、文件位置和人工修复建议。

## 内容边界

代理入口只包含：

- 知识库入口路径
- 七类任务优先使用 `knowledge-base-context`
- 修改前读取要求
- 按任务加载相关文档的要求
- 知识库冲突时回到源码验证
- 增量更新触发条件

不要放入完整模块、API、表或页面清单。
