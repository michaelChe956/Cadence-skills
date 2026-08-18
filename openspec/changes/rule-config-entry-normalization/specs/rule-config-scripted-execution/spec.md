## MODIFIED Requirements

### Requirement: 合并与保护语义脚本内确定性实现
系统 MUST 在脚本内实现现行全部合并与保护语义，且按资产类别区分动作空间。框架受管规则文件（`.claude/rules/` 下的 `mcp-servers.md`、`code-reading.md`、`document-storage.md`、`language.md`、`markdown-format.md`、`code-usage.md`、`playwright.md`）MUST 采用框架权威全覆盖：内容与框架模板一致则幂等跳过，不一致时 MUST 先将原文件复制到 `cadence/legacy/` 归档，再以模板内容原子覆盖原位；MUST NOT 产生 `**项目补充**` 段落、保留项目独有章节或对这类文件调用章节级合并。`openspec-superpowers-workflow.md`（L1）MUST 保留基于完整内容的版本识别与升级语义，不纳入权威全覆盖。L0 受管区块的插入/升级/替换与双入口统一预检备份屏障、OpenSpec config.yaml 的保守合并去重、时间戳归档屏障与同文件系统原子发布 MUST 按现行语义执行。入口文件 `## 强制规则` 章节的规范化（缺失创建、失效引用清理、重排编号、用户内容保留）MUST 按 entry-file-normalization 能力契约在脚本内确定性实现，两模式同动作且不经用户决策；规范化 MUST NOT 修改受管区块外的项目内容。普通模式对框架受管规则文件 drift SHALL 询问用户，无响应或拒绝时 MUST NOT 覆盖，跳过并报告；no-interrupt 模式 MUST 直接权威覆盖并归档原文件。`**项目补充**` 标记仅对仍适用章节合并的非框架资产保留合并协议保留字语义。no-interrupt 下目标内容与现有文件逐字一致时 MUST 跳过写盘并在报告中标记 `unchanged`。任何必要归档失败时 MUST 整体终止且保持原文件不变；`atomic_write` 失败时原文件 MUST 因原子替换语义保持不变，无需回滚归档。

#### Scenario: no-interrupt 下框架规则文件权威覆盖
- **WHEN** 目标项目已存在与模板内容不一致的框架受管规则文件并以 no-interrupt 运行
- **THEN** 脚本 MUST 先将原文件复制到 `cadence/legacy/<时间戳>/<相对路径>` 归档
- **AND** 仅在归档成功后 SHALL 以模板内容原子覆盖原位
- **AND** 结果 MUST NOT 含 `**项目补充**` 段落或项目独有章节

#### Scenario: 框架规则文件幂等跳过
- **WHEN** 框架受管规则文件内容已与模板逐字一致
- **THEN** 脚本 MUST 跳过写盘且 MUST NOT 产生归档
- **AND** 报告 MUST 标记 `unchanged`

#### Scenario: 普通模式下冲突规则文件默认不覆盖
- **WHEN** 普通模式遇到与模板冲突的既有框架受管规则文件且用户无响应或拒绝覆盖
- **THEN** 脚本 MUST 保持原文件不变并在报告中标记跳过
- **AND** 缺失的规则文件 SHALL 照常创建

#### Scenario: Markdown 无法可靠解析的框架规则文件
- **WHEN** no-interrupt 模式下既有框架受管规则文件无法可靠解析
- **THEN** 脚本 MUST 先归档原文件，再以模板内容原子覆盖原位
- **AND** 归档失败时 MUST 终止且原文件不变

#### Scenario: 备份失败整体终止
- **WHEN** 任一动作需要归档但归档复制失败
- **THEN** 脚本 MUST 立即终止且原文件保持不变
- **AND** 报告 MUST 记录失败文件、原因与恢复建议

#### Scenario: 原子覆盖失败不破坏原文件
- **WHEN** 归档成功后 `atomic_write` 原子替换原位失败
- **THEN** 原文件 MUST 保持运行前内容不变
- **AND** 已归档副本 SHALL 保留在 `cadence/legacy/` 供恢复
- **AND** 报告 MUST 记录写入失败与归档恢复路径

#### Scenario: 入口文件单次处理
- **WHEN** 脚本处理 CLAUDE.md 与 AGENTS.md
- **THEN** L0 区块与强制规则章节规范化 MUST 在一次运行内合并完成，每个入口至多写入一次
- **AND** 受管区块外的项目内容 MUST 原样保留
- **AND** 章节规范化 MUST 按权威清单重排编号、清理退役引用并保留用户内容，不再仅追加缺失摘要

### Requirement: JSON 报告与失败关闭
脚本 MUST 输出结构化 JSON 报告，包含总体状态、模式、项目类型、各步骤状态与耗时、每资产动作明细、备份路径、冲突处理结果和失败恢复建议；报告 MUST 包含顶层 `warnings` 数组，元素含 `code`、`file`、`message` 与可选 `detail`，错误码限于契约枚举（`USER_LINES_KEPT`、`DUPLICATE_H2`、`ORPHAN_RULE6`、`INVALID_TOGGLE`、`ENTRY_TOGGLE_MISMATCH`、`L0_DEDUP`）；warning MUST NOT 改变 `overall` 取值；dry-run 与 apply 产出的 warnings MUST 一致，no-interrupt 模式 MUST 同样产出。codegraph 步骤耗时 MUST 单独列出并标注不计入初始化预算；报告 MUST 包含规范字段 `hints.next: "mcp-configuration"`，Agent 汇报后 MUST 据此将配置结果交接给 mcp-configuration 流程。任一步骤失败 MUST 使报告停在失败项并附失败文件、原因与恢复建议；**唯一例外**是 codegraph 步骤中 `install`/`init`/`status` 子命令失败，可按 degraded 降级继续，但 S8 内的配置补写、备份与原子写失败仍 MUST 终止。PyYAML 缺失时脚本 MUST 以专属退出码退出并仍写出报告，供 Agent 以 uvx 兜底重跑。Agent MUST 依据报告如实汇报，缺少成功证据时不得声称完成。

#### Scenario: 报告区分幂等跳过与实际变更
- **WHEN** 在已初始化项目上重复运行脚本
- **THEN** 报告 MUST 将未变化资产标记为幂等跳过
- **AND** Agent 汇报时 MUST NOT 把跳过说成新建或合并

#### Scenario: warnings 不影响总体状态
- **WHEN** 运行产生保留用户内容、非法开关值等 warning 且无失败
- **THEN** 报告 `overall` MUST 保持 `ok`
- **AND** `warnings` 数组 MUST 包含对应错误码、文件与说明
- **AND** dry-run 与实际运行产出的 warnings MUST 一致

#### Scenario: codegraph 已初始化状态幂等
- **WHEN** `.codegraph/` 已存在，或 `.mcp.json` 与 `.codex/config.toml` 均已包含 CodeGraph MCP
- **THEN** 脚本 MUST 按现行 CodeGraph 增量状态矩阵处理：`.codegraph/` 已存在时只运行 `codegraph status` 不重复 init，双配置齐全时不重复写入
- **AND** 任一配置文件缺少 CodeGraph MCP 时 MUST 先执行 `codegraph install --target=claude,codex --location=local --yes`，再核验并仅补齐仍缺失的一方
- **AND** `.codegraph/` 不存在时 MUST 执行 install 与 init

#### Scenario: codegraph install 失败仍补齐双配置
- **WHEN** `codegraph install` 失败
- **THEN** 脚本 MUST 按兜底配置自动补齐 `.mcp.json` 与 `.codex/config.toml` 的 CodeGraph MCP 配置
- **AND** 该步骤 MUST 标记为 degraded 且整体流程继续

#### Scenario: codegraph init/status 失败不阻断
- **WHEN** `codegraph init` 或 `codegraph status` 失败
- **THEN** 该步骤 MUST 标记为 degraded 且整体流程继续
- **AND** 报告 SHALL 给出项目语言、目录规模提示与手动兜底配置
