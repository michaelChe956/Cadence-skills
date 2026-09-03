"""eval/tests/test_idempotency.py —— 幂等双跑与 gate 过渡三遍稳态（tasks 1.3）。"""
import tempfile
import unittest
from pathlib import Path

from eval.fixtures import generator as gen
from eval.install import idempotency as idem
from eval.runner import cli as cli_mod

REPO_ROOT = Path(__file__).resolve().parents[2]


class TestIdempotency(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.bin = cli_mod.mock_bin(self.base)
        self.fx = gen.make_fixture("fresh", self.base / "fx", REPO_ROOT)

    def test_two_passes_byte_identical(self):
        """ut-idem-2pass：双跑末遍 workspace diff 为空（jarvy 先例）。"""
        rep = idem.run_idempotency("claude", self.fx, {"pinned_model": "glm-5.3"},
                                   passes=2, bin_dir=self.bin, verify=lambda r: 0)
        self.assertTrue(rep["stable"])
        self.assertEqual(rep["diffs"][-1], {})

    def test_three_passes_locks_gate_transition(self):
        """ut-idem-3pass：gate 从无到有过渡写入场景，第三遍达稳态幂等（显式锁定）。

        依据 rule-config SKILL：无 .mcp.json 的全新项目首轮 apply 因 S8 先写
        .mcp.json 实际创建权限区块；mock 首轮即含区块，第三遍仍必须零 diff。
        """
        rep = idem.run_idempotency("claude", self.fx, {"pinned_model": "glm-5.3"},
                                   passes=3, bin_dir=self.bin, verify=lambda r: 0)
        self.assertTrue(rep["stable"])
        self.assertEqual(rep["diffs"][2], {})

    def test_snapshot_excludes_git(self):
        """ut-idem-snap：快照排除 .git/ 与运行器自身产物 .eval-*（P8 可判）。"""
        (self.fx.root / ".eval-claude-123-456-stdout.jsonl").write_text(
            "x", encoding="utf-8")
        snap = idem.snapshot_tree(self.fx.root)
        self.assertTrue(all(not k.startswith(".git/") for k in snap))
        self.assertTrue(all(not k.startswith(".eval-") for k in snap))
        self.assertIn("package.json", snap)

    def test_detects_append_regression(self):
        """ut-idem-regress：第二遍追加内容被 diff 捕获（防假绿）。"""
        gi = self.fx.root / ".gitignore"
        gi.write_text("node_modules/\n", encoding="utf-8")  # fresh 变体无 .gitignore，先落初始内容
        first = idem.snapshot_tree(self.fx.root)
        gi.write_text(gi.read_text(encoding="utf-8") + "\n追加行\n", encoding="utf-8")
        diff = idem.diff_trees(first, idem.snapshot_tree(self.fx.root))
        self.assertIn(".gitignore", diff)
        self.assertEqual(diff[".gitignore"], "changed")


if __name__ == "__main__":
    unittest.main()
