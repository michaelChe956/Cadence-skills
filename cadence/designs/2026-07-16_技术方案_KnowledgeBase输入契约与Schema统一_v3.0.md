# KnowledgeBase 输入契约与 Schema 统一技术方案

## 1. 文档信息

| 项目 | 内容 |
|------|------|
| 文档版本 | v3.0 |
| 编写日期 | 2026-07-16 |
| 适用范围 | `cadence-init/skills/knowledge-base-*` |
| 主要目标 | 统一用户输入、分析范围、输出 Schema、API 分类和跨运行时交互 |

## 2. 背景与目标

当前 KnowledgeBase Skills 同时存在目录命名不一致、核心产物可选性冲突、API 单接口测试流程覆盖全量职责、数据库在线验证、运行时工具名不兼容和项目特定规则混入通用 Skill 等问题。

本次调整目标：

1. 以目标项目中的用户输入文档作为唯一分析范围来源。
2. 以 `base-info.md` 作为强制入口，输入不完整时停止分析并返回模板。
3. 统一使用 `cadence/knowledge-base/` 输出 Schema，不处理旧目录。
4. 明确用户提供的接口清单是全部对外能力的权威清单。
5. 支持 API 全量分析与指定能力分析，不因单接口测试缩减 Skill 职责。
6. 数据库分析只使用用户 DDL、代码、Mapper、SQL、Entity 和配置，不连接数据库。
7. 保留接口 Demo 作为格式参考，缺失字段不阻断生成。
8. 统一 Claude Code 与 Codex 的用户交互降级策略。

## 3. 设计原则

- 用户输入决定范围，Skill 不自行扩大范围。
- 缺失输入先报告，不生成不可控的半成品。
- 用户提供的对外能力清单优先于代码命名推断。
- 代码用于验证实现、状态和调用链，不用于推翻用户明确的对外分类。
- 无证据字段允许为空、`未提供`、`未发现` 或 `不适用`。
- 项目特定事实进入 KnowledgeBase 和证据索引，不自动升级为项目规则。
- 所有进度和状态进入 Manifest 与领域索引，不依赖运行时任务或记忆目录。

## 4. 用户输入目录

### 4.1 插件模板目录

插件只保留通用模板：

```text
cadence-init/skills/knowledge-base-bootstrap/user-input/
├── base-info.md
├── project-scope.md
├── database-ddl.sql
├── middleware-scope.md
├── api-scope.md
└── page-scope.md
```

不得在插件模板目录中保留具体项目的工程清单、真实 DDL、接口注册表、页面菜单或环境资料。

### 4.2 目标项目输入目录

用户在目标项目提供实际资料：

```text
cadence/knowledge-base/user-input/
├── base-info.md
├── project-scope.md
├── database-ddl.sql
├── middleware-scope.md
├── api-scope.md
└── page-scope.md
```

该目录属于用户输入区。Bootstrap 和领域 Skills 只能读取，不得覆盖、格式化或补写用户资料。

## 5. base-info.md 输入契约

### 5.1 强制章节

`base-info.md` 必须包含：

1. 工程信息。
2. 数据模型。
3. 中间件。
4. 接口。
5. 页面。

每个章节必须声明状态。状态为 `全量` 或 `指定` 时必须提供引用文件；状态为 `不适用` 时必须说明原因。有效状态为：

- `全量`：在已声明工程范围内全盘分析该领域。
- `指定`：只分析引用文件中列出的范围。
- `不适用`：明确跳过该领域。

空白、状态无法识别、链接文件不存在或指定范围为空均视为输入缺失。

### 5.2 接口章节示例

```markdown
### 接口

- 对外能力清单：[接口清单](./api-scope.md)
- 执行范围：全量
- 指定能力：无
```

接口状态不是 `不适用` 时，接口清单文件必须存在。未列出具体指定能力但执行范围为 `全量`，表示分析全部对外能力以及所选工程内发现的对内能力。

### 5.3 缺失处理

Bootstrap 在任何分析前完成输入校验。发现缺失时：

1. 停止代码扫描和知识库生成。
2. 列出缺失章节、字段和文件。
3. 给出目标路径。
4. 展示对应插件模板位置和最小示例。
5. 等待用户补齐后重新执行。

`不适用`是有效输入，不属于缺失。

## 6. 唯一输出 Schema

```text
cadence/knowledge-base/
├── user-input/
├── manifest.yaml
├── README.md
├── base-information.md
├── development-guide.md
├── interfaces/
│   ├── README.md
│   ├── {标识}_{接口名称}_{API名称}.md
│   └── {标识}_{接口名称}_{API名称}_参数与报文.md
├── pages/
│   ├── README.md
│   └── {页面标识}_{页面名称}.md
├── services/
├── data-models/
├── evidence/
│   ├── source-index.md
│   └── traceability-matrix.md
├── domain-glossary.md
├── open-questions.md
└── change-history.md
```

约束：

- 只使用 `cadence/knowledge-base/`。
- 不迁移、不识别、不兼容 `cadence/knowledgeBase/`。
- API 目录统一为 `interfaces/`，不再使用 `apis/`。
- `manifest.yaml`、`README.md`、证据索引和待确认项是核心产物，不得标记为可选。
- `services/` 和 `data-models/` 仅在需要拆分时生成，但路径固定。
- 不适用领域不生成详细文档，必须在 Manifest 记录状态和原因。

## 7. Manifest 契约

Manifest 是解析后范围和执行状态的唯一机器可读来源，至少记录：

```yaml
schema_version: "3.0"
generator:
  skill: knowledge-base-bootstrap
  version: "3.0"
mode: full-or-scoped
git:
  branch: unknown
  baseline_commit: unknown
input:
  root: cadence/knowledge-base/user-input
  base_info: cadence/knowledge-base/user-input/base-info.md
scope:
  projects: []
  database: full-or-scoped-or-not-applicable
  middleware: full-or-scoped-or-not-applicable
  api: full-or-scoped-or-not-applicable
  pages: full-or-scoped-or-not-applicable
documents: []
coverage: {}
open_questions: {}
```

领域 Skills 必须读取 Manifest 中解析后的范围，不得重新解释用户输入并扩大范围。

## 8. API 能力分类

### 8.1 对外能力

`base-info.md` 链接的 `api-scope.md` 是全部对外能力的权威清单。

- 清单中的能力统一归类为对外能力。
- 代码用于确认实现位置、装配状态、调用链和数据副作用。
- 不能仅因缺少 Controller、网关或调用证据将已登记能力改判为对内能力。
- 清单与代码冲突时，保留对外分类并将实现冲突写入待确认项。

### 8.2 对内能力

在所选工程中发现但未登记在对外能力清单中的 REST、RPC、消息、文件和任务能力统一归类为对内能力。

疑似对外但未登记的能力不得自动升级为对外，标记为对内候选或待确认。

### 8.3 索引结构

`interfaces/README.md` 至少包含：

```markdown
## 对外能力

以用户提供的对外能力清单为准。

## 对内能力

代码中发现但未登记在对外能力清单中的能力。
```

## 9. API 执行模式

### 9.1 全量模式

分析：

1. 对外公开 REST API。
2. 合作方或受限外部 API。
3. 内部前端 REST API。
4. 服务间 REST API。
5. RPC Provider 与 Consumer。
6. 消息生产与消费能力。
7. Redis 队列式能力。
8. FTP、SFTP、对象存储和文件交换。
9. 定时任务、批处理和异步作业。

先建立完整索引，再逐项深挖。单接口测试结果不得替代项目级能力盘点。

### 9.2 指定模式

- 只深挖用户指定的能力。
- 允许追踪完成调用链所需的内部依赖。
- 不额外盘点与指定能力无关的接口。
- 指定能力不在对外清单中时默认归类为对内能力，除非用户明确修正。

### 9.3 批量行为

- 用户已经明确全量或多个标识后连续执行，不在每完成一个能力后重复确认。
- 不使用 `TaskCreate`。
- 不使用 `memory/`。
- 进度写入 Manifest 和 `interfaces/README.md`。

## 10. API 输出模板

### 10.1 请求响应能力

HTTP 或 RPC 请求响应能力统一生成：

```text
{标识}_{接口名称}_{API名称}.md
{标识}_{接口名称}_{API名称}_参数与报文.md
```

不再以 500 行决定是否拆分。

### 10.2 非请求响应能力

消息、文件、任务等能力生成主文档。没有参数或请求响应报文时，不强制生成空的配套文件。

### 10.3 缺失字段

- 有证据时填写真实值和来源。
- 用户未提供时填写 `未提供`。
- 扫描未发现时填写 `未发现`。
- 不适用于该能力时填写 `不适用`。
- 允许留空，不因单个字段缺失中止 Skill。

### 10.4 Demo 与 Asset

- 保留 `references/demo.md`。
- 保留 `references/demo_参数与报文.md`。
- Demo 仅用于展示最终格式，不作为目标项目事实或强制字段来源。
- 从配套 Demo 提炼正式的参数与报文 Asset 模板。
- 通用模板不得默认假设 HSF、MSHA、Ehcache、MySQL 或特定分层名称存在。

## 11. 数据库与代码证据

- 只使用用户提供的 DDL、Mapper、SQL、Entity、迁移文件和配置。
- 禁止连接数据库、中间件或远程环境。
- 禁止查询 `information_schema` 或其他在线元数据表。
- 数据库类型由 DDL 和配置判断，不强制 MySQL。
- Mapper XML 位置通过项目结构探测，不假设固定在 `src/main/java` 或 `resources`。
- 无法确认 Schema 或表归属时标记待确认，不使用工程名代替数据库名。

## 12. 跨运行时用户交互

优先级：

1. Claude Code：使用 `AskUserQuestion`。
2. Codex：工具可用时使用 `request_user_input`。
3. Codex Default 模式或工具未提供：使用普通文本提问。

Skill 文档不得使用不存在的 `user_input`、`user_input_xxx` 或其他猜测名称。

仅在输入缺失、范围冲突或同名能力无法判定时提问。用户已明确范围时不得重复确认。

## 13. Skill 元数据与通用化

- `description` 使用 `Use when...` 描述触发条件，不总结完整流程。
- 删除 `knowledge-base-api` 的 `license: Proprietary`，继承插件 MIT License。
- 更新所有受影响的 `agents/openai.yaml`。
- 项目特定分析发现写入 KnowledgeBase、证据索引或待确认项。
- 不自动写入 `cadence/project-rules/`。
- 通用 Skill 不硬编码特定项目的能力集、双活 Key、发布方式、缓存结构或 Mapper 目录。

## 14. 领域 Skill 协作

- Bootstrap 负责输入校验、Manifest 初始化和领域编排。
- Base Info 只分析 Manifest 声明的工程、DDL、中间件和配置范围。
- API 以对外清单进行分类，并按全量或指定模式执行。
- Pages 只分析页面范围文件声明的应用、菜单和路由。
- Overview 生成总入口、术语、待确认项和稳定代理入口区块。
- Update 只认 Schema 3.0 Manifest 和当前目录，不处理旧 Schema。

## 15. 异常处理

| 场景 | 行为 |
|------|------|
| `base-info.md` 缺失 | 停止，返回路径和模板 |
| 必填章节缺失 | 停止，列出缺失章节 |
| 引用文件不存在 | 停止，列出失效链接和模板 |
| 状态为不适用 | 记录 Manifest，跳过领域 |
| DDL 不完整 | 继续有限证据分析，记录未覆盖表 |
| 接口在对外清单但代码未定位 | 保留对外分类，状态写待确认 |
| 代码发现未登记接口 | 归类为对内能力 |
| 请求响应字段缺失 | 留空或标记未提供，不阻断 |
| CodeGraph 或 AST 不可用 | 文本检索定位候选后定向阅读 |

## 16. 影响文件

计划调整：

- `knowledge-base-bootstrap/SKILL.md`
- `knowledge-base-bootstrap/references/input-contract.md`
- `knowledge-base-bootstrap/references/demo.md`
- `knowledge-base-bootstrap/assets/input-inventory-template.md`
- `knowledge-base-bootstrap/assets/manifest-template.yaml`
- `knowledge-base-bootstrap/user-input/*`
- `knowledge-base-api/SKILL.md`
- `knowledge-base-api/assets/api-capabilities-template.md`
- 新增参数与报文 Asset 模板
- `knowledge-base-api/references/api-analysis-guide.md`
- `knowledge-base-api/agents/openai.yaml`
- `knowledge-base-base-info/SKILL.md`
- `knowledge-base-pages/SKILL.md`
- `knowledge-base-overview/SKILL.md` 及其模板与规则接入指南
- `knowledge-base-update/SKILL.md`
- `.gitignore`

## 17. 验证方案

### 17.1 静态验证

- `git diff --check` 无错误。
- 所有 KnowledgeBase Skills 通过 `quick_validate.py`。
- `cadence-init/skills/knowledge-base-*` 不再使用 `cadence/knowledgeBase/`。
- `cadence-init/skills/knowledge-base-*` 不再使用 `apis/`、`TaskCreate`、`memory/`、`information_schema` 和错误的 `user_input` 工具名。
- 所有引用模板和 Demo 配套文件存在。

### 17.2 行为场景

1. `base-info.md` 缺失：停止并展示模板。
2. 页面状态为不适用：其他领域继续执行。
3. API 为全量：生成对外与对内能力索引。
4. API 为指定单接口：只深挖指定能力及其内部依赖。
5. 对外清单中的接口无法定位代码：保持对外分类并记录待确认。
6. 代码发现未登记接口：归入对内能力。
7. DDL 只包含部分表：基于现有 DDL 和代码继续，记录缺口。
8. 运行时没有结构化提问工具：退化为普通文本提问。

## 18. 完成标准

- 用户输入路径和插件模板路径职责清晰。
- 输入不完整时不会启动分析。
- 输出只使用 Schema 3.0 目录。
- Manifest 成为所有领域 Skill 的范围来源。
- 对外能力完全以用户清单为准。
- API 全量与指定模式行为明确。
- 不连接数据库，不依赖在线元数据查询。
- Demo 缺失字段不阻断生成。
- Claude Code 与 Codex 交互工具名正确且有降级路径。
- 所有引用、模板、元数据和路径通过验证。
