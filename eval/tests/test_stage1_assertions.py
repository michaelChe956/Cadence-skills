"""eval/tests/test_stage1_assertions.py —— 阶段一产物断言表（tasks 1.2 断言部分）。"""
import json
import os
import tempfile
import unittest
from pathlib import Path

from eval.fixtures import generator as gen
from eval.install import assertions as asrt


def _installed_workspace(root: Path) -> None:
    """构造一个满足阶段一断言的"已安装"workspace。"""
    rules = root / ".claude" / "rules"
    rules.mkdir(parents=True, exist_ok=True)  # 先建目录再写文件（否则 helper 自身报错）
    for name in gen.expected_rules_files():
        (rules / name).write_text(
            "---\ndescription: 测试规则占位\n---\n\n# 规则正文\n", encoding="utf-8")
    # omp 桥接资产（Change A 产物形态）：.agents/rules 软链 + .omp/AGENTS.md 受管正文
    bridge = root / ".agents" / "rules"
    bridge.mkdir(parents=True, exist_ok=True)
    for name in gen.expected_rules_files():
        os.symlink(f"../../.claude/rules/{name}", bridge / name)
    omp = root / ".omp"
    omp.mkdir(parents=True, exist_ok=True)
    (omp / "AGENTS.md").write_text(asrt.OMP_AGENTS_MD_BODY, encoding="utf-8")
    claude = (root / "CLAUDE.md").read_text(encoding="utf-8") if (root / "CLAUDE.md").exists() else ""
    (root / "CLAUDE.md").write_text(
        "<!-- cadence-managed:openspec-superpowers-routing:v5:start -->\n"
        "Cadence L0 路由内核 v5\n" + claude +
        "<!-- cadence-managed:openspec-superpowers-routing:v5:end -->\n", encoding="utf-8")
    deny_doc = {"permissions": {"deny": [
        "UserDeny",
        "@@cadence-managed:permission-gate:v1:start@@",
        "Grep", "Glob", "Bash(grep:*)",
        "@@cadence-managed:permission-gate:v1:end@@"]}}
    (root / ".claude" / "settings.json").write_text(
        json.dumps(deny_doc, ensure_ascii=False, indent=2), encoding="utf-8")
    (root / "AGENTS.md").write_text(
        "intro\n<!-- cadence-managed:codex-rules-inline:v1:start -->\n链\n"
        "<!-- cadence-managed:codex-rules-inline:v1:end -->\n", encoding="utf-8")
    (root / ".mcp.json").write_text(json.dumps({"mcpServers": {
        "zai-mcp-server": {"command": "npx"}, "MiniMax": {"command": "uvx"},
        "codegraph": {"command": "codegraph-server"},
        "existing-server": {"command": "echo"}}}, indent=2), encoding="utf-8")
    (root / ".codex").mkdir(exist_ok=True)
    (root / ".codex" / "config.toml").write_text(
        "[mcp_servers.zai-mcp-server]\ncommand = \"npx\"\n"
        "[mcp_servers.MiniMax]\ncommand = \"uvx\"\n"
        "[mcp_servers.codegraph]\ncommand = \"codegraph-server\"\n"
        "[mcp_servers.existing-server]\ncommand = \"echo\"\n", encoding="utf-8")
    (root / ".gitignore").write_text(
        ".worktrees/\n.mcp.json\n.codex/config.toml\ncadence/cache/mcp-availability/\n",
        encoding="utf-8")
    pr = root / "cadence" / "project-rules"
    (pr / "examples").mkdir(parents=True)
    (pr / "README.md").write_text("# 项目规则\n", encoding="utf-8")


TEXTS = {"pre-check": "诊断报告：镜像与环境检查完成", "rule-config": "apply 完成",
         "mcp-configuration": "MCP 配置完成", "project-rules-examples": "模板就位"}


class TestStage1Assertions(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "fixture"
        self.root.mkdir()

    def _all_ok(self, variant="fresh", verify_exit=0, **kw):
        results = asrt.assert_stage1(variant, self.root, verify_exit, dict(TEXTS), kw.get("extra"))
        bad = [r for r in results if not r.ok]
        self.assertEqual(bad, [], [f"{r.name}: {r.detail}" for r in bad])
        return results

    def test_fresh_all_green(self):
        """ut-s1-fresh：全新变体全绿（清单/L0v5/权限区/内联区/verify=0）。"""
        _installed_workspace(self.root)
        names = [r.name for r in self._all_ok()]
        for expect in ("pre-check.report", "pre-check.zero-change", "rules.manifest",
                       "l0.v5", "gate.region", "codex.inline", "verify.exit0",
                       "mcp.valid", "mcp.codex-consistent", "mcp.gitignore",
                       "prx.placed", "prx.not-rules"):
            self.assertIn(expect, names)

    def test_missing_rule_file_fails_manifest(self):
        """ut-s1-manifest：规则清单缺文件判红。"""
        _installed_workspace(self.root)
        (self.root / ".claude/rules/language.md").unlink()
        results = asrt.assert_stage1("fresh", self.root, 0, dict(TEXTS))
        self.assertFalse(next(r for r in results if r.name == "rules.manifest").ok)

    def test_verify_nonzero_fails(self):
        """ut-s1-verify：--verify 退出码非 0 判红（p1 断言原语消费）。"""
        _installed_workspace(self.root)
        results = asrt.assert_stage1("fresh", self.root, 1, dict(TEXTS))
        self.assertFalse(next(r for r in results if r.name == "verify.exit0").ok)

    def test_zero_change_openspec_layered_guard(self):
        """ut-s1-zerochange-layered：11 场景白名单与变更检测（含 4 反斜杠回归）。"""
        cases = [
            ({"openspec/specs/base.md": "h"}, {"openspec/specs/base.md": "h", "openspec/config.yaml": "new", ".claude/skills/openspec-x": "x"}, []),
            ({"openspec/config.yaml": "old"}, {"openspec/config.yaml": "new"}, ["openspec/config.yaml"]),
            ({"openspec/config.yaml": "old"}, {}, ["openspec/config.yaml"]),
            ({"openspec/specs/x.md": "old"}, {"openspec/specs/x.md": "new"}, ["openspec/specs/x.md"]),
            ({}, {"openspec/specs/new.md": "x"}, ["openspec/specs/new.md"]),
            ({}, {"unexpected": "x"}, ["unexpected"]),
            ({}, {".claude/skills/openspec-x": "x"}, []),
            ({r"openspec\config.yaml": "old"}, {r"openspec\config.yaml": "new"}, ["openspec/config.yaml"]),
            ({r"openspec\specs\x.md": "old"}, {r"openspec\specs\x.md": "new"}, ["openspec/specs/x.md"]),
            ({}, {r"unexpected\x.txt": "x"}, ["unexpected/x.txt"]),
            ({}, {r".claude\skills\openspec-x": "x"}, []),
            ({}, {".agents/skills/.openspec-target": "codex"}, []),
        ]
        for before, after, expected in cases:
            with self.subTest(before=before, after=after):
                self.assertEqual(asrt._zero_change_violations(before, after), expected)

    def test_pre_check_dirty_tree_fails(self):
        """ut-s1-zerochange：pre-check 产生文件改动判红。"""
        _installed_workspace(self.root)
        results = asrt.assert_stage1("fresh", self.root, 0, dict(TEXTS),
                                     {"pre_check_clean": False})
        self.assertFalse(next(r for r in results if r.name == "pre-check.zero-change").ok)


class TestPreCheckAssertions(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "fixture"
        self.root.mkdir()

    def test_report_projections_links_phases_and_budget_green(self):
        _installed_workspace(self.root)
        phase_actions = {
            "base-tools": "do_base_tools",
            "openspec": "update-verify",
            "superpowers-git": "fetch-pull-ff-only",
            "superpowers-links": "all-skipped",
            "verify": "all-skipped",
        }
        report = {
            "overall": "success", "steps": [],
            "phases": [
                {"phase": n, "result": "skipped", "action": phase_actions[n], "duration_ms": 12,
                 "created": 0, "updated": 0, "skipped": 14, "conflicts": 0, "error": None}
                for n in ("base-tools", "openspec", "superpowers-git", "superpowers-links", "verify")
            ],
        }
        report["phases"][2].update({"action": "fetch-pull-ff-only", "origin": "fixture-origin", "branch": "main", "before_revision": "abc", "after_revision": "abc"})
        results = asrt.assert_stage1(
            "fresh", self.root, 0, dict(TEXTS),
            {"pre_check_report": report, "pre_check_tool_calls": 1, "pre_check_duration_s": 8.0},
        )
        self.assertEqual([r.name for r in results if not r.ok], [])

    def test_home_path_schema_rejects_mismatch_and_missing_mode(self):
        """ut-s1-home-schema：HOME 路径事实缺失或错配必须判红。"""
        fixture = self.root
        bad_inherited = {"mode": "inherited", "path": str(fixture),
                         "fixture_path": str(fixture), "before": {}, "after": {}}
        missing_mode = {"path": str(fixture), "fixture_path": str(fixture),
                        "before": {}, "after": {}}
        self.assertFalse(asrt._precheck_home_changed(bad_inherited)[0])
        self.assertFalse(asrt._precheck_home_changed(missing_mode)[0])

    def test_home_path_schema_accepts_matching_fixture(self):
        """ut-s1-home-schema-green：fixture 模式路径与 fixture_path 一致时通过。"""
        info = {"mode": "fixture", "path": str(self.root),
                "fixture_path": str(self.root), "before": {}, "after": {}}
        self.assertTrue(asrt._precheck_home_changed(info)[0])

    def test_bad_report_or_budget_fails(self):
        _installed_workspace(self.root)
        results = asrt.assert_stage1(
            "fresh", self.root, 0, dict(TEXTS),
            {"pre_check_report": {"overall": "success", "steps": [], "phases": []},
             "pre_check_tool_calls": 6, "pre_check_duration_s": 121.0},
        )
        by_name = {r.name: r for r in results}
        self.assertFalse(by_name["pre-check.projections"].ok)
        self.assertFalse(by_name["pre-check.performance"].ok)


class TestStage1VariantAssertions(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "fixture"
        self.root.mkdir()

    def test_v3_upgrade_assertions(self):
        """ut-s1-v3：v3 变体断言升级+备份+区块外逐字不变。"""
        _installed_workspace(self.root)
        # 区块外用户内容（升级后必须逐字保留）与 legacy 备份先行落位
        with (self.root / "CLAUDE.md").open("a", encoding="utf-8") as fh:
            fh.write("\n## 团队约定\n\n- 提交前跑 `npm test`。\n")
        legacy = self.root / "cadence" / "legacy" / "20260902"
        legacy.mkdir(parents=True)
        (legacy / "CLAUDE.md.v3.bak").write_text("v3 backup", encoding="utf-8")
        results = asrt.assert_stage1("v3", self.root, 0, dict(TEXTS),
                                     {"outside_l0_baseline": "## 团队约定\n\n- 提交前跑 `npm test`。\n"})
        bad = [r for r in results if not r.ok]
        self.assertEqual(bad, [], [f"{r.name}: {r.detail}" for r in bad])

    def test_v3_outside_changed_fails(self):
        """ut-s1-v3-outside：区块外内容被改判红。"""
        _installed_workspace(self.root)
        results = asrt.assert_stage1("v3", self.root, 0, dict(TEXTS),
                                     {"outside_l0_baseline": "## 旧内容\n"})
        self.assertFalse(next(r for r in results if r.name == "v3.outside-verbatim").ok)

    def test_mcp_pre_preserves_existing_server(self):
        """ut-s1-mcppre：既有 server 不被覆盖（集合合并语义）。"""
        _installed_workspace(self.root)
        doc = json.loads((self.root / ".mcp.json").read_text(encoding="utf-8"))
        doc["mcpServers"].pop("existing-server")
        (self.root / ".mcp.json").write_text(json.dumps(doc), encoding="utf-8")
        results = asrt.assert_stage1("mcp_pre", self.root, 0, dict(TEXTS))
        self.assertFalse(next(r for r in results if r.name == "mcp.pre-existing").ok)

    def test_prx_must_not_touch_rules(self):
        """ut-s1-prx：project-rules-examples 不得写 .claude/rules/。"""
        import hashlib
        _installed_workspace(self.root)
        # 快照口径与实现一致：文件名→sha256（interfaces：rules_before 为哈希快照）
        before = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                  for p in (self.root / ".claude/rules").iterdir()}
        results = asrt.assert_stage1("fresh", self.root, 0, dict(TEXTS),
                                     {"rules_before": before})
        self.assertTrue(next(r for r in results if r.name == "prx.not-rules").ok)
        before["injected.md"] = "被改了"
        results = asrt.assert_stage1("fresh", self.root, 0, dict(TEXTS),
                                     {"rules_before": before})
        self.assertFalse(next(r for r in results if r.name == "prx.not-rules").ok)


class TestStage1RuleAssetAssertions(unittest.TestCase):
    """四条净新增确定性断言：rules.frontmatter / omp.symlinks / omp.agents-md / agents-md.budget。"""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "fixture"
        self.root.mkdir()

    def _by_name(self):
        return {r.name: r for r in
                asrt.assert_stage1("fresh", self.root, 0, dict(TEXTS))}

    def test_rule_assets_all_green_with_readme_exempt(self):
        """ut-s1-assets-green：完整正例四条全绿；README.md 无 frontmatter 也豁免两集合。"""
        _installed_workspace(self.root)
        # README 是仓库自有文档：无 frontmatter 不判红，也不要求 .agents/rules 软链
        (self.root / ".claude" / "rules" / "README.md").write_text(
            "# 规则索引说明，无 frontmatter\n", encoding="utf-8")
        by = self._by_name()
        for name in ("rules.frontmatter", "omp.symlinks", "omp.agents-md",
                     "agents-md.budget"):
            self.assertTrue(by[name].ok, f"{name}: {by[name].detail}")

    def test_rules_frontmatter_missing_description_fails(self):
        """ut-s1-frontmatter-bad：规则文件缺 frontmatter description → 判红并指明文件名。"""
        _installed_workspace(self.root)
        (self.root / ".claude" / "rules" / "language.md").write_text(
            "# 语言规则\n\n正文无 frontmatter 围栏。\n", encoding="utf-8")
        a = self._by_name()["rules.frontmatter"]
        self.assertFalse(a.ok)
        self.assertIn("language.md", a.detail)

    def test_omp_symlinks_missing_link_fails(self):
        """ut-s1-symlinks-bad：.agents/rules 缺一条软链 → 集合不符判红。"""
        _installed_workspace(self.root)
        (self.root / ".agents" / "rules" / "language.md").unlink()
        self.assertFalse(self._by_name()["omp.symlinks"].ok)

    def test_omp_symlinks_plain_file_fails(self):
        """ut-s1-symlinks-plain：软链被普通文件顶替（OR-07 形态）→ 判红。"""
        _installed_workspace(self.root)
        link = self.root / ".agents" / "rules" / "language.md"
        link.unlink()
        link.write_text("用户自留普通文件\n", encoding="utf-8")
        a = self._by_name()["omp.symlinks"]
        self.assertFalse(a.ok)
        self.assertIn("language.md", a.detail)

    def test_omp_agents_md_unmanaged_content_fails(self):
        """ut-s1-omp-md-bad：.omp/AGENTS.md 非受管正文（逐字比对）→ 判红。"""
        _installed_workspace(self.root)
        (self.root / ".omp" / "AGENTS.md").write_text("<!-- cadence-managed:omp-context:v1 -->\n"
                                                      "@../.claude/CLAUDE.md\n自写内容\n",
                                                      encoding="utf-8")
        self.assertFalse(self._by_name()["omp.agents-md"].ok)

    def test_agents_md_budget_exceeded_fails(self):
        """ut-s1-budget-bad：AGENTS.md 超 200 行预算 → 判红并报行数。"""
        _installed_workspace(self.root)
        (self.root / "AGENTS.md").write_text(
            "\n".join(f"第 {i} 行" for i in range(1, 202)) + "\n", encoding="utf-8")
        a = self._by_name()["agents-md.budget"]
        self.assertFalse(a.ok)
        self.assertIn("201", a.detail)

    def test_agents_md_budget_boundary_200_ok(self):
        """ut-s1-budget-edge：恰好 200 行在预算内（边界不判红）。"""
        _installed_workspace(self.root)
        (self.root / "AGENTS.md").write_text(
            "\n".join(f"第 {i} 行" for i in range(1, 201)) + "\n", encoding="utf-8")
        self.assertTrue(self._by_name()["agents-md.budget"].ok)


if __name__ == "__main__":
    unittest.main()
