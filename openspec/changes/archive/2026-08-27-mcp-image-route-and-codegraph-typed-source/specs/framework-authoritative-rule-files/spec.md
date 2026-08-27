# framework-authoritative-rule-files 变更提案

## ADDED Requirements

### Requirement: 代码阅读规则必须按项目类型单选来源且落地名恒定
系统 MUST 依据最终项目类型选择唯一的代码阅读规则来源模板，并 MUST 始终以 `code-reading.md` 作为落地文件名。系统 SHALL NOT 同时生成多个代码阅读规则文件，SHALL NOT 使用带项目类型后缀的落地文件名，也 SHALL NOT 将两类来源模板内容合并。非 Coding 来源模板 MUST NOT 包含默认的 CodeGraph 初始化、构建或优先使用要求，MUST NOT 将结构化大纲命令设为文档配置类文件的阅读前置；当任务明确涉及单个辅助源码文件时 MAY 允许仅对该文件使用大纲工具。drift 判定与幂等覆盖 MUST 以当前项目类型对应的来源模板为基准；已存在来自旧单一通用模板或与当前类型不符来源的内容时，系统 MUST 归档原文件后以当前类型对应模板原子覆盖原位。规则来源相关的执行语义受 rule-config-scripted-execution 能力约束。

#### Scenario: Coding 项目获得代码阅读工作流
- **WHEN** 最终项目类型为 Coding
- **THEN** 系统 MUST 以编码项目模板内容生成 `.claude/rules/code-reading.md`
- **AND** 模板 MUST 包含 CodeGraph 与结构化大纲协同使用的阅读约束

#### Scenario: 非 Coding 项目获得无代码图要求的阅读工作流
- **WHEN** 最终项目类型为非 Coding 且用户未显式启用 CodeGraph 开关
- **THEN** 系统 MUST 以非 Coding 模板内容生成 `.claude/rules/code-reading.md`
- **AND** 该模板 MUST NOT 包含默认初始化或构建代码图的要求
- **AND** 对明确涉及的辅助源码文件 MAY 仅针对该文件使用大纲工具

#### Scenario: 旧版内容按当前类型权威覆盖
- **WHEN** 已存在的 `code-reading.md` 内容与当前项目类型所选来源不符（含历史单一通用模板产物）
- **THEN** 系统 MUST 归档原文件后以当前类型对应模板原子覆盖原位
- **AND** 系统 SHALL NOT 将两类模板内容合并进同一文件

#### Scenario: 显式启用不改变来源归属
- **WHEN** 非 Coding 项目在用户显式启用 CodeGraph 开关下运行
- **THEN** 落地的 `code-reading.md` 仍 MUST 来自非 Coding 来源模板
- **AND** 显式开关仅影响 CodeGraph 安装与初始化行为

#### Scenario: 入口引用不产生悬空链接
- **WHEN** `rule-config` 完成执行
- **THEN** 入口文件与 L0 受管区块中对代码阅读规则的引用 MUST 指向实际存在的 `.claude/rules/code-reading.md`
