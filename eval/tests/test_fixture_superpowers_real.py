"""superpowers real 模式 fixture 测试：真实源软链桥接（方案 A）。"""
import unittest
from pathlib import Path

import eval.fixtures.generator as gen

REPO_ROOT = Path(__file__).resolve().parents[2]
REAL_SKILL_NAMES = [
    "brainstorming", "using-superpowers", "writing-plans", "executing-plans",
    "test-driven-development", "systematic-debugging", "verification-before-completion",
    "requesting-code-review", "receiving-code-review", "finishing-a-development-branch",
    "subagent-driven-development", "dispatching-parallel-agents", "skill-creator",
    "writing-skills",
]


def _make_real_source(base: Path, names=None) -> Path:
    """构造可控的"真实 superpowers 源"（模拟 ~/.agents/superpowers）。"""
    src = base / "real-superpowers"
    skills = src / "skills"
    skills.mkdir(parents=True)
    for name in (names if names is not None else REAL_SKILL_NAMES):
        (skills / name).mkdir()
        (skills / name / "SKILL.md").write_text(f"# {name}\n", encoding="utf-8")
    (skills / "knowledge-base-context").mkdir()  # 哨兵：不投影
    (skills / "knowledge-base-context" / "SKILL.md").write_text("# sentinel\n", encoding="utf-8")
    return src


class TestSuperpowersRealMode(unittest.TestCase):
    def setUp(self):
        import tempfile
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_real_mode_links_real_skill_names(self):
        """real 模式：四层链名=真实技能名，resolve 到真实源，无 superpower-N 假名。"""
        src = _make_real_source(self.base)
        fx = gen.make_fixture("fresh", self.base / "fx", REPO_ROOT,
                              superpowers_mode="real", real_superpowers_source=src)
        for rel in (".claude/skills", ".agents/skills", ".codex/skills/skills", ".pi/agent/skills"):
            layer = fx.home / rel
            links = {p.name for p in layer.iterdir()}
            # 层内= Cadence 技能链 + 14 条真实 superpowers 链（超集）；
            # 不得出现 superpower-N 假名
            self.assertTrue(set(REAL_SKILL_NAMES) <= links, rel)
            self.assertFalse([n for n in links if n.startswith("superpower-")], rel)
            cadence_names = {d.name for d in REPO_ROOT.joinpath("cadence-init/skills").iterdir()
                             if (d / "SKILL.md").is_file()}
            for p in layer.iterdir():
                # 只验 superpowers 14 链指向真实源；与 Cadence 技能重名者（如
                # skill-creator）由 _install_skills 先占位指向工作树——与真实
                # 环境安装顺序一致，属预期行为，不视为桥接失败
                if p.name in REAL_SKILL_NAMES and p.name not in cadence_names:
                    self.assertEqual(p.resolve(), (src / "skills" / p.name).resolve(), rel)
        self.assertFalse((fx.home / ".agents" / "superpowers").exists(),
                         "real 模式不得在 fixture 内造假源")

    def test_real_mode_missing_source_fails_fast(self):
        """real 模式：源不存在 → ValueError 带安装指引。"""
        with self.assertRaises(ValueError) as cm:
            gen.make_fixture("fresh", self.base / "fx", REPO_ROOT,
                             superpowers_mode="real",
                             real_superpowers_source=self.base / "nope")
        self.assertIn("superpowers", str(cm.exception))
        self.assertIn("pre-check", str(cm.exception))

    def test_real_mode_rejects_incomplete_skill_set(self):
        """real 模式：技能清单不齐（13 个）→ ValueError 列出现状。"""
        src = _make_real_source(self.base, names=REAL_SKILL_NAMES[:13])
        with self.assertRaises(ValueError) as cm:
            gen.make_fixture("fresh", self.base / "fx", REPO_ROOT,
                             superpowers_mode="real", real_superpowers_source=src)
        self.assertIn("brainstorming", str(cm.exception))

    def test_real_mode_rejects_non_directory_skill(self):
        """real 模式：技能条目非目录/断链 → ValueError。"""
        src = _make_real_source(self.base)
        import shutil
        shutil.rmtree(src / "skills" / "brainstorming")
        (src / "skills" / "brainstorming").write_text("not a dir", encoding="utf-8")
        with self.assertRaises(ValueError):
            gen.make_fixture("fresh", self.base / "fx", REPO_ROOT,
                             superpowers_mode="real", real_superpowers_source=src)

    def test_mock_mode_unchanged_default(self):
        """默认参数保持 mock 现状：superpower-N 假名 + fixture 内假源。"""
        fx = gen.make_fixture("fresh", self.base / "fx", REPO_ROOT)
        links = {p.name for p in (fx.home / ".claude" / "skills").iterdir()}
        self.assertTrue(any(n.startswith("superpower-") for n in links))
        self.assertTrue((fx.home / ".agents" / "superpowers" / "skills").is_dir())


class TestNightRealSuperpowersGuard(unittest.TestCase):
    def test_validate_real_superpowers_missing(self):
        """夜测真实模式启动校验：源缺失返回错误信息含安装指引。"""
        from eval.runner import night
        msg = night.validate_real_superpowers(Path("/nonexistent-superpowers"))
        self.assertIsNotNone(msg)
        self.assertIn("pre-check", msg)

    def test_validate_real_superpowers_ok(self):
        """校验通过：14 技能齐 → None。"""
        import tempfile
        from pathlib import Path as P
        with tempfile.TemporaryDirectory() as td:
            src = _make_real_source(P(td))
            from eval.runner import night
            self.assertIsNone(night.validate_real_superpowers(src))


if __name__ == "__main__":
    unittest.main()
