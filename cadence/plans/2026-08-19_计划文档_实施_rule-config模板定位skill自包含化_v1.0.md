# rule-config 模板定位 skill 自包含化 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** rule-config 的规则/配置模板定位从"写死的三级客户端路径"改为"脚本自身所在 skill 目录（`SKILL_DIR`）单源唯一定位"，缺件即失败关闭；删除 marketplace/local/glob 全部外部候选。

**Architecture:** 引入模块级 `SKILL_DIR = Path(__file__).resolve().parent.parent` 常量；`locate_templates()` 重写为"SKILL_DIR/references/ 四件套 + openspec/config.yaml 成对校验，缺任一 TemplateError"；`_load_reference`/`_load_kernel_source` 改用同一常量。skill 包自包含：脚本、模板、references 同船分发。

**Tech Stack:** Python 3（标准库 + PyYAML）、pytest、bash 生命周期套件。

**Spec:** `openspec/changes/rule-config-self-contained-templates/`（proposal/design/specs/tasks —— 本计划只展开该契约）

**OpenSpec 工作包映射：** Task 1 ↔ tasks.md 工作包 1（测试先行）；Task 2 ↔ 工作包 2（脚本实现）；Task 3 ↔ 工作包 3（文档对账）；Task 4 ↔ 工作包 4（全量验证）。

## Global Constraints

- 模板唯一定位：`SKILL_DIR/references/`；禁止任何 `~/.claude/plugins/` 等客户端路径候选与全局搜索回退。
- 必备文件清单固定：`references/rules/` 下 `agent-routing-kernel.md`、`language.md`、`openspec-superpowers-workflow.md`、`document-storage.md`，及 `references/openspec/config.yaml`。缺任一 → `TemplateError`，非零退出、目标项目零写入、报告缺失清单与"请重新安装 skill"。
- 模板定位不得依赖 `HOME` 环境变量。
- `resolve()` 必须保留（软链安装解析到真实仓库）。
- compute_plan 的 `TemplateError → plan["failure"]` 与 step_s2 的报告回填语义不变（调用点不改）。
- 测试运行目录：`cadence-init/skills/rule-config/`；pytest `uv run --with pytest python3 -m pytest tests/test_rule_config.py -q`；shell `bash tests/verify-managed-lifecycle.sh`。
- 提交信息遵循仓库既有风格。

---

### Task 1: 测试改写（pytest 重写 + shell 反转 + 回归用例）

**映射：** tasks.md 1.1/1.2/1.3；spec「模板与脚本必须同源」三个 scenario。

**Files:**
- Test: `cadence-init/skills/rule-config/tests/test_rule_config.py`（替换 `TestLocateTemplates` 整类，约 1078-1251 行）
- Test: `cadence-init/skills/rule-config/tests/verify-managed-lifecycle.sh`（C16e 约 1471-1489 行；ONLINE_TEMPLATE_SKILL fixture 约 106-108 行）

**Interfaces:**
- Consumes: 现有 `rc.locate_templates() -> (rules_root: Path, openspec_yaml: Path)`、`rc.TemplateError`、测试工具 `mock`/`tempfile`/`os`（模块已导入）。
- Produces（Task 2 实现的对照契约）: `rc.SKILL_DIR: Path` 模块级常量；`locate_templates()` 返回 `SKILL_DIR/references/rules` 与 `SKILL_DIR/references/openspec/config.yaml`；缺件时 `TemplateError` 消息含每个缺失的相对路径与"重新安装"字样。

- [ ] **Step 1: 重写 `TestLocateTemplates` 整类（红）**

整个类（`class TestLocateTemplates` 到下一个 class 之前，含 setUp 与全部八个用例）替换为：

```python
class TestLocateTemplates(unittest.TestCase):
    """ut-locate_templates-* / skill 自包含单源定位契约（S1b 重构）。"""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def _make_skill_dir(self, missing=()):
        """构造完整 skill 目录 fixture：<root>/skill/，可按 missing 缺件。"""
        skill = self.root / "skill"
        rules = skill / "references" / "rules"
        rules.mkdir(parents=True)
        for name in ("agent-routing-kernel.md", "language.md",
                     "openspec-superpowers-workflow.md", "document-storage.md"):
            if name not in missing:
                (rules / name).write_text(f"tpl:{name}\n", encoding="utf-8")
        (skill / "references" / "openspec").mkdir(parents=True)
        if "config.yaml" not in missing:
            (skill / "references" / "openspec" / "config.yaml").write_text(
                "schema: spec-driven\n", encoding="utf-8"
            )
        return skill

    def test_skill_dir_templates_preferred(self):
        """ut-locate_templates-skill-dir / S1b-01（skill 目录完整 → 以其 references 为唯一模板源）"""
        skill = self._make_skill_dir()
        with mock.patch.object(rc, "SKILL_DIR", skill):
            rules_root, openspec_yaml = rc.locate_templates()
        self.assertEqual(rules_root, skill / "references" / "rules")
        self.assertEqual(
            openspec_yaml, skill / "references" / "openspec" / "config.yaml"
        )

    def test_missing_files_raise_template_error_with_list(self):
        """ut-locate_templates-incomplete / S1b-02（缺件 → TemplateError 且列出缺失清单与重装建议）"""
        skill = self._make_skill_dir(missing=("document-storage.md", "config.yaml"))
        with mock.patch.object(rc, "SKILL_DIR", skill):
            with self.assertRaises(rc.TemplateError) as ctx:
                rc.locate_templates()
        msg = str(ctx.exception)
        self.assertIn("document-storage.md", msg)
        self.assertIn("config.yaml", msg)
        self.assertIn("重新安装", msg)

    def test_no_home_dependency(self):
        """ut-locate_templates-no-home / S1b-03（HOME 为空目录仍命中 skill 目录）"""
        skill = self._make_skill_dir()
        empty_home = self.root / "empty-home"
        empty_home.mkdir()
        with mock.patch.object(rc, "SKILL_DIR", skill), \
                mock.patch.dict(os.environ, {"HOME": str(empty_home)}):
            rules_root, _ = rc.locate_templates()
        self.assertEqual(rules_root, skill / "references" / "rules")

    def test_stale_marketplace_copy_ignored(self):
        """ut-locate_templates-ignore-stale-marketplace / 回归（naruto 事故场景）：
        过期 marketplace 副本存在且内容不同，仍取 skill 目录模板。"""
        skill = self._make_skill_dir()
        stale_home = self.root / "home"
        mkt_rules = (
            stale_home / ".claude" / "plugins" / "marketplaces"
            / "cadence-skills-marketplace" / "cadence-init" / "skills"
            / "rule-config" / "references" / "rules"
        )
        mkt_rules.mkdir(parents=True)
        for name in ("agent-routing-kernel.md", "language.md",
                     "openspec-superpowers-workflow.md", "document-storage.md"):
            (mkt_rules / name).write_text("旧模板内容\n", encoding="utf-8")
        (mkt_rules.parent.parent / "openspec").mkdir(parents=True)
        (mkt_rules.parent.parent / "openspec" / "config.yaml").write_text(
            "schema: spec-driven\n", encoding="utf-8"
        )
        with mock.patch.object(rc, "SKILL_DIR", skill), \
                mock.patch.dict(os.environ, {"HOME": str(stale_home)}):
            rules_root, _ = rc.locate_templates()
        self.assertEqual(rules_root, skill / "references" / "rules")
        self.assertNotEqual(str(rules_root), str(mkt_rules))
```

- [ ] **Step 2: 运行确认红**

Run: `cd cadence-init/skills/rule-config && uv run --with pytest python3 -m pytest tests/test_rule_config.py::TestLocateTemplates -q`
Expected: FAIL（`rc.SKILL_DIR` 不存在 → patch AttributeError / 新契约未实现）。其余测试类不受影响。

- [ ] **Step 3: shell C16e 语义反转（红）**

`verify-managed-lifecycle.sh` C16e 段（约 1471-1489 行）整段替换为：

```bash
# C16e. 空 HOME 仍可运行——模板来自 skill 目录，不依赖 HOME（it-s2-skill-self-contained / §11.5）。
# 2026-08-19 语义反转：旧契约为「候选全缺 → 失败关闭」；新契约（skill 自包含）下 HOME 无关。
case_root="$TEST_ROOT/fx-templates-missing"
mkdir -p "$case_root"
printf '# placeholder\n' > "$case_root/README.md"
fake_home="$TEST_ROOT/fake-home-empty"
mkdir -p "$fake_home"
REPORT="$(mktemp /tmp/rule-config-report.XXXXXX)"
set +e
HOME="$fake_home" "$(command -v python3)" "$SCRIPT" apply --project-root "$case_root" --report "$REPORT" --no-interrupt >/dev/null 2>&1
RUN_STATUS=$?
set -e
if [ "$RUN_STATUS" -eq 0 ] \
  && ! jqr "['overall']" 2>/dev/null | grep -qix 'fail'; then
  record_result it-s2-skill-self-contained "$RUN_STATUS" "-" "-" pass
else
  record_result it-s2-skill-self-contained "$RUN_STATUS" "-" "-" fail
fi
```

- [ ] **Step 4: shell 删除 ONLINE_TEMPLATE_SKILL fixture（约 106-108 行）**

删除三行 fixture 搭建。先 `grep -n 'ONLINE_TEMPLATE_SKILL\|TEST_HOME' tests/verify-managed-lifecycle.sh` 确认无其他引用；若 `TEST_HOME` 仍被别处使用则保留其定义，仅删 marketplace 铺陈三行。

- [ ] **Step 5: 运行确认红**

Run: `bash tests/verify-managed-lifecycle.sh`
Expected: `it-s2-skill-self-contained` FAIL（旧脚本在空 HOME 下 TemplateError、非零退出）；其余 pass。

- [ ] **Step 6: Commit（测试红态快照）**

```bash
git add cadence-init/skills/rule-config/tests/
git commit -m "test(rule-config): 模板定位 skill 自包含契约测试（红态）"
```

---

### Task 2: 脚本实现（SKILL_DIR 常量 + locate_templates 单源重写）

**映射：** tasks.md 2.1/2.2；spec「模板与脚本必须同源」requirement。

**Files:**
- Modify: `cadence-init/skills/rule-config/scripts/rule-config.py`（常量区 ~417-432；`_load_reference` ~236-243；`_load_kernel_source` ~1926-1934；`locate_templates` 全体 ~1784-1860 及其辅助）

**Interfaces:**
- Consumes: Task 1 的测试契约。
- Produces: `SKILL_DIR`（Path）、新 `locate_templates()`；删除 `_ONLINE_RULES_SUBPATH`、`_OFFLINE_RULES_SUBPATH`、`_FALLBACK_GLOB_PATTERN`、`TEMPLATE_REQUIRED_FALLBACK`、`_format_template_failures` 及三级定位全部代码。

- [ ] **Step 1: 引入 `SKILL_DIR` 并统一三件套清单**

在常量区（`TEMPLATE_REQUIRED` 附近）：

```python
# skill 自包含唯一定位基准：脚本自身所在 skill 目录（软链经 resolve 解析到真实仓库）。
SKILL_DIR = Path(__file__).resolve().parent.parent
```

将 `TEMPLATE_REQUIRED` 扩为四件套并删除 `TEMPLATE_REQUIRED_FALLBACK`：

```python
TEMPLATE_REQUIRED = (
    "agent-routing-kernel.md",
    "language.md",
    "openspec-superpowers-workflow.md",
    "document-storage.md",
)
```

- [ ] **Step 2: `locate_templates()` 重写**

删除旧实现全体（含在线/离线/glob 逻辑与 `_format_template_failures`、候选校验辅助），替换为：

```python
def locate_templates() -> tuple:
    """模板定位：skill 自包含单源（契约「模板与脚本必须同源」）。

    唯一候选：SKILL_DIR/references/（rules/ 四件套 + openspec/config.yaml）。
    缺失任一 → TemplateError（列出缺失清单与重装建议）；不降级到任何外部路径。
    """
    references = SKILL_DIR / "references"
    rules_root = references / "rules"
    openspec_yaml = references / "openspec" / "config.yaml"
    missing = [
        f"references/rules/{name}"
        for name in TEMPLATE_REQUIRED
        if not (rules_root / name).is_file()
    ]
    if not openspec_yaml.is_file():
        missing.append("references/openspec/config.yaml")
    if missing:
        raise TemplateError(
            "skill 安装不完整（缺少模板文件）：\n  - "
            + "\n  - ".join(missing)
            + "\n请重新安装 skill 后重试。"
        )
    return rules_root, openspec_yaml
```

同时删除 `_ONLINE_RULES_SUBPATH`/`_OFFLINE_RULES_SUBPATH`/`_FALLBACK_GLOB_PATTERN` 常量与 `_format_template_failures` 等只被旧实现引用的辅助函数。

- [ ] **Step 3: 两处 loader 改用 `SKILL_DIR`**

`_load_reference` 与 `_load_kernel_source` 中的 `skill_dir = Path(__file__).resolve().parent.parent` 改为直接使用 `SKILL_DIR` 常量。

- [ ] **Step 4: 运行确认绿**

Run: `uv run --with pytest python3 -m pytest tests/test_rule_config.py -q && bash tests/verify-managed-lifecycle.sh`
Expected: pytest 全量 PASS（含 TestLocateTemplates 四新用例）；shell 全量 pass（含 `it-s2-skill-self-contained`）。

- [ ] **Step 5: Commit**

```bash
git add cadence-init/skills/rule-config/scripts/rule-config.py
git commit -m "feat(rule-config): 模板定位改为 skill 自包含单源，删除写死的客户端路径"
```

---

### Task 3: 文档与对账

**映射：** tasks.md 3.1/3.2/3.3。

**Files:**
- Modify: `cadence-init/skills/rule-config/SKILL.md`（第一步——定位脚本）
- Modify: `cadence-init/skills/rule-config/references/merge-semantics.md`（§11.5）
- Modify: `cadence-init/skills/rule-config/tests/skill-clause-map.md`（S1b-01~04 行）

- [ ] **Step 1: SKILL.md 第一步改写**

"**第一步——定位脚本（与 pre-check 同款约定）**"整段改为：

```markdown
**第一步——定位脚本**：脚本是本 rule-config skill 的关联脚本，即本 SKILL 所在目录的 `scripts/rule-config.py`（各客户端按其 skill 安装位置定位该目录，如 `<skill 安装根>/cadence-init/skills/rule-config/`）。模板与脚本同包（skill 自包含），由脚本自动解析其 skill 目录下的 `references/`，Agent 不做模板定位。脚本只读，不要 `cd` 进 skill 目录，也不要把脚本复制到别处执行。若脚本报"skill 安装不完整"，重新安装 skill 后重试，不得从其他项目或安装位置复制模板补齐。
```

- [ ] **Step 2: merge-semantics.md §11.5 整节重写**

```markdown
### 11.5 模板定位（skill 自包含）

模板根路径与 OpenSpec 配置模板路径 MUST 以脚本自身所在 skill 目录（`SKILL_DIR`，`Path(__file__).resolve().parent.parent`）为唯一来源：`SKILL_DIR/references/rules/` 与 `SKILL_DIR/references/openspec/config.yaml`。禁止引用 `~/.claude/plugins/` 等客户端目录候选或全局搜索回退；模板定位 MUST NOT 依赖 `HOME` 环境变量。

**成对校验**：`references/rules/` 下必须存在 `agent-routing-kernel.md`、`language.md`、`openspec-superpowers-workflow.md`、`document-storage.md` 四件套，且 `references/openspec/config.yaml` 必须存在；缺任一即 `TemplateError` 失败关闭（非零退出、目标项目零写入），报告逐个列出缺失文件名并给出"skill 安装不完整，请重新安装"恢复建议（对应测试 `ut-locate_templates-incomplete`；空 HOME 正常运行为 `it-s2-skill-self-contained`）。
```

§12 追加对账记录：`2026-08-19 定位自包含化对账（change rule-config-self-contained-templates）：模板三级定位（在线/离线/glob）删除，改为 skill 目录单源；it-s2-templates-missing 反转为 it-s2-skill-self-contained；TestLocateTemplates 六用例重写为 ut-locate_templates-skill-dir/-incomplete/-no-home/-ignore-stale-marketplace。`

- [ ] **Step 3: skill-clause-map.md 同步**

S1b-01~04 行改为单源语义与上述测试 ID；头部追加 2026-08-19 变更记录。

- [ ] **Step 4: Commit**

```bash
git add cadence-init/skills/rule-config/SKILL.md cadence-init/skills/rule-config/references/merge-semantics.md cadence-init/skills/rule-config/tests/skill-clause-map.md
git commit -m "docs(rule-config): 定位规则与合并语义对账为 skill 自包含"
```

---

### Task 4: 全量验证 + 过期 marketplace 共存 E2E

**映射：** tasks.md 4.1/4.2/4.3。

- [ ] **Step 1: pytest 全量**

Run: `cd cadence-init/skills/rule-config && uv run --with pytest python3 -m pytest tests/test_rule_config.py -q`
Expected: 全量 PASS。

- [ ] **Step 2: shell 全量**

Run: `bash tests/verify-managed-lifecycle.sh`
Expected: SUMMARY 全 pass 0 fail。

- [ ] **Step 3: E2E——过期 marketplace 共存环境**

```bash
E2E=$(mktemp -d)
# 伪造过期 marketplace：模板 document-storage 为旧版（无产物路径覆盖）
mkdir -p "$E2E/home/.claude/plugins/marketplaces/cadence-skills-marketplace/cadence-init/skills/rule-config/references/rules"
grep -v -A8 '产物路径覆盖' /home/michaelche/.agents/Cadence-skills/cadence-init/skills/rule-config/references/rules/document-storage.md > "$E2E/home/.claude/plugins/marketplaces/cadence-skills-marketplace/cadence-init/skills/rule-config/references/rules/document-storage.md" || true
# 项目：预置与旧模板一致的 document-storage.md（旧契约下会被误判幂等）
mkdir -p "$E2E/proj/.claude/rules"
cp "$E2E/home/.claude/plugins/marketplaces/cadence-skills-marketplace/cadence-init/skills/rule-config/references/rules/document-storage.md" "$E2E/proj/.claude/rules/document-storage.md"
# 用仓库 skill 目录的脚本执行（HOME 指向伪 marketplace 环境）
HOME="$E2E/home" python3 cadence-init/skills/rule-config/scripts/rule-config.py apply --project-root "$E2E/proj" --report "$E2E/r.json" --no-interrupt
# 断言：document-storage.md 被覆盖为 skill 目录（含产物路径覆盖）版本且已归档
grep -q '产物路径覆盖' "$E2E/proj/.claude/rules/document-storage.md"
ls "$E2E/proj/cadence/legacy"/*/.claude/rules/document-storage.md
```

Expected: grep 命中；归档存在；退出码 0。

- [ ] **Step 4: 收尾提交（如有修复）**

```bash
git add -A && git commit -m "test(rule-config): skill 自包含定位全量验证与 E2E"
```

---

## Self-Review 记录

- **Spec coverage**：requirement「模板与脚本必须同源」三 scenario ↔ Task 1 三个 pytest 用例 + shell 反转用例 + Task 4 E2E；无遗漏。
- **Placeholder 扫描**：无 TBD；测试与实现代码完整。
- **类型一致性**：`SKILL_DIR` 常量名、四件套清单、TemplateError 消息关键词（"重新安装"）在 Task 1（断言）与 Task 2（实现）间逐字一致。
- **中间态**：Task 1 红态提交仅含测试；Task 2 绿态后双套件全绿。
