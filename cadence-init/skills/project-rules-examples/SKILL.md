---
name: project-rules-examples
description: "创建项目个性化规则模板：需求文档模板、设计文档模板、代码开发规范、测试规范"
---

# 个性化规则示例

## 概述

创建项目个性化规则模板，包括需求文档模板、设计文档模板、代码开发规范和测试规范。默认不需要人工交互即可完成模板初始化。

所有权边界：

- 本 Skill 只拥有 `cadence/project-rules/README.md` 与 `cadence/project-rules/examples/` 下五个模板目标文件。
- **绝不创建或修改 `CLAUDE.md` / `AGENTS.md`**：入口文件由 `rule-config` 唯一拥有；本 Skill 只做只读检查并报告 `skipped` / `needs-rule-config`。
- `cadence/project-rules/` 顶层的其他用户文件不属于本 Skill，不碰。

## 参数模式

支持以下调用方式：

```text
/project-rules-examples
/project-rules-examples no-interrupt
/project-rules-examples --no-interrupt
```

- 命令参数包含完整 token `no-interrupt` 或 `--no-interrupt`：进入 `no-interrupt` 模式。
- 未携带上述参数：进入普通模式，遵循目标文件存在则跳过、不覆盖和条件询问逻辑。
- 两种模式互斥；不得把 `no-interrupt` 模板合并规则应用到普通模式。

### no-interrupt 通用规则

- 禁止调用 `AskUserQuestion`、`request_user_input` 或等价用户提问工具。
- 禁止等待用户输入、设置交互超时或通过推荐默认值继续。
- 目标文件存在时由脚本按确定性章节合并处理；模型不得改写、重排或概括用户正文。
- 合并前必须保留项目已有内容；备份、写入或验证失败时立即报错终止。
- 失败报告必须包含失败文件、失败原因、已完成文件和恢复建议。

### no-interrupt 确定性章节合并（脚本）

no-interrupt 模式的全部写入由 `scripts/apply.py` 完成（`apply.sh` 为其 wrapper）；模型不做语义合并，不重写已存在文件。

执行：`bash <skill 目录>/scripts/apply.sh --project-root <项目根>`

| 脚本输出 | 含义 | 你的动作 |
|----------|------|----------|
| `created <路径>` | 目标原不存在，脚本已复制模板 | 仅 `design-template.md` 需要做项目事实定制（见第 3 步） |
| `pristine <路径>` | 目标与模板逐字节一致 | 该步骤视为完成 |
| `merged <路径>` | 目标存在且不同：脚本已按确定性章节合并写回（写入前已备份） | 该步骤视为完成 |
| `unchanged <路径>` | 目标存在且无需变更：零写入 | 该步骤视为完成 |
| `skipped CLAUDE.md/AGENTS.md` | 入口已含等价引用，脚本未写 | 该步骤视为完成 |
| `needs-rule-config CLAUDE.md/AGENTS.md` | 入口文件缺失或缺少引用 | 交给 `rule-config` 处理；本 Skill 不写入口文件，只记入报告 |

脚本保证的合并规则（模型不得绕过）：

- 章节身份 = 标题级别 + 去编号标题文本（NB-01）；围栏代码块内的 `#` 不识别为标题。
- 章节清单框架保证：模板有而目标缺失的章节，按模板原文追加到文件末尾。
- 有 `cadence/framework-state/` 基线且模板发生变化时，执行章节级三方合并：以用户文件章节顺序为骨架，用户未改的章节升级为最新模板，用户改过的章节正文保留，模板新增章节追加到末尾，框架新版冲突写入 stderr `pending` 提示；无基线时只做保守追加，不重写任何既有正文。
- 已存在章节正文用户所有：逐字保留（含空行、表格、围栏代码块与尾部空行），不重排、不改写、不压缩。
- 不生成“项目补充”章节；追加块之外的任何用户字节不被改动。
- 任何实际写入既有文件前，先备份到 `cadence/legacy/<14位时间戳>/cadence/project-rules/<相对路径>`。
- 幂等：第二次运行全部 `unchanged` / `pristine` / `skipped`，零写入、零备份。

### 失败与恢复

- 脚本对无法安全解析的文件（非空但无任何标题、围栏代码块未闭合、非 UTF-8 文本）保持原样并输出 `unchanged` 与 stderr 警告，不写、不删。
- 备份或写入失败时脚本立即终止（退出码 3）；按 `cadence/legacy/<时间戳>/` 中的写入前原像恢复。

## 无交互默认策略

> 本节仅适用于未携带 `no-interrupt` 或 `--no-interrupt` 的普通模式。

| 项 | 默认行为 |
|----|----------|
| 目录创建 | 自动创建 `cadence/project-rules/examples/` |
| 模板文件 | 缺失则创建，已存在则跳过不覆盖 |
| 项目事实 | 无法确认时保留模板中的待补充项，不阻塞初始化 |
| 入口引用 | 只读检查：已有等价引用报告 `skipped`；缺失报告 `needs-rule-config`，由 `rule-config` 处理 |
| 冲突处理 | 不覆盖用户已有文件，报告需人工处理项 |

## 人工交互策略

> 本节仅适用于未携带 `no-interrupt` 或 `--no-interrupt` 的普通模式。

默认不向用户提问。只有出现以下情况才进入人工交互：

| 触发条件 | 处理方式 |
|----------|----------|
| 用户明确要求覆盖已有模板文件 | 询问是否覆盖具体文件；无响应则不覆盖 |
| 用户要求根据真实项目事实定制模板但事实不足 | 询问一个最关键事实；无响应则保留待补充项 |

提问规则：

- 每次只问一个问题。
- 问题必须给出推荐默认选项。
- 如果运行环境支持自动超时，超时后采用推荐默认值。
- 如果无法等待用户输入，采用保守默认：不覆盖已有模板、保留待补充项。

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

1. **运行脚本快速路径** — `bash <skill 目录>/scripts/apply.sh --project-root <项目根>`（两种模式都先执行）
2. **README.md** — 脚本铺设/合并 `cadence/project-rules/README.md`
3. **requirement-template.md** — 需求文档模板
4. **design-template.md** — 设计文档模板；仅对本次 `created` 的文件做项目事实定制（见第 3 步生成要求）
5. **coding-standards.md** — 代码开发规范
6. **test-standards.md** — 测试规范
7. **入口引用检查（只读）** — 脚本输出 `skipped CLAUDE.md/AGENTS.md` 即完成；输出 `needs-rule-config` 时记入报告，由 `rule-config` 处理，本 Skill 不写入口文件

**下一步**：返回结果给 @cadencing skill 完成初始化

## 处理流程

### 0. 脚本快速路径（apply.sh）

执行 `bash <skill 目录>/scripts/apply.sh --project-root <项目根>`，按上方状态表分派。no-interrupt 模式必须先执行本步；脚本已完成的铺设/合并不得逐字重写。

### 1. 创建 README.md（普通模式手工路径）

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

**项目事实定制边界**：只对本次 `created`（脚本刚复制模板）的文件做项目事实定制；已存在文件（含 `pristine`、`merged`、`unchanged`）不重写、不重新定制——其中内容视为用户内容。

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

### 6. 入口引用检查（只读）

对项目根目录的 `CLAUDE.md` / `AGENTS.md` 只做等价引用检查（同时包含“项目个性化规则”且指向 `cadence/project-rules`）：

- 已有等价引用 → 报告 `skipped`。
- 文件缺失或缺少引用 → 报告 `needs-rule-config`，交给 `rule-config` 处理。

入口文件由 `rule-config` 唯一拥有；本 Skill 绝不创建、修改或向入口文件追加引用。

## 核心原则

- **可定制** — 用户可以根据项目需求选择和修改模板
- **完整性** — 提供完整的模板结构作为参考
- **实用性** — 模板应该能够直接使用或快速适配
- **零丢失** — 已存在文件的用户正文逐字保留；缺失章节只追加、不改写
- **无交互** — 默认不向用户提问；冲突项报告给用户后续处理
