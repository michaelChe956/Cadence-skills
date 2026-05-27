---
name: legacy-bootstrap
description: "当需要为当前本地 legacy 项目建立 Cadence 项目认知时，使用 repomix bootstrap 并更新入口文档"
disable-model-invocation: true
---

# Legacy Bootstrap

## 概述

使用 `npx repomix@latest` 汇总当前本地 legacy 项目上下文，分析项目结构、架构、模块、依赖、风险和未知项，并将结果沉淀到目标项目的 `cadence/` 目录。

该 skill 属于 `cadence-init` 插件，面向已经在 Claude Code 或 Codex 中打开的本地 clone 项目。

## 核心原则

- 只处理当前打开的本地项目，不 clone 远程仓库。
- 默认使用 `npx repomix@latest`。
- 所有认知产物写入 `cadence/`，不生成 `.ai/`。
- 产物生成完成后必须更新 `CLAUDE.md` 与 `AGENTS.md`。
- 不直接重构业务代码。
- 不把未知业务事实写成确定结论。
- `--skill-generate` 只作为结构参考，不作为主流程。

## 何时使用

### 使用场景

- 用户要求为 legacy 项目初始化项目认知。
- 用户要求使用 repomix bootstrap 当前项目。
- 用户要求生成架构、模块、风险、构建测试画像等 Cadence 文档。
- 进入历史项目并计划修改前，需要先建立项目认知。
- 当前 Claude Code 或 Codex 已经打开目标项目的本地 clone。

### 不使用场景

- 目标是全新空项目，没有 legacy 代码或历史结构需要梳理。
- 用户只要求查看少量文件或回答局部问题。
- 用户明确要求不生成 Cadence 文档。
- 用户要求分析远程 GitHub 仓库，但没有提供或打开本地 clone。

## 检查清单

1. 确认当前目录是目标项目根目录。
2. 读取目标项目规则。
3. 确认执行模式。
4. 执行 repomix。
5. 必要时参考 skill-generate 输出结构，默认不执行 `--skill-generate`。
6. 分析项目认知。
7. 按证据生成 Cadence 候选产物。
8. 更新入口文档。
9. 输出 bootstrap 摘要。

## 执行模式

启动时先询问用户是否选择深度模式。未选择时使用标准模式；轻量模式只作为降级选项。

| 模式 | 使用时机 | 候选产物范围 |
|------|----------|----------|
| 标准模式 | 默认模式，适合多数 legacy bootstrap | 按证据生成总览、模块地图、构建测试画像、领域与数据初稿、风险区域、术语表、后续调研计划等候选产物 |
| 深度模式 | 用户明确选择，或项目复杂且需要更细颗粒度认知 | 在标准模式候选产物基础上，按证据拆分更多模块、领域、风险和调研文档 |
| 轻量模式 | 项目过大、时间有限或 repomix 输出不可处理时降级 | 保留核心事实、风险、未知项和下一步计划，减少拆分文档数量 |

## 处理流程

### 1. 确认目标项目根目录

读取目标项目规则前，必须先确认当前工作目录是目标项目根目录。判断信号包括：

- `.git`。
- 主项目清单或包管理文件，例如 `package.json`、`Cargo.toml`、`pyproject.toml`、`go.mod`、`pom.xml`、`build.gradle`。
- 常见项目配置文件，例如 `Makefile`、`README.md`、`tsconfig.json`、`vite.config.*`、`docker-compose.yml`。

如果无法判断当前目录是否为目标项目根目录，先询问用户确认；确认不是根目录时停止执行，提示用户在目标项目根目录重新运行，不要对上级目录或不确定目录写入产物。

### 2. 读取目标项目规则

在目标项目根目录优先读取：

- `CLAUDE.md`
- `AGENTS.md`
- `.claude/rules/document-storage.md`
- `.claude/rules/markdown-format.md`
- `.claude/rules/code-usage.md`
- `cadence/project-rules/README.md`

如果目标项目没有 Cadence 规则文件，使用默认目录约定：所有项目认知产物写入 `cadence/` 下对应子目录，入口规则写入根目录 `CLAUDE.md` 与 `AGENTS.md`。

读取规则时只采纳与当前 bootstrap 相关的约束；不得修改目标项目 `.claude/rules/` 中的框架规则文件。

### 3. 确认执行模式

向用户确认是否使用深度模式：

- 用户选择深度模式：在标准模式候选产物基础上，并按证据补充模块、领域、风险和调研拆分文档。
- 用户未选择或未明确要求：执行标准模式，按证据生成候选产物。
- repomix 输出过大、无法处理或时间受限：说明原因后降级为轻量模式。

### 4. 执行 repomix

基础命令：

```bash
npx repomix@latest --output cadence/analysis-docs/YYYY-MM-DD_分析资料_repomix-output_v1.0.xml
```

这是最小可运行命令，不应在实际项目中无判断地直接复制。执行时应优先按项目情况补充 `--ignore`，避免把旧 repomix 输出、历史分析产物、生成物、缓存和大型构建目录重新打包。

执行前确保 `cadence/analysis-docs/` 存在。项目较大时优先考虑以下选项，而不是放弃 bootstrap：

- `--compress`
- `--include`
- `--ignore`
- `--split-output`
- `--token-count-tree`
- `--include-logs`
- `--include-diffs`

建议使用 `--ignore` 避免把已有 repomix 输出、历史分析产物、生成物、缓存和大型构建目录重新打包。不要整体排除 `cadence/`，因为入口规则和部分项目文档可能是有效证据；应重点排除旧 repomix 输出和明显产物。

示例：

```bash
npx repomix@latest \
  --ignore "**/repomix-output*.xml,cadence/analysis-docs/*repomix-output*.xml,cadence/analysis-docs/*分析资料*.xml,node_modules,dist,build,coverage,.next,.turbo,target,tmp,cache,.cache" \
  --output cadence/analysis-docs/YYYY-MM-DD_分析资料_repomix-output_v1.0.xml
```

如果 `npx` 不可用，提示用户先运行 `/pre-check` 或安装 Node.js/npx。

如果 repomix 失败，必须记录失败原因、已执行命令和建议重试命令；不得在缺少 repomix 证据时编造分析文档。

### 5. 参考 repomix skill-generate

`--skill-generate` 是 repomix 的实验能力，只能作为结构参考。

可参考内容：

- 目录组织方式。
- 触发描述写法。
- 上下文拆分方式。
- 将代码库认知封装为 Agent 入口的表达方式。

禁止事项：

- 不能把 `--skill-generate` 作为本 skill 的默认主流程。
- 不能把 `--skill-generate` 输出直接作为最终 `legacy-bootstrap` skill。
- 不能把 `--skill-generate` 输出直接作为 Cadence 项目认知产物。

### 6. 分析项目认知

基于 repomix 输出、目标项目规则和必要的本地文件读取，整理以下内容：

- 技术栈。
- 运行环境。
- 目录结构。
- 模块边界。
- 核心业务域。
- 依赖关系。
- 数据模型线索。
- 构建测试命令。
- 风险区域。
- 未知信息。

不得编造业务知识。证据不足的信息必须标记为 `UNKNOWN`、`TODO` 或 `NEED_CONFIRMATION`。

### 7. 生成 Cadence 产物

所有产物必须写入 `cadence/`，不生成 `.ai/`。

#### 标准模式候选产物

标准模式也必须按证据充分性生成产物。下表是默认候选产物清单，不代表必须全量生成 8 个文档；证据不足时不要生成空文档，应在 bootstrap 总报告中记录未生成的文档、原因和后续确认方式。

| 路径 | 内容 |
|------|------|
| `cadence/analysis-docs/YYYY-MM-DD_分析报告_Legacy项目Bootstrap_v1.0.md` | bootstrap 总报告、证据来源、事实摘要、未知项和后续建议 |
| `cadence/architecture/YYYY-MM-DD_架构文档_系统总览_v1.0.md` | 系统目标、技术栈、运行形态、关键依赖和整体架构 |
| `cadence/architecture/YYYY-MM-DD_架构文档_模块地图_v1.0.md` | 目录结构、模块边界、调用关系和维护入口 |
| `cadence/docs/YYYY-MM-DD_开发文档_构建测试画像_v1.0.md` | 构建、测试、启动、检查命令和环境要求 |
| `cadence/models/YYYY-MM-DD_数据模型_领域与数据初稿_v1.0.md` | 领域对象、数据模型线索、持久化与接口数据结构 |
| `cadence/docs/YYYY-MM-DD_约束文档_风险区域与遗留陷阱_v1.0.md` | 高风险区域、遗留陷阱、修改前注意事项 |
| `cadence/docs/YYYY-MM-DD_术语表_业务与技术术语_v1.0.md` | 业务术语、技术术语、缩写和代码命名含义 |
| `cadence/plans/YYYY-MM-DD_计划文档_Legacy后续调研_v1.0.md` | 后续调研任务、待确认问题和优先级 |

#### 深度模式额外候选产物

| 路径 | 内容 |
|------|------|
| `cadence/architecture/YYYY-MM-DD_架构文档_<模块名>模块分析_v1.0.md` | 单个模块的职责、边界、依赖和修改风险 |
| `cadence/models/YYYY-MM-DD_数据模型_<领域名>领域模型_v1.0.md` | 单个领域的数据结构、实体关系和未知项 |
| `cadence/analysis-docs/YYYY-MM-DD_分析报告_<模块名>风险分析_v1.0.md` | 单个模块的风险点、历史包袱和验证建议 |
| `cadence/plans/YYYY-MM-DD_计划文档_<领域名>后续调研_v1.0.md` | 单个领域的后续调研计划和确认问题 |

证据不足时不生成空洞文档，在 bootstrap 总报告中说明未生成原因。

### 8. 更新入口文档

产物完成后必须更新目标项目根目录的 `CLAUDE.md` 与 `AGENTS.md`。

更新方式不是复制完整分析，而是新增 `Legacy 项目认知` 或 `渐进式项目认知加载` 区域，指向 Cadence 入口文档和任务相关文档。

推荐 Markdown 结构：

```markdown
## Legacy 项目认知

### 首选入口

- `cadence/analysis-docs/YYYY-MM-DD_分析报告_Legacy项目Bootstrap_v1.0.md`
- `cadence/architecture/YYYY-MM-DD_架构文档_系统总览_v1.0.md`
- `cadence/architecture/YYYY-MM-DD_架构文档_模块地图_v1.0.md`

### 修改代码前必须读取

- 构建与测试：`cadence/docs/YYYY-MM-DD_开发文档_构建测试画像_v1.0.md`
- 风险区域：`cadence/docs/YYYY-MM-DD_约束文档_风险区域与遗留陷阱_v1.0.md`
- 相关模块或领域文档：按当前任务选择读取 `cadence/architecture/`、`cadence/models/`、`cadence/docs/` 中的对应文件

### 使用规则

- 不确定内容以 `UNKNOWN`、`TODO`、`NEED_CONFIRMATION` 为准。
- 不得把 bootstrap 初稿视为绝对事实。
- 发现文档与代码不一致时，优先相信当前代码，并更新对应 Cadence 文档。
```

如果 `CLAUDE.md` 或 `AGENTS.md` 不存在，应创建最小入口文档，并保留上述渐进式加载区域。

### 9. 输出 bootstrap 摘要

完成后向用户汇报：

- repomix 输出文件路径。
- 生成的 Cadence 文档列表。
- 更新的入口文档列表。
- 已确认事实摘要。
- `UNKNOWN`、`TODO`、`NEED_CONFIRMATION` 摘要。
- 建议下一步。

## 错误处理

| 错误 | 处理方式 |
|------|----------|
| 当前目录不是项目根目录 | 先检查 `.git`、主项目清单文件和常见配置文件，例如 `package.json`、`Cargo.toml`、`pyproject.toml`、`go.mod`、`pom.xml`、`build.gradle`、`Makefile`、`README.md` 等；无法判断时先询问用户确认。确认不是根目录后停止执行，提示用户在目标项目根目录重新运行；不要对上级目录或不确定目录写入产物 |
| `npx` 不可用 | 提示用户运行 `/pre-check` 或安装 Node.js/npx；不要继续执行 repomix |
| repomix 失败 | 记录失败原因、命令和建议重试命令；不要编造分析文档 |
| repomix 输出过大 | 优先使用 `--compress`、`--include`、`--ignore`、`--split-output`、`--token-count-tree` 缩小范围；必要时降级轻量模式 |
| `cadence/` 不存在 | 创建 `cadence/` 及所需子目录，并遵循目标项目文档存储规则 |
| `CLAUDE.md` 或 `AGENTS.md` 不存在 | 创建最小入口文档，加入渐进式项目认知加载区域 |
| 信息证据不足 | 使用 `UNKNOWN`、`TODO`、`NEED_CONFIRMATION` 标记，并在总报告中列入待确认问题 |

## 完成标准

- 已确认当前目录是目标项目根目录。
- 已读取目标项目规则或明确使用默认目录约定。
- 已执行 repomix，或已记录无法执行的原因与重试方式。
- 已基于证据生成 Cadence 项目认知产物。
- 已更新 `CLAUDE.md` 与 `AGENTS.md` 的渐进式加载入口。
- 未生成 `.ai/`。
- 未把未知业务事实写成确定结论。
- 已向用户输出 bootstrap 摘要。
