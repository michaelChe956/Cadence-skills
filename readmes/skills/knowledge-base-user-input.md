# knowledge-base-user-input Skill

## 概述

`knowledge-base-user-input` 为尚未准备 Schema 4.0 KnowledgeBase 输入的目标项目生成 `cadence/knowledge-base/user-input/` 下的 9 个输入文件草稿。

草稿只依据目标项目自身的代码、构建与配置证据推导，每条结论带 `文件:行号` 证据位置；无法从代码推导的部分（哪些能力真正对外、配置快照锁定到哪个发布批次、产品目的与业务目标）显式标为 `【待确认】`，由用户逐项裁决。

它是 `knowledge-base-bootstrap` 的输入前置，不是它的替代：草稿落盘后不会自动初始化，确认完成后仍由 `/knowledge-base-bootstrap` 校验输入并按固定顺序建立知识库。

## 使用前提

- 目标项目位于 Java 后端与 Vue/React 前端存量形态（至少具备其中一种）。
- 目标项目尚未建立 KnowledgeBase：`cadence/knowledge-base/` 下除 `user-input/` 外没有任何固定产物。
- `user-input/` 下尚不齐全 9 个文件，或已有文件仍是未填写的模板占位（基线信息为空、状态为默认占位）；已填写的文件不会被覆盖或改写。

## 生成的文件

```text
cadence/knowledge-base/user-input/
├── base-info.md            # 唯一入口：六领域状态、资料链接、不适用原因
├── project-scope.md        # 工程清单与纳入范围
├── data-model-scope.md     # 数据库、结构证据、分库分表、排除范围
├── configuration-scope.md  # 配置快照元信息与文件规则
├── middleware-scope.md     # 中间件清单
├── api-scope.md            # 对外能力清单（待用户裁决对外属性）
├── page-scope.md           # 前端应用、页面与路由
├── database-ddl.sql        # 可选证据：权威 DDL 或无 DDL 说明
└── product.md              # 可选输入：产品目的、目标用户、关键特性、业务目标
```

插件内置模板位于仓库源目录 `cadence-init/skills/knowledge-base-bootstrap/user-input/`；生成时结构与模板逐字一致，只删除指导语与示例行。

## 如何使用

### 自然语言自动触发

```text
这个项目还没准备知识库输入，帮我按项目现状生成一版输入草稿。
```

### Claude Code 手动调用（/knowledge-base-user-input）

```text
/knowledge-base-user-input
```

### Codex/pi/Kimi Code 手动调用（裸 skill 名）

```text
knowledge-base-user-input
```

调用名与仓库源目录 `cadence-init/skills/knowledge-base-user-input/` 一致，不使用插件命名空间或变量形式。

## 工作流程

1. 只读校验目标项目：已有输入、知识库已存在、项目形态不符时立即停止并报告。
2. 只读采集证据：构建文件与模块划分、数据模型结构证据、配置目录、中间件依赖、对外入口注解、前端路由定义。
3. 在内存中生成 9 个文件内容，逐个原子写入 `cadence/knowledge-base/user-input/`。
4. 执行生成后自检（状态枚举、资料链接、结构证据、快照字段、敏感信息、证据位置、模板列头）。
5. 输出确认清单，等待用户确认。

## 状态取值规则

| 领域 | 草稿取值依据 |
| --- | --- |
| 工程信息 | 固定适用 |
| 数据模型 | 存在可定位结构证据时 `全量`；否则 `不适用` + 原因 |
| 配置 | 本地工作目录不是不可变快照，默认 `不适用` + 原因；用户给出固定提交、标签或导出快照后才可改 `全量`/`指定` |
| 中间件 | 探测到中间件依赖时 `全量`；否则 `不适用` + 原因 |
| 接口 | 探测到入口时 `全量`；否则 `不适用` + 原因 |
| 页面 | 存在前端工程时 `全量`；否则 `不适用` + 原因 |

状态值逐字取 `全量`、`指定`、`不适用`，不带任何标记；待确认信息只出现在备注、原因与说明等自由文本字段。

## 确认清单

生成完成后输出逐文件清单：

| 文件 | 状态 | 关键结论 | 证据 | 待确认 |
| --- | --- | --- | --- | --- |

用户可以直接编辑文件修订，也可以在会话中确认后由该 Skill 修订。未经确认的草稿不得直接进入 `/knowledge-base-bootstrap`。

## 与 Bootstrap 的边界

- 不生成 `manifest.yaml`、`input-inventory.md` 或任何其它知识库固定产物。
- 不调用 `knowledge-base-bootstrap`，不调用任何领域 Skill。
- 不把未确认草稿当作用户权威输入消费。

## 常见问题

### Q：草稿能替代我填写输入吗？

不能。草稿只覆盖可从代码与配置推导的部分，对外属性、配置快照锁定批次、产品目标仍需用户裁决。

### Q：会覆盖我已经填好的文件吗？

不会。已存在的文件保持原样，只生成缺失文件；9 个文件齐全时直接停止。

### Q：配置快照没有不可变目录怎么办？

本地工作目录不满足契约要求，草稿把配置判为 `不适用` 并记录探测到的配置目录。用户提供固定提交、标签或导出快照后，改为 `全量` 或 `指定` 并补齐快照字段即可。

### Q：会不会执行迁移脚本或连数据库？

不会。该 Skill 只读扫描，不执行迁移、部署、发布、启动脚本，不连接数据库或配置中心。

## 相关 Skills

- `knowledge-base-bootstrap`：校验输入并初始化 Schema 4.0 KnowledgeBase。
- `knowledge-base-context`：初始化完成后按任务获取最小上下文。
- `knowledge-base-update`：使用完整变更包增量更新知识库。

## 技术细节

- [Skill 定义](../../cadence-init/skills/knowledge-base-user-input/SKILL.md)
- [证据映射](../../cadence-init/skills/knowledge-base-user-input/references/evidence-mapping.md)
- [典型场景](../../cadence-init/skills/knowledge-base-user-input/references/demo.md)
- [输入契约](../../cadence-init/skills/knowledge-base-bootstrap/references/input-contract.md)
