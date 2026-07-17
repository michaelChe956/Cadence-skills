---
name: knowledge-base-overview
description: "Use when 需要将 Schema 4.0 KnowledgeBase 的基础信息、接口、页面、服务、字段级数据模型、配置快照、证据和变更历史整理成 Coding Agent 项目导航，或安全接入 CLAUDE.md、AGENTS.md 与项目级 KnowledgeBase 使用规则。"
---

# KnowledgeBase 项目概览

## 概述

把 Schema 4.0 领域技能产物整理成 Coding Agent 的首选入口，提供项目边界、核心流程、一级导航、领域术语、常见修改场景和待确认项。入口只保留摘要与导航；只维护稳定标记内的代理入口，不覆盖目标项目已有规则。

## 必读资源

- 更新代理入口前读取 `references/rules-integration-guide.md`。
- 生成项目概览时使用 `assets/project-overview-template.md`。
- 生成术语表时使用 `assets/domain-glossary-template.md`。
- 生成待确认清单时使用 `assets/open-questions-template.md`。
- 生成项目规则时使用 `assets/knowledge-base-usage-template.md`。
- 需要参考完整用法时读取 `references/demo.md`。

## 前置输入

只接受 Schema 4.0 KnowledgeBase，优先读取：

- `cadence/knowledge-base/manifest.yaml`（必须为 Schema 4.0）
- `cadence/knowledge-base/base-information.md`
- `cadence/knowledge-base/development-guide.md`
- `cadence/knowledge-base/interfaces/README.md`
- `cadence/knowledge-base/pages/README.md`
- `cadence/knowledge-base/services/`
- `cadence/knowledge-base/data-models/README.md`
- `cadence/knowledge-base/configurations/README.md`
- `cadence/knowledge-base/evidence/`
- `cadence/knowledge-base/change-history.md`
- `cadence/knowledge-base/open-questions.md`
- 用户提供的术语、架构和业务流程资料

Manifest 不存在或 Schema 不是 4.0 时停止并引导使用 `knowledge-base-bootstrap`。缺少某个适用领域文档时，不得把概览技能变成重复的全仓分析技能；记录缺失并引导执行对应领域技能。不适用领域按 Manifest 跳过。

## 强制规则

- 概览是导航与摘要，不复制领域文档全文。
- 项目入口不得复制字段清单、全部配置键或领域文档明细。
- 业务流程必须能够追踪到页面、API、服务或模块、表、配置或中间件证据。
- 用户提供的术语与代码候选术语分开标记。
- 知识库与源码冲突时，概览必须引导回到来源验证。
- 任务开始前必须先使用 `knowledge-base-context` 获取渐进式任务上下文。
- 表相关任务必须读取字段级表文档和当前结构证据；配置相关任务必须读取服务配置文档和当前快照证据。
- 变更完成后必须由用户显式指定唯一变更标识，并在唯一合法目录 `cadence/knowledge-base/user-input/updates/CHANGE-变更标识/` 准备完整变更包，再由 `knowledge-base-update` 消费后执行 Update。
- 只更新 `CLAUDE.md`、`AGENTS.md` 中的稳定管理区块。
- 管理标记损坏、重复或嵌套时停止覆盖并写入待确认项。
- 用户自定义详细规则写入 `cadence/project-rules/knowledge-base-usage.md`。
- 不修改目标项目的框架内置规则目录。

## 工作流程

### 1. 汇总项目边界

用简洁文字说明：

- 项目解决什么问题
- 系统包含哪些仓库、服务和前端应用
- 系统明确不负责什么
- 主要外部系统和中间件
- 当前分析分支、基线和覆盖范围

无法由用户资料或代码证据确认的业务定位必须标记为推断。

### 2. 建立导航

README 必须直接提供以下一级导航，顺序保持稳定：

```text
base-information.md
development-guide.md
interfaces/README.md
pages/README.md
services/
data-models/README.md
configurations/README.md
evidence/
change-history.md
open-questions.md
```

一级入口下面可以链接到服务、接口、页面、表、配置和证据子文档，但不得把子文档明细复制到 README。

### 3. 整理核心业务流程

优先选择三到五条对项目最重要且证据充分的流程，使用稳定 ID 串联：

```text
PAGE → API → SERVICE/MODULE → TABLE → CONFIGURATION/MIDDLEWARE
```

允许根据实际项目省略不适用节点或补充 ROUTE、EVENT 等旁路节点，但稳定主链必须支持 PAGE、API、SERVICE/MODULE、TABLE 和 CONFIGURATION/MIDDLEWARE。记录入口、主要步骤、数据变化、配置影响、异步边界、失败处理和证据。证据不足的流程放入待确认清单，不用推测补齐。

### 4. 整理领域术语

每个术语记录：

- 中文或英文名称
- 缩写和同义词
- 项目内含义
- 适用模块或流程
- 与通用含义的差异
- 来源、证据和可信度

用户提供的行业解释优先标记 `[用户提供]`；仅从代码命名提取的候选标记 `[合理推断]`。

### 5. 生成常见修改场景

至少覆盖：

- 字段变更：读取字段级表文档、关联 API/页面和当前结构证据。
- SQL/Mapper 变更：读取表文档、SQL/Mapper 证据和服务调用关系。
- 配置键变更：读取服务配置文档、配置索引和当前快照证据。
- Profile/Feature Flag 变更：读取环境差异、启用条件和当前快照证据。
- API 参数变更：读取接口主文档、调用方、服务和数据模型影响关系。
- 页面字段变更：读取页面文档、API 参数和字段映射关系。
- 中间件配置变化：读取配置文档、中间件证据、依赖服务和验证入口。

每个场景列出必读文档、主要入口、影响关系和验证指南链接。不得为项目不存在的工具创造命令。

### 6. 整理待确认项

按级别分类：

- 阻断：影响完整模式结论
- 高：影响外部暴露、安全、数据或关键流程
- 中：影响局部业务语义或关系
- 低：补充说明和示例

每项记录问题、影响、证据、建议确认人或资料类型和处理状态。没有 CODEOWNERS 或用户资料时不得猜测负责人。

### 7. 生成知识库入口

生成或更新：

- `cadence/knowledge-base/README.md`（入口索引）
- `cadence/knowledge-base/domain-glossary.md`
- `cadence/knowledge-base/open-questions.md`
- `cadence/project-rules/knowledge-base-usage.md`

`README.md` 作为 Coding Agent 首选入口，保持短小，只提供项目摘要、读取顺序、覆盖范围和一级导航，不复制字段清单、全部配置键或领域文档正文。

### 8. 更新 CLAUDE.md 与 AGENTS.md

使用稳定标记：

```markdown
<!-- cadence-knowledge-base:start -->
## 项目 KnowledgeBase

需求澄清、Design、Plan、Coding、Testing、Review 或 Debug 前，先使用 `knowledge-base-context` 获取最小任务上下文。
修改代码前读取 `cadence/knowledge-base/README.md`，并按任务范围读取相关文档。
表相关任务读取字段级表文档和当前结构证据；配置相关任务读取服务配置文档和当前快照证据。
变更完成后，由用户显式指定唯一变更标识，在 `cadence/knowledge-base/user-input/updates/CHANGE-变更标识/` 准备五份不可合并或省略的固定文件，再使用 `knowledge-base-update` 执行 Update。
<!-- cadence-knowledge-base:end -->
```

处理规则：

1. 文件不存在时创建最小入口文件。
2. 文件存在且没有管理区块时，在不破坏原结构的位置追加区块。
3. 管理区块存在且完整时，只更新区块内部。
4. 标记损坏、重复或嵌套时不写入，记录高优先级待确认项。
5. 不复制完整知识库到代理入口。

### 9. 更新 manifest

登记：

- 概览、术语、待确认和项目规则文档
- 当前分支与基线
- 执行模式和覆盖范围
- 待确认项数量
- 大型项目子文档索引

## Coding Agent 使用原则

项目规则至少表达：

1. 修改代码前先读知识库入口。
2. 每个任务开始前先使用 `knowledge-base-context`，按任务渐进读取相关领域文档，不一次加载全部大型文档。
3. 表相关任务读取 `data-models/README.md`、字段级表文档及 `evidence/` 中的当前结构证据。
4. 配置相关任务读取 `configurations/README.md`、服务配置文档及 `evidence/` 中的当前快照证据。
5. 知识库是事实索引，不替代源码、DDL、有效配置和当前证据。
6. `[合理推断]` 与 `[待人工确认]` 不能当作确定事实。
7. 知识库与当前实现冲突时回到来源验证并更新知识库。
8. 影响字段、SQL/Mapper、配置、Profile/Feature Flag、API 参数、页面字段或中间件后，必须由用户显式指定唯一变更标识，在 `cadence/knowledge-base/user-input/updates/CHANGE-变更标识/` 准备符合固定契约的完整变更包，并使用 `knowledge-base-update` 执行 Update。

## 强制变更包契约

完整变更包的变更标识必须由用户显式指定，唯一合法根目录为：

```text
cadence/knowledge-base/user-input/updates/CHANGE-变更标识/
```

该根目录始终包含以下五份固定文件，文件之间不得合并，也不得省略：

```text
change-summary.md
code-change.md
database-change.md
configuration-change.md
verification.md
```

附件只能提供补充证据，不能替代任何固定文件。即使数据库无变更，`database-change.md` 仍必须存在并说明无变更及判断依据；即使配置无变更，`configuration-change.md` 仍必须存在并说明无变更及判断依据。目录、文件和依据不完整时，不得调用 `knowledge-base-update` 或把 Update 标记为完成。

## 禁止行为

- 不覆盖或重写用户现有代理规则。
- 不在 `.claude/rules/` 等框架内置规则目录写入用户规则。
- 不把所有领域文档拼接成一个超长 README。
- 不在 README 中复制字段清单或全部配置键。
- 不根据类名和表名编造项目定位或业务流程。
- 不将低可信度术语定义写成正式业务定义。
- 不删除已解决问题的历史记录；应更新状态或转入变更历史。

## 完成条件

- Coding Agent 能从 README 导航到全部核心文档。
- README 直接提供 Schema 4.0 的十个一级导航入口，且只保留摘要和导航。
- 核心流程支持 `PAGE → API → SERVICE/MODULE → TABLE → CONFIGURATION/MIDDLEWARE` 稳定链路和证据。
- 术语区分用户定义与代码推断。
- 待确认项按优先级整理。
- `CLAUDE.md`、`AGENTS.md` 只修改稳定区块。
- 项目规则明确 Context 前置、表与配置证据读取，以及唯一变更包目录、五份不可合并或省略的固定文件和 Update 要求。
