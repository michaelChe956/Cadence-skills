# no-interrupt 四步幂等升级实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让 Cadence no-interrupt 四步初始化在用户修改规则后可安全重跑：框架内容升级、用户修改优先、零静默丢失、全流程可备份回滚。

**Architecture:** 以“单元 + 基线 + 三方判定”为核心：新增共享 Markdown/三方合并模块；`rule-config` 负责入口与 `.claude/rules`，`project-rules-examples` 负责模板章节合并，`mcp-configuration` 负责结构化 MCP 合并，`pre-check` 负责外部投影归档。任何实际写入先归档到 `cadence/legacy/<ts>/`。

**Tech Stack:** Python 3（标准库 difflib/unittest/json）、Bash、Markdown；测试使用仓库现有 `unittest` 与 shell harness。

**Spec:** `cadence/designs/2026-10-28_方案设计_no-interrupt四步幂等升级_v1.0.md`

## Global Constraints

- 不得修改 `/tmp/test-center-java`；所有真实运行在临时副本上完成。
- no-interrupt 全流程不提问；冲突用户胜并写入 `pending`，基础设施失败才退出非零。
- 任何改变既有文件字节的写入，必须先归档到 `cadence/legacy/<14位时间戳>/<相对路径>`。
- 第二次运行必须零写入、零备份；dry-run 与 apply 写集合一致。
- `.claude/rules` 7 个框架文件保持纯净；用户差异抽取到 `.claude/rules/user-<name>.md`。
- project-rules 模板：章节清单框架保证，正文用户优先；不再生成“项目补充”。
- MCP：缺失默认 server 重跑补回；已有同名 server 用户值优先。
- 安全单元（`.gitignore` 保护项、permission deny）框架优先并强警告。
- 状态目录 `cadence/framework-state/` 本地保存，不提交 VCS。
- 不提交 git commit（仓库产物自动提交开关为关闭），只落文件并汇报路径。

## Review Focus

- 用户行包含 `cadence/project-rules/` 或 `.claude/rules/<file>` 时不得被删除。
- 用户表格、围栏代码块、空行必须逐字保留。
- 入口 L0/强制规则写入必须进入备份屏障。
- `.claude/rules` 用户编辑必须抽取到 overlay 且框架文件恢复纯净。
- project-rules 已存在定制文件不得被模型重写。
- MCP 用户删除的默认 server 按裁决重跑补回；用户已改字段不得被覆盖。
- 第二次运行必须幂等零写入。

---

### Task 1: 共享 Markdown 合并模块

**Files:**
- Create: `cadence-init/skills/rule-config/scripts/cadence_merge.py`
- Test: `cadence-init/skills/rule-config/tests/test_cadence_merge.py`

**Interfaces:**
- Produces: `normalize_title(title: str) -> str`、`parse_sections(text: str) -> list[Section]`、`three_way(base: str|None, ours: str, theirs: str) -> tuple[str, list[dict]]`、`merge_sections(base: str|None, ours: str, theirs: str, required_keys: list[str]|None = None) -> tuple[str, list[dict]]`。
- `Section` 字段：`level: int`、`key: str`、`title: str`、`body_lines: list[str]`。

- [ ] **Step 1: 写失败测试**：围栏内 `#` 不识别为标题；`### 6. 项目个性化规则（强制规则）` 归一为 `项目个性化规则`；用户正文与框架正文冲突时保留用户；缺失章节从模板补齐。
- [ ] **Step 2: 运行测试确认失败**：`cd cadence-init/skills/rule-config && python3 -m unittest tests.test_cadence_merge -v`，期望 `ModuleNotFoundError`/import 失败。
- [ ] **Step 3: 实现 `cadence_merge.py`**：fence 状态机、标题归一、章节合并、行级三方（ours==base 取 theirs；theirs==base 取 ours；冲突用户胜并返回 pending）。
- [ ] **Step 4: 运行测试确认通过**：同一命令，期望 `OK`。
- [ ] **Step 5: 回归**：`python3 -m unittest discover -s tests -p 'test_*.py'`，期望全绿。

### Task 2: rule-config P0 安全修复

**Files:**
- Modify: `cadence-init/skills/rule-config/scripts/rule-config.py`
- Modify: `cadence-init/skills/rule-config/tests/test_rule_config.py`
- Test: 同上

**Interfaces:**
- Consumes: Task 1 的 `normalize_title`、`parse_sections`。
- Produces: `_normalize_mandatory_rules` 保留用户 H3/用户追加；`_backup_required_for` 对 S4 skip-backfill 返回 True；`_ensure_commit_toggle` 支持 `打开/启用/on`。

- [ ] **Step 1: 写失败测试**：用户表格行含 `cadence/project-rules/...` 不被删除；规则 6 的 CLAUDE 常量含 `.claude/rules/`；`打开` 不报 `INVALID_TOGGLE`；S4 skip 且内容变化时 `_backup_required_for` 返回 True。
- [ ] **Step 2: 运行测试确认失败**：`python3 -m unittest tests.test_rule_config -v`。
- [ ] **Step 3: 实现**：H3 标题归属替代 marker 子串；保留 H3 块内用户追加与空行；修正常量；开关别名；S4 skip 合成后比较并纳入备份。
- [ ] **Step 4: 运行测试确认通过**：同上命令。
- [ ] **Step 5: 回归**：`python3 -m unittest discover -s tests -p 'test_*.py'`。

### Task 3: `.claude/rules` overlay 抽取与状态

**Files:**
- Modify: `cadence-init/skills/rule-config/scripts/rule-config.py`
- Create: `cadence-init/skills/rule-config/scripts/cadence_state.py`
- Test: `cadence-init/skills/rule-config/tests/test_rule_overlay.py`

**Interfaces:**
- Consumes: Task 1 合并模块。
- Produces: `extract_overlay(base, ours, theirs, rule_name) -> str`；`load_manifest(root)`/`save_manifest(root, data)`；`.claude/rules/user-<name>.md` 自动抽取区。

- [ ] **Step 1: 写失败测试**：用户改 `.claude/rules/language.md` 后重跑，框架文件等于模板，`user-language.md` 含用户新增/替换/禁用，第二次运行零写入。
- [ ] **Step 2: 运行测试确认失败**：`python3 -m unittest tests.test_rule_overlay -v`。
- [ ] **Step 3: 实现**：状态 manifest（`cadence/framework-state/manifest.json`）、base 读取、diff 抽取、overlay 写入、备份。
- [ ] **Step 4: 运行测试确认通过**：同上命令。
- [ ] **Step 5: 回归**：`python3 -m unittest discover -s tests -p 'test_*.py'`。

### Task 4: project-rules-examples 确定性合并

**Files:**
- Modify: `cadence-init/skills/project-rules-examples/scripts/apply.sh`
- Create: `cadence-init/skills/project-rules-examples/scripts/apply.py`
- Modify: `cadence-init/skills/project-rules-examples/SKILL.md`
- Modify: `cadence-init/skills/project-rules-examples/tests/test-apply.sh`

**Interfaces:**
- Consumes: Task 1 `parse_sections`/`merge_sections`（通过相对路径导入，失败时本地回退）。
- Produces: `apply.py --project-root <root>` 输出 `created|pristine|merged|unchanged|skipped|needs-rule-config`；不再创建/修改 CLAUDE.md/AGENTS.md。

- [ ] **Step 1: 写失败测试**：已存在定制文件重跑后用户段落逐字保留、缺失章节补齐；CLAUDE.md/AGENTS.md 哈希不变。
- [ ] **Step 2: 运行测试确认失败**：`cd cadence-init/skills/project-rules-examples && bash tests/test-apply.sh`。
- [ ] **Step 3: 实现 `apply.py` 并让 `apply.sh` 转发**；更新 SKILL.md 为脚本合并、仅新建文件做事实定制。
- [ ] **Step 4: 运行测试确认通过**：同一命令。
- [ ] **Step 5: 回归**：`bash tests/test-apply.sh`。

### Task 5: MCP 确定性合并

**Files:**
- Create: `cadence-init/skills/mcp-configuration/scripts/mcp-config.py`
- Create: `cadence-init/skills/mcp-configuration/tests/test_mcp_config.py`
- Modify: `cadence-init/skills/mcp-configuration/SKILL.md`

**Interfaces:**
- Produces: `mcp-config.py apply --project-root <root> --report <path> [--no-interrupt]`；缺失默认 server 补回；同名用户字段优先；写入前归档。

- [ ] **Step 1: 写失败测试**：用户删除默认 `time` 后重跑补回；用户改 `context7.command` 保留；额外 server 保留；写入前 `cadence/legacy/` 有归档；第二次运行零写入。
- [ ] **Step 2: 运行测试确认失败**：`python3 -m unittest discover -s cadence-init/skills/mcp-configuration/tests -p 'test_*.py'`。
- [ ] **Step 3: 实现脚本**：JSON 键级合并、TOML 表块补齐、备份、报告。
- [ ] **Step 4: 运行测试确认通过**：同一命令。
- [ ] **Step 5: 回归**：同一命令。

### Task 6: pre-check 投影保护

**Files:**
- Modify: `cadence-init/skills/pre-check/scripts/pre-check.sh`
- Test: `cadence-init/skills/pre-check/tests/test-projection-guard.sh`（新建）

**Interfaces:**
- Produces: 运行 OpenSpec 投影前后记录哈希；被外部命令覆盖的用户修改归档到 `cadence/legacy/` 并报告。

- [ ] **Step 1: 写失败测试**：伪造投影文件，运行 guard 函数，断言归档存在且报告出现。
- [ ] **Step 2: 运行测试确认失败**。
- [ ] **Step 3: 实现哈希快照/比较/归档**。
- [ ] **Step 4: 运行测试确认通过**。
- [ ] **Step 5: 回归**：`bash -n scripts/pre-check.sh`。

### Task 7: 契约与文档

**Files:**
- Modify: `cadence-init/skills/rule-config/SKILL.md`
- Modify: `cadence-init/skills/rule-config/references/merge-semantics.md`
- Modify: `cadence-init/skills/rule-config/references/rules/agent-routing-kernel.md`
- Modify: `cadence-init/skills/rule-config/references/rules/document-storage.md`
- Modify: `README.md`

- [ ] **Step 1: 更新 `.claude/rules` 策略文案**：7 个框架文件不得修改；用户覆盖写入 `user-*.md`。
- [ ] **Step 2: 更新 `merge-semantics.md`**：H3 标题归属、用户优先、overlay、备份“凡写即归档”。
- [ ] **Step 3: 更新 SKILL.md 四步 no-interrupt 行为与脚本调用**。
- [ ] **Step 4: 文档自检**：grep 无“禁止在 `.claude/rules` 添加用户规则”旧文案。

### Task 8: 端到端回归

**Files:**
- Create: `cadence-init/skills/rule-config/tests/test-four-step-rerun.sh`（或 Python 集成测试）

- [ ] **Step 1: 复制 `/tmp/test-center-java` 到新的临时目录**，不写原目录。
- [ ] **Step 2: 执行四步 no-interrupt 两次**（pre-check 只跑 check/guard，rule-config、project-rules-examples、mcp-config 用副本）。
- [ ] **Step 3: 断言**：第一次有 `cadence/legacy` 归档；用户引用表/规则 8/`打开` 保留；第二次零写入、零备份。
- [ ] **Step 4: 断言 `.claude/rules` 框架文件等于模板，`user-*.md` 存在且用户内容可读**。
- [ ] **Step 5: 运行全部回归**：`python3 -m unittest discover -s cadence-init/skills/rule-config/tests -p 'test_*.py'` + `bash cadence-init/skills/project-rules-examples/tests/test-apply.sh` + MCP 测试。

## Execution Note

- 本计划在用户明确要求下于当前 `main` 工作区执行；不创建 worktree。
- 每个任务先 RED 后 GREEN；任务完成后运行全量相关测试。
- 任何计划偏差记录在最终汇报的“裁决”中，不静默改语义。

## 实施结果（2026-10-28）

- Task 1 共享合并模块：完成；`cadence_merge.py` 支持围栏感知、标题归一、章节三方合并、重复章节不丢段。
- Task 2 rule-config P0：完成；H3 归属、用户行/空行/围栏保留、规则 6 路径、开关别名、skip-backfill 备份、loss guard。
- Task 3 overlay/状态：完成最小闭环；`.claude/rules/user-*.md` 抽取、`cadence/framework-state` manifest/base、二次运行零写入。
- Task 4 project-rules：完成；确定性脚本、缺失章节补齐、有基线时章节三方合并、无基线保守追加、入口只读、写前备份。
- Task 5 MCP：完成；默认 server 补回、用户值优先、额外 server/扩展字段保留、`.codex` 表块补齐、`.gitignore` 安全单元、统一备份。
- Task 6 pre-check：完成；OpenSpec 投影前后哈希快照、被覆盖前像归档、warning/backups 报告。
- Task 7 文档：完成；README、rule-config SKILL、merge-semantics v2、rules/README、document-storage、project-rules/MCP/pre-check SKILL 同步。
- Task 8 端到端：完成；临时副本四步连跑两次，第二次零写入、零备份；用户引用表/规则 8/`打开` 保留；`/tmp/test-center-java` 未修改。

测试汇总：rule-config 327、project-rules 38 shell + 16 Python、MCP 33、pre-check 55 + harness 3。

评审修复：围栏长度感知、overlay 标记前缀匹配与累积、不可读 overlay 先归档、规则 6 overlay 文案与旧文案清理、用户 Playwright 引用保留、重复规范 H3 保留、loss guard 收紧、MCP 非 UTF-8 降级、`--allow-security-override` 顺序、permission deny 框架优先、S4 insert 备份、S6/S8 写前备份、project-rules 前置围栏保留、异常回滚清理新建文件、pending 落盘、fallback overlay provisional；并补 L0 用户行迁出、入口用户覆盖块/pending、L1 overlay、project-rules 保序、`.gitignore` 尾部不变量、MCP args 包名去重、dry-run planned_* 预演、CI 全量测试。

已知限制：存量项目首次运行无历史基线时走保守模式并报 `BASE_MISSING`/`pending`，可能把旧框架文本抽入 overlay；有基线后恢复正常三方判定。skill 侧历史版本快照未入库，后续可作为增强项。

## 延期项（2026-10-29 用户裁决：不实现，初始化后由用户自行比对文件）

以下设计项本期不实现，初始化完成后由用户自行比对文件：
- 入口 per-unit 基线（manifest `units` + 三方合并 + 用户覆盖块之外的精确替换）；
- skill 侧历史模板快照（首次升级精确匹配）；
- `decisions.json` 模型裁决层与 `review.md` / `review_required` 闭环；
- `.gitignore` 的 `git check-ignore` 后置复核、dry-run 对 S8 的预演、MCP TOML args 逐项验证。

不新增任何验收/报告类功能；工具只保证「不丢内容 + 写前备份 + 幂等」，结果由用户初始化后自行比对文件。
