---
name: project-rules-examples
description: "创建项目个性化规则模板：需求文档模板、设计文档模板、代码开发规范、测试规范"
---

# 个性化规则示例

## 概述

创建项目个性化规则模板，包括需求文档模板、设计文档模板、代码开发规范和测试规范。默认不需要人工交互即可完成模板初始化。

## 无交互默认策略

| 项 | 默认行为 |
|----|----------|
| 目录创建 | 自动创建 `cadence/project-rules/examples/` |
| 模板文件 | 缺失则创建，已存在则跳过不覆盖 |
| 项目事实 | 无法确认时保留模板中的待补充项，不阻塞初始化 |
| CLAUDE.md 引用 | 缺失则追加，已存在则跳过 |
| AGENTS.md 引用 | 缺失则追加，已存在则跳过 |
| 冲突处理 | 不覆盖用户已有文件，报告需人工处理项 |

## 人工交互策略

默认不向用户提问。只有出现以下情况才进入人工交互：

| 触发条件 | 处理方式 |
|----------|----------|
| 用户明确要求覆盖已有模板文件 | 询问是否覆盖具体文件；无响应则不覆盖 |
| CLAUDE.md / AGENTS.md 中存在冲突的项目规则路径 | 询问是否追加新引用或保留旧引用；无响应则保留旧引用并报告 |
| 用户要求根据真实项目事实定制模板但事实不足 | 询问一个最关键事实；无响应则保留待补充项 |

提问规则：
- 每次只问一个问题。
- 问题必须给出推荐默认选项。
- 如果运行环境支持自动超时，超时后采用推荐默认值。
- 如果无法等待用户输入，采用保守默认：不覆盖已有模板、不删除已有引用、保留待补充项。

生成规则时必须遵循以下要求：

- 模板内容要尽量贴近当前项目技术栈、目录结构、历史实现方式，不要输出空泛的通用模板。
- `design-template.md` 必须先确认“项目事实”（项目类型、现有调用链、契约格式、异常体系），再写方案细节。
- `design-template.md` 禁止写死后端固定层级（例如固定 `controller -> ability -> busi -> ...`）或固定响应结构（例如固定 `respCode/respDesc` 或固定 `code/message/data`）。
- 设计模板必须兼容前端、后端、全栈三类项目，按项目类型选择章节深度。
- `coding-standards.md` 必须优先描述“项目事实”和“AI 执行规则”，而不是只给语言通用风格清单。
- 若项目是 Java / Spring / MyBatis、多模块后端工程，不要输出偏前端 React 风格示例。
- 若项目已有明确的返回结构、异常体系、日志框架、DAO/Mapper 命名，模板中必须体现这些约束。
- 若暂时无法确认项目事实，模板中应显式留出待补充项，并提醒用户基于代码库补全，不要假设不存在的规范。

## 检查清单

你必须为以下每个项目创建任务并按顺序完成：

1. **创建 README.md** — 创建项目个性化规则说明文档
2. **创建 requirement-template.md** — 需求文档模板
3. **创建 design-template.md** — 设计文档模板
4. **创建 coding-standards.md** — 代码开发规范
5. **创建 test-standards.md** — 测试规范
6. **添加 CLAUDE.md 规则** — 在项目 CLAUDE.md 中添加个性化规则引用
7. **添加 AGENTS.md 规则** — 在项目 AGENTS.md 中添加个性化规则引用

**下一步**：返回结果给 @cadencing skill 完成初始化

## 处理流程

### 1. 创建 README.md

**文件路径**：`cadence/project-rules/README.md`

**文件内容**：`references/project-rules/README.md`

**增量行为**：如果目标文件已存在，跳过并报告，不覆盖。

### 2. 创建 requirement-template.md

**文件路径**：`cadence/project-rules/examples/requirement-template.md`

**文件内容**：`references/project-rules/examples/requirement-template.md`

**增量行为**：如果目标文件已存在，跳过并报告，不覆盖。

### 3. 创建 design-template.md

**文件路径**：`cadence/project-rules/examples/design-template.md`

**文件内容**：`references/project-rules/examples/design-template.md`

**生成要求**：

- 必须先输出“项目事实确认”章节（项目类型、技术栈、现有调用链、现有契约）
- 后端分层、前端分层、全栈分层均使用可替换占位，不得硬编码某一套层级
- 契约设计必须要求“沿用项目现有响应结构”，不能默认某种响应字段
- 必须提供“编码落地清单”，确保设计可以直接驱动 AI 实施
- 无法确认项目事实时，保留待补充项，不向用户提问，不阻塞初始化

**增量行为**：如果目标文件已存在，跳过并报告，不覆盖。

### 4. 创建 coding-standards.md

**文件路径**：`cadence/project-rules/examples/coding-standards.md`

**文件内容**：`references/project-rules/examples/coding-standards.md`

**生成要求**：

- 优先生成“项目级 AI 编码规范”而不是“通用语言代码风格”
- 必须包含：总体原则、项目事实、分层边界、接口/返回值、异常、日志、数据访问、测试验证、禁止事项、AI 执行清单
- 必须提醒用户根据当前项目真实实现补齐模板中的项目事实部分
- 禁止默认输出仅适用于前端或单体 Node 项目的内容
- 无法确认项目事实时，保留待补充项，不向用户提问，不阻塞初始化

**增量行为**：如果目标文件已存在，跳过并报告，不覆盖。

### 5. 创建 test-standards.md

**文件路径**：`cadence/project-rules/examples/test-standards.md`

**文件内容**：`references/project-rules/examples/test-standards.md`

**增量行为**：如果目标文件已存在，跳过并报告，不覆盖。

### 6. 添加 CLAUDE.md 规则引用

在项目的 `CLAUDE.md` 文件中添加个性化规则引用。

**目标文件**：项目根目录的 `CLAUDE.md`

**添加位置**：在 CLAUDE.md 的"强制规则"章节中 `### 7. 项目个性化规则（强制规则）` 部分

**添加内容**：`references/project-rules/CLAUDE-RULE.md`（已更新为强制约束 + 摘要引用格式）

**注意事项**：
- 确保 CLAUDE.md 中已有 `### 7. 项目个性化规则（强制规则）` 摘要引用
- `project-rules/` 是用户自定义规则的唯一合法目录
- 禁止将用户自定义规则写入 `.claude/rules/` 目录
- 如果 CLAUDE.md 中已存在等价引用，跳过不重复追加
- 如果 CLAUDE.md 不存在，创建最小 CLAUDE.md 并写入项目个性化规则引用

### 7. 添加 AGENTS.md 规则引用

在项目的 `AGENTS.md` 文件中添加个性化规则引用。

**目标文件**：项目根目录的 `AGENTS.md`

**添加内容**：与 CLAUDE.md 保持语义一致，强调：
- 用户自定义规则只能存放在 `cadence/project-rules/` 目录
- 禁止在 `.claude/rules/` 目录中添加用户自定义规则
- 禁止直接修改 `.claude/rules/` 目录下的框架内置规则文件
- 详见 `cadence/project-rules/README.md`

**无交互行为**：
- 如果 AGENTS.md 中已存在等价引用，跳过不重复追加。
- 如果 AGENTS.md 不存在，创建最小 AGENTS.md 并写入项目个性化规则引用。
- 不覆盖 AGENTS.md 中已有内容。

## 核心原则

- **可定制** — 用户可以根据项目需求选择和修改模板
- **完整性** — 提供完整的模板结构作为参考
- **实用性** — 模板应该能够直接使用或快速适配
- **无交互** — 默认不向用户提问；已有内容不覆盖，冲突项报告给用户后续处理
