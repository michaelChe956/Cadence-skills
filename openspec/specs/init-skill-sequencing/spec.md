# init-skill-sequencing Specification

## Purpose
TBD - created by archiving change fix-init-skill-dependency. Update Purpose after archive.
## Requirements
### Requirement: OpenSpec 检查完成门槛不含 config.yaml

pre-check 的 OpenSpec 检查完成条件 MUST 仅包含：OpenSpec CLI 可用，以及 claude/codex/pi/kimi 四客户端指令产物验证成功。pre-check MUST NOT 将 `openspec/config.yaml` 的存在性作为完成条件或失败条件。

#### Scenario: 全新项目执行 pre-check

- **WHEN** 在不存在 `openspec/config.yaml` 且无任何客户端指令产物的全新项目上执行 `/pre-check`
- **THEN** pre-check 执行 `openspec init --tools claude,codex,pi,kimi` 生成四客户端产物后，OpenSpec 检查判定通过，不终止、不报失败

#### Scenario: config.yaml 缺失但产物齐全

- **WHEN** 四客户端指令产物齐全但 `openspec/config.yaml` 不存在
- **THEN** OpenSpec 检查判定通过，并输出 config.yaml 将由 rule-config 创建的提示

### Requirement: config.yaml 缺失提示语义

`openspec/config.yaml` 缺失时，pre-check MUST 输出中文提示，说明该文件将由 rule-config 步骤 11 创建；该提示 MUST NOT 影响 OpenSpec 检查判定；no-interrupt 模式 MUST NOT 因 config.yaml 缺失而终止 `/pre-check`。

#### Scenario: no-interrupt 模式下 config.yaml 缺失

- **WHEN** 以 `no-interrupt` 参数执行 `/pre-check` 且 `openspec/config.yaml` 不存在
- **THEN** pre-check 输出提示信息并继续后续检查项，不立即终止

### Requirement: 按客户端检测的增量补齐

pre-check MUST 分别检测 claude、codex、pi、kimi 四客户端指令产物的存在性；对缺失的客户端执行 `openspec init --tools <缺失客户端列表>`，随后执行 `openspec update`；产物已齐全的客户端 MUST NOT 被重新 init；`openspec/config.yaml` 的存在性 MUST NOT 作为分支判断条件。codex 客户端产物就绪判定 MUST 以项目根 `.agents/skills/` 下存在 `openspec-*` 目录为准（最新 OpenSpec 为 skills-only，codex 产物落项目根 `.agents/skills/`，不再产生 `.codex/` 目录）；MUST NOT 以 `.codex/skills/` 作为 codex 就绪判定路径。

#### Scenario: rule-config 先行后执行 pre-check

- **WHEN** 项目存在 rule-config 写入的 `openspec/config.yaml` 但四客户端指令产物均缺失，执行 `/pre-check`
- **THEN** pre-check 执行 `openspec init --tools claude,codex,pi,kimi` 与 `openspec update`，四客户端产物验证通过，且 `openspec/config.yaml` 内容保持 rule-config 写入值不变

#### Scenario: 仅 pi 产物缺失

- **WHEN** claude、codex、kimi 产物齐全、pi 产物缺失，执行 `/pre-check`
- **THEN** pre-check 仅执行 `openspec init --tools pi` 与 `openspec update`，claude、codex、kimi 产物不被重新生成

#### Scenario: 三客户端产物齐全

- **WHEN** claude、codex、pi 产物齐全、kimi 产物缺失，执行 `/pre-check`
- **THEN** pre-check 仅执行 `openspec init --tools kimi` 与 `openspec update`，claude、codex、pi 产物不被重新生成

#### Scenario: 四客户端产物齐全

- **WHEN** claude、codex、pi、kimi 四客户端产物均齐全，执行 `/pre-check`
- **THEN** pre-check 仅执行 `openspec update`，不执行任何 `openspec init`

#### Scenario: codex 产物按最新路径判定

- **WHEN** 项目经 `openspec init --tools codex` 生成产物（最新 OpenSpec 为 skills-only，产物在项目根 `.agents/skills/openspec-*`，无 `.codex/` 目录），执行 `/pre-check`
- **THEN** pre-check 以 `.agents/skills/` 下存在 `openspec-*` 目录判定 codex 就绪，MUST NOT 因 `.codex/skills/` 不存在而误判 codex 缺失或重复执行 `openspec init --tools codex`

### Requirement: 硬门槛与失败语义保留

OpenSpec CLI 安装失败、`openspec init`/`openspec update` 失败、或四客户端指令产物验证失败时，no-interrupt 模式 MUST 立即终止 `/pre-check`，普通模式 MUST 报告失败；npx/uvx/ast-grep/codegraph/OpenSpec/Superpowers 六个基础检查的门槛地位 MUST 保持不变。

#### Scenario: 产物验证失败

- **WHEN** 以 `no-interrupt` 参数执行 `/pre-check`，init 与 update 执行后任一客户端指令产物验证失败
- **THEN** `/pre-check` 立即终止，报告失败步骤、失败原因、已完成步骤和恢复建议，不宣称初始化成功

### Requirement: README 职责边界同步

README MUST 明确以下口径并与 pre-check SKILL.md 一致：pre-check 的 OpenSpec 检查范围为 OpenSpec CLI 与四客户端指令产物；`openspec/config.yaml` 由 rule-config 创建与合并；初始化顺序仍为 pre-check 先、rule-config 后，顺序颠倒时 pre-check 能按缺失客户端补齐产物。

#### Scenario: 文档口径一致性核验

- **WHEN** 对照阅读 README 初始化章节与 pre-check SKILL.md 的 OpenSpec 检查条款
- **THEN** 两处对完成条件、config.yaml 归属与顺序约束的表述一致，无相互矛盾的验收口径

### Requirement: Superpowers 在线源使用代理候选列表
cn 镜像的 Superpowers 在线安装源 MUST 为 GitHub 加速代理候选列表（顺序：ghfast.top、gh-proxy.com、mirror.ghproxy.com，均指向 obra/superpowers 上游）；default 镜像 MUST 为单元素候选列表（GitHub 官方地址）。报告 MUST 以 `hints.superpowers_git_candidates` 数组暴露候选列表，MUST NOT 再输出单一地址字段。clone MUST 按序尝试候选并使用 `--depth 1` 浅克隆；全部候选失败时步骤 MUST 判定 `failed` 并报告逐个候选的错误原因，no-interrupt 模式 MUST 按失败关闭规则立即终止。

#### Scenario: 首个代理可用时浅克隆
- **WHEN** 执行 Superpowers 在线安装且第一个代理候选 clone 成功
- **THEN** 使用该候选以 `--depth 1` 完成克隆并继续软链同步

#### Scenario: 全部候选失败
- **WHEN** 三个代理候选 clone 全部失败
- **THEN** 步骤判定 `failed`，报告列出每个候选的错误
- **AND** no-interrupt 模式立即终止 `/pre-check`，不降级为警告

### Requirement: Superpowers 更新必须切换到候选源
本地 `~/.agents/superpowers` 的 origin 不在候选列表内（如历史 Gitee 地址）时，更新逻辑 MUST 先将 origin 切换为首个可拉取成功的候选再执行更新；候选内地址 MUST 直接更新。

#### Scenario: 历史安装源切换
- **WHEN** 已有安装的 origin 指向 Gitee 镜像且执行更新
- **THEN** 先切换 origin 为首个可用代理候选
- **AND** 切换后完成更新与软链同步

### Requirement: 不做离线兜底
Superpowers 安装/更新失败时系统 MUST NOT 提示或校验离线复制目录；失败即报告失败，MUST NOT 提供降级路径。

#### Scenario: 失败不降级
- **WHEN** Superpowers 在线安装失败
- **THEN** 报告失败原因与恢复建议（检查网络/代理可达性）
- **AND** MUST NOT 提示"离线复制到 ~/.agents/superpowers"或类似兜底路径
