# 计划文档：实施 rule-config 入口规范化与产物覆盖及提交开关

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 修复 rule-config 初始化三问题——入口文件强制规则规范化合并、Superpowers 产物路径覆盖、design/plan 自动提交开关。

**Architecture:** 单一脚本 `rule-config.py` 内完成：以 `CANONICAL_RULES` 单一事实源权威渲染 `## 强制规则` 章节；L0 内核升 v2（路径覆盖表 + 提交开关条款）并完成 v1→v2 确定性升级接线；`## 项目配置` 新增自动提交开关；报告新增顶层 `warnings` 契约。

**Tech Stack:** Python 3 单脚本（unittest，importlib 加载）；OpenSpec change `rule-config-entry-normalization`；技术方案 v1.2 `cadence/designs/2026-08-13_技术方案_rule-config入口规范化与产物覆盖及提交开关_v1.0.md`。

## Global Constraints

- 测试加载方式（既有约定，逐字沿用）：`rc = importlib` 加载 `scripts/rule-config.py`；测试文件 `tests/test_rule_config.py`。
- 每个 Task 结束运行：`python3 -m unittest discover -s cadence-init/skills/rule-config/tests -v`（工作目录=仓库根），全绿才 commit。
- 规范化为确定性整理动作：普通/no-interrupt 两模式同动作，不产生 conflicts/decisions。
- 失效删除仅限 `RETIRED_RULE_FILES = ["serena-usage.md"]`，禁止"文件不存在即删"。
- 章节外用户内容逐字保留；禁止全文级文案替换。
- warning 错误码仅限枚举：`USER_LINES_KEPT`、`DUPLICATE_H2`、`ORPHAN_RULE6`、`INVALID_TOGGLE`、`ENTRY_TOGGLE_MISMATCH`、`L0_DEDUP`；warning 不改变 `overall`。
- L0 当前版本升 v2；受支持旧版 = v0、v1；升级走确定性 upgrade（两模式同动作，不经用户决策）。
- 映射表三源（kernel v2 / document-storage.md / 脚本常量）逐字一致。
- 合并语义合计行数 62 → 64，需同步 `merge-semantics.md:21`、`SKILL.md:129`、`tests/skill-clause-map.md:13,368`。
- commit 信息中文、前缀 `feat(rule-config):` / `test(rule-config):` / `docs(rule-config):`。

---

### Task 1: 技术栈双入口不一致复现与修复

**Files:**
- Test: `cadence-init/skills/rule-config/tests/test_rule_config.py`（新增 `TestTechStackDualEntry`）
- Modify: `cadence-init/skills/rule-config/scripts/rule-config.py`（`step_s4_entry_files` 2255 起，按复现结果定位）

**Interfaces:**
- Consumes: 既有 `step_s4_entry_files(root, intents, plan, report)`、`report["tech_stack"]`（dict，键 `language/pkg_manager/test/lint/format`）。
- Produces: 修复后双入口写入同一份 `tech_stack`；后续 Task 依赖"两入口均经 `_compose_entry` 且 tech_stack 参数一致"的事实。

- [ ] **Step 1: 写失败复现测试**

```python
class TestTechStackDualEntry(unittest.TestCase):
    def test_both_entries_receive_same_techstack(self):
        """ut-dual-entry-techstack：双入口写入同一份 tech_stack（SM/DF 一致性）。"""
        import tempfile, subprocess
        from pathlib import Path
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "package.json").write_text('{"scripts":{"test":"vitest"}}')
            # 既有非 Cadence 入口（无 ## 强制规则、无技术栈块）
            (root / "AGENTS.md").write_text("# KB\n\nEnglish content\n")
            (root / "CLAUDE.md").write_text("# CLAUDE.md\n\n说明\n")
            subprocess.run(
                ["python3", str(SCRIPT_PATH), "apply", "--project-root", str(root),
                 "--report", str(root.parent / "r.json"), "--no-interrupt"],
                check=True)
            for name in ("AGENTS.md", "CLAUDE.md"):
                text = (root / name).read_text()
                self.assertIn("- **语言**：JavaScript/TypeScript", text,
                              f"{name} 技术栈未写入检测值")
```

- [ ] **Step 2: 运行确认失败**

Run: `python3 -m unittest discover -s cadence-init/skills/rule-config/tests -k TechStackDualEntry -v`
Expected: FAIL（AGENTS.md 断言失败，复现"未检测到"）

- [ ] **Step 3: 定位根因并最小修复**

按失败形态定位：若 AGENTS.md 命中 `step_s4_entry_files` skip 分支（`action == "skip"` 或 `state is None and action != "create"`），检查 `_compose_entry` 是否被调用、`tech_stack` 是否为空 dict 提前返回。修复方向（按实际根因二选一）：
- 若 `report["tech_stack"]` 在 skip 分支为空：确认 `detect_project`（1754 行）在 dry-run/apply 均写入 `report["tech_stack"]`，缺失则补写；
- 若 `_ensure_techstack_block`（2612 行）因 `### 项目技术栈` 缺失应整体追加而未追加：检查其 `if not tech_stack: return` 提前返回是否吞掉了非空 tech_stack（不应），修正调用参数。
修复必须最小化，不改变其他分支语义。

- [ ] **Step 4: 运行确认通过**

Run: 同 Step 2 命令 + 全量 `python3 -m unittest discover -s cadence-init/skills/rule-config/tests -v`
Expected: 新测试 PASS；既有 160 用例全绿

- [ ] **Step 5: Commit**

```bash
git add cadence-init/skills/rule-config/scripts/rule-config.py cadence-init/skills/rule-config/tests/test_rule_config.py
git commit -m "fix(rule-config): 修复双入口技术栈写入不一致"
```

---

### Task 2: CANONICAL_RULES / RETIRED_RULE_FILES 常量与 BASE 渲染

**Files:**
- Modify: `cadence-init/skills/rule-config/scripts/rule-config.py`（常量区 243-345 行附近）
- Test: `cadence-init/skills/rule-config/tests/test_rule_config.py`（新增 `TestCanonicalRules`）

**Interfaces:**
- Produces（后续 Task 依赖的精确签名）：

```python
# identity markers, 标题, claude 文案行, agents 文案行
CANONICAL_RULES: list[tuple[tuple[str, ...], str, str, str]]
RETIRED_RULE_FILES: list[str]  # ["serena-usage.md"]
def render_base_entry(entry_name: str, project_type: str,
                      existing_rule_files: set[str]) -> str
def render_mandatory_section(entry_name: str, project_type: str,
                             existing_rule_files: set[str]) -> str
def _canonical_rules_for(existing_rule_files: set[str]) -> list  # 含 playwright 条件项
```

- [ ] **Step 1: 写失败测试**

```python
class TestCanonicalRules(unittest.TestCase):
    def test_base_rendered_from_canonical_rules(self):
        """ut-canonical-base：BASE 与 CANONICAL_RULES 渲染逐字一致（防双事实源漂移）。"""
        for entry in ("CLAUDE.md", "AGENTS.md"):
            rendered = rc.render_base_entry(entry, "non-coding", set())
            self.assertIn("### 1. 语言规则", rendered)
            self.assertIn("### 7. 代码阅读规则", rendered)
            self.assertNotIn("serena", rendered.lower())

    def test_rule6_identity_marker(self):
        """ut-rule6-marker：规则 6 以 cadence/project-rules/ 为身份 marker。"""
        markers = dict()
        for m, title, _c, _a in rc.CANONICAL_RULES:
            markers[title] = m
        self.assertIn("cadence/project-rules/", markers["项目个性化规则"])

    def test_playwright_conditional(self):
        """ut-canonical-playwright：playwright.md 存在时清单含第 8 条。"""
        with_pw = rc._canonical_rules_for({"playwright.md"})
        without = rc._canonical_rules_for(set())
        self.assertEqual(len(with_pw), len(without) + 1)
        self.assertIn("playwright.md", with_pw[-1][0])

    def test_retired_list_seed(self):
        """ut-retired-seed：退役清单初始含 serena-usage.md。"""
        self.assertEqual(rc.RETIRED_RULE_FILES, ["serena-usage.md"])
```

- [ ] **Step 2: 运行确认失败**（`AttributeError: CANONICAL_RULES`）

Run: `python3 -m unittest discover -s cadence-init/skills/rule-config/tests -k CanonicalRules -v`

- [ ] **Step 3: 实现常量与渲染**

在常量区新增（文案逐字取自现有 `BASE_CLAUDE_MD`/`BASE_AGENTS_MD` 对应条目，规则 2 提供 coding/non-coding 两 variant）：

```python
RETIRED_RULE_FILES = ["serena-usage.md"]

RULE2_TEXT_CODING = "- **遵循 TDD 和代码规范** → 详见 `.claude/rules/code-usage.md`"
RULE2_TEXT_NONCODING = "- **非必要不编写代码** → 详见 `.claude/rules/code-usage.md`"

# (markers, 标题, claude 正文行(不含标题), agents 正文行)
CANONICAL_RULES = [
    (("language.md",), "语言规则",
     "- **必须使用中文回答** → 详见 `.claude/rules/language.md`",
     "- **必须使用中文回答** → 详见 `.claude/rules/language.md`"),
    (("code-usage.md",), "代码使用规则", "{RULE2}", "{RULE2}"),  # 渲染时按 project_type 替换
    (("document-storage.md",), "文档存储规则",
     "- **Cadence 产物文档必须存放在 `cadence` 目录下；Claude Code 框架规则保留在 `.claude/rules/` 目录下** → 详见 `.claude/rules/document-storage.md`",
     "- **Cadence 产物文档必须存放在 `cadence` 目录下；Claude Code 框架规则保留在 `.claude/rules/` 目录下** → 详见 `.claude/rules/document-storage.md`"),
    (("markdown-format.md",), "Markdown 格式规则",
     "- **代码块嵌套使用 4 反引号/3 反引号** → 详见 `.claude/rules/markdown-format.md`",
     "- **代码块嵌套使用 4 反引号/3 反引号** → 详见 `.claude/rules/markdown-format.md`"),
    (("mcp-servers.md",), "MCP Server 使用规则",
     "- **各 MCP 工具的使用规范** → 详见 `.claude/rules/mcp-servers.md`",
     "- **各 MCP 工具及相关自动化工具的使用必须遵循项目规范** → 详见 `.claude/rules/mcp-servers.md`"),
    (("cadence/project-rules/",), "项目个性化规则",
     RULE6_BLOCK_CLAUDE_BODY,   # 既有 4 行块（去掉标题行）
     RULE6_BLOCK_AGENTS_BODY),
    (("code-reading.md",), "代码阅读规则",
     "- **大范围检索使用 CodeGraph，精确结构阅读优先使用 ast-grep outline** → 详见 `.claude/rules/code-reading.md`",
     "- **大范围检索使用 CodeGraph，精确结构阅读优先使用 ast-grep outline** → 详见 `.claude/rules/code-reading.md`"),
]

CANONICAL_RULE_PLAYWRIGHT = (
    ("playwright.md",), "Playwright CLI 使用规则",
    "- **浏览器自动化工具必须遵循项目规范** → 详见 `.claude/rules/playwright.md`",
    "- **浏览器自动化工具必须遵循项目规范** → 详见 `.claude/rules/playwright.md`")
```

`_canonical_rules_for`：`list(CANONICAL_RULES)` +（`"playwright.md" in existing_rule_files` 时 append `CANONICAL_RULE_PLAYWRIGHT`）。
`render_mandatory_section`：`## 强制规则` + 引用块 + 按序编号渲染 `### N. 标题\n正文`。
`render_base_entry`：文件说明头（CLAUDE/AGENTS 各自现有首段）+ `render_mandatory_section`。
保留 `BASE_CLAUDE_MD`/`BASE_AGENTS_MD` 名称作为兼容别名（`render_base_entry(...)` 结果），避免既有引用点全部改动。

- [ ] **Step 4: 运行确认通过 + 全量回归**

Run: `python3 -m unittest discover -s cadence-init/skills/rule-config/tests -v`
Expected: 新增 4 用例 PASS；既有用例全绿

- [ ] **Step 5: Commit**

```bash
git add cadence-init/skills/rule-config/scripts/rule-config.py cadence-init/skills/rule-config/tests/test_rule_config.py
git commit -m "feat(rule-config): CANONICAL_RULES 单一事实源与 BASE 渲染"
```

---

### Task 3: `_normalize_mandatory_rules` 规范化算法

**Files:**
- Modify: `cadence-init/skills/rule-config/scripts/rule-config.py`（替换 `_ensure_summary_lines` 2530-2606）
- Test: `cadence-init/skills/rule-config/tests/test_rule_config.py`（新增 `TestNormalizeMandatoryRules`）

**Interfaces:**
- Consumes: Task 2 的 `_canonical_rules_for`、`render_mandatory_section`、`RETIRED_RULE_FILES`。
- Produces:

```python
def _normalize_mandatory_rules(text: str, entry_name: str, project_type: str,
                               existing_rule_files: set[str]) -> tuple[str, list[dict]]
# 返回 (规范化文本, warnings)；warning dict: {"code","file","message","detail"}
```

- [ ] **Step 1: 写失败测试（17 用例核心，逐一实现）**

```python
KB_AGENTS = "# KB\n\nEnglish knowledge base content.\n\n## NOTES\n\n- keep me\n"

class TestNormalizeMandatoryRules(unittest.TestCase):
    def _norm(self, text, entry="AGENTS.md", ptype="non-coding", files=set()):
        return rc._normalize_mandatory_rules(text, entry, ptype, files)

    def test_create_section_when_missing(self):
        """ut-norm-create：无章节时创建（全局顺序在 Task 5 集成验证）。"""
        out, warns = self._norm(KB_AGENTS)
        self.assertIn("## 强制规则", out)
        self.assertIn("### 1. 语言规则", out)
        self.assertIn("### 7. 代码阅读规则", out)
        self.assertIn("English knowledge base content.", out)  # 用户内容保留

    def test_serena_removed(self):
        """ut-norm-retired：退役清单命中删除。"""
        text = "## 强制规则\n\n### 5. Serena 使用规则\n- **禁止分析 .git 目录** → 详见 `.claude/rules/serena-usage.md`\n"
        out, _ = self._norm(text, "CLAUDE.md")
        self.assertNotIn("serena-usage.md", out)
        self.assertNotIn("Serena", out)

    def test_forward_reference_kept(self):
        """ut-norm-forward-ref：未在退役清单的不存在文件引用按用户内容保留。"""
        text = "## 强制规则\n\n### 9. 自定义规则\n- **我的规则** → 详见 `.claude/rules/my-future.md`\n"
        out, warns = self._norm(text)
        self.assertIn("my-future.md", out)
        self.assertTrue(any(w["code"] == "USER_LINES_KEPT" for w in warns))

    def test_renumber_1_to_9(self):
        """ut-norm-renumber：1-9 错乱重排为权威 1-7。"""
        text = ("## 强制规则\n\n### 5. Serena 使用规则\n- x `.claude/rules/serena-usage.md`\n"
                "### 1. 语言规则\n- **必须使用中文回答** → 详见 `.claude/rules/language.md`\n")
        out, _ = self._norm(text, "CLAUDE.md", "coding")
        self.assertIn("### 1. 语言规则", out)
        self.assertIn("### 2. 代码使用规则", out)
        self.assertIn("遵循 TDD", out)  # coding 文案
        self.assertNotIn("### 8.", out)

    def test_dedup_same_ref(self):
        """ut-norm-dedup：同规则文件多引用保留首个。"""
        text = ("## 强制规则\n\n- **必须使用中文回答** → 详见 `.claude/rules/language.md`\n"
                "- 重复行 `.claude/rules/language.md`\n")
        out, _ = self._norm(text)
        self.assertEqual(out.count("language.md"), 1)

    def test_idempotent(self):
        """ut-norm-idempotent：二次运行逐字不变。"""
        once, _ = self._norm(KB_AGENTS)
        twice, warns2 = self._norm(once)
        self.assertEqual(once, twice)

    def test_rule2_coding_switch(self):
        """ut-norm-rule2：规则 2 按 project_type 选文案。"""
        text = "## 强制规则\n\n- **非必要不编写代码** → 详见 `.claude/rules/code-usage.md`\n"
        out, _ = self._norm(text, "CLAUDE.md", "coding")
        self.assertIn("遵循 TDD", out)
        self.assertNotIn("非必要不编写代码", out)

    def test_playwright_included_when_file_exists(self):
        """ut-norm-playwright：条件项。"""
        out, _ = self._norm(KB_AGENTS, files={"playwright.md"})
        self.assertIn("Playwright", out)
        out2, _ = self._norm(KB_AGENTS)
        self.assertNotIn("Playwright", out2)

    def test_user_h3_block_moved_as_whole(self):
        """ut-norm-user-h3：用户 H3 小节整体平移到权威条目之后。"""
        text = ("## 强制规则\n\n### 1. 语言规则\n- **必须使用中文回答** → 详见 `.claude/rules/language.md`\n"
                "### 我的自定义小节\n正文第一行\n正文第二行\n")
        out, warns = self._norm(text)
        idx_custom = out.index("### 我的自定义小节")
        idx_rule7 = out.index("### 7. 代码阅读规则")
        self.assertGreater(idx_custom, idx_rule7)
        self.assertIn("正文第一行\n正文第二行", out)

    def test_orphan_rule6_outside_section_warns(self):
        """ut-norm-orphan-rule6：章节外孤立规则 6 H2 保留 + ORPHAN_RULE6。"""
        text = ("## 强制规则\n\n- **必须使用中文回答** → 详见 `.claude/rules/language.md`\n\n"
                "## 项目个性化规则（强制规则）\n\n- 旧文案\n")
        out, warns = self._norm(text)
        self.assertIn("## 项目个性化规则（强制规则）", out)
        self.assertTrue(any(w["code"] == "ORPHAN_RULE6" for w in warns))

    def test_duplicate_h2_only_first_normalized(self):
        """ut-norm-dup-h2：多个 ## 强制规则 仅规范化首个 + DUPLICATE_H2。"""
        text = "## 强制规则\n\n- x `.claude/rules/language.md`\n\n## 强制规则\n\n- 旧 `.claude/rules/serena-usage.md`\n"
        out, warns = self._norm(text)
        self.assertTrue(any(w["code"] == "DUPLICATE_H2" for w in warns))
        self.assertEqual(out.count("## 强制规则"), 2)
        self.assertIn("serena-usage.md", out.split("## 强制规则")[2])  # 第二个章节不动

    def test_rule6_old_wording_replaced(self):
        """ut-norm-rule6-old：旧 CLAUDE/AGENTS 规则 6 文案识别并替换为权威块。"""
        old = "## 强制规则\n\n### 6. 项目个性化规则（强制规则）\n- **用户自定义规则只能存放在 `cadence/project-rules/` 目录**\n- 禁止在 `rules/` 目录中添加用户自定义规则\n- 详见 `cadence/project-rules/README.md`\n"
        out, _ = self._norm(old, "CLAUDE.md")
        self.assertIn("### 6. 项目个性化规则", out)
        self.assertNotIn("（强制规则）", out.split("## 强制规则")[1])

    def test_rule2_text_outside_section_untouched(self):
        """ut-norm-outside-rule2：章节外规则 2 旧文案不被修改。"""
        text = "## 强制规则\n\n- x `.claude/rules/language.md`\n\n## 笔记\n\n遵循 TDD 和代码规范 是我的座右铭\n"
        out, _ = self._norm(text, "CLAUDE.md", "non-coding")
        self.assertIn("遵循 TDD 和代码规范 是我的座右铭", out)

    def test_empty_retired_list_no_deletion(self):
        """ut-norm-retired-empty：退役清单为空时无删除。"""
        with mock.patch.object(rc, "RETIRED_RULE_FILES", []):
            text = "## 强制规则\n\n- x `.claude/rules/serena-usage.md`\n"
            out, _ = self._norm(text)
            self.assertIn("serena-usage.md", out)

    def test_claude_agents_wording_differs(self):
        """ut-norm-wording：MCP/规则 6 双入口文案差异。"""
        out_c, _ = self._norm(KB_AGENTS, "CLAUDE.md")
        out_a, _ = self._norm(KB_AGENTS, "AGENTS.md")
        self.assertIn("各 MCP 工具的使用规范", out_c)
        self.assertIn("各 MCP 工具及相关自动化工具的使用必须遵循项目规范", out_a)
```

- [ ] **Step 2: 运行确认失败**（`AttributeError: _normalize_mandatory_rules`）

- [ ] **Step 3: 实现**

```python
def _normalize_mandatory_rules(text, entry_name, project_type, existing_rule_files):
    warnings_out = []
    rules = _canonical_rules_for(existing_rule_files)
    rule2 = RULE2_TEXT_CODING if project_type == "coding" else RULE2_TEXT_NONCODING

    lines = text.splitlines()
    h2_idx = [i for i, l in enumerate(lines) if l.strip() == "## 强制规则"]
    if not h2_idx:
        # 无章节：在 L0 end 之后创建；无 L0 则追加文末（防御，正常流程 L0 已插入）
        section = render_mandatory_section(entry_name, project_type, existing_rule_files)
        end_marker = rc.L0_END if hasattr(rc, "L0_END") else None
        # 实现：找 L0_END 所在行，插到其后空行处；找不到则 append
        ...
        return new_text, warnings_out
    if len(h2_idx) > 1:
        warnings_out.append({"code": "DUPLICATE_H2", "file": entry_name,
                             "message": "存在多个 ## 强制规则，仅规范化首个", "detail": {"count": len(h2_idx)}})
    start = h2_idx[0]
    end = len(lines)
    for i in range(start + 1, len(lines)):
        s = lines[i].strip()
        if s.startswith("## ") or s.startswith("# "):
            end = i
            break
    section_lines = lines[start + 1:end]

    # 分类：把 section_lines 切成块（### 标题块 / 非标题行各自成块）
    blocks = _split_into_blocks(section_lines)  # [(kind, [lines])]，kind ∈ heading-block / line
    canonical, user_blocks = [], []
    seen = set()
    for blk in blocks:
        blk_text = "\n".join(blk)
        retired = [r for r in RETIRED_RULE_FILES if r in blk_text]
        if retired:
            continue  # 删除
        owner = None
        for markers, title, _c, _a in rules:
            if any(m in blk_text for m in markers):
                owner = title
                break
        if owner and owner not in seen:
            seen.add(owner)
            continue  # 权威条目由渲染产出，原文丢弃（实现重排/文案修正/去重）
        if owner and owner in seen:
            continue  # 去重：丢弃后续重复引用
        user_blocks.append(blk)

    rebuilt = render_mandatory_section(entry_name, project_type, existing_rule_files).splitlines()
    if user_blocks:
        warnings_out.append({"code": "USER_LINES_KEPT", "file": entry_name,
                             "message": "强制规则章节含非框架条目，已保留在权威条目之后",
                             "detail": {"blocks": len(user_blocks)}})
    new_section = rebuilt[1:] + [""] + [l for blk in user_blocks for l in blk]  # 去 ## 行，章节标题保留
    result = lines[:start + 1] + new_section + lines[end:]

    # 章节外孤立规则 6 H2 检测
    outside = "\n".join(result[:start] + result[start + 1 + len(new_section):])
    for l in outside.splitlines():
        if l.startswith("## ") and "项目个性化规则" in l:
            warnings_out.append({"code": "ORPHAN_RULE6", "file": entry_name,
                                 "message": "章节外存在孤立的项目个性化规则 H2，请人工确认", "detail": {}})
            break
    return "\n".join(result), warnings_out
```

注意：用户块内部结构（H3+正文）在 `_split_into_blocks` 中按"### 起始连续块"保持整体；`render_mandatory_section` 返回以 `## 强制规则` 开头的完整章节，拼接时去首行。
原 `_ensure_summary_lines` 删除，引用点（`_compose_entry` 步骤 3）改调新函数并收集 warnings。

- [ ] **Step 4: 运行确认通过 + 全量回归**

Run: `python3 -m unittest discover -s cadence-init/skills/rule-config/tests -v`
Expected: 17 新用例 PASS（除明确标注 Task 5 集成的顺序断言）、既有全绿

- [ ] **Step 5: Commit**

```bash
git add cadence-init/skills/rule-config/scripts/rule-config.py cadence-init/skills/rule-config/tests/test_rule_config.py
git commit -m "feat(rule-config): 强制规则章节规范化算法替代追加式补全"
```

---

### Task 4: `_compose_entry` 清理（移除全文规则 2 替换）与 warnings 贯通

**Files:**
- Modify: `cadence-init/skills/rule-config/scripts/rule-config.py`（`_compose_entry` 2380-2432、`step_s4_entry_files` 2255-2377、`_record_step_actions` 2207 附近）

**Interfaces:**
- Consumes: Task 3 `_normalize_mandatory_rules` 返回的 warnings。
- Produces:
  - `_compose_entry(existing, l0_source, *, state, project_type, tech_stack, entry_name, existing_rule_files)` → `(text, diffs, warnings)`（三元组，调用点全部更新）；
  - `report["warnings"]: list[dict]`（顶层字段，初始化时为空数组）。

- [ ] **Step 1: 写失败测试**

```python
class TestComposeEntryWarnings(unittest.TestCase):
    def test_compose_returns_warnings(self):
        """ut-compose-warnings：_compose_entry 返回 (text, diffs, warnings)。"""
        text, diffs, warns = rc._compose_entry(
            "## 笔记\n\n遵循 TDD 和代码规范 保留我\n", rc._load_kernel_source(),
            state="insert", project_type="non-coding",
            tech_stack={}, entry_name="CLAUDE.md", existing_rule_files=set())
        self.assertIsInstance(warns, list)
        self.assertIn("遵循 TDD 和代码规范 保留我", text)  # 章节外不被全文替换

    def test_step_s4_aggregates_warnings_to_report(self):
        """ut-s4-warnings：S4 执行后 report['warnings'] 汇总入口类 warning。"""
        # 用 Task 1 的临时项目方式跑 apply，断言 report JSON 含 warnings 数组
        import tempfile, subprocess, json
        from pathlib import Path
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "AGENTS.md").write_text("## 强制规则\n\n- 我的行 `.claude/rules/my-x.md`\n")
            report_path = Path(td) / "r.json"
            subprocess.run(["python3", str(SCRIPT_PATH), "apply", "--project-root", str(root),
                            "--report", str(report_path), "--no-interrupt"], check=True)
            rep = json.loads(report_path.read_text())
            self.assertIn("warnings", rep)
            self.assertTrue(any(w["code"] == "USER_LINES_KEPT" for w in rep["warnings"]))
            self.assertEqual(rep["overall"], "ok")  # warning 不影响 overall
```

- [ ] **Step 2: 运行确认失败**

- [ ] **Step 3: 实现**
1. `_compose_entry` 签名加 `existing_rule_files`，返回值改三元组；删除步骤 2（全文规则 2 替换循环）；步骤 3 改调 `_normalize_mandatory_rules` 并透传 warnings。
2. `step_s4_entry_files` 全部调用点解包三元组；`existing_rule_files` 在步骤入口计算：`{p.name for p in (root / ".claude/rules").glob("*.md")}`（目录不存在时为空集）。
3. 报告骨架初始化处（`run_dry_run`/`run_apply` 或 main 构建 report dict 处）加 `report.setdefault("warnings", [])`；`_record_step_actions` 后把 S4 warnings extend 进 `report["warnings"]`。

- [ ] **Step 4: 运行确认通过 + 全量回归**（注意既有调用 `_compose_entry` 的测试需同步解包三元组）

- [ ] **Step 5: Commit**

```bash
git add cadence-init/skills/rule-config/scripts/rule-config.py cadence-init/skills/rule-config/tests/test_rule_config.py
git commit -m "feat(rule-config): warnings 报告契约贯通与全文规则2替换移除"
```

---

### Task 5: L0 插入位置修正与全局顺序

**Files:**
- Modify: `cadence-init/skills/rule-config/scripts/rule-config.py`（`_insert_l0_block` 2437-2466）
- Test: `cadence-init/skills/rule-config/tests/test_rule_config.py`（`TestL0InsertPosition`）

**Interfaces:**
- Consumes: 既有 `L0_BEGIN/L0_END`、`l0_block` 状态机。
- Produces: `_insert_l0_block` 无 `## 强制规则` 时插入 H1+首个简介段落之后；既有 TestL0Block 用例不回归。

- [ ] **Step 1: 写失败测试**

```python
class TestL0InsertPosition(unittest.TestCase):
    def test_insert_after_intro_when_no_section(self):
        """ut-l0-pos：无 ## 强制规则 时 L0 位于 H1+简介之后、用户内容之前。"""
        text = "# KB\n\n项目简介段落。\n\n## NOTES\n\n- 用户内容\n"
        out = rc._insert_l0_block(text, L0_SOURCE)
        idx_l0 = out.index("<!-- cadence-managed")
        idx_notes = out.index("## NOTES")
        idx_intro = out.index("项目简介段落。")
        self.assertLess(idx_intro, idx_l0)
        self.assertLess(idx_l0, idx_notes)  # 不再追加到文件末尾

    def test_global_order_end_to_end(self):
        """ut-global-order：H1/说明 → L0 → 强制规则 → 用户内容。"""
        import tempfile, subprocess
        from pathlib import Path
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "AGENTS.md").write_text("# KB\n\n简介。\n\n## NOTES\n\n- 用户内容\n")
            subprocess.run(["python3", str(SCRIPT_PATH), "apply", "--project-root", str(root),
                            "--report", str(Path(td) / "r.json"), "--no-interrupt"], check=True)
            out = (root / "AGENTS.md").read_text()
            i1, i2, i3 = out.index("<!-- cadence-managed"), out.index("## 强制规则"), out.index("## NOTES")
            self.assertLess(i1, i2)
            self.assertLess(i2, i3)
```

- [ ] **Step 2: 运行确认失败**（L0 当前落在文末，`idx_l0 > idx_notes`）

- [ ] **Step 3: 实现**

`_insert_l0_block` 的 `insert_idx is None` 分支改为：跳过 H1 行与其后连续空行，再跳过首个非空段落（简介），插到段落后的空行处；防御：全文无 H1 时退化为插到文首。同步修正 docstring（删除"启发式/文件末尾"旧注释）。

- [ ] **Step 4: 运行确认通过 + 全量回归**（重点回归 `TestL0Block::test_insert_position_two_branches`，其"无章节"分支预期需同步更新为 H1 后插入）

- [ ] **Step 5: Commit**

```bash
git add cadence-init/skills/rule-config/scripts/rule-config.py cadence-init/skills/rule-config/tests/test_rule_config.py
git commit -m "fix(rule-config): L0 无章节分支插入位置改为 H1 简介之后"
```

---

### Task 6: L0 v1→v2 接线与迁移不变量

**Files:**
- Modify: `cadence-init/skills/rule-config/scripts/rule-config.py`（107-109 常量、`l0_block` 约 875-930、`_remove_l0_block_pair` 2470-2505、`_compose_entry` L0 分支）
- Test: `cadence-init/skills/rule-config/tests/test_rule_config.py`（TestL0Block 改造 + `TestL0V2Migration`）

**Interfaces:**
- Produces:
  - `L0_CURRENT_VERSION = "v2"`；`L0_OLD_VERSIONS = ["v1", "v0"]`；`L0_BEGIN/L0_END` 由 `L0_CURRENT_VERSION` 派生；
  - `l0_block(text, source)` 状态集不变（skip/insert/upgrade/drift/broken），v1 成对+内容一致 → `upgrade`；
  - `_normalize_l0_to_single_block(text, source) -> (text, warnings)`：混合标记/重复区块归并。

- [ ] **Step 1: 写失败测试**

```python
V2_START = "<!-- cadence-managed:openspec-superpowers-routing:v2:start -->"
V2_END = "<!-- cadence-managed:openspec-superpowers-routing:v2:end -->"

class TestL0V2Migration(unittest.TestCase):
    def test_v1_pair_is_upgrade(self):
        """ut-l0-v2-upgrade：v1 成对区块对 v2 源判 upgrade（非 drift）。"""
        v1_text = V1_START + "\n旧路由内容\n" + V1_END + "\n"
        self.assertEqual(rc.l0_block(v1_text, L0_SOURCE), "upgrade")

    def test_upgrade_yields_single_v2_block(self):
        """ut-l0-v2-single：升级后恰好一个当前版本区块且区块外保留。"""
        v1_text = "# 头\n\n" + V1_START + "\n旧路由\n" + V1_END + "\n\n## 用户章节\nx\n"
        out, warns = rc._normalize_l0_to_single_block(v1_text, L0_SOURCE)
        self.assertEqual(out.count(V2_START), 1)
        self.assertEqual(out.count(V2_END), 1)
        self.assertIn("## 用户章节", out)

    def test_mixed_markers_not_broken_residue(self):
        """ut-l0-v2-mixed：旧版成对+当前单侧残留 → 归并为一个规范区块。"""
        mixed = V1_START + "\n旧\n" + V1_END + "\n\n" + V2_START + "\n残留单侧\n"
        out, _ = rc._normalize_l0_to_single_block(mixed, L0_SOURCE)
        self.assertEqual(out.count(V2_START), 1)
        self.assertEqual(out.count(V2_END), 1)

    def test_duplicate_current_blocks_deduped(self):
        """ut-l0-v2-dedup：重复当前版本区块保留首个 + L0_DEDUP warning。"""
        dup = L0_SOURCE + "\n\n## 中间\n\n" + L0_SOURCE
        out, warns = rc._normalize_l0_to_single_block(dup, L0_SOURCE)
        self.assertEqual(out.count(V2_START), 1)
        self.assertTrue(any(w["code"] == "L0_DEDUP" for w in warns))
        self.assertIn("## 中间", out)

    def test_v2_skip_idempotent(self):
        """ut-l0-v2-skip：v2 与源一致判 skip。"""
        self.assertEqual(rc.l0_block(L0_SOURCE, L0_SOURCE), "skip")
```

- [ ] **Step 2: 运行确认失败**

- [ ] **Step 3: 实现**
1. 常量区：`L0_CURRENT_VERSION = "v2"`；`L0_BEGIN/END` 用 f-string 由版本派生；`L0_OLD_VERSIONS = ["v1", "v0"]`。
2. `l0_block`：两处 `for ver in ("v0",)` 改 `for ver in L0_OLD_VERSIONS`；"当前版本"标记检测仍用 `L0_BEGIN/L0_END`。
3. `_remove_l0_block_pair`：`versions = [L0_CURRENT_VERSION] + L0_OLD_VERSIONS`。
4. 新增 `_normalize_l0_to_single_block`：先 `_remove_l0_block_pair` 移除全部版本成对区块（统计移除的当前版本区块数 >1 时记 `L0_DEDUP`），再 `_strip_l0_marker_lines_only` 剥离单侧标记，最后 `_insert_l0_block`。
5. `_compose_entry` L0 分支重构：state ∈ insert/upgrade/drift/broken 时统一走 `_normalize_l0_to_single_block`（drift 的"替换"语义=移除+插入规范源，保持区块外逐字）。
6. 测试文件头部 `V1_START/V1_END/V0_START/V0_END` 保留（v1/v0 作为旧版样本），新增 `V2_START/V2_END`；`TestL0Block` 中断言"v1 为当前版本"的用例改为以 v2 为当前版本（`test_skip_when_v1_block_matches_source` 改名/改为 v2 源 skip；`test_drift_when_v1_markers_but_content_differs` 改用 V2 marker 构造 drift；`test_upgrade_when_old_version_markers` 保留并加 v1 分支）。
7. `verify-managed-lifecycle.sh`（约 169 行）硬编码 v1 marker 改 v2。

- [ ] **Step 4: 运行确认通过 + 全量回归 + 集成脚本**

Run: `python3 -m unittest discover -s cadence-init/skills/rule-config/tests -v` 与 `bash cadence-init/skills/rule-config/tests/verify-managed-lifecycle.sh`
Expected: 全绿

- [ ] **Step 5: Commit**

```bash
git add cadence-init/skills/rule-config/scripts/rule-config.py cadence-init/skills/rule-config/tests/
git commit -m "feat(rule-config): L0 升 v2 并接线 v1 确定性升级与迁移不变量"
```

---

### Task 7: 产物路径覆盖表（内核 v2 + document-storage + 三源一致）

**Files:**
- Modify: `cadence-init/skills/rule-config/scripts/rule-config.py`（新增 `ARTIFACT_PATH_OVERRIDES` 常量）
- Modify: `cadence-init/skills/rule-config/references/rules/agent-routing-kernel.md`（升 v2）
- Modify: `cadence-init/skills/rule-config/references/rules/document-storage.md`
- Test: `cadence-init/skills/rule-config/tests/test_rule_config.py`（`TestArtifactPathOverrides`）

**Interfaces:**
- Produces: `ARTIFACT_PATH_OVERRIDE_TABLE: str`（脚本内单一事实源，markdown 表文本，供 kernel 与 document-storage 渲染/校验）。

- [ ] **Step 1: 写失败测试**

```python
class TestArtifactPathOverrides(unittest.TestCase):
    def test_three_sources_verbatim_consistent(self):
        """ut-override-3src：内核/document-storage/脚本常量三源映射表逐字一致。"""
        refs = Path(__file__).resolve().parents[1] / "references" / "rules"
        kernel = (refs / "agent-routing-kernel.md").read_text()
        doc_storage = (refs / "document-storage.md").read_text()
        table = rc.ARTIFACT_PATH_OVERRIDE_TABLE
        self.assertIn(table, kernel)
        self.assertIn(table, doc_storage)
        self.assertIn("docs/superpowers/specs/", table)
        self.assertIn("cadence/designs/", table)
        self.assertIn("docs/superpowers/plans/", table)
        self.assertIn("cadence/plans/", table)
        self.assertIn("优先级高于任何 Skill 正文", kernel)

    def test_kernel_is_v2(self):
        """ut-kernel-v2：内核标记为 v2。"""
        kernel = (Path(__file__).resolve().parents[1] / "references" / "rules"
                  / "agent-routing-kernel.md").read_text()
        self.assertTrue(kernel.startswith(V2_START))
        self.assertIn("产物自动提交", kernel)

    def test_no_global_skill_rewrite(self):
        """ut-override-no-skill-rewrite：覆盖声明不改写 Skill 路径（openspec 保留）。"""
        self.assertIn("openspec/", rc.ARTIFACT_PATH_OVERRIDE_TABLE)
```

- [ ] **Step 2: 运行确认失败**

- [ ] **Step 3: 实现**
1. 脚本常量：

```python
ARTIFACT_PATH_OVERRIDE_TABLE = (
    "| Skill 默认路径 | 本项目强制路径 |\n"
    "|---|---|\n"
    "| `docs/superpowers/specs/`（design/spec） | `cadence/designs/` |\n"
    "| `docs/superpowers/plans/`（plan） | `cadence/plans/` |"
)
```

2. `agent-routing-kernel.md`：标记 v1→v2；在路由表后新增小节"产物路径覆盖（强制）"：嵌入上表 + 声明"本表优先级高于任何 Skill 正文中的路径指示；OpenSpec 产物仍放 `openspec/` 目录"；新增条款"产物自动提交开关：调用 `brainstorming`/`writing-plans` 完成文档写入后，必须读取入口文件'产物自动提交（design/plan）'开关；为 `关闭` 时禁止 `git commit`，只汇报产物路径并等待用户确认。开关读取顺序：CLAUDE.md 为准、AGENTS.md 兜底；不一致按 `关闭`"。
3. `document-storage.md`：同步嵌入同一映射表与优先级声明。
4. 注意：`ARTIFACT_PATH_OVERRIDE_TABLE` 文本必须与两文件中的表逐字一致（含换行）。

- [ ] **Step 4: 运行确认通过 + 全量回归**（`L0_SOURCE` 读取的即是 v2 内核，TestL0V2Migration 联动验证）

- [ ] **Step 5: Commit**

```bash
git add cadence-init/skills/rule-config/
git commit -m "feat(rule-config): L0 v2 产物路径覆盖表与自动提交条款三源一致"
```

---

### Task 8: 产物自动提交开关 `_ensure_commit_toggle`

**Files:**
- Modify: `cadence-init/skills/rule-config/scripts/rule-config.py`（新增函数；`_compose_entry` 步骤 4 后调用）
- Test: `cadence-init/skills/rule-config/tests/test_rule_config.py`（`TestCommitToggle`）

**Interfaces:**
- Produces:

```python
TOGGLE_PREFIX = "- **产物自动提交（design/plan）**："
def _ensure_commit_toggle(text: str, entry_name: str) -> tuple[str, list[dict]]
```

- [ ] **Step 1: 写失败测试**

```python
class TestCommitToggle(unittest.TestCase):
    def test_default_written_when_missing(self):
        """ut-toggle-default：缺失时写默认值 关闭。"""
        out, _ = rc._ensure_commit_toggle("# x\n", "CLAUDE.md")
        self.assertIn("- **产物自动提交（design/plan）**：关闭", out)
        self.assertIn("## 项目配置", out)

    def test_user_value_preserved(self):
        """ut-toggle-keep：用户值 开启 保留。"""
        text = "## 项目配置\n\n- **产物自动提交（design/plan）**：开启\n"
        out, warns = rc._ensure_commit_toggle(text, "CLAUDE.md")
        self.assertIn("：开启", out)
        self.assertEqual(warns, [])

    def test_invalid_value_kept_with_warning(self):
        """ut-toggle-invalid：非法值保留原文 + INVALID_TOGGLE。"""
        text = "## 项目配置\n\n- **产物自动提交（design/plan）**：也许\n"
        out, warns = rc._ensure_commit_toggle(text, "CLAUDE.md")
        self.assertIn("：也许", out)
        self.assertTrue(any(w["code"] == "INVALID_TOGGLE" for w in warns))

    def test_toggle_after_techstack_block(self):
        """ut-toggle-position：落点在 ### 项目技术栈 块之后、章节末尾。"""
        text = ("## 项目配置\n\n### 项目技术栈\n- **语言**：Java\n\n## 其他\n")
        out, _ = rc._ensure_commit_toggle(text, "CLAUDE.md")
        self.assertLess(out.index("### 项目技术栈"), out.index(rc.TOGGLE_PREFIX))
        self.assertLess(out.index(rc.TOGGLE_PREFIX), out.index("## 其他"))

    def test_empty_techstack_still_lands(self):
        """ut-toggle-empty-ts：tech_stack 为空时开关仍落位（独立于 _ensure_techstack_block）。"""
        out, _ = rc._compose_entry("# x\n", rc._load_kernel_source(), state="insert",
                                   project_type="non-coding", tech_stack={},
                                   entry_name="CLAUDE.md", existing_rule_files=set())
        self.assertIn(rc.TOGGLE_PREFIX, out[0] if isinstance(out, tuple) else out)

    def test_duplicate_toggle_deduped(self):
        """ut-toggle-dup：重复开关行保留首个。"""
        text = ("## 项目配置\n\n- **产物自动提交（design/plan）**：开启\n"
                "- **产物自动提交（design/plan）**：关闭\n")
        out, warns = rc._ensure_commit_toggle(text, "CLAUDE.md")
        self.assertEqual(out.count(rc.TOGGLE_PREFIX), 1)
        self.assertIn("：开启", out)

    def test_multiple_project_config_sections(self):
        """ut-toggle-multi-section：多个 ## 项目配置 仅处理首个 + DUPLICATE_H2。"""
        text = "## 项目配置\n\n- **产物自动提交（design/plan）**：开启\n\n## 项目配置\n\nx\n"
        out, warns = rc._ensure_commit_toggle(text, "CLAUDE.md")
        self.assertTrue(any(w["code"] == "DUPLICATE_H2" for w in warns))
        self.assertIn("：开启", out)

    def test_idempotent(self):
        """ut-toggle-idempotent：幂等。"""
        once, _ = rc._ensure_commit_toggle("# x\n", "CLAUDE.md")
        twice, _ = rc._ensure_commit_toggle(once, "CLAUDE.md")
        self.assertEqual(once, twice)
```

- [ ] **Step 2: 运行确认失败**

- [ ] **Step 3: 实现**

```python
TOGGLE_PREFIX = "- **产物自动提交（design/plan）**："
TOGGLE_DEFAULT = "关闭"

def _ensure_commit_toggle(text, entry_name):
    warns = []
    lines = text.splitlines()
    # 1. 定位首个 ## 项目配置
    idxs = [i for i, l in enumerate(lines) if l.strip() == "## 项目配置"]
    if not idxs:
        block = ["", "## 项目配置", "",
                 "> 以下内容由初始化脚本根据项目环境自动检测生成，非通用规则。", "",
                 TOGGLE_PREFIX + TOGGLE_DEFAULT]
        return "\n".join(lines) .rstrip("\n") + "\n" + "\n".join(block) + "\n", warns
    if len(idxs) > 1:
        warns.append({"code": "DUPLICATE_H2", "file": entry_name,
                      "message": "存在多个 ## 项目配置，仅处理首个", "detail": {}})
    start = idxs[0]
    end = len(lines)
    for i in range(start + 1, len(lines)):
        s = lines[i].strip()
        if s.startswith("## ") or s.startswith("# "):
            end = i
            break
    # 2. 章节内开关行去重（保留首个），非法值 warning
    toggle_idx = [i for i in range(start + 1, end) if lines[i].startswith(TOGGLE_PREFIX)]
    if toggle_idx:
        first = toggle_idx[0]
        value = lines[first][len(TOGGLE_PREFIX):].strip()
        if value not in ("开启", "关闭"):
            warns.append({"code": "INVALID_TOGGLE", "file": entry_name,
                          "message": f"产物自动提交开关值非法（{value}），按关闭处理", "detail": {}})
        drop = set(toggle_idx[1:])
        lines = [l for i, l in enumerate(lines) if i not in drop]
        return "\n".join(lines), warns
    # 3. 章节末尾插入（end 之前，吸收尾部空行）
    insert_at = end
    while insert_at > start + 1 and lines[insert_at - 1].strip() == "":
        insert_at -= 1
    lines = lines[:insert_at] + [TOGGLE_PREFIX + TOGGLE_DEFAULT, ""] + lines[end:]
    return "\n".join(lines), warns
```

`_compose_entry` 末尾追加调用并把 warnings 并入返回。

- [ ] **Step 4: 运行确认通过 + 全量回归**

- [ ] **Step 5: Commit**

```bash
git add cadence-init/skills/rule-config/scripts/rule-config.py cadence-init/skills/rule-config/tests/test_rule_config.py
git commit -m "feat(rule-config): 产物自动提交开关写入与取值语义"
```

---

### Task 9: 合并语义与对账文档同步

**Files:**
- Modify: `cadence-init/skills/rule-config/references/merge-semantics.md`（§6 SM 表、L0 表"当前 v1"表述、21 行合计 62→64）
- Modify: `cadence-init/skills/rule-config/tests/skill-clause-map.md`（条款对账、13/368 行计数）
- Modify: `cadence-init/skills/rule-config/SKILL.md`（摘要语义描述、129 行计数 62→64、开关说明）

- [ ] **Step 1: merge-semantics.md**
- §6 重写为 SM-01~05：`SM-01 幂等跳过` / `SM-02 章节缺失创建` / `SM-03 退役引用删除（RETIRED_RULE_FILES）` / `SM-04 重排重编号与旧文案替换` / `SM-05 用户内容保留+warnings`；每行含两模式同动作、备份需求"无"、对应测试 ID。
- L0 表："当前 v1"表述改"当前版本（v2）"，旧版集合补 v1；补充混合标记/重复区块归并语义行。
- 文首合计 62 → 64 行。

- [ ] **Step 2: skill-clause-map.md 与 SKILL.md**
- skill-clause-map：新增 SM-04/SM-05、L0 v2、warnings、toggle、规范化相关条款到测试 ID 的映射；计数 62→64。
- SKILL.md：概述中"缺失摘要行追加"改"强制规则章节规范化（创建/清理/重排/保留）"；新增开关与 warnings 简述；计数 62→64。

- [ ] **Step 3: 校验**
Run: `grep -n "62" cadence-init/skills/rule-config/references/merge-semantics.md cadence-init/skills/rule-config/SKILL.md cadence-init/skills/rule-config/tests/skill-clause-map.md`
Expected: 无残留"62 行"合计表述

- [ ] **Step 4: Commit**

```bash
git add cadence-init/skills/rule-config/references/merge-semantics.md cadence-init/skills/rule-config/tests/skill-clause-map.md cadence-init/skills/rule-config/SKILL.md
git commit -m "docs(rule-config): SM-01~05 与 L0 v2 合并语义及对账同步"
```

---

### Task 10: 本仓库副本同步

**Files:**
- Modify: 本仓库 `.claude/rules/document-storage.md`、`.claude/rules/` 内同步副本（按 managed-rule-lifecycle"先改规范源再同步副本"要求）
- Modify: 本仓库 `AGENTS.md` / `CLAUDE.md` 的 L0 区块（v1→v2）

- [ ] **Step 1: 同步规范源副本**
将 `references/rules/document-storage.md` 等变更从规范源同步到本仓库 `.claude/rules/` 对应文件。

- [ ] **Step 2: 更新本仓库入口 L0**
将本仓库 `AGENTS.md`/`CLAUDE.md` 中 L0 区块内容替换为 v2 内核全文（标记同步升 v2），区块外内容不动。

- [ ] **Step 3: 校验**
Run: `diff <(sed -n '/cadence-managed:openspec-superpowers-routing:v2:start/,/cadence-managed:openspec-superpowers-routing:v2:end/p' AGENTS.md) cadence-init/skills/rule-config/references/rules/agent-routing-kernel.md`
Expected: 无差异

- [ ] **Step 4: Commit**

```bash
git add .claude/rules/ AGENTS.md CLAUDE.md
git commit -m "docs(rule-config): 同步本仓库规则副本与入口 L0 v2"
```

---

### Task 11: 端到端验证（/tmp 问题文件回归）

**Files:**
- Test: `cadence-init/skills/rule-config/tests/test_rule_config.py`（`TestEndToEndRegression`）

- [ ] **Step 1: 用 /tmp/AGENTS.md、/tmp/CLAUDE.md 作为 fixture 写端到端测试**

```python
class TestEndToEndRegression(unittest.TestCase):
    def _run(self, agents_text, claude_text):
        import tempfile, subprocess, json
        from pathlib import Path
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "package.json").write_text('{"scripts":{"test":"vitest","lint":"oxlint src"}}')
        (root / "AGENTS.md").write_text(agents_text)
        (root / "CLAUDE.md").write_text(claude_text)
        rep = root / "r.json"
        subprocess.run(["python3", str(SCRIPT_PATH), "apply", "--project-root", str(root),
                        "--report", str(rep), "--no-interrupt"], check=True)
        return root, json.loads(rep.read_text())

    def test_kb_agents_gets_full_section(self):
        """ut-e2e-kb：KB 型 AGENTS.md 获得完整强制规则且用户内容保留。"""
        kb = Path("/tmp/AGENTS.md").read_text()
        claude = Path("/tmp/CLAUDE.md").read_text()
        root, rep = self._run(kb, claude)
        agents = (root / "AGENTS.md").read_text()
        self.assertIn("### 1. 语言规则", agents)
        self.assertIn("### 7. 代码阅读规则", agents)
        self.assertIn("## WHERE TO LOOK", agents)          # 用户 KB 内容保留
        self.assertIn("产物自动提交（design/plan）**：关闭", agents)
        self.assertNotIn("serena-usage.md", agents)

    def test_claude_serena_removed_and_renumbered(self):
        """ut-e2e-claude：CLAUDE.md Serena 清理、重排、双入口技术栈一致。"""
        kb = Path("/tmp/AGENTS.md").read_text()
        claude = Path("/tmp/CLAUDE.md").read_text()
        root, rep = self._run(kb, claude)
        c = (root / "CLAUDE.md").read_text()
        a = (root / "AGENTS.md").read_text()
        self.assertNotIn("Serena", c)
        self.assertIn("### 1. 语言规则", c)
        self.assertNotIn("### 8. Playwright", c)  # 项目无 playwright.md
        # 双入口技术栈一致
        for name, text in (("CLAUDE.md", c), ("AGENTS.md", a)):
            self.assertIn("- **语言**：JavaScript/TypeScript", text, name)
```

（fixture 不存在时 `setUp` 跳过：`if not Path("/tmp/AGENTS.md").exists(): self.skipTest(...)`，或将两份文件复制到 `tests/fixtures/` 作为永久 fixture——**采用后者**：复制为 `tests/fixtures/entry-kb-agents.md` 与 `entry-drift-claude.md`，测试读 fixtures。）

- [ ] **Step 2: 运行确认通过 + 全量回归**

Run: `python3 -m unittest discover -s cadence-init/skills/rule-config/tests -v` + `bash cadence-init/skills/rule-config/tests/verify-managed-lifecycle.sh`
Expected: 全绿

- [ ] **Step 3: Commit**

```bash
git add cadence-init/skills/rule-config/tests/
git commit -m "test(rule-config): /tmp 问题入口文件端到端回归"
```

---

## Self-Review 结论

- **Spec 覆盖**：entry-file-normalization 6 Requirement → Task 2/3/4/5/11；superpowers-artifact-governance 3 Requirement → Task 7/8；managed-rule-lifecycle MODIFIED → Task 6/9；rule-config-scripted-execution MODIFIED（warnings/合并语义）→ Task 4/9。无缺口。
- **占位符**：Task 3 步骤 3 中"无章节创建"分支留有 `...` 伪码（插入位置逻辑在 Task 5 落定，实施时合并完成），其余均为可执行代码。
- **类型一致**：`_compose_entry` 三元组 `(text, diffs, warnings)`、`_normalize_mandatory_rules`/`_ensure_commit_toggle`/`_normalize_l0_to_single_block` 均 `(text, warnings)`、错误码枚举全程一致。

## 执行交接

Plan 已保存到 `cadence/plans/2026-08-18_计划文档_实施_rule-config入口规范化与产物覆盖及提交开关_v1.0.md`。两种执行方式：

1. **Subagent-Driven（推荐）**——每个 Task 派发新 subagent，任务间两阶段审查，迭代快
2. **Inline Execution**——本会话内按 executing-plans 分批执行+检查点

选哪种？
