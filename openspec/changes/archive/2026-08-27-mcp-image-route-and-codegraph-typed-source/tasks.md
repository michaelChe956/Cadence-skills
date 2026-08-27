# Tasks: MCP 图片识别路由规则引入与 CodeGraph 规则按项目类型分发修复

> 实施遵循 TDD：每组先写失败测试，再最小实现。产物自动提交开关=关闭：全程 `git commit` 禁用。铁律：模板/摘要选择只消费最终 `plan["project_type"]`；no-interrupt 裁决逻辑零改动。

## 1. 失败测试先行（code-reading 双来源）

- [x] 1.1 在 `test_rule_config.py` 仿 `TestCodeUsageSingleSource` 新增 code-reading 双来源测试类：fixed target=`code-reading.md`、selected template_source 随项目类型切换、source 模板不得落地到 `.claude/rules/`；验证运行失败（命令见各测试内注释）
- [x] 1.2 新增 S3 drift/no-interrupt 权威覆盖断言（按所选来源比较）与入口第 7 条双文案渲染测试；新增显式启用场景断言「S8 执行但 code-reading 仍为 noncoding 来源」；验证全部 RED

## 2. 双来源实现

- [x] 2.1 新建 `references/rules/code-reading-coding.md`（迁移现行正文并补项目类型前提）与 `code-reading-noncoding.md`（文档/配置结构化阅读指引；无默认 CodeGraph 要求；ast-grep 单辅助文件窄例外）；移除旧单文件模板
- [x] 2.2 修改 `rule-config.py`：新增 `CODE_READING_SOURCE_MAP`/`CODE_READING_TARGET` 常量；`ORDINARY_RULE_FILES` 移除 code-reading（5→4）；S3 按类型单选追加目标项并记录 template_source；drift 以所选来源比较；`CODEGRAPH_RULE_FILE` 常量中性化更名
- [x] 2.3 locate_templates 必备清单纳入两份新来源（缺失即 TemplateError 失败关闭）；运行 `python3 -m unittest cadence-init/skills/rule-config/tests/test_rule_config.py -k reading` 全绿

## 3. 入口第 7 条双文案

- [x] 3.1 在 `rule-config.py` 定义 RULE7_TEXT_CODING / RULE7_TEXT_NONCODING 双文案常量并在受管区块渲染处按最终 project_type 选择；更新对应静态断言；验证第 7 条相关单测全绿
- [x] 3.2 核对 CLAUDE.md / AGENTS.md 渲染路径（含 `_compose_entry` 替换范围）仅作用于权威区块；运行既有入口规范化测试组确认无回归

## 4. mcp-servers.md 路由小节与 CodeGraph 条件化

- [x] 4.1 在权威模板智普/MiniMax 小节之前新增「图片识别路由与 MCP 可用性状态」独立小节：能力三分 multimodal/text-only/unknown、原生优先禁止多余调用、探测前置与至多一次、无固定优先级明示（章节顺序不代表优先级）、全不可用如实报告
- [x] 4.2 同文件新增可用性状态缓存契约：`cadence/cache/mcp-availability/<task-scope-id>.json`、status 三态、每 scope 每 provider 至多一探、失效三条件视作 unknown、白名单字段安全禁令（不得记录密钥/Authorization/原始响应等）
- [x] 4.3 将该文件 CodeGraph 小节的「项目必须先执行 codegraph init」等无条件表述条件化为「仅 Coding 项目或用户显式启用时允许」；为智普/MiniMax 小节补交叉引用一句；同步根副本 `.claude/rules/mcp-servers.md`

## 5. mcp-configuration 所有权收缩

- [x] 5.1 修改 `mcp-configuration/SKILL.md`：删除 395-407 行「规则追加到 `.claude/rules/mcp-servers.md` 文件末尾」旧流程及「已有段落则跳过」逻辑；改述为规则由 rule-config 权威模板维护、本 Skill 仅负责 .mcp.json/Codex config/gitignore 配置交接
- [x] 5.2 收敛 SKILL.md 内重复的大段视觉/图片说明为指向路由小节的简述；新增静态契约测试断言 SKILL.md 不再出现「追加到 `.claude/rules/mcp-servers.md` 文件末尾」且含 canonical 引用表述；验证静态测试 GREEN
- [x] 5.3 幂等追加 `.gitignore` 条目 `cadence/cache/mcp-availability/`（不忽略整个 cache 目录）及其测试

## 6. 集成测试与文档对账

- [x] 6.1 更新 `verify-managed-lifecycle.sh`：converged fixtures 按 kind 同时取 code-usage/code-reading 来源；显式启用用例断言 S8 执行且来源不变；no-interrupt/CLI 提升/检测 coding 三类下游一致性用例；根副本特殊来源映射（本仓库根副本对 noncoding 来源同步校验）
- [x] 6.2 更新 `tests/skill-clause-map.md` 与 `references/merge-semantics.md` 中涉及 code-reading/CodeGraph 的映射与合并语义描述
- [x] 6.3 更新本仓库自身落地副本：`.claude/rules/code-reading.md` ← noncoding 来源逐字同步（diff 校验通过）
- [x] 6.4 全量回归：`python3 -m unittest cadence-init/skills/rule-config/tests/test_rule_config.py`、`bash verify-managed-lifecycle.sh`、`openspec validate 2026-08-27-mcp-image-route-and-codegraph-typed-source --strict`、`git diff --check`
- [x] 6.5 终检：确认 `.codegraph/` 与缓存目录未被 git 跟踪；确认仓库活动文件中 grep 不到「全新 worktree 必须先初始化 CodeGraph」「追加到 \`.claude/rules/mcp-servers.md\` 文件末尾」残留（归档历史文档除外）；人工删除本 worktree 现场 `.codegraph/` 后汇报
