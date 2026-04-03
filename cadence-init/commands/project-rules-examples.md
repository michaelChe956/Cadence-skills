---
name: project-rules-examples
description: "创建项目个性化规则模板：需求文档模板、设计文档模板、代码开发规范、测试规范"
---

# 个性化规则示例

## 概述

创建项目个性化规则模板，包括需求文档模板、设计文档模板、代码开发规范和测试规范。

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

**下一步**：返回结果给 @cadencing skill 完成初始化

## 处理流程

### 1. 创建 README.md

**文件路径**：`.claude/project-rules/README.md`

**文件内容**：`references/project-rules/README.md`

### 2. 创建 requirement-template.md

**文件路径**：`.claude/project-rules/examples/requirement-template.md`

**文件内容**：`references/project-rules/examples/requirement-template.md`
### 3. 创建 design-template.md

**文件路径**：`.claude/project-rules/examples/design-template.md`

**文件内容**：`references/project-rules/examples/design-template.md`

**生成要求**：

- 必须先输出“项目事实确认”章节（项目类型、技术栈、现有调用链、现有契约）
- 后端分层、前端分层、全栈分层均使用可替换占位，不得硬编码某一套层级
- 契约设计必须要求“沿用项目现有响应结构”，不能默认某种响应字段
- 必须提供“编码落地清单”，确保设计可以直接驱动 AI 实施

### 4. 创建 coding-standards.md

**文件路径**：`.claude/project-rules/examples/coding-standards.md`

**文件内容**：`references/project-rules/examples/coding-standards.md`

**生成要求**：

- 优先生成“项目级 AI 编码规范”而不是“通用语言代码风格”
- 必须包含：总体原则、项目事实、分层边界、接口/返回值、异常、日志、数据访问、测试验证、禁止事项、AI 执行清单
- 必须提醒用户根据当前项目真实实现补齐模板中的项目事实部分
- 禁止默认输出仅适用于前端或单体 Node 项目的内容

### 5. 创建 test-standards.md

**文件路径**：`.claude/project-rules/examples/test-standards.md`

**文件内容**：`references/project-rules/examples/test-standards.md`

### 6. 添加 CLAUDE.md 规则

在项目的 `CLAUDE.md` 文件中添加个性化规则引用，使 Claude Code 能够自动使用这些定制规则。

**目标文件**：项目根目录的 `CLAUDE.md`

**添加位置**：在 CLAUDE.md的最末位置，添加一个新的章节 `### 项目个性化规则`

**添加内容**：`references/project-rules/CLAUDE-RULE.md`

## 核心原则

- **可定制** — 用户可以根据项目需求选择和修改模板
- **完整性** — 提供完整的模板结构作为参考
- **实用性** — 模板应该能够直接使用或快速适配
