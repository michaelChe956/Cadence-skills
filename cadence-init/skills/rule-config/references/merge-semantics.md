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
6. **备份要求** — 写入前是否需要备份、备份命名、备份失败处理（见 §11.1）。
7. **报告要求** — 报告中必须出现的字段或清单（见 §11.3）。
8. **对应测试 ID** — `tests/skill-clause-map.md` 中登记的单测/集成/静态 ID，多个以 `/` 分隔。

行 ID 合计：NC-01~08（8）+ OS-01~08（8）+ L1-01~07（7）+ L0-01~07（7）+ RF-01~04（4）+ SM-01~03（3）+ OP-01~04（4）+ CS-01~08（8）+ CG-01~08（8）+ HM-01~03（3）= **60 行**。

> 每表前注来源为现行 SKILL.md 的表头与数据行号区间（以 `tests/skill-clause-map.md` §3.1 为准）。脚本实现与测试不得偏离本表语义；本文件修改必须先与 `skill-clause-map.md` 对账。

## 1. no-interrupt 权威合并规则（NC-01~08）

> 来源：现行 `SKILL.md` 第 35-50 行（"no-interrupt 权威合并规则"节，数据行 41-48，含第 50 行同名章节识别与备份命名辅助条款）。
> 适用模式：no-interrupt。同名章节识别与备份命名（NB-01/02，SKILL 50 行）为两模式共用的辅助条款，并入本表相关行的"备份要求"列与本节正文。

模板结构、必需章节、强制约束、框架规则路径和摘要引用是权威内容；当前项目内容作为补充保留。

| 行 ID | 资产 | 冲突状态 | 普通模式动作 | no-interrupt 动作 | 备份要求 | 报告要求 | 对应测试 ID |
|-------|------|----------|--------------|-------------------|----------|----------|-------------|
| NC-01 | 目标 Markdown/YAML 文件 | 目标文件不存在 | 创建标准文件（普通模式遵循不覆盖语义；此处目标本就不存在，直接创建） | 创建标准文件 | 无（无原文件可备份） | 报告新增文件路径与来源模板 | `ut-merge_markdown-target-missing` / `it-s3-create` |
| NC-02 | Markdown 文件 | 模板与项目存在不同章节 | 遵循不覆盖/冲突跳过策略；询问用户是否合并（无响应按保守默认保留项目文件） | 保留模板章节，并按原顺序保留项目独有章节 | 无（未修改项目文件时无需备份；若 no-interrupt 写入则按 §11.1 命名） | 报告保留的模板章节与项目独有章节清单 | `ut-merge_markdown-keep-project-sections` |
| NC-03 | Markdown 文件 | 模板与项目存在同名章节 | 询问是否合并；无响应保留并报告 | 模板规范在前，项目独有内容去重后追加到该章节的"项目补充" | 写入前按 §11.1 备份原文件 | 报告合并的章节名与去重后的"项目补充"行数 | `ut-merge_markdown-same-section-append` |
| NC-04 | CLAUDE.md / AGENTS.md 强制规则区 | 强制规则摘要或引用路径冲突 | 遵循 L0 受管区块处理（见 §4 L0 表）；强制规则冲突进入交互或保留并报告 | 强制规则摘要和引用路径以 `rule-config` 为准，项目技术栈、命令、业务规则和其他章节保留 | 按 L0 全局备份屏障（见 §11.2） | 报告以 rule-config 为准的摘要/路径与保留的项目章节 | `ut-merge_markdown-mandatory-override` |
| NC-05 | `openspec/config.yaml` | 配置已存在且可解析、无 `rules.apply` | 遵循 OS 表（见 §2）保守合并；交互分支见 OS-04 | 保留已有 `schema`、项目 context 和 proposal、design、specs、tasks 的额外规则，仅追加模板缺失内容 | 按 OS-B1 备份命名（见 §11.1） | 报告保留字段与新增内容清单 | `ut-merge_yaml-preserve-existing` |
| NC-06 | `openspec/config.yaml` | OpenSpec YAML 无法可靠解析或目标字段结构/类型不兼容 | 保留原文件并报告具体字段路径、实际类型和冲突，不发布候选 | 先备份；无法证明可无损规范化时终止，保持原文件不变并报告冲突；备份成功不代表允许破坏性重写 | 先成功备份原文件（§11.1）；备份失败立即终止且不修改原文件 | 报告字段路径、实际类型、冲突说明与终止原因 | `ut-merge_yaml-unparseable-abort` |
| NC-07 | 任意待合并文件 | 内容完全重复 | 跳过重复项并报告 | 只保留一份 | 无（无实质修改） | 报告去重前后的条目数 | `ut-merge_markdown-dedupe` |
| NC-08 | Markdown 文件 | Markdown 无法可靠解析 | 保留原文件并报告，不写标准结构 | 先备份，再写标准结构，并把原内容附加到"原项目补充" | 写入前按 §11.1 备份原文件 | 报告标准结构已写入、原内容位置（"原项目补充"）与备份路径 | `ut-merge_markdown-unparseable-fallback` |

**辅助条款（两模式共用）**：

- **NB-01 同名章节识别**（SKILL 50 行）：以"标题级别 + 去除开头编号后的标题文本"识别同名章节。例如 `## 1. 语言规则` 与 `## 语言规则` 视为同名；标题级别不同则不判同名。对应测试 `ut-merge_markdown-section-identity`。
- **NB-02 备份命名**（SKILL 50 行）：备份文件命名为 `<原文件名>.cadence-backup-YYYYMMDDHHMMSS`，禁止删除原始内容。命名细则见 §11.1。

## 2. OpenSpec 配置处理（OS-01~08）

> 来源：现行 `SKILL.md` 第 631-675 行（"OpenSpec 配置处理"节，数据行 666-673）；辅助条款 OS-N1~N13（SKILL 633-660 行）与 OS-B1/OS-B2（SKILL 662/675 行）并入本节正文与"备份要求/报告要求"列。
> 适用模式：两模式。OS-N 编号条款与 OS-01~08 数据行的差异仅在交互/无交互分支，详见各列。

候选在目标文件同文件系统的临时工作区构建与验证；此阶段不得直接创建、覆盖或修改目标 `openspec/config.yaml`。目标存在时以原配置为候选基础，禁止用模板整体覆盖已有配置。

| 行 ID | 资产 | 冲突状态 | 普通模式动作 | no-interrupt 动作 | 备份要求 | 报告要求 | 对应测试 ID |
|-------|------|----------|--------------|-------------------|----------|----------|-------------|
| OS-01 | `openspec/config.yaml` | 配置不存在 | 从模板构建候选，结构预检 + 四类 instructions 验证通过后原子创建 | 同普通模式（两模式同动作） | 无（无原文件）；原子创建仍须经同文件系统 `os.replace()` | 报告原子创建成功、内容来源（模板基础） | `it-s7-openspec-create` / `ut-atomic_write-publish` |
| OS-02 | `openspec/config.yaml` | 配置可解析且无 `rules.apply` | 在候选中保守合并，完整行/完整字符串去重 | 同普通模式（两模式同动作） | 按 OS-B1 备份命名（§11.1） | 报告新增 context 行、按 proposal/design/specs/tasks 分组的合并规则 | `it-s7-openspec-merge` |
| OS-03 | `openspec/config.yaml` 目标字段 | 目标字段结构/类型不兼容（根非映射、schema 非标量、context 非字符串、rules 非映射、artifact 非字符串数组等） | 保留原文件；报告字段路径、实际类型和冲突，不发布候选 | 先备份；无法证明可无损规范化则终止且保持原文件不变 | no-interrupt：先成功备份原文件（§11.1）；备份失败终止且不改原文件。普通：无需备份（不改原文件） | 报告字段路径、实际类型、冲突说明；no-interrupt 另报备份路径与终止原因 | `it-s7-openspec-incompatible-modes` |
| OS-04 | `openspec/config.yaml` 的 `rules.apply` | 存在 `rules.apply`（禁止创建的键） | 询问；无响应则保留并报告；确认移除时先创建备份，备份成功后在候选中移除并继续合并 | 先创建备份；备份成功后在候选中移除并继续合并 | 移除分支：先成功备份原文件（OS-B1，§11.1）；任何必要备份失败立即终止且不修改原文件 | 报告 `rules.apply` 处理结果（保留/移除）、备份路径；保留分支说明无虚构 apply artifact | `it-s7-openspec-apply-modes` / `it-s7-openspec-apply-remove` / `it-s7-openspec-apply-keep` |
| OS-05 | `openspec/config.yaml` | YAML 无法可靠解析 | 保留原文件并报告 | 先备份；仍无法无损合并则终止且不改原文件 | no-interrupt：先成功备份原文件（§11.1）；备份失败终止。普通：无需备份 | 报告解析冲突、原文件状态；no-interrupt 另报备份路径 | `it-s7-openspec-unparseable-modes` |
| OS-06 | 临时 Change `cadence-rule-config-validation` 的四类 instructions 验证 | 任一候选 `openspec instructions <artifact> --change cadence-rule-config-validation --json` 验证失败 | 终止并报告失败 artifact、带有 `--change cadence-rule-config-validation --json` 的实际命令和错误；原文件不变 | 同普通模式（两模式同动作） | 无（不改原文件；候选在临时工作区） | 报告失败 artifact、实际命令（含 `--change cadence-rule-config-validation --json`）、错误信息、候选清理/保留结果 | `it-s7-openspec-instructions-fail`（随 design D4 删除 instructions 验证后本行转为"结构预检失败"分支） |
| OS-07 | `openspec/config.yaml` 发布 | 原子替换/原子创建失败 | 终止并保持或恢复原文件；目标原本不存在时保持不存在；不得声称成功 | 同普通模式（两模式同动作） | 发布失败不扩大损害；已建备份保留 | 报告发布失败原因、原文件状态（保持/恢复/不存在）、明确"未声称成功" | `it-s7-openspec-publish-fail` / `ut-atomic_write-fail` |
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
- **OS-N10 临时 Change 验证**：创建固定名称为 `cadence-rule-config-validation` 的临时 Change，依次运行 `openspec instructions proposal/design/specs/tasks --change cadence-rule-config-validation --json` 四类命令，必须全部成功且输出能读取公共 context 与对应 artifact rules；不得以 `openspec instructions apply` 作为 artifact 验证。
  - **演进状态**：design D4 计划在 Task 实施中删除该 instructions 验证步骤；删除前现行语义以此为准，删除后 OS-N10/OS-06 标记为"已废止"而非从本表删除，保持对账可追溯。
- **OS-N11 原子发布**：同 OS-07；候选通过全部语法、结构、合并和四类 instructions 验证后，才允许使用同文件系统内 `os.replace()` 原子替换发布；目标原本不存在时也以原子创建方式发布，不得先落入半成品。
- **OS-N12 候选验证失败**：同 OS-06；报告失败 artifact、实际命令与错误、候选清理/保留结果，原文件不变，目标原本不存在时不得创建。
- **OS-N13 原子失败**：同 OS-07。
- **OS-B1 备份命名**：备份名固定为 `openspec/config.yaml.cadence-backup-YYYYMMDDHHMMSS`；所有需备份分支必须在写入前完成备份；备份失败时不得部分合并 context、artifact 规则或删除无效键。
- **OS-B2 完成报告清单**：逐项列出新增 context 完整行、按 proposal/design/specs/tasks 分组的合并规则、发现及处理的无效键、所有备份路径、结构冲突的具体字段路径与实际类型、解析或内容冲突、候选验证结果、失败 artifact 及其 `--change cadence-rule-config-validation --json` 实际命令与错误、候选清理/保留结果、原子发布结果、四个 `openspec instructions ... --json` 命令的验证结果；无新增内容时明确报告为幂等跳过。

## 3. L1 协作规则增量（L1-01~07）

> 来源：现行 `SKILL.md` 第 677-689 行（"OpenSpec 与 Superpowers 协作规则增量处理"节，数据行 681-687；辅助条款 L1-B1/L1-B2 在 SKILL 689 行）。
> 适用模式：两模式。

仅处理带 `cadence-framework-rule:openspec-superpowers-workflow` 标记的 L1 文件；普通规则不覆盖策略见 §5 RF 表。标记只用于候选版本定位，最终识别必须比较完整文件内容。

| 行 ID | 资产 | 冲突状态 | 普通模式动作 | no-interrupt 动作 | 备份要求 | 报告要求 | 对应测试 ID |
|-------|------|----------|--------------|-------------------|----------|----------|-------------|
| L1-01 | `.claude/rules/openspec-superpowers-workflow.md` | 文件不存在 | 创建 v1（内容与框架 v1 规范源逐字一致） | 同普通模式（两模式同动作） | 无（无原文件） | 报告创建路径与版本 v1 | `it-s3-l1-create` |
| L1-02 | 同上 | 文件完整内容与当前框架 v1 一致 | 跳过 | 同普通模式（两模式同动作） | 无（不改文件） | 报告幂等跳过、判定 `current` | `ut-classify_l1-current` / `it-s3-l1-idempotent` |
| L1-03 | 同上 | 版本标记受支持且完整内容与对应旧版规范逐字一致 | 备份后升级为当前 v1 | 同普通模式（两模式同动作） | 按 L1-B1 备份命名（§11.1）；备份失败终止且不得替换原文件 | 报告判定 `old-version`、备份路径、升级到 v1 | `ut-classify_l1-old-version` / `it-s3-l1-upgrade` |
| L1-04 | 同上 | 仅受支持旧版本标记匹配但完整内容与对应旧版规范不同 | 归入"与任何已知框架版本不匹配"；询问，无响应则保留并报告 | 归入"与任何已知框架版本不匹配"；备份后以框架 v1 替换并报告 | no-interrupt：先成功备份（L1-B1，§11.1）；备份失败终止 | 报告判定 `mismatch`（非 `old-version`）；no-interrupt 另报备份路径与替换 | `ut-classify_l1-old-marker-drift` / `it-s3-l1-old-marker-drift` |
| L1-05 | 同上 | 当前 v1 标记存在但完整内容不同 | 同 L1-04：归入"不匹配"，询问，无响应保留并报告 | 同 L1-04：归入"不匹配"，备份后以框架 v1 替换并报告 | 同 L1-04 | 报告判定 `mismatch`；不得仅凭标记当作 `current` 跳过 | `ut-classify_l1-v1-marker-drift` / `it-s3-l1-v1-marker-drift` |
| L1-06 | 同上 | 文件无标记或与已知版本不匹配 | 询问；无响应则保留并报告 | 备份后以框架 v1 替换并报告 | no-interrupt：先成功备份（L1-B1，§11.1）；备份失败终止 | 报告判定 `unmarked`；两模式分支动作符合表义 | `ut-classify_l1-unmarked` / `it-s3-l1-unmarked` |
| L1-07 | 同上任意需 L1 备份的分支 | 任何需要 L1 备份的分支备份失败 | 终止且不得替换原文件 | 同普通模式（两模式同动作） | 备份失败本身即终止条件 | 报告失败备份路径、失败原因、原文件不变 | `it-s3-l1-backup-fail` |

**辅助条款（L1-B1/L1-B2，SKILL 689 行）**：

- **L1-B1 备份命名**：固定为 `.claude/rules/openspec-superpowers-workflow.md.cadence-backup-YYYYMMDDHHMMSS`。
- **L1-B2 标记仅用于定位**：`cadence-framework-rule:openspec-superpowers-workflow` 标记只用于候选版本定位；最终识别必须比较完整文件内容，不得仅凭标记把文件识别为当前或受支持旧版，也不得把无标记文件当作已知框架版本覆盖。

## 4. L0 入口增量（L0-01~07）

> 来源：现行 `SKILL.md` 第 691-711 行（"CLAUDE.md / AGENTS.md 入口增量处理"节，数据行 699-705；屏障与受管区块外保留条款 L0-B1/L0-B2 在 SKILL 691-694、707 行）。L0-P1~P12 处理流程条款在 SKILL 185-200 行，与本表互证。
> 适用模式：两模式。

写入入口文件前必须先完成双入口统一预检，确定两个入口的标记、版本、完整内容、交互结果、目标动作和全部备份需求；在写入任一入口前创建本次所需的全部 L0 备份，仅当全部必要备份成功后才按下表执行各入口动作。任一必要备份失败时 CLAUDE.md 与 AGENTS.md 均不得写入。

| 行 ID | 资产 | 冲突状态 | 普通模式动作 | no-interrupt 动作 | 备份要求 | 报告要求 | 对应测试 ID |
|-------|------|----------|--------------|-------------------|----------|----------|-------------|
| L0-01 | CLAUDE.md / AGENTS.md | 入口不存在 | 创建基础入口并插入当前 v1（L0 放在文件说明之后、`## 强制规则` 之前） | 同普通模式（两模式同动作） | 无（无原文件） | 报告创建路径、L0 版本 v1、插入位置 | `it-s4-entry-create` |
| L0-02 | 入口的 L0 受管区块 | 当前 v1 区块与规范源完整一致 | 跳过，不重复写入 | 同普通模式（两模式同动作） | 无（不改区块） | 报告幂等跳过；双入口 sha256 不变 | `it-s4-idempotent` |
| L0-03 | 同上 | 当前 v1 标记成对但完整受管区块与规范源不同 | 视为无法识别的本地修改；询问，无响应则保留并报告 | 先备份，成功后替换为规范源当前 v1 并报告 | no-interrupt：先成功备份（§11.1）；普通确认替换分支：将该入口纳入本次备份屏障。任一必要备份失败双入口均不得写入 | 报告判定"本地修改"；no-interrupt 另报备份路径与替换 | `it-s4-drift-normal` / `it-s4-drift-replace` |
| L0-04 | 同上 | 受支持旧版本标记成对 | 备份成功后升级到当前 v1 并报告 | 同普通模式（两模式同动作） | 将该入口纳入本次备份屏障（§11.2）；屏障失败双入口均不得写入 | 报告备份路径、升级到 v1 | `it-s4-upgrade` |
| L0-05 | 同上 | 无 L0 标记 | 插入当前 v1，入口原内容保留 | 同普通模式（两模式同动作） | 无（不改原内容，仅插入） | 报告插入位置；原内容 sha256 不变 | `it-s4-insert` |
| L0-06 | 同上 | 单侧标记或标记顺序错误 | 询问；无响应则保留并报告 | 先备份，成功后写入单一当前 v1 区块并报告 | no-interrupt：先成功备份（§11.1）。任一必要备份失败双入口均不得写入 | 报告处理后标记成对且唯一；区块外内容保留 | `it-s4-broken-markers` |
| L0-07 | 同上任意需 L0 备份的分支 | 任何 L0 备份失败 | 终止本次 L0 更新，CLAUDE.md 与 AGENTS.md 均不得写入 | 同普通模式（两模式同动作） | 备份失败本身即终止条件（全局屏障，见 §11.2） | 报告失败备份路径、失败原因、双入口零写入 | `it-s4-backup-barrier-modes` |

**辅助条款（L0-B1/L0-B2；L0-P1~P12 互证）**：

- **L0-B1 统一预检 + 全局备份屏障**（SKILL 691-694 行；与 L0-P2~P4 在 SKILL 190-192 行互证）：写入任一入口前先按"L0 受管区块处理"完成双入口统一预检，确定两个入口的标记、版本、完整内容、交互结果、目标动作和全部备份需求；在写入任一入口前创建本次所需的全部 L0 备份；仅当统一预检和全部必要备份成功后才允许按各入口分支写入；任一必要备份失败时双入口均不得写入，区块内外保持原样。细则见 §11.2。
- **L0-B2 区块外内容保留**（SKILL 707 行）：所有场景必须保持 L0 受管区块外的项目技术栈、命令、业务规则和用户内容原样。
- **L0 版本一致性**（L0-P12，SKILL 200 行）：CLAUDE.md 与 AGENTS.md 必须使用相同 L0 版本和语义。

## 5. 规则文件增量（RF-01~04）

> 来源：现行 `SKILL.md` 第 606-629 行（"规则文件增量处理"节，数据行 612-615）。
> 适用模式：两模式。本表适用于普通规则，不改变已有的"不自动覆盖"语义；`openspec-superpowers-workflow.md` 仅按 §3 L1 表版本化特例处理。

| 行 ID | 资产 | 冲突状态 | 普通模式动作 | no-interrupt 动作 | 备份要求 | 报告要求 | 对应测试 ID |
|-------|------|----------|--------------|-------------------|----------|----------|-------------|
| RF-01 | `.claude/rules/*.md` 普通规则文件 | 文件不存在 | 从模板根路径读取并创建 | 同普通模式（两模式同动作） | 无（无原文件） | 报告创建路径与来源模板 | `it-s3-rules-create` |
| RF-02 | 同上 | 文件已存在 | 不自动覆盖，报告已存在 | 同普通模式（两模式同动作） | 无（不改文件） | 报告"已存在"；原文件 sha256 不变 | `it-s3-rules-no-overwrite` |
| RF-03 | `.claude/rules/code-reading.md` | 新增 `code-reading.md`（老项目补齐） | 所有项目默认新增；非 Coding 仅跳过 CodeGraph 初始化 | 同普通模式（两模式同动作） | 无（新增，无原文件） | 报告补齐 `code-reading.md`；非 Coding 记录跳过 CodeGraph 初始化 | `it-s3-code-reading-backfill` |
| RF-04 | 已存在的普通规则文件 | 规则文件已存在但缺少 CodeGraph 段落 | 不自动覆盖，报告需要用户手动合并 | 同普通模式（两模式同动作） | 无（不改文件） | 报告文件路径与"需用户手动合并 CodeGraph 段落"提示 | `it-s3-codegraph-section-missing` |

## 6. 摘要引用增量（SM-01~03）

> 来源：现行 `SKILL.md` 第 713-717 行（"CLAUDE.md / AGENTS.md 入口增量处理"节末"其他规则摘要仍按以下策略增量处理"表，数据行 715-717）。
> 适用模式：两模式。摘要引用的 L0 受管区块本身按 §4 L0 表处理；本表仅处理摘要行。

| 行 ID | 资产 | 冲突状态 | 普通模式动作 | no-interrupt 动作 | 备份要求 | 报告要求 | 对应测试 ID |
|-------|------|----------|--------------|-------------------|----------|----------|-------------|
| SM-01 | CLAUDE.md / AGENTS.md 的规则摘要行 | 摘要行已存在 | 跳过，不重复写入 | 同普通模式（两模式同动作） | 无（不改文件） | 报告摘要行只出现一次；文件其余内容不变 | `it-s4-summary-idempotent` |
| SM-02 | 同上 | 摘要行缺失 | 追加到 `## 强制规则` 章节末尾 | 同普通模式（两模式同动作） | 无（追加单行；L0 区块本身按 L0 表处理） | 报告追加位置（`## 强制规则` 章节末尾）与摘要内容 | `it-s4-summary-append` |
| SM-03 | 同上 | 规则编号与现有内容冲突 | 不覆盖原内容，追加缺失摘要并在报告中说明可能需要人工整理编号 | 同普通模式（两模式同动作） | 无（不改原编号行） | 报告保留的原编号行、追加的缺失摘要、"可能需人工整理编号"提示 | `it-s4-summary-number-conflict` |

## 7. 可选规则增量（OP-01~04）

> 来源：现行 `SKILL.md` 第 719-728 行（"可选规则增量处理"节，数据行 725-728）。
> 适用模式：两模式。

| 行 ID | 资产 | 冲突状态 | 普通模式动作 | no-interrupt 动作 | 备份要求 | 报告要求 | 对应测试 ID |
|-------|------|----------|--------------|-------------------|----------|----------|-------------|
| OP-01 | 可选规则文件 + 摘要（code-reading / playwright 等） | 规则文件和摘要均已存在 | 视为已启用，仅检查完整性 | 同普通模式（两模式同动作） | 无（不改文件） | 报告完整性检查结果；文件与摘要不重写 | `it-s3-optional-complete` |
| OP-02 | `.claude/rules/code-reading.md` | 代码阅读规则缺失 | 所有项目默认新增；非 Coding 仅跳过 CodeGraph 初始化 | 同普通模式（两模式同动作） | 无（新增） | 报告规则文件补齐；非 Coding 记录跳过 CodeGraph 初始化 | `it-s3-code-reading-backfill` |
| OP-03 | `.claude/rules/playwright.md` | Playwright 规则缺失 | 默认跳过，用户明确要求时新增 | 同普通模式（两模式同动作；no-interrupt 下"用户明确要求"由意图参数 `--enable-playwright` 表达） | 无（默认跳过；新增时无原文件） | 报告默认跳过或按 `--enable-playwright` 新增 | `it-s10-playwright-skip` / `it-s10-playwright-enable` |
| OP-04 | 可选规则历史选择 | 无法判断历史选择 | 按本节默认值处理，不询问 | 同普通模式（两模式同动作；no-interrupt 本就不询问） | 无（不询问，不改文件） | 报告按默认值执行；不生成提问冲突项 | `it-s3-optional-default-no-ask` |

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
| CS-07 | 同上 | `codegraph install` 失败 | 提供 `mcp-configuration.md` 手动兜底配置，并分别补齐 `.mcp.json` 与 `.codex/config.toml` | 同普通模式（两模式同动作）；步骤标记 `degraded` 并继续，补写/备份/原子写失败仍终止（design D3） | 同 CS-04 | 报告步骤状态 `degraded`、两文件由脚本补齐、整体不因此失败 | `it-s8-codegraph-install-fail` |
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
| HM-01 | `.claude/<dir>` → `cadence/<dir>`（16 个历史目录之一） | `cadence/<dir>` 不存在 | 将 `.claude/<dir>` 移动到 `cadence/<dir>` | 不执行迁移（按 NH-02 仅报告） | 无（mv 不要求备份；目标为空目录） | 报告源不存在、目标内容一致 | `it-s5-history-move` |
| HM-02 | 同上 | `cadence/<dir>` 已存在且为空 | 将 `.claude/<dir>` 的内容移动到 `cadence/<dir>`，并清理空源目录 | 不执行迁移（按 NH-02 仅报告） | 无 | 报告全部条目移入目标；源目录被移除或为空 | `it-s5-history-merge-empty` |
| HM-03 | 同上 | `cadence/<dir>` 已存在且非空 | 跳过该目录并报告冲突，要求用户手动处理 | 不执行迁移（按 NH-02 仅报告） | 无（不移动） | 报告源与目标均不变；含冲突目录与手动处理提示 | `it-s5-history-conflict-skip` |

**辅助条款（NH-01~03，SKILL 54-56 行；no-interrupt 专用）**：

- **NH-01 检测清单**：no-interrupt 只检测 16 个精确历史目录：`.claude/prds`、`.claude/analysis`、`.claude/analysis-docs`、`.claude/docs`、`.claude/designs`、`.claude/designs-reviews`、`.claude/plans`、`.claude/readmes`、`.claude/modaos`、`.claude/models`、`.claude/architecture`、`.claude/notes`、`.claude/logs`、`.claude/reports`、`.claude/project-rules`、`.claude/cache`。清单外同名目录不检出。对应测试 `it-s5-history-detect-list`。
- **NH-02 仅报告不动手**：检测到历史目录仅写入执行报告，不执行 `mv`、目录内容合并、目录删除或空目录清理。对应测试 `it-s5-history-no-interrupt`。
- **NH-03 模式归属**：本规则只覆盖 no-interrupt；普通模式继续执行 HM-01~03 的历史产物迁移步骤。对应测试 `it-s5-history-normal`。
- **禁止迁移**（S6-01，SKILL 435-437 行）：普通模式下禁止迁移 `.claude/rules`、`.claude/commands`、`.claude/skills`。对应测试 `it-s5-history-forbidden`。

## 11. 横切契约与辅助正文

以下条款为十张表共用的横切规则，脚本实现与 Agent 行为均必须遵守。

### 11.1 备份命名

- 通用命名：`<原文件名>.cadence-backup-YYYYMMDDHHMMSS`（时间戳为 14 位 `YYYYMMDDHHMMSS`，本地时区），禁止删除原始内容。
- 固定命名（按资产）：
  - OpenSpec 配置：`openspec/config.yaml.cadence-backup-YYYYMMDDHHMMSS`（OS-B1）。
  - L1 协作规则：`.claude/rules/openspec-superpowers-workflow.md.cadence-backup-YYYYMMDDHHMMSS`（L1-B1）。
  - L0 入口：`CLAUDE.md.cadence-backup-YYYYMMDDHHMMSS` / `AGENTS.md.cadence-backup-YYYYMMDDHHMMSS`（按通用命名）。
- 备份与写入关系：所有需要备份的分支都必须在写入前完成备份；备份失败时不得部分合并、不得删除无效键、不得修改原文件。备份成功不等于允许破坏性重写（NC-06/OS-03 反复强调）。
- 测试基线：备份文件名匹配正则 `.*\.cadence-backup-[0-9]{14}$`；原文件仍在（`ut-backup_file-naming`、`ut-backup_file-openspec-naming`、`ut-backup_file-l1-naming`）。

### 11.2 全局备份屏障

L0 入口更新采用**全局备份屏障**：写入任一入口前，先对 CLAUDE.md 与 AGENTS.md 完成本次所需的全部 L0 备份；仅当统一预检和全部必要备份成功后，才允许按各入口分支写入；任一必要备份失败时双入口均不得写入，区块内外保持原样。

屏障的执行顺序（对应 `step_entry_files` 实现）：

1. `compute_plan` — 对双入口执行统一预检，确定标记/版本/完整内容/交互结果/目标动作/全部备份需求。
2. 全量备份 — 一次性创建本次预检出的所有必要 L0 备份（CLAUDE.md 与 AGENTS.md 各自需要的备份）。
3. 发布 — 仅当步骤 2 全部成功后，才按 L0 表分支写入对应入口。

屏障失败语义：步骤 2 任一备份失败 → 步骤 3 不执行，双入口零写入，已建备份不扩大损害（不回滚已成功备份，但不再写入入口）。对应测试 `it-s4-backup-barrier` / `it-s4-backup-barrier-modes`（L0-P4 / L0-07 / L0-B1 互证）。OpenSpec（OS-N4/OS-08）与 L1（L1-07）各自有等价的"必要备份失败即终止"屏障，但不跨资产；只有 L0 是跨双入口的全局屏障。

### 11.3 报告要求（失败关闭与 schema）

**失败关闭**：必调 Skill、OpenSpec 契约、实施 Plan 或新鲜验证证据缺失时停止，不得降级绕过。脚本层面的失败关闭体现为：任一必要备份失败、原子发布失败、候选验证失败、结构/类型不兼容无法证明无损规范化时，立即非零退出且零写入（或保持/恢复原文件），报告必须包含失败文件、失败原因、已完成项目和恢复建议（NR-04/NR-05，SKILL 32-33 行）。

**失败报告字段**（NR-05，SKILL 33 行）：必须含失败文件、失败原因、已完成项目（逐项列出）、恢复建议。对应测试 `it-apply-failure-report-fields`。

**成功完成报告**（OS-B2，SKILL 675 行）：逐项列出新增 context 完整行、按 artifact 分组的合并规则、无效键处理、所有备份路径、结构冲突字段路径与实际类型、解析或内容冲突、候选验证结果、失败 artifact 及实际命令、候选清理/保留结果、原子发布结果、四类 instructions 命令结果；无新增内容时明确报告"幂等跳过"。

**决策文件 schema**（design D3 横切契约 XC-03，普通模式 apply 入口）：

- **conflict_id 格式**：`<step>:<资产>[:<分支>]`。`<step>` 为步骤标识（如 `s1`、`s3`、`s4`、`s7`）；`<资产>` 为受冲突的文件或配置块标识；可选 `<分支>` 用于同步骤同资产的多分支冲突。
- **decision 枚举**：按资产类型取值：
  - 普通规则文件覆盖冲突：`replace` / `keep`（IA-01，对应测试 `it-apply-decision-keep`）。
  - OpenSpec `rules.apply`：`remove_apply` / `keep`（OS-04）。
  - L1 协作规则不匹配：`replace_v1` / `keep`（L1-04/L1-05/L1-06）。
  - L0 受管区块漂移：`replace_v1` / `keep`（L0-03/L0-06）。
  - 项目类型检测矛盾：`non-coding` / `coding`（IA-02，固定冲突标识 `s1:project-type-conflict`）。
- **allowed_decisions**：每个 conflict_id 的 decision 必须在其资产类型对应的枚举内；超出枚举的决策视为非法。
- **default_keep 语义**（见 §11.6 详细说明）：普通模式下，缺失决策的默认动作因资产类型而异。

**decisions 四类异常**（XC-03）：任一即非零退出且零写入——

1. 决策文件缺失或无法解析（普通模式提供决策文件时）。
2. 决策含未知或重复 `conflict_id`。
3. 计划存在的冲突缺少对应决策。
4. 决策与新鲜计划不符（stale）。

计划无冲突时不要求决策文件；no-interrupt 模式不读取也不要求决策文件，全部冲突按十张表内部规则决策（XC-04，对应测试 `it-apply-no-interrupt-no-decisions`）。

### 11.4 原子发布

- 机制：候选验证通过后，使用目标文件**同文件系统**内的临时文件 + `os.replace()` 原子替换发布；目标原本不存在时也以原子创建方式发布（先写临时文件再 `os.replace()`），不得先落入半成品目标。
- 适用：OpenSpec 配置发布（OS-07/OS-N11/OS-N13）、所有需要写入目标文件的合并分支。
- 失败处理：原子替换/原子创建失败时立即终止，保持或恢复原文件（目标原本不存在时保持不存在），不得声称成功（OS-07）。
- 故障注入（design D6）：原子发布失败以目标目录 `chmod 555` 复现（`fx-readonly-target`）；备份失败以只读父目录复现（`fx-readonly-parent`）。
- 对应测试：`ut-atomic_write-publish`、`ut-atomic_write-replace`、`ut-atomic_write-fail`、`it-s7-openspec-publish-fail`。

### 11.5 模板三级定位

模板根路径与 OpenSpec 配置模板路径必须**成对定位**并在后续步骤中复用（包括步骤 8 的 `code-reading.md`、步骤 10 的 `playwright.md` 和步骤 11 的 OpenSpec 配置）。

按以下优先级顺序查找（S1b-01~04，SKILL 138-159 行）：

1. **在线安装路径**：检查 `~/.claude/plugins/marketplaces/cadence-skills-marketplace/cadence-init/skills/rule-config/references/rules/` 下是否同时存在 `agent-routing-kernel.md`、`language.md`、`openspec-superpowers-workflow.md`，并检查同一 `references/` 下的 `openspec/config.yaml`。同时存在则取 `references/rules/` 为模板根路径、`references/openspec/config.yaml` 为 OpenSpec 配置模板路径。
2. **离线安装路径**：检查 `~/.claude/plugins/marketplaces/cadence-skills-local/cadence-init/skills/rule-config/references/rules/` 下同样三件套与同 `references/` 下的 `openspec/config.yaml`。规则同上。
3. **回退搜索（开发环境）**：使用 Glob 搜索标识文件 `**/cadence-init/skills/rule-config/references/rules/language.md`，从返回结果提取目录路径（去掉末尾 `language.md`）作为候选；回退路径需额外验证 `document-storage.md` 存在（即四件套：`agent-routing-kernel.md`、`language.md`、`openspec-superpowers-workflow.md`、`document-storage.md`），并验证同 `references/` 下 `openspec/config.yaml` 存在。多候选取修改时间最新者。

**成对校验**：任一候选缺少 `references/openspec/config.yaml` 时不得选用该候选；所有候选均不完整时终止并报告缺失模板（对应测试 `ut-locate_templates-all-incomplete` / `it-s2-templates-missing`，非零退出、目标项目零写入）。

### 11.6 default_keep 语义（Task 8 裁决区分）

普通模式下，决策缺失时的默认动作因资产类型的安全可恢复性而异，脚本与文档必须如实区分：

**A. 有安全默认的冲突 → 保留并报告（status=0）**：

- `rules.apply`（OS-04）：普通模式询问，**无响应则保留原文件并报告**，不阻塞流程，步骤状态 `status=0`。
- OpenSpec 结构/类型不兼容（OS-03）、OpenSpec YAML 无法解析（OS-05）：普通模式**保留原文件并报告**，不发布候选；这不阻塞其他步骤，相关步骤状态 `status=0`。
- 普通规则文件覆盖冲突（RF-02、IA-01）：普通模式询问，**无响应则不覆盖、保留并报告**，`status=0`。
- L1 协作规则不匹配（L1-04/L1-05/L1-06）、L0 受管区块漂移（L0-03/L0-06）：普通模式询问，**无响应则保留并报告**，`status=0`。

**B. 无安全默认的冲突 → fail closed（非零退出）**：

- 规则文件 drift（RF-04：已存在但缺 CodeGraph 段落）在普通模式下不自动覆盖，但若决策缺失导致无法推进关键路径时按 fail closed 处理。
- L0 入口 drift（L0-03/L0-06）：若普通模式无响应**且**该入口是后续步骤的硬依赖（如 L0 受管区块必须存在才能写入摘要），缺失决策时 fail closed，不得继续。
- L1 drift（L1-04/L1-05/L1-06）：若普通模式无响应**且**该 L1 文件是必调 Skill 路由的硬依赖，缺失决策时 fail closed。
- s1 类型矛盾（IA-02，固定冲突标识 `s1:project-type-conflict`）：检测结果互相矛盾且影响规则选择时，**无决策时 apply 拒绝**（fail closed），dry-run 报告含 `s1:project-type-conflict`；decision=`non-coding`/`coding` 时按对应类型执行。

**区分原则**：当冲突的"保留原状"是安全可恢复的（如不覆盖文件、不移除 `rules.apply`、保留无法解析的配置），缺失决策默认保留并报告，`status=0`；当冲突的"保留原状"会导致后续步骤无法安全进行（如类型矛盾使规则选择无法确定、drift 使必调路由依赖断裂），缺失决策 fail closed。脚本实现必须在 `compute_plan` 阶段对每个冲突标注其 default_keep 归属（A 或 B），并在报告中明示。

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
