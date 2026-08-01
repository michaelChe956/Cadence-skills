## Context

`rule-config` 当前对 `.claude/rules/` 下框架规则文件采用 `merge_markdown` 章节级保守合并（NC-02/NC-03），把"被模板取代的旧内容"当作"项目独有内容"追加到 `**项目补充**`。该合并基于一个错误前提：框架规则文件可承载项目定制。但项目规则早已规定"禁止直接修改 `.claude/rules/` 下框架规则文件、用户自定义规则只能放在 `cadence/project-rules/`"，前提与现实不符，导致合并复杂度与全部污染。

备份机制现为同目录 `<原文件名>.cadence-backup-<14 位时间戳>` 副本（`backup_file`，`shutil.copy2`），散落在 `.claude/rules/`、项目根等处，无统一归档目录，且与"禁止删除原始内容"的原地可恢复语义绑定。

实测（naruto 执行 `rule-config no-interrupt`）暴露：Serena MCP 整段复活、模板已更新措辞的旧行重复、入口摘要块重复追加、`code-usage.md` 引用断链（落地的是 `code-usage-coding.md`/`code-usage-noncoding.md` 两个互斥模板）、`agent-routing-kernel.md` 既作 L0 插入源又被复制为规则文件的矛盾。

术语澄清：现有 `managed-rule-lifecycle` spec 中"规则层集成不得依赖 legacy"的 "legacy" 指 `cadence-workflow` 遗留框架；本设计的 `cadence/legacy/` 是备份归档目录，二者无关。

## Goals / Non-Goals

**Goals:**
- 把框架规则文件从"保守合并"切换为"框架权威全覆盖"，消灭 `**项目补充**` 及其全部污染。
- 统一备份为 `cadence/legacy/` 复制归档 + 原子覆盖，不纳入版本控制。
- 修复 `code-usage.md` 引用断链与 `agent-routing-kernel.md` 定位矛盾。
- 建立并验证"执行 N 次 = 执行 1 次"的幂等契约。
- 修复摘要重复追加与技术栈占位卡死两个连带 bug。

**Non-Goals:**
- 不改动 `pre-check` skill（校对未发现其产物问题）。
- 不改 L0 受管区块的插入/区块外保留语义、不改 `openspec/config.yaml` 的保守合并语义、不改 L1 的版本识别语义（这三类保留原语义）。
- 不主动清理业务项目里既有的污染产物（如 naruto 已生成的 Serena 段落）--新设计只保证后续运行幂等；对执行 `rule-config` 的受管文件，权威覆盖会替换旧污染并归档原文件，但不对未运行 `rule-config` 的项目批量扫描清理。历史清理留给项目自行处理。
- 不改 `.mcp.json`/`.codex/config.toml` 的 MCP 配置写入逻辑（它们承载用户密钥，非框架权威内容）。

## Decisions

### D1. 资产三分法

按"是否承载项目特定内容"将资产分三类，分别用不同写入语义：

| 类别 | 资产 | 写入语义 | 理由 |
|---|---|---|---|
| 框架权威全覆盖 | `.claude/rules/` 下框架受管规则文件（`mcp-servers.md`/`code-reading.md`/`document-storage.md`/`language.md`/`markdown-format.md`/`code-usage.md`/`playwright.md`） | 内容=模板则跳过；否则归档原文件+写模板 | 框架产物，项目定制应走 `cadence/project-rules/` |
| 版本化特例 | `openspec-superpowers-workflow.md`（L1） | 保留 `classify_l1` 版本识别与升级 | 有跨版本升级能力，全覆盖会丢失 |
| 保留原语义 | `CLAUDE.md`/`AGENTS.md`（L0）、`openspec/config.yaml`（OS） | L0 插入/区块外保留；OS 保守合并 | 含真实用户内容/项目配置字段 |

**备选**：全部资产统一全覆盖。**否决**：L0 入口含项目技术栈/命令/业务说明，OS 配置含项目 context 与自定义规则，整体覆盖会丢用户数据，违反 L0-B2 与 OS 保守合并契约。

### D2. `cadence/legacy/` 复制归档 + 原子覆盖

- 路径：`cadence/legacy/<14 位时间戳>/<相对项目根路径>`，如 `cadence/legacy/20260801021957/.claude/rules/mcp-servers.md`。同秒冲突在时间戳目录后追加 `-2`/`-3`（形如 `<时间戳>-2/<相对路径>`）。
- 机制：`shutil.copy2` 原文件到归档路径（原位文件不动）-> `atomic_write` 新内容 `os.replace` 原子替换原位。归档复制失败即终止，原文件不动；`atomic_write` 失败时 `os.replace` 原子性保证原文件不变，已归档副本保留供恢复，无需回滚逻辑。
- `.gitignore`：在 `cadence/legacy/` 内创建，内容为 `*` 换行 `!.gitignore`（忽略全部条目但保留 `.gitignore` 自身）。每次运行归档前验证该文件存在且内容正确，缺失/损坏则修复。
- 统一适用：规则文件、L0 入口、L1、OS config.yaml 的全部备份分支都改用此机制，`backup_file` 单一实现。
- 双入口屏障事务性：L0 双入口先全部复制归档，全部成功后才依次 `atomic_write` 覆盖；任一归档失败则不写入任一入口（原文件未动）；任一 `atomic_write` 失败则该入口原文件不变（原子性），另一入口已写入的保持新内容（各自独立原子操作）。这规避了"移动"语义下"原文件已消失、新内容未写入"的窗口与回滚复杂度。

**备选 A**：保留原地 `.cadence-backup-` 副本，仅规则文件走 `cadence/legacy/`。**否决**：两套备份机制并存增加维护成本与测试矩阵。
**备选 B**：`shutil.move` 原文件到归档 + write 新内容。**否决**（reviewer B2）：move 后原文件从原路径消失，若后续步骤失败（双入口第二个 move 失败、或 write 失败），需回滚逻辑把文件从归档移回，事务复杂且易错；复制+atomic_write 利用 `os.replace` 原子性天然规避此问题，效果等价（原位被新内容替换、归档有旧内容副本）。

### D3. `code-usage.md` 按项目类型单选来源 + 恒定落地名

- 来源映射：Coding -> `references/rules/code-usage-coding.md`，非 Coding -> `references/rules/code-usage-noncoding.md`。
- 落地名恒为 `.claude/rules/code-usage.md`，与 L0 规范源、`RULE2_TEXT_*` 摘要的引用一致。
- 项目类型变化时：归档原 `code-usage.md` + 以新类型模板整体覆盖。两个模板语义互斥（"遵循 TDD 先写测试" vs "非必要不编写代码"），MUST NOT 合并。
- 遗留的 `code-usage-coding.md`/`code-usage-noncoding.md`（框架错误生成产物）：归档到 `cadence/legacy/` 后从 `.claude/rules/` 移除。

**备选**：落地名带后缀（`code-usage-coding.md`）。**否决**：L0 规范源 `agent-routing-kernel.md` 路由表与 `RULE2_TEXT_*` 常量都引用 `code-usage.md`，带后缀会维持死链。

### D4. `agent-routing-kernel.md` 从受管规则文件清单移除

从 `ORDINARY_RULE_FILES` 移除，仅作 L0 插入源。这解决模板 `README.md`"不复制到 `.claude/rules/`"与脚本实际复制的矛盾，同时避免 L0 区块内容以规则文件形式重复存在于 `.claude/rules/`。

### D5. 幂等契约：归一化 + 比对再写

所有受管资产写入统一为"先归一化到目标内容，与现文件比对，相同则跳过，不同则归档+写"：

| 资产 | 目标内容 | 幂等判据 |
|---|---|---|
| 框架规则文件 | 模板内容 | `现内容 == 模板` 则跳过 |
| `code-usage.md` | 当前类型对应模板 | `现内容 == 目标模板` 则跳过 |
| L0 区块 | 规范源 v1 | `skip` 状态（已一致）则不写 |
| 摘要行 | 指向各规则文件的引用存在 | 已存在引用则不追加 |
| 技术栈块 | 逐项：占位->检测值，真实值->保留 | 详见 D6 |

第二次执行时所有资产目标内容已等于现内容 -> 全跳过，不产生归档。保证 `run(N) == run(1)`。

### D6. 摘要与技术栈的幂等修复

- **摘要**：`_ensure_summary_lines` 缺失判据由"整行精确措辞匹配"改为"强制规则章节内是否已存在指向该规则文件名的引用"。规则 6 多行块改为"块首行已存在则跳过，首行缺失才整块处理"。同一规则文件在章节中只被引用一次。
- **规则 2 摘要**：保留现有 `_compose_entry` 步骤 2 的 `replace` 逻辑（按类型移除另一类型行+写入当前类型行），已幂等。
- **技术栈**：`_ensure_techstack_block` 逐项判断。占位集合 = `{"待确认", "未检测到"}`。某项为占位且检测到值 -> 替换；某项为占位且未检测到 -> 保持；某项为非占位真实值 -> 保留，检测值不同仅报告提示。区块整体缺失 -> 追加完整区块。

**备选**：技术栈"块内容 ≠ 检测值就整体替换"。**否决**：会覆盖用户手填值（如用户补的 `pnpm lint`），且技术栈区在 L0 区块外，受 L0-B2 保护，不应权威覆盖。

## Risks / Trade-offs

- **[框架规则文件全覆盖丢失项目侧改写]** -> 项目定制本就该在 `cadence/project-rules/`，且原文件副本归档到 `cadence/legacy/` 可恢复。设计上可接受。
- **[项目类型检测不稳定导致 `code-usage.md` 反复切换]** -> 类型检测基于有界扫描+工程配置文件，稳定；且每次切换都有归档，不丢数据。若检测抖动，报告会显式提示类型变化。
- **[`cadence/legacy/` 术语与现有 spec "legacy" 冲突]** -> design 与 spec 已显式澄清二者无关；`cadence/legacy/` 是目录名，spec 中的 "legacy" 指 `cadence-workflow` 遗留框架。
- **[复制归档+原子覆盖改变 §11.1/§11.2 备份契约]** -> `backup_file` 重构为复制归档 + `atomic_write` 原子覆盖，§11.1 命名、§11.2 L0 全局屏障、OS-08/L1-07 屏障都需同步改写；测试需覆盖归档失败与 `atomic_write` 失败分支（后者原文件不变）。
- **[历史污染产物不自动清理]** -> 新设计只保证后续幂等，业务项目既有污染（如 naruto 的 Serena 段落）需项目自行重跑或手动清理。已列入 Non-Goals。

## Migration Plan

1. 重构 `backup_file` 为 `cadence/legacy/` 复制归档 + `atomic_write` 原子覆盖，保留同秒 `-N` 目录后缀逻辑。
2. 重构 S3 规则文件步骤：全覆盖分支（跳过 `merge_markdown`），`code-usage.md` 按类型单选，移除 `agent-routing-kernel.md`。
3. 修复 `_ensure_summary_lines`（引用存在性判据）、`_ensure_techstack_block`（逐项占位替换）。
4. 同步 `merge-semantics.md`（NC-02/03 适用范围、RF 表权威覆盖行、SM 表、§11.1/§11.2）、`SKILL.md` 概述。
5. 更新 `tests/test_rule_config.py` 与 `skill-clause-map.md`，新增幂等回归（连续两次 apply 断言产物一致、无新归档）。
6. 回滚：若新机制出现问题，因覆盖前均归档原文件到 `cadence/legacy/`，可从归档恢复；脚本层可回退到上一版本。

## Open Questions

无。所有影响 specs 或任务分解的决策已在 brainstorming 阶段与用户确认。
