# rule-config-scripted-execution Delta

## MODIFIED Requirements

### Requirement: 项目配置产物与现行语义一致

脚本 MUST 保留现行项目配置相关产物语义：脚本 MUST NOT 检测项目技术栈（语言、包管理器、测试/检查/格式化命令、覆盖率），MUST NOT 在入口文件写入或更新 `### 项目技术栈` 块、包管理器规则或覆盖率阈值；入口中用户既有的技术栈内容 MUST 逐字保留。入口文件 `## 项目配置` 章节仅维护"产物自动提交（design/plan/code）"开关；旧名"产物自动提交（design/plan）"开关行 MUST 按身份迁移处理（保留用户值，归并后恰好一行新名开关行）。历史产物目录仅检测现行精确目录集合，no-interrupt 模式 MUST 只写入报告且 SHALL NOT 执行移动、合并、删除或清理，普通模式 SHALL 按现行迁移表处理且目标目录非空时跳过并报告冲突；`cadence/` 默认不加入 `.gitignore`；`.codegraph/` 在 Coding 项目或 `--enable-codegraph` 时 SHALL 加入 `.gitignore`，`codegraph.json` MUST NOT 加入；Playwright 规则默认跳过。

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
- **THEN** 脚本 SHALL 按现行迁移表迁移
- **AND** 目标非空时 MUST 跳过该目录并报告冲突，不覆盖、不合并
