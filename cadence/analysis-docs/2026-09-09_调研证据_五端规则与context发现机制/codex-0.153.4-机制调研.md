# Research: OpenAI Codex CLI 0.153.4 规则与 context 发现机制

> 调研人:researcher 子代理(CodexResearch),2026-09-09。来源:官方文档(developers.openai.com/codex)+ 本机无头实测(codex exec + rollout grep + binary strings)。

## Summary

Codex 的行为规则层只有 **AGENTS.md 单文件链**(全局→项目根→CWD 逐级拼接,32KiB 总量截断,无按需/渐进加载),**不存在** Cursor 式 markdown 规则目录;`.codex/rules/` 实为 **Starlark 沙箱命令策略**(prefix_rule 允许/禁止命令),与 agent 行为无关。渐进加载能力全部押在 **Skills**(name+description 常驻、SKILL.md 正文按需读取)。0.153.4 为当前最新版,本地 6 组无头实测与官方文档完全一致。

## Findings

### 1. context 文件发现(哪些文件、优先级、遮蔽/合并)

1. **发现链(官方文档确认 + 本地实测一致)**:启动时组装一次(每次 run / 每个 TUI 会话一次)。① 全局层 `$CODEX_HOME`(默认 `~/.codex`):`AGENTS.override.md` 存在则优先,否则 `AGENTS.md`,该层只取第一个非空文件;② 项目层:从项目根(通常 git root)向下走到 CWD,每级目录按 `AGENTS.override.md` → `AGENTS.md` → `project_doc_fallback_filenames` 回退名顺序取**至多一个**文件;③ 合并:根→CWD 逐文件拼接(空行分隔),越靠近 CWD 越靠后=越强。无项目根时只查当前目录。[官方 AGENTS.md 文档](https://developers.openai.com/codex/agents-md)
2. **同目录遮蔽(本地实测)**:`/tmp` fixture 中同目录放 `AGENTS.md`(OVR-BASE-1)+ `AGENTS.override.md`(OVR-SUPER-2),`codex exec` 后 session rollout 只含 OVR-SUPER-2——override 完全遮蔽同目录基础文件。
3. **跨目录是合并不是遮蔽(本地实测)**:根 `AGENTS.md`(CXROOT-7Q2)+ 子目录 `AGENTS.md`(CXSUB-9Z4),在子目录运行时两个 marker 都进上下文;rollout 原文可见拼接结果。
4. **回退文件名可配置(本地实测)**:`-c 'project_doc_fallback_filenames=["TEAM_GUIDE.md"]'` 后无 AGENTS.md 的目录里的 TEAM_GUIDE.md(CXFALL-5M1)被加载。config 键默认 `[]`。[Config Reference](https://developers.openai.com/codex/config-reference)
5. **不读 CLAUDE.md(本地实测)**:只有 `CLAUDE.md` 的目录,marker 未进上下文。二进制内确有 `CLAUDE.md` 字符串(迁移/检测类字面量),但无发现行为。
6. **大小限制**:`project_doc_max_bytes` 默认 **32768(32KiB,合并总量)**,超限即停止追加后续文件;空文件跳过。组装好的指令**全文进上下文,无任何按需机制**。

### 2. 规则系统(目录、文件格式、frontmatter、渐进/按需能力)

7. **`.rules` = 沙箱执行策略,不是行为规则**:`rules/` 目录放在各活跃 config 层旁(用户层 `~/.codex/rules/`、Team Config 层、项目层 `<repo>/.codex/rules/`——项目层需 trust)。文件为 **Starlark** 格式,核心函数 `prefix_rule(pattern=[...], decision=allow|prompt|forbidden, ...)`,控制哪些命令可在沙箱外运行;多条匹配取最严格。[官方 Rules 文档](https://developers.openai.com/codex/rules)。本地 `~/.codex/rules/default.rules` 实为 TUI「always allow」自动写入的 5 条 allow 规则。
8. **无 markdown 规则目录、无 frontmatter 约定**:`.codex/rules/` 放 .md 自动加载只是 [issue #17401](https://github.com/openai/codex/issues/17401)(OPEN)的未实现提案;description/alwaysApply/globs/agents 等 frontmatter 字段在 Codex 中不存在。`codex exec --ignore-rules` 只针对 execpolicy `.rules`。
9. **无 @import/@include(官方 issue 确认)**:AGENTS.md 不支持 `@path` 语法,写入的字面量原样进上下文。
10. **渐进加载只在 Skills**:初始上下文只含各 skill 的 name+description+路径(预算=上下文窗口 2% 或 8000 字符,超限先缩短描述再省略),选中后才读全文 SKILL.md。发现位置:`$CWD` 至 repo root 每级的 `.agents/skills/`、`$HOME/.agents/skills`、`/etc/codex/skills`、内置。[官方 Skills 文档](https://developers.openai.com/codex/skills)

### 3. agent/角色限定能力

11. **子代理指令经 agent TOML 的 `developer_instructions` 字段**:自定义 agent 放 `~/.codex/agents/` 或 `.codex/agents/`(项目),必填 `name`/`description`/`developer_instructions`——「按 agent 过滤规则」= 给每个角色写独立 TOML 配置层(内嵌指令字符串),而非给规则文件打 agent 标签。[Subagents 文档](https://developers.openai.com/codex/subagents)

### 4. 符号链接兼容性

12. **AGENTS.md 为 symlink:跟随(本地实测)**:被正常读取进上下文。
13. **skill 目录 symlink:官方明确支持并跟随**。
14. `.rules` 目录/项目 `.codex/` 为 symlink:未实测、文档未提及。

### 5. 版本注记

15. 本机 0.153.4 = 当前 latest(2026-09-07 version cache),官方文档与本地版本同代;openai/codex GitHub docs 已改指向官网的 stub。
16. 二进制 strings:含 `AGENTS.override.md`、`AGENTS.md`、`project_doc_fallback_filenames`、`project_doc_max_bytes`、`CLAUDE.md`。
17. `codex features list`:`skill_search`/`multi_agent`=stable/true、`memories`=stable/false。

### 6. 对五端统一规则架构的启示

18. **AGENTS.md 是唯一稳态公约层**:Codex 端内容必须自包含扁平文本(无 @import、无 frontmatter 语义),模块化文件需构建期 flatten 进 AGENTS.md。
19. **32KiB 合并硬顶决定分层策略**:按需部分在 Codex 端的天然落点是 Skills 的 progressive disclosure。
20. **`.codex/rules/` 是安全策略通道**:可复用于命令白名单,但不要把行为规则误投到该目录(不会进上下文)。

## Sources

- developers.openai.com/codex/{agents-md, rules, config-reference, skills, subagents}
- openai/codex issue #17401(@include 与 markdown 规则目录均为未实现请求)
- 本地实测:`codex exec` 6 组 /tmp fixture 无头探针 + `~/.codex/sessions` rollout grep + binary strings

## Gaps

- `.rules` 目录本身为 symlink 时是否被扫描:未实测。
- 全局层 `~/.codex/AGENTS.override.md` 与 `CODEX_HOME` 重定向:文档明确但未本地实测(避免改动真实 `~/.codex`)。
- Team Config 层的确切路径与优先级:仅文档一句带过,未展开。
- execpolicy 对 `.rules` 数量/单文件大小无上限(唯一硬顶是 AGENTS.md 链 32KiB 与 skills 索引预算)。
