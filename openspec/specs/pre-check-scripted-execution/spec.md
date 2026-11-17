## Purpose

为 pre-check 提供确定性、可审计且可复跑的五阶段脚本执行契约，统一模型入口、结构化报告、性能边界、冲突处理和验证失败语义，确保既有实施行为能够被自动化验收并长期维护。

## Requirements

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

#### Scenario: OpenSpec 重试不得使整体超出熔断上限
- **WHEN** OpenSpec CLI ≥ 2.1.0 的初始化或更新在多个加速代理候选上依次超时
- **THEN** 该阶段按其阶段级网络预算停止重试并以失败报告，整体运行耗时不超过 240 秒熔断上限

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

### Requirement: OpenSpec 作用域与初始化参数

pre-check MUST 在为缺失客户端执行 OpenSpec 初始化前探测 CLI 版本。CLI 版本 ≥ 2.1.0 时，MUST 为初始化调用显式指定项目作用域，使技能写入项目根的共享技能目录；CLI 版本低于 2.1.0 时，MUST NOT 传入该参数，保持既有调用形态。CLI 版本无法解析时 MUST 按低于 2.1.0 处理。四端投影复核失败时，对应 phase 的 `error` MUST 保留既有失败前缀，并在 CLI ≥ 2.1.0 时追加说明该版本默认把技能装入用户家目录的全局作用域，以及在项目根重跑初始化的补救方向。

#### Scenario: 2.1.0 在无既有投影的项目上产出项目根投影
- **WHEN** 项目内没有任何既有 OpenSpec 技能投影，且 CLI 版本为 2.1.0
- **THEN** 初始化调用带项目作用域参数，共享技能写入项目根的共享技能目录并登记已配置客户端，用户家目录下不出现任何 OpenSpec 技能目录，四端复核通过且 phase 结果为 `success`

#### Scenario: 旧版本 CLI 不接受作用域参数
- **WHEN** CLI 版本为 2.0.0 或更早
- **THEN** 初始化调用不携带作用域参数，既有调用形态与既有判定口径不变

#### Scenario: 复核失败文案点名作用域原因
- **WHEN** CLI 版本 ≥ 2.1.0 且四端投影复核失败
- **THEN** phase 的 `error` 以既有失败前缀开头，并写明该版本默认装入家目录全局作用域的原因与补救方向

### Requirement: OpenSpec 网络调用超时与镜像回退

OpenSpec CLI ≥ 2.1.0 的初始化与更新需要访问 GitHub 获取技能，而 CLI 自身不提供网络超时。pre-check MUST 对该版本的初始化与更新施加单次调用超时与阶段级网络预算，MUST 使二者在同一阶段内共享同一截止时间，MUST NOT 通过重复重试使整体运行突破仓库规定的网络熔断上限。单次调用超时 MUST 不超过 60 秒，阶段级网络预算 MUST 不超过 180 秒，两者 MUST 可由环境变量调整。超时 MUST 按失败报告，对应 phase 的 `error` MUST 写明已尝试次数与下一步。CLI 低于 2.1.0 时，MUST NOT 施加该超时，保持既有调用形态。

`--mirror cn` 时，pre-check MUST 按镜像配置给出的 GitHub 加速代理候选顺序访问 GitHub，前一个候选失败时方可尝试下一个。MUST 通过仅作用于该次命令子进程的 git url 重写实现，MUST NOT 写入任何 git 全局或仓库配置，MUST NOT 改写用户已有的同类环境配置。默认镜像 MUST 直连，不启用代理。

#### Scenario: GitHub 不可达时有界失败
- **WHEN** CLI 版本 ≥ 2.1.0 且 GitHub 在超时窗口内始终不可达
- **THEN** 阶段以失败结束并写明超时、已尝试次数与下一步，整个运行不会因该调用无限挂起

#### Scenario: 加速代理逐个回退
- **WHEN** `--mirror cn` 下第一个加速代理候选访问失败而第二个可用
- **THEN** 脚本依次尝试候选并在可用候选上成功完成调用，报告不出现失败

#### Scenario: 代理改写只作用于本次调用
- **WHEN** 脚本经加速代理完成 OpenSpec 调用
- **THEN** 重写仅出现在该次命令的子进程环境中，git 配置与用户既有环境配置保持不变

### Requirement: 升级范围与镜像透传

`--upgrade` 的升级范围 MUST 包含 ast-grep、codegraph、openspec、pi-mcp-adapter 与 uv 本体，MUST NOT 包含 uvx 临时包与 playwright-cli。pi-mcp-adapter MUST 经其自身的更新机制升级，MUST 沿用当前镜像的 npm 源，MUST NOT 直接改写其安装目录；版本低于当前源 latest 时 MUST 升级并记录版本变化，已是最新时 MUST NOT 触发更新动作，版本固定写法 MUST 视为用户的有意选择并保持不变，升级后版本未追到 latest MUST 记为升级失败。

安装 pi-mcp-adapter 与获取 codegraph 外网回退下载时 MUST 跟随当前镜像；codegraph 在大陆镜像下 MUST 经 GitHub 加速代理获取回退下载，用户已自行设置下载源时 MUST NOT 覆盖。pre-check MUST NOT 执行 codegraph 的初始化、索引或同步。

#### Scenario: 落后版本被升级并记录版本变化
- **WHEN** `--upgrade` 下 pi-mcp-adapter 的已装版本低于当前源 latest
- **THEN** 脚本通过 pi 的更新机制完成升级，报告该工具的版本由旧值变为新值，且升级调用使用当前镜像的 npm 源

#### Scenario: 已是最新与固定版本不触发更新
- **WHEN** pi-mcp-adapter 已是当前源 latest，或其包名带固定版本写法
- **THEN** 脚本不发起更新动作，对应步骤保持既有状态

#### Scenario: 升级未达 latest 记为失败
- **WHEN** 更新动作执行后已装版本仍未追到 latest
- **THEN** 对应步骤记为升级失败并带上目标版本与当前版本，整体结果按既有失败语义判定

#### Scenario: 脚本不重建 codegraph 索引
- **WHEN** pre-check 完成工具检查与升级
- **THEN** 脚本不执行 codegraph 的初始化、索引或同步，索引由后续阶段决定
