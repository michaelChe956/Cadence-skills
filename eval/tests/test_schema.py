"""eval/tests/test_schema.py —— 结果 JSON 版本化最小契约（tasks 2.6 / oracle §2-e）。"""
import json
import tempfile
import unittest
from pathlib import Path

from eval.scoring import schema


class TestSchema(unittest.TestCase):
    def test_build_result_stable_keys(self):
        """ut-schema-keys：稳定键齐备 + 顶层 schema_version。"""
        doc = schema.build_result(run_id="r1", agent="claude", probe_id="P1",
                                  verdict="PASS")
        self.assertEqual(doc["schema_version"], "1.0")
        missing = [k for k in schema.STABLE_KEYS if k not in doc]
        self.assertEqual(missing, [])
        self.assertEqual(doc["model"], "")
        self.assertEqual(doc["rule_clause_ids"], [])

    def test_validate_result(self):
        """ut-schema-validate：缺稳定键被点名；details 自由字段不报警。"""
        doc = schema.build_result(run_id="r1", agent="claude", probe_id="P1",
                                  verdict="PASS")
        doc.pop("verdict")
        doc["details"] = {"any_extra": [1, 2, 3]}
        problems = schema.validate_result(doc)
        self.assertIn("verdict", problems)

    def test_validate_result_reports_type_mismatch(self):
        """ut-schema-type：稳定键类型错误被点名；MODEL_DRIFT 枚举合法。"""
        doc = schema.build_result(run_id="r1", agent="claude", probe_id="P1",
                                  verdict="MODEL_DRIFT")
        doc["duration_s"] = "not-a-duration"
        problems = schema.validate_result(doc)
        self.assertIn("duration_s", problems)
        doc["duration_s"] = 1.5
        self.assertEqual(schema.validate_result(doc), [])

    def test_baseline_same_major_participates(self):
        """ut-schema-same-major：主版本一致的基线参与 diff（含次版本差异）。"""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "baseline.json"
            path.write_text(json.dumps({"schema_version": "1.1", "probe_agent": {}}),
                            encoding="utf-8")
            doc, reason = schema.load_baseline(path)
        self.assertIsNotNone(doc)
        self.assertIsNone(reason)

    def test_baseline_major_mismatch_rejected(self):
        """ut-schema-major：主版本不匹配不参与 diff 且报告显式标注。"""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "baseline.json"
            path.write_text(json.dumps({"schema_version": "2.0", "probe_agent": {}}),
                            encoding="utf-8")
            doc, reason = schema.load_baseline(path)
        self.assertIsNone(doc)
        self.assertIn("基线 schema 不兼容", reason)
        self.assertIn("2.0", reason)


if __name__ == "__main__":
    unittest.main()
