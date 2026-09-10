"""eval/tests/test_night_score.py —— Docker 夜测文本评分接线（无断言分支不再假绿）。"""
import json
import os
import re
import shutil
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

from eval.docker import night
from eval.install import assertions as asrt
from eval.probes import definitions as prb


def _probe_result(final_text, rc=0, **extra):
    """最小 probe_result dict（对齐 run_probe 落盘字段 + _score_probe_text 读取键）。"""
    r = {"final_text": final_text, "stdout": final_text, "returncode": rc,
         "duration_s": 1.0}
    r.update(extra)
    return r


# R1 风格探针定义（rules-progressive-load）：两条 text_contains 锚点断言
R1_STYLE = {
    "id": "R1", "name": "规则渐进加载",
    "rule_clause_ids": ["rules/load.md#probe[0]"],
    "prompt_variants": ["说明规则加载流程", "描述 cadence-rules 如何生效"],
    "assertions": [
        {"kind": "text_contains", "pattern": "cadence-rules"},
        {"kind": "text_contains", "pattern": "加载顺序"},
    ],
    "needs_fake_mcp": [], "expected_red_pre_gate": False,
}


class TestScoreProbeText(unittest.TestCase):
    def test_r1_missing_anchors_fail(self):
        """ut-night-r1-fail：text_contains 锚点缺失 → FAIL（消除无条件 PASS 假绿）。"""
        with mock.patch.dict(prb.PROBES, {"R1": R1_STYLE}):
            score = night._score_probe_text(
                "codex", "R1", _probe_result("我完成了任务，一切正常。"))
        self.assertEqual(score["verdict"], "FAIL")
        self.assertEqual(score["behavior"], "FAIL")
        self.assertIn("cadence-rules", score["behavior_failures"])
        self.assertIn("加载顺序", score["behavior_failures"])

    def test_r1_anchors_present_pass(self):
        """ut-night-r1-pass：锚点齐全 → PASS（断言全满足维持原判定）。"""
        with mock.patch.dict(prb.PROBES, {"R1": R1_STYLE}):
            score = night._score_probe_text(
                "codex", "R1",
                _probe_result("已按 cadence-rules 的加载顺序 读取规则并执行。"))
        self.assertEqual(score["verdict"], "PASS")
        self.assertEqual(score["behavior"], "PASS")

    def test_text_lacks_forbidden_content(self):
        """ut-night-tlacks：text_lacks 命中禁止串 → FAIL；未命中 → PASS。"""
        spec = dict(R1_STYLE, assertions=[{"kind": "text_lacks", "pattern": "TODO"}])
        with mock.patch.dict(prb.PROBES, {"R1": spec}):
            hit = night._score_probe_text("codex", "R1", _probe_result("TODO: 后续再补"))
            miss = night._score_probe_text("codex", "R1", _probe_result("结论完整，无遗留。"))
        self.assertEqual(hit["behavior"], "FAIL")
        self.assertIn("TODO", hit["behavior_failures"])
        self.assertEqual(miss["behavior"], "PASS")

    def test_p1_keyword_branch_unchanged_pass(self):
        """ut-night-p1-parity：P 组对拍——P1 输出含调用链关键词仍按旧分支 PASS。"""
        score = night._score_probe_text(
            "codex", "P1", _probe_result("我分析了 users 模块的调用链与入口。"))
        self.assertEqual(score["verdict"], "PASS")
        self.assertEqual(score["behavior"], "PASS")

    def test_p1_missing_keyword_still_fails(self):
        """ut-night-p1-red：P1 输出无关键词 → 仍 FAIL（P 组语义零变化）。"""
        score = night._score_probe_text("codex", "P1", _probe_result("做完了。"))
        self.assertEqual(score["verdict"], "FAIL")
        self.assertEqual(score["behavior"], "FAIL")

    def test_rc_nonzero_infra_fail_first(self):
        """ut-night-infra：rc≠0 → INFRA_FAIL 优先（断言接线不改变 infra 路径）。"""
        with mock.patch.dict(prb.PROBES, {"R1": R1_STYLE}):
            score = night._score_probe_text(
                "codex", "R1", _probe_result("", rc=1))
        self.assertEqual(score["verdict"], "INFRA_FAIL")


class _FakeContainer:
    """容器 mock：exec 探路径存在性；copy_out 从本地伪项目拷贝（保软链，模拟 podman cp）。"""

    def __init__(self, project: Path):
        self.project = project

    def exec(self, cmd, cwd="/home/tester", env=None, timeout=300):
        m = re.search(r"test -e (\S+)", cmd)
        rel = m.group(1).removeprefix("/home/tester/project/")
        hit = (self.project / rel).exists()
        return {"rc": 0, "stdout": "Y\n" if hit else "N\n", "stderr": ""}

    def copy_out(self, src, dst):
        rel = src.removeprefix("/home/tester/project/")
        source = self.project / rel
        if source.is_dir():
            shutil.copytree(source, dst, symlinks=True)
        else:
            shutil.copy2(source, dst)


def _fake_container_project(project: Path) -> None:
    """构造容器内 /home/tester/project 的四类断言资产（全好形态）。"""
    rules = project / ".claude" / "rules"
    rules.mkdir(parents=True)
    for name in ("language.md", "code-usage.md"):
        (rules / name).write_text("---\ndescription: 规则\n---\n\n正文\n", encoding="utf-8")
    bridge = project / ".agents" / "rules"
    bridge.mkdir(parents=True)
    for name in ("language.md", "code-usage.md"):
        os.symlink(f"../../.claude/rules/{name}", bridge / name)
    (project / ".omp").mkdir()
    (project / ".omp" / "AGENTS.md").write_text(asrt.OMP_AGENTS_MD_BODY, encoding="utf-8")
    (project / "AGENTS.md").write_text("简短上下文\n", encoding="utf-8")


class TestStage1AssertionRecord(unittest.TestCase):
    """_write_stage1_assertions：拷回容器资产 → 四条断言 → stage1 记录落盘（mock 容器）。"""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        patcher = mock.patch.object(night, "RESULT_ROOT", self.base / "results")
        patcher.start()
        self.addCleanup(patcher.stop)

    def _runs_dir(self):
        return self.base / "results" / "reports" / "nightly" / time.strftime("%Y-%m-%d") / "runs"

    def test_stage1_record_pass(self):
        """ut-night-s1-pass：资产全好 → probe_id=stage1 记录 PASS，四条断言逐条入 details。"""
        project = self.base / "project"
        _fake_container_project(project)
        path = night._write_stage1_assertions(_FakeContainer(project), "claude", "s1")
        doc = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(path, self._runs_dir() / "docker-claude-s1-stage1.json")
        self.assertEqual(doc["schema_version"], "1.0")
        self.assertEqual(doc["run_id"], "docker-claude-s1-stage1")
        self.assertEqual(doc["probe_id"], "stage1")
        self.assertEqual(doc["verdict"], "PASS")
        self.assertEqual(doc["fail_reason"], "")
        self.assertEqual([a["name"] for a in doc["details"]["assertions"]],
                         list(night.STAGE1_ASSERTION_NAMES))
        self.assertTrue(all(a["ok"] for a in doc["details"]["assertions"]))

    def test_stage1_record_fail_on_missing_symlink(self):
        """ut-night-s1-fail：软链缺失 → verdict=FAIL，fail_reason 指明 omp.symlinks。"""
        project = self.base / "project"
        _fake_container_project(project)
        (project / ".agents" / "rules" / "language.md").unlink()
        path = night._write_stage1_assertions(_FakeContainer(project), "omp", "s2")
        doc = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(doc["verdict"], "FAIL")
        self.assertIn("omp.symlinks", doc["fail_reason"])

    def test_stage1_record_fail_when_assets_absent(self):
        """ut-night-s1-absent：容器资产全缺 → 缺失路径不拷不炸，记录照写并 FAIL。"""
        project = self.base / "empty"
        project.mkdir()
        path = night._write_stage1_assertions(_FakeContainer(project), "omp", "s3")
        doc = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(doc["verdict"], "FAIL")
        by_name = {a["name"]: a for a in doc["details"]["assertions"]}
        self.assertFalse(by_name["omp.agents-md"]["ok"])

    def test_stage1_record_survives_copy_error(self):
        """ut-night-s1-copyerr：copy_out 崩溃不外抛 → FAIL 记录留痕（不阻塞探针）。"""
        project = self.base / "project"
        _fake_container_project(project)
        c = _FakeContainer(project)
        with mock.patch.object(c, "copy_out", side_effect=RuntimeError("podman 炸了")):
            path = night._write_stage1_assertions(c, "claude", "s4")
        doc = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(doc["verdict"], "FAIL")
        self.assertIn("stage1-assert-error", doc["fail_reason"])


if __name__ == "__main__":
    unittest.main()
