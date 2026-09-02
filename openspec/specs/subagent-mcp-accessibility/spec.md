# Subagent MCP Accessibility Specification

## Purpose
规则要求"原生搜索不可用时用 MCP 兜底"在子代理层不可执行——pi 子代理不继承 MCP（实测工具面为 0），三端（Claude Code/Codex/Kimi）子代理默认继承但有已知 bug 与写法坑。本能力把四端可达性现状、验证方法与兜底链规则随 Cadence 下发。

## Requirements

### Requirement: mcp-configuration 必须提供四端子代理可达性指引

mcp-configuration skill MUST 包含四端子代理 MCP 可达性矩阵：Claude Code/Codex 默认继承（附已知继承 bug 与排查指引）、Kimi 默认保留全部工具（自定义 agent 写 `tools` 时必须含 `mcp__server__*` glob，裸 server 名无效）、pi 为已知限制（子代理不继承，规避策略为 MCP 依赖任务留在主会话）。

#### Scenario: 配置时获得正确指引

- **WHEN** 业务项目运行 /mcp-configuration
- **THEN** 输出包含四端矩阵与各端已知坑位说明

### Requirement: 配置后必须执行子代理可见性验证探针

mcp-configuration 检查清单 MUST 包含"子代理 MCP 可见性探针"步骤：向四端各派一个子代理执行"列出你的 MCP 工具名"；探针失败 MUST 仅告警不阻断，并输出对应端的排查指引。

#### Scenario: 探针发现继承失效

- **WHEN** Claude Code 子代理探针报告 0 个 MCP 工具
- **THEN** 输出告警与排查指引（如改用用户级配置或 mcpServers frontmatter 引用），流程不因此中断

### Requirement: 规则模板必须包含子代理兜底链

mcp-servers 规则模板 MUST 包含子代理兜底链条款：联网搜索优先原生 `web_search`；不可用或失败时检查工具面有无 MCP 搜索工具（如 `webSearchPrime`）并改用；两者皆不可用时向主会话报告"搜索通道不可用"，MUST NOT 放弃任务或编造结果。

#### Scenario: pi 子代理正确退化

- **WHEN** pi 子代理（无任何 MCP 工具）接受需要联网搜索的任务且原生搜索失败
- **THEN** 其向主会话报告通道不可用，由主会话（有 MCP）接手，而非编造结果
