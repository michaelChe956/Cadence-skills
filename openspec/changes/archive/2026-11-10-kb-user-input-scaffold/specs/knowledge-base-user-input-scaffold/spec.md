# knowledge-base-user-input 规格增量

## ADDED Requirements

### Requirement: 生成前置门禁（既有输入与既有知识库）

`knowledge-base-user-input` MUST 在写入任何文件前只读校验目标项目。目标 `cadence/knowledge-base/user-input/` 下已有文件时 MUST 只生成缺失文件且 MUST NOT 覆盖或改写已有文件，9 个输入文件全部存在时 MUST 停止并引导使用 `knowledge-base-bootstrap`。目标 `cadence/knowledge-base/` 下存在 `user-input/` 以外的固定产物（完整集合以 `knowledge-base-bootstrap` 的固定产物检测集合为准，含 `manifest.yaml`、`input-inventory.md` 与知识库文档目录）时 MUST 停止并引导 `knowledge-base-bootstrap`、`knowledge-base-context` 或 `knowledge-base-update`。

#### Scenario: 目标目录已有部分输入

- **WHEN** `user-input/base-info.md` 已存在而其余 8 个文件缺失
- **THEN** 只生成缺失文件，`base-info.md` 内容保持原样，输出中列出已存在与新生成的文件

#### Scenario: 九个文件已齐备

- **WHEN** `user-input/` 下 9 个输入文件全部存在
- **THEN** 立即停止，不写任何文件，提示改用 `knowledge-base-bootstrap` 校验并初始化

#### Scenario: 知识库固定产物已存在

- **WHEN** 目标项目已有 `cadence/knowledge-base/manifest.yaml`
- **THEN** 立即停止，不生成任何输入草稿，引导 `knowledge-base-bootstrap` 续跑或 `knowledge-base-context` 查询

### Requirement: 生成前置门禁（项目形态与只读边界）

`knowledge-base-user-input` MUST 只在目标项目具备 Java 后端特征（`pom.xml`/`build.gradle` 且存在 `src/main/java`）或 Vue/React 前端特征（`package.json` 且依赖 vue/react）时执行，两者都不具备时 MUST 停止并报告。MUST NOT 执行迁移文件、部署脚本、发布脚本或启动脚本，MUST NOT 连接数据库、配置中心或远程环境，MUST NOT 安装依赖，MUST NOT 修改业务代码、DDL 或运行配置。

#### Scenario: 非目标项目形态

- **WHEN** 目标项目既无 Java 构建特征也无前端 `package.json`
- **THEN** 停止并报告项目形态不匹配，不创建 `user-input/` 目录

#### Scenario: 只有后端形态

- **WHEN** 目标项目只有 Java 后端工程且无前端工程
- **THEN** 按实际形态生成，在 `base-info.md` 分析说明中写明项目形态，不虚构前端范围

### Requirement: 只读证据采集

`knowledge-base-user-input` MUST 只依据目标项目自身的可读证据推导输入内容，每条结论 MUST 保留 `文件:行号` 证据位置；MUST NOT 引用目标项目之外的资料、既有知识库内容或推测结论。证据采集 MUST 覆盖构建文件与模块划分、数据模型结构证据、配置来源目录、中间件依赖与配置线索、对外入口注解与前端路由定义。

#### Scenario: 结论锚定到代码位置

- **WHEN** 草稿把某个 REST 能力登记进对外能力清单
- **THEN** 该行备注给出控制器文件与行号，且能力类型与探测到的注解一致

#### Scenario: 无证据即不推导

- **WHEN** 目标项目没有任何可定位结构证据
- **THEN** 数据模型不登记推测表结构，状态落到 `不适用` 并写明原因

### Requirement: 九文件结构与状态取值

`knowledge-base-user-input` MUST 在 `cadence/knowledge-base/user-input/` 生成 `base-info.md`、`project-scope.md`、`data-model-scope.md`、`configuration-scope.md`、`middleware-scope.md`、`api-scope.md`、`page-scope.md`、`database-ddl.sql`、`product.md` 九个文件，结构 MUST 与 `cadence-init/skills/knowledge-base-bootstrap/user-input/` 的模板一致，MUST 删除面向填写者的指导语与示例行。六领域状态值 MUST 逐字取 `全量`、`指定` 或 `不适用`，MUST NOT 在状态值中附加任何标记；`不适用` MUST 给出非空原因。

#### Scenario: 状态值保持纯净

- **WHEN** 某领域的适用性需要用户裁决
- **THEN** 该领域状态写三态之一，待确认说明写在备注或原因字段，bootstrap 校验该状态值时不会命中非法状态

#### Scenario: 不适用领域不留失效链接

- **WHEN** 目标项目没有前端工程
- **THEN** 不生成 `page-scope.md`，`base-info.md` 页面状态为 `不适用` 并写明原因，且不含指向 `page-scope.md` 的资料链接

#### Scenario: 不适用但有证据仍保留文件

- **WHEN** 某领域判为 `不适用` 但探测到该领域证据
- **THEN** 仍生成对应 scope 文件作为证据记录，`base-info.md` 保留资料链接并写明不适用原因

### Requirement: 领域文件的证据登记规则

数据模型状态为 `全量` 或 `指定` 时 `data-model-scope.md` MUST 至少登记一种契约允许的结构证据（DDL、数据库迁移文件、Entity、Mapper 接口、Mapper XML、普通 SQL、人工资料）。配置状态为 `全量` 或 `指定` 时 `configuration-scope.md` MUST 填写快照标识、环境、外部目录、锁定依据、范围摘要、纳入文件数量或清单摘要、服务摘要与文件规则摘要，否则配置状态 MUST 为 `不适用`。`database-ddl.sql` MUST 只复制权威 DDL 文件内容，找不到时 MUST 只写“未找到权威 DDL，结构证据见 data-model-scope.md”的说明，MUST NOT 编造表结构。对外能力清单 MUST 列出探测到的全部入口且状态列写 `待确认`，MUST NOT 自行判定对外属性。

#### Scenario: 配置默认不适用

- **WHEN** 目标项目只有本地工作目录中的配置
- **THEN** 配置状态为 `不适用`，原因写明本地目录不是锁定发布批次的不可变快照，同时 `configuration-scope.md` 记录探测到的配置目录与纳入文件数量供用户改判

#### Scenario: 对外能力清单不漏项

- **WHEN** 目标项目存在 3 个 REST 控制器
- **THEN** `api-scope.md` 的清单包含全部 3 个入口且状态列为 `待确认`，不擅自判定对外属性

#### Scenario: 无 DDL 时不编造

- **WHEN** 目标项目没有权威 DDL 文件但有 Entity 与 Mapper 证据
- **THEN** `database-ddl.sql` 只写说明行，数据模型仍以其他结构证据登记为适用

### Requirement: 敏感信息与草稿标记

生成文件 MUST NOT 包含密码、Token、AccessKey、Secret、密钥、私钥、完整连接串与内部域名、IP、URL；配置证据只记录配置键、用途与值类型，内部端点 MUST 写为 `<redacted>`。每个生成文件 MUST 带有草稿横幅，`【待确认】` 标记 MUST 只出现在备注、原因、说明等自由文本字段，MUST NOT 出现在状态值。

#### Scenario: 敏感值命中即停止写入

- **WHEN** 配置证据中出现未脱敏的 Token 或完整连接串
- **THEN** 停止写入该文件，报告位置，敏感值不落盘

#### Scenario: 待确认标记不污染状态

- **WHEN** 某领域存在待裁决项
- **THEN** 标记只出现在备注或原因字段，状态值仍逐字取三态之一

### Requirement: 生成后自检与确认清单交付

`knowledge-base-user-input` MUST 在写完全部文件后执行自检：9 个文件齐备、`user-input/` 外无新增文件、`base-info.md` 六领域状态值合法、不适用领域有非空原因、资料链接均指向存在文件、数据模型适用时存在结构证据、配置适用时快照字段完整、状态值不含待确认标记、无敏感值、每条结论有证据位置或显式待确认标记、表格列头与模板一致。自检不通过时 MUST 报告未通过项与影响，MUST NOT 声明草稿可用。自检通过后 MUST 在会话中输出确认清单：逐文件列出关键结论、证据位置、待确认项与建议动作，并明确说明草稿未经用户确认不得进入 `knowledge-base-bootstrap`。

#### Scenario: 自检通过后的确认交付

- **WHEN** 9 个文件生成完毕且自检全部通过
- **THEN** 输出确认清单，逐文件列出状态、结论、证据位置与待确认问题，并提示用户确认后再执行 `/knowledge-base-bootstrap`

#### Scenario: 自检未过不声明可用

- **WHEN** 自检发现某领域状态值非法
- **THEN** 报告未通过项与影响，不声明草稿可用

### Requirement: 草稿与 Bootstrap 的边界

`knowledge-base-user-input` MUST NOT 生成 `manifest.yaml`、`input-inventory.md` 或任何其它知识库固定产物，MUST NOT 调用 `knowledge-base-bootstrap`，MUST NOT 把未确认草稿当作用户权威输入消费。`knowledge-base-bootstrap` 在输入缺失时 MUST 指引用户可先调用 `knowledge-base-user-input` 生成草稿，但 MUST 继续以现有输入契约校验输入，MUST NOT 代替用户填写，MUST NOT 直接采信未经用户确认的草稿。

#### Scenario: 草稿生成后不自动初始化

- **WHEN** 草稿生成完成
- **THEN** 不产生 Manifest、不执行任何领域阶段，控制流停在等待用户确认

#### Scenario: Bootstrap 缺失输入时的指引

- **WHEN** bootstrap 校验输入时发现六领域输入缺失
- **THEN** 返回缺失项、模板路径与继续入口，并额外指引可先调用 `knowledge-base-user-input` 生成草稿，仍要求用户确认后才可继续