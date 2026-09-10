# omp-client-support Specification(Change A delta:新增能力)

## ADDED Requirements

### Requirement: omp 规则桥必须以文件级软链投影规则

`rule-config` MUST 在项目 `.agents/rules/` 下为每个框架落地规则文件(`.claude/rules/*.md`,排除 `README.md`)维护指向该文件的**文件级相对软链**;MUST NOT 使用目录级软链或指向仓库外目标的软链。软链集合 MUST 与规则文件集合保持一致:规则新增时创建对应软链,规则退役且源文件不存在时删除孤儿软链,断链或指向非规则源的**软链**重定向修复;`.agents/rules/` 内非本管线创建的文件 MUST 逐字保留并记录 warning,与规则同名的非软链普通文件 MUST 先复制归档到 `cadence/legacy/` 再以软链替换并记录 warning(内容可回滚),MUST NOT 无备份删除。重复运行 MUST 幂等:集合已一致时不产生任何写入。

#### Scenario: 与规则同名的用户普通文件被归档后替换

- **WHEN** `.agents/rules/code-usage.md` 是用户手工创建的普通文件(非软链)
- **THEN** `rule-config` 将其归档到 `cadence/legacy/` 后替换为指向规则源的软链,并记录 warning
- **AND** 归档副本内容与原文件一致,可回滚
#### Scenario: 新装项目软链集合与规则集合一致

- **WHEN** `rule-config apply` 在无 `.agents/rules/` 的项目上执行
- **THEN** 每个落地规则文件(除 README)都有同名软链指向 `../../.claude/rules/<名>.md`
- **AND** 重复执行同一命令不产生新的写入动作

#### Scenario: 规则退役后孤儿软链被清理

- **WHEN** 某规则文件已从 `.claude/rules/` 移除后重新运行 `rule-config`
- **THEN** 指向该文件的孤儿软链被删除
- **AND** 用户自建的非软链文件保持原样并出现 warning

### Requirement: `.omp/AGENTS.md` 必须为受管活引用

`rule-config` MUST 将项目 `.omp/AGENTS.md` 维护为整文件受管产物,内容为对 `.claude/CLAUDE.md` 与根 `AGENTS.md` 的活引用(`@../.claude/CLAUDE.md` + `@../AGENTS.md`),MUST NOT 在其中保留任何内容的副本。存在非受管旧文件(含手工过渡版)时,MUST 先复制归档到 `cadence/legacy/` 再原子替换。codegraph 等第三方再生成 `.claude/CLAUDE.md` 后,omp 会话经活引用 MUST 自动看到新内容,无需重跑 `rule-config`。

#### Scenario: 手工过渡文件被受管替换

- **WHEN** 项目存在手工维护的 `.omp/AGENTS.md`(含 CodeGraph 块副本)
- **THEN** `rule-config` 将其归档到 `cadence/legacy/<时间戳>/` 后替换为受管活引用
- **AND** 后续 codegraph 再生成 `.claude/CLAUDE.md` 时 omp 新会话无需任何修复动作即可见新内容

### Requirement: symlink 不可用环境必须降级物化并警告

运行环境无法创建 symlink(平台不支持或权限不足)时,`rule-config` MUST 降级为在 `.agents/rules/` 物化规则副本,并记录 warning(如 `OMP_BRIDGE_MATERIALIZED`);重跑时物化副本与源不一致 MUST 刷新。降级 MUST NOT 使 apply 失败关闭。

#### Scenario: 无 symlink 权限的环境

- **WHEN** symlink 创建在运行环境中失败
- **THEN** apply 以物化副本完成并成功退出
- **AND** 报告 warnings 中出现降级标识

### Requirement: verify 必须断言 omp 资产一致性

`rule-config verify`(只读自检)MUST 断言:软链集合与规则文件集合一致(排除 README)、`.omp/AGENTS.md` 与受管内容一致;发现漂移时以非零退出码报告,不写入任何文件。

#### Scenario: 软链缺失被 verify 发现

- **WHEN** 人为删除一个软链后运行 `verify`
- **THEN** 退出码非零且报告指明缺失的软链

### Requirement: 项目类型扫描必须剪枝 `.omp`

项目类型检测的有界扫描 MUST 剪枝 `.omp` 目录(omp 扩展为 TypeScript,防误判 Coding),且该剪枝清单 MUST 与 skill 文档中的扫描命令逐项一致(既有双向断言延续)。

#### Scenario: 仅含 omp 扩展的项目不被误判

- **WHEN** 项目源码仅存在于 `.omp/` 下
- **THEN** 项目类型检测不因其判定为 Coding
