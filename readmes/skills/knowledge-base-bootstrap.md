# knowledge-base-bootstrap Skill

## 概述

`knowledge-base-bootstrap` 是 Schema 4.0 KnowledgeBase 的唯一初始化入口。

它以目标项目的 `cadence/knowledge-base/user-input/base-info.md` 为唯一入口，先判定初始化生命周期（首次初始化、未完成续跑、已完成保护、显式重新初始化），再校验六领域输入，并按固定顺序编排 `knowledge-base-base-info`、`knowledge-base-api`、`knowledge-base-pages`、`knowledge-base-overview` 和内置 `global-validation` 验收阶段。

该 Skill 只生成和消费 Manifest Schema 4.0；输入不完整时返回模板和继续入口，不扩大扫描范围，也不兼容或迁移旧版本知识库。

## 使用前提

- 目标项目为 Java 后端与 Vue/React 前端存量项目。
- 已准备好六领域输入文件，至少 `base-info.md` 与 `project-scope.md` 声明了工程范围。
- 配置领域为 `全量` 或 `指定` 时，配置来源必须是锁定发布批次的不可变快照目录（固定到明确提交、标签或导出快照），不能使用持续变化的工作目录。
- 用户输入和外部配置快照只读，Bootstrap 不会覆盖、补写、复制或迁入知识库。

## Schema 4.0 输入目录

```text
cadence/knowledge-base/user-input/
├── base-info.md            # 唯一入口
├── project-scope.md
├── data-model-scope.md
├── configuration-scope.md
├── middleware-scope.md
├── api-scope.md
├── page-scope.md
└── database-ddl.sql        # 可选
```

六个领域分别声明 `全量`、`指定` 或 `不适用`；`不适用` 必须给出非空原因。数据模型为 `全量` 或 `指定` 时，至少需要一种可定位的结构证据（DDL、迁移、Entity、Mapper、SQL 或人工资料）；DDL 可缺省，其他证据有效时继续。

| 状态 | 含义 |
|------|------|
| `全量` | 引用文件必须存在可读，在声明的工程范围内全盘分析该领域 |
| `指定` | 引用文件必须存在，指定清单或匹配规则不得为空，只分析明确范围及必要依赖 |
| `不适用` | 必须写明原因，领域被跳过；`api`、`pages` 不适用时登记到 Manifest 的 `skipped_stages` |

### 填写案例

假设一个 Java 订单服务 + Vue 管理后台，纯内部系统、无对外开放 API：

```markdown
<!-- base-info.md（唯一入口，声明六领域状态） -->
- 工程信息：全量 → project-scope.md
- 数据模型：指定 → data-model-scope.md
- 配置：指定 → configuration-scope.md
- 中间件：指定 → middleware-scope.md
- 接口：不适用（系统仅内部使用，无对外开放 API）
- 页面：全量 → page-scope.md
```

```markdown
<!-- project-scope.md -->
- 工程路径：/home/me/order-service（Java/Spring Boot）
- 工程路径：/home/me/order-admin（Vue 3）
```

```markdown
<!-- data-model-scope.md -->
- 数据库：order_db
- 指定表：orders、order_item
- 结构证据：database-ddl.sql
```

```markdown
<!-- middleware-scope.md -->
- 指定中间件：RocketMQ（订单消息）、Redis（缓存）
```

接口声明 `不适用` 后，生成的 Manifest 会跳过 `api` 阶段：

```yaml
scope:
  api:
    status: 不适用
coverage:
  initialization:
    completed_stages: [base-info]
    skipped_stages:
      - stage: api
        reason: 系统仅内部使用，无对外开放 API
```

编排顺序变为 `base-info →（跳过 api）→ pages → overview → global-validation`。

插件内置模板目录：

```text
cadence-init/skills/knowledge-base-bootstrap/user-input/
```

Bootstrap 只引用模板，不代替用户填写。

## 如何使用

### 自然语言自动触发

```text
为这个项目建立 KnowledgeBase，六领域输入我已经填好了。
```

```text
上次初始化中断了，帮我继续。
```

```text
知识库已经建好了，接下来该用什么？
```

### Claude Code 手动调用

```text
/cadence-init:knowledge-base-bootstrap
```

### Codex 手动调用

```text
$knowledge-base-bootstrap
```

`agents/openai.yaml` 只提供 Codex 展示名称和默认提示，不负责安装或触发注册。

## 初始化生命周期判定

Bootstrap 按以下唯一顺序判定，任何一步不匹配即停止：

| 情形 | 判定 | 行为 |
|------|------|------|
| 无任何固定产物 | 首次初始化 | 生成 `input-inventory.md` 与 `manifest.yaml` 后按固定顺序执行阶段 |
| 有产物但 Manifest 缺失/不可解析/非 4.0 | 停止 | 不覆盖、不迁移、不删除，报告现状 |
| Manifest 4.0 且 `coverage.initialization` 块缺失 | 兼容分支 | 只读执行完整 `global-validation`，按实际验收结果一次性回填初始化块 |
| 初始化块损坏或矛盾 | 停止 | 报告每个异常字段的实际值与违反的不变量，不自动修复 |
| 合法 `status: in_progress` | 未完成续跑 | 从固定顺序中首个未完成阶段继续，已完成且产物一致的阶段直接复用 |
| 合法 `status: complete` | 完成保护 | 停止重复初始化，引导使用 Context 或 Update |
| 用户显式请求“重新初始化 Schema 4.0” | 破坏性重建 | 二次明确授权 + 全部扫描前门禁通过后，才清理旧产物并全量重建 |

普通初始化、补文档、修复、Context 或 Update 请求均不构成清理授权。

## 初始化状态不变量

`coverage.initialization` 是初始化的唯一进度事实来源：

- `status` 只能是 `in_progress` 或 `complete`；`global_validation` 只能是 `pending`、`failed` 或 `passed`。
- `completed_stages` 是固定阶段序列 `base-info → api → pages → overview → global-validation` 的合法前缀或子序列，无重复、不逆序。
- `skipped_stages` 每项只有 `stage` 和 `reason` 两个键；只有 `api`、`pages` 可跳过，`base-info`、`overview`、`global-validation` 永不可跳过。
- `scope.api.status: 不适用` 时 `api` 必须且只能出现在 `skipped_stages`；接口适用时不得跳过。`pages` 同理。
- `status: complete` 当且仅当：适用阶段全部完成、不适用阶段正确跳过、`global_validation: passed`、`completed_at` 非空，且与实际产物一致。

任何续跑、复用、领域调用、完成保护或写入前都会重新校验上述不变量；状态损坏时所有 Skill 立即停止且不修改任何产物。

## 固定阶段顺序

```text
1. base-info         始终执行：基础信息、服务、字段级数据模型、配置知识
2. api               仅 scope.api 适用时执行，否则登记跳过原因
3. pages             仅 scope.pages 适用时执行，否则登记跳过原因
4. overview          所有适用领域完成后执行：入口、导航、术语、项目规则
5. global-validation 内置验收：通过后才把 status 标记为 complete
```

每个阶段完成后立即把阶段 ID 原子写入 `completed_stages`；已在 Manifest 登记为完成且文档、索引、证据一致的阶段直接复用，不重复扫描。

`global-validation` 会核对六领域范围、文档登记、索引链接、稳定 ID、对外能力分类、待确认四级计数、模板占位符、敏感信息，并显式拒绝仍存在 `待后续阶段补齐（api）` / `待后续阶段补齐（pages）` 的知识库。验收失败时保留可续跑状态（`global_validation: failed`），不会把部分产物报告为初始化完成。

## 配置快照安全

- 清理前和分析结束时分别计算最终快照指纹，必须与 Manifest 授权指纹一致；不一致立即停止，不连接配置中心或远程环境补取。
- 同一 `snapshot_id` 不得映射到不同环境或不同外部目录。
- Manifest 只保存最终指纹、来源元数据和可审计范围摘要，不保存原始配置内容、单文件哈希或敏感值哈希。
- 密码、Token、密钥、完整连接串、内部域名/IP/URL 等敏感值统一写为 `<redacted>`。

## 固定输出

```text
cadence/knowledge-base/
├── user-input/
├── input-inventory.md
├── manifest.yaml
├── README.md
├── base-information.md
├── development-guide.md
├── interfaces/
├── pages/
├── services/
├── data-models/
├── configurations/
├── evidence/
│   ├── source-index.md
│   └── traceability-matrix.md
├── domain-glossary.md
├── open-questions.md
└── change-history.md
```

## 完成报告

初始化结束时报告：初始化判定、Manifest Schema、Git 基线、六领域范围、实际执行/复用/跳过阶段、文档数量、对外能力清单来源、`open_questions` 四级计数、工具或证据降级项、剩余风险和 `global-validation` 验收结果。未通过全局验收时不会使用“初始化完成”表述。

## 常见问题

### Q: 输入不完整会怎样

Bootstrap 停止并返回缺失项、对应模板路径和补齐后的继续入口，不会自行猜测范围或扩大扫描。

### Q: 没有 DDL 能初始化吗

可以。数据模型为 `全量` 或 `指定` 时，只要迁移、Entity、Mapper、SQL 或人工资料中至少有一种可定位结构证据即可继续；完全没有结构证据时停止，或要求把数据模型领域改为 `不适用`。

### Q: 中断后如何继续

直接再次执行 Bootstrap。合法 `in_progress` 状态会从首个未完成阶段续跑，已完成且产物一致的阶段直接复用，不重复扫描。

### Q: 知识库已完成后再次执行会怎样

触发完成保护：不修改任何既有产物，并引导使用 `knowledge-base-context` 查询或 `knowledge-base-update` 处理变更包。

### Q: 如何重建知识库

必须显式请求“重新初始化 Schema 4.0”。Bootstrap 会报告拟清理的精确路径、人工内容丢失、基线失效风险和全量重建范围，取得针对该范围的再次明确授权，且六领域输入、结构证据、配置快照等全部扫描前门禁通过后，才清理旧产物。

### Q: 会自动安装依赖或连数据库吗

不会。Bootstrap 不下载或安装依赖，不连接任何数据库、配置中心或远程环境，不执行迁移、部署、发布或启动脚本；这些脚本只作为只读证据。

## 相关 Skills

- `knowledge-base-base-info`：阶段 1，生成基础信息、服务文档、字段级数据模型和配置知识。
- `knowledge-base-api`：阶段 2，分析对外能力和工程内对内能力。
- `knowledge-base-pages`：阶段 3，分析页面、路由、权限和 REST API 关联。
- `knowledge-base-overview`：阶段 4，生成知识库入口、关系导航和项目使用规则。
- `knowledge-base-context`：初始化完成后按任务获取最小上下文。
- `knowledge-base-update`：使用完整变更包幂等更新已有知识库。

## 技术细节

- [Skill 定义](../../cadence-init/skills/knowledge-base-bootstrap/SKILL.md)
- [输入契约](../../cadence-init/skills/knowledge-base-bootstrap/references/input-contract.md)
- [典型判定案例](../../cadence-init/skills/knowledge-base-bootstrap/references/demo.md)
- [Manifest 模板](../../cadence-init/skills/knowledge-base-bootstrap/assets/manifest-template.yaml)
