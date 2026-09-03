"""eval/tests/test_denial_gate.py —— deny 双分类与改道率（tasks 2.4 / oracle 拍板点 1）。"""
import unittest

from eval import ifmt
from eval.scoring import denial_gate as dg


def _settings(deny):
    return {"permissions": {"deny": list(deny)}}


MANAGED = ["@@cadence-managed:permission-gate:v1:start@@",
           "Bash(ls:*)", "Bash(find:*)", "Grep", "Glob",
           "@@cadence-managed:permission-gate:v1:end@@"]


def _traj(calls, denials, settings=None):
    traj = ifmt.IntermediateTrajectory(agent="claude")
    traj.tool_calls = [ifmt.ToolCall(index=i, tool=t, raw_tool=t,
                                     args_digest=d, is_error=False)
                       for i, (t, d) in enumerate(calls)]
    traj.denials = [ifmt.Denial(at_index=i, tool=t, reason="denied", raw={})
                    for i, t in denials]
    traj.settings_snapshot = settings if settings is not None else _settings(MANAGED)
    return traj


class TestDenialGate(unittest.TestCase):
    def test_managed_entries_extracted(self):
        """ut-dg-managed：受管区块内条目提取，区块外用户条目排除。"""
        deny = ["UserDeny"] + MANAGED
        entries = dg.managed_deny_entries(_settings(deny))
        self.assertIn("Grep", entries)
        self.assertIn("Bash(ls:*)", entries)
        self.assertNotIn("UserDeny", entries)
        self.assertNotIn(dg.GATE_BEGIN, entries)

    def test_missing_region_all_unmanaged(self):
        """ut-dg-noregion：区块缺失→空集→全部按区块外（保守判 FAIL）。"""
        traj = _traj([("Grep", "pattern=x")], [])
        traj.denials = [ifmt.Denial(at_index=0, tool="Grep", reason="denied", raw={})]
        traj.settings_snapshot = _settings(["UserDeny"])
        out = dg.classify_denials(traj, traj.settings_snapshot)
        self.assertEqual(len(out["unmanaged"]), 1)
        self.assertEqual(out["managed"], [])

    def test_classify_managed_vs_unmanaged(self):
        """ut-dg-classify：受管内 deny 不判 FAIL 转改道；区块外判 FAIL。"""
        traj = _traj(
            [("Grep", "pattern=x"), ("mcp__codegraph__codegraph_explore", "q"),
             ("Edit", "file_path=a.py")],
            [(0, "Grep"), (2, "Edit")])
        out = dg.classify_denials(traj, traj.settings_snapshot)
        self.assertEqual([d.tool for d in out["managed"]], ["Grep"])
        self.assertEqual([d.tool for d in out["unmanaged"]], ["Edit"])

    def test_reroute_within_window(self):
        """ut-dg-reroute：N 步内改用 preferred → rerouted。"""
        traj = _traj([("Grep", "pattern=x"),
                      ("mcp__codegraph__codegraph_explore", "q")],
                     [(0, "Grep")])
        out = dg.apply_deny_gate(traj, {"id": "P1"})
        self.assertEqual(out["rerouted"], 1)
        self.assertEqual(out["abandoned"], 0)

    def test_abandoned_beyond_window(self):
        """ut-dg-abandon：窗口内未改道 → abandoned（判 FAIL）。"""
        calls = [("Grep", "x")] + [("Read", f"file_path=f{i}") for i in range(10)]
        traj = _traj(calls, [(0, "Grep")])
        out = dg.apply_deny_gate(traj, {"id": "P1"})
        self.assertEqual(out["abandoned"], 1)

    def test_apply_gate_counts(self):
        """ut-dg-apply：managed/unmanaged/abandoned/rerouted 四计数（与实现语义对齐）。"""
        traj = _traj(
            [("Grep", "x"), ("mcp__codegraph__codegraph_explore", "q"),
             ("Edit", "file_path=a.py")],
            [(0, "Grep"), (2, "Edit")])
        out = dg.apply_deny_gate(traj, {"id": "P1"})
        # Grep 命中受管条目→managed=1 且窗口内 codegraph 改道→rerouted=1；
        # Edit 无受管条目命中→unmanaged=1；全部调用 is_error=False→silent_errors=0
        self.assertEqual((out["managed"], out["unmanaged"],
                          out["rerouted"], out["abandoned"]), (1, 1, 1, 0))
        self.assertEqual(out["silent_errors"], 0)

    def test_param_qualified_entry_matches_prefix(self):
        """ut-dg-param：Bash(grep:*) 条目按命令头前缀限定比对（grep 命中、ls 不命中）。"""
        settings = _settings(["@@cadence-managed:permission-gate:v1:start@@",
                              "Bash(grep:*)",
                              "@@cadence-managed:permission-gate:v1:end@@"])
        grep_traj = _traj([("Bash", "grep -rn orders src")], [(0, "Bash")])
        grep_traj.settings_snapshot = settings
        out = dg.classify_denials(grep_traj, settings)
        self.assertEqual(len(out["managed"]), 1)
        ls_traj = _traj([("Bash", "ls -R src")], [(0, "Bash")])
        ls_traj.settings_snapshot = settings
        out = dg.classify_denials(ls_traj, settings)
        self.assertEqual(len(out["unmanaged"]), 1)

    def test_silent_is_error_flagged(self):
        """ut-dg-silent：非受管位置的 is_error 计入 silent_errors（假绿防线）。"""
        traj = _traj([("Read", "file_path=x"), ("Read", "file_path=y")], [])
        traj.tool_calls[0].is_error = True
        out = dg.apply_deny_gate(traj, {"id": "P1"})
        self.assertEqual(out["silent_errors"], 1)


if __name__ == "__main__":
    unittest.main()
