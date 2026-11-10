# knowledge-base-user-input-scaffold 规格增量

## MODIFIED Requirements

### Requirement: 生成前置门禁（既有输入与既有知识库）

`knowledge-base-user-input` MUST 在写入任何文件前只读校验目标项目。目标 `cadence/knowledge-base/user-input/` 下已有文件时 MUST 先判定这些文件是已填写的用户输入还是未填写的模板占位：已填写时 MUST 只生成缺失文件且 MUST NOT 覆盖或改写已有文件，9 个输入文件全部存在时 MUST 停止并引导使用 `knowledge-base-bootstrap`；未填写的模板占位（基线信息字段仍为空、状态仍是模板默认占位、示例行与填写提示仍在）MUST 视为输入尚未准备，MUST 允许生成草稿覆盖并在报告中标明被覆盖的占位文件，同一目录中已填写的文件仍 MUST NOT 被覆盖。目标 `cadence/knowledge-base/` 下存在 `user-input/` 以外的固定产物（完整集合以 `knowledge-base-bootstrap` 的固定产物检测集合为准，含 `manifest.yaml`、`input-inventory.md` 与知识库文档目录）时 MUST 停止并引导 `knowledge-base-bootstrap`、`knowledge-base-context` 或 `knowledge-base-update`。

#### Scenario: 目标目录已有部分输入

- **WHEN** `user-input/base-info.md` 已存在而其余 8 个文件缺失
- **THEN** 只生成缺失文件，`base-info.md` 内容保持原样，输出中列出已存在与新生成的文件

#### Scenario: 九个文件已齐备

- **WHEN** `user-input/` 下 9 个输入文件全部存在且已填写
- **THEN** 立即停止，不写任何文件，提示改用 `knowledge-base-bootstrap` 校验并初始化

#### Scenario: 模板占位未填写

- **WHEN** `user-input/` 下 9 个文件都存在但内容仍是插件模板的原始占位
- **THEN** 视为输入尚未准备，生成草稿覆盖占位内容，并在报告中列出被覆盖的占位文件

#### Scenario: 知识库固定产物已存在

- **WHEN** 目标项目已有 `cadence/knowledge-base/manifest.yaml`
- **THEN** 立即停止，不生成任何输入草稿，引导 `knowledge-base-bootstrap` 续跑或 `knowledge-base-context` 查询

### Requirement: 敏感信息与草稿标记

生成文件 MUST NOT 包含密码、Token、AccessKey、Secret、密钥、私钥、完整连接串与内部域名、IP、URL；配置证据只记录配置键、用途与值类型，内部端点 MUST 写为 `<redacted>`。服务监听端口不含主机信息，MUST 允许作为服务标识保留在工程范围与页面范围文件中；带主机部分的地址（`host:port`、连接串、URL）MUST 按敏感内部地址处理。每个生成文件 MUST 带有草稿横幅，`【待确认】` 标记 MUST 只出现在备注、原因、说明等自由文本字段，MUST NOT 出现在状态值。

#### Scenario: 敏感值命中即停止写入

- **WHEN** 配置证据中出现未脱敏的 Token 或完整连接串
- **THEN** 停止写入该文件，报告位置，敏感值不落盘

#### Scenario: 端口与带主机地址分别处理

- **WHEN** 草稿需要登记服务端口与后端直连地址
- **THEN** 端口写入工程范围备注，直连地址与主机名按 `<redacted>` 处理且不落盘

#### Scenario: 待确认标记不污染状态

- **WHEN** 某领域存在待裁决项
- **THEN** 标记只出现在备注或原因字段，状态值仍逐字取三态之一

## ADDED Requirements

### Requirement: 规划能力与实现现状的区分

`knowledge-base-user-input` MUST 只把代码中已存在的入口登记进能力清单。需求或规划文档（issue、PRD、设计稿）描述但尚未实现的能力 MUST NOT 计入已实现清单，MUST 在清单说明段落登记为规划项并交用户裁决；发现规划项时 MUST NOT 因此把对应领域判为不适用。

#### Scenario: 规划文档中的能力未实现

- **WHEN** 规划文档描述了分类 CRUD、详情、编辑等能力而当前代码只有列表与创建
- **THEN** 已实现清单只含代码中存在的入口，规划项登记在说明段落并标注待确认，接口领域状态保持适用

#### Scenario: 规划项不进入稳定 ID 依据

- **WHEN** 能力清单含规划项说明
- **THEN** 规划项不作为稳定 ID 的生成依据，由 `knowledge-base-api` 阶段按实际实现生成稳定 ID