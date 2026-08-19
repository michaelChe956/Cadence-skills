# rule-config 合并语义权威定义

> 版本：v1.0（2026-07-30）
> 权威来源：现行 `cadence-init/skills/rule-config/SKILL.md`（758 行）与 `cadence-init/skills/rule-config/tests/skill-clause-map.md`（Task 1 行 ID 基线）。
> 用途：`rule-config` 脚本化提速（OpenSpec change `script-rule-config-for-speed`）后，SKILL.md 仅保留路由与触发说明；本文件作为合并语义的**权威定义**，按需加载。脚本实现（Task 4+ 的 `merge_markdown` / `merge_yaml` / `l0_block` / `classify_l1` / `precheck_openspec_structure` / `backup_file` / `atomic_write` / `sha256_file` / `step_*`）与本文件的十张表逐行对账，测试 ID 见 `tests/skill-clause-map.md`。
> 模式取值：`普通`（未携带 `no-interrupt`/`--no-interrupt`）/ `no-interrupt`（携带上述完整 token）/ `两模式`（两种调用均适用）。两模式互斥，no-interrupt 的权威合并与禁迁移规则不得应用于普通模式。

## 0. 八列定义与行 ID 基线

十张表统一采用八列结构，列序固定为：

1. **行 ID** — design D2 基线编号（NC/OS/L1/L0/RF/SM/OP/CS/CG/HM 前缀 + 两位序号）。
2. **资产** — 受本行规则约束的目标对象（文件、目录或配置块）。
3. **冲突状态** — 触发本行的输入状态或冲突条件。
4. **普通模式动作** — 普通模式下对该状态的确定性或交互式动作。
5. **no-interrupt 动作** — no-interrupt 模式下对该状态的确定性动作；无分支差异的行写"同普通模式"。
6. **备份要求** — 写入前是否需要复制归档、归档路径、归档失败处理（见 §11.1）。
7. **报告要求** — 报告中必须出现的字段或清单（见 §11.3）。
8. **对应测试 ID** — `tests/skill-clause-map.md` 中登记的单测/集成/静态 ID，多个以 `/` 分隔。

行 ID 合计：NC-01~08（8）+ OS-01~08（8）+ L1-01~07（7）+ L0-01~07（7）+ RF-01~05（6）+ SM-01~05（5）+ OP-01~04（4）+ CS-01~08（8）+ CG-01~08（8）+ HM-01~03（3）= **64 行**。

> 每表前注来源为现行 SKILL.md 的表头与数据行号区间（以 `tests/skill-clause-map.md` §3.1 为准）。脚本实现与测试不得偏离本表语义；本文件修改必须先与 `skill-clause-map.md` 对账。

## 1. no-interrupt 权威合并规则（NC-01~08）

> 来源：现行 `SKILL.md` 第 35-50 行（"no-interrupt 权威合并规则"节，数据行 41-48，含第 50 行同名章节识别与复制归档辅助条款）。
> 适用模式：no-interrupt。同名章节识别与复制归档（NB-01/02，SKILL 50 行）为两模式共用的辅助条款，并入本表相关行的"备份要求"列与本节正文。
>
> **适用范围限制**：本表不适用于 `.claude/rules/` 下 7 个框架受管规则文件（见 RF-05）；框架规则文件走权威全覆盖。`merge_markdown` 与 NC-02/NC-03/NC-08 仍保留给非框架 Markdown 资产。

对于非框架资产，模板结构、必需章节、强制约束和摘要引用是权威内容；当前项目内容可按本表作为补充保留。

| 行 ID | 资产 | 冲突状态 | 普通模式动作 | no-interrupt 动作 | 备份要求 | 报告要求 | 对应测试 ID |
|-------|------|----------|--------------|-------------------|----------|----------|-------------|
| NC-01 | 目标 Markdown/YAML 文件 | 目标文件不存在 | 创建标准文件（普通模式遵循不覆盖语义；此处目标本就不存在，直接创建） | 创建标准文件 | 无（无原文件可备份） | 报告新增文件路径与来源模板 | `ut-merge_markdown-target-missing` / `it-s3-create` |
| NC-02 | 非框架 Markdown 文件 | 模板与项目存在不同章节 | 遵循不覆盖/冲突跳过策略；询问用户是否合并（无响应按保守默认保留项目文件） | 保留模板章节，并按原顺序保留项目独有章节 | 无（未修改项目文件时无需备份；若 no-interrupt 写入则按 §11.1 命名） | 报告保留的模板章节与项目独有章节清单 | `ut-merge_markdown-keep-project-sections` |
| NC-03 | 非框架 Markdown 文件 | 模板与项目存在同名章节 | 询问是否合并；无响应保留并报告 | 模板规范在前，项目独有内容去重后追加到该章节的"项目补充"（`**项目补充**` 为合并协议保留字，重跑幂等：`merge(t, merge(t, x)) == merge(t, x)`；合并结果与现有文件一致时跳过写盘并报告 `unchanged`） | 写入前按 §11.1 备份原文件 | 报告合并的章节名与去重后的"项目补充"行数 | `ut-merge_markdown-same-section-append` / `ut-merge_markdown-rerun-idempotent` / `ut-merge_markdown-polluted-self-heal` / `ut-step_s3-ordinary-unchanged` |
| NC-04 | CLAUDE.md / AGENTS.md 强制规则区 | 强制规则摘要或引用路径冲突 | 遵循 L0 受管区块处理（见 §4 L0 表）；强制规则冲突进入交互或保留并报告 | 强制规则摘要和引用路径以 `rule-config` 为准，项目技术栈、命令、业务规则和其他章节保留 | 按 L0 全局备份屏障（见 §11.2） | 报告以 rule-config 为准的摘要/路径与保留的项目章节 | `ut-merge_markdown-mandatory-override` |
| NC-05 | `openspec/config.yaml` | 配置已存在且可解析、无 `rules.apply` | 遵循 OS 表（见 §2）保守合并；交互分支见 OS-04 | 保留已有 `schema`、项目 context 和 proposal、design、specs、tasks 的额外规则，仅追加模板缺失内容 | 按 OS-B1 复制归档（见 §11.1） | 报告保留字段与新增内容清单 | `ut-merge_yaml-preserve-existing` |
| NC-06 | `openspec/config.yaml` | OpenSpec YAML 无法可靠解析或目标字段结构/类型不兼容 | 保留原文件并报告具体字段路径、实际类型和冲突，不发布候选 | 先备份；无法证明可无损规范化时终止，保持原文件不变并报告冲突；备份成功不代表允许破坏性重写 | 先成功备份原文件（§11.1）；备份失败立即终止且不修改原文件 | 报告字段路径、实际类型、冲突说明与终止原因 | `ut-merge_yaml-unparseable-abort` |
| NC-07 | 任意待合并文件 | 内容完全重复 | 跳过重复项并报告 | 只保留一份 | 无（无实质修改） | 报告去重前后的条目数 | `ut-merge_markdown-dedupe` |
| NC-08 | 非框架 Markdown 文件 | Markdown 无法可靠解析；或 existing 无任何 ATX 标题 / 首个标题前有实质前言（终审 I-1：章节合并会静默丢弃原文，同走本行 fallback） | 保留原文件并报告，不写标准结构 | 先备份，再写标准结构，并把原内容附加到"原项目补充" | 写入前按 §11.1 备份原文件 | 报告标准结构已写入、原内容位置（"原项目补充"）与备份路径 | `ut-merge_markdown-unparseable-fallback` / `ut-merge_markdown-no-headings-fallback` / `ut-merge_markdown-preamble-fallback` / `it-s3-markdown-unparseable-fallback` |

**辅助条款（两模式共用）**：

- **NB-01 同名章节识别**（SKILL 50 行）：以"标题级别 + 去除开头编号后的标题文本"识别同名章节。例如 `## 1. 语言规则` 与 `## 语言规则` 视为同名；标题级别不同则不判同名。对应测试 `ut-merge_markdown-section-identity`。
- **NB-02 复制归档路径**（SKILL 50 行）：需要备份时复制到 `cadence/legacy/<时间戳[-N]>/<相对 root 路径>`，原位文件不动。命名与 `.gitignore` 细则见 §11.1。

## 2. OpenSpec 配置处理（OS-01~08）

> 来源：现行 `SKILL.md` 第 631-675 行（"OpenSpec 配置处理"节，数据行 666-673）；辅助条款 OS-N1~N13（SKILL 633-660 行）与 OS-B1/OS-B2（SKILL 662/675 行）并入本节正文与"备份要求/报告要求"列。
> 适用模式：两模式。OS-N 编号条款与 OS-01~08 数据行的差异仅在交互/无交互分支，详见各列。

候选在目标文件同文件系统的临时工作区构建与验证；此阶段不得直接创建、覆盖或修改目标 `openspec/config.yaml`。目标存在时以原配置为候选基础，禁止用模板整体覆盖已有配置。

| 行 ID | 资产 | 冲突状态 | 普通模式动作 | no-interrupt 动作 | 备份要求 | 报告要求 | 对应测试 ID |
|-------|------|----------|--------------|-------------------|----------|----------|-------------|
| OS-01 | `openspec/config.yaml` | 配置不存在 | 从模板构建候选，经 YAML parser 解析与结构预检（根映射/schema 标量/context 字符串/rules 映射/artifact 字符串数组）通过后原子创建 | 同普通模式（两模式同动作） | 无（无原文件）；原子创建仍须经同文件系统 `os.replace()` | 报告原子创建成功、内容来源（模板基础）、结构预检结果 | `it-s7-openspec-create` / `ut-atomic_write-publish` |
| OS-02 | `openspec/config.yaml` | 配置可解析且无 `rules.apply` | 在候选中保守合并，完整行/完整字符串去重 | 同普通模式（两模式同动作） | 按 OS-B1 复制归档（§11.1） | 报告新增 context 行、按 proposal/design/specs/tasks 分组的合并规则 | `it-s7-openspec-merge-idempotent` |
| OS-03 | `openspec/config.yaml` 目标字段 | 目标字段结构/类型不兼容（根非映射、schema 非标量、context 非字符串、rules 非映射、artifact 非字符串数组等） | 先归档，归档成功后以模板内容原子替换原位并报告（两模式同动作，不经用户决策） | 同普通模式 | 先成功备份原文件（§11.1）；备份失败终止且不改原文件 | 报告字段路径、实际类型、冲突说明、备份路径与替换结果 | `it-s7-openspec-yaml-type-conflict-backed-up-replaced` |
| OS-04 | `openspec/config.yaml` 的 `rules.apply` | 存在 `rules.apply`（禁止创建的键） | 先创建备份；备份成功后在候选中移除并继续合并（两模式同动作，不经用户决策） | 同普通模式 | 先成功备份原文件（OS-B1，§11.1）；任何必要备份失败立即终止且不修改原文件 | 报告 `rules.apply` 移除结果、备份路径；不虚构 apply artifact | `it-s7-openspec-apply-backed-up-removed` / `it-s7-openspec-normal-apply-removed` |
| OS-05 | `openspec/config.yaml` | YAML 无法可靠解析 | 先归档，归档成功后以模板内容原子替换原位并报告（两模式同动作，不经用户决策） | 同普通模式 | 先成功备份原文件（§11.1）；备份失败终止且不改原文件 | 报告解析冲突、备份路径与替换结果 | `it-s7-openspec-invalid-yaml-backed-up-replaced` |
| OS-06 | 临时 Change `cadence-rule-config-validation` 的四类 instructions 验证 | **已废止，由结构预检取代**（design D4 删除了临时 Change 与四类 `openspec instructions` 验证）。现行语义以 OS-01/OS-N2 的结构预检为准。保留行 ID 用于对账，但各列正文仅记录废止前语义与现行取代 | 废止前：终止并报告失败 artifact、实际命令与错误。现行：结构预检失败→终止并报告失败字段路径、实际类型与错误；原文件不变 | 同普通模式（两模式同动作；现行同 OS-N12 结构预检失败分支） | 无（不改原文件；候选在临时工作区） | 现行报告：失败字段路径、实际类型、错误信息、候选清理/保留结果（不再报告 `openspec instructions ... --json` 实际命令或失败 artifact） | 已废止（design D4 已删除 instructions 验证；结构预检失败分支与 OS-N12 同路径） |
| OS-07 | `openspec/config.yaml` 发布 | 原子替换/原子创建失败 | 终止并保持或恢复原文件；目标原本不存在时保持不存在；不得声称成功 | 同普通模式（两模式同动作） | 发布失败不扩大损害；已建备份保留 | 报告发布失败原因、原文件状态（保持/恢复/不存在）、明确"未声称成功" | `it-s7-openspec-publish-failure-preserved` / `ut-atomic_write-fail` |
| OS-08 | `openspec/config.yaml` 任一必要备份分支 | 任一必要备份失败 | 终止且不改原文件；候选不发布 | 同普通模式（两模式同动作） | 备份失败本身即终止条件；不得部分合并 context、artifact 规则或删除无效键 | 报告失败备份路径、失败原因、候选不发布结果 | `it-s7-openspec-backup-fail-modes` |

**辅助条款（OS-N1~N13，SKILL 633-660 行；两模式共用，分支差异见上表）**：

- **OS-N1 候选隔离**：候选在目标文件同文件系统临时工作区构建；此阶段不得直接创建/覆盖/修改目标；目标存在时以原配置为候选基础，禁止模板整体覆盖。
- **OS-N2 结构预检**：YAML 根必须为映射；`schema` 必须缺失或为可保留标量；`context` 必须缺失或为字符串块/字符串标量；`rules` 必须缺失或为映射；`rules.proposal`/`rules.design`/`rules.specs`/`rules.tasks` 必须分别缺失或为字符串数组。除单独处理的无效 `rules.apply` 外，其他项目自定义键和 artifact 规则必须原样保留。
- **OS-N3 结构/类型不兼容处理**：同 OS-03。
- **OS-N4 候选处理不取消备份**：发现需备份分支时必须先成功备份，再对候选执行规范化/合并/无效键移除；必要备份失败时终止，候选不发布，原文件不变。
- **OS-N5 schema 保留**：预检通过后在候选中保留已有 `schema`；未设置 `schema` 时写入 `spec-driven`。
- **OS-N6 context 追加**：按完整行去重追加模板的 Cadence 协作 context（**实际为 5 行**，见 §11.5 修正说明），保留原有顺序以及项目技术栈、领域知识和其他上下文。
- **OS-N7 artifact 数组追加**：在 proposal、design、specs、tasks 数组中追加模板规则，按完整字符串去重，保留各 artifact 下的项目额外规则和原有顺序。
- **OS-N8 `rules.apply` 处理**：同 OS-04；禁止创建 `rules.apply`，也不得虚构 apply artifact。
- **OS-N9 YAML 无法可靠解析**：同 OS-05；不得静默重写。
- **OS-N10 临时 Change 验证**：**已废止，由结构预检取代**（design D4 删除了临时 Change 与四类 `openspec instructions` 验证；现行语义以 OS-01 的 YAML parser 解析与结构预检为准：根映射、`schema` 缺失或标量、`context` 缺失或字符串、`rules` 缺失或映射、四个 artifact 规则分别缺失或字符串数组）。保留行 ID 用于对账，但脚本 MUST NOT 创建临时 Change 或调用 `openspec instructions`。
- **OS-N11 原子发布**：同 OS-07；候选通过全部语法解析、结构预检、合并去重后（instructions 验证已废止，见 OS-N10），才允许使用同文件系统内 `os.replace()` 原子替换发布；目标原本不存在时也以原子创建方式发布，不得先落入半成品。
- **OS-N12 候选验证失败**：同 OS-06（已废止）；结构预检失败时报告失败字段路径、实际类型与错误，原文件不变，目标原本不存在时不得创建。
- **OS-N13 原子失败**：同 OS-07。
- **OS-B1 复制归档**：所有需备份分支都将原配置复制到 `cadence/legacy/<时间戳[-N]>/openspec/config.yaml`；必须在写入前完成归档，归档失败时不得部分合并 context、artifact 规则或删除无效键。
- **OS-B2 完成报告清单**：逐项列出新增 context 完整行、按 proposal/design/specs/tasks 分组的合并规则、发现及处理的无效键、所有备份路径、结构冲突的具体字段路径与实际类型、解析或内容冲突、候选结构预检结果、原子发布结果；无新增内容时明确报告为幂等跳过。（instructions 验证已废止，见 OS-N10；不再报告 `openspec instructions ... --json` 命令结果或失败 artifact。）

## 3. L1 协作规则增量（L1-01~07）

> 来源：现行 `SKILL.md` 第 677-689 行（"OpenSpec 与 Superpowers 协作规则增量处理"节，数据行 681-687；辅助条款 L1-B1/L1-B2 在 SKILL 689 行）。
> 适用模式：两模式。

仅处理带 `cadence-framework-rule:openspec-superpowers-workflow` 标记的 L1 文件；普通规则不覆盖策略见 §5 RF 表。标记只用于候选版本定位，最终识别必须比较完整文件内容。

| 行 ID | 资产 | 冲突状态 | 普通模式动作 | no-interrupt 动作 | 备份要求 | 报告要求 | 对应测试 ID |
|-------|------|----------|--------------|-------------------|----------|----------|-------------|
| L1-01 | `.claude/rules/openspec-superpowers-workflow.md` | 文件不存在 | 创建 v1（内容与框架 v1 规范源逐字一致） | 同普通模式（两模式同动作） | 无（无原文件） | 报告创建路径与版本 v1 | `it-s3-l1-create` |
| L1-02 | 同上 | 文件完整内容与当前框架 v1 一致 | 跳过 | 同普通模式（两模式同动作） | 无（不改文件） | 报告幂等跳过、判定 `current` | `ut-classify_l1-current` / `it-s3-l1-idempotent` |
| L1-03 | 同上 | 版本标记受支持且完整内容与对应旧版规范逐字一致 | 备份后升级为当前 v1 | 同普通模式（两模式同动作） | 按 L1-B1 复制归档（§11.1）；归档失败终止且不得替换原文件 | 报告判定 `old-version`、归档路径、升级到 v1 | `ut-classify_l1-old-version` / `it-s3-l1-upgrade`（仅单测覆盖：仓库仅存在 v1 规范源，upgrade 分支无法集成复现，待补） |
| L1-04 | 同上 | 仅受支持旧版本标记匹配但完整内容与对应旧版规范不同 | 归入"与任何已知框架版本不匹配"；备份后以框架 v1 替换并报告（两模式同动作，不经用户决策） | 同普通模式（两模式同动作） | 两模式均先成功备份（L1-B1，§11.1）；备份失败终止 | 报告判定 `mismatch`（非 `old-version`）与备份路径、替换结果 | `ut-classify_l1-old-marker-drift` / `it-s3-l1-old-marker-drift`（仅单测覆盖：同 L1-03 无法集成复现，待补）/ `it-s3-l1-drift-normal-replaced` |
| L1-05 | 同上 | 当前 v1 标记存在但完整内容不同 | 同 L1-04：归入"不匹配"，备份后以框架 v1 替换并报告（两模式同动作，不经用户决策） | 同普通模式（两模式同动作） | 同 L1-04 | 报告判定 `mismatch`；不得仅凭标记当作 `current` 跳过 | `ut-classify_l1-v1-marker-drift` / `it-l1-drift-replace` / `it-s3-l1-drift-normal-replaced` |
| L1-06 | 同上 | 文件无标记或与已知版本不匹配 | 归入"与任何已知框架版本不匹配"；备份后以框架 v1 替换并报告（两模式同动作，不经用户决策） | 同普通模式（两模式同动作） | 两模式均先成功备份（L1-B1，§11.1）；备份失败终止 | 报告判定 `unmarked`；两模式分支动作符合表义 | `ut-classify_l1-unmarked` / `it-l1-unknown-replace` / `it-s3-l1-drift-normal-replaced` |
| L1-07 | 同上任意需 L1 备份的分支 | 任何需要 L1 备份的分支备份失败 | 终止且不得替换原文件 | 同普通模式（两模式同动作） | 备份失败本身即终止条件 | 报告失败备份路径、失败原因、原文件不变 | `it-s3-l1-backup-failure-preserved` |

**辅助条款（L1-B1/L1-B2，SKILL 689 行）**：

- **L1-B1 复制归档**：需要备份时复制到 `cadence/legacy/<时间戳[-N]>/.claude/rules/openspec-superpowers-workflow.md`，原位文件不动；归档失败终止且不得替换原文件。
- **L1-B2 标记仅用于定位**：`cadence-framework-rule:openspec-superpowers-workflow` 标记只用于候选版本定位；最终识别必须比较完整文件内容，不得仅凭标记把文件识别为当前或受支持旧版，也不得把无标记文件当作已知框架版本覆盖。

## 4. L0 入口增量（L0-01~07）

> 来源：现行 `SKILL.md` 第 691-711 行（"CLAUDE.md / AGENTS.md 入口增量处理"节，数据行 699-705；屏障与受管区块外保留条款 L0-B1/L0-B2 在 SKILL 691-694、707 行）。L0-P1~P12 处理流程条款在 SKILL 185-200 行，与本表互证。
> 适用模式：两模式。

当前 L0 版本为 **v2**，受支持旧版为 **v0、v1**。v1 只有在完整受管区块与规范源 `references/rules/l0-history/agent-routing-kernel-v1.md` 逐字一致时才判定为可升级；标记匹配但正文不一致一律判定 drift。v0 没有规范源，成对标记即执行 upgrade（该无规范源例外须写入报告）。

写入入口文件前必须先完成双入口统一预检，确定两个入口的标记、版本、完整内容、交互结果、目标动作和全部备份需求；在写入任一入口前创建本次所需的全部 L0 备份，仅当全部必要备份成功后才按下表执行各入口动作。任一必要备份失败时 CLAUDE.md 与 AGENTS.md 均不得写入。

L0 迁移不变量：最终只保留一个 v2 区块；混合版本标记仅在安全成对时删除完整区块，孤立标记只删除自身标记行；重复区块归并并报告 `L0_DEDUP`；完整区块含污染对时降级为只剥离边界标记，保留区块内部用户正文，避免重叠删除吞掉内容。dedup/upgrade 在普通与 no-interrupt 模式执行相同动作。

| 行 ID | 资产 | 冲突状态 | 普通模式动作 | no-interrupt 动作 | 备份要求 | 报告要求 | 对应测试 ID |
|-------|------|----------|--------------|-------------------|----------|----------|-------------|
| L0-01 | CLAUDE.md / AGENTS.md | 入口不存在 | 创建基础入口并插入当前 v2（L0 放在文件说明之后、`## 强制规则` 之前） | 同普通模式（两模式同动作） | 无（无原文件） | 报告创建路径、L0 版本 v2、插入位置 | `it-entry-base-created` |
| L0-02 | 入口的 L0 受管区块 | 当前 v2 区块与规范源完整一致 | 跳过，不重复写入 | 同普通模式（两模式同动作） | 无（不改区块） | 报告幂等跳过；双入口 sha256 不变 | `it-s4-idempotent` / `ut-l0-v2-skip` |
| L0-03 | 同上 | 当前 v2 标记成对但完整受管区块与规范源不同 | 视为本地修改；纳入备份屏障后以规范源当前 v2 替换（两模式同动作，不经用户决策） | 同普通模式 | 先成功备份（§11.1、§11.2 全局屏障）；任一必要备份失败双入口均不得写入 | 报告判定"本地修改"、备份路径与替换结果 | `it-s4-drift-normal-replaced` / `it-s4-drift-replaced-outside-preserved` / `ut-l0-v2-v1-drift` |
| L0-04 | 同上 | 受支持旧版本标记成对 | 备份成功后升级到当前 v2 并报告；v1 仅规范源逐字一致时可升级，v0 成对标记按无规范源例外升级 | 同普通模式（两模式同动作） | 将该入口纳入本次备份屏障（§11.2）；屏障失败双入口均不得写入 | 报告备份路径、处理动作与分支 | `it-s4-upgrade` / `ut-l0-v2-upgrade` / `ut-l0-v2-v1-drift` |
| L0-05 | 同上 | 无 L0 标记 | 插入当前 v2，入口原内容保留 | 同普通模式（两模式同动作） | 无（不改原内容，仅插入） | 报告插入位置；原内容 sha256 不变 | `it-s4-insert` |
| L0-06 | 同上 | 单侧/顺序错误，或混合版本、重复区块等需归并的标记状态 | 单侧/顺序错误、混合版本与重复区块均按确定性安全归并执行（两模式同动作，不经用户决策） | 同普通模式 | 归并/替换分支按 §11.1、§11.2 全局屏障；任一必要备份失败双入口均不得写入 | 报告处理后标记成对且唯一；重复归并记 `L0_DEDUP`；区块外内容保留 | `it-s4-broken-markers-preserve-arbitrary` / `ut-l0-v2-mixed` / `ut-l0-v2-dedup` / `ut-l0-v2-nested-broken` |
| L0-07 | 同上任意需 L0 备份的分支 | 任何 L0 备份失败 | 终止本次 L0 更新，CLAUDE.md 与 AGENTS.md 均不得写入 | 同普通模式（两模式同动作） | 备份失败本身即终止条件（全局屏障，见 §11.2） | 报告失败备份路径、失败原因、双入口零写入 | `it-s4-backup-barrier` |

**辅助条款（L0-B1/L0-B2；L0-P1~P12 互证）**：

- **L0-B1 统一预检 + 全局备份屏障**（SKILL 691-694 行；与 L0-P2~P4 在 SKILL 190-192 行互证）：写入任一入口前先按"L0 受管区块处理"完成双入口统一预检，确定两个入口的标记、版本、完整内容、交互结果、目标动作和全部备份需求；在写入任一入口前创建本次所需的全部 L0 备份；仅当统一预检和全部必要备份成功后才允许按各入口分支写入；任一必要备份失败时双入口均不得写入，区块内外保持原样。细则见 §11.2。
- **L0-B2 区块外内容保留**（SKILL 707 行）：所有场景必须保持 L0 受管区块外的项目技术栈、命令、业务规则和用户内容原样。
- **L0 版本一致性**（L0-P12，SKILL 200 行）：CLAUDE.md 与 AGENTS.md 必须使用相同 L0 版本和语义。

## 5. 规则文件处理（RF-01~05）

> 来源：现行 `SKILL.md` 第 606-629 行（"规则文件增量处理"节，数据行 612-615）。
> 适用模式：两模式。`.claude/rules/` 下 7 个框架受管规则文件统一使用 RF-05 的权威全覆盖语义；`openspec-superpowers-workflow.md` 仅按 §3 L1 表版本化特例处理。RF-01~RF-04 仅保留给非框架资产或历史条款对账，资产列均明确指向 RF-05。

框架受管清单固定为：`mcp-servers.md`、`code-reading.md`、`document-storage.md`、`language.md`、`markdown-format.md`、`code-usage.md`、`playwright.md`。其中缺失文件从所选模板创建，内容与模板一致时幂等跳过；存在 drift 时执行 RF-05。`code-usage.md` 按项目类型从 `code-usage-coding.md` / `code-usage-noncoding.md` 单选来源。

| 行 ID | 资产 | 冲突状态 | 普通模式动作 | no-interrupt 动作 | 备份要求 | 报告要求 | 对应测试 ID |
|-------|------|----------|--------------|-------------------|----------|----------|-------------|
| RF-01 | 非框架普通规则资产（框架资产改用 RF-05） | 文件不存在 | 从模板根路径读取并创建 | 同普通模式（两模式同动作） | 无（无原文件） | 报告创建路径与来源模板 | `it-s3-rules-create` |
| RF-02 | 非框架普通规则资产（框架资产改用 RF-05） | 文件已存在且完整内容与模板一致 | 幂等跳过，不重复写入 | 同普通模式（两模式同动作） | 无（不改文件） | 报告幂等跳过；原文件 sha256 不变 | `it-s3-rules-idempotent` |
| RF-02b | 非框架普通规则资产（框架资产改用 RF-05） | 文件已存在但完整内容与模板不一致（drift） | 见 RF-05 权威覆盖（两模式同动作，不经用户决策） | 见 RF-05 权威覆盖；不得对框架受管规则文件执行章节级合并 | 两模式均按 §11.1 复制归档原文件，归档失败终止且不改原文件 | 报告冲突标识 `s3:<rel>`、状态 `drift`、RF-05 权威覆盖结果、归档路径 | `it-s3-normal-authoritative-overwrite` |
| RF-03 | 历史 `code-reading.md` 补齐条款（框架资产改用 RF-05） | 新增 `code-reading.md`（老项目补齐） | 所有项目默认新增；非 Coding 仅跳过 CodeGraph 初始化 | 同普通模式（两模式同动作） | 无（新增，无原文件） | 报告补齐 `code-reading.md`；非 Coding 记录跳过 CodeGraph 初始化 | `it-s3-code-reading-backfill` |
| RF-04 | 历史 CodeGraph 段落条款（框架资产改用 RF-05） | 规则文件已存在但缺少 CodeGraph 段落 | 视为 RF-05 drift：两模式屏障归档后以模板覆盖，不经用户决策 | 见 RF-05 权威覆盖；不得章节合并或保留项目补充 | 两模式均纳入 RF-05 全局归档屏障 | 报告统一 drift 冲突与 `authoritative-overwrite`/`unchanged`，旧 no-interrupt 章节合并映射已废弃 | `ut-s3-codegraph-section-unified-drift` / `ut-s3-codegraph-section-unified-merge`（旧测试名保留，断言已改为完整模板覆盖） |
| RF-05 | `.claude/rules/` 下 7 个框架受管规则文件（`mcp-servers.md`/`code-reading.md`/`document-storage.md`/`language.md`/`markdown-format.md`/`code-usage.md`/`playwright.md`） | 文件存在但内容≠模板 | 屏障归档+`atomic_write` 模板（两模式同动作，不经用户决策） | 屏障归档+`atomic_write` 模板 | 全局屏障统一归档 | `authoritative-overwrite`/`unchanged` | `ut-s3-authoritative-overwrite`/`ut-s3-authoritative-idempotent` |

## 6. 强制规则章节与摘要合并语义（SM-01~05）

> 来源：前 8 个任务落地后的入口规范化实现；摘要引用、`## 强制规则` 章节规范化与项目配置开关均由 S4 合成流程统一处理。
> 适用模式：两模式。五行均为两模式同动作，且不需要备份；L0 受管区块本身仍按 §4 L0 表处理。

| 行 ID | 资产 | 冲突状态 | 普通模式动作 | no-interrupt 动作 | 备份要求 | 报告要求 | 对应测试 ID |
|-------|------|----------|--------------|-------------------|----------|----------|-------------|
| SM-01 | CLAUDE.md / AGENTS.md 的入口内容 | 规则章节及摘要引用已收敛，重跑不会产生内容变化 | 幂等跳过，不写盘 | 同普通模式 | 无 | 报告幂等跳过；顶层 `warnings` 仍存在且不改变 `overall` | `TestStepS4EntryFiles::test_skip_state_idempotent_no_change` / `it-s4-idempotent` / `ut-norm-idempotent` |
| SM-02 | `## 强制规则` 章节 | 章节缺失或摘要引用缺失 | 创建强制规则章节；在 L0 之后（有 L0 时）落位，并按规则文件 marker 补齐缺失摘要 | 同普通模式 | 无 | 报告章节创建/摘要补齐位置；项目配置开关不重复创建 H2 | `TestNormalizeMandatoryRules::test_create_section_when_missing` / `ut-ensure_summary-missing-rule2-rule6` |
| SM-03 | 强制规则章节中的退役引用 | 命中 `RETIRED_RULE_FILES`（当前为 `serena-usage.md`） | 仅删除该退役规则引用块；仅对 `serena-usage.md` 生效 | 同普通模式 | 无 | 报告正文不再保留退役引用；不得误删未列入退役清单的用户内容 | `TestNormalizeMandatoryRules::test_serena_removed` / `ut-norm-retired` / `ut-norm-retired-empty` |
| SM-04 | 强制规则章节 | 规则编号、规则 6 两类旧文案或规则 5 标题与权威文本不一致 | 按权威 1~7 顺序重排重编号；替换规则 6 两类旧文案；规则 5 标题统一为 `MCP Server 使用规则` | 同普通模式 | 无 | 报告合成结果；权威条目顺序、编号、标题和入口文案可重复收敛 | `TestCanonicalRules` / `TestNormalizeMandatoryRules::test_renumber_1_to_9` / `ut-norm-rule6-old` / `ut-norm-wording` |
| SM-05 | 强制规则章节与入口用户内容 | 存在用户自定义 H3/行块、重复 `## 强制规则` 或章节外孤立规则 6 | 保留无法识别的用户内容并置于权威条目之后；只规范化首个章节，报告 warnings | 同普通模式 | 无 | 顶层 `warnings` 契约固定包含脚本实际五个码：`USER_LINES_KEPT`、`DUPLICATE_H2`、`ORPHAN_RULE6`、`INVALID_TOGGLE`、`L0_DEDUP`；warnings 不影响 `overall`，dry-run/apply/no-interrupt 三态字段一致 | `TestComposeEntryWarnings` / `ut-norm-user-h3` / `ut-norm-orphan-rule6` / `ut-norm-dup-h2` / `ut-compose-warnings` / `ut-s4-warnings` |

## 7. 可选规则增量（OP-01~04）

> 来源：现行 `SKILL.md` 第 719-728 行（"可选规则增量处理"节，数据行 725-728）。
> 适用模式：两模式。

| 行 ID | 资产 | 冲突状态 | 普通模式动作 | no-interrupt 动作 | 备份要求 | 报告要求 | 对应测试 ID |
|-------|------|----------|--------------|-------------------|----------|----------|-------------|
| OP-01 | 可选规则文件 + 摘要（code-reading / playwright 等） | 规则文件和摘要均已存在 | 视为已启用，仅检查完整性 | 同普通模式（两模式同动作） | 无（不改文件） | 报告完整性检查结果；文件与摘要不重写 | `it-s3-optional-complete`（待补） |
| OP-02 | `.claude/rules/code-reading.md` | 代码阅读规则缺失 | 所有项目默认新增；非 Coding 仅跳过 CodeGraph 初始化 | 同普通模式（两模式同动作） | 无（新增） | 报告规则文件补齐；非 Coding 记录跳过 CodeGraph 初始化 | `it-s3-code-reading-backfill` |
| OP-03 | `.claude/rules/playwright.md` | Playwright 规则缺失 | 默认跳过，用户明确要求时新增 | 同普通模式（两模式同动作；no-interrupt 下"用户明确要求"由意图参数 `--enable-playwright` 表达） | 无（默认跳过；新增时无原文件） | 报告默认跳过或按 `--enable-playwright` 新增 | `it-s3-playwright-skip` / `it-s3-playwright-enable` |
| OP-04 | 可选规则历史选择 | 无法判断历史选择 | 按本节默认值处理，不询问 | 同普通模式（两模式同动作；no-interrupt 本就不询问） | 无（不询问，不改文件） | 报告按默认值执行；不生成提问冲突项 | `it-s3-playwright-skip`（默认跳过不询问分支） |

## 8. CodeGraph 已存在状态（CS-01~08）

> 来源：现行 `SKILL.md` 第 499-580 行（"CodeGraph 项目初始化"节"已存在状态处理"表，数据行 560-567）。
> 适用模式：两模式。CS 表描述 `codegraph install`/`init` 后的状态核验与补齐；与 §10 CG 表的增量矩阵互证。

| 行 ID | 资产 | 冲突状态 | 普通模式动作 | no-interrupt 动作 | 备份要求 | 报告要求 | 对应测试 ID |
|-------|------|----------|--------------|-------------------|----------|----------|-------------|
| CS-01 | `.codegraph/` + MCP 配置 | `.codegraph/` 不存在 | Coding 项目默认执行 `codegraph install` 与 `codegraph init` | 同普通模式（两模式同动作） | 无（生成新目录） | 报告 `.codegraph/` 生成；两配置文件含 CodeGraph MCP | `it-s8-codegraph-fresh` |
| CS-02 | `.codegraph/` | `.codegraph/` 已存在 | 运行 `codegraph status`，报告已初始化，不重复 `codegraph init` | 同普通模式（两模式同动作） | 无（不改目录） | 报告 `status` 结果；init 未再次执行（调用计数=0） | `it-s8-codegraph-existing` |
| CS-03 | `.mcp.json` + `.codex/config.toml` | 两文件均已有 CodeGraph MCP server | 跳过，不重复写入 | 同普通模式（两模式同动作） | 无（不改文件） | 报告跳过；两配置文件 sha256 不变 | `it-s8-codegraph-both-present` |
| CS-04 | 同上 | `.mcp.json` 有 CodeGraph MCP，但 `.codex/config.toml` 缺少 `[mcp_servers.codegraph]` | 参考 `.mcp.json` 手动补齐 `.codex/config.toml` | 同普通模式（两模式同动作） | 无（增量补 toml 块；按 §11.1 配置补齐不要求备份，除非破坏既有内容，破坏性写入仍按 §11.1） | 报告 toml 补齐的块；其余内容不变 | `it-s8-codegraph-toml-missing` |
| CS-05 | 同上 | `.mcp.json` 缺少 CodeGraph MCP | 按 `mcp-configuration.md` 兜底配置补齐 `.mcp.json`，再同步补齐 `.codex/config.toml` | 同普通模式（两模式同动作） | 同 CS-04 | 报告两文件均补齐兜底配置 | `it-s8-codegraph-mcp-missing` |
| CS-06 | 同上 | Claude/Codex 缺少 CodeGraph MCP server | 执行 `codegraph install --target=claude,codex --location=local --yes` 后必须再次核验两个配置文件 | 同普通模式（两模式同动作） | 同 CS-04 | 报告 install 调用、二次核验、仅补缺失方 | `it-s8-codegraph-install-reverify` |
| CS-07 | 同上 | `codegraph install` 失败 | 提供 `mcp-configuration.md` 手动兜底配置，并分别补齐 `.mcp.json` 与 `.codex/config.toml` | 同普通模式（两模式同动作）；步骤标记 `degraded` 并继续，补写/备份/原子写失败仍终止（design D3） | 同 CS-04 | 报告步骤状态 `degraded`、两文件由脚本补齐、整体不因此失败 | `it-s8-codegraph-install-fail` / `it-s8-codegraph-binary-missing`（codegraph 二进制缺失/不可执行同走本行降级路径，终审 C-2） |
| CS-08 | `.codegraph/` | `codegraph init` 失败 | 报告项目语言、目录规模或 `codegraph.json` 可能需要人工配置，不阻塞其他初始化项 | 同普通模式（两模式同动作）；步骤标记 `degraded` | 无（不改文件） | 报告步骤 `degraded`、后续步骤照常、含人工配置建议 | `it-s8-codegraph-init-fail` |

## 9. CodeGraph 增量（CG-01~08）

> 来源：现行 `SKILL.md` 第 730-743 行（"CodeGraph 增量处理"节，数据行 736-743）。
> 适用模式：两模式。与 §8 CS 表互证；CG 表聚焦重复运行的增量补齐。

| 行 ID | 资产 | 冲突状态 | 普通模式动作 | no-interrupt 动作 | 备份要求 | 报告要求 | 对应测试 ID |
|-------|------|----------|--------------|-------------------|----------|----------|-------------|
| CG-01 | CodeGraph 相关规则/摘要/MCP 配置/`.codegraph/`/`.gitignore` | 老项目已跑过 `/rule-config` 但缺少 CodeGraph | 只补 CodeGraph 相关规则、摘要、MCP 配置、`.codegraph/` 初始化和 `.gitignore` | 同普通模式（两模式同动作） | 同 CS-04（仅补齐缺失项） | 报告仅新增 CodeGraph 相关项；其余文件 sha256 不变 | `it-s8-codegraph-backfill` |
| CG-02 | `.codegraph/` | `.codegraph/` 已存在 | 运行 `codegraph status` 并跳过初始化 | 同普通模式（两模式同动作） | 无 | 报告跳过 init；status 入报告 | `it-s8-codegraph-existing` |
| CG-03 | `.codegraph/` | `.codegraph/` 不存在 | Coding 项目默认执行 `codegraph init` | 同普通模式（两模式同动作） | 无（生成新目录） | 报告 init 执行且 `.codegraph/` 生成 | `it-s8-codegraph-fresh` |
| CG-04 | `.mcp.json` + `.codex/config.toml` | 双配置均已有 CodeGraph MCP server | 跳过，不重复写入 | 同普通模式（两模式同动作） | 无 | 报告跳过；两配置文件 sha256 不变 | `it-s8-codegraph-both-present` |
| CG-05 | 同上 | `.mcp.json` 有、`.codex/config.toml` 缺 | 参考 `.mcp.json` 补齐 Codex 本地 MCP 配置 | 同普通模式（两模式同动作） | 同 CS-04 | 报告 toml 补齐且其余内容不变 | `it-s8-codegraph-toml-missing` |
| CG-06 | 同上 | 任一配置文件缺少 CodeGraph MCP server | 先执行 `codegraph install --target=claude,codex --location=local --yes`，再核验并补齐缺失文件 | 同普通模式（两模式同动作） | 同 CS-04 | 报告 install 后二次核验、只补缺失方 | `it-s8-codegraph-install-reverify` |
| CG-07 | `.gitignore` | `.gitignore` 已有 `.codegraph/` | 跳过 | 同普通模式（两模式同动作） | 无 | 报告跳过；不重复追加 | `it-s6-gitignore-codegraph-idempotent` |
| CG-08 | `codegraph.json` | `codegraph.json` 存在 | 保留，不加入 `.gitignore` | 同普通模式（两模式同动作） | 无（不改文件） | 报告保留 `codegraph.json`；`.gitignore` 不含其条目 | `it-s6-codegraph-json-keep` |

## 10. 历史目录迁移（HM-01~03）

> 来源：现行 `SKILL.md` 第 408-460 行（"历史产物迁移（仅普通模式）"节，数据行 431-433）。no-interrupt 模式不执行本表，只执行 NH-01~03（SKILL 54-56 行）：仅检测 16 个精确历史目录清单并写入报告，不 `mv`、不合并、不删除、不清理空目录。
> 适用模式：HM 表普通；NH 条款 no-interrupt。

| 行 ID | 资产 | 冲突状态 | 普通模式动作 | no-interrupt 动作 | 备份要求 | 报告要求 | 对应测试 ID |
|-------|------|----------|--------------|-------------------|----------|----------|-------------|
| HM-01 | `.claude/<dir>` → `cadence/<dir>`（16 个历史目录之一） | `cadence/<dir>` 不存在 | 将 `.claude/<dir>` 迁移至 `cadence/<dir>` | 不执行迁移（按 NH-02 仅报告） | 无（mv 不要求备份；目标为空目录） | 报告源不存在、目标内容一致 | `it-s5-history-hm01-reachable` |
| HM-02 | 同上 | `cadence/<dir>` 已存在且为空 | 将 `.claude/<dir>` 的内容迁入 `cadence/<dir>`，并清理空源目录 | 不执行迁移（按 NH-02 仅报告） | 无 | 报告全部条目移入目标；源目录被移除或为空 | `it-s5-history-merge-empty` |
| HM-03 | 同上 | `cadence/<dir>` 已存在且非空 | 跳过该目录并报告冲突，要求用户手动处理 | 不执行迁移（按 NH-02 仅报告） | 无（不移动） | 报告源与目标均不变；含冲突目录与手动处理提示 | `it-s5-history-conflict-skip` |

**辅助条款（NH-01~03，SKILL 54-56 行；no-interrupt 专用）**：

- **NH-01 检测清单**：no-interrupt 只检测 16 个精确历史目录：`.claude/prds`、`.claude/analysis`、`.claude/analysis-docs`、`.claude/docs`、`.claude/designs`、`.claude/designs-reviews`、`.claude/plans`、`.claude/readmes`、`.claude/modaos`、`.claude/models`、`.claude/architecture`、`.claude/notes`、`.claude/logs`、`.claude/reports`、`.claude/project-rules`、`.claude/cache`。清单外同名目录不检出。对应测试 `it-s5-history-report-only`。
- **NH-02 仅报告不动手**：检测到历史目录仅写入执行报告，不执行 `mv`、目录内容合并、目录删除或空目录清理。对应测试 `it-s5-history-no-interrupt`。
- **NH-03 模式归属**：本规则只覆盖 no-interrupt；普通模式继续执行 HM-01~03 的历史产物迁移步骤。对应测试 `it-s5-history-normal`。
- **禁止迁移**（S6-01，SKILL 435-437 行）：普通模式下禁止迁移 `.claude/rules`、`.claude/commands`、`.claude/skills`。对应测试 `it-s5-history-forbidden`。

## 11. 横切契约与辅助正文

以下条款为十张表共用的横切规则，脚本实现与 Agent 行为均必须遵守。

### 11.1 `cadence/legacy` 复制归档

- **归档路径**：`backup_file(path, root)` 使用 `shutil.copy2` 将原文件复制到 `cadence/legacy/<时间戳[-N]>/<相对 root 路径>`；时间戳为 14 位本地时间 `YYYYMMDDHHMMSS`。原位文件保持不动，禁止使用 `shutil.move`。
- **同秒冲突**：首个归档目录为 `<时间戳>`；同一秒再次归档时在**时间戳目录**后追加 `-2`、`-3`……，例如 `cadence/legacy/20260801120000-2/.claude/rules/language.md`。文件名不追加后缀。
- **固定 `.gitignore`**：`cadence/legacy/.gitignore` 内容固定为 `*\n!.gitignore\n`；每次归档前都必须验证，缺失或内容不符时修复后再归档。
- **失败语义**：归档失败统一抛出 `BackupError` 并终止对应发布分支；原位文件未被移动。所有规则文件、L0 入口、L1 与 `openspec/config.yaml` 的备份分支均使用本路径结构。
- **备份与写入关系**：所有需要归档的分支必须先完成归档，再执行 `atomic_write`；归档失败时不得部分合并、不得删除无效键、不得修改原文件。归档成功不等于允许破坏性重写（NC-06/OS-03 仍适用）。
- **测试基线**：相对 root 的归档路径匹配 `^cadence/legacy/[0-9]{14}(-[0-9]+)?/.+$`，且原位文件仍在；对应 `ut-backup_file-legacy-copy`、`ut-backup_file-legacy-gitignore`、`ut-backup_file-unique-suffix`，资产相对路径另由 `ut-backup_file-openspec-naming` / `ut-backup_file-l1-naming` 覆盖。

### 11.2 L0 双入口复制归档屏障

L0 更新先完成 CLAUDE.md 与 AGENTS.md 的统一预检，收集本次全部归档需求；随后使用 §11.1 的 `cadence/legacy` 复制归档。只有全部必要归档成功后，才允许依次对需要更新的入口执行 `atomic_write` 覆盖。

1. `compute_plan`：统一确定双入口的标记、版本、完整内容、交互结果、目标动作和全部归档需求。
2. 全量复制归档：原位文件保持不动，将本次全部必要恢复点复制到 `cadence/legacy/<时间戳[-N]>/<相对路径>`。
3. 原子覆盖：仅当步骤 2 全部成功后，才依次对各入口执行 `atomic_write`；`atomic_write` 使用 `os.replace`，某入口发布失败时该入口原文件因原子性保持不变。

失败语义：任一归档失败，步骤 3 完全不执行，CLAUDE.md 与 AGENTS.md 均不写入；已成功创建的归档保留。对应 `test_l0_second_archive_failure_keeps_both`。任一 `atomic_write` 失败时，失败入口的原文件保持不变，对应 `test_atomic_write_failure_keeps_original`。OpenSpec（OS-N4/OS-08）与 L1（L1-07）各自也遵守“必要归档失败即终止”，但不跨资产；只有 L0 是跨双入口屏障。

### 11.3 报告要求（失败关闭与 schema）

**失败关闭**：必调 Skill、OpenSpec 契约、实施 Plan 或新鲜验证证据缺失时停止，不得降级绕过。脚本层面的失败关闭体现为：任一必要备份失败、原子发布失败、候选验证失败、结构/类型不兼容无法证明无损规范化时，立即非零退出且零写入（或保持/恢复原文件），报告必须包含失败文件、失败原因、已完成项目和恢复建议（NR-04/NR-05，SKILL 32-33 行）。

**失败报告字段**（NR-05，SKILL 33 行）：必须含失败文件、失败原因、已完成项目（逐项列出）、恢复建议。对应测试 `it-apply-failure-report-fields`。

**成功完成报告**（OS-B2，SKILL 675 行）：逐项列出新增 context 完整行、按 artifact 分组的合并规则、无效键处理、所有备份路径、结构冲突字段路径与实际类型、解析或内容冲突、候选结构预检结果、原子发布结果；无新增内容时明确报告"幂等跳过"。（instructions 验证已废止，见 OS-N10；不再报告失败 artifact 或四类 instructions 命令结果。）

**顶层 `warnings` 契约**：报告无论 dry-run、普通 apply 或 no-interrupt apply 都必须有顶层数组 `warnings`；它只承载诊断，不改变 `overall` 的 `ok` / `degraded` / `fail` 判定。脚本实际枚举五个 code：`USER_LINES_KEPT`（用户规则块保留）、`DUPLICATE_H2`（仅处理首个同名 H2）、`ORPHAN_RULE6`（章节外孤立规则 6）、`INVALID_TOGGLE`（非法开关值保留原文）与 `L0_DEDUP`（L0 重复/孤立当前标记归并）。`ENTRY_TOGGLE_MISMATCH` 是 Agent 读取双入口开关时的不一致告警，不由脚本写入此数组。

**产物自动提交开关**：`_ensure_commit_toggle` 在首个既有 `## 项目配置` 章节末尾确保唯一 `- **产物自动提交（design/plan）**：关闭`；没有该章节时创建它。章节仅维护该开关，既有技术栈等用户内容逐字保留且不由脚本检测或写入。合法用户值 `开启` / `关闭` 原样保留，非法值保留原文并发出 `INVALID_TOGGLE`。写入双入口一致的开关。读取行为由 Agent 层执行：CLAUDE.md 优先、AGENTS.md 兜底；两者不一致按关闭处理并提示 `ENTRY_TOGGLE_MISMATCH`。

**产物路径覆盖表**：`ARTIFACT_PATH_OVERRIDE_TABLE` 的三份逐字一致副本位于 L0 v2 kernel、`document-storage.md` 与脚本常量：`docs/superpowers/specs/`（design/spec）→ `cadence/designs/`，`docs/superpowers/plans/`（plan）→ `cadence/plans/`。OpenSpec 产物仍位于 `openspec/`。

**决策文件 schema**（design D3 横切契约 XC-03，普通模式 apply 入口）：

- **conflict_id 格式**：`<step>:<资产>[:<分支>]`。`<step>` 为步骤标识（如 `s1`、`s3`、`s4`、`s7`）；`<资产>` 为受冲突的文件或配置块标识；可选 `<分支>` 用于同步骤同资产的多分支冲突。
- **decision 枚举**：按资产类型取值（以下枚举条目 2026-08-19 起均转为两模式确定性动作，不再产生该冲突；枚举与 `allowed_decisions` 校验保留为休眠兜底契约，供未来冲突类型复用）：
  - 框架受管规则文件 drift（RF-05；RF-02b 为历史非框架条款，状态 `drift`，冲突标识 `s3:<rel>`）：`replace` / `keep`（2026-08-19 起转为确定性动作，不再产生该冲突；原 A 类 keep 保留分支随权威化消亡，原测试 `it-s3-normal-keep-decision` 改名为 `it-s3-normal-authoritative-overwrite`）。
  - L1 协作规则 drift/unmarked（L1-04/L1-05/L1-06，冲突标识 `s3:<rel>`、kind=`l1`）：`replace` / `keep`（2026-08-19 起转为确定性动作，不再产生该冲突；替换分支由 `it-s3-l1-drift-normal-replaced` 覆盖）。
  - L0 受管区块 drift/broken（L0-03/L0-06，冲突标识 `s4:<entry>`）：`replace` / `keep`（2026-08-19 起转为确定性动作，不再产生该冲突；替换分支由 `it-s4-drift-normal-replaced` 覆盖）。
  - OpenSpec `rules.apply`（OS-04，冲突标识 `s7:openspec/config.yaml`）：`remove_apply` / `keep`（2026-08-19 起转为确定性动作，不再产生该冲突；移除分支由 `it-s7-openspec-normal-apply-removed` 覆盖）。
  - ~~项目类型检测矛盾：`non-coding` / `coding`（IA-02，固定冲突标识 `s1:project-type-conflict`）~~（codex 五轮已删除：项目类型判定重构为两模式唯⼀规则，不再产生冲突，详见 spec/design「项目类型判定两模式规则」）。
- **allowed_decisions**：每个 conflict_id 的 decision 必须在其资产类型对应的枚举内；超出枚举的决策视为非法（当前无活跃冲突类型，机制休眠兜底）。RF-04 不再产生独立的 report-only 冲突，框架资产统一复用 RF-05 的 drift 决策枚举 `replace` / `keep`。
- **default_keep 语义**（见 §11.6 详细说明）：2026-08-19 权威化后六类原 A 类冲突均转为两模式确定性动作，`default_keep` 标注机制休眠兜底，供未来冲突类型复用。

**decisions 四类异常**（XC-03）：任一即非零退出且零写入——

1. 决策文件缺失或无法解析（普通模式提供决策文件时）。
2. 决策含未知或重复 `conflict_id`。
3. 计划存在的冲突缺少对应决策（休眠兜底机制：2026-08-19 权威化后当前系统无活跃冲突类型，所有原 A 类冲突均已转为两模式确定性动作；本机制保留供未来引入无安全默认的冲突时复用）。
4. 决策与新鲜计划不符（stale）。

计划无冲突时不要求决策文件；no-interrupt 模式不读取也不要求决策文件，全部冲突按十张表内部规则决策（XC-04，对应测试 `it-entry-base-created`——任一 no-interrupt 无 `--decisions` 成功用例）。2026-08-19 起当前系统无活跃冲突类型，决策文件编排路径整体休眠兜底。

### 11.4 原子发布

- 机制：候选验证通过后，使用目标文件**同文件系统**内的临时文件 + `os.replace()` 原子替换发布；目标原本不存在时也以原子创建方式发布（先写临时文件再 `os.replace()`），不得先落入半成品目标。
- 适用：OpenSpec 配置发布（OS-07/OS-N11/OS-N13）、所有需要写入目标文件的合并分支。
- 失败处理：原子替换/原子创建失败时立即终止，保持或恢复原文件（目标原本不存在时保持不存在），不得声称成功（OS-07）。
- 故障注入（design D6）：原子发布失败以目标目录 `chmod 555` 复现（`fx-readonly-target`）；备份失败以只读父目录复现（`fx-readonly-parent`）。
- 对应测试：`ut-atomic_write-publish`、`ut-atomic_write-replace`、`ut-atomic_write-fail`、`it-s7-openspec-publish-failure-preserved`。

### 11.5 模板三级定位

模板根路径与 OpenSpec 配置模板路径必须**成对定位**并在后续步骤中复用（包括步骤 8 的 `code-reading.md`、步骤 10 的 `playwright.md` 和步骤 11 的 OpenSpec 配置）。

按以下优先级顺序查找（S1b-01~04，SKILL 138-159 行）：

1. **在线安装路径**：检查 `~/.claude/plugins/marketplaces/cadence-skills-marketplace/cadence-init/skills/rule-config/references/rules/` 下是否同时存在 `agent-routing-kernel.md`、`language.md`、`openspec-superpowers-workflow.md`，并检查同一 `references/` 下的 `openspec/config.yaml`。同时存在则取 `references/rules/` 为模板根路径、`references/openspec/config.yaml` 为 OpenSpec 配置模板路径。
2. **离线安装路径**：检查 `~/.claude/plugins/marketplaces/cadence-skills-local/cadence-init/skills/rule-config/references/rules/` 下同样三件套与同 `references/` 下的 `openspec/config.yaml`。规则同上。
3. **回退搜索（开发环境）**：使用 Glob 搜索标识文件 `**/cadence-init/skills/rule-config/references/rules/language.md`，从返回结果提取目录路径（去掉末尾 `language.md`）作为候选；回退路径需额外验证 `document-storage.md` 存在（即四件套：`agent-routing-kernel.md`、`language.md`、`openspec-superpowers-workflow.md`、`document-storage.md`），并验证同 `references/` 下 `openspec/config.yaml` 存在。多候选取修改时间最新者。

**成对校验**：任一候选缺少 `references/openspec/config.yaml` 时不得选用该候选；所有候选均不完整时终止并报告缺失模板（对应测试 `ut-locate_templates-all-incomplete` / `it-s2-templates-missing`，非零退出、目标项目零写入）。

### 11.6 default_keep 语义（Task 8 裁决区分）

**2026-08-19 权威化裁决（change `rule-config-authoritative-overwrite`）**：六类原 A 类冲突全部转为**两模式确定性动作**，不再经用户决策、不再产生交互冲突：

- **RF-05 框架受管规则文件 drift**：两模式统一为屏障归档+`atomic_write` 模板（`authoritative-overwrite`）。
- **L1-04/L1-05/L1-06 协作规则 drift/unmarked**：两模式统一为备份后以框架 v1 替换。
- **L0-03 受管区块 drift**：两模式统一为纳入备份屏障后以规范源当前 v2 替换。
- **L0-06 单侧/顺序错误子分支**：与混合版本/重复区块一样按确定性安全归并执行。
- **OS-03 结构/类型不兼容、OS-05 YAML 无法解析**：两模式统一为先归档，成功后以模板内容原子替换原位。
- **OS-04 `rules.apply` 存在**：两模式统一为先备份，成功后在候选中移除并继续合并。

**当前系统无活跃冲突类型**：`default_keep` / `validate_decisions` 机制代码保留为休眠兜底，供未来引入新的冲突类型时复用；若未来重新引入冲突，须先回写本节与十张表。

**裁决依据（2026-08-19 用户裁决）**：框架受管内容以 Cadence-skills 模板为权威；归档（`cadence/legacy` 全局备份屏障）提供可恢复性，替代"保留原状"作为安全兜底。

> 说明（codex 五轮重构历史）：原 `s1:project-type-conflict` 是「检测与 CLI 矛盾时」的唯一 B 类
> fail-closed 冲突；codex 四轮曾为其补「决策消费覆盖 project_type」逻辑。五轮用户裁决删除整个
> s1 冲突机制（项目类型判定重构为两模式唯⼀规则），连带删除 `_apply_s1_decision_to_project_type`、
> 决策 schema 中 `s1` 处理与 `allowed_decisions=['coding','non-coding']`。`default_keep`/`validate_decisions`
> 机制代码本身保留（供未来冲突复用），但当时所有冲突均为 A 类保留兜底。
>
> 说明（codex 三轮 C3 纠正历史）：第二轮曾把 L0-03/06、L1-04/05/06、RF-02b 强行改为
> B 类 fail closed，理由是「其保留原状并非脚本认可的安全默认」。但这与脚本实现
> （三者 `recommendation=keep` 且 apply keep 分支不写盘）、SKILL.md「无响应→写推荐默认决策」、
> spec.md「普通模式无响应 MUST NOT 覆盖」同时矛盾，制造 C3 指出的语义冲突。三轮按方案 X
> 回归：凡 `recommendation=keep` 的冲突统一为 A 类（保留并报告 status=0）。五轮进一步删除
> s1 类型矛盾（项目类型判定重构），当时无 B 类。
>
> 说明（2026-08-19 裁决记录）：codex 三轮/五轮历史均以「保留原状」为 A 类安全默认。
> 2026-08-19 用户裁决改为：框架受管内容（RF-05、L1-04~06、L0-03、L0-06 单侧/顺序错误子分支、
> OS-03、OS-04、OS-05）以 Cadence-skills 模板为权威，两模式统一执行归档+权威处理；
> 归档提供可恢复性，替代「保留原状」作为安全兜底。原 A 类冲突清单全部清空，
> 当前系统无活跃冲突类型。

### 11.7 context 追加修正（5 行而非"四行"）

> **修正说明**：现行 `SKILL.md` 第 638 行写"在候选中将模板**四行** Cadence 协作 context 追加到现有 context"，经核对模板实际 context 为 **5 行**，"四行"系笔误。本文件按"5 行"如实记录。

**OS-N6 context 追加（修正后）**：在候选中将模板的 Cadence 协作 context（**实际 5 行**）追加到现有 context，**按完整行去重**，保留原有顺序以及项目技术栈、领域知识和其他上下文。

实现要求：

- 按完整行（含前导/尾随空白归一化后的整行）去重，不得按 token 或片段去重。
- 追加位置在现有 context 末尾；模板已存在的行不重复追加。
- 保留项目原有 context 行的原顺序与内容。
- 对应测试 `ut-merge_yaml-context-append`（断言追加按完整行去重、原顺序与项目技术栈等内容保留）。

## 12. 与 skill-clause-map.md 的交叉引用

本文件十张表的每一行均通过"对应测试 ID"列与 `tests/skill-clause-map.md` 的映射条目一一对应。交叉引用一致性要求：

- 行 ID、SKILL 行号区间、测试 ID 三者在 `merge-semantics.md`、`SKILL.md`、`skill-clause-map.md` 三处必须一致。
- 新增或修改脚本行为必须先更新本文件，再同步 `skill-clause-map.md` 的对应行（测试 ID、关键断言），保持对账可追溯。
- 已知演进点（OS-N10/OS-06 的 instructions 验证随 design D4 删除）按"标记已废止而非删除"处理，本文件与映射表同步保留行 ID。

**2026-07-30 终审对账（I-3）**：本文件"对应测试 ID"列曾与 harness 实际用例名存在 47 处悬空，已逐一处理——
改名的回写为真实用例名（如 `it-s10-playwright-*`→`it-s3-playwright-*`、`it-s4-entry-create`→`it-entry-base-created`、
`it-s4-drift-replace`→`it-s4-drift-replaced-outside-preserved`、`it-s7-openspec-publish-fail`→`it-s7-openspec-publish-failure-preserved` 等）；
真缺口的补集成用例（CS-03~06、CG-01/05/06、`it-s2-templates-missing`、`it-s3-create`、`it-s3-rules-create`、
`it-s3-code-reading-backfill`、`it-s3-l1-create`、`it-s3-l1-idempotent`、`it-s7-openspec-create`、`it-s7-openspec-backup-fail-modes`、
`it-s5-history-merge-empty`、`it-s5-history-forbidden`、`it-s6-gitignore-codegraph-idempotent`、`it-s6-codegraph-json-keep`、
`it-s4-insert`、`it-s4-upgrade`、`it-s8-codegraph-binary-missing`、`it-apply-failure-report-fields`）；
无法集成复现或行为缺口的在行内显式标注"仅单测覆盖/待补"（`it-s3-l1-upgrade`、`it-s3-l1-old-marker-drift`、
`it-s3-optional-complete`、OS-06 已废止、OS-03/OS-05 普通分支）；RF-04 框架资产统一 drift/权威全覆盖由
`ut-s3-codegraph-section-unified-drift` / `ut-s3-codegraph-section-unified-merge` 覆盖（后者名称保留，断言已改为完整模板覆盖）。

**2026-08-19 权威化对账（change rule-config-authoritative-overwrite）**：RF-05/L1-04~06/L0-03/L0-06/OS-03~05 普通模式列两模式统一为归档+权威处理；§11.6 A 类清单清空；it-s3-normal-keep-decision→it-s3-normal-authoritative-overwrite 等 7 个集成 ID 改名（清单见 skill-clause-map.md）；it-l0-drift-normal-keep-default、it-l1-drift-normal-keep-default、it-decisions-unknown、it-decisions-stale 四个用例随决策编排路径消亡移除。
