# Proposal

## Why

`knowledge-base-bootstrap` 的唯一入口是目标项目的 `cadence/knowledge-base/user-input/base-info.md`。契约允许六领域状态取 `全量`/`指定`/`不适用`，其中 `database-ddl.sql` 与 `product.md` 是可选输入、`base-info.md` 的“业务知识证据”章节可整体省略，但 `base-info.md` 与六个领域 scope 文件在领域适用时必须由用户填写。

实际落地时这段人工成本很高：存量 Java + Vue/React 项目第一次建立 KnowledgeBase，用户要手工写出工程清单、数据模型结构证据、配置快照元信息、中间件清单、对外能力清单、页面路由清单六份范围文件；填错状态值、漏写不适用原因、留下失效资料链接，会让 bootstrap 在扫描前直接停止并返工。

这些内容有相当一部分是可以从目标项目自身证据客观推导的（构建文件与模块划分、Entity/Mapper/迁移文件、配置目录、依赖清单中的中间件、Controller 与前端路由定义），缺口集中在「用户权威声明」部分：哪些能力真正对外、配置快照锁定到哪个发布批次、产品目的与业务目标。

因此需要一个输入侧的草稿生成能力：只依据目标项目证据生成可用的输入版本，把不可推导的部分显式标为待确认，交由用户逐项确认后再进入 bootstrap。

## What Changes

- 新增 Skill `knowledge-base-user-input`：为尚未准备 Schema 4.0 输入的目标项目生成 `cadence/knowledge-base/user-input/` 下的 9 个输入文件草稿，并输出逐项确认清单。
- 草稿生成遵守既有输入契约：状态值只允许 `全量`/`指定`/`不适用`；不适用的领域必须给出原因；数据模型适用时至少一种可定位结构证据；配置适用时必须是锁定发布批次的不可变快照。
- 草稿只写入 `cadence/knowledge-base/user-input/`，不产生 `manifest.yaml`、`input-inventory.md` 等任何知识库固定产物，避免触发 bootstrap 的“固定产物存在但 Manifest 缺失”停止分支。
- 草稿落盘后不自动执行 `knowledge-base-bootstrap`，由用户确认后自行进入初始化。
- `knowledge-base-bootstrap` 在输入缺失时增加一条指引：可先调用 `knowledge-base-user-input` 生成草稿，但草稿仍需用户确认，bootstrap 不代替用户填写。
- 仓库文档与 `network-skill-install` 规格中的 skill 数量口径由 14 同步为 15。

## Capabilities

### New Capabilities

- `knowledge-base-user-input`: 目标项目缺失 Schema 4.0 输入文件时的草稿生成能力——前置门禁、只读证据采集、9 文件生成规则、草稿标记与确认清单交付边界。

### Modified Capabilities

- `network-skill-install`: skill 数量口径由 14 个同步为 15 个。

## Impact

- 新增目录 `cadence-init/skills/knowledge-base-user-input/`：`SKILL.md`、`references/evidence-mapping.md`、`references/demo.md`、`agents/openai.yaml`。
- 修改 `cadence-init/skills/knowledge-base-bootstrap/SKILL.md`：缺失输入时增加草稿生成指引（不改变 bootstrap 的校验、门禁与阶段语义）。
- 文档：`README.md`、`readmes/skills/README.md`、新增 `readmes/skills/knowledge-base-user-input.md`。
- 测试：`evals/kb/assertions/tier0.py` 增加新 Skill 与 bootstrap 模板一致性的结构断言。
- 行为变更：仅在用户显式调用新 Skill 时发生；既有 KnowledgeBase 初始化、续跑、完成保护与 Update 流程不受影响。
- 无 **BREAKING** 契约变更：`knowledge-base-bootstrap` 的输入契约、状态枚举与固定产物检测集合均未修改。
