"""eval/tests/test_fixture_generator.py —— fixture 四变体与隔离（tasks 1.1/1.4 变体部分）。"""
import tempfile
import unittest
from pathlib import Path

from eval.fixtures import generator as gen

REPO_ROOT = Path(__file__).resolve().parents[2]


class TestFixtureGenerator(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)

    def test_four_variants_declared(self):
        """ut-fx-variants：四变体齐备（含未安装对照组）。"""
        self.assertEqual(gen.VARIANTS, ("fresh", "v3", "mcp_pre", "control"))

    def test_fresh_has_project_but_no_claude(self):
        """ut-fx-fresh：全新变体含 coding 工程结构与 git 仓库，无任何 Cadence 痕迹。"""
        fx = gen.make_fixture("fresh", self.base, REPO_ROOT)
        self.assertTrue((fx.root / "package.json").is_file())
        self.assertTrue((fx.root / "src" / "orders" / "entry.py").is_file())
        self.assertTrue((fx.root / ".git").is_dir())
        # P7 探针的截图占位（1x1 PNG，魔数校验）
        png = fx.root / "assets" / "error.png"
        self.assertTrue(png.is_file())
        self.assertEqual(png.read_bytes()[:8], b"\x89PNG\r\n\x1a\n")
        self.assertFalse((fx.root / "CLAUDE.md").exists())
        self.assertFalse((fx.root / ".claude").exists())

    def test_installed_home_has_skill_links(self):
        """ut-fx-links：安装变体的隔离 HOME 复刻三层软链布局（14 skill 全量）。"""
        fx = gen.make_fixture("fresh", self.base, REPO_ROOT)
        for skill in ("pre-check", "rule-config", "mcp-configuration", "project-rules-examples"):
            link = fx.home / ".claude" / "skills" / skill
            self.assertTrue(link.is_symlink(), link)
            self.assertTrue((link / "SKILL.md").is_file())
        shared = fx.home / ".agents" / "skills" / "rule-config"
        self.assertTrue(shared.parent.is_symlink() or shared.is_symlink() or shared.exists())

    def test_control_home_has_no_links(self):
        """ut-fx-control：对照组不安装（HOME 无 skill 链接），项目同构。"""
        fx = gen.make_fixture("control", self.base, REPO_ROOT)
        self.assertFalse((fx.home / ".claude" / "skills").exists())
        self.assertTrue((fx.root / "package.json").is_file())

    def test_v3_variant_seeds_frozen_l0(self):
        """ut-fx-v3：v3 变体 CLAUDE.md 逐字含冻结 v3 历史源 + 区块外用户文本。"""
        fx = gen.make_fixture("v3", self.base, REPO_ROOT)
        text = (fx.root / "CLAUDE.md").read_text(encoding="utf-8")
        v3 = (REPO_ROOT / "cadence-init/skills/rule-config/references/rules/l0-history"
              / "agent-routing-kernel-v3.md").read_text(encoding="utf-8")
        self.assertIn(v3, text)
        self.assertIn("## 团队约定", text)  # 区块外内容（升级断言的逐字保留对象）

    def test_mcp_pre_variant_preserves_servers(self):
        """ut-fx-mcppre：已配变体带既有 server 与 codegraph，测防重写。"""
        import json
        fx = gen.make_fixture("mcp_pre", self.base, REPO_ROOT)
        doc = json.loads((fx.root / ".mcp.json").read_text(encoding="utf-8"))
        self.assertIn("existing-server", doc["mcpServers"])
        self.assertIn("codegraph", doc["mcpServers"])
        toml = (fx.root / ".codex" / "config.toml").read_text(encoding="utf-8")
        self.assertIn("[mcp_servers.existing-server]", toml)

    def test_fixture_files_leak_no_repo_path(self):
        """ut-fx-noleak：fixture 项目文本文件不含 Cadence 仓库路径（防泄漏 spec 场景）。"""
        fx = gen.make_fixture("fresh", self.base, REPO_ROOT)
        needle = str(REPO_ROOT)
        for p in sorted(fx.root.rglob("*")):
            if p.is_file():
                self.assertNotIn(needle, p.read_text(encoding="utf-8", errors="ignore"), p)

    def test_theme_rotation_changes_module(self):
        """ut-fx-theme：题库轮换——不同 theme 生成不同模块名（同构不同名）。"""
        a = gen.make_fixture("fresh", self.base / "a", REPO_ROOT, theme="orders")
        b = gen.make_fixture("fresh", self.base / "b", REPO_ROOT, theme="billing")
        self.assertTrue((a.root / "src" / "orders").is_dir())
        self.assertTrue((b.root / "src" / "billing").is_dir())
        self.assertEqual(len(gen.expected_rules_files()), 9)

    def test_global_config_snapshot_diff(self):
        """ut-fx-snapshot：全局配置快照可对比出夜间运行期间的变化。"""
        fx = gen.make_fixture("fresh", self.base, REPO_ROOT)
        before = gen.snapshot_global_configs(fx.home)
        (fx.home / ".claude").mkdir(parents=True, exist_ok=True)
        (fx.home / ".claude" / "settings.json").write_text('{"x":1}', encoding="utf-8")
        after = gen.snapshot_global_configs(fx.home)
        self.assertEqual(gen.diff_global_configs(before, after),
                         [str(fx.home / ".claude" / "settings.json")])

    def test_global_config_snapshot_real_home_sim(self):
        """ut-fx-realhome：HOME 策略 b 方案——run_night 以真实 HOME 路径传参
        快照/ Diff，函数对任意 home（含 Path.home()）成立，漂移可归位到具体文件。"""
        fake_home = self.base / "realhome"  # 模拟 Path.home() 的用户级配置树
        (fake_home / ".codex").mkdir(parents=True)
        (fake_home / ".codex" / "config.toml").write_text("x = 1\n", encoding="utf-8")
        before = gen.snapshot_global_configs(fake_home)
        (fake_home / ".codex" / "config.toml").write_text("x = 2\n", encoding="utf-8")
        after = gen.snapshot_global_configs(fake_home)
        self.assertEqual(gen.diff_global_configs(before, after),
                         [str(fake_home / ".codex" / "config.toml")])


if __name__ == "__main__":
    unittest.main()
