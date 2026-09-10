"""eval/tests/test_r_group.py —— R 组探针定义(R1/R2)离线单测。
(R3/agents_only/rollout 审计已按 2026-09-10 用户裁决移除。)"""
import json
import unittest
from pathlib import Path
from unittest import mock

from eval.docker import night, session
from eval.probes import definitions as prb


class TestRGroupDefinitions(unittest.TestCase):
    """R 组三探针:定义 schema 与端限定字段。"""

    def test_r_group_constant_and_keys(self):
        """ut-rgrp-keys:R_GROUP=("R1","R2","R3") 且三键均在 PROBES。"""
        self.assertEqual(prb.R_GROUP, ("R1", "R2"))
        for pid in prb.R_GROUP:
            self.assertIn(pid, prb.PROBES)
            self.assertEqual(prb.PROBES[pid]["id"], pid)

    def test_r_group_assertion_kinds_legal(self):
        """ut-rgrp-kinds:R 组断言 kind 全部落在 docker 评分器接线的文本断言集。"""
        legal = {"text_contains", "text_lacks"}
        for pid in prb.R_GROUP:
            for a in prb.PROBES[pid]["assertions"]:
                self.assertIn(a["kind"], legal, pid)
                self.assertIn("pattern", a)

    def test_r1_definition(self):
        """ut-rgrp-r1:R1 断言 language/code-usage 双锚,绑定 entry.mandatory-rules。"""
        r1 = prb.PROBES["R1"]
        self.assertEqual(r1["rule_clause_ids"], ["entry.mandatory-rules"])
        self.assertEqual([a["pattern"] for a in r1["assertions"]],
                         ["language", "code-usage"])
        self.assertEqual(r1["needs_fake_mcp"], [])
        self.assertFalse(r1["expected_red_pre_gate"])

    def test_r2_definition(self):
        """ut-rgrp-r2:R2 断言规则正文首标题,绑定 progressive-rules.body-on-demand。"""
        r2 = prb.PROBES["R2"]
        self.assertEqual(r2["rule_clause_ids"], ["progressive-rules.body-on-demand"])
        self.assertEqual([a["pattern"] for a in r2["assertions"]],
                         ["Markdown 格式规则"])
        self.assertEqual(r2["needs_fake_mcp"], [])

    def test_r_group_single_variant_inline(self):
        """ut-rgrp-variant:R 组 prompt_variants 单条(首变体内联,变体轮换不属本期)。"""
        for pid in prb.R_GROUP:
            self.assertEqual(len(prb.PROBES[pid]["prompt_variants"]), 1, pid)

    def test_r_group_prompts_adopted(self):
        """ut-rgrp-prompt:R 组 prompt 逐字采用任务卡文案(关键片段锚定)。"""
        self.assertIn("禁止调用任何工具", prb.PROBES["R1"]["prompt_variants"][0])
        self.assertIn("「语言规则」和「代码使用规则」",
                      prb.PROBES["R1"]["prompt_variants"][0])
        self.assertIn("rule://markdown-format",
                      prb.PROBES["R2"]["prompt_variants"][0])
        self.assertIn("第一个标题行", prb.PROBES["R2"]["prompt_variants"][0])






