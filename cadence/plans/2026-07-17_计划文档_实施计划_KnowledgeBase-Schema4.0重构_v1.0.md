# KnowledgeBase Schema 4.0 重构实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development`（推荐）or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将现有 KnowledgeBase Skills 全量重构为 Schema 4.0，使配置成为一级输入和证据、数据模型固定生成字段级文档、Update 强制消费显式变更包、Context 渐进检索代码、数据模型与配置快照。

**Architecture:** Bootstrap 通过六领域输入生成 Manifest 4.0；Base Info 基于多源证据生成固定的数据模型与配置领域文档；Update 只接受完整变更包并验证 MR、数据库资料和配置快照；Context 使用知识库、当前代码、数据模型和配置四类证据路径渐进检索。API、Pages 和 Overview 只消费 Manifest 授权范围，并链接新的字段级表文档和服务配置文档。

**Tech Stack:** Markdown、YAML、SQL 输入模板、Claude Code Skills、Codex Skills、Shell 静态检查、仓库现有 `quick_validate.py`。

## Global Constraints

- 所有交互、说明、模板和文档使用中文；源码标识、配置键、协议名和字段名保留原文。
- 不新增业务代码、验证脚本或外部依赖；只修改 Markdown、YAML、JSON 和 SQL 模板，复用现有 `quick_validate.py`。
- 目标 Schema 固定为 `schema_version: "4.0"`，不兼容、不迁移、不识别 Schema 3.0 或其他旧版知识库。
- Bootstrap 一级领域固定为工程、数据模型、配置、中间件、接口和页面。
- DDL 是可选结构证据，不能成为 Bootstrap 或日常 Context 的强制前置条件。
- 配置使用外部不可变发布快照，不把原始配置包复制进 KnowledgeBase。
- `knowledge-base-update` 必须显式指定完整变更包，Git Diff 和扫描结果只能验证输入，不能替代输入。
- `knowledge-base-context` 必须检查数据模型和配置关系，但只渐进读取任务所需的最小充分范围。
- 不连接数据库、配置中心、中间件或远程环境，不执行迁移、部署或发布脚本。
- 不输出密码、Token、AccessKey、Secret、私钥、完整连接串和敏感内部地址。
- 所有文件编辑使用 `apply_patch`；不得覆盖、清理或恢复用户已有变更。
- 每个任务完成后运行该任务的定向验证并提交独立 Git Commit。
- 设计依据：`cadence/designs/2026-07-17_技术方案_KnowledgeBase配置与数据模型重构_v4.0.md`。

---

## 文件结构映射

### Bootstrap 负责的输入与 Schema

- `cadence-init/skills/knowledge-base-bootstrap/`：六领域输入校验、Manifest 4.0、目录初始化和领域编排。
- `cadence-init/skills/knowledge-base-bootstrap/user-input/`：目标项目可复制的初始化输入模板。

### Base Info 负责的领域产物

- `cadence-init/skills/knowledge-base-base-info/`：基础信息、字段级数据模型、配置体系、服务配置明细和证据关系。
- 数据模型与配置仍由 Base Info Skill 生成，不新增额外 Skill。

### Update 负责的显式增量输入

- `cadence-init/skills/knowledge-base-update/user-input/change-package/`：五份强制变更文档和附件说明模板。
- `cadence-init/skills/knowledge-base-update/`：变更包校验、MR 验证、数据模型增量、配置快照差异和幂等历史。

### Context 负责的渐进消费

- `cadence-init/skills/knowledge-base-context/`：四类证据路径、七类任务画像和扩展后的证据矩阵。
- `readmes/skills/knowledge-base-context.md`：用户侧 Schema 4.0 使用说明。

### 领域关联与导航

- `knowledge-base-api`、`knowledge-base-pages`：关联 TABLE 和 CONFIGURATION 实体。
- `knowledge-base-overview`：将 `data-models/` 和 `configurations/` 提升为一级导航。
- 插件 Manifest 与 Marketplace：同步插件版本和能力描述。

---

### Task 1: 重构 Bootstrap 六领域输入与 Manifest 4.0

**Files:**

- Modify: `cadence-init/skills/knowledge-base-bootstrap/SKILL.md`
- Modify: `cadence-init/skills/knowledge-base-bootstrap/agents/openai.yaml`
- Modify: `cadence-init/skills/knowledge-base-bootstrap/assets/input-inventory-template.md`
- Modify: `cadence-init/skills/knowledge-base-bootstrap/assets/manifest-template.yaml`
- Modify: `cadence-init/skills/knowledge-base-bootstrap/references/input-contract.md`
- Modify: `cadence-init/skills/knowledge-base-bootstrap/references/demo.md`
- Modify: `cadence-init/skills/knowledge-base-bootstrap/user-input/base-info.md`
- Modify: `cadence-init/skills/knowledge-base-bootstrap/user-input/database-ddl.sql`
- Create: `cadence-init/skills/knowledge-base-bootstrap/user-input/data-model-scope.md`
- Create: `cadence-init/skills/knowledge-base-bootstrap/user-input/configuration-scope.md`

**Interfaces:**

- Consumes: 用户填写的 `base-info.md`、六领域范围文件和可选 DDL。
- Produces: `schema_version: "4.0"` Manifest、六领域解析清单、配置快照基线和领域 Skills 的唯一授权范围。

- [ ] **Step 1: 运行 Schema 4.0 前置失败检查**

Run:

```bash
test -f cadence-init/skills/knowledge-base-bootstrap/user-input/data-model-scope.md
```

Expected: 退出码 1，文件尚不存在。

Run:

```bash
rg -n 'schema_version: "4\.0"|configurations:|data_models:' cadence-init/skills/knowledge-base-bootstrap/assets/manifest-template.yaml
```

Expected: 无输出，证明旧模板尚未满足 Schema 4.0。

- [ ] **Step 2: 创建数据模型范围模板**

创建 `data-model-scope.md`，固定包含以下章节和字段：

```markdown
# 数据模型分析范围

## 数据库与 Schema

| 数据源标识 | 数据库类型 | 数据库或实例 | Schema | 业务域 | 纳入分析 | 备注 |
|------------|------------|--------------|--------|--------|----------|------|

## 结构证据

| 证据类型 | 路径或来源 | 环境 | 更新时间 | 纳入分析 | 备注 |
|----------|------------|------|----------|----------|------|

## 分库分表

| 逻辑表 | 分片键 | 分片规则 | 物理表规则 | 配置来源 | 备注 |
|--------|--------|----------|------------|----------|------|

## 排除范围

| 数据库或 Schema | 表或模式 | 排除原因 |
|-----------------|----------|----------|
```

在说明中明确证据类型允许 DDL、迁移文件、Entity、Mapper、SQL 和人工资料；DDL 可以不提供，但至少要有一种可定位结构证据。

- [ ] **Step 3: 创建配置快照范围模板**

创建 `configuration-scope.md`，固定包含：

```markdown
# 配置分析范围

## 当前基线快照

- 快照标识：
- 环境：
- 发布批次：
- 外部目录：
- 生成或获取时间：
- 快照指纹：
- 来源类型：配置中心导出 / ConfigMap / 发布配置包 / 配置仓库 / 其他

## 纳入服务

| 服务标识 | 配置目录或匹配规则 | 纳入分析 | 备注 |
|----------|--------------------|----------|------|

## 文件规则

| 类型 | 规则 | 处理方式 | 备注 |
|------|------|----------|------|

## 敏感信息说明
```

说明默认排除 `.idea`、`.gitkeep`、空文件和明确历史备份；Mapper XML 归入数据模型证据；部署脚本只作为加载链路证据。

快照指纹固定为：对纳入范围内文件按相对路径排序，为每个文件计算 SHA-256，再对 `相对路径 + 制表符 + 文件 SHA-256` 的有序清单计算最终 SHA-256。Manifest 只保存最终快照指纹，不保存单个敏感配置值的哈希；重复文件哈希只在当前分析过程中临时使用。

- [ ] **Step 4: 重写 base-info 六领域入口**

将 `base-info.md` 固定为工程信息、数据模型、配置、中间件、接口和页面六节。每节包含 `状态`、`资料` 和 `不适用原因`；数据模型指向 `data-model-scope.md`，配置指向 `configuration-scope.md`。

状态只允许：

```text
全量
指定
不适用
```

将 `database-ddl.sql` 的文件头改为“可选 DDL 证据模板”，删除任何“必须替换为实际 DDL 才能继续”的表述。

- [ ] **Step 5: 重写 Bootstrap Skill 和输入契约**

在 `SKILL.md` 与 `references/input-contract.md` 中落实：

- Frontmatter Description 同时出现工程、数据模型、配置快照、中间件、接口和页面。
- 只接受 Schema 4.0，不包含兼容或迁移分支。
- 扫描前校验六领域状态和引用文件。
- 配置状态为全量或指定时，快照目录必须可读。
- 数据模型无 DDL但有其他结构证据时允许继续。
- 数据模型没有任何结构证据时停止或要求不适用。
- 输出固定初始化 `data-models/` 和 `configurations/`。

- [ ] **Step 6: 更新 Manifest、输入清单、案例和 Agent 元数据**

Manifest 模板必须包含以下一级键：

```yaml
schema_version: "4.0"
generator: {}
git:
  repositories: []
input: {}
scope:
  projects: {}
  data_models: {}
  configurations: {}
  middleware: {}
  api: {}
  pages: {}
evidence:
  code: {}
  data_model_sources: {}
  configuration_snapshots: {}
update:
  last_change_package: {}
  processed_packages: []
documents:
  core: []
  interfaces: []
  pages: []
  services: []
  data_models: []
  configurations: []
coverage: {}
open_questions: {}
```

输入清单新增数据模型来源和配置快照字段。案例至少覆盖：无 DDL但有代码结构证据、配置快照缺失、配置不适用、六领域全部通过。

- [ ] **Step 7: 验证 Bootstrap Schema 4.0 契约**

Run:

```bash
rg -n 'schema_version: "4\.0"|data_models:|configurations:|configuration_snapshots:|processed_packages:' cadence-init/skills/knowledge-base-bootstrap
```

Expected: Manifest、Skill、输入契约和案例均出现对应 Schema 4.0 内容。

Run:

```bash
rg -n 'Schema 3\.0|schema_version: "3\.0"|Manifest 3\.0' cadence-init/skills/knowledge-base-bootstrap
```

Expected: 无输出。

Run:

```bash
python3 cadence-init/skills/skill-creator/scripts/quick_validate.py cadence-init/skills/knowledge-base-bootstrap
```

Expected: `Skill is valid`。

- [ ] **Step 8: 提交 Bootstrap 重构**

```bash
git add cadence-init/skills/knowledge-base-bootstrap
git commit -m "feat: redesign knowledge base bootstrap for schema 4"
```

---

### Task 2: 固定生成字段级数据模型文档

**Files:**

- Modify: `cadence-init/skills/knowledge-base-base-info/SKILL.md`
- Modify: `cadence-init/skills/knowledge-base-base-info/agents/openai.yaml`
- Modify: `cadence-init/skills/knowledge-base-base-info/assets/base-information-template.md`
- Modify: `cadence-init/skills/knowledge-base-base-info/references/java-bs-analysis-guide.md`
- Modify: `cadence-init/skills/knowledge-base-base-info/references/demo.md`
- Create: `cadence-init/skills/knowledge-base-base-info/assets/data-model-index-template.md`
- Create: `cadence-init/skills/knowledge-base-base-info/assets/schema-data-model-template.md`
- Create: `cadence-init/skills/knowledge-base-base-info/assets/table-data-model-template.md`

**Interfaces:**

- Consumes: Task 1 的 `scope.data_models`、`evidence.data_model_sources`、工程范围和配置中的数据源/分片信息。
- Produces: `data-models/README.md`、每数据库或 Schema 索引、每逻辑表字段级文档及对应证据关系。

- [ ] **Step 1: 运行字段级模板前置失败检查**

Run:

```bash
test -f cadence-init/skills/knowledge-base-base-info/assets/table-data-model-template.md
```

Expected: 退出码 1。

- [ ] **Step 2: 创建数据模型总索引模板**

`data-model-index-template.md` 固定包含：

```markdown
# 数据模型索引

## 当前范围与基线
## 数据库与 Schema
## 业务域、服务与数据源映射
## 逻辑表清单
## 表关系导航
## 分库分表摘要
## 覆盖率与证据新鲜度
## 来源冲突与待确认项
```

逻辑表清单列固定为：稳定 ID、数据库/Schema、逻辑表、业务含义、读服务、写服务、证据状态、文档链接。

- [ ] **Step 3: 创建 Schema 索引模板**

`schema-data-model-template.md` 固定包含当前数据库/Schema、表清单、主要关系、读写服务、分片规则和未覆盖对象。该模板不得复制每张表的全部字段。

- [ ] **Step 4: 创建逻辑表字段级模板**

`table-data-model-template.md` 固定包含：

```markdown
# {{逻辑表名称}}

## 1. 元数据
## 2. 业务含义
## 3. 字段清单
## 4. 索引与约束
## 5. 分库分表
## 6. Entity、Mapper 与 SQL 映射
## 7. 读写服务
## 8. 关联 API 与页面
## 9. 特殊字段与数据规则
## 10. 证据与来源冲突
## 11. 变更记录
```

字段清单列固定为：字段、类型、可空、默认值、主键、含义、代码映射、证据状态、证据位置。

证据状态只允许：`DDL 已确认`、`迁移已确认`、`代码可推导`、`用户提供`、`来源冲突`、`待确认`。

- [ ] **Step 5: 重写 Base Info 数据模型流程**

在 `SKILL.md` 和分析指南中明确：

- 只接受 Manifest 4.0，不包含 Schema 3.0 兼容分支。
- `data-models/` 始终生成，不再仅限大型项目。
- 一张逻辑表对应一个文档；物理分片只记录规则。
- 不再允许用单个 `data-model-overview.md` 代替总索引和字段级表文档。
- DDL、迁移、Entity、Mapper、SQL、配置和用户资料多源合并。
- 没有 DDL 时仍生成，但不推断实际索引、默认值和数据库约束。
- 同名字段不能单独证明外键关系。
- API、页面、服务、配置和表使用稳定 ID 关联。

在 `base-information-template.md` 中把数据模型章节改为摘要与导航，不重复完整字段清单。

同步更新 `agents/openai.yaml`，默认提示明确按 Manifest 4.0 的数据模型范围生成总索引、Schema 索引和字段级逻辑表文档。

- [ ] **Step 6: 更新数据模型 Demo**

Demo 至少展示：

- 一张普通逻辑表的字段级文档摘要。
- 一张分片逻辑表及物理表规则。
- DDL 与 Entity 字段冲突。
- 无 DDL、从 Mapper/SQL 推导字段并标记完整性限制。

- [ ] **Step 7: 验证字段级数据模型契约**

Run:

```bash
rg -n 'data-models/README\.md|每张逻辑表|字段清单|DDL 已确认|代码可推导|来源冲突' cadence-init/skills/knowledge-base-base-info
```

Expected: Skill、指南、模板和 Demo 均出现字段级模型规则。

Run:

```bash
python3 cadence-init/skills/skill-creator/scripts/quick_validate.py cadence-init/skills/knowledge-base-base-info
```

Expected: `Skill is valid`。

- [ ] **Step 8: 提交数据模型产物重构**

```bash
git add cadence-init/skills/knowledge-base-base-info
git commit -m "feat: add field level knowledge base data models"
```

---

### Task 3: 建立配置快照与服务配置文档

**Files:**

- Modify: `cadence-init/skills/knowledge-base-base-info/SKILL.md`
- Modify: `cadence-init/skills/knowledge-base-base-info/agents/openai.yaml`
- Modify: `cadence-init/skills/knowledge-base-base-info/assets/base-information-template.md`
- Modify: `cadence-init/skills/knowledge-base-base-info/assets/development-guide-template.md`
- Modify: `cadence-init/skills/knowledge-base-base-info/references/java-bs-analysis-guide.md`
- Modify: `cadence-init/skills/knowledge-base-base-info/references/demo.md`
- Create: `cadence-init/skills/knowledge-base-base-info/assets/configuration-index-template.md`
- Create: `cadence-init/skills/knowledge-base-base-info/assets/service-configuration-template.md`

**Interfaces:**

- Consumes: Task 1 的 `scope.configurations`、配置快照外部目录、快照指纹、服务范围和文件分类规则。
- Produces: `configurations/README.md`、每服务配置文档、Base Info 配置体系摘要及配置到代码/数据模型/中间件的关系。

- [ ] **Step 1: 运行配置模板前置失败检查**

Run:

```bash
test -f cadence-init/skills/knowledge-base-base-info/assets/service-configuration-template.md
```

Expected: 退出码 1。

- [ ] **Step 2: 创建配置总索引模板**

`configuration-index-template.md` 固定包含：

```markdown
# 配置知识索引

## 当前配置基线
## 配置来源与加载顺序
## 环境与 Profile
## 服务配置导航
## 配置组与影响能力
## 敏感信息策略
## 快照差异摘要
## 来源冲突与待确认项
```

服务导航列固定为：服务稳定 ID、环境、配置来源、主要配置组、敏感级别摘要、文档链接。

- [ ] **Step 3: 创建服务配置文档模板**

`service-configuration-template.md` 固定包含：

```markdown
# {{服务名称}}配置

## 1. 元数据
## 2. 配置来源与加载顺序
## 3. Profile 与环境
## 4. 配置键清单
## 5. 代码绑定与生效条件
## 6. 数据源与分片配置
## 7. 中间件与外部系统配置
## 8. 敏感配置
## 9. 来源冲突与待确认项
## 10. 变更记录
```

配置键清单列固定为：配置键、用途、值类型、环境、来源文件、绑定位置、敏感级别、状态、证据。

状态只允许：`存在`、`新增`、`删除`、`修改`、`缺失`、`来源冲突`、`待确认`。

- [ ] **Step 4: 重写配置快照分析规则**

在 `SKILL.md` 与分析指南中明确：

- 配置是与代码、数据模型同级的一级证据。
- 原始配置快照只读且不复制进 KnowledgeBase。
- Properties、YAML、运行时 XML、Nginx 和缓存文件属于配置证据。
- Mapper XML 属于数据模型证据。
- 部署脚本只用于加载顺序和部署方式分析，不执行。
- 日志配置归入可观测性。
- 相同内容文件合并分析并记录适用服务。
- 重复文件哈希只用于当前运行的去重，不写入 KnowledgeBase；Manifest 仅保存 Task 1 定义的最终快照指纹。
- `.idea`、`.gitkeep`、空文件和历史备份默认排除。
- 敏感值统一写为 `<redacted>`，不得保存敏感值哈希。

- [ ] **Step 5: 更新 Base Info 与开发指南模板**

`base-information-template.md` 的配置章节改为当前快照、来源、加载顺序、Profile、配置组、风险和 `configurations/` 导航。

`development-guide-template.md` 增加：当前开发/测试配置基线、允许读取的配置来源、不可在本地执行的部署脚本、验证配置变更的安全方式。

- [ ] **Step 6: 更新配置 Demo 和 Agent 元数据**

Demo 使用虚构服务展示：重复配置文件合并、Mapper XML 转交数据模型、敏感键脱敏、配置键到 `@ConfigurationProperties` 的绑定、Profile 差异。

`agents/openai.yaml` 的默认提示必须明确读取 Manifest 4.0、字段级数据模型范围和配置快照范围。

- [ ] **Step 7: 验证配置知识契约**

Run:

```bash
rg -n 'configurations/README\.md|不可变|配置快照|<redacted>|Mapper XML|相同内容|不得保存.*哈希' cadence-init/skills/knowledge-base-base-info
```

Expected: Skill、指南、模板和 Demo 覆盖配置快照与安全规则。

Run:

```bash
python3 cadence-init/skills/skill-creator/scripts/quick_validate.py cadence-init/skills/knowledge-base-base-info
```

Expected: `Skill is valid`。

- [ ] **Step 8: 提交配置领域重构**

```bash
git add cadence-init/skills/knowledge-base-base-info
git commit -m "feat: add configuration snapshot knowledge domain"
```

---

### Task 4: 强制 Update 使用完整变更包

**Files:**

- Modify: `cadence-init/skills/knowledge-base-update/SKILL.md`
- Modify: `cadence-init/skills/knowledge-base-update/agents/openai.yaml`
- Modify: `cadence-init/skills/knowledge-base-update/assets/change-history-template.md`
- Modify: `cadence-init/skills/knowledge-base-update/references/incremental-update-guide.md`
- Modify: `cadence-init/skills/knowledge-base-update/references/demo.md`
- Create: `cadence-init/skills/knowledge-base-update/user-input/change-package/change-summary.md`
- Create: `cadence-init/skills/knowledge-base-update/user-input/change-package/code-change.md`
- Create: `cadence-init/skills/knowledge-base-update/user-input/change-package/database-change.md`
- Create: `cadence-init/skills/knowledge-base-update/user-input/change-package/configuration-change.md`
- Create: `cadence-init/skills/knowledge-base-update/user-input/change-package/verification.md`
- Create: `cadence-init/skills/knowledge-base-update/user-input/change-package/attachments/README.md`

**Interfaces:**

- Consumes: Manifest 4.0、用户显式指定的 `updates/CHANGE-变更标识/`、本地 MR 提交范围、数据库变化资料和配置新旧快照。
- Produces: 受影响实体更新、变更历史、`processed_packages`、新配置基线和可审计的来源冲突。

- [ ] **Step 1: 运行强制变更包前置失败检查**

Run:

```bash
test -f cadence-init/skills/knowledge-base-update/user-input/change-package/change-summary.md
```

Expected: 退出码 1。

- [ ] **Step 2: 创建 change-summary 模板**

固定包含：变更标识、目的、目标环境、涉及服务、业务影响、风险和领域变更矩阵。领域矩阵必须覆盖代码、数据模型、配置、中间件、接口和页面，并只允许 `有变更` 或 `无变更`。

- [ ] **Step 3: 创建代码与数据库变更模板**

`code-change.md` 固定包含：

```markdown
- 变更状态：有变更 / 无变更
- Merge Request 地址或编号：
- 源分支：
- 目标分支：
- 起始提交：
- 结束提交：
- 修改工程：
- 修改文件与符号：
- 无变更判断依据：
```

`database-change.md` 固定包含：变更状态、数据库/Schema、逻辑表、字段/索引/约束变化、DDL或迁移路径、上线状态、兼容性、回滚方式、无变更依据。

- [ ] **Step 4: 创建配置与验证模板**

`configuration-change.md` 固定包含：变更状态、环境、基线快照、目标快照、两个外部目录、两个快照指纹、纳入文件范围、涉及服务、配置组、已知差异、无变更依据。

`verification.md` 固定包含：已执行测试、发布验证、数据兼容验证、配置生效验证、回滚方式、未验证项目和风险。

`attachments/README.md` 说明可放脱敏 DDL 差异、迁移说明、配置差异摘要和 MR 导出说明，但不得放明文凭证或完整生产配置。

- [ ] **Step 5: 重写 Update 前置校验和执行流程**

`SKILL.md` 必须明确：

- 只接受 Manifest 4.0。
- 调用时必须显式指定目标项目的变更包路径。
- 五份文档全部强制存在。
- 无变更声明必须有判断依据。
- 代码有变更时 MR 信息和本地可验证提交范围都必须存在。
- 配置有变更时基线和目标快照必须同环境且目录可读。
- 缺失时返回目标补齐目录、插件模板目录、缺失字段和影响。
- Git Diff、代码扫描和快照比较只验证输入。
- 相同变更包重复执行保持幂等。

- [ ] **Step 6: 更新增量指南、历史模板、Demo 和 Agent 元数据**

增量指南写明以下影响链：

```text
变更包 → MR/提交 → 变更文件与符号 → 稳定 ID → 数据模型/配置/API/页面 → 受影响文档
```

变更历史模板增加变更包标识、MR、提交范围、数据库资料、配置快照、受影响实体和幂等标识。

Demo 覆盖：完整变更包、缺少数据库文档而停止、无配置变化但快照有差异、代码字段变化但数据库声明无变化、重复包不重复更新。

- [ ] **Step 7: 验证强制变更包规则**

Run:

```bash
for f in change-summary.md code-change.md database-change.md configuration-change.md verification.md; do test -f "cadence-init/skills/knowledge-base-update/user-input/change-package/$f"; done
```

Expected: 退出码 0。

Run:

```bash
rg -n '必须显式指定|五份|无变更.*判断依据|Merge Request|基线快照|目标快照|只能验证.*不能替代' cadence-init/skills/knowledge-base-update
```

Expected: Skill、指南、模板和 Demo 均覆盖强制输入规则。

Run:

```bash
python3 cadence-init/skills/skill-creator/scripts/quick_validate.py cadence-init/skills/knowledge-base-update
```

Expected: `Skill is valid`。

- [ ] **Step 8: 提交 Update 重构**

```bash
git add cadence-init/skills/knowledge-base-update
git commit -m "feat: require explicit knowledge base change packages"
```

---

### Task 5: 将 Context 扩展为四类渐进证据路径

**Files:**

- Modify: `cadence-init/skills/knowledge-base-context/SKILL.md`
- Modify: `cadence-init/skills/knowledge-base-context/agents/openai.yaml`
- Modify: `cadence-init/skills/knowledge-base-context/assets/task-context-template.md`
- Modify: `cadence-init/skills/knowledge-base-context/references/progressive-retrieval-guide.md`
- Modify: `cadence-init/skills/knowledge-base-context/references/task-profiles.md`
- Modify: `cadence-init/skills/knowledge-base-context/references/demo.md`
- Modify: `readmes/skills/knowledge-base-context.md`

**Interfaces:**

- Consumes: Manifest 4.0、KnowledgeBase 索引、当前代码、字段级表文档、DDL/迁移证据、服务配置文档、当前配置快照和相关变更包。
- Produces: 包含四类来源的最小任务上下文包，不修改 KnowledgeBase 或用户输入。

- [ ] **Step 1: 运行 Context Schema 4.0 前置失败检查**

Run:

```bash
rg -n '四类证据|DDL/数据模型证据|配置快照证据|Schema 4\.0' cadence-init/skills/knowledge-base-context
```

Expected: 无输出或内容不完整。

- [ ] **Step 2: 重写 Context 入口与前置校验**

更新 Frontmatter 和正文：

- 只在 Schema 4.0 KnowledgeBase 存在时使用。
- Manifest 非 4.0 时停止。
- 必须读取数据模型来源状态、配置基线快照、最近变更包和 Git 基线。
- 配置外部路径只读，不输出敏感值。

- [ ] **Step 3: 实现四类证据路径和渐进算法**

在 Skill 与检索指南中固定：

```text
知识库语义：README → 领域索引 → 稳定 ID → 关系矩阵
当前代码：任务对象 → 文件/符号 → 调用链 → 测试
数据模型：TABLE → 字段级模型 → Mapper/SQL/Entity → DDL/迁移
配置：服务/配置组 → 配置键 → 当前快照文件 → 绑定代码 → 生效条件
```

每次任务必须检查表和配置关系；没有直接关系时记录无直接关系，不继续扫描全部数据模型或配置包。

- [ ] **Step 4: 更新七类任务画像**

`task-profiles.md` 为每类画像增加：

- 需求澄清：数据能力、字段约束、环境开关。
- Design：表结构、数据源、Profile、Feature Flag。
- Plan：Mapper/SQL、字段映射、配置键、目标环境。
- Coding：数据库映射、配置生效链路、相关测试。
- Testing：Fixture、数据库约束、测试配置和环境差异。
- Review：MR、数据库变化、配置变化和变更包一致性。
- Debug：配置快照、生效条件、数据源路由、SQL 和字段状态。

- [ ] **Step 5: 扩展 Context 输出模板**

将证据矩阵改为：

```markdown
| 结论 | KnowledgeBase | 当前代码 | DDL/数据模型证据 | 配置快照证据 | 状态 | 任务影响 |
|------|---------------|----------|------------------|--------------|------|----------|
```

固定状态新增：`数据模型证据缺失` 和 `配置证据缺失`。输出中增加数据模型上下文、配置上下文和相关变更包小节。

- [ ] **Step 6: 更新异常规则、Demo、Agent 和用户说明**

覆盖：

- DDL 缺失时使用字段级模型、迁移和代码证据继续。
- 配置目录失效且任务依赖实际配置时阻断。
- 任务点名未处理变更包时读取该包并标记基线漂移。
- 页面任务沿 PAGE → API → SERVICE/MODULE 检查表与配置。
- 敏感值只返回键、用途、状态和绑定位置。

`readmes/skills/knowledge-base-context.md` 的输入目录、Schema、检索路径、FAQ 和相关 Skills 全部同步到 4.0。

- [ ] **Step 7: 验证 Context 四类证据契约**

Run:

```bash
rg -n '知识库语义|当前代码|数据模型|配置快照|DDL/数据模型证据|配置快照证据|Schema 4\.0' cadence-init/skills/knowledge-base-context readmes/skills/knowledge-base-context.md
```

Expected: Skill、指南、画像、模板、Demo 和用户说明均包含四类证据规则。

Run:

```bash
rg -n 'Schema 3\.0|schema_version: "3\.0"|Manifest 3\.0' cadence-init/skills/knowledge-base-context readmes/skills/knowledge-base-context.md
```

Expected: 无输出。

Run:

```bash
python3 cadence-init/skills/skill-creator/scripts/quick_validate.py cadence-init/skills/knowledge-base-context
```

Expected: `Skill is valid`。

- [ ] **Step 8: 提交 Context 重构**

```bash
git add cadence-init/skills/knowledge-base-context readmes/skills/knowledge-base-context.md
git commit -m "feat: add data and configuration context retrieval"
```

---

### Task 6: 让 API 与 Pages 关联字段级表和配置实体

**Files:**

- Modify: `cadence-init/skills/knowledge-base-api/SKILL.md`
- Modify: `cadence-init/skills/knowledge-base-api/agents/openai.yaml`
- Modify: `cadence-init/skills/knowledge-base-api/assets/api-capabilities-template.md`
- Modify: `cadence-init/skills/knowledge-base-api/references/api-analysis-guide.md`
- Modify: `cadence-init/skills/knowledge-base-api/references/demo.md`
- Modify: `cadence-init/skills/knowledge-base-api/references/demo_对内REST.md`
- Modify: `cadence-init/skills/knowledge-base-pages/SKILL.md`
- Modify: `cadence-init/skills/knowledge-base-pages/agents/openai.yaml`
- Modify: `cadence-init/skills/knowledge-base-pages/assets/page-capabilities-template.md`
- Modify: `cadence-init/skills/knowledge-base-pages/references/page-analysis-guide.md`
- Modify: `cadence-init/skills/knowledge-base-pages/references/demo.md`

**Interfaces:**

- Consumes: Manifest 4.0、`data-models/` 的 TABLE 稳定 ID、`configurations/` 的服务配置实体和 Base Info 关系矩阵。
- Produces: API 与页面文档中的字段级数据影响、配置依赖和可导航链接。

- [ ] **Step 1: 运行领域关联前置失败检查**

Run:

```bash
rg -n '配置实体|字段级表文档|configurations/|TABLE 稳定 ID' cadence-init/skills/knowledge-base-api cadence-init/skills/knowledge-base-pages
```

Expected: 无输出或关联规则不完整。

- [ ] **Step 2: 更新 API 前置输入与分析链**

API Skill 只接受 Manifest 4.0，并在能力分析中增加：

```text
API → SERVICE/MODULE → TABLE → 字段/SQL
API → SERVICE/MODULE → CONFIGURATION → 配置键/生效条件
```

只有直接影响请求、响应、副作用、路由、鉴权、中间件或外部系统的配置才进入 API 文档。

- [ ] **Step 3: 更新 API 模板与 Demo**

`api-capabilities-template.md` 新增：

- 数据模型影响：TABLE ID、读写类型、字段、Mapper/SQL 和表文档链接。
- 配置依赖：服务配置实体、配置键、生效条件、环境和配置文档链接。

两个 Demo 分别展示对外能力和对内 REST 如何链接表字段和配置键，不写真实环境值。

- [ ] **Step 4: 更新 Pages 前置输入与分析链**

Pages Skill 只接受 Manifest 4.0，沿以下关系渐进分析：

```text
PAGE/ROUTE → API → SERVICE/MODULE → TABLE/CONFIGURATION
```

页面不得根据字段同名直接关联表；必须通过 API 模型、请求代码或后端证据建立关系。

- [ ] **Step 5: 更新 Pages 模板与 Demo**

页面模板新增：关联 TABLE、字段来源、影响页面字段、环境/Feature Flag 配置、配置文档链接和证据状态。

Demo 展示页面字段通过 API 映射到表字段，以及页面能力受 Feature Flag 控制的证据链。

- [ ] **Step 6: 更新两个 Agent 元数据**

API 默认提示加入 Manifest 4.0、表字段和配置依赖；Pages 默认提示加入页面到 API、TABLE 和配置实体的关系。

- [ ] **Step 7: 验证 API/Pages 关联契约**

Run:

```bash
rg -n 'TABLE|字段|配置键|configurations/|data-models/' cadence-init/skills/knowledge-base-api cadence-init/skills/knowledge-base-pages
```

Expected: 两个 Skill、模板、指南和 Demo 均包含数据模型与配置关联。

Run:

```bash
for d in cadence-init/skills/knowledge-base-api cadence-init/skills/knowledge-base-pages; do python3 cadence-init/skills/skill-creator/scripts/quick_validate.py "$d"; done
```

Expected: 两次 `Skill is valid`。

- [ ] **Step 8: 提交 API 与 Pages 关联更新**

```bash
git add cadence-init/skills/knowledge-base-api cadence-init/skills/knowledge-base-pages
git commit -m "feat: link interfaces and pages to data and configuration"
```

---

### Task 7: 升级 Overview 导航和插件元数据

**Files:**

- Modify: `cadence-init/skills/knowledge-base-overview/SKILL.md`
- Modify: `cadence-init/skills/knowledge-base-overview/agents/openai.yaml`
- Modify: `cadence-init/skills/knowledge-base-overview/assets/project-overview-template.md`
- Modify: `cadence-init/skills/knowledge-base-overview/assets/knowledge-base-usage-template.md`
- Modify: `cadence-init/skills/knowledge-base-overview/references/demo.md`
- Modify: `cadence-init/skills/knowledge-base-overview/references/rules-integration-guide.md`
- Modify: `cadence-init/.claude-plugin/plugin.json`
- Modify: `.claude-plugin/marketplace.json`

**Interfaces:**

- Consumes: Manifest 4.0、Base Info、Interfaces、Pages、Services、Data Models、Configurations、Evidence 和 Change History。
- Produces: Schema 4.0 项目入口、使用规则、常见修改场景导航和同步的插件版本元数据。

- [ ] **Step 1: 运行 Overview 导航前置失败检查**

Run:

```bash
rg -n 'data-models/README\.md|configurations/README\.md|CONFIGURATION' cadence-init/skills/knowledge-base-overview
```

Expected: 无输出或导航内容不完整。

- [ ] **Step 2: 重写 Overview 输入和导航**

Overview 只接受 Manifest 4.0，并将以下入口设为一级导航：

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

- [ ] **Step 3: 更新核心流程和修改场景**

核心流程允许：

```text
PAGE → API → SERVICE/MODULE → TABLE → CONFIGURATION/MIDDLEWARE
```

常见修改场景至少覆盖：字段变更、SQL/Mapper 变更、配置键变更、Profile/Feature Flag、API 参数变更、页面字段变更和中间件配置变化。

- [ ] **Step 4: 更新项目模板、使用规则和 Demo**

项目入口只保留摘要和导航，不复制字段清单或全部配置键。

KnowledgeBase 使用规则明确：

- 修改前先使用 Context。
- 表相关任务读取字段级表文档及当前结构证据。
- 配置相关任务读取服务配置文档及当前快照证据。
- 变更完成后必须使用强制变更包执行 Update。

Demo 展示完整导航和一个包含 TABLE、CONFIGURATION 的核心流程。

- [ ] **Step 5: 更新代理接入指南和 Agent 元数据**

接入指南使用 Schema 4.0 路径和规则，不保留 Schema 3.0、旧目录或旧输入说明。Agent 默认提示明确生成数据模型和配置一级导航。

- [ ] **Step 6: 同步插件版本**

将以下两个位置的 `cadence-init` 版本从 `0.0.3` 升级为 `0.0.4`：

- `cadence-init/.claude-plugin/plugin.json`
- `.claude-plugin/marketplace.json`

插件描述增加“字段级数据模型、配置快照、强制变更包和渐进式任务上下文”。

- [ ] **Step 7: 验证 Overview 和插件元数据**

Run:

```bash
rg -n 'data-models/README\.md|configurations/README\.md|TABLE|CONFIGURATION|变更包' cadence-init/skills/knowledge-base-overview
```

Expected: Skill、模板、指南和 Demo 均包含一级导航和使用规则。

Run:

```bash
python3 -m json.tool cadence-init/.claude-plugin/plugin.json
```

Expected: 输出格式化 JSON，退出码 0。

Run:

```bash
python3 -m json.tool .claude-plugin/marketplace.json
```

Expected: 输出格式化 JSON，退出码 0。

Run:

```bash
python3 cadence-init/skills/skill-creator/scripts/quick_validate.py cadence-init/skills/knowledge-base-overview
```

Expected: `Skill is valid`。

- [ ] **Step 8: 提交 Overview 与插件版本更新**

```bash
git add cadence-init/skills/knowledge-base-overview cadence-init/.claude-plugin/plugin.json .claude-plugin/marketplace.json
git commit -m "feat: expose schema 4 knowledge base navigation"
```

---

### Task 8: 执行 Schema 4.0 端到端一致性验证

**Files:**

- Verify: `cadence-init/skills/knowledge-base-api/`
- Verify: `cadence-init/skills/knowledge-base-base-info/`
- Verify: `cadence-init/skills/knowledge-base-bootstrap/`
- Verify: `cadence-init/skills/knowledge-base-context/`
- Verify: `cadence-init/skills/knowledge-base-overview/`
- Verify: `cadence-init/skills/knowledge-base-pages/`
- Verify: `cadence-init/skills/knowledge-base-update/`
- Verify: `readmes/skills/knowledge-base-context.md`
- Verify: `cadence-init/.claude-plugin/plugin.json`
- Verify: `.claude-plugin/marketplace.json`

**Interfaces:**

- Consumes: Tasks 1–7 的全部 Schema 4.0 Skills、模板、参考资料和元数据。
- Produces: 无旧 Schema 残留、结构完整、格式有效、敏感规则一致且可进入代码评审的最终变更。

- [ ] **Step 1: 验证所有 KnowledgeBase Skills Frontmatter**

Run:

```bash
for d in cadence-init/skills/knowledge-base-api cadence-init/skills/knowledge-base-base-info cadence-init/skills/knowledge-base-bootstrap cadence-init/skills/knowledge-base-context cadence-init/skills/knowledge-base-overview cadence-init/skills/knowledge-base-pages cadence-init/skills/knowledge-base-update; do python3 cadence-init/skills/skill-creator/scripts/quick_validate.py "$d"; done
```

Expected: 七次 `Skill is valid`。

- [ ] **Step 2: 验证旧 Schema 已清除**

Run:

```bash
rg -n 'Schema 3\.0|schema_version: "3\.0"|Manifest 3\.0' cadence-init/skills/knowledge-base-* readmes/skills/knowledge-base-context.md
```

Expected: 无输出。

Run:

```bash
rg -n 'cadence/knowledgeBase|\bapis/' cadence-init/skills/knowledge-base-* readmes/skills/knowledge-base-context.md
```

Expected: 无输出。

- [ ] **Step 3: 验证初始化输入与强制变更包文件完整**

Run:

```bash
for f in base-info.md project-scope.md data-model-scope.md configuration-scope.md middleware-scope.md api-scope.md page-scope.md; do test -f "cadence-init/skills/knowledge-base-bootstrap/user-input/$f"; done
```

Expected: 退出码 0。

Run:

```bash
for f in change-summary.md code-change.md database-change.md configuration-change.md verification.md attachments/README.md; do test -f "cadence-init/skills/knowledge-base-update/user-input/change-package/$f"; done
```

Expected: 退出码 0。

- [ ] **Step 4: 验证关键 Schema 4.0 契约覆盖**

Run:

```bash
rg -l 'schema_version: "4\.0"|Schema 4\.0' cadence-init/skills/knowledge-base-{bootstrap,base-info,api,pages,overview,update,context}/SKILL.md
```

Expected: 输出七个 `SKILL.md` 文件。

Run:

```bash
rg -n 'data-models/README\.md|configurations/README\.md|configuration_snapshots|processed_packages|DDL/数据模型证据|配置快照证据' cadence-init/skills/knowledge-base-*
```

Expected: Bootstrap、Base Info、Update、Context、API、Pages 和 Overview 均能定位到相关契约。

- [ ] **Step 5: 验证 DDL 可选与敏感信息规则**

Run:

```bash
rg -n 'DDL.*必须提供|database-ddl\.sql.*必须|缺少 DDL.*停止' cadence-init/skills/knowledge-base-*
```

Expected: 无输出。

Run:

```bash
rg -n '<redacted>|不得.*密码|不得.*AccessKey|不得保存.*哈希' cadence-init/skills/knowledge-base-{bootstrap,base-info,update,context}
```

Expected: 四个相关 Skill 均包含敏感信息保护规则。

- [ ] **Step 6: 执行 JSON 与 Diff 格式检查**

Run:

```bash
python3 -m json.tool cadence-init/.claude-plugin/plugin.json
```

Expected: 退出码 0。

Run:

```bash
python3 -m json.tool .claude-plugin/marketplace.json
```

Expected: 退出码 0。

Run:

```bash
git diff --check
```

Expected: 无输出，退出码 0。

- [ ] **Step 7: 检查范围和未跟踪文件**

Run:

```bash
git status --short
```

Expected: 只出现本计划列出的 KnowledgeBase Skill、模板、用户说明和插件元数据变更；不得出现配置样本、敏感文件、`.DS_Store` 或无关用户文件。

- [ ] **Step 8: 提交最终一致性修正**

如果 Step 1–7 发现并修正了跨任务一致性问题：

```bash
git add cadence-init/skills/knowledge-base-api cadence-init/skills/knowledge-base-base-info cadence-init/skills/knowledge-base-bootstrap cadence-init/skills/knowledge-base-context cadence-init/skills/knowledge-base-overview cadence-init/skills/knowledge-base-pages cadence-init/skills/knowledge-base-update readmes/skills/knowledge-base-context.md cadence-init/.claude-plugin/plugin.json .claude-plugin/marketplace.json
git commit -m "chore: verify knowledge base schema 4 consistency"
```

如果没有任何修正，不创建空提交。

---

## 最终完成条件

- 七个 KnowledgeBase Skills 全部只接受 Schema 4.0。
- Bootstrap 六领域输入和 Manifest 4.0 完整。
- DDL 是可选证据，数据模型固定生成字段级表文档。
- 配置快照作为一级输入，配置明细固定生成到 `configurations/`。
- Update 缺少完整变更包时必定停止并返回补齐路径。
- Context 能渐进找到 TABLE、字段、DDL/迁移、配置键、快照文件和绑定代码。
- API、Pages 和 Overview 可导航到数据模型与配置领域。
- 插件版本与 Marketplace 版本一致。
- 所有 Skill Frontmatter、JSON 和 Git Diff 检查通过。
- 最终变更不包含敏感配置样本、旧 Schema 兼容逻辑或无关文件。
