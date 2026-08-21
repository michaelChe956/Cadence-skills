# Design: slim-l0-routing-kernel-v3

## Context

L0 模板 `cadence-init/skills/rule-config/references/rules/agent-routing-kernel.md` 当前为 v2（约 5.2KB），L1 `references/rules/openspec-superpowers-workflow.md` 约 5.2KB。版本升级机制已存在：`scripts/rule-config.py` 中 `L0_CURRENT_VERSION`/`L0_OLD_VERSIONS`/`L0_OLD_SOURCES` + `l0_block()` 六态分类（skip/dedup/drift/insert/upgrade/broken），v1 历史源存于 `references/rules/l0-history/agent-routing-kernel-v1.md`。`drift` 与 `upgrade` 在 apply 时同为"权威覆盖为当前版本 + 备份 + 区块外逐字保留"。

## Goals / Non-Goals

**Goals:**

- L0 v3 ≤2KB，删除全部姿态类条款与四客户端逐段差异，KB 门禁成为模板标准内容。
- 存量 v2/v1/v0 项目经现有升级机制增量到达 v3，不重装。
- L1 同步瘦身，语义保留（职责边界、7 步、可判定失败关闭、阈值与豁免）。

**Non-Goals:**

- 不改 pre-check 的 superpowers 安装逻辑（若发现其注入路由全文，另行提出）。
- 不在入口文件非受管区新增"客户端说明段"（方案 A 已定：客户端差异以 2-3 行中性说明内联于 v3）。
- 不处理 aria 平台的 prompt 注入问题（另行处理）。
- 不改 `l0_block()` 六态分类语义。

## Decisions

### D1: 客户端差异内联中性短说明（已与用户确认）

v3 保留约 2-3 行："Claude/Kimi 用客户端原生 Skill 调用；Codex/pi 从清单显式选择后将用途并入首段回执，随后立即全文读取对应 SKILL.md 作为调用"。
备选 B（入口文件非受管区新增客户端说明段 + v3 仅留指针）被否：存量项目非受管区不会被升级机制写入，指针落空，需额外注入逻辑。

### D2: v2 漂移走既有 drift 权威覆盖，不改分类（已与用户确认，方案一）

`l0_block()` 不改：v2 完整对逐字一致 → `upgrade`；v2 漂移（含手加行）→ `drift`，两者 apply 动作相同（备份 + 权威覆盖为 v3）。dry-run 保留"本地修改将被覆盖"提示。
备选（把旧版漂移重标为 `upgrade`）被否：需改判定逻辑与既有 v1 漂移用例，且丢失"手改被覆盖"的可见警告，纯风险无收益。

### D3: KB 门禁并入 v3 模板正文

v2 时代该行为 naruto 手写私有行；v3 起写死在模板（约 2-3 行），语义与 `knowledge-base-context` SKILL.md description 门禁一致。门禁是条件性描述，无 manifest 项目无副作用。

### D4: 版本常量与历史源

- 现 v2 模板全文逐字移入 `references/rules/l0-history/agent-routing-kernel-v2.md`（作为 `L0_OLD_SOURCES["v2"]`，逐字比对用）。
- `L0_CURRENT_VERSION = "v3"`；`L0_OLD_VERSIONS = ["v2", "v1", "v0"]`。
- v3 首尾标记随版本号生成（`:v3:start/:end`），与 v2 机制同构。

### D5: L1 瘦身走既有 drift 权威覆盖

L1 无版本迁移逻辑；规范源更新后，逐字一致的项目 `skip`，其余按现有 `replace`（备份 + 覆盖）处理。瘦身不改变 L1 的任何判定分支。

## Risks / Trade-offs

- [弱模型对 v3 删除的姿态条款（静默输出等）遵循率回退] → 这些条款本就不可验证、遵循率低；v3 缩短正文提高可验证条款的相对显著性，属有意取舍。
- [v2 漂移区块的手加内容（naruto 的 KB 门禁行）被覆盖丢失] → 覆盖前归档到 `cadence/legacy/` 可回滚；且 v3 模板已内置同语义门禁句，实际无信息损失。
- [模板全文逐字比对相关的既有单测/一致性校验（本仓库入口、`ARTIFACT_PATH_OVERRIDE_TABLE`、skill-clause-map）大面积失效] → 任务中逐个更新；`ARTIFACT_PATH_OVERRIDE_TABLE` 在 v3 中保留且必须与模板逐字一致。
- [v3 ≤2KB 目标与保留内容冲突] → 以"四条铁律 + 路由表 + KB 门禁 + 路径覆盖 + 自动提交开关 + 客户端两行"为下限，超限时优先压缩表格措辞而非删门禁。

## Migration Plan

1. 单测先行：v2→v3 五分类用例（逐字 v2、v2 漂移含手加行、v1、v0、无标记）+ 既有用例更新。
2. 模板与脚本改动（v3 重写、历史源、版本常量）、L1 瘦身。
3. 本仓库自验证：rule-config dry-run 确认本仓库入口升级路径正常，apply 后本仓库 L0 为 v3。
4. 实测 naruto（v2 + 手加 KB 门禁行）：dry-run 应报 v2 drift，apply 后 L0=v3、KB 门禁保留（来自模板）、双入口一致、块外内容不动。
5. 一个非 KnowledgeBase 项目冒烟：确认门禁段无副作用。
回滚：模板与脚本为仓库文件，git revert 即回滚；已升级项目的旧区块存于 `cadence/legacy/` 归档。

## Open Questions

（无）
