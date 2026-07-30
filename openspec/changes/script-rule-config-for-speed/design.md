# Design: script-rule-config-for-speed

## Context

动机见 proposal.md。约束现状：`rule-config/SKILL.md` 758 行，全部语义由 LLM 逐步读写执行；07-30 稳定性修复确立了备份屏障、原子发布与候选验证语义；pre-check（#75）已建立"skill 目录内 scripts/ + Agent 绝对路径调用 + /tmp JSON 报告 + `python3 -c` 解读"的仓库先例，并保证 uvx 可用。用户流程固定为 pre-check → rule-config。本设计已经过一轮 codex 独立评审，评审结论（9 条）逐条核实后并入下文。

## Goals / Non-Goals

**Goals:**

- 单一 python3 脚本执行体承载全部确定性文件操作；Agent 只调用脚本、中转提问、解读报告。
- dry-run/apply 两阶段衔接普通模式提问；no-interrupt 单次 apply 完成。
- 现行合并、备份屏障、原子发布、失败关闭语义**逐条**脚本化（含用户意图参数、历史目录、技术栈写入、Markdown 不可解析回退等全部既有分支），行为被"SKILL 条款→fixture/test 映射表"锁定。
- 空项目 no-interrupt 端到端 ≤5 分钟，预算**不含整个 codegraph 步骤（S8，含 install 与 init）**；codegraph 保持同步执行。

**Non-Goals:**

- 不改变 L0/L1 版本号、合并规则、模板内容与路由语义本身（managed-rule-lifecycle 契约不变）。
- 不引入强制新依赖（PyYAML 为运行时依赖，缺失时 uvx 兜底）。
- 不为 codegraph install/init 做异步化或性能优化。
- 不修改 `.claude/rules/` 框架规则与 pre-check。

## Decisions

### D1: python 单脚本，PyYAML 为固定运行时依赖

章节级 Markdown 合并与 YAML 合并是主要复杂度，python 实现可单测、无 BSD/GNU 方言问题（07-30 已踩坑）。备选 bash 主干方案在两种语言间传递章节清单与冲突结构过于别扭，否决。**YAML 处理固定使用真实 parser（PyYAML）**：文本行级处理无法可靠区分 block scalar、flow collection 与 anchor，不能满足结构预检 requirement，该降级方案经评审否决，不留活口。脚本启动时 `import yaml`，缺失即以专属退出码（77）退出并在 stderr 说明，Agent 改用 `uvx --with pyyaml python <脚本>` 重跑（pre-check 保证 uvx 可用）；退出码 77 不算失败，报告照常写出。

### D2: dry-run/apply 两阶段，模式×资产×冲突状态矩阵

脚本 `dry-run` 零写入输出计划（动作、冲突、备份需求）；`apply` 执行。两模式的**动作空间不同**，不是"同一合并、决策来源不同"：

| 资产 | 冲突状态 | 普通模式 | no-interrupt |
|------|---------|---------|-------------|
| 普通规则文件 | 已存在且与模板冲突 | 询问；无响应/拒绝→不覆盖、跳过并报告；确认覆盖→备份后写模板 | 备份后按章节级权威规则合并（模板在前、项目独有章节保留、同名章节项目内容去重后入"项目补充"） |
| 普通规则文件 | Markdown 无法可靠解析 | 询问；无响应→保留并报告 | 备份→写标准结构→原文完整附加到"原项目补充" |
| CLAUDE.md/AGENTS.md（L0） | 各标记/漂移分支 | 按现行 L0 表逐分支询问，无响应→保留并报告 | 纳入双入口统一预检与备份屏障后按现行 L0 表处理 |
| openspec-superpowers-workflow.md（L1） | 版本/漂移分支 | 按现行 L1 表询问，无响应→保留并报告 | 备份后升级或替换并报告 |
| openspec/config.yaml | 结构/类型不兼容、`rules.apply`、无法解析 | 按现行 OpenSpec 表询问，无响应→保留并报告 | 备份后按现行表处理；无法证明无损规范化→终止且原文件不变 |

完整矩阵的固定位置与最小结构在契约期锁定：矩阵正文位于 `references/merge-semantics.md`（任务 3.1 创建），行清单 = 现行 SKILL.md **十张表**逐行迁移，行数与行 ID 基线如下（实施时以此对账）：no-interrupt 权威合并 8 行（NC-01~08）、OpenSpec 配置处理 8 行（OS-01~08）、L1 协作规则增量 7 行（L1-01~07）、L0 入口增量 7 行（L0-01~07）、规则文件增量 4 行（RF-01~04）、摘要引用增量 3 行（SM-01~03）、可选规则增量 4 行（OP-01~04）、CodeGraph 已存在状态处理 8 行（CS-01~08）、CodeGraph 增量处理 8 行（CG-01~08）、历史目录迁移 3 行（HM-01~03）。最小列 = 行 ID / 资产 / 冲突状态 / 普通模式动作 / no-interrupt 动作 / 备份要求 / 报告要求 / 对应测试 ID；任务 3.1 的验收以矩阵行与上述十张表行数一一对应为准。

普通模式提问由 Agent 逐条 `AskUserQuestion`（每次一问、给推荐默认项），决策写入 decisions.json 传入 `apply`。

### D3: CLI 接口与步骤流水线

CLI：`rule-config.py {dry-run|apply} --project-root <path> --report <path> [--no-interrupt] [--decisions <file>] [--project-type coding|non-coding] [--ignore-cadence] [--enable-playwright] [--enable-codegraph]`。后四个为**用户意图参数**，承载现行 SKILL 中"用户明确指定项目类型""用户明确要求忽略 cadence/""用户明确要求启用 Playwright""用户明确要求启用 CodeGraph（即使未检测到源码）"四个分支，由 Agent 从命令参数解析后透传；`--enable-codegraph` 只控制 S8 是否执行，不改变项目类型及其连带语义（规则 2 文本、默认角色等）。Agent 参数解析 MUST 保持现行调用兼容性：命令中完整 token `no-interrupt` 与 `--no-interrupt` 等价，裸 token 一律规范化为 `--no-interrupt` 透传脚本。

decisions.json schema（契约期冻结）：JSON 数组，元素为 `{"conflict_id": "<step>:<资产相对路径>[:<分支标识>]", "decision": "<枚举>"}`；`decision` 枚举按资产类型定义（规则文件/L0/L1：`replace|keep`；OpenSpec `rules.apply`：`remove_apply|keep`；其余分支以矩阵为准）。**决策文件机制仅适用普通模式**：普通模式 `apply` 开始时内部重算新鲜计划，计划无冲突时不要求决策文件，有计划内冲突时校验决策——文件缺失或无法解析、含未知或重复 `conflict_id`、冲突缺少决策、决策与新鲜计划不符，任一发生即非零退出、写出报告且零写入。no-interrupt 模式不读取也不要求决策文件，全部冲突内部按权威规则决策并记录报告。项目类型检测矛盾（现行"先询问，无响应按非 Coding"分支）仅在普通模式以固定冲突标识 `s1:project-type-conflict` 进入决策文件，枚举 `coding|non-coding`，普通模式无响应默认 `non-coding`；no-interrupt 内部按 `non-coding` 决策并在报告中记录该标识与所采用决策。`--report` 与 `--decisions` 路径 MUST 位于项目根之外（建议 `/tmp`），脚本 SHALL 拒绝项目根内的报告/决策路径，保证 dry-run 零写入契约不被报告文件自身破坏。

流水线（每步独立计时、独立状态，失败即终止；**S8 为唯一例外**：install/init/status 失败按 degraded 降级继续）：

- **S1 detect**：有界 find 判项目类型（现行剪枝清单原样）+ 技术栈/包管理器检测（语言、test/lint/format 脚本，未检出写"未检测到"）；`--project-type` 优先于检测结果。
- **S2 locate_templates**：按现行三级规则定位——在线安装路径 → 离线安装路径 → 开发回退 Glob；每候选 MUST 成对校验 `references/rules/` 下 `agent-routing-kernel.md`、`language.md`、`openspec-superpowers-workflow.md`（回退路径还要求 `document-storage.md`）与同级 `references/openspec/config.yaml`；回退路径多候选时取修改时间最新者；全部候选不完整时终止并报告缺失模板。
- **S3 rules_files**：9 个规则文件，按 D2 矩阵处理（含 Playwright 规则：默认跳过，`--enable-playwright` 时创建）。
- **S4 entry_files**：CLAUDE.md/AGENTS.md 一次性处理——L0 区块 + 全部摘要行（含规则 2 按项目类型选择文本、技术栈与包管理器检测结果）单入口至多写入一次；双入口统一预检与全量备份屏障通过后才写任一入口；摘要编号冲突保留原文、追加缺失摘要并在报告中说明。
- **S5 scaffold**：17 个 `cadence/` 子目录；历史目录仅检测现行 16 个精确目录：no-interrupt 只写入报告、禁止 mv/合并/删除/清理；普通模式按现行迁移表处理（目标非空→跳过并报告冲突，不询问）。
- **S6 gitignore**：`.codegraph/`（Coding 项目或 `--enable-codegraph` 时默认加；`codegraph.json` 不加）；`cadence/` 默认不加，仅 `--ignore-cadence` 时追加；行级幂等。
- **S7 openspec_config**：候选构建 → YAML 解析+结构预检 → 保守合并去重 → 备份屏障 → 原子发布。
- **S8 codegraph**：Coding 项目或携带 `--enable-codegraph` 时同步执行。按现行增量状态矩阵执行：`.codegraph/` 已存在→只 `codegraph status` 不重复 init；`.mcp.json` 与 `.codex/config.toml` 双配置齐全→不重复写入；任一配置缺少 CodeGraph MCP→先执行 `codegraph install --target=claude,codex --location=local --yes`，再核验并仅补齐仍缺失的一方；`.codegraph/` 不存在→执行 install 与 init。**install 失败**：仍按 mcp-configuration 兜底配置由脚本自动补齐两份配置文件，步骤标记 degraded 并继续；**init/status 失败**：degraded、报告项目语言/目录规模提示与手动配置建议，不阻断整体；S8 内的配置补写、备份与原子写失败仍终止。S8 耗时单独列出，不计入预算。

横切：统一时间戳备份（`<文件>.cadence-backup-<时间戳>`，OpenSpec 配置与 L1 用现行固定路径）、`os.replace()` 原子写、`merge_markdown()`/`merge_yaml()`/`l0_block()` 三个纯函数库。

### D4: 删除 4 次 openspec instructions 验证

依据：pre-check 已保证 CLI 健康；脚本结构预检比 instructions 更直接地检查字段类型且报错更精确；候选来源封闭（canonical 模板 + 已工作的既有配置），合并只做去重追加不产生新结构；07-30 故障链本质是验证方式在无 change 项目上报错，去掉后临时工作区/临时 Change 一并消失。兜底：备份屏障仍在，用户 openspec 命令报错可恢复。

### D5: 语义权威迁移与 SKILL.md 瘦身

SKILL.md 758 行 → 约 150 行编排骨架（参数解析与透传、两阶段流程、提问规则、报告解读、失败关闭）；**保留现行"下一步：将配置结果传递给 mcp-configuration"交接**，脚本报告以规范字段 `hints.next: "mcp-configuration"` 承载，Agent 汇报后按交接继续。合并语义正文与 D2 完整矩阵移入 `references/merge-semantics.md` 作为按需加载的权威定义，脚本 docstring 做索引。

### D6: 测试对象改为脚本本体，三层手段

1. **单元测试** `tests/test_rule_config.py`（stdlib unittest，零依赖）：三个纯函数库的边界分支，含 Markdown 不可解析回退与 YAML 全类型矩阵。
2. **生命周期集成** `verify-managed-lifecycle.sh`：fixture 项目 → 脚本 CLI → 断言文件系统结果 + report 字段。故障注入**不使用专门接口**：原子发布失败以目标目录 `chmod 555` 复现，备份失败以只读父目录复现（沿用现有 shell 测试手段）。用例集 = 现有 22 个用例迁移 **+ "现行 SKILL 条款→fixture/test 映射表"补齐的缺口用例**（历史目录两模式、普通规则不覆盖、技术栈/包管理器写入、`cadence/` gitignore 两分支、Playwright 两分支、Markdown 不可解析回退、摘要编号冲突、用户意图参数透传）；映射表本身作为测试文件提交。保留 macOS/Linux 双平台与 sha256sum/shasum 回退验收。删除 `managed-lifecycle-reference.sh`。
3. **静态契约检查**（沿用现有"从 SKILL.md 提取 find 命令"先例）：断言 SKILL.md 不含直接读写目标项目文件的操作指令、包含有界扫描与两阶段调用文本——覆盖"Agent 不读写目标项目文件"等无法经文件系统断言的 Agent 行为约束；普通模式逐条提问行为由 SKILL.md 文本规定，纳入静态检查与人工验收，不伪造自动化断言。

预算计时断言：空 fixture 项目 `apply --no-interrupt` 的报告字段 `budget_seconds_excluding_codegraph < 60`（脚本入口→S7 完成，CI 代理指标，留 5 倍余量）；最终验收以真实环境端到端人工计时（Skill 触发→最终汇报，扣除 S8 实际耗时区间）≤5 分钟为准。

## Risks / Trade-offs

- [758 行语义翻译遗漏，脚本行为与旧 Skill 不一致] → "SKILL 条款→fixture/test 映射表"逐条锁定；合并语义正文保留在 references 供比对；实施时逐节对照翻译。
- [python3 或 uvx 在目标环境缺失] → pre-check 环境均有；脚本检测后在报告 hints 给出安装建议。
- [普通模式交互时机变化（冲突集中在 dry-run 后询问）] → 询问内容、推荐默认项与现行表格一一对应，仅时机变化；在 SKILL.md 中明确流程。
- [删除 instructions 验证后极端情况下发布无效 config] → 结构预检 + 封闭候选来源 + 备份屏障兜底；routing-conformance 静态检查仍校验有效 artifact 键。
- [用户意图参数遗漏导致行为回退] → D3 四个参数对应现行全部"用户明确指定/要求"分支，集成测试覆盖透传。
- [单元测试与生命周期测试重复覆盖导致维护成本] → 单测只覆盖纯函数边界分支，集成只覆盖端到端场景，不重复断言中间状态。

## Migration Plan

- 实现顺序：映射表与测试改造（RED）→ 脚本实现（GREEN）→ SKILL.md 瘦身与 references 迁移 → 双平台与真实环境预算验收。
- 回滚：本 change 全部产物在 git 中，回滚即还原 commit；已发布到用户项目的规则文件不受本 change 影响（脚本只在新运行时生效）。
- 老项目重跑 `/rule-config`：脚本幂等，全部 skipped，无迁移动作。
