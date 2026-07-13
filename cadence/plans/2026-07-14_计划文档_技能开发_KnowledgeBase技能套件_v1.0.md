# KnowledgeBase 技能套件实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 `cadence-init/skills/` 下创建六个兼容 Claude Code 与 Codex 的 KnowledgeBase 技能。

**Architecture:** 使用一个总控技能编排五个领域技能。每个技能保持独立，包含自己的 `SKILL.md`、Codex 元数据、按需参考资料和输出模板，不依赖跨技能相对路径。

**Tech Stack:** Markdown、YAML、JSON；不新增脚本代码。

## Global Constraints

- 六个技能必须直接位于 `cadence-init/skills/`。
- `SKILL.md` frontmatter 只包含 `name` 和 `description`。
- 技能默认使用中文交互和生成文档。
- 知识库输出到目标项目的 `cadence/knowledgeBase/`。
- 不修改 `.claude/rules/`。
- 不创建技能级 README。
- 按用户要求，不运行结构验证、行为验证、前向测试或子代理测试。
- 最终状态必须标记为“已创建、未验证”。

---

### Task 1: 创建六个技能骨架

**Files:**

- Create: `cadence-init/skills/knowledge-base-bootstrap/`
- Create: `cadence-init/skills/knowledge-base-base-info/`
- Create: `cadence-init/skills/knowledge-base-api/`
- Create: `cadence-init/skills/knowledge-base-pages/`
- Create: `cadence-init/skills/knowledge-base-overview/`
- Create: `cadence-init/skills/knowledge-base-update/`

**Interfaces:**

- Consumes: v2.0 技术方案中的技能名称和双端兼容约束。
- Produces: 六个包含 `SKILL.md` 与 `agents/openai.yaml` 的标准技能目录。

- [ ] 使用现有 `init_skill.py` 逐个生成技能骨架。
- [ ] 为需要模板和案例的技能创建 `references/` 与 `assets/`。
- [ ] 不生成脚本目录和示例占位文件。

### Task 2: 实现总控技能

**Files:**

- Modify: `cadence-init/skills/knowledge-base-bootstrap/SKILL.md`
- Modify: `cadence-init/skills/knowledge-base-bootstrap/agents/openai.yaml`
- Create: `cadence-init/skills/knowledge-base-bootstrap/references/input-contract.md`
- Create: `cadence-init/skills/knowledge-base-bootstrap/references/demo.md`
- Create: `cadence-init/skills/knowledge-base-bootstrap/assets/input-inventory-template.md`
- Create: `cadence-init/skills/knowledge-base-bootstrap/assets/manifest-template.yaml`

**Interfaces:**

- Consumes: 用户资料、项目规则、仓库信息和其他五个技能。
- Produces: 输入清单、执行模式、知识库目录、manifest 和最终汇总。

- [ ] 编写总控角色、输入引导、模式选择、编排顺序和全局守则。
- [ ] 编写完整输入契约和敏感信息规则。
- [ ] 编写输入清单与 manifest 模板。
- [ ] 编写完整模式与有限证据模式案例。

### Task 3: 实现基础信息技能

**Files:**

- Modify: `cadence-init/skills/knowledge-base-base-info/SKILL.md`
- Modify: `cadence-init/skills/knowledge-base-base-info/agents/openai.yaml`
- Create: `cadence-init/skills/knowledge-base-base-info/references/java-bs-analysis-guide.md`
- Create: `cadence-init/skills/knowledge-base-base-info/references/demo.md`
- Create: `cadence-init/skills/knowledge-base-base-info/assets/base-information-template.md`
- Create: `cadence-init/skills/knowledge-base-base-info/assets/development-guide-template.md`

**Interfaces:**

- Consumes: 代码、DDL、配置、中间件清单和输入状态。
- Produces: 基础信息、开发指南、证据索引和基础关系。

- [ ] 编写 Java、Vue/React、DDL、配置和中间件分析流程。
- [ ] 加入横切关注点、生命周期和可信度规则。
- [ ] 编写基础信息和开发指南模板。
- [ ] 编写多服务、分库分表和消息中间件案例。

### Task 4: 实现 API 能力技能

**Files:**

- Modify: `cadence-init/skills/knowledge-base-api/SKILL.md`
- Modify: `cadence-init/skills/knowledge-base-api/agents/openai.yaml`
- Create: `cadence-init/skills/knowledge-base-api/references/api-analysis-guide.md`
- Create: `cadence-init/skills/knowledge-base-api/references/demo.md`
- Create: `cadence-init/skills/knowledge-base-api/assets/api-capabilities-template.md`

**Interfaces:**

- Consumes: API 文档、后端代码、基础信息和非 HTTP 能力资料。
- Produces: 对外、对内、服务间和非 HTTP 能力清单。

- [ ] 编写 REST、RPC、消息、文件和任务能力分析流程。
- [ ] 加入声明、实现、装配和暴露状态判断。
- [ ] 编写 API 能力模板和综合案例。

### Task 5: 实现页面能力技能

**Files:**

- Modify: `cadence-init/skills/knowledge-base-pages/SKILL.md`
- Modify: `cadence-init/skills/knowledge-base-pages/agents/openai.yaml`
- Create: `cadence-init/skills/knowledge-base-pages/references/page-analysis-guide.md`
- Create: `cadence-init/skills/knowledge-base-pages/references/demo.md`
- Create: `cadence-init/skills/knowledge-base-pages/assets/page-capabilities-template.md`

**Interfaces:**

- Consumes: 路由资料、Vue/React 代码、基础信息和 API 能力文档。
- Produces: 页面、路由、权限、API 和数据之间的映射。

- [ ] 编写静态、动态、后端下发路由分析流程。
- [ ] 加入页面可达性、权限、状态和 API 关联规则。
- [ ] 编写页面能力模板和 Vue/React 案例。

### Task 6: 实现项目概览技能

**Files:**

- Modify: `cadence-init/skills/knowledge-base-overview/SKILL.md`
- Modify: `cadence-init/skills/knowledge-base-overview/agents/openai.yaml`
- Create: `cadence-init/skills/knowledge-base-overview/references/rules-integration-guide.md`
- Create: `cadence-init/skills/knowledge-base-overview/references/demo.md`
- Create: `cadence-init/skills/knowledge-base-overview/assets/project-overview-template.md`
- Create: `cadence-init/skills/knowledge-base-overview/assets/domain-glossary-template.md`
- Create: `cadence-init/skills/knowledge-base-overview/assets/open-questions-template.md`
- Create: `cadence-init/skills/knowledge-base-overview/assets/knowledge-base-usage-template.md`

**Interfaces:**

- Consumes: 基础信息、API、页面和领域术语。
- Produces: 项目概览、术语表、待确认项和 Coding Agent 规则入口。

- [ ] 编写项目导航、核心流程和常见修改场景整理流程。
- [ ] 编写 `CLAUDE.md`、`AGENTS.md` 稳定管理区块更新规则。
- [ ] 编写概览、术语、待确认项和使用规则模板。
- [ ] 编写规则合并案例。

### Task 7: 实现增量更新技能

**Files:**

- Modify: `cadence-init/skills/knowledge-base-update/SKILL.md`
- Modify: `cadence-init/skills/knowledge-base-update/agents/openai.yaml`
- Create: `cadence-init/skills/knowledge-base-update/references/incremental-update-guide.md`
- Create: `cadence-init/skills/knowledge-base-update/references/demo.md`
- Create: `cadence-init/skills/knowledge-base-update/assets/change-history-template.md`

**Interfaces:**

- Consumes: 现有知识库、Git 基线、增量资料和代码差异。
- Produces: 受影响文档更新、稳定 ID 映射和变更历史。

- [ ] 编写基线、变更分类、影响映射和幂等更新流程。
- [ ] 加入人工内容保护、Schema 迁移和无 Git 降级规则。
- [ ] 编写变更历史模板和综合增量案例。

### Task 8: 更新 cadence-init 插件元数据

**Files:**

- Modify: `cadence-init/.claude-plugin/plugin.json`
- Modify: `.claude-plugin/marketplace.json`

**Interfaces:**

- Consumes: 新增六技能的用途和版本信息。
- Produces: 能反映 KnowledgeBase 能力的插件描述、关键词和版本。

- [ ] 将 `cadence-init` 版本提升到 `0.1.0`。
- [ ] 更新插件描述和关键词。
- [ ] 同步 marketplace 中的版本和描述。

### Task 9: 收尾

**Files:**

- Review only: 本计划列出的全部文件。

**Interfaces:**

- Consumes: 已创建文件。
- Produces: 未执行验证的实现交付说明。

- [ ] 汇总创建和修改的文件。
- [ ] 不运行 `quick_validate.py`、行为验证、前向测试或其他验证命令。
- [ ] 最终明确标记“已创建、未验证”。

