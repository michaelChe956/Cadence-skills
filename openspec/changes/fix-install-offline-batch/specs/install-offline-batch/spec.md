# Spec: install-offline-batch

离线安装脚本的 JSON 配置生成行为规范。

## MODIFIED Requirements

### Requirement: JSON 配置文件生成正确

`install-offline.bat` 脚本在步骤4中生成或更新 `known_marketplaces.json` 文件时，SHALL 生成合法的 JSON 格式。

#### Scenario: 创建新的配置文件
- **WHEN** `known_marketplaces.json` 文件不存在
- **THEN** 脚本 SHALL 创建新文件，内容为合法的 JSON 格式
- **AND** 文件 SHALL 包含 `cadence-skills-local` 配置项

#### Scenario: 更新现有配置文件
- **WHEN** `known_marketplaces.json` 文件已存在
- **AND** 文件中不包含 `cadence-skills-local` 配置项
- **THEN** 脚本 SHALL 保留现有配置项
- **AND** 添加 `cadence-skills-local` 配置项
- **AND** 结果文件 SHALL 为合法的 JSON 格式

#### Scenario: 配置项已存在
- **WHEN** `known_marketplaces.json` 文件已存在
- **AND** 文件中已包含 `cadence-skills-local` 配置项
- **THEN** 脚本 SHALL 显示提示信息，不修改文件

### Requirement: 错误处理

脚本 SHALL 在 JSON 处理失败时向用户提供清晰的错误信息。

#### Scenario: 路径包含特殊字符
- **WHEN** 安装路径包含空格或中文字符
- **THEN** 脚本 SHALL 正确处理路径
- **AND** 生成的 JSON 文件中路径 SHALL 正确转义

#### Scenario: PowerShell 不可用
- **WHEN** 系统 PowerShell 不可用或执行策略阻止脚本运行
- **THEN** 脚本 SHALL 显示明确的错误信息
- **AND** 建议用户如何解决
