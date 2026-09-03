"""eval/tests/test_workflow_contract.py —— Tier-0/1 workflow 契约（tasks 4.2/4.3）。"""
import unittest
from pathlib import Path

WF = Path(".github/workflows/eval.yml")


class TestWorkflowContract(unittest.TestCase):
    def test_tier0_zero_real_cli(self):
        """ut-wf-tier0：Tier-0 步骤只有 python 单测/冒烟/离线重跑，无端调用。"""
        doc = self._load()
        steps = doc["jobs"]["eval-tier0"]["steps"]
        script = "\n".join(str(s.get("run", "")) for s in steps)
        for banned in ("claude -p", "codex exec", "kimi -p", "pi -p"):
            self.assertNotIn(banned, script)
        self.assertIn("unittest discover", script)
        self.assertIn("rerun", script)

    def test_tier1_selfhosted_and_probe(self):
        """ut-wf-tier1：self-hosted 标签路由 + 云端探活条件触发 + mock 自检前置 + 手动触发。"""
        doc = self._load()
        tier1 = doc["jobs"]["eval-tier1-nightly"]
        self.assertEqual(tier1["runs-on"], ["self-hosted", "cadence-eval"])
        self.assertEqual(tier1["needs"], "runner-probe")
        self.assertIn("needs.runner-probe.outputs.available == 'true'",
                      tier1["if"])
        self.assertIn("workflow_dispatch", tier1["if"])  # 手动触发允许（s7）
        self.assertEqual(tier1["env"]["EVAL_BASE"], "$HOME/eval-runs")
        first_run = next(s["run"] for s in tier1["steps"] if "run" in s)
        self.assertIn("smoke", first_run)
        self.assertIn("night --date", "\n".join(str(s.get("run", ""))
                                                for s in tier1["steps"]))
        self.assertIn("TZ=Asia/Shanghai", "\n".join(str(s.get("run", ""))
                                                    for s in tier1["steps"]))
        self.assertIn(
            'any(l.get("name") == "cadence-eval" for l in r.get("labels", []))',
            WF.read_text(encoding="utf-8"),
        )

    def test_ci_yml_untouched(self):
        """ut-wf-noci：既有 ci.yml 车道零改动（R9；Tier-0 是新增 workflow 文件）。"""
        text = Path(".github/workflows/ci.yml").read_text(encoding="utf-8")
        self.assertNotIn("eval", text)

    def _load(self):
        try:
            import yaml
        except ImportError:
            self.skipTest("本地无 PyYAML；CI 车道内执行本契约")
        return yaml.safe_load(WF.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
