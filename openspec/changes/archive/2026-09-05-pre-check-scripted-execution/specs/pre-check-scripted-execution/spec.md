## Purpose

为 pre-check 提供确定性、可审计且可复跑的五阶段脚本执行契约，统一模型入口、结构化报告、性能边界、冲突处理和验证失败语义，确保既有实施行为能够被自动化验收并长期维护。

## ADDED Requirements

### Requirement: 五阶段编排与结构化阶段报告

pre-check 的 `run` MUST 在一次调用内按 `base-tools`、`openspec`、`superpowers-git`、`superpowers-links`、`verify` 的固定顺序执行五个阶段。输出 JSON MUST 保留既有 `steps[]`，并提供 `phases[]`；`phases[]` 每项 MUST 包含恰好用于阶段审计的 `phase`、`result`、`action`、`duration_ms`、`created`、`updated`、`skipped`、`conflicts`、`error` 九个字段，其中 `result` 取 `success`、`partial`、`failed` 或 `skipped`，`duration_ms` 为非负整数，`error` 为字符串或 `null`。`superpowers-git` 阶段 MUST 额外提供 `origin`、`branch`、`before_revision`、`after_revision` 四个 Git 字段；`superpowers-links` 阶段 MUST 额外提供 `source_entries` 与 `layers[]` 字段，以支持来源条目和链路层级的审计。阶段计数 MUST 反映实际创建、更新、跳过与冲突，不得用 `skipped` 隐藏写入。

#### Scenario: 首次运行完成五阶段并报告 Git 与链接元数据
- **WHEN** 项目执行一次完整 `run`，且工具、OpenSpec 投影、Superpowers 来源/软链与复核均可处理
- **THEN** 报告按上述五阶段顺序包含 `phases[]`，写入阶段的 `created` 或 `updated` 计数反映实际结果，Git 阶段包含四个 Git 字段，软链阶段包含 `source_entries` 和 `layers[]` 字段

#### Scenario: 阶段错误进入对应 error 字段
- **WHEN** Git 阶段发生来源或命令错误，或 verify 阶段发现产物不完整
- **THEN** 对应 phase 的 `result` 为 `failed` 或普通模式下的 `partial`，且 `error` 为非空错误说明；错误不会只存在于非结构化 stderr 中

### Requirement: SKILL.md 三步调用契约

pre-check 的 SKILL.md MUST 将模型入口限定为三步：定位 pre-check 脚本并拼出绝对路径；在项目根目录以一次脚本调用执行 `run`（可传递镜像、`--no-interrupt` 或升级参数）；读取 JSON 报告并以中文呈现结果。模型 MUST NOT 临场重写安装、更新、Git 或软链编排命令，不得通过 heredoc 或等价临时脚本补全阶段动作；单次 pre-check 交互的工具调用总数 MUST 不超过 5 次。`unsupported`、冲突或失败状态 MUST 由报告显式呈现并交由人工处理，不得静默回退到模型自由编排。

#### Scenario: 模型用项目根的一次调用完成 pre-check
- **WHEN** 模型已定位 `<PRE_CHECK_SH>`，并从项目根执行 `bash "<PRE_CHECK_SH>" run` 及所需脚本参数
- **THEN** 脚本负责五阶段动作，模型不再执行逐项安装、OpenSpec 更新、Superpowers Git 或软链命令，并随后只读取报告呈现结果

#### Scenario: 调用上限与失败不得被临场编排绕过
- **WHEN** 报告显示 `unsupported`、冲突或阶段失败
- **THEN** SKILL 契约要求模型停止自动补写或自行改写命令，按模式报告/终止并交由人工处理，且整个入口保持不超过 5 次工具调用

### Requirement: 统一性能验收与网络熔断

pre-check 的可接受性能线 MUST 对冷热启动、增量运行和首次工具/Superpowers 获取一视同仁，端到端耗时统一不超过 120 秒。脚本 MAY 使用 240 秒作为网络异常的硬熔断上限；超过该上限 MUST 判为基础设施失败（`INFRA_FAIL`），不得将 240 秒视为合格性能线或为冷启动另设宽松预算。

#### Scenario: 冷启动也必须满足统一验收线
- **WHEN** 在隔离项目首次执行 pre-check，包含必要的工具安装、OpenSpec 投影补齐或 Superpowers 首次获取
- **THEN** 端到端耗时不超过 120 秒，且不得因冷启动而适用更宽的成功阈值

#### Scenario: 网络异常只触发 240 秒熔断
- **WHEN** 网络候选持续异常导致执行达到 240 秒熔断上限
- **THEN** 执行判定为 `INFRA_FAIL` 并停止相应网络动作；该结果不被报告为性能合格

### Requirement: 冲突结果与 no-interrupt 恢复语义

普通模式发现同名非软链冲突时 MUST 保留原内容，记录 warning/skip 并增加 `conflicts` 计数，不得静默忽略；在没有其他阶段错误时，该阶段结果 MUST 为 `success`，并可以在冲突后继续下游与统一报告。`--no-interrupt` 模式处理冲突时 MUST 按备份→创建→验证顺序执行：三步均成功则 phase 结果为 `success`，仅当备份、创建或验证链任一步失败时才为 `failed`；成功恢复不得因曾经存在冲突而错误判定失败。

#### Scenario: 普通模式冲突可继续但必须可审计
- **WHEN** 目标路径已有同名非软链，且以普通模式运行
- **THEN** 原内容保持不变，阶段结果为 `success`，报告记录 warning/skip 和正的 `conflicts` 计数，并继续执行可继续的后续阶段，而不是静默跳过冲突

#### Scenario: no-interrupt 冲突恢复链成功
- **WHEN** `--no-interrupt` 遇到同名非软链，备份、创建目标软链和解析验证均成功
- **THEN** 该 phase 的 `result` 为 `success`，且报告保留冲突及动作计数供审计

#### Scenario: no-interrupt 恢复链失败即失败快返
- **WHEN** `--no-interrupt` 的备份、创建或验证任一步失败
- **THEN** 该 phase 的 `result` 为 `failed` 并记录错误，且不得把恢复不完整报告为 success

### Requirement: 幂等重跑与 precheck-v2 基线守卫

对已就绪项目重跑 pre-check MUST 不写入目标树；五个阶段 MUST 均报告 `skipped`，整体 MUST 报告 `all-skipped`（或等价的整体跳过动作），并且目标树前后 diff 为零。实现与验收 MUST 以 `precheck-v2` 作为旧实现、真实投影布局和隔离本地 Git 来源重采的 1:1 基线；基线对照 MUST 保护非目标文件不被改写，同时不得放宽真实 OpenSpec 投影的数量和命名判定来制造假绿。

#### Scenario: 已初始化项目二次运行零写入
- **WHEN** 首次运行已经建立所有必需投影、Git 来源和四层正确软链，随后以相同参数再次运行
- **THEN** 五个 phase 的 `created`、`updated`、`conflicts` 均为 0，五 phase 均 `skipped` 且 `superpowers-links`/`verify` 的 `action` 为 `all-skipped`，目标树 diff 为空

#### Scenario: 基线对照拒绝非目标变更
- **WHEN** 将新实现首跑结果与 `precheck-v2` 基线在同一隔离 fixture 中逐项比较
- **THEN** 目标行为与产物保持 1:1，任何非目标文件变化或通过虚构旧命名布局放宽检查的行为均使验收失败

### Requirement: 只读 verify 与失败快返

`verify` 阶段 MUST 只读复核五阶段产物路径、数量、软链最终可解析性及报告所需状态，零写入且无冲突时结果为 `skipped`。在 `--no-interrupt` 模式下，任一前置阶段失败 MUST 立即返回 `failed` 并阻断下游写入；普通模式的前置阶段失败 MUST 记录 `partial`、错误与返回码，继续可执行的下游阶段，并由主流程统一 emit 最终报告。verify 发现错误时 MUST 将 `VERIFY_ERROR` 写入自身 `error` 字段并使总体结果可判定失败。

#### Scenario: verify 成功时只读且可跳过
- **WHEN** 五阶段产物均完整、软链可解析且没有冲突，执行 verify
- **THEN** verify 不创建或更新文件，报告其 `result` 为 `skipped`，`action` 为 `all-skipped` 或等价的整体只读跳过动作

#### Scenario: no-interrupt 前置失败阻断下游
- **WHEN** `--no-interrupt` 下 base-tools、openspec、superpowers-git 或 superpowers-links 任一阶段失败
- **THEN** 脚本立即报告失败并阻断所有下游写入，不执行后续会产生写入的阶段

#### Scenario: 普通模式 partial 续跑并统一输出
- **WHEN** 普通模式下任一前置阶段失败但流程仍可继续
- **THEN** 失败阶段记录 `partial`、错误和返回码，后续阶段按规则继续，最终只由主流程统一 emit 一份完整报告，不回退模型临场编排
