# Research: pi CLI 0.85.0 规则与 context 发现机制

> 调研人:researcher 子代理(PiResearch),2026-09-09。来源:包内 docs + dist 源码互证 + 本机 0.85.0 CLI 冒烟(最强证据为本地源码)。

## 1. context 文件发现

**每目录单文件、候选序固定**(源码 `dist/core/resource-loader.js` `loadContextFileFromDir`):

```
AGENTS.override.md > AGENTS.md > AGENTS.MD > CLAUDE.md > CLAUDE.MD
```

- 同一目录内 **AGENTS.md 遮蔽 CLAUDE.md**(取第一个命中,不合并两者)。[实测 fixture「both」:同目录双文件,结果只含 PKG-BOTH-AGENTS]
- 只有 CLAUDE.md 时正常加载(agentskills 生态兼容位)。
- `AGENTS.override.md` 存在时替代该目录的 AGENTS.md/CLAUDE.md,其他目录照常分层。

**发现范围与顺序**(`loadProjectContextFiles`):

1. 全局:`~/.pi/agent/{AGENTS.override.md|AGENTS.md|CLAUDE.md}`(可用 `PI_CODING_AGENT_DIR` 覆盖)
2. 从 cwd **逐级向上遍历到文件系统根**(不在 git root/home 停止),每目录至多取一个文件
3. 最终顺序:全局 → 最远祖先 → cwd,按 path 去重
- 特例:嵌套在主仓库内的 git worktree 触发 `findShadowedContextFile` 遮蔽去重。
- **`.pi/AGENTS.md`、`.claude/CLAUDE.md` 等子目录路径不是候选**(候选只有目录根)。[实测]
- **无 `@import` 语法**:`grep -rn '@import' dist/core dist/modes` 零命中。

**加载语义:全文、一次性、进系统提示**(`<project_context>` + `<project_instructions path="...">全文</project_instructions>`);`/reload` 或重启刷新;`--no-context-files/-nc` 关闭;扩展可用 `agentsFilesOverride` 钩子改写。

- `.pi/SYSTEM.md`(项目,需 trust)> `~/.pi/agent/SYSTEM.md`(全局)**替换**默认系统提示(context 仍追加);`APPEND_SYSTEM.md` 同序发现、追加于系统提示之后;CLI 另有 `--system-prompt`/`--append-system-prompt`。

## 2. 规则系统

**pi 没有任何 rulebook/rules 机制**:`rulebook`、`alwaysApply`、`.pi/rules`、`.omp`、`.cursor/rules` 在 0.85.0 dist 全部零命中。[grep 实测]

原生可承载「规则」的三个通道:

| 通道 | 位置(0.85.0) | 格式 | 注入方式 |
|---|---|---|---|
| Context files | 见上 | 纯 Markdown,无 frontmatter 语义 | 启动时全文进系统提示(常驻) |
| **Skills**(渐进) | `~/.pi/agent/skills/`、`<cwd>/.pi/skills/`(需 trust)、`.agents/skills/` 自 cwd 向上至 git root(需 trust)、`~/.agents/skills/`、pi packages、`--skill` | `SKILL.md` frontmatter:`name`(≤64)、`description`(必填,≤1024)、`disable-model-invocation`;agentskills.io 标准;尊重 .gitignore/.ignore/.fdignore;递归发现 | **渐进**:系统提示只放 `<available_skills>` 索引,模型按需读 SKILL.md |
| Prompt templates | `~/.pi/agent/prompts/`、`.pi/prompts/`(非递归 .md)、packages | frontmatter `description`/`argument-hint`;`$1/$@/${N:-default}` 参数替换 | **手动**:用户敲 `/name` 展开,不自动注入 |

- Skills 重名:先到先得 + collision 诊断;按 realpath 去重。
- 扩展(TypeScript)是万能逃生舱:可自定义工具/命令/系统提示/compaction/子代理(官方哲学:核心不含 sub-agents/plan mode/权限弹窗,全部交给扩展)。

## 3. agent/角色限定能力

**不能。** pi 核心无子代理(官方 README Philosophy 明示 "No sub-agents")。最接近的能力:

- Skills `disable-model-invocation: true`:从索引隐藏,仅 `/skill:name` 人工调用(可见性开关,非角色过滤);
- Prompt templates:人工触发的分场景提示词,需用户显式敲 `/name`;
- 扩展可自建子代理并各自组装系统提示 → 角色限定只能在扩展层实现,无声明式配置。

## 4. 符号链接兼容性

**全部跟随,实测通过**(直接调用 0.85.0 shipped dist 模块于 /tmp fixture):

| 场景 | 结果 |
|---|---|
| `AGENTS.md` → 指向目录外文件的 symlink | ✅ 加载(`existsSync`+`statSync().isFile()` 均跟随) |
| 整个 `.pi` 目录是 symlink(内含 skills/、prompts/) | ✅ skill 与 prompt template 均被发现 |
| 单个 `SKILL.md` 是 symlink | ✅ 加载 |
| 断链 symlink | 跳过(加载器显式 try/catch continue) |
| 双路径(symlink+原文件)指向同一 skill | 按 canonicalizePath 去重,只加载一次 |

## 5. 版本注记

- 本机 `@earendil-works/pi-coding-agent` **0.85.0**(npm 全局;CHANGELOG 2026-09-04,与 main 几乎同步),所有核对行为无已知分叉。
- **仓库已迁移**:badlogic/pi-mono → **earendil-works/pi**(作者 Mario Zechner/badlogic 延续);**pi.codes 域名已失效**,现行文档域为 **pi.dev**。
- 本机 0.85.0 包内自带 `docs/`(版本精确),结论优先取自包内 docs 并与 dist 源码互证。
- 附带发现:直接 ESM import `dist/core/*.js` 会因可选依赖 `@earendil-works/pi-server` 未安装而失败;CLI 本体走 `dist/bundle/cli.js` 不受影响。

## 6. 对五端统一规则架构的启示

1. **pi 是「根 AGENTS.md 兼容底线」**:pi 只读目录根的 AGENTS.md/CLAUDE.md,不读 `.omp/AGENTS.md`、`.claude/CLAUDE.md`、`.pi/AGENTS.md`、无 @import。对 pi 可见的稳定入口必须落在一个真实的根 `AGENTS.md`(可物化或 symlink——symlink 已实测安全)。omp 的遮蔽分层在 pi 侧完全不存在:pi 看到的就是拼接全文,需在「omp 常驻层」与「pi 可见层」之间做明确的物化策略,避免重复或漏读。
2. **渐进加载在 pi 侧只有一个原生通道:Skills**(agentskills.io 标准)——无 condition/astCondition 触发、无 description→`rule://` 的按需 URI,触发语义只能靠模型读 description 自行判断;`alwaysApply` 语义必须走 AGENTS.md 常驻。
3. **无角色过滤**:分角色规则在 pi 侧只能靠人工触发的 prompt template 或扩展自建子代理;若要求声明式 per-agent 规则,pi 端需小扩展或接受降级为「全量常驻 + skills 按需」两级。

## 验证记录(均为本机 0.85.0)

- fixture(node 直接调用 shipped dist 模块,隔离 agentDir):6 组目录形态 + 系统提示组装,全部断言符合源码预期(遮蔽/顺序/symlink/.pi 忽略)。
- 真实 CLI 冒烟:`cd /tmp/pifix-*/proj/pkg-dotpi && pi -p --no-session --no-extensions --no-skills --no-prompt-templates --no-themes '列出系统提示中所有 project_instructions 块'` → 仅报 `proj/AGENTS.md` 与 `proj/pkg-dotpi/AGENTS.md`,`.pi/AGENTS.md` 未进入上下文。
- fixture 已清理。

## Sources

- earendil-works/pi `packages/coding-agent/{README.md, docs/usage.md}`(与 0.85.0 行为一致,已源码互证)
- 本机 0.85.0 源码(最强证据):`.../pi-coding-agent/dist/core/{resource-loader,system-prompt,skills,prompt-templates,package-manager,trust-manager}.js` + 包内 docs + CHANGELOG

## Gaps

- omp 与 pi 的代码血缘(fork 点/版本对应)未做仓库级考证——本任务只需机制对比,omp 侧事实已由用户核实。
- pi 上游对未来 rules 机制无公开计划信号;「无 rulebook」结论覆盖 0.85.0 及当前 main 文档。
