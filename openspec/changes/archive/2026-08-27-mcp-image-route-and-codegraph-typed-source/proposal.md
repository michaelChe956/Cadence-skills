# Proposal: MCP 图片识别路由规则引入与 CodeGraph 规则按项目类型分发修复

## Why

非代码项目（如本仓库）在创建新 worktree 后被规则文案强制执行 `codegraph init`，产生无用的 `.codegraph/` 数据库——根因是 `code-reading.md` 被无差别分发给所有项目类型，而安装脚本 S8 早已按 `project_type` 条件化，「文案与工具配置」信号割裂。同时，`mcp-servers.md` 缺少图片识别的全局路由语义：模型自带多模态时未要求优先原生识图、双 MCP（智普/MiniMax）间无「无固定优先级」约定、调用前无可用性探测与状态标记，且 `mcp-configuration` 残留旧版「追加规则到受管文件末尾」流程构成第二写者。

## What Changes

- **code-reading 双来源单选**：照 `code-usage` 先例，将 `references/rules/code-reading.md` 拆分为 `code-reading-coding.md` / `code-reading-noncoding.md`，按最终 `plan["project_type"]` 单选，落地名仍固定为 `.claude/rules/code-reading.md`；no-code 版不含任何默认 CodeGraph 初始化/使用要求；入口第 7 条摘要同步按项目类型渲染双文案。
- **CodeGraph 显式例外边界收紧**：保留 `--enable-codegraph`，但限定只能由用户显式触发（Agent 不得自行推断），仅控制 S8 安装步骤，不改变项目类型与两个规则模板来源的选择。
- **新增图片识别路由契约**：模型原生多模态优先 → 否则智普/MiniMax MCP 可用（每 provider 每任务 scope 至多探测一次，结果记录至 `cadence/cache/mcp-availability/<task-scope-id>.json`）；两 provider 无固定优先级；安全字段禁令（不记录密钥/原始响应等）。
- **mcp-servers.md CodeGraph 小节条件化**：仅 coding 或用户显式启用时允许初始化，作为显式例外场景的唯一使用指引出口。
- **mcp-configuration 所有权收缩**：删除「追加到 `.claude/rules/mcp-servers.md` 文件末尾」旧流程；本 Skill 仅负责 `.mcp.json`/Codex config/gitignore 配置交接。

## Capabilities

### New Capabilities

- `mcp-image-input-routing`: 图片输入的路由决策与 MCP 可用性状态——原生多模态优先、智普/MiniMax 独立探测与 task-scope 状态缓存 schema、无固定供应商优先级、探测安全约束、受管规则单一来源（mcp-configuration 不再写入）。

### Modified Capabilities

- `managed-rule-lifecycle`: 重写「非 Coding 项目仍获得代码阅读规则」Scenario 为「代码阅读规则按最终项目类型单选来源」；新增 non-coding 阅读规则不得含默认 CodeGraph 要求、入口摘要同步、显式开关不改类型/来源/摘要等条款。
- `rule-config-scripted-execution`: code-reading 来源选择与第 7 条摘要纳入最终 project_type 连带语义；明确 no-interrupt 行为不变；`--enable-codegraph` 保持独立于类型裁决。
- `framework-authoritative-rule-files`: 受管落地名仍为固定 `code-reading.md`，但 drift 与幂等判定必须针对当前项目类型所选的来源模板。
- `progressive-context-routing`: 不再对所有项目统一暗示 CodeGraph/ast-grep 工具链；代码工具路由仅适用于 coding 项目或显式启用场景。

## Impact

- **脚本**：`cadence-init/skills/rule-config/scripts/rule-config.py`（ORDINARY_RULE_FILES 清单、CODE_READING_SOURCE_MAP 新增、S3 选择逻辑、drift 比较、locate_templates 完整性清单、RULE7 双文案常量与渲染）
- **模板**：`cadence-init/skills/rule-config/references/rules/`（移除单一代码阅读模板，新增两份变体；mcp-servers.md 增加路由小节与条件化 CodeGraph 小节）
- **下游 Skill**：`cadence-init/skills/mcp-configuration/SKILL.md`（删除规则追加职责）
- **测试**：`test_rule_config.py`（双来源、摘要双文案、drift 拆分期望）、`verify-managed-lifecycle.sh`（fixtures 按类型取源、显式启用断言、根副本来源映射）、SKILL.md 静态契约
- **本仓库自身产物**：`.claude/rules/code-reading.md` 与 `.claude/rules/mcp-servers.md` 根副本同步（本仓库为 non-coding）；`.gitignore` 幂等追加缓存目录
- **兼容性**：非破坏。no-interrupt、权威覆盖、备份屏障、归档屏障、固定落地名等既有红线不变；受管落地文件总数维持 7 个
