@echo off
REM ################################################################################
REM Cadence Skills 离线安装脚本 (Windows)
REM
REM 使用方法:
REM   双击运行 install-offline.bat
REM   或在命令行中执行: install-offline.bat
REM
REM 作者: Cadence Team
REM 版本: v2.0
REM 更新记录:
REM   v2.0 (2026-04-03): 适配拆分后的双插件 marketplace 结构 (cadence-init + cadence-workflow)
REM   v1.1 (2025-03-17): 修复步骤4的 JSON 配置生成语法错误
REM   v1.0: 初始版本
REM ###############################################################################

setlocal enabledelayedexpansion

REM 打印横幅
echo ============================================================
echo   Cadence Skills 离线安装脚本 v2.0 (Windows)
echo   包含插件: cadence-init + cadence-workflow
echo ============================================================
echo.

REM 获取脚本所在目录（项目根目录）
set "SOURCE_DIR=%~dp0"
REM 去掉末尾的反斜杠
set "SOURCE_DIR=%SOURCE_DIR:~0,-1%"

REM 目标目录
set "TARGET_DIR=%USERPROFILE%\.claude\plugins\marketplaces\cadence-skills-local"
set "MARKETPLACES_DIR=%USERPROFILE%\.claude\plugins\marketplaces"

echo 📁 目标安装目录: %TARGET_DIR%
echo.

REM 步骤 1: 创建 marketplaces 目录
echo 🔨 步骤 1: 创建 marketplaces 目录
if not exist "%MARKETPLACES_DIR%" (
    mkdir "%MARKETPLACES_DIR%"
    echo   ✅ 已创建: %MARKETPLACES_DIR%
) else (
    echo   ℹ️  目录已存在: %MARKETPLACES_DIR%
)
echo.

REM 步骤 2: 创建安装目录
echo 🔨 步骤 2: 创建安装目录
if not exist "%TARGET_DIR%" (
    mkdir "%TARGET_DIR%"
    echo   ✅ 已创建: %TARGET_DIR%
) else (
    echo   ℹ️  目录已存在: %TARGET_DIR%
    echo   ⚠️  将覆盖现有安装
)
echo.

REM 步骤 3: 复制项目文件
echo 🔨 步骤 3: 复制项目文件
echo   📂 源目录: %SOURCE_DIR%
echo   📂 目标目录: %TARGET_DIR%
echo.

REM 清理目标目录中的旧文件
if exist "%TARGET_DIR%" (
    echo   🗑️  清理旧文件...
    del /q "%TARGET_DIR%\*" 2>nul
    for /d %%p in ("%TARGET_DIR%\*") do rd /s /q "%%p" 2>nul
)

REM 复制各目录和文件（排除 .git 和安装脚本）
echo   📋 复制文件中...

REM 复制 .claude-plugin 目录
if exist "%SOURCE_DIR%\.claude-plugin" (
    xcopy "%SOURCE_DIR%\.claude-plugin" "%TARGET_DIR%\.claude-plugin\" /E /I /Y >nul
)

REM 复制 cadence-init 插件
if exist "%SOURCE_DIR%\cadence-init" (
    xcopy "%SOURCE_DIR%\cadence-init" "%TARGET_DIR%\cadence-init\" /E /I /Y >nul
)

REM 复制 cadence-workflow 插件
if exist "%SOURCE_DIR%\cadence-workflow" (
    xcopy "%SOURCE_DIR%\cadence-workflow" "%TARGET_DIR%\cadence-workflow\" /E /I /Y >nul
)

REM 复制根目录文件
for %%f in (CLAUDE.md README.md LICENSE .mcp.json) do (
    if exist "%SOURCE_DIR%\%%f" (
        copy /y "%SOURCE_DIR%\%%f" "%TARGET_DIR%\" >nul
    )
)

REM 复制 readmes 目录
if exist "%SOURCE_DIR%\readmes" (
    xcopy "%SOURCE_DIR%\readmes" "%TARGET_DIR%\readmes\" /E /I /Y >nul
)

echo.
echo   ✅ 复制完成
echo.

REM 步骤 4: 配置 known_marketplaces.json
echo 🔨 步骤 4: 配置 known_marketplaces.json

set "PLUGINS_DIR=%USERPROFILE%\.claude\plugins"
set "MARKETPLACES_FILE=%PLUGINS_DIR%\known_marketplaces.json"

REM 创建 plugins 目录（如果不存在）
if not exist "%PLUGINS_DIR%" (
    mkdir "%PLUGINS_DIR%"
    echo   ✅ 已创建: %PLUGINS_DIR%
)

REM 使用 PowerShell 处理 JSON
powershell -Command "$f='%MARKETPLACES_FILE%'; $p='%TARGET_DIR:\=/%'; if(Test-Path $f){$j=Get-Content $f -Raw | ConvertFrom-Json}else{$j=@{}}; if($j.PSObject.Properties.Match('cadence-skills-local')){Write-Host '  ℹ️  cadence-skills-local 配置已存在，跳过更新'}else{$t=[DateTime]::UtcNow.ToString('yyyy-MM-ddTHH:mm:ss.000Z'); $j | Add-Member -NotePropertyName 'cadence-skills-local' -NotePropertyValue @{source=@{source='github';repo='cadence/cadence-skills-local'};installLocation=$p;lastUpdated=$t} -Force; $j | ConvertTo-Json -Depth 10 | Out-File $f -Encoding UTF8; Write-Host '  ✅ 已添加 cadence-skills-local 配置'}"

echo.

REM 安装完成
echo ============================================================
echo   ✅ 安装成功！
echo ============================================================
echo.
echo 📍 安装位置: %TARGET_DIR%
echo.
echo 📦 已安装插件:
echo   - cadence-init: 项目初始化 (环境检查、项目分析、规则配置、MCP配置)
echo   - cadence-workflow: 开发工作流 (完整流程、快速流程、探索流程、TDD等)
echo.
echo 💡 提示:
echo   - 重启 Claude Code 以加载新安装的插件
echo   - 使用 /cadence:* 命令访问 Cadence skills
echo.

pause
