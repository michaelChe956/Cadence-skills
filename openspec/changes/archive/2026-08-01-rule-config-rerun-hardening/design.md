# Design: rule-config-rerun-hardening

## Context

见 proposal.md - Why。关键现状（均已代码实证）：

- `rule-config.py` 的 `merge_markdown`（约 741-842 行）在注入项目补充时使用魔法字符串 `**项目补充**`（约 806-809 行），无 marker pair；重跑时该标记行不在模板行集合中，被项目独有行过滤（约 797-800 行）保留后再注入新标记 → 重复。`_dedup_lines_preserve_order` 使重复标记封顶在 2 个，但 run1 ≠ run2，不幂等成立。
- 对照：L0/L1 受管区块均有可识别、可剥离的 marker pair，重跑天然幂等；项目补充协议缺这一层。
- RF-04 特判位于 `compute_plan`（约 1418-1437 行）与 `step_s3`（约 2074-2080 行），判定条件为全文 substring `"CodeGraph" not in existing_text`，两模式 report-only。
- dry-run 冲突条目的 `recommendation` 在 `compute_plan` 中恒为安全默认 `keep`，不随模式分支。

## Goals / Non-Goals

- Goals：章节合并重跑幂等且自愈；no-interrupt 报告不误导；缺 CodeGraph 段落文件零人工自动合并；补齐重跑幂等回归测试。
- Non-Goals：不改变普通模式冲突询问流程；不做脚本单文件拆分与近似行去重（P2）；不改动 L0/L1 合并路径。

## Decisions

### D1：幂等修复采用最小修复（排除保留字），不引入 marker pair

在 `merge_markdown` 的项目独有行过滤中排除 `line.strip() == "**项目补充**"` 的标记行；标记字符串提升为模块级常量（如 `PROJECT_SUPPLEMENT_MARKER`）供注入与过滤共用，杜绝两处字面量漂移。

- **为何选 A 而非 B（结构化 marker pair）**：B 改变所有已合并文档的可见输出格式、需改 NC-03 契约并加旧格式兼容逻辑（否则存量文件中的裸标记会泄漏为项目行），成本远大于收益。保留字被用户真实手写的概率极低，即便出现，被规范化进补充区语义也合理。
- **自愈特性**：已污染文件下次合并时，重复标记被过滤、仅重新注入一个 → 无需用户手动恢复备份。
- **备选考虑**：C（在 project_only 收集时识别并跳过上一次注入的整个补充区块）——与 A 等效但逻辑更复杂，且 A 已能保证结果逐字一致，弃用。

### D2：unchanged 跳过写盘放在 step_s3 普通规则 no-interrupt 分支

合并后比较 `merged == existing_text`：一致则不调用 `atomic_write`，动作记为 `unchanged`。放在执行层而非 merge_markdown 内（merge_markdown 是纯函数，不应感知文件 IO）。NC-08 回退分支不套用此判定（回退本身就是异常路径，写盘是必要的）。

### D3：RF-04 去特判，回归统一 drift 处理

删除 `compute_plan` 的 `codegraph-section-missing` 分支与 `step_s3` 对应执行分支；code-reading.md 与其他普通规则文件同路径：一致 → skip；drift → 普通模式询问 / no-interrupt 章节合并。

- **为何不做模式分叉（普通 report-only / no-interrupt 自动合并）**：两模式行为分叉正是评审批评点；保留特判就要保留粗糙的 substring 判定。
- **原 I5 顾虑的化解**：merge_markdown 对"模板有、项目无的章节"天然保留模板内容，项目内容全保留，且有统一备份屏障可回滚——风险与 mcp-servers.md 等其他规则文件同级，无额外风险。

### D4：报告字段增量而非 recommendation 分支

no-interrupt 下 drift 冲突条目增加 `no_interrupt_action: "markdown-merge"`，`recommendation=keep` 安全默认保持不变。

- **为何不让 recommendation 按模式分支**：recommendation 语义是"普通模式询问时的推荐默认项"，按模式改写会破坏其单一语义，且普通模式仍需要它。增量字段向后兼容（旧消费者忽略未知字段）。

### D5：SKILL.md 定位规则按安装场景分层

在「第一步——定位脚本」段落补充 plugin 安装场景的候选根定位顺序（plugin 缓存路径 → 仓库路径）与"缓存缺 scripts/ 时重装 plugin"指引。纯文档改动，不动脚本。

## Risks / Trade-offs

- [用户真实手写了 `**项目补充**` 文本被当作协议保留字规范化] → 概率极低且语义等价；merge-semantics.md NC-03 行明确标注该字符串为合并保留字。
- [RF-04 去特判后，老项目 code-reading.md 在 no-interrupt 下被自动合并写盘，用户未预期] → 统一备份屏障可回滚；报告资产动作明细体现 merged；这正是 no-interrupt 的模式承诺。
- [unchanged 判定基于逐字比较，对仅 mtime 关心者行为变化（文件不再被刷新）] → 这正是该改动的目的；报告明确标记 `unchanged` 可区分。
- [存量测试断言 RF-04 report-only 行为将失败] → 删改旧断言、改写为自动合并断言，并在 skill-clause-map.md 同步映射。

## Migration Plan

1. 代码与测试按 tasks.md 工作包推进（先失败测试后实现）。
2. 已被重复标记污染的目标项目文件：升级脚本后重跑一次 no-interrupt 即自愈，无需人工恢复备份。
3. 回滚：change 为单仓库文档/脚本改动，git revert 即可；目标项目侧任何一次合并均有时间戳备份可回滚。

## Open Questions

（无）
