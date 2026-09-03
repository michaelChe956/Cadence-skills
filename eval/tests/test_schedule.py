"""eval/tests/test_schedule.py —— 分夜轮转调度表（tasks 4.3 调度部分）。"""
import unittest

from eval.runner import schedule as sch

AGENTS = ["claude", "codex", "pi", "kimi"]


class TestSchedule(unittest.TestCase):
    def test_parity_probe_sets(self):
        """ut-sch-parity：夜序号奇→P1/P3/P5/P7，偶→P2/P4/P6/P8（SCHED_START=2026-09-07 周一起算）。"""
        # 2026-09-08 夜序号 1（奇）；2026-09-09 夜序号 2（偶）
        odd = sch.night_plan("2026-09-08", AGENTS)
        self.assertEqual(odd["probe_ids"], ["P1", "P3", "P5", "P7"])
        self.assertEqual(odd["parity"], "odd")
        self.assertEqual(odd["runs"], 2)
        even = sch.night_plan("2026-09-09", AGENTS)
        self.assertEqual(even["probe_ids"], ["P2", "P4", "P6", "P8"])
        self.assertEqual(even["parity"], "even")

    def test_control_rotation_covers_all(self):
        """ut-sch-control：对照组每夜 2 端轮换，4 夜（序号 0–3）覆盖全部端。"""
        seen = set()
        for day in range(7, 11):  # 2026-09-07..10：夜序号 0..3
            date_str = f"2026-09-{day:02d}"
            seen.update(sch.night_plan(date_str, AGENTS)["control_agents"])
        self.assertEqual(seen, set(AGENTS))

    def test_v3_weekly_strong_offset(self):
        """ut-sch-weekly：v3 每周（夜序号%7==0）2 端；strong 错峰（%7==3）每周。"""
        days = range(7, 18)  # 2026-09-07..17：夜序号 0..10，覆盖 v3 两夜/strong 两夜
        v3_nights = [d for d in days
                     if sch.night_plan(f"2026-09-{d:02d}", AGENTS)["v3_agents"]]
        self.assertEqual(v3_nights, [7, 14])    # 夜序号 0 与 7
        strong_nights = [d for d in days
                         if sch.night_plan(f"2026-09-{d:02d}", AGENTS)["strong_agents"]]
        self.assertEqual(strong_nights, [10, 17])  # 夜序号 3/10（与 v3 错峰）

    def test_theme_rotation(self):
        """ut-sch-theme：题库 theme 三夜轮换（夜序号 0/1/2 → orders/billing/users）。"""
        themes = [sch.night_plan(f"2026-09-{d:02d}", AGENTS)["theme"]
                  for d in range(7, 10)]
        self.assertEqual(sorted(themes), ["billing", "orders", "users"])


if __name__ == "__main__":
    unittest.main()
