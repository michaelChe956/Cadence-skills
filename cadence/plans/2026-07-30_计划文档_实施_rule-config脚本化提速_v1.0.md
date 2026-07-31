# rule-config 脚本化提速 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Change:** `openspec/changes/script-rule-config-for-speed`（proposal / design / specs / tasks 已获批，commit f83b390）。本 Plan 只展开契约，不重定义范围、架构与验收。

**Goal:** 将 rule-config 从 758 行 LLM 操作手册改造为"薄 Skill + python 单脚本两阶段执行"，空项目 no-interrupt 端到端 ≤5 分钟（扣 S8 实际耗时），不丢失任何现行合并、备份与失败关闭语义。

**Architecture:** `scripts/rule-config.py` 为唯一执行体（dry-run/apply 两阶段、S1-S8 流水线、全局备份屏障与 `os.replace()` 原子写、JSON 报告）；`merge_markdown()`/`merge_yaml()`/`l0_block()` 三个纯函数库承载合并语义，L1 框架规则走独立的"完整内容比对"分支（不做章节合并）；测试三层 = stdlib unittest 单测 + `verify-managed-lifecycle.sh` 集成（fixture→CLI→断言文件系统与 report）+ SKILL.md 与 routing-conformance 静态契约检查；`tests/skill-clause-map.md` 为语义对账基线。

**Tech Stack:** python3（stdlib，PyYAML 经 import 失败退出码 77 + `uvx --with pyyaml` 兜底）、Bash（集成 harness）、现有 OpenSpec CLI 校验、Markdown。

## Global Constraints

- 仅修改 `.worktrees/feat-b-rule-config-cost-time` 工作树；不得修改 `.claude/rules/` 框架规则。
- 契约权威：`openspec/changes/script-rule-config-for-speed/`；合并矩阵行 ID 基线 = design D2 十张表（NC-01~08、OS-01~08、L1-01~07、L0-01~07、RF-01~04、SM-01~03、OP-01~04、CS-01~08、CG-01~08、HM-01~03）。
- **接口名冻结（与 OpenSpec tasks 逐字一致）**：`merge_markdown(template: str, existing: str) -> str | None`、`merge_yaml(template_text: str, existing_text: str | None) -> tuple[str, list[dict]]`、`l0_block(text: str, source_v1: str) -> str`（返回 `skip|drift|insert|upgrade|broken`）、`precheck_openspec_structure(doc) -> list[str]`、`backup_file(path: Path) -> Path`、`atomic_write(path: Path, content: str) -> None`、`sha256_file(path: Path) -> str`。**禁止**使用 `merge_yaml_candidate`/`classify_l0`/`build_candidate` 等别名。
- 脚本文件名为 `rule-config.py`（连字符，不可直接 import）；单测 MUST 用 `importlib.util.spec_from_file_location("rule_config", SCRIPT_PATH)` 加载。
- PyYAML 为固定运行时依赖；`import yaml` 失败 MUST 以退出码 77 退出并仍写出报告；文本行级 YAML 处理方案已被契约否决，不得回退。
- 备份命名 `<文件>.cadence-backup-YYYYMMDDHHMMSS`；同秒冲突追加 `-2`/`-3` 唯一后缀（不覆盖首个）；备份成功绝不等于授权破坏性重写。
- **全局备份屏障（执行顺序冻结）**：apply = `compute_plan` → 汇总本次全部必要备份（S3 普通规则/L1/S4 双入口/S7）并**一次性全部创建** → 任一备份失败→立即终止、**零发布**（备份文件本身保留并列入报告）→ 屏障通过后才按 S1-S8 顺序执行发布。
- `--report` 与 `--decisions` 路径 MUST 在项目根外（脚本拒绝根内路径）；dry-run 对项目根零写入。
- 决策文件机制仅普通模式：计划无冲突→不要求学决策文件；有冲突→缺失/未知/重复/过期均失败关闭零写入；**用户无响应时由 Agent 把推荐默认（如 `keep`）显式写入决策文件**，脚本不得把"无决策"当"跳过"。no-interrupt 单次 apply 内部自动决策；`s1:project-type-conflict` 仅普通模式进决策文件。
- S8 是唯一失败例外：仅 install/init/status 子命令失败可 degraded；S8 内配置补写、备份、原子写失败仍终止。codegraph 子进程 MUST `subprocess.run(..., cwd=project_root)`。
- 预算 = 脚本 `main()` 入口记录单一 `T0 = time.monotonic()`、S7 完成时取差值（墙钟区间，含 CLI 解析与步骤间耗时）；S8 单独计时。CI 代理指标 `budget_seconds_excluding_codegraph < 60`；端到端验收 = Skill 触发→最终汇报扣 S8 实际耗时 ≤5 分钟。
- 删除 OpenSpec 候选验证的临时工作区与 4 次 `openspec instructions`；结构预检取代之。
- L1 文件（`openspec-superpowers-workflow.md`）MUST NOT 走 `merge_markdown()` 章节合并；只能按 L1-01~07 的"完整文件内容与已知版本逐字比对"分支处理。脚本内置 `KNOWN_L1_VERSIONS = {"v1": <规范源文本>}`，受支持旧版当前为空集；upgrade 分支由单测经参数注入旧版文本覆盖。
- 写入任何目标文件前 MUST 先 `mkdir -p` 其父目录（空项目无 `.claude/rules/`、`openspec/` 等）。
- 集成测试 MUST NOT 依赖开发机真实 `codegraph`；用 fixture 前置 PATH 的 fake `codegraph` 可执行文件。`chmod 555` 故障注入 MUST 先 `stat` 保存原权限、cleanup 恢复原权限；注入点为 `atomic_write` 内临时文件创建/替换失败分支（555 覆盖该分支即可证明"发布失败保持原文件"）；测试以非 root 用户运行为前提。
- 所有验证命令在仓库根执行，路径用 `cadence-init/skills/rule-config/tests/...` 全路径；**失败判定必须取测试命令自身退出码**：统一模式 `cmd > /tmp/x.log 2>&1; s=$?; echo "exit=$s"; tail -5 /tmp/x.log`，RED 期望 `exit!=0`、GREEN 期望 `exit=0`；禁止以 `tail`/`grep` 管道退出码作为判定。
- TDD：每个 Task 先 RED 后 GREEN；提交信息中文、遵循仓库历史风格。

---

### Task 1: 语义对账基线 `tests/skill-clause-map.md`

**Files:**
- Create: `cadence-init/skills/rule-config/tests/skill-clause-map.md`

**Interfaces:**
- Consumes: 现行 `SKILL.md` 全文、design D2 行 ID 基线。
- Produces: Task 3 的用例清单来源；Task 10 的矩阵正文来源。

- [ ] **Step 1: 通读现行 SKILL.md 并列出全部行为条款**

逐节登记：参数模式（裸 token 等价）、no-interrupt 通用规则与权威合并 8 行、无交互默认策略表、人工交互策略表、检查清单 11 项、处理流程 S1-S11 全部命令与表格、增量运行 6 张表、核心原则。每条款给唯一编号。

- [ ] **Step 2: 按最小列写映射表**

列：`SKILL 行号区间 | 条款摘要 | 适用模式 | 脚本函数或 references 条目 | fixture | 测试 ID | 关键断言`。十张表行 ID 用 design D2 基线（NC-01 等）；测试 ID 命名规则：单测 `ut-<函数>-<场景>`，集成 `it-<步骤>-<场景>`，静态 `sc-<条款>`。fixture 命名：`fx-<场景>`。

- [ ] **Step 3: 自审覆盖度**

逐条款检查都有测试 ID 或 references 条目；特别确认缺口清单（历史目录两模式、普通规则不覆盖、技术栈/包管理器/覆盖率 80%、gitignore 两分支、Playwright 两分支、CodeGraph 显式启用与增量矩阵、Markdown 不可解析回退、摘要编号冲突、检测矛盾、意图参数透传、裸 token、disable-model-invocation、L1 独立分支、基础入口文本、dry-run 零写入、decisions 四类异常、全局备份屏障）。

- [ ] **Step 4: 提交**

```bash
git add cadence-init/skills/rule-config/tests/skill-clause-map.md
git commit -m "test(rule-config): 新增 SKILL 条款到测试的语义对账映射表"
```

### Task 2: 单测骨架与纯函数失败测试（RED）

**Files:**
- Create: `cadence-init/skills/rule-config/tests/test_rule_config.py`

**Interfaces:**
- Consumes: Task 1 的 `ut-*` 清单。
- Produces: 加载方式与签名（Task 4-9 必须逐字实现）：

```python
import importlib.util
from pathlib import Path
SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "rule-config.py"
spec = importlib.util.spec_from_file_location("rule_config", SCRIPT_PATH)
rc = importlib.util.module_from_spec(spec); spec.loader.exec_module(rc)
# rc.merge_markdown / rc.merge_yaml / rc.l0_block / rc.precheck_openspec_structure
# rc.backup_file / rc.atomic_write / rc.sha256_file / rc.classify_l1
```

- [ ] **Step 1: 写 merge_markdown 失败测试**

```python
class TestMergeMarkdown(unittest.TestCase):
    def test_appends_project_only_sections_in_order(self):
        tpl = "# T\n\n## A\ntpl-a\n\n## B\ntpl-b\n"
        old = "# T\n\n## A\nold-a\n\n## C\nold-c\n"
        out = rc.merge_markdown(tpl, old)
        self.assertIn("tpl-a", out); self.assertIn("## C", out)
        self.assertLess(out.index("## B"), out.index("## C"))
    def test_same_name_section_gets_project_supplement(self):
        tpl = "## 1. 规则\ntpl-line\n"
        old = "## 1. 规则\ntpl-line\nold-line\n"
        out = rc.merge_markdown(tpl, old)
        self.assertEqual(out.count("tpl-line"), 1)  # 去重
        self.assertIn("项目补充", out); self.assertIn("old-line", out)
    def test_numbering_stripped_for_identity(self):
        self.assertIn("old", rc.merge_markdown("## 规则\nx\n", "## 3. 规则\nx\nold\n"))
    def test_unparseable_returns_none(self):
        self.assertIsNone(rc.merge_markdown("# T\nx\n", "\x00\x01binary"))
```

- [ ] **Step 2: 写 l0_block 失败测试**

覆盖 `skip`（v1 标记对+内容一致）、`drift`（标记对+内容不同）、`insert`（无标记）、`upgrade`（旧版标记对）、`broken`（单侧/乱序标记）。

- [ ] **Step 3: 写 merge_yaml 与 precheck 失败测试**

```python
TPL = (Path(__file__).resolve().parents[1] / "references" / "openspec" / "config.yaml").read_text()
def test_appends_template_rules_dedup_preserving_order(self):
    existing = "schema: spec-driven\ncontext: |\n  line1\nrules:\n  proposal:\n    - keep-me\n"
    merged, conflicts = rc.merge_yaml(TPL, existing)
    doc = yaml.safe_load(merged)
    self.assertEqual(doc["rules"]["proposal"][0], "keep-me")
    self.assertIn("记录 Why、范围、非目标和受影响 capability；不要写精确文件级实施步骤。", doc["rules"]["proposal"])
def test_rules_apply_reported_as_conflict(self):
    _, conflicts = rc.merge_yaml(TPL, "rules:\n  apply:\n    - x\n")
    self.assertEqual(conflicts[0]["kind"], "rules.apply")
def test_type_conflict_listed(self):
    self.assertIn("rules.proposal", rc.precheck_openspec_structure({"rules": {"proposal": "not-a-list"}}))
```

- [ ] **Step 4: 写 backup/atomic/classify_l1 失败测试**

备份名正则 `.*\.cadence-backup-\d{14}(-\d+)?$`（接受可选 `-N` 同秒冲突后缀）；备份后原文件 `sha256_file` 不变；`atomic_write` 后内容一致。`classify_l1(path, template_text, known_versions)`：注入 `known_versions={"v0": 旧版文本}` 覆盖 upgrade（文件与 v0 逐字一致→`upgrade`）；v1 一致→`skip`；v1 漂移/无标记→`replace`。

- [ ] **Step 5: 运行确认 RED**

Run: `cd cadence-init/skills/rule-config && python3 -m unittest discover -s tests -v > /tmp/ut.log 2>&1; s=$?; echo "exit=$s"; tail -3 /tmp/ut.log`
Expected: `exit!=0`（`scripts/rule-config.py` 不存在，importlib 加载失败）。

- [ ] **Step 6: 提交**

```bash
git add cadence-init/skills/rule-config/tests/test_rule_config.py
git commit -m "test(rule-config): 纯函数库失败测试（RED）"
```

### Task 3: 集成 harness 改造 + 新用例 + 静态契约 + 预算断言（RED）

**Files:**
- Modify: `cadence-init/skills/rule-config/tests/verify-managed-lifecycle.sh`
- Create: `cadence-init/skills/rule-config/tests/helpers/run-script.sh`
- Create: `cadence-init/skills/rule-config/tests/helpers/fake-codegraph.sh`

**Interfaces:**
- Consumes: Task 1 的 `it-*`/`sc-*` 清单、Task 2 签名。
- Produces（后续 Task 与全部用例依赖，逐字实现）：

```bash
# helpers/run-script.sh（由 verify-managed-lifecycle.sh 顶部定义 TEST_DIR 后 source）
TEST_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"   # tests/
SKILL_DIR="$(cd "$TEST_DIR/.." && pwd)"                        # rule-config/
SCRIPT="$SKILL_DIR/scripts/rule-config.py"
SKILL_MD="$SKILL_DIR/SKILL.md"
run_script() {  # run_script <dry-run|apply> <fixture_root> [extra args]
  local mode="$1" root="$2"; shift 2
  REPORT="$(mktemp /tmp/rule-config-report.XXXXXX)"
  set +e
  python3 "$SCRIPT" "$mode" --project-root "$root" --report "$REPORT" "$@"
  RUN_STATUS=$?
  set -e
}
jqr() { python3 -c "import json,sys;print(json.load(open('$REPORT'))$1)"; }  # 用法: jqr "['overall']"
fake_codegraph() {  # fake_codegraph <bin_dir> <install_rc> <init_rc> <status_rc> <write_config 0|1>
  sed -e "s/@INSTALL_RC@/$2/" -e "s/@INIT_RC@/$3/" -e "s/@STATUS_RC@/$4/" -e "s/@WRITE_CONFIG@/$5/" \
    "$TEST_DIR/helpers/fake-codegraph.sh" > "$1/codegraph"; chmod +x "$1/codegraph"
}
```

- [ ] **Step 1: 写 helper 并替换 harness 头部**

创建 `helpers/run-script.sh`（内容如上，逐字）；创建 `helpers/fake-codegraph.sh`：按 `$1` 分发——`version` 打印版本退出 0；`install` 在 `@WRITE_CONFIG@=1` 时向 cwd 写 `.mcp.json` 与 `.codex/config.toml`（`=0` 不写）后退出 `@INSTALL_RC@`；`init` 退出 `@INIT_RC@`（=0 时 `mkdir -p .codegraph`）；`status` 退出 `@STATUS_RC@`。harness 顶部：`TEST_DIR="$(cd "$(dirname "$0")" && pwd)"; source "$TEST_DIR/helpers/run-script.sh"`；删除 `source helpers/managed-lifecycle-reference.sh` 与 `run_reference()`；**删除** `assert_fresh_change_contract`（instructions 验证已废弃），**保留改造** `assert_bounded_source_scan_contract`：改为断言脚本 `PRUNE_DIRS` 常量与 SKILL.md 剪枝清单一致。

- [ ] **Step 2: 迁移既有 22 用例到 CLI 驱动**

逐用例改为"准备 fixture → run_script → 断言文件系统 + `jqr` 断言 report"；OpenSpec 用例删除 `openspec instructions` 与临时 change，改为 `jqr "['steps']"` 提取 openspec_config 动作 + `python3 -c "import yaml..."` 逐字段比对合并结果。全部失败关闭用例用 `record_result <name> "$RUN_STATUS" "$before_hash" "$after_hash" pass|fail` 记录场景、退出状态、运行前后 SHA-256（沿用现有 record_result 五参签名）。

- [ ] **Step 3: 新增缺口用例（按 Task 1 映射表）**

`it-dryrun-zero-write`（dry-run 前后用现有 `managed_block_hash` 对 fixture 全树取 hash 一致，report 含每资产动作/冲突/备份需求）；`it-decisions-missing|unknown|duplicate|stale`（普通模式 apply，各断言 `RUN_STATUS!=0` + fixture hash 不变 + report 含原因）；`it-s5-history-report-only`；`it-s5-history-migrate`；`it-s3-normal-keep-decision`（decisions 显式 `keep`→不覆盖）；`it-s3-markdown-unparseable-fallback`；`it-l1-drift-replace`、`it-l1-unknown-replace`（no-interrupt，结果**不含**"项目补充"；upgrade 分支仅由 Task 2 单测参数注入覆盖，说明原因：仓库仅存在 v1 规范源）；`it-s1-techstack-written`；`it-s6-gitignore-*`；`it-s3-playwright-*`；`it-s8-*`（`fake_codegraph` 覆盖：install_rc=1 仍补双配置 degraded、init_rc=1 degraded、status_rc=1 degraded、`.codegraph/` 已存在只 status、write_config=0 时脚本补双方、非 Coding+`--enable-codegraph`；PATH 前置 fake bin）；`it-s1-conflict-noncoding-default`；`it-intent-params`；`it-entry-summary-number-conflict`；`it-entry-base-created`。故障注入：`mode=$(stat -c %a "$d" 2>/dev/null || stat -f %Lp "$d"); chmod 555 "$d"`，cleanup `chmod "$mode" "$d"`，断言 `RUN_STATUS!=0` + 原文件 hash 不变。

- [ ] **Step 4: 新增静态契约检查 `sc-*`（全部可执行，`record_result` 五参逐字调用）**

```bash
grep -q 'disable-model-invocation: true' "$SKILL_MD" \
  && record_result sc-disable-model-invocation 0 present present pass \
  || record_result sc-disable-model-invocation 1 present missing fail
grep -qE 'no-interrupt.*--no-interrupt|--no-interrupt.*no-interrupt' "$SKILL_MD" \
  && record_result sc-bare-token 0 present present pass || record_result sc-bare-token 1 present missing fail
grep -q 'dry-run' "$SKILL_MD" && grep -q 'apply' "$SKILL_MD" \
  && record_result sc-two-phase 0 present present pass || record_result sc-two-phase 1 present missing fail
for d in .venv venv env .env node_modules vendor; do
  grep -q -- "$d" "$SKILL_MD" || record_result "sc-prune-list-$d" 1 present missing fail
done
test -f "$SCRIPT" \
  && record_result sc-script-exists 0 present present pass || record_result sc-script-exists 1 present missing fail
# routing-conformance delta 静态检查：
diff -q "$SKILL_DIR/references/rules/openspec-superpowers-workflow.md" \
        "$REPO_ROOT/.claude/rules/openspec-superpowers-workflow.md" >/dev/null \
  && record_result sc-l1-source-copy-sync 0 same same pass || record_result sc-l1-source-copy-sync 1 same diff fail
python3 -c "import yaml;d=yaml.safe_load(open('$REPO_ROOT/openspec/config.yaml'));assert 'apply' not in (d.get('rules') or {})" \
  && record_result sc-no-rules-apply 0 absent absent pass || record_result sc-no-rules-apply 1 absent present fail
# L0 引用的规则文件存在性：提取 CLAUDE.md L0 区块内 .claude/rules/*.md 引用逐一 test -f
python3 - "$REPO_ROOT/CLAUDE.md" <<'EOF'
import re,sys,os
text=open(sys.argv[1]).read()
refs=set(re.findall(r'\.claude/rules/[\w.-]+\.md', text))
missing=[r for r in refs if not os.path.exists(os.path.join(os.path.dirname(sys.argv[1]), r))]
print('\n'.join(missing)); sys.exit(1 if missing else 0)
EOF
  && record_result sc-l0-rule-refs-exist 0 none none pass || record_result sc-l0-rule-refs-exist 1 none missing fail
# 瘦身 SKILL 不得含直接读写目标项目文件的操作指令
! grep -qE '读取内容，写入项目的|将以下文件从.*写入' "$SKILL_MD" \
  && record_result sc-no-direct-target-writes 0 absent absent pass \
  || record_result sc-no-direct-target-writes 1 absent present fail
```

- [ ] **Step 5: 新增预算断言 `it-budget`**

空 fixture（仅 `app.py`）→ `run_script apply "$fx" --no-interrupt` → `jqr "['budget_seconds_excluding_codegraph']"` 断言 `< 60`；断言 report 的 codegraph 步骤含独立 `elapsed_ms`。

- [ ] **Step 6: 运行确认 RED**

Run: `bash cadence-init/skills/rule-config/tests/verify-managed-lifecycle.sh > /tmp/it.log 2>&1; s=$?; echo "exit=$s"; tail -5 /tmp/it.log`
Expected: `exit!=0`，集成用例大面积 fail；`SUMMARY fail>0`。

- [ ] **Step 7: 提交**

```bash
git add cadence-init/skills/rule-config/tests/
git commit -m "test(rule-config): 集成 harness 改测脚本 CLI，补缺口用例与静态契约（RED）"
```

### Task 4: 脚本骨架——CLI、报告、备份、原子写、decisions、全局备份屏障（GREEN 第一批）

**Files:**
- Create: `cadence-init/skills/rule-config/scripts/rule-config.py`

**Interfaces:**
- Consumes: Task 2/3 的调用约定。
- Produces（后续 Task 依赖的精确签名）：
  - `main(argv) -> int`；退出码 `0=success/degraded，1=failed，2=usage，77=missing-yaml`；`main()` 入口立即记录 `T0 = time.monotonic()`
  - `build_report(mode, project_root) -> dict`；`write_report(path, report)`；schema 冻结：`{overall, mode, project_root, project_type, budget_seconds_excluding_codegraph, steps:[{name,status,elapsed_ms,actions:[{file,action,detail,backup}],note}], conflicts:[{conflict_id,asset,state,question,recommendation}], backups:[], hints:{next:"mcp-configuration"}, failure:{file,reason,recovery}|None}`
  - `validate_external_path(p: Path, root: Path) -> None`（根内→`UsageError`）
  - `class Intents(NamedTuple): no_interrupt: bool; project_type: str|None; ignore_cadence: bool; enable_playwright: bool; enable_codegraph: bool; decisions: Path|None`
  - `load_decisions(path: Path) -> list[dict]`；`validate_decisions(plan: dict, decisions: list[dict]) -> list[str]`（返回违规清单：缺失/未知/重复/过期，空=通过；仅普通模式且 plan 有冲突时调用）
  - `ensure_parent(path: Path) -> None`（`path.parent.mkdir(parents=True, exist_ok=True)`）

- [ ] **Step 1: 实现骨架**

argparse 子命令 dry-run/apply；`import yaml` try/except（except→构造 failed 报告写 `--report` 后 `sys.exit(77)`）；`backup_file`（`shutil.copy2`，命名 `<file>.cadence-backup-%Y%m%d%H%M%S`，失败抛 `BackupError`）；`atomic_write`（先 `ensure_parent`，同目录 `tempfile.mkstemp` + 写入 + `os.replace`，任何一步异常→删临时文件抛 `PublishError`，目标文件不变）；`sha256_file`（hashlib）；`validate_external_path`。

- [ ] **Step 2: 实现两阶段骨架、decisions 校验与全局备份屏障**

`compute_plan(root, intents) -> dict`（S1-S8 各步只读探测，填充 actions/conflicts/backup_needs）；dry-run=compute_plan+写报告；apply 顺序冻结：
1. `compute_plan`；
2. 普通模式且 plan 有冲突→`load_decisions`+`validate_decisions`，违规→failed 报告+退出 1+零写入；
3. **全局备份屏障**：汇总 plan 全部 backup_needs 逐一 `backup_file`，任一失败→终止零发布（已建备份列入 `backups[]`）；
4. 屏障通过后按 S1-S8 执行发布（no-interrupt 的冲突决策在屏障前按权威规则写入 plan.actions）；
5. S7 完成时写 `budget_seconds_excluding_codegraph = time.monotonic() - T0`；异常兜底 `except Exception`→`overall=crashed`+写报告+退出 1。

- [ ] **Step 3: 跑 Task 2 部分单测与 Task 3 两阶段用例**

Run: `cd cadence-init/skills/rule-config && python3 -m unittest discover -s tests -k backup -k atomic > /tmp/ut.log 2>&1; s1=$?; bash tests/verify-managed-lifecycle.sh > /tmp/it.log 2>&1; s2=$?; echo "ut=$s1 it=$s2"; grep -E "it-dryrun|it-decisions" /tmp/it.log`
Expected: `ut=0`；`it-dryrun-zero-write` 与 `it-decisions-missing` pass（其余待 S1-S8 实现，本轮 `it` 仍非 0）。

- [ ] **Step 4: 提交**

```bash
git add cadence-init/skills/rule-config/scripts/rule-config.py
git commit -m "feat(rule-config): 脚本骨架——CLI/报告/备份/原子写/decisions/全局备份屏障"
```

### Task 5: S1 检测 + S2 模板定位（GREEN）

**Files:**
- Modify: `cadence-init/skills/rule-config/scripts/rule-config.py`

**Interfaces:**
- Produces: `detect_project(root, intents) -> dict(project_type, evidence, tech_stack)`；`locate_templates() -> tuple[Path, Path]`（rules_root, openspec_yaml）；`PRUNE_DIRS`、`SOURCE_EXTS`、`TEMPLATE_REQUIRED` 常量（`sc-prune-list` 断言来源）。

- [ ] **Step 1: 实现有界检测**

`os.walk` 首命中即停：`PRUNE_DIRS={'.git','.claude','.claude-plugin','.codex','.pi','.codegraph','cadence-init','Cadence-skills','node_modules','vendor','venv','.venv','env','.env','dist','build','coverage','.next','target','__pycache__'}` 剪枝，`SOURCE_EXTS` 13 个扩展名首命中返回相对路径；无命中再查 6 个主工程配置。技术栈检测：package.json scripts 提取 test/lint/format、requirements.txt/pyproject.toml 检测 pytest；未检出="未检测到"；`intents.project_type` 优先；矛盾判定→冲突项 `s1:project-type-conflict`。

- [ ] **Step 2: 实现三级模板定位**

依次检查 `~/.claude/plugins/marketplaces/cadence-skills-marketplace/cadence-init/skills/rule-config/references/rules/` 与 `~/.claude/plugins/marketplaces/cadence-skills-local/cadence-init/skills/rule-config/references/rules/` 固定路径，再 glob 回退 `**/cadence-init/skills/rule-config/references/rules/language.md`；成对校验 `agent-routing-kernel.md/language.md/openspec-superpowers-workflow.md`（回退加 `document-storage.md`）+ 同级 `references/openspec/config.yaml`；多候选取 mtime 最新；全不完整→`TemplateError` 终止并列缺失。

- [ ] **Step 3: 跑集成用例**

Run: `bash cadence-init/skills/rule-config/tests/verify-managed-lifecycle.sh > /tmp/it.log 2>&1; s=$?; echo "exit=$s"; grep -E "source-scan|template" /tmp/it.log`
Expected: `source-scan-*` 3 个与模板定位用例 pass（全量仍非 0）。

- [ ] **Step 4: 提交** `git commit -m "feat(rule-config): S1 有界检测与技术栈、S2 三级模板定位"`

### Task 6: S3 规则文件（含 L1 独立分支）+ S4 入口文件（GREEN 核心）

**Files:**
- Modify: `cadence-init/skills/rule-config/scripts/rule-config.py`
- Modify: `cadence-init/skills/rule-config/tests/test_rule_config.py`（如有补充用例）

**Interfaces:**
- Consumes: Task 2 签名、S2 产物。
- Produces: `step_rules_files(ctx)`；`step_entry_files(ctx)`；`parse_sections(text) -> list[Section]`（`Section(level, key, title, body_lines)`，key=级别+去编号标题）；`render_sections(sections) -> str`；`classify_l1(path: Path, template_text: str, known_versions: dict[str,str]) -> str`（`skip|upgrade|replace`）；L0 标记常量 `L0_BEGIN='<!-- cadence-managed:openspec-superpowers-routing:v1:start -->'`、`L0_END='<!-- cadence-managed:openspec-superpowers-routing:v1:end -->'`；`KNOWN_L1_VERSIONS = {"v1": <references/rules/openspec-superpowers-workflow.md 全文>}`（受支持旧版当前为空集）；`BASE_CLAUDE_MD`/`BASE_AGENTS_MD` 基础入口文本常量（含文件说明与 `## 强制规则` 骨架，供入口不存在时创建）；决策枚举 `replace|keep`。

- [ ] **Step 1: 实现 parse_sections/merge_markdown（使 Task 2 单测转 GREEN）**

按 `^(#{1,6})\s+(.+)$` 切章；key 去编号正则 `^\d+[.、．]?\s*`；合并：模板章节序为主，项目独有章节按原序追加，同名章节=模板正文+`\n\n**项目补充**\n`+项目去重行（按完整行去重、保序）；二进制/零章节且非空→返回 None。

- [ ] **Step 2: 实现 S3 普通规则 8 文件分支**

`ensure_parent` 后循环 8 个普通规则文件（**不含** `openspec-superpowers-workflow.md`）：不存在→读模板 `atomic_write`（created）；一致→skipped；冲突→普通模式：decisions 给 `keep`→不覆盖报告（缺失/未知/重复/过期已由 Task 4 `validate_decisions` 失败关闭，本步不再兜底）、给 `replace`→备份后写模板；no-interrupt→备份需求进 plan.backup_needs，屏障后 `merge_markdown`，返回 None→备份+标准结构+`\n\n## 原项目补充\n\n`+原文；Playwright 文件仅在 `intents.enable_playwright` 时处理。

- [ ] **Step 3: 实现 L1 独立分支**

`classify_l1`：当前 v1 标记且完整内容与规范源逐字一致→skip；`known_versions` 中某旧版逐字一致→（备份后）upgrade 为当前 v1；其余（v1 漂移/旧版漂移/无标记）→普通模式按 decisions（`replace`→备份替换、`keep`→保留报告），no-interrupt→备份后替换为当前 v1；**任何分支 MUST NOT 调用 merge_markdown，结果 MUST NOT 含"项目补充"**；备份经全局屏障，失败→终止不替换。

- [ ] **Step 4: 实现 l0_block 与 S4 单次写入、双入口屏障**

`l0_block` 五分类（Task 2 单测 GREEN）；S4：入口不存在→以 `BASE_CLAUDE_MD`/`BASE_AGENTS_MD` 为基线；统一预检（各自分类+目标动作+备份需求并入 plan.backup_needs，全局屏障任一失败→两入口零写入终止）→ 每入口内存合成最终文本（L0 插入位置=首个 `## 强制规则` 前、无则文件说明后；缺失摘要行追加；技术栈/包管理器/覆盖率 80% 块；规则 2 按项目类型选文本；摘要编号冲突→保留原文追加缺失并在 detail 说明）→ 各一次 `atomic_write`。

- [ ] **Step 5: 跑单测+集成**

Run: `cd cadence-init/skills/rule-config && python3 -m unittest discover -s tests > /tmp/ut.log 2>&1; s1=$?; bash tests/verify-managed-lifecycle.sh > /tmp/it.log 2>&1; s2=$?; echo "ut=$s1 it=$s2"; grep -E "l0-|l1-|rules-|entry-|markdown" /tmp/it.log | head -20`
Expected: `ut=0`；l0/l1/规则文件/入口相关集成用例 pass（含 `it-l1-*` 结果不含"项目补充"断言）。

- [ ] **Step 6: 提交** `git commit -m "feat(rule-config): S3 章节合并与 L1 独立分支、S4 入口单次写入与全局备份屏障"`

### Task 7: S5 目录/历史 + S6 gitignore（GREEN）

**Interfaces:**
- Produces: `step_scaffold(ctx)`；`step_gitignore(ctx)`；`HISTORY_DIRS`（16 个精确目录）、`CADENCE_DIRS`（17 个子目录）常量；`ensure_gitignore_line(root, line, comment) -> str`（`added|skipped`）。

- [ ] **Step 1: 实现 S5**

`mkdir -p` 17 目录；历史目录检测仅 `HISTORY_DIRS`；no-interrupt→只写 report actions；普通模式→按 HM-01~03 迁移表（不存在→mv、空→内容移入+rmdir、非空→跳过+冲突报告）。

- [ ] **Step 2: 实现 S6**

行级判断后追加；`.codegraph/` 条件=（coding 或 enable_codegraph）；`cadence/` 仅 `intents.ignore_cadence`；`codegraph.json` 不处理。

- [ ] **Step 3: 跑集成**

Run: `bash cadence-init/skills/rule-config/tests/verify-managed-lifecycle.sh > /tmp/it.log 2>&1; s=$?; echo "exit=$s"; grep -E "s5-|s6-|history|gitignore" /tmp/it.log`
Expected: 相关用例 pass。

- [ ] **Step 4: 提交** `git commit -m "feat(rule-config): S5 目录与历史迁移、S6 gitignore 幂等"`

### Task 8: S7 OpenSpec 配置（GREEN）

**Interfaces:**
- Produces: `step_openspec_config(ctx)`；决策枚举 `remove_apply|keep`。

- [ ] **Step 1: 实现 merge_yaml/precheck（Task 2 单测 GREEN）**

`yaml.safe_load` 双方；precheck 类型矩阵（根映射/schema 标量/context str/rules 映射/四 artifact str 列表）；合并：保留 schema（缺省 `spec-driven`）；context 按完整行去重追加模板四行；rules 四 artifact 数组追加去重保序；`rules.apply`→conflict（普通模式：decisions 给 `remove_apply`→备份后移除，给 `keep`→保留报告，缺失决策已由 validate_decisions 失败关闭；no-interrupt→备份后移除）；无法解析/类型不兼容→普通模式保留+报告字段路径与类型，no-interrupt 备份后无法无损→终止。

- [ ] **Step 2: 实现 S7 发布**

`ensure_parent(root/'openspec/config.yaml')`→候选写目标同目录临时文件→precheck→备份需求进 plan.backup_needs（全局屏障）→`atomic_write` 发布；全程无临时 change、无 `openspec instructions`；失败→终止、原文件不变、report 含失败详情。

- [ ] **Step 3: 跑集成**

Run: `bash cadence-init/skills/rule-config/tests/verify-managed-lifecycle.sh > /tmp/it.log 2>&1; s=$?; echo "exit=$s"; grep -E "openspec|yaml|apply-key|atomic" /tmp/it.log`
Expected: pass（含 555 原子发布失败、只读父目录备份失败两故障注入用例，cleanup 已按保存的 mode 恢复）。

- [ ] **Step 4: 提交** `git commit -m "feat(rule-config): S7 OpenSpec 候选结构预检、保守合并与原子发布"`

### Task 9: S8 CodeGraph + 预算计时收口（GREEN）

**Interfaces:**
- Produces: `step_codegraph(ctx)`；`has_codegraph_mcp_mcpjson(root) -> bool`；`has_codegraph_mcp_codex(root) -> bool`；`CODEX_MCP_BLOCK`（toml 文本常量：`[mcp_servers.codegraph]\ncommand = "codegraph"\nargs = ["serve", "--mcp"]`）。

- [ ] **Step 1: 实现状态矩阵**

启用条件=（coding 或 enable_codegraph）；`.codegraph/` 存在→仅 `codegraph status`；双 MCP 配置齐全→跳过写入；任一缺失→`subprocess.run(["codegraph","install","--target=claude,codex","--location=local","--yes"], cwd=project_root)`→再核验、仅补仍缺失方（`.codex/config.toml` 追加 `CODEX_MCP_BLOCK`，`.mcp.json` 按兜底 JSON 合并）；`.codegraph/` 不存在→install+`codegraph init`（同样 `cwd=project_root`）。

- [ ] **Step 2: 实现失败降级与预算口径**

install 失败→仍补齐双配置+`status=degraded`+note；init/status 失败→degraded+note；配置补写/备份/原子写失败→抛错终止；S8 全程 `elapsed_ms` 单独计时；**预算 = S7 完成时的 `time.monotonic() - T0`**（T0 为 main 入口单一起点，含 CLI 解析与步骤间耗时），写入 `budget_seconds_excluding_codegraph`。

- [ ] **Step 3: 跑集成 + 全量（fake codegraph 驱动）**

Run: `bash cadence-init/skills/rule-config/tests/verify-managed-lifecycle.sh > /tmp/it.log 2>&1; s1=$?; cd cadence-init/skills/rule-config && python3 -m unittest discover -s tests > /tmp/ut.log 2>&1; s2=$?; echo "it=$s1 ut=$s2"; tail -3 /tmp/it.log; tail -3 /tmp/ut.log`
Expected: `it=0 ut=0`；`SUMMARY fail=0`（含 `it-s8-*` 与 `it-budget`）；单测全 PASS。

- [ ] **Step 4: 删除参考模型并提交**

```bash
git rm cadence-init/skills/rule-config/tests/helpers/managed-lifecycle-reference.sh
git add cadence-init/skills/rule-config/
git commit -m "feat(rule-config): S8 CodeGraph 增量矩阵与降级、预算计时收口；删除 shell 参考模型"
```

### Task 10: references/merge-semantics.md（语义迁移）

**Files:**
- Create: `cadence-init/skills/rule-config/references/merge-semantics.md`

- [ ] **Step 1: 按 Task 1 映射表誊写十张表**

逐行迁移 NC/OS/L1/L0/RF/SM/OP/CS/CG/HM（design D2 行 ID 基线），每行含全部八列（行 ID/资产/冲突状态/普通模式动作/no-interrupt 动作/备份要求/报告要求/对应测试 ID），每表前注来源（现行 SKILL.md 行号区间）；补备份命名、原子发布、全局备份屏障、失败关闭、决策文件 schema、模板三级定位精确规则正文。

- [ ] **Step 2: 对账**

行数与 design D2 基线一致（8+8+7+7+4+3+4+8+8+3=60 行）；八列无空缺；与 Task 1 映射表交叉引用一致。

- [ ] **Step 3: 提交** `git commit -m "docs(rule-config): 合并语义权威正文迁移至 references"`

### Task 11: SKILL.md 重写 + 文档更新

**Files:**
- Modify: `cadence-init/skills/rule-config/SKILL.md`（758 行→约 150 行）
- Modify: `cadence-init/skills/rule-config/references/rules/README.md`（如审计发现引用过期行为）

- [ ] **Step 1: 重写 SKILL.md**

保留 frontmatter（`name`、`description`、`disable-model-invocation: true`）；章节：概述、参数模式（裸 token 与 `--no-interrupt` 等价规范化、四个意图参数）、调用方式（定位 `<skill 安装根>/cadence-init/skills/rule-config/scripts/rule-config.py`，pre-check 同款约定；PyYAML 缺失退出码 77→`uvx --with pyyaml python` 重跑）、两阶段流程（dry-run→读 plan→普通模式逐条 AskUserQuestion→**无响应时 Agent 将推荐默认决策显式写入** decisions.json（/tmp）→apply；no-interrupt 单次 apply）、有界扫描说明（剪枝清单全文保留，供 sc-prune-list）、报告解读（`python3 -c` 提取示例）、失败关闭（退出码表、恢复建议）、下一步 mcp-configuration 交接、合并语义指向 `references/merge-semantics.md`。**不得**包含"读取内容，写入项目的"等由 Agent 直接读写目标文件的指令。

- [ ] **Step 2: 审计并同步引用文档**

检查 `references/rules/README.md` 与 `cadence/archive/INDEX.md` 等提及 rule-config 行为的位置：README"从旧版迁移"段若与两阶段脚本流程冲突则更新为等价新表述；历史归档索引不改。

- [ ] **Step 3: 跑静态契约与全量回归**

Run: `bash cadence-init/skills/rule-config/tests/verify-managed-lifecycle.sh > /tmp/it.log 2>&1; s=$?; echo "exit=$s"; tail -3 /tmp/it.log`
Expected: `exit=0`，含 `sc-*` 全 pass、`SUMMARY fail=0`。

- [ ] **Step 4: 提交** `git commit -m "refactor(rule-config): SKILL 瘦身为编排骨架，语义迁移 references"`

### Task 12: 验收与收尾

- [ ] **Step 1: 双平台与工具链回归**

macOS 与 Linux 各跑一次全量；受控 PATH 验证 sha256sum 默认路径与 shasum 回退路径均 `SUMMARY fail=0`；`bash -n cadence-init/skills/rule-config/tests/verify-managed-lifecycle.sh`；`git diff --check`。

- [ ] **Step 2: 真实环境预算验收**

Claude Code 空项目执行 `/rule-config --no-interrupt`：人工计时 Skill 触发→最终汇报（扣 S8 区间）≤5 分钟；抽查合并/备份/幂等/历史目录/意图参数行为符合 specs；记录证据（报告 JSON + 计时）。

- [ ] **Step 3: 契约校验与勾选**

`openspec validate --all --strict` 通过；勾选 `openspec/changes/script-rule-config-for-speed/tasks.md` 全部工作包。

- [ ] **Step 4: 提交推送**

```bash
git add -A && git commit -m "test(rule-config): 双平台回归与预算验收证据"
git push origin feat-b-rule-config-cost-time
```

---

## Self-Review 记录

- **Spec 覆盖**：6 个 requirement ↔ Task 4-9（两阶段/合并/OpenSpec/报告/预算）、Task 1/3（对账与验收）、Task 10-11（语义迁移与编排）；routing-conformance delta ↔ Task 3 Step 2（失败关闭用例记录场景/退出状态/前后 SHA-256）与 Step 4（sc-l1-source-copy-sync/sc-no-rules-apply/sc-l0-rule-refs-exist 等）。
- **占位符扫描**：无 TBD/TODO；helper、静态检查、故障注入、标记常量、toml 块均为完整可执行文本。
- **类型一致性**：`merge_markdown/merge_yaml/l0_block/classify_l1/precheck_openspec_structure/backup_file/atomic_write/sha256_file/ensure_parent/run_script/jqr/fake_codegraph` 签名在 Task 2-9 与 Global Constraints 间逐字一致。
- **评审修订记录**：第一轮 10 条与第二轮 10 条全部闭合——第二轮：helper 路径 `../..` 与 TEST_DIR 解析、`set +e` 退出码捕获、静态检查全量可执行五参 `record_result`、全局备份屏障（compute_plan→全量备份→发布）、record_result 记录场景/退出码/前后 SHA-256、sc-l0-rule-refs-exist 与 sc-no-direct-target-writes、decisions 语义统一（无响应=Agent 写显式默认；缺失=失败关闭）、验证命令 `s=$?` 模式与 `-k backup -k atomic` 双 flag、codegraph `cwd=project_root` 与 fake 五参 write_config 两态、L0_END 全字面值与 known_versions 空集说明（upgrade 单测注入）、mktemp 去 .json 后缀与 stat 保存恢复权限。
