"""eval/tests/test_probes.py —— 8 探针定义与题库轮换（tasks 3.1/3.2）。"""
import unittest

from eval.probes import definitions as prb


class TestProbes(unittest.TestCase):
    def test_eight_probes_declared(self):
        """ut-prb-eight：P 组 8 探针齐备；R 组 2 探针另册（docker 通道规则体系探针）。"""
        self.assertEqual(sorted(prb.PROBES), ["P1", "P2", "P3", "P4",
                                              "P5", "P6", "P7", "P8",
                                              "R1", "R2"])

    def test_every_probe_binds_clauses(self):
        """ut-prb-clauses：每探针绑定条款 ID；cadence-tools 条款与 p1 元数据同源命名。"""
        for pid, probe in prb.PROBES.items():
            self.assertTrue(probe["rule_clause_ids"], pid)
        self.assertIn("code-reading-coding.md#cadence-tools[0]",
                      prb.PROBES["P1"]["rule_clause_ids"])
        self.assertIn("mcp-servers.md#cadence-tools[0]",
                      prb.PROBES["P2"]["rule_clause_ids"])

    def test_p1_targets_roaming(self):
        """ut-prb-p1-roam：P1 断言含 no_roam（ls/find 漫游检测）与 preferred 检索。"""
        kinds = [a["kind"] for a in prb.PROBES["P1"]["assertions"]]
        self.assertIn("no_roam", kinds)
        self.assertIn("tool_used", kinds)
        preferred = next(a for a in prb.PROBES["P1"]["assertions"]
                         if a["kind"] == "tool_used")["pattern"]
        self.assertIn("codegraph", preferred)

    def test_p3_expected_red_pre_gate(self):
        """ut-prb-p3-red：时序探针标记门禁上线前预期红（版本对比常设标尺）。"""
        self.assertTrue(prb.PROBES["P3"]["expected_red_pre_gate"])
        kinds = [a["kind"] for a in prb.PROBES["P3"]["assertions"]]
        self.assertIn("plan_before_edit", kinds)

    def test_mcp_probes_declare_fake_roles(self):
        """ut-prb-mcp：P2/P6/P7 声明 fake MCP 角色。"""
        self.assertEqual(prb.PROBES["P2"]["needs_fake_mcp"], ["context7"])
        self.assertEqual(prb.PROBES["P6"]["needs_fake_mcp"], ["time"])
        self.assertEqual(prb.PROBES["P7"]["needs_fake_mcp"], ["image"])

    def test_prompt_variants_rotation(self):
        """ut-prb-variants：P 组每探针 ≥2 题库变体；夜间轮换确定性且覆盖全部变体。

        R 组本期单变体（首变体内联，变体轮换不属本期），不适用轮换要求。
        """
        for pid in prb.PROBES:
            if pid in prb.R_GROUP:
                continue
            self.assertGreaterEqual(len(prb.PROBES[pid]["prompt_variants"]), 2, pid)
        seen = {prb.variant_for_night("P1", n) for n in range(4)}
        self.assertEqual(seen, {0, 1})

    def test_env_injection_only_path(self):
        """ut-prb-env：prompt 经 env 注入；特殊字符原样保持（注入安全场景）。"""
        probe = prb.PROBES["P4"]
        original = probe["prompt_variants"][0]
        probe["prompt_variants"][0] = '含"引号"与 $HOME 与 `id`'
        try:
            env = prb.probe_env("P4", 0)
        finally:
            probe["prompt_variants"][0] = original
        self.assertEqual(env["EVAL_PROBE_ID"], "P4")
        self.assertIn("`id`", env["EVAL_PROMPT"])
        self.assertIn("$HOME", env["EVAL_PROMPT"])

    def test_control_probes(self):
        """ut-prb-control：对照组探针=规则相关四项。"""
        self.assertEqual(prb.CONTROL_PROBES, ("P1", "P3", "P4", "P5"))


if __name__ == "__main__":
    unittest.main()
