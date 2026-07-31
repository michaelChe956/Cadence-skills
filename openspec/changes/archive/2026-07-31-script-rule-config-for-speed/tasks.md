# Tasks: script-rule-config-for-speed

## 1. 测试改造（RED）

- [x] 1.1 编制"现行 SKILL 条款→fixture/test 映射表"并提交为 `tests/skill-clause-map.md`，最小列：SKILL 行号区间 / 条款摘要 / 适用模式 / 脚本函数或 references 条目 / fixture / 测试 ID / 关键断言；逐条覆盖现行 SKILL.md 全部行为分支（含 design D2 锁定的十张表行 ID 基线），识别既有 22 用例未覆盖的缺口——历史目录两模式、普通规则不覆盖、技术栈/包管理器写入与覆盖率 80%、`cadence/` gitignore 两分支、Playwright 两分支、CodeGraph 显式启用与增量状态矩阵、Markdown 不可解析回退、摘要编号冲突、项目类型两模式规则（no-interrupt 以检测为准；普通模式 CLI 仅提升 non-coding→coding）、用户意图参数透传（对应 specs 全部 requirement）
- [x] 1.2 新建 `tests/test_rule_config.py`（stdlib unittest）：为 `merge_markdown()`（含不可解析回退）、`merge_yaml()`（全类型矩阵）、`l0_block()`、备份命名与屏障编写失败测试（对应"合并与保护语义脚本内确定性实现"）
- [x] 1.3 改造 `tests/verify-managed-lifecycle.sh`：既有 22 用例迁移为驱动脚本 CLI，并按 1.1 映射表补齐缺口用例；原子发布失败以目标目录 `chmod 555` 复现，备份失败以只读父目录复现；删除"4 次 instructions 验证"断言，改为结构预检与合并结果断言（对应 routing-conformance 修改的 requirement）
- [x] 1.4 新增静态契约检查：断言 SKILL.md 不含直接读写目标项目文件的操作指令、包含有界扫描与两阶段调用文本、包含裸 token `no-interrupt` 与 `--no-interrupt` 等价规范化条款、保留 `disable-model-invocation: true`（沿用"从 SKILL.md 提取 find 命令"先例）
- [x] 1.5 新增预算计时断言：空 fixture 项目 `apply --no-interrupt` 的 `budget_seconds_excluding_codegraph < 60`（计时起点脚本入口、终点 OpenSpec 配置步骤完成；对应"端到端耗时预算"）
- [x] 1.6 运行测试确认 RED（脚本不存在，全部失败）

## 2. 脚本实现（GREEN）

- [x] 2.1 新建 `scripts/rule-config.py` 骨架：CLI（dry-run/apply、--no-interrupt、--decisions、--report、--project-type、--ignore-cadence、--enable-playwright、--enable-codegraph）、JSON 报告 schema（含规范字段 `hints.next`）、decisions.json 校验（未知/重复/缺失/过期失败关闭）、统一备份与 `os.replace()` 原子写、PyYAML 缺失退出码 77 且照常写报告（对应"脚本两阶段执行与模式衔接""JSON 报告与失败关闭"）
- [x] 2.2 实现 S1-S2：有界项目类型检测（detect_project 只返回检测结果；_compute_final_project_type 按两模式规则裁决）、技术栈/包管理器检测、模板三级定位成对校验
- [x] 2.3 实现 S3-S4：`merge_markdown()` 章节合并与不可解析回退、普通模式不覆盖分支、Playwright 两分支、`l0_block()` 与双入口统一预检备份屏障、入口文件单次写入、摘要编号冲突保留原文（对应"合并与保护语义脚本内确定性实现"）
- [x] 2.4 实现 S5-S6：目录创建、历史目录两模式处理（no-interrupt 只报告精确目录集合）、gitignore 两分支行级幂等（对应"项目配置产物与现行语义一致"）
- [x] 2.5 实现 S7：`merge_yaml()` 保守合并、PyYAML 解析+结构预检、备份屏障与原子发布（对应"OpenSpec 配置验证以结构预检取代 instructions 验证"）
- [x] 2.6 实现 S8：codegraph 同步执行（Coding 项目或 `--enable-codegraph`），增量状态矩阵（`.codegraph/` 已存在只 status、双配置齐全跳过、任一缺 MCP 先 install 固定参数 `--target=claude,codex --location=local --yes` 再补齐仍缺失方、`.codegraph/` 不存在执行 install+init）、install 失败自动补齐双配置并 degraded、init/status 失败 degraded 不阻断、配置补写/备份/原子写失败终止、单独计时
- [x] 2.7 运行 1.1-1.5 全部测试至 GREEN；删除 `tests/helpers/managed-lifecycle-reference.sh`

## 3. Skill 瘦身与语义迁移

- [x] 3.1 新增 `references/merge-semantics.md`：迁移现行 SKILL.md 的合并规则、完整"模式×资产×冲突状态"矩阵与完成报告要求正文
- [x] 3.2 重写 `SKILL.md` 为约 150 行编排骨架：保留 frontmatter `disable-model-invocation: true`、参数解析与意图参数透传（裸 token `no-interrupt` 规范化为 `--no-interrupt`）、脚本定位与调用、dry-run→逐条提问→apply 流程、报告解读、失败关闭、保留"下一步：mcp-configuration"交接
- [x] 3.3 更新涉及 rule-config 行为描述的仓库文档（`.claude/rules/README.md`、相关 cadence 文档索引）

## 4. 验收

- [ ] 4.1 macOS/Linux 双平台生命周期回归通过（含 sha256sum/shasum 回退路径）
- [ ] 4.2 Claude Code 真实环境空项目端到端验收：no-interrupt 从 Skill 触发到最终汇报 ≤5 分钟（扣除 S8 实际耗时），合并/备份/幂等/历史目录/用户意图参数行为抽查符合 specs
- [x] 4.3 `openspec validate --strict` 通过，提交并推送 feat-b-rule-config-cost-time
