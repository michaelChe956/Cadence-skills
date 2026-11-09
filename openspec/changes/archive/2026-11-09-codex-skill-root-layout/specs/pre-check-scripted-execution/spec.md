# pre-check-scripted-execution 规格增量

## MODIFIED Requirements

### Requirement: 五阶段编排与结构化阶段报告

pre-check 的 `run` MUST 在一次调用内按 `base-tools`、`openspec`、`superpowers-git`、`superpowers-links`、`verify` 的固定顺序执行五个阶段。输出 JSON MUST 保留既有 `steps[]`，并提供 `phases[]`；`phases[]` 每项 MUST 包含恰好用于阶段审计的 `phase`、`result`、`action`、`duration_ms`、`created`、`updated`、`skipped`、`conflicts`、`error` 九个字段，其中 `result` 取 `success`、`partial`、`failed` 或 `skipped`，`duration_ms` 为非负整数，`error` 为字符串或 `null`。`superpowers-git` 阶段 MUST 额外提供 `origin`、`branch`、`before_revision`、`after_revision` 四个 Git 字段；`superpowers-links` 阶段 MUST 额外提供 `source_entries` 与 `layers[]` 字段，以支持来源条目和链路层级的审计。`superpowers-links` 阶段 MUST 把 Superpowers 条目软链到四层：`~/.agents/skills`、`~/.claude/skills`、`~/.codex/skills`、`~/.pi/agent/skills`；Codex 层 MUST 为扁平目录 `~/.codex/skills/<name>`，MUST NOT 使用 `~/.codex/skills/skills/<name>` 嵌套布局，并 MUST 迁移旧嵌套层中本阶段托管的链接、迁空后删除旧目录。阶段计数 MUST 反映实际创建、更新、跳过与冲突，不得用 `skipped` 隐藏写入。

#### Scenario: 首次运行完成五阶段并报告 Git 与链接元数据

- **WHEN** 项目执行一次完整 `run`，且工具、OpenSpec 投影、Superpowers 来源/软链与复核均可处理
- **THEN** 报告按上述五阶段顺序包含 `phases[]`，写入阶段的 `created` 或 `updated` 计数反映实际结果，Git 阶段包含四个 Git 字段，软链阶段包含 `source_entries` 和 `layers[]` 字段

#### Scenario: 阶段错误进入对应 error 字段

- **WHEN** Git 阶段发生来源或命令错误，或 verify 阶段发现产物不完整
- **THEN** 对应 phase 的 `result` 为 `failed` 或普通模式下的 `partial`，且 `error` 为非空错误说明；错误不会只存在于非结构化 stderr 中

#### Scenario: Codex 层为扁平布局

- **WHEN** `superpowers-links` 阶段在全新环境完成
- **THEN** 四层各存在同名软链，Codex 层条目直接位于 `~/.codex/skills/<name>`，且每条软链最终解析到 Superpowers 来源目录

#### Scenario: 旧嵌套层条目被迁移

- **WHEN** 环境中存在旧布局 `~/.codex/skills/skills/<name>` 的 Superpowers 受管链接
- **THEN** 新布局 `~/.codex/skills/<name>` 被建立为可解析软链，旧层中该条目被移除，旧层目录在迁空后被删除

### Requirement: 只读 verify 与失败快返

`verify` 阶段 MUST 只读复核五阶段产物路径、数量、软链最终可解析性及报告所需状态，零写入且无冲突时结果为 `skipped`。软链可解析性复核 MUST 覆盖四层每个受管软链：`SKILL.md` MUST 可读，不可读时 MUST 写入 `VERIFY_ERROR` 并使总体失败；`~/.codex/skills/.system` 与插件缓存下的条目 MUST NOT 计入受管集合。在 `--no-interrupt` 模式下，任一前置阶段失败 MUST 立即返回 `failed` 并阻断下游写入；普通模式的前置阶段失败 MUST 记录 `partial`、错误与返回码，继续可执行的下游阶段，并由主流程统一 emit 最终报告。verify 发现错误时 MUST 将 `VERIFY_ERROR` 写入自身 `error` 字段并使总体结果可判定失败。

#### Scenario: verify 成功时只读且可跳过

- **WHEN** 五阶段产物均完整、软链可解析且没有冲突，执行 verify
- **THEN** verify 不创建或更新文件，报告其 `result` 为 `skipped`，`action` 为 `all-skipped` 或等价的整体只读跳过动作

#### Scenario: 受管软链不可解析即失败

- **WHEN** 任一层的受管软链最终解析不到可读的 `SKILL.md`
- **THEN** `verify` 阶段 `result` 为 `failed`，`error` 字段记录具体路径，整体运行结果为失败

#### Scenario: 系统技能目录不计入受管集合

- **WHEN** `~/.codex/skills/.system` 下存在 Codex 内置技能
- **THEN** verify 不把这些条目计入受管集合，也不因它们产生 `VERIFY_ERROR`

#### Scenario: no-interrupt 前置失败阻断下游

- **WHEN** `--no-interrupt` 下 base-tools、openspec、superpowers-git 或 superpowers-links 任一阶段失败
- **THEN** 脚本立即报告失败并阻断所有下游写入，不执行后续会产生写入的阶段

#### Scenario: 普通模式 partial 续跑并统一输出

- **WHEN** 普通模式下任一前置阶段失败但流程仍可继续
- **THEN** 失败阶段记录 `partial`、错误和返回码，后续阶段按规则继续，最终只由主流程统一 emit 一份完整报告，不回退模型临场编排
