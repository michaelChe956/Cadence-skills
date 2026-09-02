# 研究:Codex CLI 如何加载项目规则/指令文件(AGENTS.md 之外的机制)

## 一、Codex 官方能力(developers.openai.com/codex + openai/codex 源码)

1. **发现链与加载时机**:指令链在启动时构建一次("once per run; in the TUI this usually means once per launched session")。全局层读 `~/.codex/AGENTS.override.md`(优先)或 `~/.codex/AGENTS.md`(取第一个非空);项目层从 project root(默认 `.git` 标记)向下走到 cwd,逐目录串联,不越过 root。源码证实:每目录候选顺序为 `AGENTS.override.md` → `AGENTS.md` → fallback 名单,**每目录最多取一个文件**。[官方指南](https://developers.openai.com/codex/guides/agents-md) · [源码 agents_md.rs](https://github.com/openai/codex/blob/main/codex-rs/core/src/agents_md.rs)
2. **嵌套子目录 AGENTS.md**:只有位于 root→cwd 启动路径上才会加载;启动后 cd 进入子目录**不会**动态加载,社区要求"按 cwd 动态加载/最近文件优先"的 issue #12115 仍是 open(Stripe/Wix/Palantir 等列为 Must-have),#9836 确认外层启动看不到子目录文件。[Issue #12115](https://github.com/openai/codex/issues/12115) · [Issue #9836](https://github.com/openai/codex/issues/9836)
3. **无 include/import/@ 语法**:AGENTS.md 按纯文本读入拼接,源码与文档均无任何引用跟读逻辑;文件内"详见 xxx.md"只是普通文本。官方对"规则多且长"的建议是 keep it small + 渐进披露(细节放链接文档/Skills/Memories),Claude Code 式 `@file` import 在 Codex 不存在。[Customization](https://developers.openai.com/codex/concepts/customization)
4. **config 键**:`project_doc_max_bytes` 默认 **32KiB**(`DEFAULT_PROJECT_DOC_MAX_BYTES = 32 * 1024`),预算沿链**累计共享**、超出截断(文档一页写"每文件"与代码矛盾,以代码为准,见 issue #36371);`project_doc_fallback_filenames` 可加备选文件名(如 `CLAUDE.md`),但仅当该目录无 AGENTS.md 时才尝试、不追加、不能指向目录(无法加载 `.claude/rules/`),且有版本 bug(#22454)。`developer_instructions` 可向 system prompt 追加文本;`model_instructions_file`(原 `experimental_instructions_file`,#9555 改名)**整体替换**内置 base prompt,非追加,慎用;`instructions` 键保留未用。项目级 `.codex/config.toml` 从 root 走到 cwd 逐个加载、最近者优先、仅 trusted 项目生效。[Config Reference](https://developers.openai.com/codex/config-reference) · [Advanced Config](https://developers.openai.com/codex/config-advanced) · [源码](https://github.com/openai/codex/blob/53b50197/codex-rs/config/src/config_toml.rs) · [Issue #36371](https://github.com/openai/codex/issues/36371)

## 二、agents.md 开放规范(agents.md / agentsmd GitHub)

5. 规范刻意最小化:纯 Markdown、无 schema、无必填字段;唯一"多文件机制"是**嵌套放置**(编辑文件最近的 AGENTS.md 优先);**不定义** include/import/@引用/组合机制。OpenAI 主仓库有 88 个 AGENTS.md 即靠嵌套。[agents.md](https://agents.md/)
6. 引用/目录聚合均为**开放提案未落地**:`@import`(#66、#11)、目录支持如 `.agents/`(#9)、progressive disclosure 与语义明确化(#135)、标准化实现规范(#211)。各 harness 自行扩展:Cursor `.mdc` 支持 `@依赖` 链、Claude Code 支持 `CLAUDE.md` `@import` 且把 AGENTS.md 作 fallback、Copilot 用 `.github/instructions/*.instructions.md`+`applyTo`——这些都不属于 agents.md 规范,Codex 也不兼容。[Issue #11](https://github.com/agentsmd/agents.md/issues/11) · [Issue #66](https://github.com/agentsmd/agents.md/issues/66) · [Issue #9](https://github.com/agentsmd/agents.md/issues/9)

## 三、生成器/聚合模式(社区工程实践)

7. **片段→构建 AGENTS.md**:`npx agents-md compose` 从多片段源构建 AGENTS.md,附 `setup:compose-before-commit` 生成 git pre-commit 钩子、提交前自动重组装,语言无关;`agents-md-compiler` 把有序 Markdown 策略模块编译成确定性 AGENTS.md(无依赖/无网络/无 LLM);`agents-md-sync` 用中央模板 repo 向多 repo 分发共享段落并允许每 repo 追加 per-section addenda;`agentsgen` 提供 marker-safe 更新 + CI drift 检查(check/doctor/GitHub Action)。[ivawzh/agents-md](https://github.com/ivawzh/agents-md) · [agents-md-compiler](https://github.com/netopsengineer/agents-md-compiler) · [agents-md-sync](https://github.com/trick77/agents-md-sync) · [agentsgen](https://github.com/markoblogo/AGENTS.md_generator)
8. **共识最佳实践**:AGENTS.md 保持约 100–150 行,摘要+链接渐进披露;多工具团队用单一 canonical 源 + symlink 分发。对 Cadence 的直接映射:以 `.claude/rules/*.md` 为唯一源,Makefile/CI/pre-commit 聚合生成根 AGENTS.md 内联块(带更新标记),CI 校验防漂移——正是社区主流解法。[agent-config 指南](https://agent-config.com/guides/writing-agents-md/) · [aihackers 实践](https://aihackers.net/posts/agents-md-practical-guide/)

## 四、按需加载(JIT rules retrieval)

9. **官方途径:Codex Skills**(渐进披露)——只把每个 skill 的 name+description+路径注入上下文,Codex 决定使用时才读全文 `SKILL.md`;skill 可放 repo `.codex/skills/` 或 `~/.codex/skills`,这是官方唯一原生"规则正文按需拉取"机制,与 Cadence 现有 skills 体系天然契合。[官方 Skills 文档](https://developers.openai.com/codex/skills) · [skills.md](https://github.com/openai/codex/blob/main/docs/skills.md)
10. **社区 MCP 实践**:`mcp-standards-loader`(运行时按 custom/team/framework/language 四级动态加载标准、优先级冲突消解、TTL 缓存);`standards-mcp`(标准变 live data store,任务时查询,28 条规则约 700 token);`rulekit-mcp/codex-mcp`(project/group/tech/language 作用域,按需载入);`codeguide-mcp`(明确以 MCP resources "extend or replace AGENTS.md")。另 ToolSearch 已默认稳定,MCP 工具 schema 按需发现而非全量注入。[mcp-standards-loader](https://github.com/techdeveloper-org/mcp-standards-loader) · [standards-mcp](https://github.com/anotherben/standards-mcp) · [codex-mcp](https://github.com/IgorKrupenja/codex-mcp) · [codeguide-mcp](https://github.com/delian/codeguide-mcp)
11. **风险**:JIT 依赖模型主动调用,遵守率低于 always-on 注入(实测 "AGENTS.md wins on adherence";#12926 亦指出 AGENTS.md 遵循率不稳、developer_instructions 注入更强),漏调用即漏规则,需配合 hooks/CI 兜底校验。[aihackers](https://aihackers.net/posts/agents-md-practical-guide/) · [Issue #12926](https://github.com/openai/codex/issues/12926)

## 结论(一句话回答)

**截至今天(2026-09,基于最新官方文档、源码与 open issue 证据):Codex 官方不存在任何"自动加载 AGENTS.md 之外规则文件"的原生机制**——AGENTS.md 无 include/import/@ 引用语法,`project_doc_fallback_filenames` 仅是同目录缺 AGENTS.md 时的备选文件名而非追加通道,嵌套 AGENTS.md 只在启动路径上加载且动态加载仍是未实现的 open feature request;官方推荐的替代是 Skills 渐进披露,工程上可行的分发方案是"片段源→构建/CI 聚合生成 AGENTS.md"或 MCP 按需拉取。
