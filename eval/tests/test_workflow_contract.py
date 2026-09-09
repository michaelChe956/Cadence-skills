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

    def test_tier1_docker_selfhosted(self):
        """ut-wf-tier1：self-hosted 路由 + Docker 四端夜测 + PR 触发 + 并发执行。"""
        doc = self._load()
        tier1 = doc["jobs"]["eval-tier1-docker"]
        self.assertEqual(tier1["runs-on"], ["self-hosted", "cadence-eval"])
        cond = tier1["if"]
        self.assertIn("pull_request", cond)  # PR 触发（用户决策 B 方案）
        self.assertIn("workflow_dispatch", cond)  # 手动触发保留
        script = "\n".join(str(s.get("run", "")) for s in tier1["steps"])
        self.assertIn("eval/docker/night.py", script)  # Docker 夜测入口
        self.assertIn("report_matrix.py", script)      # 透视汇总
        self.assertIn("declare -A pids", script)       # 四端并发
        # 端命令零直调：夜测全部经容器（Tier-1 不在宿主裸跑 CLI）
        for banned in ("claude -p", "codex exec", "kimi -p", "pi -p"):
            self.assertNotIn(banned, script)

    def test_tier1_teardown_and_artifacts(self):
        """ut-wf-tier1-artifacts：结果 artifact 上传 + 失败仍出透视（if: always）。"""
        doc = self._load()
        tier1 = doc["jobs"]["eval-tier1-docker"]
        names = [s.get("name", "") for s in tier1["steps"]]
        self.assertTrue(any("上传" in n for n in names))
        summary = next(s for s in tier1["steps"] if "透视" in s.get("name", ""))
        self.assertEqual(summary.get("if"), "always()")

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
