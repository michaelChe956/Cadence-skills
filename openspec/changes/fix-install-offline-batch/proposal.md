# Proposal: 修复 install-offline.bat 脚本 JSON 语法错误

## Why

用户执行 `install-offline.bat` 脚本时，在步骤4配置 `known_marketplaces.json` 文件时出现错误：`此时不应有 )。`，导致离线安装流程中断。这是批处理脚本中 PowerShell 命令的语法问题，导致生成的 JSON 格式不合法，阻止用户完成离线安装。

## What Changes

- **修复 `install-offline.bat` 中步骤4的 PowerShell 命令**：重写 JSON 配置逻辑，确保生成的 JSON 格式合法
- **优化 PowerShell 脚本的转义处理**：修复批处理文件中 `$` 符号和换行符的处理问题
- **增强错误处理**：添加 JSON 验证逻辑，在写入文件前验证 JSON 格式

## Capabilities

### New Capabilities

无新增能力。这是一个修复，不引入新功能。

### Modified Capabilities

- `install-offline-batch`: 修复 JSON 配置生成的语法错误，确保离线安装流程正常完成

## Impact

**受影响文件**：
- `install-offline.bat` - 步骤4的 PowerShell 命令将被重写

**用户影响**：
- 用户可以正常执行离线安装流程
- 生成的 `known_marketplaces.json` 文件格式正确

**向后兼容性**：
- 完全兼容，不影响已安装的用户
- 仅修复 bug，不改变任何功能行为
