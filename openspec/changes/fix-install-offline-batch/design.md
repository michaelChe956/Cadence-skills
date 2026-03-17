# Technical Design: 修复 install-offline.bat JSON 语法错误

## Context

`install-offline.bat` 是 Cadence Skills 的 Windows 离线安装脚本。当前实现在步骤4（配置 `known_marketplaces.json` 文件）中使用 PowerShell 命令生成/更新 JSON 文件时存在语法问题。

**当前问题**：
- 批处理脚本使用 `^` 作为续行符，但 PowerShell 命令中的 `$` 符号处理不当
- 多行 PowerShell 命令在 batch 文件中的换行和转义存在冲突
- 导致生成的 JSON 文件格式不合法，出现 `此时不应有 )。` 错误

**问题代码位置**：`install-offline.bat` 第 125-146 行

## Goals / Non-Goals

**Goals:**
- 修复步骤4的 PowerShell 命令，确保生成的 JSON 格式正确
- 简化代码逻辑，减少批处理与 PowerShell 混合编写的复杂度
- 添加基本的错误处理，在 JSON 写入失败时给用户清晰提示

**Non-Goals:**
- 不重构整个安装脚本的架构
- 不添加新功能（如在线安装、多版本管理等）
- 不改变安装目录结构或配置文件格式

## Decisions

### Decision 1: 使用单行 PowerShell 脚本

**选择**：将 PowerShell 逻辑改为单行命令，避免批处理续行符与 PowerShell 语法的冲突

**原因**：
- 批处理文件中使用 `^` 续行符会干扰 PowerShell 命令的解析
- 单行命令更清晰，减少转义问题
- 可以使用 `-replace` 操作符简化字符串处理

**备选方案**：
1. ❌ 使用外部 PowerShell 脚本文件 - 增加文件依赖，安装流程更复杂
2. ❌ 使用批处理变量存储 JSON - 复杂度高，难以维护

### Decision 2: 使用 PowerShell Here-String 生成 JSON

**选择**：使用 PowerShell 的 here-string (`@"..."@`) 来构建 JSON 内容

**原因**：
- 避免复杂的转义处理
- JSON 内容更易读
- 减少语法错误可能性

**实现方式**：
```powershell
$json = @"
{
  "cadence-skills-local": {
    "source": { "source": "github", "repo": "cadence/cadence-skills-local" },
    "installLocation": "<path>",
    "lastUpdated": "<timestamp>"
  }
}
"@
```

### Decision 3: 统一 JSON 文件处理逻辑

**选择**：无论是创建新文件还是更新现有文件，都使用相同的 JSON 生成逻辑

**原因**：
- 减少代码重复
- 统一的行为更易于测试和维护
- 避免两套逻辑产生不一致的结果

## Risks / Trade-offs

| 风险 | 缓解措施 |
|------|---------|
| 路径中包含特殊字符（空格、中文等） | 使用双引号包裹路径，PowerShell 自动处理 |
| PowerShell 执行策略限制 | 脚本使用 `powershell -Command`，大多数系统默认允许 |
| 现有 JSON 文件包含其他配置 | 读取现有内容，仅更新/添加 cadence-skills-local 条目 |

## Implementation Outline

```batch
REM 步骤 4: 配置 known_marketplaces.json (重写)
echo 🔨 步骤 4: 配置 known_marketplaces.json

set "PLUGINS_DIR=%USERPROFILE%\.claude\plugins"
set "MARKETPLACES_FILE=%PLUGINS_DIR%\known_marketplaces.json"

REM 创建 plugins 目录
if not exist "%PLUGINS_DIR%" mkdir "%PLUGINS_DIR%"

REM 使用 PowerShell 处理 JSON (单行命令)
powershell -Command "$f='%MARKETPLACES_FILE%'; $p='%TARGET_DIR:\=/%'; $t=(Get-Date -Format 'yyyy-MM-ddTHH:mm:ss.000Z' -AsUTC); if(Test-Path $f){$j=Get-Content $f -Raw | ConvertFrom-Json}else{$j=@{}}; if(-not $j.PSObject.Properties.Match('cadence-skills-local')){$j | Add-Member -NotePropertyName 'cadence-skills-local' -NotePropertyValue @{source=@{source='github';repo='cadence/cadence-skills-local'};installLocation=$p;lastUpdated=$t} -Force}; $j | ConvertTo-Json -Depth 10 | Out-File $f -Encoding UTF8; Write-Host '  ✅ 配置完成'"

echo.
```

**关键改进**：
1. 单行 PowerShell 命令，无续行符问题
2. 统一处理"创建新文件"和"更新现有文件"两种场景
3. 使用 `-Force` 参数确保属性可以被更新
