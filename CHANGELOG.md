# CHANGELOG

所有重要的更改都将记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
本项目遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [Unreleased]

### Fixed
- 修复 `install-offline.bat` 步骤4的 JSON 配置生成语法错误
  - 问题：多行 PowerShell 命令在批处理文件中的续行符 `^` 导致 JSON 语法错误
  - 解决：将 PowerShell 逻辑改为单行命令，统一处理创建和更新场景

## [1.0.0] - 2025-03-01

### Added
- 初始版本的 Cadence Skills 离线安装脚本
- 支持离线安装到 `~/.claude/plugins/marketplaces/cadence-skills-local`
- 自动配置 `known_marketplaces.json` 文件
