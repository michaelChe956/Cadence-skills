"""eval/tests/test_assertor.py —— 确定性断言器（tasks 2.4 核心）。"""
import unittest
from pathlib import Path

from eval import ifmt
from eval.scoring import assertor as asr


def _traj(calls, denials=None, final_text="中文结论：完成", writes=None):
    traj = ifmt.IntermediateTrajectory(agent="claude")
    traj.model_readback = "glm-5.3"
    traj.tool_calls = [
        ifmt.ToolCall(index=i, tool=t, raw_tool=t, args_digest=d, is_error=False)
        for i, (t, d) in enumerate(calls)]
    traj.denials = denials or []
    traj.writes = [ifmt.WriteEvent(at_index=i, path=p)
                   for i, p in enumerate(writes or [])]
    traj.final_text = final_text
    traj.settings_snapshot = {"permissions": {"deny": [
        "@@cadence-managed:permission-gate:v1:start@@",
        "Bash(ls:*)", "@@cadence-managed:permission-gate:v1:end@@"]}}
    return traj


P1 = {"id": "P1", "name": "检索", "rule_clause_ids": ["code-reading-coding.md#cadence-tools[0]"],
      "assertions": [
          {"kind": "tool_used", "pattern": "codegraph|ast-grep"},
          {"kind": "tool_absent", "pattern": "^Grep$"},
          {"kind": "no_roam", "max_ls_find": 5, "preferred": "codegraph"}]}


class TestPrimitives(unittest.TestCase):
    def test_tool_used_on_events_not_prose(self):
        """ut-asr-prose：朗读规则原文不算使用（排除规则原文防线）。"""
        traj = _traj([("Grep", "pattern=orders")],
                     final_text="规则要求优先使用 codegraph 与 ast-grep，我已阅读")
        self.assertFalse(asr.tool_used(traj, "codegraph"))
        self.assertTrue(asr.tool_used(traj, "^Grep$"))

    def test_roam_detect_ls_find(self):
        """ut-asr-roam：ls/find 漫游命中（真实违规形态靶子）。"""
        roam = _traj([("Bash", "ls -R src"), ("Bash", "ls src/orders"),
                      ("Bash", "find . -name x"), ("Bash", "find src -type f"),
                      ("Bash", "ls ."), ("Bash", "find . -maxdepth 1"),
                      ("Read", "file_path=src/orders/entry.py")])
        self.assertTrue(asr.roam_detect(roam, max_count=5, preferred_pattern="codegraph"))
        ok = _traj([("mcp__codegraph__codegraph_explore", "query=orders")])
        self.assertFalse(asr.roam_detect(ok, max_count=5, preferred_pattern="codegraph"))

    def test_zh_ratio(self):
        """ut-asr-zh：中文占比口径。"""
        self.assertGreaterEqual(asr.zh_ratio("这是中文结论 done"), 0.6)
        self.assertLess(asr.zh_ratio("english only text"), 0.6)

    def test_classify_infra(self):
        """ut-asr-infra：基础设施失败归因分类。"""
        self.assertEqual(asr.classify_infra(0, "", traj_present=False),
                         "infra-fail:transcript-missing")
        self.assertEqual(asr.classify_infra(1, "login required / auth expired",
                                           traj_present=True), "infra-fail:login")
        self.assertEqual(asr.classify_infra(0, "", traj_present=True, timed_out=True),
                         "infra-fail:timeout")
        self.assertIsNone(asr.classify_infra(0, "", traj_present=True))

    def test_classify_infra_upstream_api_error_not_transcript_missing(self):
        """ut-asr-infra-api：会话里的上游报错不能归因 transcript-missing。

        r5 夜测中 pi 真会话只有 503 No available accounts；轨迹确实拿到了，
        只是上游拒给 token——归因 transcript-missing 会把配额问题误指为 harness 缺陷。
        """
        self.assertEqual(
            asr.classify_infra(0, "", traj_present=False,
                               infra_errors=['503 {"message":"No available accounts"}']),
            "infra-fail:api-error")
        self.assertEqual(
            asr.classify_infra(0, "", traj_present=False,
                               infra_errors=["401 invalid credential"]),
            "infra-fail:login")
        self.assertEqual(
            asr.classify_infra(0, "", traj_present=False,
                               infra_errors=["429 usage limit reached"]),
            "infra-fail:quota")
        # 无上游报错证据时仍归 transcript-missing（harness 真没拿到轨迹）
        self.assertEqual(asr.classify_infra(0, "", traj_present=False, infra_errors=[]),
                         "infra-fail:transcript-missing")

    def test_score_run_uses_traj_infra_errors(self):
        """ut-asr-infra-api-wired：score_run 必须把轨迹的 infra_errors 接入归因。"""
        traj = ifmt.IntermediateTrajectory(agent="pi")
        traj.infra_errors = ['503 {"message":"No available accounts"}']
        result = asr.score_run("r-api", P1, traj)
        self.assertEqual(result["verdict"], "INFRA_FAIL")
        self.assertEqual(result["fail_reason"], "infra-fail:api-error")


class TestScoreRun(unittest.TestCase):
    def test_pass(self):
        """ut-asr-pass：preferred 工具 + 无裸 grep + 无漫游 → PASS。"""
        traj = _traj([("mcp__codegraph__codegraph_explore", "query=orders")])
        result = asr.score_run("r1", P1, traj)
        self.assertEqual(result["verdict"], "PASS")
        self.assertEqual(result["fail_reason"], "")

    def test_fail_roam(self):
        """ut-asr-fail-roam：漫游替代检索 → FAIL 且 fail_reason 具名。"""
        traj = _traj([("Bash", "ls -R src"), ("Bash", "find . -name x"),
                      ("Bash", "ls a"), ("Bash", "ls b"), ("Bash", "ls c"),
                      ("Bash", "ls d"), ("Bash", "ls e")])
        result = asr.score_run("r2", P1, traj)
        self.assertEqual(result["verdict"], "FAIL")
        self.assertIn("no_roam", result["fail_reason"])

    def test_infra_fail_verdict(self):
        """ut-asr-infra-verdict：infra 失败判 INFRA_FAIL（不入矩阵）。"""
        traj = _traj([])
        result = asr.score_run("r3", P1, traj, returncode=1,
                               stderr="claude: auth expired")
        self.assertEqual(result["verdict"], "INFRA_FAIL")
        self.assertIn("infra-fail", result["fail_reason"])

    def test_managed_deny_reroute_pass(self):
        """ut-asr-deny-reroute：受管 deny→N 步内改道 preferred → PASS+改道计数。"""
        traj = _traj(
            [("Bash", "ls -R src"),
             ("mcp__codegraph__codegraph_explore", "query=orders")],
            denials=[ifmt.Denial(at_index=0, tool="Bash",
                                 reason="permission denied", raw={})])
        result = asr.score_run("r4", P1, traj)
        self.assertEqual(result["verdict"], "PASS")
        self.assertEqual(result["details"]["deny_gate"]["rerouted"], 1)

    def test_unmanaged_deny_fail(self):
        """ut-asr-deny-unmanaged：区块外 deny → FAIL 且归类 harness 配置错误。"""
        traj = _traj([("Edit", "file_path=src/a.py"), ("Read", "file_path=src/b.py")],
                     denials=[ifmt.Denial(at_index=0, tool="Edit",
                                          reason="permission denied", raw={})])
        result = asr.score_run("r5", P1, traj)
        self.assertEqual(result["verdict"], "FAIL")
        self.assertEqual(result["details"]["deny_gate"]["unmanaged"], 1)
        self.assertIn("harness", result["fail_reason"])

    def test_is_error_outside_managed_fail(self):
        """ut-asr-iserror：区块外工具 is_error → FAIL（防静默失败假绿）。"""
        traj = _traj([("Read", "file_path=x"), ("Read", "file_path=y")])
        traj.tool_calls[0].is_error = True
        result = asr.score_run("r6", P1, traj)
        self.assertEqual(result["verdict"], "FAIL")


if __name__ == "__main__":
    unittest.main()
