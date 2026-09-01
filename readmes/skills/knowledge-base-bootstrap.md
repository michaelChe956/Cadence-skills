# knowledge-base-bootstrap Skill

## 概述

`knowledge-base-bootstrap` 是 Schema 4.0 KnowledgeBase 的唯一初始化入口。它以目标项目的 `cadence/knowledge-base/user-input/base-info.md` 为入口，判定首次初始化、未完成续跑、已完成保护或显式重新初始化，再校验六领域输入并按固定顺序编排领域 Skills。

该 Skill 只生成和消费 Manifest Schema 4.0，不扩大扫描范围，不兼容或迁移旧版本知识库；用户输入和配置快照均只读。

## 使用前提

- 目标项目是 Java 后端与 Vue/React 前端存量项目。
- 已准备六领域输入，至少包含 `base-info.md` 和 `project-scope.md`。
- 配置为“全量”或“指定”时，来源必须是锁定发布批次的不可变快照目录。
- 输入不完整时，Skill 返回缺失项、模板路径和继续入口，不自行猜测范围。

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

六个领域分别声明“全量”“指定”或“不适用”；“不适用”必须给出具体原因。数据模型为“全量”或“指定”时，需要 DDL、迁移、Entity、Mapper、SQL 或人工资料中的至少一种可定位结构证据。

插件内置模板位于仓库源目录 `cadence-init/skills/knowledge-base-bootstrap/user-input/`，仅供参考；Bootstrap 不代替用户填写，也不会把模板复制为目标项目事实。

## 如何使用

### 自然语言自动触发

在目标项目完成输入准备后，可以提出：

```text
为这个项目建立 Schema 4.0 KnowledgeBase，六领域输入我已经填好了。
```

或：

```text
上次初始化中断了，帮我继续。
```

### Claude Code 手动调用（/knowledge-base-bootstrap）

```text
/knowledge-base-bootstrap
```

### Codex/pi/Kimi Code 手动调用（裸 skill 名）

使用裸 Skill 名 `knowledge-base-bootstrap`，例如在支持命令输入的客户端中调用：

```text
knowledge-base-bootstrap
```

调用名与仓库源目录 `cadence-init/skills/knowledge-base-bootstrap/` 一致，不使用插件命名空间或变量形式。

## 初始化生命周期判定

| 情形 | 判定 | 行为 |
| --- | --- | --- |
| 无固定产物 | 首次初始化 | 生成输入清单和 Manifest 后按固定顺序执行 |
| Manifest 缺失、不可解析或不是 4.0 | 停止 | 不覆盖、不迁移、不删除，报告现状 |
| Manifest 4.0 但初始化块缺失 | 兼容判定 | 只读验收并按结果补齐初始化状态 |
| 初始化状态损坏或矛盾 | 停止 | 报告异常字段，不自动修复 |
| `status: in_progress` | 未完成续跑 | 从首个未完成阶段继续，复用一致的已完成阶段 |
| `status: complete` | 已完成保护 | 不重复初始化，引导使用 Context 或 Update |
| 用户明确请求“重新初始化 Schema 4.0” | 破坏性重建 | 二次授权和全部门禁通过后才清理并重建 |

普通修复、补文档、Context 或 Update 请求不构成重新初始化授权。

## 初始化状态不变量

`coverage.initialization` 是初始化进度的唯一事实来源：

- `status` 只能是 `in_progress` 或 `complete`；全局验收只能是 `pending`、`failed` 或 `passed`。
- `completed_stages` 必须遵循 `base-info → api → pages → overview → global-validation`，不得重复或逆序。
- 只有 `api`、`pages` 可以跳过，并且跳过必须登记非空原因。
- `status: complete` 只有在适用阶段全部完成、非适用阶段正确跳过、全局验收通过且产物一致时成立。

状态损坏时，所有相关 Skill 停止且不修改产物。

## 固定阶段顺序

```text
1. base-info         基础信息、服务、字段级数据模型和配置知识
2. api               适用时分析 API 和集成能力，否则登记跳过原因
3. pages             适用时分析页面能力，否则登记跳过原因
4. overview          生成入口、导航、术语和项目规则
5. global-validation 全局验收，通过后才标记 complete
```

每个阶段完成后更新 Manifest。全局验收会核对范围、文档登记、索引链接、稳定 ID、待确认项、模板占位符和敏感信息。

## 配置快照安全

- 分析前后核对最终快照指纹与 Manifest 授权指纹。
- 同一 `snapshot_id` 不得映射到不同环境或外部目录。
- Manifest 只记录指纹、来源元数据和范围摘要，不保存原始配置或敏感值。
- 密码、Token、密钥、连接串及内部地址统一写为 `<redacted>`。

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
├── domain-glossary.md
├── open-questions.md
└── change-history.md
```

上述是目标项目的生成目录，不是本仓库安装目录。仓库内定义文件仍位于 `cadence-init/skills/knowledge-base-bootstrap/`。

## 完成报告

完成或停止时报告：判定状态、Manifest Schema、Git 基线、六领域范围、执行/复用/跳过阶段、文档数量、对外能力来源、待确认计数、降级项、风险和全局验收结果。未通过验收时不使用“初始化完成”表述。

## 常见问题

### Q：输入不完整会怎样？

停止并返回缺失项、模板路径和补齐后的继续入口，不自行扩大扫描。

### Q：没有 DDL 能初始化吗？

可以。迁移、Entity、Mapper、SQL 或人工资料只要能提供可定位结构证据即可；完全没有结构证据时停止，或将该领域明确标记为“不适用”。

### Q：中断后如何继续？

再次调用 `/knowledge-base-bootstrap`。合法的 `in_progress` 状态会从首个未完成阶段续跑。

### Q：知识库已完成后再次执行会怎样？

触发完成保护，不修改既有产物，改用 `knowledge-base-context` 查询或 `knowledge-base-update` 更新。

### Q：会自动安装依赖或连接数据库吗？

不会。Bootstrap 不下载依赖、不连接数据库或配置中心、不执行迁移、部署、发布或启动脚本。

## 相关 Skills

- `knowledge-base-base-info`：生成基础信息、服务文档、字段级数据模型和配置知识。
- `knowledge-base-api`：分析对外能力和工程内对内能力。
- `knowledge-base-pages`：分析页面、路由、权限和 API 关联。
- `knowledge-base-overview`：生成知识库入口和项目使用规则。
- `knowledge-base-context`：初始化完成后按任务获取最小上下文。
- `knowledge-base-update`：使用完整变更包增量更新知识库。

## 技术细节

- [Skill 定义](../../cadence-init/skills/knowledge-base-bootstrap/SKILL.md)
- [输入契约](../../cadence-init/skills/knowledge-base-bootstrap/references/input-contract.md)
- [典型判定案例](../../cadence-init/skills/knowledge-base-bootstrap/references/demo.md)
- [输入模板](../../cadence-init/skills/knowledge-base-bootstrap/user-input/)
