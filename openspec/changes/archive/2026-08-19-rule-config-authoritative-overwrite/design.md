# Design: rule-config-authoritative-overwrite

## Context

现状与动机见 proposal.md。设计相关的当前状态：

- `scripts/rule-config.py` 在 `compute_plan` 的 S3（规则文件）、S4（L0 入口）、S7（OpenSpec 配置）为六类 drift 生成冲突条目（`recommendation=keep`、`default_keep: true`），普通模式 apply 按 `decisions_map` 消费决策，no-interrupt 走独立的权威分支。
- `references/merge-semantics.md` 是合并语义权威定义（NC/OS/L1/L0/RF/SM/OP/CS/CG/HM 十表 64 行 + §11.6 A/B 类裁决），与 `tests/skill-clause-map.md` 逐条对账。
- 六类 A 类冲突是本 change 的全部范围，改动后系统无活跃冲突类型。

## Goals / Non-Goals

**Goals:**

- 六类受管内容状态两模式统一为"归档 + 权威覆盖/归并/移除"，全程不经用户决策。
- 复用既有备份屏障与原子发布机制，不新增保护代码路径。
- 决策文件机制转为休眠兜底，语义保持失败关闭、可供未来冲突类型复用。
- 三份文档（SKILL.md / merge-semantics.md / README.md）与条款对账表同步到新语义。

**Non-Goals:**

- 不改变备份归档路径结构、L0 双入口屏障、原子发布、幂等跳过语义。
- 不删除 `merge_markdown`、`validate_decisions`、`default_keep` 等休眠代码。
- 不改变 HM 历史目录迁移的模式差异、`--project-type` 提升权、SM 章节规范化。

## Decisions

### D1：drift 不再产生冲突条目，而非保留"信息性冲突"

六类状态从 `plan.conflicts` 中移除（两模式），计划动作由 `steps[].assets[].action=replace` + `backup_needs` 表达，执行结果由 `steps[].actions[]` 的 `overwritten` / `authoritative-overwrite` / `replaced` 等条目记录。替代方案"保留冲突条目并标 `auto_resolved`"被否决：冲突清单在普通模式流程中是提问队列，保留信息性条目会稀释"冲突=待决策"的模型，且需要 SKILL.md 额外区分两类条目。

### D2：决策机制休眠而非删除

`--decisions` 参数、`validate_decisions` 校验（未知/重复 id、stale 计划失败关闭）、`default_keep` 标注代码全部保留。对齐 codex 五轮删除 `s1:project-type-conflict` 后的既定原则（机制保留兜底供未来复用）。普通模式计划无冲突时不要求决策文件；若用户误传含旧 `s3:`/`s4:`/`s7:` 条目的决策文件，按"未知 conflict_id"失败关闭——决策文件本就是每次运行 `mktemp` 的一次性产物，无兼容负担。

### D3：L1 只变决策权，不变版本识别

`classify_l1` 的完整内容版本识别逻辑不动（current→skip、旧版逐字一致→upgrade、其余→replace 类）。仅 replace 类状态（drift/unmarked/mismatch）从"询问"变为"归档+替换"。由此满足契约"不得降级为无版本识别的整体覆盖"。

### D4：普通模式直接复用 no-interrupt 代码路径

S3 规则文件、L0-03/L0-06、OS-04 的普通模式 decision 分支删除，两模式合流到现有 no-interrupt 权威分支（备份屏障 + 覆盖/归并/移除）。不新写普通模式专用逻辑，把两模式差异面收缩到 HM 迁移与意图参数两处既有差异。

### D5：OS-03/05 从失败关闭改为归档+模板替换

既有 `openspec/config.yaml` 无法解析或结构/类型不兼容时：候选 = 模板文本经结构预检，归档屏障成功后 `atomic_write` 发布，正常完成（status=0）并报告。no-interrupt 从"备份后终止"对齐为同一动作。替代方案"保留失败关闭"被用户裁决否决；替代方案"类型归一化修复"被否决（无法证明无损，违背 OS-N3 一贯原则）。

### D6：报告分支命名统一

普通模式原有的 `rules-replace` / `rules-keep` / `l1-replace` / `l1-keep` / `rules-apply-keep` 等决策分支名退役，两模式统一使用 `authoritative-overwrite` / `authoritative-idempotent` / `l1-no-interrupt`（更名为 `l1-replace-authoritative`）等确定性分支名；`no_interrupt_action` 字段随冲突条目一并移除。SKILL.md 的"汇报冲突实际动作"规则改为依据 `steps[].actions[]`。

## Risks / Trade-offs

- **项目对受管内容的本地定制被自动覆盖**（如 naruto 的 Serena 版 mcp-servers、TDD 版 code-usage）→ 归档到 `cadence/legacy/` 可恢复；SKILL.md 要求 Agent 汇报 overwritten 清单与归档路径，用户可人工捞回。
- **OS-03/05 整文件替换丢失项目配置**（schema/context/自定义规则）→ 仅发生在文件已损坏或不合规时；备份可恢复；报告明确记录替换动作。
- **测试面改写量大**（普通模式 keep/replace 决策用例成批失效）→ 按 `skill-clause-map.md` 逐条对账改写，先红后绿；条款 map 同步标注语义变更。
- **两模式行为合流后普通模式"价值"下降** → 可接受：普通模式仍独有 HM 迁移与 `--project-type` 提升权，且 dry-run/apply 两阶段汇报不变。

## Migration Plan

1. 本 change 为仓库内脚本/测试/文档变更，按 TDD 实施：先改写失效测试断言新语义（红），再改脚本（绿），最后同步三份文档与条款对账表。
2. 框架用户无需迁移操作：下次在目标项目运行 `rule-config` 自动按新语义执行；已被覆盖的文件可从 `cadence/legacy/<时间戳>/` 恢复。
3. 回滚：git 回滚本 change 的实现提交即可；目标项目侧无持久状态需要回滚。

## Open Questions

无。
