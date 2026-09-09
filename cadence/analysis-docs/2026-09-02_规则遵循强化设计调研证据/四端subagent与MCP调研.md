# Research: 四款 coding agent 的 subagent 使用 MCP server 的现状与方案

## Summary
四端结论各异:Claude Code 官方文档明确 subagent 默认继承主会话 MCP 工具,且提供 `mcpServers` frontmatter + `tools` 字段 MCP 模式,但历史上有一串继承 bug;Codex CLI 已有原生子代理(默认启用),文档称省略时 `mcp_servers` 继承父会话,v0.125 实测为"全量继承且无法退出";Kimi Code 子代理默认保留全部工具(含 MCP),`tools` 字段原生支持 `mcp__server__*` glob;pi 用 `tools: mcp:server/tool` 语法解决。通用兜底为主会话中转、子代理自挂 MCP(proxy/frontmatter)、把 MCP 包装成 CLI/headless 子进程调用。

## 1. Claude Code(Task/Agent 工具派生的 subagent)
1. **默认继承(官方文档)**:文档原文"Subagents inherit the built-in tools and MCP tools available in the main conversation";后台 subagent 也"keeps every MCP tool"。[Subagents 文档](https://code.claude.com/docs/en/sub-agents)
2. **tools 字段写法**:`tools`/`disallowedTools` 接受精确名 `mcp__<server>__<tool>`,也接受 server 级模式 `mcp__<server>` 或 `mcp__<server>__*`;`disallowedTools` 中 `mcp__*` 可移除全部 MCP 工具。[Subagents 文档](https://code.claude.com/docs/en/sub-agents)
3. **mcpServers frontmatter 字段**:条目可为字符串(引用已配置 server,与父会话共享连接)或内联定义(subagent 启动时连接、结束断开,主会话不加载、省上下文);v2.1.153 起主会话的 MCP 限制策略同样覆盖该字段。[Subagents 文档](https://code.claude.com/docs/en/sub-agents)、[MCP 文档](https://code.claude.com/docs/en/mcp)
4. **实践坑(多 issue)**:项目级 `.mcp.json` 的 server 曾对 subagent 不可见而全局配置可用([#13898](https://github.com/anthropics/claude-code/issues/13898));通配/前缀写法曾报 Unrecognized([#53865](https://github.com/anthropics/claude-code/issues/53865));后台/插件 subagent 继承不稳([#13254](https://github.com/anthropics/claude-code/issues/13254)、[#30280](https://github.com/anthropics/claude-code/issues/30280)、[#25200](https://github.com/anthropics/claude-code/issues/25200))。建议:优先用户级配置或 `mcpServers` 字符串引用,落地后实测验证。

## 2. Codex CLI(截至 2026-09)
1. **有原生子代理**:官方文档"Current Codex releases enable subagent workflows by default",出现在 CLI/IDE/ChatGPT 桌面端;直接要求或 AGENTS.md/skill 指示即可委派。[Codex Subagents](https://developers.openai.com/codex/subagents)
2. **MCP 继承**:文档原文(经两个 issue 引用)——`mcp_servers` 等"inherit from the parent session when you omit them"。v0.117 时曾有不继承 bug([#16475](https://github.com/openai/codex/issues/16475),OPEN);v0.125 实测已变为全量继承且无法用 `mcp_servers = {}` 退出([#20135](https://github.com/openai/codex/issues/20135),OPEN 的 opt-out 特性请求)。
3. **主会话 MCP 生效方式**:`~/.codex/config.toml`(用户)与 `.codex/config.toml`(项目,需 trust)的 `[mcp_servers.<name>]` 表,支持 stdio 与 streamable HTTP;`codex mcp add` 等子命令管理。[Config Reference](https://developers.openai.com/codex/config-reference)
4. **自定义 agent + 每 agent MCP**:`[agents.<name>]` + `config_file = "agents/foo.toml"`,agent TOML 内可写 `mcp_servers = ["filesystem", "github"]` 做按 agent 收窄。[社区实践](https://github.com/shanraisshan/codex-cli-best-practice/blob/main/best-practice/codex-mcp.md)、[Config Reference](https://developers.openai.com/codex/config-reference)
5. **社区编排方案**:`codex exec` 并行 + tmux 编排器 + git worktree 隔离;`codex mcp-server` 把 Codex 本身做成 MCP 节点交给 Agents SDK 编排。[并行模式](https://codex.danielvaughan.com/2026/04/18/running-multiple-codex-agents-parallel-orchestration/)、[Codex as MCP Server](https://codex.danielvaughan.com/2026/05/10/codex-cli-agents-sdk-mcp-server-multi-agent-orchestration/)、[queue/worker 讨论 #3898](https://github.com/openai/codex/discussions/3898)

## 3. Kimi Code
1. **有 subagent 机制**:内置 `coder`/`explore`/`plan` 三个子代理;自定义 agent 为 Markdown 文件(`.kimi-code/agents/`、`~/.kimi-code/agents/`、跨工具共享 `.agents/agents/`,或 `--agent`/`--agent-file`)。[Agents 文档](https://www.kimi.com/code/docs/en/kimi-code-cli/customization/agents.html)
2. **MCP 配置文件是 `mcp.json`(非 config.toml、非 .mcp.json)**:用户级 `~/.kimi-code/mcp.json`(或 `$KIMI_CODE_HOME/mcp.json`)、项目级 `.kimi-code/mcp.json`,项目级同名覆盖;TUI `/mcp-config` 管理;`config.toml` 的 `[mcp]` 节只有超时等客户端行为。[MCP 文档](https://www.kimi.com/code/docs/en/kimi-code-cli/customization/mcp.html)
3. **subagent 继承 MCP:是**。agent 文件不写 `tools` 即"保留全部工具"(含 MCP);`tools` 字段原生支持 glob,如 `mcp__github__*`(注意裸 `mcp__github` 不匹配任何工具);主 Agent 的 "always allow" 权限规则自动传播到子代理。[Agents 文档](https://www.kimi.com/code/docs/en/kimi-code-cli/customization/agents.html)、[MCP 文档](https://www.kimi.com/code/docs/en/kimi-code-cli/customization/mcp.html)

## 4. 通用兜底模式(子代理挂不上 MCP 时)
1. **主会话中转(mediator)**:根因是 MCP 连接属于主进程,子代理各跑独立上下文;让 subagent 输出结构化"需要调用某 MCP 工具"的请求,由主会话代调并回填结果。[BSWEN: Why Can't AI Sub-Agents Use MCP](https://docs.bswen.com/blog/2026-03-17-sub-agents-mcp-access/)
2. **给子代理单独挂 MCP(proxy/生成 frontmatter)**:如 sub-mcp 为 Claude Code 生成带 `mcpServers` frontmatter 的 agent 文件,主会话零 MCP 开销;对应各端官方等价物:Claude `mcpServers` 字段、Codex agent TOML `mcp_servers`。[dev-boz/sub-mcp](https://github.com/dev-boz/sub-mcp)
3. **把 MCP 包装成 CLI/子进程供 subagent bash 调用**:用 headless agent 携带 MCP 配置起子进程,如 `codex exec -c 'mcp_servers.x.url=...'` 或 `claude -p --mcp-config` 当"工具进程";MCP 也可反向作编排总线(spawn_worker/enqueue_task 类 team server)。[Codex #16475 workaround](https://github.com/openai/codex/issues/16475)、[讨论 #3898](https://github.com/openai/codex/discussions/3898)
4. **规避**:MCP 依赖型任务不委派给 subagent,留在主会话执行(各 issue 中的常见 mitigation)。

## Sources
- Kept: code.claude.com sub-agents / mcp 官方文档、developers.openai.com codex subagents / config-reference、kimi.com/code/docs agents / mcp 官方文档(四端一手依据)
- Kept: anthropics/claude-code #13898/#53865/#13254/#30280、openai/codex #16475/#20135、openai/codex discussion #3898(真实行为与时间线)
- Kept: dev-boz/sub-mcp、BSWEN 博客、danielvaughan Codex KB(兜底模式实例)
- Dropped: learn.chatgpt.com 镜像(抓取失败,内容已被 issue 引文覆盖)、kimi-cli.com/moonshotai.github.io 旧版文档(路径为旧 `~/.kimi/`,与现行 `~/.kimi-code/` 不一致)

## Gaps
- Claude Code 各继承 bug 的修复版本号未逐一核实,建议落地时以当前版本实测为准;Codex agent TOML 每 agent `mcp_servers` 收窄的官方文档原文未能直抓(403),依据为社区实践与 config-reference 键名。
