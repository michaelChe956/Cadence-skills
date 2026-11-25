"""eval/tests/test_workflow_events.py —— 原生工作流证据采集（专项修复 P3）。

回放 eval/transcripts/workflow/ 下的真实格式 fixture，断言
trajectory.workflow_events 与 expected 完全一致（含事件次序）。
"""
import json
import tempfile
import unittest
from pathlib import Path

from eval import ifmt
from eval.adapters import get_adapter

FIX = Path(__file__).resolve().parents[1] / "transcripts" / "workflow"

CASES = [
    # (agent, 样本名)
    ("claude", "pos-claude"),
    ("claude", "neg-selfreport"),
    ("claude", "neg-rework"),
    ("claude", "neg-gaps"),
    ("claude", "neg-narration"),
    ("codex", "codex-rollout"),
    ("pi", "pi-omp"),
    ("pi", "pi-jsonmode"),
    ("kimi", "kimi-wire"),
    ("kimi", "kimi-compat"),
    ("kimi", "kimi-openai"),
]


def _expected(name: str) -> list:
    return json.loads((FIX / f"{name}.expected.json").read_text(encoding="utf-8"))


class TestWorkflowEvents(unittest.TestCase):
    """四端 parse_file 回放：事件种类、次序、真伪口径。"""

    def _events(self, agent: str, name: str) -> list:
        traj = get_adapter(agent).parse_file(FIX / f"{name}.jsonl")
        self.assertTrue(traj.source_path.endswith(f"{name}.jsonl"))
        return traj.workflow_events

    def test_pos_claude(self):
        """ut-wfe-pos：正例=真写入+独立复审通过+ask 工具提问，result 回显不重复计。"""
        events = self._events("claude", "pos-claude")
        self.assertEqual(events, _expected("pos-claude"))

    def test_neg_selfreport(self):
        """ut-wfe-selfreport：代理自述“已通过/已询问”不产 review/ask 事件。"""
        events = self._events("claude", "neg-selfreport")
        self.assertEqual(events, _expected("neg-selfreport"))
        self.assertFalse(any(e["kind"] in ("review", "ask") for e in events))

    def test_neg_rework(self):
        """ut-wfe-rework：首问后继续动工按次序留痕，复审 FAIL 为 passed=False。"""
        events = self._events("claude", "neg-rework")
        self.assertEqual(events, _expected("neg-rework"))
        kinds = [e["kind"] for e in events]
        self.assertEqual(kinds.index("ask"), 1)
        self.assertGreater(kinds.index("write", 2), kinds.index("ask"))

    def test_neg_gaps(self):
        """ut-wfe-gaps：写入缺路径/复审无回执均落 unknown 安全标识。"""
        self.assertEqual(self._events("claude", "neg-gaps"), _expected("neg-gaps"))

    def test_neg_narration(self):
        """ut-wfe-narration：“已询问用户”式终局自述不落 ask。"""
        events = self._events("claude", "neg-narration")
        self.assertEqual(events, _expected("neg-narration"))
        self.assertFalse(any(e["kind"] == "ask" for e in events))

    def test_codex_rollout(self):
        """ut-wfe-codex：apply_patch 写入+明文未通过；无确认措辞的尾部提问不算。"""
        self.assertEqual(self._events("codex", "codex-rollout"),
                         _expected("codex-rollout"))

    def test_pi_omp(self):
        """ut-wfe-pi：omp 自然消息 write/task+顺序 toolResult 配对，PASS 判通过。"""
        self.assertEqual(self._events("pi", "pi-omp"), _expected("pi-omp"))

    def test_pi_jsonmode(self):
        """ut-wfe-pi-json：--mode json 的 message_start/update 不重复计入。"""
        self.assertEqual(self._events("pi", "pi-jsonmode"),
                         _expected("pi-jsonmode"))

    def test_kimi_wire(self):
        """ut-wfe-kimi：wire tool.call/tool.result 配对，中文明文结论判通过。"""
        self.assertEqual(self._events("kimi", "kimi-wire"), _expected("kimi-wire"))

    def test_kimi_compat(self):
        """ut-wfe-kimi-compat：Claude-compatible 流同构提取，含等待态终局提问。"""
        self.assertEqual(self._events("kimi", "kimi-compat"),
                         _expected("kimi-compat"))

    def test_kimi_openai(self):
        """ut-wfe-kimi-openai：openai 分片聚合提取；残缺参数安全标 unknown。"""
        self.assertEqual(self._events("kimi", "kimi-openai"),
                         _expected("kimi-openai"))

    def test_p3_wait(self):
        """ut-wfe-p3-wait：等待态正例——CJK 路径、双 reviewer 通过、终局确认提问。"""
        events = self._events("claude", "p3-wait")
        self.assertEqual(events, _expected("p3-wait"))
        self.assertEqual([e["kind"] for e in events],
                         ["write", "review", "review", "ask"])

    def test_p3_empty(self):
        """ut-wfe-p3-empty：content 键存在且为空串≠键缺失（写空 Design 证据）。"""
        events = self._events("claude", "p3-empty")
        self.assertEqual(events, _expected("p3-empty"))
        self.assertIn("content", events[0])
        self.assertEqual(events[0]["content"], "")

    def test_p3_retracted(self):
        """ut-wfe-p3-retracted：先行实现写入及后续撤回均留痕，主流程完整。"""
        self.assertEqual(self._events("claude", "p3-retracted"),
                         _expected("p3-retracted"))

    def test_p3_early_plan(self):
        """ut-wfe-p3-early-plan：无 ask/review 的纯写入轨迹按次序留痕。"""
        self.assertEqual(self._events("claude", "p3-early-plan"),
                         _expected("p3-early-plan"))

    def test_p3_missing(self):
        """ut-wfe-p3-missing：自述“已完成两项审查”不构成 review 证据。"""
        events = self._events("claude", "p3-missing")
        self.assertEqual(events, _expected("p3-missing"))
        self.assertFalse(any(e["kind"] == "review" for e in events))

    def test_ifmt_roundtrip(self):
        """ut-wfe-ifmt：workflow_events 随中间格式序列化/反序列化保真。"""
        traj = get_adapter("claude").parse_file(FIX / "p3-wait.jsonl")
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "traj.json"
            ifmt.dump(traj, path)
            back = ifmt.load(path)
        self.assertEqual(back.workflow_events, traj.workflow_events)
        doc = traj.to_dict()
        self.assertIsInstance(doc["workflow_events"], list)
        self.assertTrue(all(isinstance(e, dict) for e in doc["workflow_events"]))


if __name__ == "__main__":
    unittest.main()
