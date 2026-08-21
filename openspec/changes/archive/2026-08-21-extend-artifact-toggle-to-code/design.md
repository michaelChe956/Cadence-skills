# Design: extend-artifact-toggle-to-code

## Context

`rule-config.py` 中 `_ensure_commit_toggle`（约 2468 行起）以 `TOGGLE_PREFIX = "- **产物自动提交（design/plan）**："` 唯一前缀行识别开关，支持章节归并、重复去重、非法值告警。本次改名 + 控制范围扩展 + 旧名身份迁移（方案已确认：单开关扩展、迁移保值、code 语义=禁 commit、L0 v3 文案同步不升版本）。

## Goals / Non-Goals

**Goals:**

- 新名 `- **产物自动提交（design/plan/code）**：<值>` 为唯一规范开关行。
- 旧名行确定性迁移为新名并保留原值；旧名+新名并存归并为恰好一行。
- L0 v3 模板、document-storage.md、SKILL.md、merge-semantics.md 文案同步。
- 全部既有开关测试/harness 用例按新基准转绿。

**Non-Goals:**

- 不改读取层语义（CLAUDE 为准/兜底/不一致按关、非法值按关、warning 码 `INVALID_TOGGLE` 不变）。
- 不新增第二开关或值组合解析。
- 不改变开关之外的 `_ensure_commit_toggle` 归并/告警行为。
- L0 不升 v4（模板逐字变化走 drift 权威覆盖）。

## Decisions

### D1: 双前缀识别、单一规范输出

新增常量 `TOGGLE_PREFIX_LEGACY = "- **产物自动提交（design/plan）**："`；规范输出统一用新名 `TOGGLE_PREFIX`。`_ensure_commit_toggle` 的开关行匹配改为“旧名前缀或新名前缀任一起始”，其余逻辑（取值、冲突判定、去重、落位）不变。旧名+新名并存天然落入既有“重复开关行归并”路径（保留首个值）。

### D2: L0 v3 模板开关句就地改文案

v3 模板开关句改为：“产物自动提交开关：完成 design/plan 文档或实现类产物（代码、测试、配置）写入后读取入口“产物自动提交（design/plan/code）”开关，`关闭` 时禁止 `git commit`、只汇报路径；CLAUDE.md 为准、不一致按 `关闭`。”体量仍 ≤2560（替换后净增 <30B，需 wc -c 验证）。存量 v3 项目按 drift 权威覆盖，不升 v4——Rationale：v3 与 v3.1 的差异仅文案，不值得冻结第二个历史源；v3 历史源文件本身为 v3 发布态，不随改。

### D3: 文档与测试基准同步

`document-storage.md`、rule-config `SKILL.md`、`references/merge-semantics.md` 中“产物自动提交（design/plan）”引用统一改新名；tests 与 harness 中开关行断言/样本改新名，另加迁移用例（旧名开启→新名开启、旧名非法值→保留原文+warning、旧名+新名并存→归并一行）。

## Risks / Trade-offs

- [某项目入口文件存在“恰好以旧名前缀起头”的用户自定义非开关行] → 前缀足够长且含完整旧开关名，误判概率极低；且归并保底恰好一行。
- [L0 不升 v4，正在 v2→v3 迁移途中的项目看到 v3 文案与冻结历史源不一致] → 历史源比对只针对 v2/v1/v0；v3 drift 走权威覆盖，无阻塞路径。

## Migration Plan

1. 单测先行（RED）：迁移/保值/并存归并/新名默认用例 + 既有开关用例改新名基准。
2. 脚本：常量与 `_ensure_commit_toggle` 匹配扩展。
3. 模板与文档文案同步。
4. harness 基准更新；本仓库 apply 实测（入口开关行迁移）。
回滚：全部改动为工作区文件，无 commit，git checkout 即回滚。
