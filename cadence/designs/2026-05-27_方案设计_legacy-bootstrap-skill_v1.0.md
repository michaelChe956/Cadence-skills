# legacy-bootstrap skill 方案设计

**生成日期**：2026-05-27  
**文档类型**：方案设计  
**版本**：v1.0  
**目标插件**：`cadence-init`  

## 1. 背景

`legacy-bootstrap` 是 `cadence-init` 插件的一部分，用于帮助 Claude Code、Codex 等 Agent 在进入本地已 clone 的历史项目时，快速建立项目认知。

该 skill 不负责 clone 远程仓库，不负责代码重构，也不把 repomix 输出直接当成结论。它的核心作用是：

- 使用 `npx repomix@latest` 汇总当前项目上下文。
- 基于 repomix 输出分析项目结构、架构、模块、依赖、风险和未知项。
- 将分析结果沉淀到目标项目的 `cadence/` 目录。
- 更新目标项目的 `CLAUDE.md` 与 `AGENTS.md`，让 Claude Code 和 Codex 能渐进式读取并使用这些认知文档。

参考资料：

- Repomix CLI Options：https://repomix.com/guide/command-line-options
- Repomix Remote Repository Processing：https://repomix.com/guide/remote-repository-processing
- Repomix Agent Skills Generation：https://repomix.com/guide/agent-skills-generation

## 2. 目标

### 2.1 主要目标

新增以下文件：

- `cadence-init/skills/legacy-bootstrap/SKILL.md`
- `cadence-init/commands/legacy-bootstrap.md`

使用户可以在一个本地 legacy 项目中显式调用 legacy bootstrap 流程，完成项目认知初始化。

### 2.2 非目标

- 不支持远程 GitHub 仓库作为输入。
- 不负责自动 clone 项目。
- 不生成 `.ai/` 目录。
- 不直接修改业务代码。
- 不把未知业务事实写成确定结论。
- 不默认使用 repomix 的实验性 `--skill-generate` 作为主流程。

## 3. 使用场景

适用于以下情况：

- 用户在 Claude Code 或 Codex 中打开一个本地 legacy 项目。
- 项目已有一定规模，Agent 需要在正式需求、设计或修改代码前建立初始认知。
- 团队希望将项目认知沉淀为可版本化、可持续维护的 Cadence 文档。
- 后续任务需要 Claude Code 与 Codex 按任务类型渐进式加载上下文。

不适用于以下情况：

- 全新空项目。
- 只需要一次性查看少量文件的小任务。
- 用户明确要求不生成项目文档。

## 4. 设计方案

采用“Repomix 标准 Bootstrap 工作流”。

该方案默认执行标准模式，但启动时必须询问用户是否升级为深度模式。轻量模式只作为项目过大、时间有限或 repomix 输出不可处理时的降级选项。

### 4.1 文件结构

```text
cadence-init/
├── commands/
│   └── legacy-bootstrap.md
└── skills/
    └── legacy-bootstrap/
        └── SKILL.md
```

### 4.2 command 职责

`cadence-init/commands/legacy-bootstrap.md` 是用户显式入口，职责是：

- 说明命令用途。
- 指向 `legacy-bootstrap` skill。
- 说明适用场景与输出产物。
- 给出典型调用方式。

command 不承载完整流程细节，避免与 skill 内容重复。

### 4.3 skill 职责

`cadence-init/skills/legacy-bootstrap/SKILL.md` 是核心 SOP，职责是：

- 检查当前项目上下文。
- 询问执行模式。
- 执行 repomix。
- 分析 repomix 输出。
- 生成 `cadence/` 文档。
- 更新 `CLAUDE.md` 与 `AGENTS.md`。
- 输出结果摘要和后续建议。

## 5. 执行流程

### 5.1 读取目标项目规则

优先读取目标项目中的以下文件：

- `CLAUDE.md`
- `AGENTS.md`
- `.claude/rules/document-storage.md`
- `.claude/rules/markdown-format.md`
- `.claude/rules/code-usage.md`

如果不存在 Cadence 规则，则使用 skill 内置默认约定：

- 认知产物统一放入 `cadence/`。
- 按文档类型分配到 `analysis-docs`、`architecture`、`docs`、`models`、`plans`、`reports` 等目录。
- 文件名使用 `YYYY-MM-DD_文档类型_文档名称_v1.0.md`。

### 5.2 确认执行模式

skill 启动后必须询问用户选择：

| 模式 | 默认 | 说明 |
|------|------|------|
| 标准模式 | 是 | 生成项目级 bootstrap 认知文档 |
| 深度模式 | 否 | 在标准模式基础上，按核心模块或领域继续拆分文档 |
| 轻量模式 | 否 | 仅在项目过大、时间有限或 repomix 输出不可处理时降级使用 |

默认推荐标准模式。用户选择深度模式后，应生成更多模块级、领域级和风险级文档。

### 5.3 执行 repomix

默认使用：

```bash
npx repomix@latest
```

推荐将 repomix 输出写入：

```text
cadence/analysis-docs/YYYY-MM-DD_分析资料_repomix-output_v1.0.xml
```

当项目规模较大时，skill 应优先考虑使用以下 repomix 参数控制上下文规模：

- `--include`
- `--ignore`
- `--compress`
- `--split-output`
- `--token-count-tree`
- `--include-logs`
- `--include-diffs`

如果 `npx` 不可用，应提示用户先执行 `pre-check` 或安装 Node.js/npx。

如果 repomix 执行失败，应记录失败原因和建议重试命令，不继续编造分析文档。

### 5.4 分析 repomix 输出

分析重点：

- 技术栈与运行环境。
- 顶层目录结构。
- 模块边界。
- 核心业务域。
- 依赖关系与调用方向。
- 数据模型与持久化线索。
- 构建、测试、格式化和检查命令。
- 风险区域与遗留陷阱。
- 未确认信息。

所有不确定内容必须标记为：

- `UNKNOWN`
- `TODO`
- `NEED_CONFIRMATION`

### 5.5 生成 Cadence 产物

所有产物必须写入目标项目 `cadence/` 目录，不生成 `.ai/`。

标准模式建议生成：

| 路径 | 内容 |
|------|------|
| `cadence/analysis-docs/YYYY-MM-DD_分析报告_Legacy项目Bootstrap_v1.0.md` | bootstrap 总报告 |
| `cadence/architecture/YYYY-MM-DD_架构文档_系统总览_v1.0.md` | 系统架构总览 |
| `cadence/architecture/YYYY-MM-DD_架构文档_模块地图_v1.0.md` | 模块边界与模块关系 |
| `cadence/docs/YYYY-MM-DD_开发文档_构建测试画像_v1.0.md` | 构建、测试、检查命令画像 |
| `cadence/models/YYYY-MM-DD_数据模型_领域与数据初稿_v1.0.md` | 数据模型与领域概念初稿 |
| `cadence/docs/YYYY-MM-DD_约束文档_风险区域与遗留陷阱_v1.0.md` | 高风险区域、耦合点、遗留陷阱 |
| `cadence/docs/YYYY-MM-DD_术语表_业务与技术术语_v1.0.md` | 术语表 |
| `cadence/plans/YYYY-MM-DD_计划文档_Legacy后续调研_v1.0.md` | 后续调研计划 |

深度模式额外生成：

| 路径 | 内容 |
|------|------|
| `cadence/architecture/YYYY-MM-DD_架构文档_<模块名>模块分析_v1.0.md` | 关键模块级分析 |
| `cadence/models/YYYY-MM-DD_数据模型_<领域名>领域模型_v1.0.md` | 核心领域模型 |
| `cadence/analysis-docs/YYYY-MM-DD_分析报告_<模块名>风险分析_v1.0.md` | 模块级风险分析 |
| `cadence/plans/YYYY-MM-DD_计划文档_<领域名>后续调研_v1.0.md` | 领域级后续调研计划 |

如果某类信息没有足够证据，不应生成空洞文档。可以在 bootstrap 总报告中记录未生成原因。

### 5.6 更新 CLAUDE.md 与 AGENTS.md

产物生成完成后，必须更新目标项目的 `CLAUDE.md` 与 `AGENTS.md`。

更新方式不是把分析内容全文塞入入口文档，而是新增“Legacy 项目认知”或“渐进式项目认知加载”区域，指向 `cadence/` 下的入口文档和任务相关文档。

推荐结构：

```markdown
## Legacy 项目认知

本项目已完成 Legacy Bootstrap。后续执行任务前，应按任务类型渐进式读取 `cadence/` 下的项目认知文档。

### 首选入口

- `cadence/analysis-docs/...Legacy项目Bootstrap...md`
- `cadence/architecture/...系统总览...md`
- `cadence/architecture/...模块地图...md`

### 修改代码前必须读取

- `cadence/docs/...风险区域与遗留陷阱...md`
- `cadence/docs/...构建测试画像...md`
- 与当前任务相关的模块、领域或风险分析文档

### 使用规则

- 不确定内容以文档中的 `UNKNOWN`、`TODO`、`NEED_CONFIRMATION` 标记为准。
- 不得把 bootstrap 初稿视为绝对事实。
- 如发现文档与代码不一致，应优先相信当前代码，并更新对应 Cadence 文档。
```

`CLAUDE.md` 面向 Claude Code，`AGENTS.md` 面向 Codex 和其他通用 Agent。两者内容应保持一致，但措辞可以分别适配。

如果目标项目缺少 `CLAUDE.md` 或 `AGENTS.md`，skill 应按 Cadence 初始化规则提示或创建对应入口文件。

### 5.7 输出 bootstrap 摘要

完成后输出：

- repomix 输出文件路径。
- 生成的 Cadence 文档列表。
- 更新的入口文档列表。
- 已确认事实摘要。
- `UNKNOWN` / `TODO` / `NEED_CONFIRMATION` 摘要。
- 建议下一步。

## 6. 错误处理

| 场景 | 处理方式 |
|------|----------|
| 当前目录不是项目根目录 | 提醒用户确认当前工作目录，不继续执行 |
| `npx` 不可用 | 提示执行 `pre-check` 或安装 Node.js/npx |
| repomix 执行失败 | 记录失败原因和重试命令，不编造分析 |
| repomix 输出过大 | 建议使用 `--compress`、`--include`、`--ignore`、`--split-output` |
| `cadence/` 不存在 | 按需创建对应子目录 |
| `CLAUDE.md` 或 `AGENTS.md` 不存在 | 提示或创建入口文件 |
| 信息证据不足 | 标记 `UNKNOWN`、`TODO` 或 `NEED_CONFIRMATION` |

## 7. 质量标准

实现完成后应满足：

- `legacy-bootstrap` skill 位于 `cadence-init/skills/legacy-bootstrap/SKILL.md`。
- `legacy-bootstrap` command 位于 `cadence-init/commands/legacy-bootstrap.md`。
- skill frontmatter 中 `name` 等于目录名。
- command 能清晰指向 skill。
- skill 明确使用本地当前项目作为输入。
- skill 默认使用 `npx repomix@latest`。
- skill 明确标准模式、深度模式和轻量降级模式。
- skill 明确所有产物写入 `cadence/`。
- skill 明确更新 `CLAUDE.md` 与 `AGENTS.md`。
- skill 明确不编造未知业务事实。

## 8. 验证方式

由于本次主要产物是 Markdown skill 与 command，应使用以下方式验证：

1. 检查新增文件路径是否正确。
2. 检查 `SKILL.md` frontmatter 是否包含正确的 `name` 和 `description`。
3. 检查 command 是否能指向 `legacy-bootstrap` skill。
4. 检查文档中没有把远程仓库作为默认输入。
5. 检查文档中没有要求生成 `.ai/`。
6. 检查 repomix 命令与 Cadence 输出目录描述一致。
7. 检查 `CLAUDE.md` 与 `AGENTS.md` 渐进式认知加载更新为必做项。

## 9. 后续实施建议

实施阶段应按以下顺序进行：

1. 新增 `cadence-init/skills/legacy-bootstrap/SKILL.md`。
2. 新增 `cadence-init/commands/legacy-bootstrap.md`。
3. 检查 Markdown 格式和 frontmatter。
4. 运行基本文件存在性验证。
5. 汇报目标路径与验证结果。
