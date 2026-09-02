# Cadence L0 只读实验摘要

## 实验状态

- 工作目录：`/home/michaelche/workspace/github/naruto`
- 证据目录：`/tmp/cadence-exp1/`
- 判卷基准：`groundtruth_l0.txt`（2501 字节；区块版本为 v3）
- 四条命令均首次运行完成，退出码均为 `0`；未触发重试，也未修改 `naruto` 下文件。
- L0 区块判定按起始/结束 HTML 注释之间的内容与基准比对；Kimi 另记录了因复述行带统一两空格缩进造成的“非逐字”差异。

## Claude

a) **是否复述 L0 区块：否。** 未输出起始/结束 HTML 注释区块，仅回答“未加载”。

b) **版本标记：缺失。**

c) **是否列出 `.claude/rules/` 文件名：是。** 列出：`README.md`、`language.md`、`markdown-format.md`、`code-usage.md`、`document-storage.md`、`openspec-superpowers-workflow.md`、`code-reading.md`、`mcp-servers.md`、`serena-usage.md`、`playwright.md`。

 d) **第 3 问：正确。** 回答产物自动提交为“关闭”。

 e) **有声明/异常迹象：是。** 输出明确声称区块“未加载”；stderr 出现模型识别异常。

关键原文（≤5 行）：

> `claude.out:1` **1.** 未加载。
> `claude.out:3` ……不存在 AGENTS.md 的加载内容……cadence-managed 区块在上下文中不存在……
> `claude.out:18` **3.** 产物自动提交（design/plan/code）开关为**关闭**。
> `claude.err:1` `[claude-code:unrecognized_model] {"model":"glm-5.3-flash[1M]",...}`

## Codex

a) **是否复述 L0 区块：部分。** 起止标记和主体均输出，但 `knowledge-base-context` 行比基准多出“，不引导 knowledge-base-bootstrap”，因此不是逐字一致。

b) **版本标记：v3。**

c) **是否列出 `.claude/rules/` 文件名：是。** 列出：`language.md`、`code-usage.md`、`document-storage.md`、`markdown-format.md`、`mcp-servers.md`、`code-reading.md`、`playwright.md`。

 d) **第 3 问：正确。** 回答“产物自动提交开关是关闭”。

 e) **有声明/异常迹象：是。** stderr 出现多次 MCP 初始化 fatal 错误；未出现工具禁用或区块未加载声明。

关键原文（≤5 行）：

> `codex.out:3` `<!-- cadence-managed:openspec-superpowers-routing:v3:start -->`
> `codex.out:20` `` `knowledge-base-context` 前置门禁：……否则跳过且不提示，不引导 knowledge-base-bootstrap。``
> `codex.out:35` `<!-- cadence-managed:openspec-superpowers-routing:v3:end -->`
> `codex.err:18` `ERROR rmcp::transport::worker: worker quit with fatal: Unexpected content type: Some("missing-content-type; body: ")`

## Pi

a) **是否复述 L0 区块：是。** 起始/结束标记之间的内容与基准逐字一致。

b) **版本标记：v3。**

c) **是否列出 `.claude/rules/` 文件名：是。** 列出：`language.md`、`code-usage.md`、`document-storage.md`、`markdown-format.md`、`mcp-servers.md`、`code-reading.md`、`playwright.md`、`README.md`。

 d) **第 3 问：正确。** 回答为“关闭”。

 e) **有声明/异常迹象：是（轻微、非错误）。** 未出现工具禁用或区块未加载声明；stderr 仅有 Pi 的终端通知控制序列，未见错误。

关键原文（≤5 行）：

> `pi.out:6` `<!-- cadence-managed:openspec-superpowers-routing:v3:start -->`
> `pi.out:38` `<!-- cadence-managed:openspec-superpowers-routing:v3:end -->`
> `pi.out:56` **关闭**（入口配置为“产物自动提交（design/plan/code）：关闭”……）
> `pi.err:1` `\x1b]777;notify;Pi;Ready for input\x07`

## Kimi

a) **是否复述 L0 区块：部分。** 语义内容完整且起止标记齐全，但区块正文各行带两空格缩进，按逐字/字节比对不一致。

b) **版本标记：v3。**

c) **是否列出 `.claude/rules/` 文件名：是。** 先回答“无”，随后实际列出：`language.md`、`code-usage.md`、`document-storage.md`、`markdown-format.md`、`mcp-servers.md`、`code-reading.md`、`playwright.md`、`README.md`。

 d) **第 3 问：正确。** 回答“关闭”。

 e) **有声明/异常迹象：是。** 未出现工具禁用或区块未加载声明；stderr 泄露了长篇内部推理/作答规划，属于异常迹象。

关键原文（≤5 行）：

> `kimi.err:1` `kimi version 0.39.1`
> `kimi.err:2` `• The user is asking me to answer purely from loaded context, no tools. Three questions:`
> `kimi.err:10` `Let me recall the context. The AGENTS.md content was provided in my system prompt.`
> `kimi.err:110` `I'll answer: 无（.claude/rules/ 各文件内容均未加载；AGENTS.md 中仅以名称引用了……）.`

## 四端对比表

| 端 | 退出码 | a) L0 区块 | b) 版本 | c) 列出规则文件名 | d) 开关答案 | e) 声明/异常迹象 |
|---|---:|---|---|---|---|---|
| Claude | 0 | 否 | 缺失 | 是：10 个 | 正确（关闭） | 是：未加载 + `unrecognized_model` stderr |
| Codex | 0 | 部分 | v3 | 是：7 个 | 正确（关闭） | 是：MCP `fatal` stderr |
| Pi | 0 | 是 | v3 | 是：8 个 | 正确（关闭） | 是：仅终端通知控制序列 |
| Kimi | 0 | 部分（缩进差异） | v3 | 是：8 个，但同时回答“无” | 正确（关闭） | 是：stderr 内部推理泄露 |

## 证据文件

- `groundtruth_l0.txt`
- `claude.out` / `claude.err`
- `codex.out` / `codex.err`
- `pi.out` / `pi.err`
- `kimi.out` / `kimi.err`
