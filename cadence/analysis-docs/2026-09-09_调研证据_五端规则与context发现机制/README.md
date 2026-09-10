# 调研证据:五端规则与 context 发现机制(2026-09-09)

> 服务于《方案设计:多 CLI 渐进式规则架构》(`cadence/designs/2026-09-09_方案设计_五端渐进式规则架构_v1.0.md`)。
> 四份机制简报由 researcher 子代理产出(官方文档 + 本机无头实测双源);omp/Claude 关键行为由主会话直接实测(见下「直接实测记录」)。
> 本机版本:claude 2.1.247 / codex 0.153.4 / pi 0.85.0(@earendil-works/pi-coding-agent)/ kimi 0.41.0(MoonshotAI)/ omp 18.1.14(can1357/oh-my-pi)。

## 文件清单

| 文件 | 内容 | 来源 |
|---|---|---|
| `codex-0.153.4-机制调研.md` | AGENTS.md 链/32KiB、`.codex/rules`=Starlark 沙箱策略、Skills 渐进、symlink 实测 | researcher(官方文档+6 组无头探针) |
| `kimi-0.41.0-机制调研.md` | AGENTS.md 合并语义、`<!-- From: path -->` 标源、32KB 警告、热重载、Skills 索引、子代理继承、symlink 实测 | researcher(官方文档+binary strings+`-p` 探针) |
| `pi-0.85.0-机制调研.md` | 每目录单文件候选序、根 AGENTS.md 遮蔽 CLAUDE.md、无 rulebook/@import、Skills 渐进、symlink 全通 | researcher(包内 docs+dist 源码互证+CLI 冒烟) |
| `claude-2.1.247-rules语义调研.md` | 仅 `paths` 两档、无 description 档、frontmatter 剥离、@import 4 跳、根内/根外 symlink 差异 | researcher(InstructionsLoaded hook 审计) |
| 本文件「直接实测记录」 | omp rulebook 软链/agents 过滤/paths 容忍/活引用;Claude `paths: []` 强载 | 主会话(/tmp fixture,2026-09-09) |

## 直接实测记录(主会话,2026-09-09,omp 18.1.14 与 claude 2.1.247)

### A. omp rulebook 扫描与软链(fixture `/tmp/omp-fx`,全新 `omp -p --model smol` 会话)

| # | 实验 | 命令要点 | 结果 |
|---|---|---|---|
| A1 | 三目录扫描+去重 | `.omp/rules/`+`.agents/rules/` 各放规则(其中 `.agents/rules/linked-claude.md` 为软链→`.claude/rules/phys-claude.md`,两目录同名) | 系统提示 `<domain-rules>` 索引仅 3 行(按名去重):`linked-claude`/`native-omp`/`compat-agents`;三个正文 marker 均不在上下文(正文零内联) |
| A2 | 目录级软链 | `.omp/rules` 整目录软链→`../.claude/rules`(内含 2 个物理规则) | **不发现**:索引无 phys-claude/second;仅 `.agents/rules` 的条目可见 → omp 目录级软链不被扫描 |
| A3 | `.omp/rules` 原生目录文件级软链 | `.omp/rules/phys-claude.md`→`../.claude/rules/phys-claude.md` | **不发现**(`rule://phys-claude` Unknown;可用列表仅 compat-agents+用户级 go-*/rs-*/ts-*)→ 原生目录文件级软链被排除 |
| A4 | `.agents/rules` 文件级软链 | `.agents/rules/phys-claude.md`→`../../.claude/rules/phys-claude.md` | **索引可见 + `rule://phys-claude` 读到正文**(`PHYS-CLAUDE-BODY-9f3a` 逐字返回)→ 兼容层文件级软链全链路通 |
| A5 | `agents:` 过滤(经软链) | 同一 `.claude/rules/` 下 `main-only.md`(agents:[main])与 `scout-only.md`(agents:[scout]),双双软链入 `.agents/rules/` | 主会话索引含 `main-only` 不含 `scout-only`;两正文 marker 均不内联 → 过滤生效且与软链正交 |
| A6 | Claude `paths:` 字段容忍 | 规则带 `description`+`paths:["**/*.rs"]`,软链入 `.agents/rules/` | 正常进 description 索引桶;`rule://` 正文可读 → 共享 frontmatter 契约可行 |
| A7 | `@import` 活引用 | `.omp/AGENTS.md` 内容仅一行 `@../.claude/CLAUDE.md` | 上下文 `<file path=".omp/AGENTS.md">` 内联展开 `.claude/CLAUDE.md` 全文(含 marker)→ CodeGraph 块零副本可行 |

索引行格式实测:`- <规则名> (): <description>`(括号为触发条件占位);omp 用户级规则目录 `~/.omp/agent/rules/` 的 go-*/rs-*/ts-* 与项目级并存。

### B. Claude Code `paths` 语义(fixture `/tmp/cc-paths-fx`,InstructionsLoaded hook 审计)

| # | 实验 | 结果 |
|---|---|---|
| B1 | `bhv.md`(frontmatter `description`+`paths: []`)与 `always.md`(仅 `description`) | 两者均 `session_start` 载入 → **`paths: []` 不构成「永不自动载入」桶,仍强载**;行为路由桶必须用永不匹配 glob |
| B2 | 无 hook 的裸探针(`-p` 后 grep transcript) | transcript 无规则 marker——无头模式不经 hook 无法可靠审计规则装载; InstructionsLoaded hook 为地面真相 |

### C. 关键否定项汇总(跨五端)

- Claude Code:不读 `AGENTS.md`;`description`/`always-apply`/`globs` 字段无效;根外软链无头不装载;`.mdc` 不发现。
- Codex:不读 `CLAUDE.md`/`.claude/rules`;无 markdown 规则目录(openai/codex#17401 提案未实现);无 `@import`。
- Kimi:不读 `CLAUDE.md`/`.claude/rules`/项目 `.agents/AGENTS.md`;0.41.0 启动上下文无 `.claude/rules` 文件名(修正 2026-09-02 探针在 0.40.x 的观察)。
- pi:不读 `.omp/`/`.claude/`(子目录路径非候选);无 rulebook、无 `@import`。
- omp:不读 `.claude/rules`;`.omp/rules` 原生目录不吃软链(目录级与文件级均不,见 A2/A3)。

## 引用方式

设计文档 §2 对照表与 §5-§8 的每条机制断言,均可回溯到上述四份简报或直接实测记录;后续 OpenSpec change 与实施 Plan 直接引用本目录,不重复展开。
