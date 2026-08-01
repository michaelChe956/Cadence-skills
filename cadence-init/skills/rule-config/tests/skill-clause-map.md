# rule-config SKILL 条款 → fixture/test 语义对账映射表

> 版本：v1.0（2026-07-30）
> 依据：现行 `cadence-init/skills/rule-config/SKILL.md`（758 行，权威行为定义）+ OpenSpec change `script-rule-config-for-speed` design D2 行 ID 基线。
> 行号基准：SKILL 行号区间基于瘦身前 758 行版本（行号对账基准），新 SKILL.md 已瘦身为编排骨架，语义正文见 references/merge-semantics.md。
> 用途：Task 2/3 的用例清单来源；Task 10 语义迁移矩阵正文来源。本文档作为测试文件提交，后续任何脚本行为变更必须先与本文档对账。

## 0. 命名与列定义

- 最小列（逐字）：`SKILL 行号区间 | 条款摘要 | 适用模式 | 脚本函数或 references 条目 | fixture | 测试 ID | 关键断言`
- 测试 ID 命名（逐字）：单测 `ut-<函数>-<场景>`，集成 `it-<步骤>-<场景>`，静态 `sc-<条款>`
- fixture 命名（逐字）：`fx-<场景>`
- 条款编号：十张表沿用 design D2 行 ID 基线并新增 RF-05（NC-01~08、OS-01~08、L1-01~07、L0-01~07、RF-01~05、SM-01~03、OP-01~04、CS-01~08、CG-01~08、HM-01~03，共 62 行）；其余条款由本文档分配唯一编号（PM、FM、NR、NB、NH、DF、IA、CK、NX、S1a、S1b、S1d、L0-P、S3~S10、OS-N、CP 等前缀），编号在"条款摘要"列首标注。
- 适用模式取值：`普通` / `no-interrupt` / `两模式`。
- 脚本函数名为 Task 4+ 将实现的目标名（`merge_markdown` / `merge_yaml` / `l0_block` / `classify_l1` / `precheck_openspec_structure` / `backup_file` / `atomic_write` / `sha256_file` / `detect_project` / `locate_templates` / `step_rules_files` / `step_entry_files` / `step_scaffold` / `step_gitignore` / `step_openspec_config` / `step_codegraph`）；静态与 Agent 行为条款记为 `references/merge-semantics.md` 对应节或 `—（静态）`。
- 故障注入约定（design D6）：原子发布失败以目标目录 `chmod 555` 复现，备份失败以只读父目录复现，对应 fixture 记 `fx-readonly-target` / `fx-readonly-parent`。

## 1. 条款清单总览（Step 1 登记结果）

| 节 | SKILL 行号区间 | 条款编号 | 数量 |
|----|----------------|----------|------|
| frontmatter | 1-5 | FM-01 | 1 |
| 概述 | 9-11 | OV-01 | 1 |
| 参数模式 | 13-25 | PM-01~03 | 3 |
| no-interrupt 通用规则 | 27-33 | NR-01~05 | 5 |
| no-interrupt 权威合并规则（表 NC） | 35-50 | NC-01~08、NB-01~02 | 10 |
| no-interrupt 历史目录规则 | 52-56 | NH-01~03 | 3 |
| 无交互默认策略（表） | 58-73 | DF-01~08 | 8 |
| 人工交互策略（表+提问规则） | 75-93 | IA-01~05、IA-R1~R4 | 9 |
| 检查清单 11 项 + 交接 | 95-111 | CK-01~11、NX-01 | 12 |
| 处理流程 S1（1a/1b/1c/1d） | 115-183 | S1a-01~05、S1b-01~04、S1c-01、S1d-01~11 | 21 |
| 处理流程 S2（L0 处理 12 条 + 两模板 + 注意） | 185-308 | L0-P1~P12、S2-T1~T3 | 15 |
| 处理流程 S3 包管理器 | 310-333 | S3-01~02 | 2 |
| 处理流程 S4 技术栈 | 335-375 | S4-01~05 | 5 |
| 处理流程 S5 目录结构 | 377-406 | S5-01~02 | 2 |
| 处理流程 S6 历史产物迁移（表 HM + 禁止迁移 + 命令/报告） | 408-460 | HM-01~03、S6-01~02 | 5 |
| 处理流程 S7 gitignore | 462-481 | S7-01~02 | 2 |
| 处理流程 S8 代码阅读 | 483-497 | S8-01~03 | 3 |
| 处理流程 S9 CodeGraph（表 CS + gitignore + 增量要求） | 499-580 | S9-01~04、CS-01~08 | 12 |
| 处理流程 S10 Playwright | 582-600 | S10-01~03 | 3 |
| 增量运行-规则文件（表 RF） | 606-629 | RF-01~05 | 6 |
| 增量运行-OpenSpec 配置（13 条 + 表 OS + 备份/报告段） | 631-675 | OS-N1~N13、OS-01~08、OS-B1~B2 | 23 |
| 增量运行-L1 协作规则（表 L1 + 备份/识别段） | 677-689 | L1-01~07、L1-B1~B2 | 9 |
| 增量运行-L0 入口（表 L0 + 屏障段） | 691-711 | L0-01~07、L0-B1~B2 | 9 |
| 增量运行-摘要引用（表 SM） | 713-717 | SM-01~03 | 3 |
| 增量运行-可选规则（表 OP） | 719-728 | OP-01~04 | 4 |
| 增量运行-CodeGraph（表 CG） | 730-743 | CG-01~08 | 8 |
| 建议 | 745-748 | AD-01 | 1 |
| 核心原则 | 750-758 | CP-01~07 | 7 |

## 2. 映射表（Step 2）

### 2.1 frontmatter、概述与参数模式

| SKILL 行号区间 | 条款摘要 | 适用模式 | 脚本函数或 references 条目 | fixture | 测试 ID | 关键断言 |
|----------------|----------|----------|----------------------------|---------|---------|----------|
| 1-5 | FM-01 frontmatter 含 `disable-model-invocation: true` 且瘦身（Task 9/10）后保留 | 两模式 | —（静态） | —（仓库内 SKILL.md） | sc-frontmatter-disable-model-invocation | SKILL.md frontmatter 解析出 `disable-model-invocation: true` |
| 9-11 | OV-01 默认无人工交互策略，按自动检测结果与保守默认值继续 | 两模式 | references/merge-semantics.md 概述节 | fx-empty-project | it-apply-default-policy | 无参数 apply 全程无提问、按默认值完成且报告记录默认值 |
| 13-21 | PM-01 三种调用形式；完整 token `no-interrupt` 与 `--no-interrupt` 等价，裸 token 一律规范化为 `--no-interrupt` 透传 | 两模式 | —（Agent 参数解析，design D3） | fx-empty-project | it-cli-bare-token | 以裸 token 调用与以 `--no-interrupt` 调用产生相同模式与相同报告 `mode` 字段 |
| 23 | PM-01b（含 PM-01）token 必须是完整 token，子串不触发 | 两模式 | —（Agent 参数解析） | fx-empty-project | it-cli-token-substring | `xno-interruptx` 等子串不进入 no-interrupt 模式 |
| 24 | PM-02 未携带参数进入普通模式，遵循不覆盖、冲突跳过、人工交互、历史迁移逻辑 | 普通 | —（Agent 参数解析） | fx-existing-rules | it-cli-normal-mode | 无参数运行报告 `mode=normal`，已存在文件不覆盖 |
| 25 | PM-03 两模式互斥，no-interrupt 合并/禁迁移规则不得应用于普通模式 | 两模式 | references/merge-semantics.md 模式互斥节 | fx-history-dirs | it-cli-mode-exclusive | 普通模式下历史目录按 HM 表迁移而非仅报告；no-interrupt 下权威合并生效 |

### 2.2 no-interrupt 通用规则（NR）

| SKILL 行号区间 | 条款摘要 | 适用模式 | 脚本函数或 references 条目 | fixture | 测试 ID | 关键断言 |
|----------------|----------|----------|----------------------------|---------|---------|----------|
| 29 | NR-01 禁止调用提问工具 | no-interrupt | —（静态） | —（仓库内 SKILL.md） | sc-ni-no-ask | 瘦身后的 SKILL.md no-interrupt 路径无 `AskUserQuestion`/`request_user_input` 指令文本 |
| 30 | NR-02 禁止等待输入、超时或推荐默认值继续 | no-interrupt | —（静态） | —（仓库内 SKILL.md） | sc-ni-no-wait | no-interrupt 章节不含"询问/等待/超时"指令 |
| 31 | NR-03 冲突按确定性规则合并，不得跳过后继续 | no-interrupt | merge_markdown / merge_yaml | fx-existing-rules | it-apply-conflict-deterministic | 同一冲突 fixture 两次运行产物 sha256 一致，报告无"跳过冲突文件"项 |
| 32 | NR-04 无法安全合并先备份；备份或写入失败立即报错终止 | no-interrupt | backup_file / atomic_write | fx-readonly-parent | it-apply-backup-fail-abort | 备份失败时非零退出、目标文件零改动、报告含失败文件与原因 |
| 33 | NR-05 失败报告含失败文件、失败原因、已完成项目、恢复建议 | no-interrupt | —（报告 schema） | fx-readonly-parent | it-apply-failure-report-fields / ut-run_apply-fail-schema / ut-extract-failure-file-message | 失败报告四字段齐全且已完成步骤逐项列出；overall 收敛 ok/degraded/fail 三值（终审 I-4） |

### 2.3 no-interrupt 权威合并规则（NC-01~08，SKILL 39-48 行表）

> 本表映射仅适用于非框架资产；`.claude/rules/` 下 7 个框架受管规则文件改用 RF-05 权威全覆盖，不调用 `merge_markdown`。

| SKILL 行号区间 | 条款摘要 | 适用模式 | 脚本函数或 references 条目 | fixture | 测试 ID | 关键断言 |
|----------------|----------|----------|----------------------------|---------|---------|----------|
| 41 | NC-01 目标文件不存在→创建标准文件 | no-interrupt | merge_markdown / merge_yaml | fx-empty-project | ut-merge_markdown-target-missing | 返回标准模板全文；集成侧 it-s3-create 断言文件创建且与模板一致 |
| 42 | NC-02 非框架资产：模板与项目存在不同章节→保留模板章节，按原顺序保留项目独有章节 | no-interrupt | merge_markdown | fx-md-extra-sections | ut-merge_markdown-keep-project-sections | 输出含全部模板章节且项目独有章节按原顺序保留；框架受管规则文件不适用 |
| 43 | NC-03 非框架资产：同名章节→模板规范在前，项目独有内容去重后追加到该章节"项目补充"；`**项目补充**` 为合并协议保留字，重复合并幂等，历史重复标记污染可自愈；合并结果逐字一致时跳过写盘并报告 `unchanged` | no-interrupt | merge_markdown | fx-md-same-section | ut-merge_markdown-same-section-append / ut-merge_markdown-rerun-idempotent / ut-merge_markdown-polluted-self-heal / ut-step_s3-ordinary-unchanged | 模板内容在前；项目独有行进入"项目补充"且按完整行去重；`merge(t, merge(t, x)) == merge(t, x)`；框架受管规则文件不适用 |
| 44 | NC-04 CLAUDE.md/AGENTS.md 强制规则冲突→摘要与引用路径以 rule-config 为准，技术栈/命令/业务规则等保留 | no-interrupt | merge_markdown / l0_block | fx-entry-mandatory-conflict | ut-merge_markdown-mandatory-override | 强制规则摘要以模板为准；项目技术栈等章节原文保留 |
| 45 | NC-05 `openspec/config.yaml` 已存在→保留 schema、context 与四个 artifact 额外规则，仅追加缺失内容；发现 `rules.apply` 先备份再移除 | no-interrupt | merge_yaml | fx-openspec-existing | ut-merge_yaml-preserve-existing | schema/项目 context/额外规则原样保留；模板缺失内容追加；`rules.apply` 仅在备份成功后移除 |
| 46 | NC-06 OpenSpec YAML 无法可靠解析或结构/类型不兼容→先备份；无法证明无损规范化则终止，原文件不变；备份成功≠授权破坏性重写 | no-interrupt | precheck_openspec_structure / merge_yaml / backup_file | fx-openspec-unparseable | ut-merge_yaml-unparseable-abort | 无法解析时返回终止信号；目标文件 sha256 不变；已创建备份存在 |
| 47 | NC-07 内容完全重复→只保留一份 | no-interrupt | merge_markdown / merge_yaml | fx-md-duplicate | ut-merge_markdown-dedupe | 重复行/章节只出现一次 |
| 48 | NC-08 非框架 Markdown 无法可靠解析（或无 ATX 标题/有实质前言，终审 I-1 同路径）→先备份，再写标准结构，原内容附加到"原项目补充" | no-interrupt | merge_markdown / backup_file | fx-markdown-unparseable | ut-merge_markdown-unparseable-fallback / ut-merge_markdown-no-headings-fallback / ut-merge_markdown-preamble-fallback / it-s3-markdown-unparseable-fallback | 输出为标准结构；原文完整出现在"原项目补充"；备份存在；框架受管规则文件不适用 |

### 2.4 权威合并辅助条款（NB）与历史目录规则（NH）

| SKILL 行号区间 | 条款摘要 | 适用模式 | 脚本函数或 references 条目 | fixture | 测试 ID | 关键断言 |
|----------------|----------|----------|----------------------------|---------|---------|----------|
| 50 | NB-01 同名章节以"标题级别 + 去除开头编号后的标题文本"识别 | 两模式 | merge_markdown | fx-md-numbered-headings | ut-merge_markdown-section-identity | `## 1. 语言规则` 与 `## 语言规则` 识别为同名章节；级别不同不判同名 |
| 50 | NB-02 复制归档到 `cadence/legacy/<时间戳[-N]>/<相对 root 路径>`；原位文件不动；同秒冲突后缀加在时间戳目录；每次归档前验证/修复 `.gitignore` 为 `*\n!.gitignore\n` | 两模式 | backup_file | fx-existing-rules | ut-backup_file-legacy-copy / ut-backup_file-legacy-gitignore / ut-backup_file-unique-suffix | 路径匹配 `^cadence/legacy/[0-9]{14}(-[0-9]+)?/.+$`；归档内容与原文件一致；原位文件仍在；`.gitignore` 内容固定且损坏后可修复；同秒两次归档不覆盖首个恢复点 |
| 54 | NH-01 no-interrupt 只检测 16 个精确历史目录清单 | no-interrupt | step_scaffold | fx-history-dirs | it-s5-history-report-only | 报告检出目录恰为清单内存在的目录；清单外同名目录不检出 |
| 55 | NH-02 检测到历史目录仅写报告，不 mv、不合并、不删除、不清理空目录 | no-interrupt | step_scaffold | fx-history-dirs | it-s5-history-no-interrupt | apply 后 `.claude/<dir>` 与 `cadence/<dir>` sha256/清单均不变，报告含检出清单 |
| 56 | NH-03 本规则只覆盖 no-interrupt；普通模式继续原有历史产物迁移步骤 | 普通 | step_scaffold | fx-history-dirs | it-s5-history-normal | 普通模式按 HM-01~03 执行迁移/跳过并报告 |

### 2.5 无交互默认策略表（DF-01~08）

| SKILL 行号区间 | 条款摘要 | 适用模式 | 脚本函数或 references 条目 | fixture | 测试 ID | 关键断言 |
|----------------|----------|----------|----------------------------|---------|---------|----------|
| 66 | DF-01 检测到源码或主配置→Coding；否则非 Coding | 两模式 | detect_project | fx-coding-project / fx-noncoding-project | ut-detect_project-coding / ut-detect_project-noncoding | 返回类型与预期一致并写入报告 |
| 67 | DF-02 技术栈自动检测写入；未检出写"未检测到" | 两模式 | detect_project / step_entry_files | fx-techstack-frontend | it-s1-techstack | CLAUDE.md/AGENTS.md 项目技术栈章节含检出值；缺失命令字段为"未检测到" |
| 68 | DF-03 历史迁移无冲突自动迁移；目标非空跳过并报告 | 普通 | step_scaffold | fx-history-target-nonempty | it-s5-history-conflict-skip | 非空目标目录不动，报告含冲突项 |
| 69 | DF-04 `cadence/` 默认不加入 `.gitignore` | 两模式 | step_gitignore | fx-empty-project | it-s6-cadence-gitignore-default | `.gitignore` 不含 `cadence/` 行 |
| 70 | DF-05 代码阅读规则所有项目创建；非 Coding 只跳过 CodeGraph 初始化 | 两模式 | step_rules_files | fx-noncoding-project | it-s3-code-reading-all-projects | 非 Coding 项目仍存在 `.claude/rules/code-reading.md` |
| 71 | DF-06 CodeGraph 初始化 Coding 默认启用、非 Coding 默认跳过 | 两模式 | step_codegraph | fx-noncoding-project | it-s8-codegraph-skip-noncoding | 非 Coding 项目不生成 `.codegraph/`，报告记录跳过原因 |
| 72 | DF-07 Playwright 规则默认跳过，仅用户明确要求时启用 | 两模式 | step_rules_files | fx-empty-project | it-s3-playwright-skip | 默认不产生 `.claude/rules/playwright.md` 与摘要 |
| 73 | DF-08 框架受管规则文件内容一致时幂等跳过；缺失文件/摘要/配置块按各表补齐；框架规则 drift 按 RF-05/IA-01 处理（普通询问/无响应默认 keep，no-interrupt 权威全覆盖） | 两模式 | step_rules_files / step_entry_files / step_openspec_config | fx-existing-rules | ut-s3-authoritative-overwrite / ut-s3-authoritative-idempotent | 内容一致文件不写盘、不归档并报告 `unchanged`/跳过；框架 drift 不走章节合并，权威覆盖结果逐字等于所选模板 |

### 2.6 人工交互策略表（IA-01~05）与提问规则（IA-R1~R4）

| SKILL 行号区间 | 条款摘要 | 适用模式 | 脚本函数或 references 条目 | fixture | 测试 ID | 关键断言 |
|----------------|----------|----------|----------------------------|---------|---------|----------|
| 83 | IA-01 即将覆盖已有框架受管规则文件（RF-05 drift）→先询问；**无响应则默认 keep 保留并报告 status=0**（A 类，有安全默认，§11.6）；决策 `keep`→不覆盖，决策 `replace`→全局屏障归档后以模板权威覆盖 | 普通 | step_rules_files（决策枚举 `replace\|keep`；drift 标 `default_keep: true`，无响应默认 keep） | fx-existing-rules | it-s3-normal-keep-decision（keep 分支）/ it-s3-rules-drift-replace（replace 分支，待补） | drift 冲突标识 `s3:<rel>`；无 decisions 时 apply status=0 且文件不变；replace 后目标逐字等于模板且不产生项目补充 |
| 84 | IA-02 项目类型判定两模式规则（codex 五轮重构）：no-interrupt 以检测结果为准（CLI 完全忽略）；普通模式 CLI `--project-type coding` 仅能把 non-coding 提升为 coding，检测为 coding 时无论 CLI 取何值均为 coding；任一组合唯⼀确定，不产生冲突 | 两模式 | detect_project / compute_plan | fx-s1-no-interrupt-ignores-cli / fx-s1-no-interrupt-detect-coding / fx-s1-normal-cli-promotes / fx-s1-normal-detect-coding / fx-s1-normal-no-cli-noncoding | it-s1-no-interrupt-ignores-cli / it-s1-no-interrupt-detect-coding / it-s1-normal-cli-promotes / it-s1-normal-detect-coding / it-s1-normal-no-cli-noncoding | 五用例覆盖两模式行表；final `project_type` 与 S8 启用/跳过与预期一致 |
| 85 | IA-03 用户明确要求启用默认跳过项但缺少必要信息→问最少必要信息；无响应跳过该可选项 | 普通 | —（Agent 提问，design D3） | fx-empty-project | sc-ia-optional-ask | SKILL.md 保留"最少必要信息/无响应跳过"文本 |
| 86 | IA-04 迁移旧目录目标非空→不询问、不合并，直接跳过并报告冲突 | 普通 | step_scaffold | fx-history-target-nonempty | it-s5-history-conflict-no-ask | dry-run/apply 计划不生成该目录的提问冲突项，报告直接记冲突跳过 |
| 87 | IA-05 需要真实密钥→不询问真实密钥，只写占位符并提示替换 | 两模式 | —（静态） | —（仓库内 SKILL.md） | sc-ia-secrets-placeholder | 全文无索取真实密钥的指令文本；占位符约定保留 |
| 89-93 | IA-R1~R4 每次一问、给推荐默认、超时采用推荐默认、无法等待采用保守默认（不覆盖/不删除/不提交密钥/不启用高成本可选项） | 普通 | —（Agent 提问规则） | —（仓库内 SKILL.md） | sc-ask-rules | 瘦身后 SKILL.md 提问规则四条原文语义保留 |

### 2.7 检查清单（CK-01~11）与交接（NX-01）

| SKILL 行号区间 | 条款摘要 | 适用模式 | 脚本函数或 references 条目 | fixture | 测试 ID | 关键断言 |
|----------------|----------|----------|----------------------------|---------|---------|----------|
| 99-109 | CK-01~11 十一项检查清单按顺序完成，逐项对应 S1~S11 | 两模式 | step_* 全流水线 | fx-empty-project | it-apply-step-order | 报告步骤顺序为 S1→S8（含 openspec_config）且逐步独立状态；前步失败后续不执行 |
| 111 | NX-01 下一步交接：配置结果传递给 mcp-configuration | 两模式 | —（报告 `hints.next`） | fx-empty-project | it-apply-hints-next | 成功报告含 `hints.next: "mcp-configuration"` |

### 2.8 处理流程 S1：项目检测与模板定位

| SKILL 行号区间 | 条款摘要 | 适用模式 | 脚本函数或 references 条目 | fixture | 测试 ID | 关键断言 |
|----------------|----------|----------|----------------------------|---------|---------|----------|
| 119-137 | S1a-01 一次有界首命中扫描判定项目类型；剪枝目录与源码扩展名清单原样 | 两模式 | detect_project | fx-coding-project | ut-detect_project-bounded-scan | 剪枝目录内源码不触发 Coding 判定；首命中即返回 |
| 121-137 | S1a-02 find 命令剪枝清单文本契约（沿用静态提取先例） | 两模式 | —（静态） | —（仓库内 SKILL.md） | sc-find-prune-list | 从 SKILL.md 提取的 find 命令与脚本内剪枝清单逐项一致 |
| 131/133-135 | S1a-03 有输出或存在主工程配置→Coding；全无→非 Coding；检测结果记入报告 | 两模式 | detect_project | fx-noncoding-project | ut-detect_project-main-config | 仅含 `package.json`/`pyproject.toml` 等主配置即判 Coding；报告记录检测证据 |
| 136 | S1a-04 项目类型按两模式唯⼀规则确定（`--project-type`：普通模式仅提升 non-coding→coding；no-interrupt 完全忽略；codex 五轮重构，原「用户指定优先」与 s1 冲突已删） | 两模式 | detect_project / compute_plan | fx-noncoding-project / fx-coding-project | ut-detect_project-ignores-cli / ut-final-project-type-* / it-s1-normal-cli-promotes / it-s1-no-interrupt-ignores-cli | 检测结果 + CLI 按两模式规则计算 final `project_type`；detect 不读取 CLI |
| 133 | S1a-05 无人工交互模式下不等待用户确认 | no-interrupt | detect_project | fx-empty-project | it-s1-no-confirm | no-interrupt 下检测直接落报告，无提问冲突项 |
| 138-157 | S1b-01 模板目录三级定位：在线安装路径→离线安装路径→开发回退 Glob | 两模式 | locate_templates | fx-templates-online / fx-templates-offline / fx-templates-dev | ut-locate_templates-online / ut-locate_templates-offline / ut-locate_templates-fallback | 各级候选按优先级命中并返回成对路径 |
| 143/147/156/159 | S1b-02 每候选成对校验 rules 三件套（回退另需 document-storage.md）+ 同级 `references/openspec/config.yaml`；缺 config.yaml 不得选用 | 两模式 | locate_templates | fx-templates-incomplete | ut-locate_templates-pair-check | 缺任一成对文件的候选被跳过 |
| 157 | S1b-03 回退路径多候选取修改时间最新者 | 两模式 | locate_templates | fx-templates-multi | ut-locate_templates-mtime-latest | 返回 mtime 最新的通过验证候选 |
| 159 | S1b-04 全部候选不完整时终止并报告缺失模板 | 两模式 | locate_templates | fx-templates-all-incomplete | ut-locate_templates-all-incomplete / it-s2-templates-missing | 非零退出；报告列出各候选缺失项；目标项目零写入 |
| 161-165 | S1c-01 创建 `.claude/rules`（幂等） | 两模式 | step_rules_files | fx-empty-project | it-s3-mkdir-idempotent | 重复运行不报错、目录权限不变 |
| 171-181 | S1d-01 `.claude/rules/` 框架受管清单为 7 个：mcp-servers/code-reading/document-storage/language/markdown-format/code-usage/playwright；Playwright 按启用/已存在条件进入处理，L1 独立于此清单 | 两模式 | step_rules_files | fx-empty-project | ut-s3-authoritative-overwrite / ut-s3-authoritative-idempotent | 受管落地名不含 agent-routing-kernel；存在 drift 时权威覆盖，内容一致时幂等跳过 |
| 179-180 | S1d-02 `code-usage-coding.md`/`code-usage-noncoding.md` 按最终项目类型单选来源，始终写入 `.claude/rules/code-usage.md`；历史双文件归档后移除 | 两模式 | step_rules_files | fx-coding-project / fx-noncoding-project | TestCodeUsageSingleSource / test_coding_project_gets_code_usage_md / test_noncoding_project_gets_noncoding_source_at_fixed_name / test_code_usage_asset_records_selected_template_source | Coding 内容=coding 模板；非 Coding 内容=noncoding 模板；plan 的 `template_source` 与项目类型一致；双来源文件不落地 |
| 183 | S1d-03 L1 独立分支：`openspec-superpowers-workflow.md` 按版本升级特例处理；7 个框架受管规则文件按 RF-05 权威全覆盖 | 两模式 | step_rules_files / classify_l1 | fx-existing-rules | it-s3-l1-independent / ut-s3-authoritative-overwrite | L1 走版本化分类且不调 `merge_markdown`；框架规则 drift 逐字覆盖为模板 |

### 2.9 处理流程 S2：入口文件与 L0 受管区块（L0-P1~P12）

| SKILL 行号区间 | 条款摘要 | 适用模式 | 脚本函数或 references 条目 | fixture | 测试 ID | 关键断言 |
|----------------|----------|----------|----------------------------|---------|---------|----------|
| 189 | L0-P1 读取模板根 `agent-routing-kernel.md` 完整内容作为规范源 | 两模式 | l0_block | fx-empty-project | ut-l0_block-read-source | 区块内容 sha256 与规范源文件一致 |
| 190 | L0-P2 双入口统一预检：标记、版本、完整内容、交互结果、目标动作、全部备份需求 | 两模式 | l0_block / step_entry_files | fx-l0-drift | it-s4-unified-precheck | dry-run 计划同时列出 CLAUDE.md 与 AGENTS.md 各自分支与备份需求 |
| 191 | L0-P3 写入任一入口前，先把本次全部必要 L0 恢复点复制归档到 `cadence/legacy/<时间戳[-N]>/<相对路径>` | 两模式 | backup_file / step_entry_files | fx-l0-drift | test_l0_second_archive_failure_keeps_both | 第二个入口归档失败时第一个入口也尚未写入；原位双入口内容不变 |
| 192 | L0-P4 任一必要复制归档失败→立即终止，双入口均不得写入；任一 `atomic_write` 失败→失败入口原文件因 `os.replace` 原子性保持不变 | 两模式 | backup_file / atomic_write | fx-readonly-parent | test_l0_second_archive_failure_keeps_both / test_atomic_write_failure_keeps_original | 归档屏障失败时 CLAUDE.md/AGENTS.md 均不变；原子覆盖失败时目标原文件不变且已建归档保留 |
| 193 | L0-P5 目标入口不存在→创建基础入口，L0 放在文件说明之后、`## 强制规则` 之前 | 两模式 | l0_block / step_entry_files | fx-empty-project | it-entry-base-created | 新建入口含基础模板全文；L0 位置在文件说明与 `## 强制规则` 之间（基础入口文本断言） |
| 194 | L0-P6 当前 v1 标记成对且区块与规范源完全一致→跳过 | 两模式 | l0_block | fx-entry-idempotent | it-s4-idempotent | 两入口 sha256 不变；报告幂等跳过 |
| 195 | L0-P7 当前 v1 标记成对但区块不一致→视为本地修改：普通询问（无响应则默认 keep 保留并报告 status=0，A 类 §11.6；确认替换纳入备份屏障）；no-interrupt 纳入屏障后替换并报告 | 两模式 | l0_block / backup_file（标 `default_keep: true`） | fx-l0-drift | it-s4-drift-normal / it-l0-drift-normal-keep-default / it-s4-drift-replaced-outside-preserved | 普通无响应保留并报告 status=0（default_keep）；no-interrupt 备份后区块=规范源 |
| 196 | L0-P8 两个标记都不存在→在首个 `## 强制规则` 前插入；无该标题则在文件说明后插入 | 两模式 | l0_block | fx-entry-no-markers | ut-l0_block-insert-position | 插入位置符合两分支；原文内容不动 |
| 197 | L0-P9 成对受支持旧版本标记→纳入备份屏障，屏障通过后升级为当前 v1 并报告 | 两模式 | l0_block / backup_file | fx-l0-old-version | it-s4-upgrade | 备份存在；区块替换为当前 v1；报告记升级 |
| 198 | L0-P10 单侧标记或顺序错误→普通询问（无响应则默认 keep 保留并报告 status=0，A 类 §11.6）；no-interrupt 屏障通过后写入单一 L0 区块并报告 | 两模式 | l0_block（标 `default_keep: true`） | fx-l0-broken-markers | it-s4-broken-markers-preserve-arbitrary | 处理后 start/end 标记各出现一次；区块外前置/后置/本地内容原样保留 |
| 199 | L0-P11 区块外项目技术栈、命令、业务规则和用户内容必须原样保留 | 两模式 | l0_block | fx-l0-drift | it-s4-outside-preserved | 区块外内容 sha256 处理前后一致 |
| 200 | L0-P12 CLAUDE.md 与 AGENTS.md 必须使用相同 L0 版本和语义 | 两模式 | step_entry_files | fx-l0-drift | it-s4-dual-entry-consistency | 两入口受管区块 sha256 相同 |
| 203-241 | S2-T1 CLAUDE.md 基础模板结构（含规则 1~7 摘要、`## 项目信息`、currentDate） | 两模式 | step_entry_files | fx-empty-project | it-s4-entry-template-claude | 新建 CLAUDE.md 含全部必备章节与摘要行 |
| 245-250 | S2-T2 注意项：规则 5/6 由其他 command 补充；规则 2 摘要按 1a 检测结果选择文本；规则 7 由步骤 8 添加 | 两模式 | step_entry_files | fx-coding-project | it-s4-rule2-text | Coding 项目规则 2 为"遵循 TDD 和代码规范"文本；非 Coding 为"非必要不编写代码"文本 |
| 252-308 | S2-T3 AGENTS.md 基础模板结构（默认角色、与 CLAUDE.md 关系、Agent 执行要求） | 两模式 | step_entry_files | fx-coding-project | it-s4-entry-template-agents | 新建 AGENTS.md 含默认角色（Coding=谨慎执行者）等必备章节 |

### 2.10 处理流程 S3~S5

| SKILL 行号区间 | 条款摘要 | 适用模式 | 脚本函数或 references 条目 | fixture | 测试 ID | 关键断言 |
|----------------|----------|----------|----------------------------|---------|---------|----------|
| 310-333 | S3-01 前端项目包管理器 pnpm、Python 项目 uv；检测后写入 CLAUDE.md 项目配置 | 两模式 | detect_project / step_entry_files | fx-techstack-frontend / fx-techstack-python | it-s1-pkg-manager | 含 `package.json` 项目写入 pnpm 规则；含 `requirements.txt`/`pyproject.toml` 项目写入 uv 规则；禁用项文本保留 |
| 319-325 | S3-02 禁止使用 npm（前端）、pip（Python）、yarn（前端） | 两模式 | step_entry_files | fx-techstack-frontend | it-s1-pkg-manager-forbidden | 写入文本含三条禁止项 |
| 335-347 | S4-01 技术栈检测五类：语言、test/lint/format 脚本、覆盖率阈值默认 80% | 两模式 | detect_project | fx-techstack-frontend | ut-detect_project-techstack | 从 `package.json` scripts 提取 test/lint/format；覆盖率默认 80% |
| 358-362 | S4-02 技术栈区块缺失时追加完整区块；已有区块按字段逐项处理，仅替换 `待确认`/`未检测到`/空字符串占位，真实用户值保留并将差异写入 report | 两模式 | `_ensure_techstack_block` / step_entry_files | fx-techstack-frontend | TestTechstackPlaceholder / test_placeholder_replaced_user_value_kept_diff_reported / test_placeholder_replacement_is_idempotent_and_diff_not_duplicated | 占位字段收敛到检测值；非占位真实值不覆盖；`techstack-diff` 含 field/user_value/detected_value；重跑不重复区块或差异 |
| 362 | S4-03 未检测到的命令写"未检测到"，不阻塞初始化；该值作为占位，未来检测到真实值时可逐项替换 | 两模式 | step_entry_files / `_ensure_techstack_block` | fx-techstack-python | TestTechstackPlaceholder / it-s4-techstack-undetected | 缺失命令字段写"未检测到"；后续运行仅替换检测到的占位项；步骤状态成功 |
| 364 | S4-04 用户写入的非占位技术栈真实值保留，若与检测值不同则记录 `techstack-diff` action | 两模式 | step_entry_files / `_ensure_techstack_block` | fx-techstack-frontend | TestTechstackPlaceholder / test_placeholder_replaced_user_value_kept_diff_reported | 用户值不被检测值覆盖；差异进入可 JSON 序列化的 report |
| 368-374 | S4-05 项目技术栈完整区块含覆盖率阈值 80%；区块缺失时一次追加完整区块 | 两模式 | step_entry_files / `_ensure_techstack_block` | fx-techstack-frontend | TestTechstackPlaceholder / it-s4-coverage-80 | 完整区块只出现一次；覆盖率阈值为 80%；重跑幂等 |
| 377-386 | S5-01 创建 `.claude/rules` 与 17 个 `cadence/` 子目录（含 project-rules/examples 与 cache） | 两模式 | step_scaffold | fx-empty-project | it-s5-scaffold-dirs | 17 个子目录全部存在；重复运行幂等 |
| 388-406 | S5-02 目录用途说明表为文档性条款 | 两模式 | references/merge-semantics.md 目录用途节 | —（仓库内文档） | sc-scaffold-dir-doc | 瘦身后 SKILL 或 references 保留目录用途说明 |

### 2.11 处理流程 S6：历史产物迁移（HM-01~03，SKILL 429-433 行表）

| SKILL 行号区间 | 条款摘要 | 适用模式 | 脚本函数或 references 条目 | fixture | 测试 ID | 关键断言 |
|----------------|----------|----------|----------------------------|---------|---------|----------|
| 431 | HM-01 `cadence/<dir>` 不存在→将 `.claude/<dir>` 移动到 `cadence/<dir>` | 普通 | step_scaffold | fx-history-dirs | it-s5-history-hm01-reachable | 移动后源不存在、目标内容一致 |
| 432 | HM-02 `cadence/<dir>` 已存在且为空→内容移入并清理空源目录 | 普通 | step_scaffold | fx-history-target-empty | it-s5-history-merge-empty | 全部条目移入目标；源目录被移除或为空 |
| 433 | HM-03 `cadence/<dir>` 已存在且非空→跳过该目录并报告冲突，要求用户手动处理 | 普通 | step_scaffold | fx-history-target-nonempty | it-s5-history-conflict-skip | 源与目标均不变；报告含冲突目录与手动处理提示 |
| 435-437 | S6-01 禁止迁移 `.claude/rules`、`.claude/commands`、`.claude/skills` | 普通 | step_scaffold | fx-history-forbidden | it-s5-history-forbidden | 三个禁止目录存在时原地不动且不在迁移清单 |
| 441-459 | S6-02 迁移完成报告已迁移/跳过/冲突三类清单 | 普通 | step_scaffold | fx-history-dirs | it-s5-history-report | 报告三类清单齐全 |

### 2.12 处理流程 S7：cadence gitignore

| SKILL 行号区间 | 条款摘要 | 适用模式 | 脚本函数或 references 条目 | fixture | 测试 ID | 关键断言 |
|----------------|----------|----------|----------------------------|---------|---------|----------|
| 466-469 | S7-01 默认不将 `cadence/` 加入 `.gitignore`（分支一） | 两模式 | step_gitignore | fx-empty-project | it-s6-cadence-gitignore-default | `.gitignore` 无 `cadence/` 行；不创建多余内容 |
| 471-479 | S7-02 仅用户明确要求忽略时追加（`--ignore-cadence`），行级幂等（分支二） | 两模式 | step_gitignore | fx-gitignore-existing | it-s6-cadence-gitignore-ignore | 追加 `cadence/` 行与注释；重复运行不重复追加 |

### 2.13 处理流程 S8：代码阅读规则

| SKILL 行号区间 | 条款摘要 | 适用模式 | 脚本函数或 references 条目 | fixture | 测试 ID | 关键断言 |
|----------------|----------|----------|----------------------------|---------|---------|----------|
| 485-491 | S8-01 从模板根复制 `code-reading.md` 并在双入口添加摘要 | 两模式 | step_rules_files / step_entry_files | fx-empty-project | it-s3-code-reading-add | 规则文件与双入口摘要均存在 |
| 493-497 | S8-02 无交互：所有项目创建规则并补齐摘要，避免 L0 悬空引用；非 Coding 仅跳过 CodeGraph 初始化 | 两模式 | step_rules_files / step_entry_files | fx-noncoding-project | it-s3-code-reading-no-dangling | 摘要引用与规则文件成对存在 |
| 497 | S8-03 已存在规则文件不覆盖；缺摘要只追加摘要 | 两模式 | step_rules_files / step_entry_files | fx-existing-rules | it-s3-code-reading-no-overwrite | 已有规则文件 sha256 不变；缺失摘要被追加 |

### 2.14 处理流程 S9：CodeGraph（CS-01~08，SKILL 558-567 行表）

| SKILL 行号区间 | 条款摘要 | 适用模式 | 脚本函数或 references 条目 | fixture | 测试 ID | 关键断言 |
|----------------|----------|----------|----------------------------|---------|---------|----------|
| 501-503 | S9-01 检测条件：Coding 项目默认启用、非 Coding 默认跳过 | 两模式 | step_codegraph | fx-coding-project | it-s8-codegraph-default-coding | Coding 项目执行 install+init 流程 |
| 513-517 | S9-02 用户明确要求时即使未检测到源码也允许执行（`--enable-codegraph`，只控 S8 不改项目类型连带语义） | 两模式 | step_codegraph | fx-noncoding-project | it-s8-codegraph-explicit-enable | 非 Coding + `--enable-codegraph` 执行 S8；规则 2 文本与默认角色仍按非 Coding |
| 519-539 | S9-03 安装后强制核验 `.mcp.json` 与 `.codex/config.toml` 双配置，缺一按参照补齐 | 两模式 | step_codegraph | fx-mcp-partial | it-s8-codegraph-reverify | install 成功后仍逐文件核验并补齐缺失方 |
| 550-554 | S9-04 配置范围：`--location=local` 只写项目级；`.codegraph/` 入 gitignore；`codegraph.json` 不入 gitignore | 两模式 | step_codegraph / step_gitignore | fx-empty-project | it-s8-codegraph-scope | 不写全局配置；gitignore 含 `.codegraph/` 不含 `codegraph.json` |
| 560 | CS-01 `.codegraph/` 不存在→Coding 默认执行 install 与 init | 两模式 | step_codegraph | fx-coding-project | it-s8-codegraph-fresh | `.codegraph/` 生成；两配置文件含 CodeGraph MCP |
| 561 | CS-02 `.codegraph/` 已存在→运行 `codegraph status` 报告已初始化，不重复 init | 两模式 | step_codegraph | fx-codegraph-existing | it-s8-codegraph-existing | init 未再次执行（调用计数=0）；status 结果入报告 |
| 562 | CS-03 `.mcp.json` 与 `.codex/config.toml` 均已有 CodeGraph MCP→跳过不重复写入 | 两模式 | step_codegraph | fx-mcp-complete | it-s8-codegraph-both-present | 两配置文件 sha256 不变 |
| 563 | CS-04 `.mcp.json` 有、`.codex/config.toml` 缺 `[mcp_servers.codegraph]`→参照 `.mcp.json` 手动补齐 toml | 两模式 | step_codegraph | fx-mcp-toml-missing | it-s8-codegraph-toml-missing | toml 增加 `[mcp_servers.codegraph]` 块且其余内容不变 |
| 564 | CS-05 `.mcp.json` 缺 CodeGraph MCP→按 mcp-configuration 兜底配置补齐 `.mcp.json`，再同步补齐 toml | 两模式 | step_codegraph | fx-mcp-missing | it-s8-codegraph-mcp-missing | 两配置文件均含 CodeGraph MCP 兜底配置 |
| 565 | CS-06 Claude/Codex 缺 CodeGraph MCP server→执行 install 后必须再次核验两个配置文件 | 两模式 | step_codegraph | fx-mcp-partial | it-s8-codegraph-install-reverify | install 调用后发生二次核验且仅补齐仍缺失方 |
| 566 | CS-07 `codegraph install` 失败→提供兜底配置并分别补齐两文件（design D3：步骤标记 degraded 并继续；补写/备份/原子写失败仍终止） | 两模式 | step_codegraph | fx-codegraph-install-fail | it-s8-codegraph-install-fail / it-s8-codegraph-binary-missing / ut-step_s8-binary-missing-degraded（二进制缺失同降级路径，终审 C-2） | 步骤状态 degraded；两配置文件由脚本补齐；整体不因此失败 |
| 567 | CS-08 `codegraph init` 失败→报告语言/目录规模/`codegraph.json` 提示，不阻塞其他初始化项 | 两模式 | step_codegraph | fx-codegraph-init-fail | it-s8-codegraph-init-fail | 步骤 degraded；后续步骤照常；报告含人工配置建议 |
| 569-575 | S9-05 `.gitignore` 增量追加 `.codegraph/`，行级幂等 | 两模式 | step_gitignore | fx-gitignore-existing | it-s6-gitignore-codegraph-idempotent | 重复运行不重复追加 |
| 577-580 | S9-06 重复运行只补缺失项、不覆盖已有配置；执行前内部计算清单、执行后报告展示 | 两模式 | step_codegraph | fx-codegraph-existing | it-s8-codegraph-incremental-report | 报告含本次新增/更新清单；已有配置不变 |

### 2.15 处理流程 S10：Playwright

| SKILL 行号区间 | 条款摘要 | 适用模式 | 脚本函数或 references 条目 | fixture | 测试 ID | 关键断言 |
|----------------|----------|----------|----------------------------|---------|---------|----------|
| 584-598 | S10-01 检测条件：用户明确要求浏览器自动化（`--enable-playwright`）时创建规则文件并加摘要 | 两模式 | step_rules_files / step_entry_files | fx-empty-project | it-s3-playwright-enable | 启用后规则文件与双入口摘要存在 |
| 596-600 | S10-02 默认跳过：不创建规则、不加摘要（分支一） | 两模式 | step_rules_files | fx-empty-project | it-s3-playwright-skip | 无 `playwright.md`、无摘要；报告记默认跳过 |
| 600 | S10-03 启用时已存在规则文件不覆盖、缺摘要只追加 | 两模式 | step_rules_files / step_entry_files | fx-existing-rules | it-s3-playwright-no-overwrite | 已有 `playwright.md` sha256 不变 |

### 2.16 增量运行：规则文件处理（RF-01~05，SKILL 610-615 行表）

| SKILL 行号区间 | 条款摘要 | 适用模式 | 脚本函数或 references 条目 | fixture | 测试 ID | 关键断言 |
|----------------|----------|----------|----------------------------|---------|---------|----------|
| 612 | RF-01 非框架资产文件不存在→从模板根路径读取并创建；框架资产创建后续由 RF-05 统一治理 | 两模式 | step_rules_files | fx-empty-project | it-s3-rules-create | 缺失文件按所选模板创建 |
| 613 | RF-02 非框架资产内容与模板一致→幂等跳过；框架资产一致状态归 RF-05 `unchanged` | 两模式 | step_rules_files | fx-existing-rules | ut-s3-authoritative-idempotent / ut-step_s3-ordinary-unchanged | 内容一致时不调用 `atomic_write`、不新增 `cadence/legacy` 归档，报告 unchanged/跳过 |
| 613 | RF-02b 非框架历史条款；框架资产改用 RF-05。普通模式 drift 询问 keep/replace，无响应 keep；no-interrupt 不再章节合并 | 普通/no-interrupt | step_rules_files | fx-existing-rules | 已由 RF-05 `authoritative-overwrite` 取代旧 no-interrupt `markdown-merge` 映射 | 框架受管规则文件不得调用 `merge_markdown`，不得生成项目补充 |
| 614 | RF-03 `code-reading.md` 老项目补齐后即进入 RF-05 受管清单；非 Coding 仅跳过 CodeGraph 初始化 | 两模式 | step_rules_files | fx-existing-rules | it-s3-code-reading-backfill / ut-s3-authoritative-idempotent | 缺失时补齐模板；后续一致则幂等跳过，drift 则 RF-05 权威覆盖 |
| 615 | RF-04 缺 CodeGraph 段落视为框架规则 drift：普通模式询问 keep/replace；no-interrupt 见 RF-05 权威覆盖 | 两模式 | step_rules_files / backup_file / atomic_write | fx-rules-missing-codegraph-section | ut-s3-codegraph-section-unified-drift / ut-s3-codegraph-section-unified-merge（旧名称保留，旧 `markdown-merge` 语义已由 `authoritative-overwrite` 取代） | 普通模式产出统一 drift 冲突；no-interrupt 结果逐字等于完整模板，不保留项目补充 |
| 615+ | RF-05 `.claude/rules/` 下 7 个框架受管规则文件存在且内容≠所选模板→普通模式询问 keep/replace，replace 时全局屏障归档+`atomic_write`；no-interrupt 屏障归档+`atomic_write` 模板；内容一致则 `unchanged` | 两模式 | step_rules_files / backup_file / atomic_write | fx-existing-rules | ut-s3-authoritative-overwrite / ut-s3-authoritative-idempotent | drift 覆盖后内容==模板，且无“项目补充”/“原项目补充”；归档存在；一致时零写入零归档；报告 `authoritative-overwrite`/`unchanged` |

### 2.17 增量运行：OpenSpec 配置（OS-N1~N13 编号条款 + OS-01~08，SKILL 664-673 行表）

| SKILL 行号区间 | 条款摘要 | 适用模式 | 脚本函数或 references 条目 | fixture | 测试 ID | 关键断言 |
|----------------|----------|----------|----------------------------|---------|---------|----------|
| 633 | OS-N1 候选在同文件系统临时工作区构建；此阶段不得直接创建/覆盖/修改目标；目标存在时以原配置为候选基础，禁止模板整体覆盖 | 两模式 | step_openspec_config | fx-openspec-existing | it-s7-candidate-isolation | dry-run/候选阶段目标文件 sha256 不变；候选以原配置为基础 |
| 634 | OS-N2 结构预检：根为映射；schema 缺失或可保留标量；context 缺失或字符串；rules 缺失或映射；四个 artifact 缺失或字符串数组；自定义键与 artifact 规则原样保留 | 两模式 | precheck_openspec_structure | fx-openspec-type-matrix | ut-precheck_openspec_structure-type-matrix | 全类型矩阵逐类通过/拒绝判定正确（design D6 YAML 全类型矩阵） |
| 635 | OS-N3 结构/类型不兼容→普通保留并报告字段路径/实际类型/冲突；no-interrupt 先备份，无法证明无损规范化则终止且原文件不变 | 两模式 | precheck_openspec_structure / backup_file | fx-openspec-incompatible | it-s7-openspec-yaml-type-conflict-backed-up-preserved | 报告含字段路径与实际类型；原文件 sha256 不变 |
| 636 | OS-N4 候选处理不取消既有备份要求；必要备份失败时终止、候选不发布、原文件不变 | 两模式 | backup_file | fx-readonly-parent | it-s7-openspec-backup-fail-modes | 非零退出；目标不变；无半成品候选残留 |
| 637 | OS-N5 预检通过后保留已有 schema；未设置时写入 `spec-driven` | 两模式 | merge_yaml | fx-openspec-no-schema | ut-merge_yaml-schema-default | 已有 schema 保留；缺失时写入 `spec-driven` |
| 638 | OS-N6 模板四行 Cadence 协作 context 按完整行去重追加，保留原顺序与项目上下文 | 两模式 | merge_yaml | fx-openspec-existing | ut-merge_yaml-context-append | 追加按完整行去重；原顺序与项目技术栈等内容保留 |
| 639 | OS-N7 四个 artifact 数组按完整字符串去重追加模板规则，保留项目额外规则与原顺序 | 两模式 | merge_yaml | fx-openspec-existing | ut-merge_yaml-rules-append | 数组合并去重且顺序稳定；额外规则保留 |
| 640 | OS-N8 禁止创建 `rules.apply`；已有 `rules.apply`：普通须确认（无响应保留并报告；确认移除先备份）；no-interrupt 先备份成功后才在候选中移除 | 两模式 | merge_yaml / backup_file | fx-openspec-apply-key | it-s7-openspec-apply-backed-up-removed / it-s7-openspec-normal-preserved | no-interrupt 备份后候选无 `rules.apply`；普通 `keep` 决策保留并报告；任何分支不虚构 apply artifact |
| 641 | OS-N9 YAML 无法可靠解析不得静默重写：普通保留并报告；no-interrupt 先备份，仍无法无损构建候选则终止 | 两模式 | merge_yaml / backup_file | fx-openspec-unparseable | it-s7-openspec-invalid-yaml-backed-up-preserved | 原文件不变；备份存在；报告解析冲突 |
| 642-657 | OS-N10 固定临时 Change `cadence-rule-config-validation` + 四类 `openspec instructions ... --json` 验证——**已废止，由结构预检取代**（design D4 已删除临时 Change 与四类 instructions 验证；现行语义以 OS-N2 结构预检为准：根映射/schema/context/rules/四 artifact 数组）。保留行 ID 仅用于对账，脚本 MUST NOT 创建临时 Change 或调用 `openspec instructions` | 两模式 | step_openspec_config / precheck_openspec_structure | —（已废止，无对应测试） | 已废止：脚本不创建临时 Change、不调 `openspec instructions`；以结构预检取代（根映射/schema 标量/context 字符串/rules 映射/四 artifact 字符串数组） |
| 658 | OS-N11 全部验证通过后才允许同文件系统原子替换发布；目标原本不存在也以原子创建发布，不得半成品 | 两模式 | atomic_write | fx-empty-project | ut-atomic_write-publish / it-s7-openspec-create | 发布经 `os.replace()`；中途失败无半成品目标 |
| 659 | OS-N12 任一候选验证失败立即终止；报告失败字段路径、实际类型与错误（已废止 instructions 语义，由结构预检取代）；报告候选清理/保留结果；原文件不变；目标原本不存在时不得创建 | 两模式 | step_openspec_config / precheck_openspec_structure | fx-openspec-incompatible | `ut-s7-publish-or-abort-precheck-fail`（单测直接注入非法候选覆盖 `_s7_publish_or_abort` 候选 precheck fail-closed 分支）；集成侧 OS-03 结构冲突覆盖同代码路径 `it-s7-openspec-yaml-type-conflict-backed-up-preserved` | 单测：候选 precheck 失败→raise PublishError、原文件不变、动作日志含失败字段路径；集成：报告含结构预检失败字段路径与实际类型，无目标文件残留 |
| 660 | OS-N13 原子替换/创建失败立即终止并保持或恢复原文件；不得声称成功 | 两模式 | atomic_write | fx-readonly-target | ut-atomic_write-fail / it-s7-openspec-publish-failure-preserved | 非零退出；原文件保持/恢复；报告不声称成功 |
| 662 | OS-B1 复制归档到 `cadence/legacy/<时间戳[-N]>/openspec/config.yaml`；同秒冲突后缀位于时间戳目录；所有需归档分支写入前完成归档，失败不得部分合并/删除键 | 两模式 | backup_file | fx-openspec-existing | ut-backup_file-legacy-copy / ut-backup_file-openspec-naming / ut-backup_file-unique-suffix | 归档路径保留 `openspec/config.yaml` 相对结构；原配置仍在；失败时零合并动作 |
| 675 | OS-B2 完成报告逐项清单（新增 context 行、分组规则、无效键、备份路径、冲突字段、候选结构预检结果、发布结果）；无新增也明确报告幂等跳过（instructions 验证已废止，见 OS-N10；不再报告四类 instructions 命令结果或失败 artifact） | 两模式 | step_openspec_config | fx-openspec-existing | it-s7-openspec-report-fields | 报告字段逐项齐全且不含 instructions 命令结果；幂等运行报告"幂等跳过" |
| 666 | OS-01 配置不存在→从模板构建候选，验证通过后原子创建（两模式同动作） | 两模式 | step_openspec_config / atomic_write | fx-empty-project | it-s7-openspec-create | 原子创建成功；内容与模板基础一致 |
| 667 | OS-02 配置可解析且无 `rules.apply`→候选中保守合并，完整行/字符串去重（两模式同动作） | 两模式 | merge_yaml | fx-openspec-existing | it-s7-openspec-merge-idempotent | 合并去重结果与单测基准一致 |
| 668 | OS-03 目标字段结构/类型不兼容→普通保留并报告不发布；no-interrupt 先备份，无法无损规范化则终止且原文件不变 | 两模式 | precheck_openspec_structure | fx-openspec-incompatible | it-s7-openspec-yaml-type-conflict-backed-up-preserved（no-interrupt 分支；普通分支仅单测覆盖 `test_structure_conflict_normal_preserved`） | 两模式分支动作与报告字段符合表义 |
| 669 | OS-04 存在 `rules.apply`→普通询问（无响应保留并报告；确认并备份后候选中移除）；no-interrupt 备份成功后移除并继续合并 | 两模式 | merge_yaml / backup_file | fx-openspec-apply-key | it-s7-openspec-apply-backed-up-removed / it-s7-openspec-normal-preserved | 普通 `remove_apply`/`keep` 决策生效；no-interrupt 备份后移除且合并继续 |
| 670 | OS-05 YAML 无法可靠解析→普通保留并报告；no-interrupt 先备份，仍无法无损合并则终止不改原文件 | 两模式 | merge_yaml | fx-openspec-unparseable | it-s7-openspec-invalid-yaml-backed-up-preserved（no-interrupt 分支；普通分支与 OS-03 同代码路径，仅单测覆盖） | 两模式原文件均不变；no-interrupt 有备份 |
| 671 | OS-06 任一候选 instructions 验证失败——**已废止，由结构预检取代**（design D4 已删除临时 Change 与四类 instructions 验证）。现行语义：结构预检失败→两模式均终止并报告失败字段路径、实际类型与错误；原文件不变 | 两模式 | step_openspec_config / precheck_openspec_structure | fx-openspec-incompatible | 已废止（design D4 已删除 instructions 验证；结构预检失败分支与 OS-N12 同代码路径，见 `ut-s7-publish-or-abort-precheck-fail`） | 结构预检失败→非零退出；报告含失败字段路径与实际类型（不含 `--change cadence-rule-config-validation --json` 实际命令，该语义已废止）；原文件不变 |
| 672 | OS-07 原子发布失败→两模式均终止并保持或恢复原文件，不得声称成功 | 两模式 | atomic_write | fx-readonly-target | it-s7-openspec-publish-failure-preserved | 原文件 sha256 不变或恢复；报告非成功 |
| 673 | OS-08 任一必要备份失败→两模式均终止且不改原文件 | 两模式 | backup_file | fx-readonly-parent | it-s7-openspec-backup-fail-modes | 原文件不变；非零退出 |

### 2.18 增量运行：L1 协作规则（L1-01~07，SKILL 679-687 行表）

| SKILL 行号区间 | 条款摘要 | 适用模式 | 脚本函数或 references 条目 | fixture | 测试 ID | 关键断言 |
|----------------|----------|----------|----------------------------|---------|---------|----------|
| 681 | L1-01 文件不存在→创建 v1（两模式同动作） | 两模式 | step_rules_files | fx-empty-project | it-s3-l1-create | 创建内容与框架 v1 规范源逐字一致 |
| 682 | L1-02 完整内容与当前框架 v1 一致→跳过（两模式同动作） | 两模式 | classify_l1 / sha256_file | fx-l1-current | ut-classify_l1-current / it-s3-l1-idempotent | 判定 current；文件不变；报告跳过 |
| 683 | L1-03 版本标记受支持且完整内容与对应旧版规范逐字一致→备份后升级（两模式同动作） | 两模式 | classify_l1 / backup_file | fx-l1-old-version | ut-classify_l1-old-version / it-s3-l1-upgrade（仅单测覆盖：仓库仅 v1 规范源，upgrade 分支无法集成复现，待补） | 判定 old-version；备份存在；内容升级为 v1 |
| 684 | L1-04 仅旧版标记匹配但内容与旧版规范不同→归入"与任何已知框架版本不匹配"：普通询问（无响应则默认 keep 保留并报告 status=0，A 类 §11.6）；no-interrupt 备份后以 v1 替换并报告 | 两模式 | classify_l1 / backup_file（标 `default_keep: true`） | fx-l1-old-marker-drift | ut-classify_l1-old-marker-drift / it-s3-l1-old-marker-drift（仅单测覆盖：同 L1-03，待补） | 判定 mismatch 而非 old-version；普通无响应保留并报告 status=0；两模式分支动作符合表义 |
| 685 | L1-05 当前 v1 标记存在但完整内容不同→同归入"不匹配"，分支同 L1-04（无响应则默认 keep 保留并报告 status=0，A 类 §11.6） | 两模式 | classify_l1 | fx-l1-v1-marker-drift | ut-classify_l1-v1-marker-drift / it-l1-drift-replace | 判定 mismatch；不得仅凭标记当作 current 跳过 |
| 686 | L1-06 文件无标记或与已知版本不匹配→普通询问（无响应则默认 keep 保留并报告 status=0，A 类 §11.6）；no-interrupt 备份后以 v1 替换并报告 | 两模式 | classify_l1 / backup_file（标 `default_keep: true`） | fx-l1-unmarked | ut-classify_l1-unmarked / it-l1-unknown-replace | 判定 unmarked；普通无响应保留并报告 status=0；两模式分支动作符合表义 |
| 687 | L1-07 任何需要 L1 备份的分支备份失败→终止且不得替换原文件（两模式同动作） | 两模式 | backup_file | fx-readonly-parent | it-s3-l1-backup-failure-preserved | 原文件 sha256 不变；非零退出 |
| 689 | L1-B1 复制归档到 `cadence/legacy/<时间戳[-N]>/.claude/rules/openspec-superpowers-workflow.md`；原位文件不动，同秒冲突后缀位于时间戳目录 | 两模式 | backup_file | fx-l1-old-version | ut-backup_file-legacy-copy / ut-backup_file-l1-naming / ut-backup_file-unique-suffix | 归档路径保留 `.claude/rules/` 相对结构；原 L1 文件仍在，覆盖仅由后续 `atomic_write` 完成 |
| 689 | L1-B2 标记只用于候选版本定位；最终识别必须比较完整文件内容；不得仅凭标记识别版本；不得把无标记文件当已知框架版本覆盖 | 两模式 | classify_l1 / sha256_file | fx-l1-v1-marker-drift | ut-classify_l1-full-compare | 分类依据为完整内容比较而非标记 |

### 2.19 增量运行：L0 入口（L0-01~07，SKILL 697-705 行表）

| SKILL 行号区间 | 条款摘要 | 适用模式 | 脚本函数或 references 条目 | fixture | 测试 ID | 关键断言 |
|----------------|----------|----------|----------------------------|---------|---------|----------|
| 691-694 | L0-B1 写入前统一预检 + 全部必要 `cadence/legacy` 复制归档屏障；任一归档失败双入口均不得写入；归档完成后各入口仅以 `atomic_write` 发布 | 两模式 | step_entry_files / backup_file / atomic_write | fx-readonly-parent | test_l0_second_archive_failure_keeps_both / test_atomic_write_failure_keeps_original | 第二个归档失败时双入口仍为原内容；原子写失败时失败入口原文件不变 |
| 699 | L0-01 入口不存在→创建基础入口并插入当前 v1（两模式同动作） | 两模式 | l0_block / step_entry_files | fx-empty-project | it-entry-base-created | 基础入口文本与 L0 v1 均存在，位置正确 |
| 700 | L0-02 当前 v1 区块与规范源完整一致→跳过不重复写入（两模式同动作） | 两模式 | l0_block / sha256_file | fx-entry-idempotent | it-s4-idempotent | 双入口 sha256 不变 |
| 701 | L0-03 当前 v1 标记成对但区块不同→视为无法识别的本地修改：普通询问（无响应则默认 keep 保留并报告 status=0，A 类 §11.6）；no-interrupt 先备份成功后替换并报告 | 两模式 | l0_block / backup_file（标 `default_keep: true`） | fx-l0-drift | it-s4-drift-normal / it-l0-drift-normal-keep-default / it-s4-drift-replaced-outside-preserved | 普通无响应保留并报告 status=0；no-interrupt 备份后替换；区块外内容保留 |
| 702 | L0-04 受支持旧版本标记成对→备份成功后升级到当前 v1 并报告（两模式同动作） | 两模式 | l0_block / backup_file | fx-l0-old-version | it-s4-upgrade / ut-compute_plan-l0-upgrade-deterministic | 备份存在；区块=当前 v1 |
| 703 | L0-05 无 L0 标记→插入当前 v1，入口原内容保留（两模式同动作） | 两模式 | l0_block | fx-entry-no-markers | it-s4-insert / ut-compute_plan-l0-insert-deterministic / ut-step_s4-insert-normal-executes | 插入位置正确；原内容 sha256 不变 |
| 704 | L0-06 单侧标记或顺序错误→普通询问（无响应则默认 keep 保留并报告 status=0，A 类 §11.6）；no-interrupt 先备份成功后写入单一当前 v1 区块并报告 | 两模式 | l0_block（标 `default_keep: true`） | fx-l0-broken-markers | it-s4-broken-markers-preserve-arbitrary | 处理后标记成对且唯一；区块外内容保留 |
| 705 | L0-07 任何 L0 复制归档失败→终止本次 L0 更新，双入口均不得写入（两模式同动作） | 两模式 | backup_file | fx-readonly-parent | test_l0_second_archive_failure_keeps_both | 双入口原位内容保持不变；非零退出；已成功创建的归档保留 |
| 707 | L0-B2 所有场景必须保持 L0 受管区块外内容原样 | 两模式 | l0_block / sha256_file | fx-l0-drift | it-s4-outside-preserved | 区块外 sha256 处理前后一致 |

### 2.20 增量运行：摘要引用（SM-01~03，SKILL 713-717 行表）

| SKILL 行号区间 | 条款摘要 | 适用模式 | 脚本函数或 references 条目 | fixture | 测试 ID | 关键断言 |
|----------------|----------|----------|----------------------------|---------|---------|----------|
| 715 | SM-01 规则文件名引用已存在且唯一→跳过不重复写入 | 两模式 | `_ensure_summary_lines` / step_entry_files | fx-entry-idempotent | TestSummaryDedup / it-s4-idempotent | 以规则文件名引用存在性判定，不要求整行措辞精确一致 |
| 716 | SM-02 按规则文件名引用存在性判缺失；同一规则文件名多引用时去重并保留首个；规则 6 多行块按首行 marker 判存在 | 两模式 | `_ensure_summary_lines` / step_entry_files | fx-entry-missing-summary | TestSummaryDedup / test_different_wording_same_ref_not_duplicated / test_duplicate_ref_deduped / ut-ensure_summary-missing-rule2-rule6 | 自定义措辞但引用同文件时不追加标准行；重复引用仅保留首个；真正缺失的引用与规则 6 块被补齐 |
| 717 | SM-03 规则编号与现有内容冲突→不覆盖原内容，按规则文件名补齐缺失引用并报告可能需人工整理编号 | 两模式 | step_entry_files | fx-summary-number-conflict | it-entry-summary-number-conflict / TestSummaryDedup | 原编号行保留；同文件引用不重复；缺失摘要追加 |

### 2.21 增量运行：可选规则（OP-01~04，SKILL 723-728 行表）

| SKILL 行号区间 | 条款摘要 | 适用模式 | 脚本函数或 references 条目 | fixture | 测试 ID | 关键断言 |
|----------------|----------|----------|----------------------------|---------|---------|----------|
| 725 | OP-01 规则文件和摘要均已存在→视为已启用，仅检查完整性 | 两模式 | step_rules_files / step_entry_files | fx-existing-rules | it-s3-optional-complete（待补） | 文件与摘要不重写；报告完整性结果 |
| 726 | OP-02 代码阅读规则缺失→所有项目默认新增；非 Coding 仅跳过 CodeGraph 初始化 | 两模式 | step_rules_files | fx-noncoding-project | it-s3-code-reading-backfill | 规则文件补齐；CodeGraph 不初始化 |
| 727 | OP-03 Playwright 规则缺失→默认跳过，用户明确要求时新增 | 两模式 | step_rules_files | fx-empty-project | it-s3-playwright-skip / it-s3-playwright-enable | 两分支动作符合表义 |
| 728 | OP-04 无法判断历史选择→按默认值处理，不询问 | 两模式 | step_rules_files | fx-existing-rules | it-s3-playwright-skip（默认跳过不询问分支） | 不生成提问冲突项；按默认值执行并报告 |

### 2.22 增量运行：CodeGraph（CG-01~08，SKILL 734-743 行表）

| SKILL 行号区间 | 条款摘要 | 适用模式 | 脚本函数或 references 条目 | fixture | 测试 ID | 关键断言 |
|----------------|----------|----------|----------------------------|---------|---------|----------|
| 736 | CG-01 老项目已跑过 rule-config 但缺 CodeGraph→只补 CodeGraph 相关规则、摘要、MCP 配置、`.codegraph/` 与 `.gitignore` | 两模式 | step_codegraph / step_rules_files | fx-legacy-no-codegraph | it-s8-codegraph-backfill | 仅 CodeGraph 相关项新增；其余文件 sha256 不变 |
| 737 | CG-02 `.codegraph/` 已存在→运行 status 并跳过初始化 | 两模式 | step_codegraph | fx-codegraph-existing | it-s8-codegraph-existing | 不重复 init；status 入报告 |
| 738 | CG-03 `.codegraph/` 不存在→Coding 默认执行 init | 两模式 | step_codegraph | fx-coding-project | it-s8-codegraph-fresh | init 执行且 `.codegraph/` 生成 |
| 739 | CG-04 双配置均已有 CodeGraph MCP→跳过不重复写入 | 两模式 | step_codegraph | fx-mcp-complete | it-s8-codegraph-both-present | 两配置文件 sha256 不变 |
| 740 | CG-05 `.mcp.json` 有、toml 缺→参照 `.mcp.json` 补齐 Codex 本地 MCP | 两模式 | step_codegraph | fx-mcp-toml-missing | it-s8-codegraph-toml-missing | toml 补齐且其余内容不变 |
| 741 | CG-06 任一配置缺 CodeGraph MCP→先 install 再核验并补齐缺失文件 | 两模式 | step_codegraph | fx-mcp-partial | it-s8-codegraph-install-reverify | install 后二次核验；只补缺失方 |
| 742 | CG-07 `.gitignore` 已有 `.codegraph/`→跳过 | 两模式 | step_gitignore | fx-gitignore-existing | it-s6-gitignore-codegraph-idempotent | 不重复追加 |
| 743 | CG-08 `codegraph.json` 存在→保留，不加入 `.gitignore` | 两模式 | step_gitignore | fx-codegraph-json | it-s6-codegraph-json-keep | `codegraph.json` 保留且 gitignore 不含其条目 |

### 2.23 建议与核心原则

| SKILL 行号区间 | 条款摘要 | 适用模式 | 脚本函数或 references 条目 | fixture | 测试 ID | 关键断言 |
|----------------|----------|----------|----------------------------|---------|---------|----------|
| 745-748 | AD-01 重跑补齐新增规则；运行前内部计算新增/更新清单，运行后输出已新增/已跳过/需人工处理 | 两模式 | step_* 全流水线 | fx-existing-rules | it-apply-plan-report | dry-run 计划与 apply 报告均含三类清单 |
| 750-758 | CP-01~07 核心原则七条（规则分离/摘要引用/契约行为分层/常驻路由按需正文/失败关闭/目录明确/无交互默认） | 两模式 | references/merge-semantics.md 核心原则节 | —（仓库内文档） | sc-core-principles | 瘦身后 SKILL 或 references 保留七条原则语义 |

### 2.24 横切契约（design D3/D6，非 SKILL 原文但为映射表必须锁定的新增执行语义）

| SKILL 行号区间 | 条款摘要 | 适用模式 | 脚本函数或 references 条目 | fixture | 测试 ID | 关键断言 |
|----------------|----------|----------|----------------------------|---------|---------|----------|
| —（D3） | XC-01 dry-run 零写入：只输出计划（动作、冲突、备份需求），`--report`/`--decisions` 路径必须位于项目根之外 | 两模式 | step_* 全流水线 | fx-existing-rules | it-dryrun-zero-write | dry-run 前后项目目录全量 sha256 快照一致；项目根内报告/决策路径被拒绝 |
| —（D3） | XC-02 用户意图四参数透传：`--project-type` / `--ignore-cadence` / `--enable-playwright` / `--enable-codegraph` | 两模式 | —（CLI 入口） | fx-empty-project | it-intent-params | 四参数各自独立生效且组合不互相污染；报告记录参数来源 |
| —（D3） | XC-03 decisions 异常：文件缺失或无法解析 / 含未知或重复 `conflict_id` / 冲突缺少决策 / 决策与新鲜计划不符，任一即非零退出且零写入；计划无冲突时不要求决策文件 | 普通 | —（apply 入口决策校验） | fx-decisions-no-conflict / fx-decisions-unknown / fx-decisions-stale | it-decisions-no-conflict-not-required / it-decisions-unknown / it-decisions-stale / ut-compute_plan-recommendation-keep（recommendation 一律保守 keep，终审 C-1） | 异常各自非零退出、报告含原因、项目目录零写入；计划无冲突时不要求决策文件。codex 五轮：s1:project-type-conflict 已删除（项目类型判定重构），当前系统无 B 类冲突；原 it-decisions-missing/lacking 依赖唯一 B 类验证「决策缺失/空缺」fail-closed，现改为 it-decisions-no-conflict-not-required 验证「无冲突时不要求决策」 |
| —（D3） | XC-04 no-interrupt 不读取也不要求决策文件，全部冲突内部按权威规则决策并记录 | no-interrupt | merge_markdown / merge_yaml | fx-existing-rules | it-entry-base-created（任一 no-interrupt 无 `--decisions` 成功用例） | 提供决策文件被忽略；冲突按 NC/OS/L1/L0 表内部决策并入报告 |
| —（P1-1） | P1-1 no-interrupt dry-run 的框架受管规则 drift 冲突在 s3 级、plan 级与对外顶层报告新增 `no_interrupt_action: "authoritative-overwrite"`；普通模式不写该键 | 两模式 | compute_plan / _sync_plan_to_report / run_dry_run | fx-existing-rules | test_dry_run_no_interrupt_action_field / ut-compute-plan-no-interrupt-action / ut-compute-plan-normal-no-action-field / ut-report-no-interrupt-action / ut-report-normal-no-action-field | no-interrupt 内部两级及对外报告字段均为 `authoritative-overwrite`，`recommendation=keep` 不变；普通模式条目不含该键；旧 `markdown-merge` 字段映射已由 authoritative-overwrite 取代 |
| —（D6） | XC-05 预算计时：空项目 `apply --no-interrupt` 报告 `budget_seconds_excluding_codegraph < 60` | no-interrupt | —（报告计时字段） | fx-empty-project | it-budget | 报告计时字段存在且 < 60；S8 耗时单独列出 |
| —（D1） | XC-06 PyYAML 缺失以退出码 77 退出且报告照常写出 | 两模式 | merge_yaml | fx-no-pyyaml | ut-merge_yaml-missing-dependency | 退出码恰为 77；stderr 说明；报告含 hints |
| —（D3） | XC-07 横切原子写 `os.replace()` 与 sha256 工具 | 两模式 | atomic_write / sha256_file | fx-empty-project | ut-atomic_write-replace / ut-sha256_file-basic | 写入经原子替换；sha256 结果与系统工具一致（含 sha256sum/shasum 回退环境） |

## 3. 自审覆盖度（Step 3）

### 3.1 十张表行数对账（design D2 基线）

| 表 | SKILL 行号区间 | 基线行数 | 本映射覆盖行 ID | 对账 |
|----|----------------|----------|------------------|------|
| no-interrupt 权威合并 | 39-48（数据行 41-48） | 8 | NC-01~08 → 2.3 | ✅ 一一对应 |
| OpenSpec 配置处理 | 664-673（数据行 666-673） | 8 | OS-01~08 → 2.17 | ✅ 一一对应 |
| L1 协作规则增量 | 679-687（数据行 681-687） | 7 | L1-01~07 → 2.18 | ✅ 一一对应 |
| L0 入口增量 | 697-705（数据行 699-705） | 7 | L0-01~07 → 2.19 | ✅ 一一对应 |
| 规则文件处理 | 610-615（数据行 612-615，新增 RF-05 语义行） | 6 | RF-01~05 → 2.16 | ✅ RF-05 对齐框架权威全覆盖 |
| 摘要引用增量 | 713-717（数据行 715-717） | 3 | SM-01~03 → 2.20 | ✅ 一一对应 |
| 可选规则增量 | 723-728（数据行 725-728） | 4 | OP-01~04 → 2.21 | ✅ 一一对应 |
| CodeGraph 已存在状态 | 558-567（数据行 560-567） | 8 | CS-01~08 → 2.14 | ✅ 一一对应 |
| CodeGraph 增量 | 734-743（数据行 736-743） | 8 | CG-01~08 → 2.22 | ✅ 一一对应 |
| 历史目录迁移 | 429-433（数据行 431-433） | 3 | HM-01~03 → 2.11 | ✅ 一一对应 |

合计 62 行，全部映射到测试 ID；Task 7 文档对账以此为准。

### 3.2 缺口清单逐条确认

| # | 缺口项 | 测试 ID | 状态 |
|---|--------|---------|------|
| 1 | 历史目录两模式 | it-s5-history-no-interrupt（NH-02）/ it-s5-history-normal（NH-03） | ✅ |
| 2 | 框架受管规则 drift（普通 keep / replace；no-interrupt 权威全覆盖） | it-s3-normal-keep-decision / it-s3-rules-drift-replace（replace 分支待补）/ ut-s3-authoritative-overwrite / ut-s3-authoritative-idempotent | ✅ authoritative 覆盖与幂等已覆盖；普通 replace 集成待补 |
| 3 | 技术栈占位逐项替换、用户真实值保留、差异入 report | TestTechstackPlaceholder / test_placeholder_replaced_user_value_kept_diff_reported / test_placeholder_replacement_is_idempotent_and_diff_not_duplicated | ✅ |
| 4 | gitignore 两分支 | it-s6-gitignore-default / it-s6-gitignore-ignore（S7-01/02） | ✅ |
| 5 | Playwright 两分支 | it-s3-playwright-skip / it-s3-playwright-enable（S10-01/02、OP-03） | ✅ |
| 6 | CodeGraph 显式启用与增量矩阵 | it-s8-codegraph-explicit-enable（S9-02）；CS-01~08、CG-01~08 全矩阵 → 2.14/2.22 | ✅ |
| 7 | Markdown 不可解析回退 | ut-merge_markdown-unparseable-fallback（NC-08） | ✅ |
| 8 | 摘要引用存在性与同文件多引用去重 | TestSummaryDedup / test_different_wording_same_ref_not_duplicated / test_duplicate_ref_deduped / it-entry-summary-number-conflict | ✅ |
| 9 | 项目类型判定两模式规则（codex 五轮重构，原「检测矛盾」已删） | it-s1-no-interrupt-ignores-cli / it-s1-no-interrupt-detect-coding / it-s1-normal-cli-promotes / it-s1-normal-detect-coding / it-s1-normal-no-cli-noncoding | ✅ |
| 10 | 意图参数透传 | it-intent-params（XC-02，四参数） | ✅ |
| 11 | 裸 token | sc-bare-token（PM-01） | ✅ |
| 12 | disable-model-invocation | sc-disable-model-invocation（FM-01） | ✅ |
| 13 | L1 独立分支 | ut-step_s3-l1-red-line（S1d-03，SKILL 183 行） | ✅ |
| 14 | 基础入口文本 | it-entry-base-created（L0-P5/L0-01，含基础模板全文断言） | ✅ |
| 15 | dry-run 零写入 | it-dryrun-zero-write（XC-01） | ✅ |
| 16 | decisions 异常与无冲突豁免 | it-decisions-no-conflict-not-required / it-decisions-unknown / it-decisions-stale（XC-03） | ✅ |
| 17 | L0 双入口复制归档屏障 + 原子覆盖失败保持原文件 | test_l0_second_archive_failure_keeps_both / test_atomic_write_failure_keeps_original + it-s7-openspec-backup-fail-modes + it-s3-l1-backup-failure-preserved | ✅ |
| 18 | `cadence/legacy` 路径、复制语义、固定 `.gitignore` 与同秒目录后缀 | ut-backup_file-legacy-copy / ut-backup_file-legacy-gitignore / ut-backup_file-unique-suffix | ✅ |
| 19 | code-usage 项目类型单选、固定落地名与模板来源字段 | TestCodeUsageSingleSource | ✅ |
| 20 | no-interrupt dry-run 动作字段 | test_dry_run_no_interrupt_action_field | ✅ `authoritative-overwrite` |

### 3.3 非表条款覆盖声明

- 参数模式、no-interrupt 通用规则、历史目录规则、默认策略表、人工交互策略表、提问规则、检查清单、处理流程 S1~S10 全部命令与表格、OpenSpec 13 条编号条款、建议、核心原则均已在第 2 节逐条登记并给出测试 ID 或 references 条目，无遗漏。
- 纯 Agent 行为约束（提问规则 IA-R、密钥占位符 IA-05、裸 token 解析 PM-01、逐条提问时机）按 design D6 第 3 条纳入静态检查（`sc-`）与人工验收，不伪造自动化断言。
- 与现有 22 个生命周期用例的关系：现有 `verify-managed-lifecycle.sh` 用例（actual-entry-idempotent、l0-drift-*、l0-broken-markers、l0-backup-barrier、l1、apply-normal、yaml-errors、openspec-success、apply-remove、publish-fail 等）按 Task 2 迁移到本表 `it-`/`ut-` 命名；本表新增缺口用例以 §3.2 为准。原 `instructions-fail` 用例已随 design D4 删除（临时 Change 与四类 `openspec instructions` 验证废止，由结构预检取代），对应的 `tests/fixtures/instrumented-openspec.sh` fixture 已删除并标记废止。
- 已知演进点：OS-N10 与 OS-06 的 instructions 验证条款已随 design D4 删除并标记废止（本表对应行现为“已废止”状态，保持行 ID 用于对账可追溯）。
