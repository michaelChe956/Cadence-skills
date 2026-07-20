# KnowledgeBase 输入契约与 Schema 统一实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:executing-plans` to implement this plan task-by-task. 当前仓库未授权子 Agent，因此默认采用内联执行。

**Goal:** 将 KnowledgeBase Skills 统一为用户输入驱动、Schema 3.0、对外清单权威分类并兼容 Claude Code 与 Codex 的稳定工作流。

**Architecture:** Bootstrap 先校验目标项目 `cadence/knowledge-base/user-input/base-info.md` 和五类领域输入，将解析结果写入强制 Manifest；领域 Skills 只消费 Manifest 范围。API Skill 以用户提供的接口清单判定全部对外能力，按全量或指定模式生成 `interfaces/` 索引和明细。

**Tech Stack:** Markdown、YAML、SQL 模板、Claude Code Skills、Codex Skills。

## 全局约束

- 所有交互、注释和文档使用中文。
- 不新增业务代码、脚本或依赖，复用现有 `quick_validate.py`。
- 只使用 `cadence/knowledge-base/`，不处理 `cadence/knowledgeBase/`。
- API 目录只使用 `interfaces/`，不使用 `apis/`。
- 不连接数据库、中间件或远程环境，不查询 `information_schema`。
- 不使用 `TaskCreate` 和 `memory/`。
- Claude Code 使用 `AskUserQuestion`；Codex 使用 `request_user_input`，工具不可用时使用普通文本提问。
- 不覆盖或清理用户已有变更，不提交 Git Commit，除非用户另行明确要求。
- 设计依据：`cadence/designs/2026-07-16_技术方案_KnowledgeBase输入契约与Schema统一_v3.0.md`。

---

### Task 1: 将插件 user-input 改为通用模板集

**Files:**

- Modify: `cadence-init/skills/knowledge-base-bootstrap/user-input/base-info.md`
- Delete: `cadence-init/skills/knowledge-base-bootstrap/user-input/2026-06-13_API文档_活动中心嵌入外围系统菜单清单_v1.0.md`
- Delete: `cadence-init/skills/knowledge-base-bootstrap/user-input/2026-07-13_数据模型_实例库8007_testhbzx_dhb_DDL_v1.0.sql`
- Delete: `cadence-init/skills/knowledge-base-bootstrap/user-input/2026-07-16_分析报告_活动中心工程列表_v1.0.md`
- Delete: `cadence-init/skills/knowledge-base-bootstrap/user-input/2026-07-16_分析报告_活动中心接口注册清单_v1.0.md`
- Create: `cadence-init/skills/knowledge-base-bootstrap/user-input/project-scope.md`
- Create: `cadence-init/skills/knowledge-base-bootstrap/user-input/database-ddl.sql`
- Create: `cadence-init/skills/knowledge-base-bootstrap/user-input/middleware-scope.md`
- Create: `cadence-init/skills/knowledge-base-bootstrap/user-input/api-scope.md`
- Create: `cadence-init/skills/knowledge-base-bootstrap/user-input/page-scope.md`

**Produces:** Bootstrap 可复制或展示的一套无项目真实数据的通用输入模板。

- [ ] **Step 1: 重写强制入口模板**

将 `base-info.md` 固定为五个章节。每节包含 `状态` 和 `资料`；接口节额外包含 `执行范围` 与 `指定能力`。状态仅允许 `全量`、`指定`、`不适用`。

- [ ] **Step 2: 创建工程范围模板**

包含项目根目录、Git 仓库、本地路径、工程标识、工程类型、是否纳入分析和备注表。明确只有表中纳入分析的工程属于外层范围。

- [ ] **Step 3: 创建 DDL 模板**

使用 SQL 注释说明数据库类型、Schema、环境、导出时间和 DDL 放置位置，并提供一个虚构 `example_table` 示例，不包含真实项目表名。

- [ ] **Step 4: 创建中间件范围模板**

包含名称、类型、版本、业务用途、生产者、消费者、Topic/Queue/Key、环境和状态表。

- [ ] **Step 5: 创建 API 范围模板**

文件开头声明该清单是全部对外能力权威清单；包含执行范围、指定标识和能力表。能力表至少包含标识、名称、API 名称、类型、版本、状态和备注。

- [ ] **Step 6: 创建页面范围模板**

包含前端应用、页面、路由、菜单、权限、执行范围和指定页面表。

- [ ] **Step 7: 验证模板无活动中心真实内容**

Run: `rg -n "活动中心|chinaunicom|testhbzx|tianti\\.tg|actInfoQry" cadence-init/skills/knowledge-base-bootstrap/user-input`

Expected: 无输出。

### Task 2: 统一 Bootstrap 输入校验和 Manifest 3.0

**Files:**

- Modify: `cadence-init/skills/knowledge-base-bootstrap/SKILL.md`
- Modify: `cadence-init/skills/knowledge-base-bootstrap/references/input-contract.md`
- Modify: `cadence-init/skills/knowledge-base-bootstrap/references/demo.md`
- Modify: `cadence-init/skills/knowledge-base-bootstrap/assets/input-inventory-template.md`
- Modify: `cadence-init/skills/knowledge-base-bootstrap/assets/manifest-template.yaml`
- Modify: `cadence-init/skills/knowledge-base-bootstrap/agents/openai.yaml`

**Consumes:** Task 1 的六个通用输入模板。

**Produces:** 输入不完整时停止、输入完整时生成 Manifest 3.0 并编排领域 Skills 的 Bootstrap。

- [ ] **Step 1: 重写输入入口规则**

将目标输入根固定为 `cadence/knowledge-base/user-input/`，将 `base-info.md` 设为唯一强制入口。删除引导用户临时提供任意路径后继续分析的模糊规则。

- [ ] **Step 2: 定义校验顺序**

在扫描代码前检查五个章节、状态、引用文件和指定范围。缺失时停止并输出缺失内容、目标路径、插件模板路径和最小示例。

- [ ] **Step 3: 统一交互降级**

写明 Claude Code 使用 `AskUserQuestion`，Codex 工具可用时使用 `request_user_input`，否则普通文本提问。删除其他猜测工具名。

- [ ] **Step 4: 更新输入契约和案例**

案例覆盖输入缺失、页面不适用、API 全量和 API 指定模式；明确 `不适用` 是有效输入。

- [ ] **Step 5: 更新输入清单模板**

输入清单改为记录 `base-info.md` 解析结果，类型固定为工程、DDL、中间件、API、页面，不再生成第二套自由格式输入范围。

- [ ] **Step 6: 将 Manifest 升级为 3.0**

模板必须包含 `schema_version: "3.0"`、输入根、Base Info 路径、五类范围、Git 基线、文档、覆盖率和待确认项；核心路径不得使用 `unknown` 占位。

- [ ] **Step 7: 更新 Bootstrap 元数据**

`agents/openai.yaml` 的默认提示明确要求读取目标项目输入文档并在缺失时返回模板。

- [ ] **Step 8: 验证 Bootstrap 契约关键词**

Run: `rg -n "base-info\\.md|request_user_input|schema_version: \\\"3\\.0\\\"|不适用|停止" cadence-init/skills/knowledge-base-bootstrap`

Expected: SKILL、输入契约、案例和 Manifest 均出现对应规则。

### Task 3: 恢复 API 全量职责并保留单能力深挖

**Files:**

- Modify: `cadence-init/skills/knowledge-base-api/SKILL.md`
- Modify: `cadence-init/skills/knowledge-base-api/assets/api-capabilities-template.md`
- Create: `cadence-init/skills/knowledge-base-api/assets/api-parameters-message-template.md`
- Modify: `cadence-init/skills/knowledge-base-api/references/api-analysis-guide.md`
- Preserve: `cadence-init/skills/knowledge-base-api/references/demo.md`
- Preserve: `cadence-init/skills/knowledge-base-api/references/demo_参数与报文.md`
- Modify: `cadence-init/skills/knowledge-base-api/agents/openai.yaml`

**Consumes:** Manifest 3.0 中的工程范围、API 执行模式和用户对外能力清单。

**Produces:** 对外清单权威分类、全量/指定两种模式、项目级索引和单能力明细。

- [ ] **Step 1: 修正 Frontmatter 和定位**

Description 使用 `Use when...` 描述触发场景；删除 `license: Proprietary`。概述明确 API Skill 同时负责项目级盘点和单能力深挖。

- [ ] **Step 2: 定义对外与对内分类**

用户 `api-scope.md` 中登记的全部能力固定为对外；所选工程中发现但未登记的 REST、RPC、消息、文件和任务能力归为对内。冲突进入待确认项，不静默改分类。

- [ ] **Step 3: 定义全量模式**

先扫描并生成 `interfaces/README.md`，覆盖 REST、RPC、消息、Redis 队列、文件交换和任务，再逐项生成明细。不得用 Demo 接口替代全盘分析。

- [ ] **Step 4: 定义指定模式**

只分析指定能力和完成调用链所需的内部依赖，不扫描无关能力。指定项不在对外清单时默认归为对内。

- [ ] **Step 5: 删除不允许的运行时行为**

删除 `TaskCreate`、`memory/`、每完成一个接口暂停询问、在线数据库验证和固定 Mapper XML 路径。进度改写入 Manifest 与接口索引。

- [ ] **Step 6: 收敛证据规则**

数据库只读取 DDL、代码、Mapper、SQL、Entity 和配置；能力清单是对外分类权威来源，代码是实现验证来源。无法确认时标记待确认。

- [ ] **Step 7: 通用化主模板**

保留 11 节结构，但删除默认 HSF、MSHA、Ehcache、Bridge、Normal 和特定项目层级。可选能力不存在时允许 `未提供`、`未发现`、`不适用` 或空白。

- [ ] **Step 8: 添加参数与报文 Asset**

从 `demo_参数与报文.md` 提炼输入参数、输出参数、请求示例和响应示例四类通用占位结构。HTTP/RPC 请求响应能力统一生成双文件，不再按 500 行判断。

- [ ] **Step 9: 更新分析指南和元数据**

指南覆盖项目级盘点、对外清单匹配、对内发现、调用链核实和跨数据库证据；`openai.yaml` 同步新的全量/指定职责。

- [ ] **Step 10: 验证 API 禁止项和必需项**

Run: `rg -n "TaskCreate|memory/|information_schema|src/main/java.*非.*resources|license: Proprietary" cadence-init/skills/knowledge-base-api`

Expected: 无输出。

Run: `rg -n "对外能力|对内能力|全量|指定|interfaces/README\\.md|api-parameters-message-template" cadence-init/skills/knowledge-base-api`

Expected: SKILL、指南与模板引用完整。

### Task 4: 让其他领域 Skills 只消费 Manifest 3.0

**Files:**

- Modify: `cadence-init/skills/knowledge-base-base-info/SKILL.md`
- Modify: `cadence-init/skills/knowledge-base-pages/SKILL.md`
- Modify: `cadence-init/skills/knowledge-base-overview/SKILL.md`
- Modify: `cadence-init/skills/knowledge-base-overview/assets/knowledge-base-usage-template.md`
- Modify: `cadence-init/skills/knowledge-base-overview/references/rules-integration-guide.md`
- Modify: `cadence-init/skills/knowledge-base-update/SKILL.md`

**Consumes:** Bootstrap 生成的 Manifest 3.0。

**Produces:** 全部领域 Skill 使用相同路径、范围和核心产物约束。

- [ ] **Step 1: 更新 Base Info**

Manifest 设为必读且非可选；只分析声明工程、DDL 和中间件范围。输出统一为 `base-information.md`、`development-guide.md`、证据索引和待确认项。

- [ ] **Step 2: 更新 Pages**

只分析 Manifest 中的页面范围；页面不适用时跳过；接口引用统一指向 `interfaces/`。

- [ ] **Step 3: 更新 Overview**

核心输入统一为 Manifest、Base Info、`interfaces/README.md`、`pages/README.md` 和开发指南；入口统一为 `cadence/knowledge-base/README.md`。

- [ ] **Step 4: 更新知识库使用规则和接入指南**

读取顺序、代理入口区块和修改场景全部使用新 Schema；删除 `apis/` 和旧编号文档。

- [ ] **Step 5: 更新 Update**

Description 和正文统一使用 `cadence/knowledge-base/`；只接受 Schema 3.0 Manifest，不迁移旧目录；基线与变更历史依赖 Manifest。

- [ ] **Step 6: 验证路径一致性**

Run: `rg -n "cadence/knowledgeBase|\\bapis/|00-project-overview|01-base-information|02-api-capabilities|03-page-capabilities|04-domain-glossary|05-change-history|06-development-guide|07-open-questions" cadence-init/skills/knowledge-base-*`

Expected: 无输出。

### Task 5: 清理工作区杂项并完成整体验证

**Files:**

- Modify: `.gitignore`
- Delete: `cadence-init/.DS_Store`
- Delete: `cadence-init/skills/.DS_Store`
- Delete: `cadence-init/skills/knowledge-base-api/.DS_Store`
- Delete: `cadence-init/skills/knowledge-base-overview/.DS_Store`

**Produces:** 可评审、无系统垃圾文件且结构校验通过的最终变更。

- [ ] **Step 1: 添加 macOS 文件忽略规则**

在 `.gitignore` 增加：

```gitignore
# macOS
.DS_Store
```

- [ ] **Step 2: 删除当前未跟踪 `.DS_Store`**

仅删除上述四个系统生成文件，不清理其他未跟踪资料。

- [ ] **Step 3: 运行 Diff 格式检查**

Run: `git diff --check`

Expected: 无输出，退出码 0。

- [ ] **Step 4: 验证所有 KnowledgeBase Skills**

Run: `for d in cadence-init/skills/knowledge-base-api cadence-init/skills/knowledge-base-base-info cadence-init/skills/knowledge-base-bootstrap cadence-init/skills/knowledge-base-overview cadence-init/skills/knowledge-base-pages cadence-init/skills/knowledge-base-update; do python3 cadence-init/skills/skill-creator/scripts/quick_validate.py "$d"; done`

Expected: 六次 `Skill is valid`。

- [ ] **Step 5: 验证模板和引用文件存在**

Run: `test -f cadence-init/skills/knowledge-base-api/references/demo_参数与报文.md && test -f cadence-init/skills/knowledge-base-api/assets/api-parameters-message-template.md && test -f cadence-init/skills/knowledge-base-bootstrap/user-input/base-info.md && test -f cadence-init/skills/knowledge-base-bootstrap/user-input/api-scope.md`

Expected: 退出码 0。

- [ ] **Step 6: 审查最终变更范围**

Run: `git status --short && git diff --stat && git diff -- cadence-init/skills/knowledge-base-* .gitignore`

Expected: 只包含本方案声明的 KnowledgeBase Skills、模板、设计/计划文档和 `.gitignore` 变更；不覆盖用户无关修改。
