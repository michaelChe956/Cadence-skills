# Tasks: 修复 install-offline.bat JSON 语法错误

## 1. 修复 PowerShell 命令

- [ ] 1.1 重写 `install-offline.bat` 步骤4的 PowerShell 命令为单行格式
- [ ] 1.2 测试新命令在 Windows 命令提示符中的执行

## 2. 验证和测试

- [ ] 2.1 测试场景：创建新的 `known_marketplaces.json` 文件
- [ ] 2.2 测试场景：更新现有的 `known_marketplaces.json` 文件
- [ ] 2.3 测试场景：`cadence-skills-local` 配置项已存在时跳过更新
- [ ] 2.4 测试场景：安装路径包含空格或中文字符

## 3. 文档更新

- [ ] 3.1 更新脚本注释说明修改内容
- [ ] 3.2 在 CHANGELOG 中记录此修复
