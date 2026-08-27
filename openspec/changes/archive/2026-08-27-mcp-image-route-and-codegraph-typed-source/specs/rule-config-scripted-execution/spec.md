# rule-config-scripted-execution 变更提案

## MODIFIED Requirements

### Requirement: 项目配置产物与现行语义一致

脚本 MUST 保留现行项目配置相关产物语义：脚本 MUST NOT 检测项目技术栈（语言、包管理器、测试/检查/格式化命令、覆盖率），MUST NOT 在入口文件写入或更新 `### 项目技术栈` 块、包管理器规则或覆盖率阈值；入口中用户既有的技术栈内容 MUST 逐字保留。入口文件 `## 项目配置` 章节仅维护"产物自动提交（design/plan/code）"开关；旧名"产物自动提交（design/plan）"开关行 MUST 按身份迁移处理（保留用户值，归并后恰好一行新名开关行）。历史产物目录仅检测现行精确目录集合，no-interrupt 模式 MUST 只写入报告且 SHALL NOT 执行移动、合并、删除或清理，普通模式 SHALL 按现行迁移表处理且目标目录非空时跳过并报告冲突；`cadence/` 默认不加入 `.gitignore`；`.codegraph/` 在 Coding 项目或 `--enable-codegraph` 时 SHALL 加入 `.gitignore`，`codegraph.json` MUST NOT 加入；Playwright 规则默认跳过。代码阅读规则的来源模板选择与入口摘要文案渲染 MUST 与最终 project_type 一致且仅消费同一裁决结果；`--enable-codegraph` MUST 仅影响 CodeGraph 安装与初始化步骤，MUST NOT 改变最终 project_type、代码阅读/代码使用规则来源或任何入口摘要文案。no-interrupt 的类型裁决行为（以检测结果为准、忽略 CLI 项目类型参数）MUST 保持不变。

#### Scenario: 技术栈检测写入入口
- **WHEN** 项目存在 package.json 等主工程配置且入口文件不含技术栈块
- **THEN** 脚本 MUST NOT 检测或写入任何技术栈字段
- **AND** 入口文件既有的 `### 项目技术栈` 用户内容 MUST 逐字保留

#### Scenario: 旧名开关行确定性迁移
- **WHEN** 目标入口文件含旧名开关行 `- **产物自动提交（design/plan）**：开启`
- **THEN** 脚本 MUST 将其替换为新名开关行 `- **产物自动提交（design/plan/code）**：开启`
- **AND** 迁移后全文件恰好一行开关行

#### Scenario: no-interrupt 历史目录只报告
- **WHEN** no-interrupt 模式检测到历史产物目录
- **THEN** 脚本 MUST 仅在报告中列出检测到的目录
- **AND** SHALL NOT 执行 `mv`、目录内容合并、目录删除或空目录清理

#### Scenario: 普通模式历史目录无冲突迁移
- **WHEN** 普通模式检测到历史目录且目标 `cadence/<dir>` 不存在或为空
- **THEN** 系统 SHALL 按现行迁移表迁移
- **AND** 目标非空时 MUST 跳过该目录并报告冲突，不覆盖、不合并

#### Scenario: code-reading 来源按最终项目类型单选
- **WHEN** S3 受管规则生成阶段执行
- **THEN** 脚本 MUST 以最终 project_type 对应的代码阅读来源模板生成落地文件
- **AND** drift 与幂等判定 MUST 针对该所选来源模板比较
- **AND** `.claude/rules/` 下 MUST NOT 落地带项目类型后缀的代码阅读来源文件

#### Scenario: 显式启用不改变规则模板来源
- **WHEN** 非 Coding 项目携带用户显式的 CodeGraph 启用开关运行
- **THEN** CodeGraph 安装与初始化步骤 SHALL 执行
- **AND** 代码阅读规则仍 MUST 来自非 Coding 来源模板
- **AND** 入口第 7 条摘要 MUST 保持非 Coding 文案不变

#### Scenario: no-interrupt 类型裁决行为保持不变
- **WHEN** no-interrupt 模式下检测结果为非 Coding 且调用方传入 Coding 类型意图
- **THEN** 最终 project_type MUST 为非 Coding
- **AND** 全流程 MUST NOT 因类型分歧产生任何打断或询问
