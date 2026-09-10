"""eval/tests/test_resident_audit.py —— claude 端常载审计走确定性通道(Change B Task 3)。

三块:
1. _audit_resident_rules 纯函数——session_start 常载清单 vs 允许集(离线可测);
2. create_test_project 端限定注入 InstructionsLoaded hook(仅 claude,mock 容器);
3. run_docker_night stage1 后截断 + 探针后审计接线(时序与汇总字段)。
"""
import json
import unittest
from pathlib import Path
from unittest import mock

from eval.docker import night, session


def _line(path, reason="session_start"):
    """构造一条 InstructionsLoaded hook 事件行。"""
    return json.dumps({"file_path": path, "load_reason": reason})


# 全好日志:允许集五路径(CLAUDE.md 三处 + 常驻桶 language.md + 目录页 README.md)
ALLOWED_LOG = "\n".join([
    _line("/home/tester/project/CLAUDE.md"),
    _line("/home/tester/project/.claude/CLAUDE.md"),
    _line("/home/tester/.claude/CLAUDE.md"),
    _line("/home/tester/project/.claude/rules/language.md"),
    _line("/home/tester/project/.claude/rules/README.md"),
])


class TestAuditResidentRules(unittest.TestCase):
    """_audit_resident_rules:session_start 装载清单仅允许常载集。"""

    def test_allow_set_all_pass(self):
        """ut-audit-allow-pass:五条允许路径全 session_start 装载 → PASS 无违规。"""
        out = night._audit_resident_rules(ALLOWED_LOG)
        self.assertEqual(out["result"], "PASS")
        self.assertEqual(out["violations"], [])
        self.assertEqual(out["loaded"], 5)

    def test_condition_bucket_at_session_start_fails(self):
        """ut-audit-cond-fail:条件桶规则出现在 session_start 装载 → FAIL+文件名(去重)。"""
        log = ALLOWED_LOG + "\n" + "\n".join([
            _line("/home/tester/project/.claude/rules/code-usage.md"),
            _line("/home/tester/project/.claude/rules/code-usage.md"),  # 二次会话重复装载
        ])
        out = night._audit_resident_rules(log)
        self.assertEqual(out["result"], "FAIL")
        self.assertEqual(out["violations"], ["code-usage.md"])

    def test_multiple_buckets_violations_listed(self):
        """ut-audit-multi-fail:条件/行为路由/媒体触发桶同时常载 → 清单列全。"""
        log = ALLOWED_LOG + "\n" + "\n".join([
            _line("/home/tester/project/.claude/rules/code-usage.md"),
            _line("/home/tester/project/.claude/rules/openspec-superpowers-workflow.md"),
        ])
        out = night._audit_resident_rules(log)
        self.assertEqual(out["result"], "FAIL")
        self.assertEqual(out["violations"],
                         ["code-usage.md", "openspec-superpowers-workflow.md"])

    def test_ondemand_load_not_audited(self):
        """ut-audit-ondemand-ok:非 session_start 装载(渐进加载正确行为)不计入审计。"""
        log = ALLOWED_LOG + "\n" + _line(
            "/home/tester/project/.claude/rules/code-usage.md", reason="matched")
        out = night._audit_resident_rules(log)
        self.assertEqual(out["result"], "PASS")
        self.assertEqual(out["violations"], [])

    def test_non_json_lines_tolerated(self):
        """ut-audit-junk:非 JSON 行/空行容错跳过,不炸也不误判。"""
        log = ("\nnot-a-json-line\n" + ALLOWED_LOG
               + "\n{\n" + _line("/home/tester/project/.claude/rules/mcp-servers.md"))
        out = night._audit_resident_rules(log)
        self.assertEqual(out["result"], "FAIL")
        self.assertEqual(out["violations"], ["mcp-servers.md"])

    def test_empty_log_passes_with_zero_loaded(self):
        """ut-audit-empty:空日志(hook 未触发)→ PASS 且 loaded=0,不误伤。"""
        out = night._audit_resident_rules("")
        self.assertEqual(out["result"], "PASS")
        self.assertEqual(out["violations"], [])
        self.assertEqual(out["loaded"], 0)


class TestCreateTestProjectHook(unittest.TestCase):
    """create_test_project:仅 claude 注入 InstructionsLoaded hook(保守合并)。"""

    def test_claude_gets_hook_injection(self):
        """ut-hook-claude-inject:claude 端 exec 注入 hook 脚本(追加写 loaded.log+合并)。"""
        c = mock.MagicMock()
        session.create_test_project(c, agent="claude")
        cmds = [call.args[0] for call in c.exec.call_args_list if call.args]
        hook_cmds = [cmd for cmd in cmds if "InstructionsLoaded" in cmd]
        self.assertEqual(len(hook_cmds), 1)
        self.assertIn("cat >> /home/tester/project/loaded.log", hook_cmds[0])
        self.assertIn(".claude/settings.json", hook_cmds[0])
        self.assertIn("python3", hook_cmds[0])  # 容器内 python3 保守合并 hooks 键
        # 既有行为不回归:基础项目脚本与 P7 截图拷贝照常
        self.assertIn(mock.call(session.PROJECT_INIT_SCRIPT, timeout=30),
                      c.exec.call_args_list)
        self.assertTrue(any(
            (call.args and len(call.args) > 1
             and call.args[1] == "/home/tester/project/assets/error.png")
            or call.kwargs.get("dst") == "/home/tester/project/assets/error.png"
            for call in c.copy_in.call_args_list))

    def test_non_claude_agents_get_no_hook(self):
        """ut-hook-nonclaude-clean:codex/omp/默认 None 均不注入 hook。"""
        for agent in ("codex", "omp", None):
            with self.subTest(agent=agent):
                c = mock.MagicMock()
                session.create_test_project(c, agent=agent)
                cmds = [call.args[0] for call in c.exec.call_args_list if call.args]
                self.assertFalse(any("InstructionsLoaded" in cmd for cmd in cmds))
                self.assertFalse(any("loaded.log" in cmd for cmd in cmds))

    def test_shared_init_script_stays_clean(self):
        """ut-hook-shared-clean:hook 片段不进五端共享 PROJECT_INIT_SCRIPT。"""
        self.assertNotIn("InstructionsLoaded", session.PROJECT_INIT_SCRIPT)
        self.assertNotIn("loaded.log", session.PROJECT_INIT_SCRIPT)
        # claude 专属脚本是独立常量,含 hook JSON 与合并语义
        hook = session.CLAUDE_HOOK_INIT_SCRIPT
        self.assertIn("InstructionsLoaded", hook)
        self.assertIn("cat >> /home/tester/project/loaded.log", hook)


_TRUNCATE_CMD = "truncate -s 0 /home/tester/project/loaded.log"


class _NightFakeContainer:
    """容器 mock:记录 exec 时序;cat loaded.log 返回预设审计日志。"""

    def __init__(self, loaded_log=""):
        self.loaded_log = loaded_log
        self.calls = []  # 时序标记:("exec", cmd) / ("stage1", None) / ("probe", ...)

    def exec(self, cmd, cwd="/home/tester", env=None, timeout=300):
        self.calls.append(("exec", cmd))
        if cmd == "cat /home/tester/project/loaded.log":
            return {"rc": 0, "stdout": self.loaded_log, "stderr": ""}
        return {"rc": 0, "stdout": "", "stderr": ""}

    def snapshot_fs(self, path="/home/tester"):
        return {}

    def destroy(self):
        pass


def _fake_stage1(c, agent=None):
    c.calls.append(("stage1", None))
    return [{"name": name, "returncode": 0, "duration_s": 1.0,
             "final_text": "", "stderr": ""}
            for name in ("pre-check", "mcp-configuration", "rule-config",
                         "project-rules-examples")]


def _fake_probe(c, agent, prompt, timeout=900, retries=1):
    c.calls.append(("probe", prompt))
    return {"returncode": 0, "duration_s": 1.0, "final_text": "ok", "stderr": ""}


class TestNightResidentAuditFlow(unittest.TestCase):
    """run_docker_night:stage1 后截断(仅 claude)→ 探针 → 审计进汇总 dict。"""

    _PROBE = {"T1": {"prompt_variants": ["审计探针 {module} <fixture>"]}}

    def _run(self, agent, loaded_log=""):
        c = _NightFakeContainer(loaded_log)
        score = {"behavior": "PASS", "verdict": "PASS",
                 "failures": [], "behavior_failures": []}
        import tempfile
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        with mock.patch.object(night, "create_test_container",
                               return_value=c), \
             mock.patch.object(night, "create_test_project") as cp, \
             mock.patch.object(night, "run_stage1", side_effect=_fake_stage1), \
             mock.patch.object(night, "_write_stage1_assertions",
                               return_value=Path("/tmp/x-stage1.json")), \
             mock.patch.object(night, "run_probe", side_effect=_fake_probe), \
             mock.patch.object(night, "_score_probe_text",
                               return_value=score), \
             mock.patch.object(night, "_write_probe_result"), \
             mock.patch.object(night, "RESULT_ROOT", Path(tmp.name)), \
             mock.patch.object(night, "PROBES", self._PROBE):
            result = night.run_docker_night(agent, ["T1"], session_id="s9")
        return result, c, cp
        return result, c, cp

    def test_claude_truncates_then_audits(self):
        """ut-night-claude-audit:截断+审计均执行,结论进 resident_audit 键。"""
        log = ALLOWED_LOG + "\n" + _line(
            "/home/tester/project/.claude/rules/code-usage.md")
        result, c, cp = self._run("claude", loaded_log=log)
        cmds = [cmd for kind, cmd in c.calls if kind == "exec"]
        self.assertIn(_TRUNCATE_CMD, cmds)
        self.assertIn("cat /home/tester/project/loaded.log", cmds)
        self.assertEqual(result["resident_audit"],
                         {"result": "FAIL", "loaded": 6,
                          "violations": ["code-usage.md"]})
        cp.assert_called_once_with(c, agent="claude")

    def test_claude_truncate_between_stage1_and_probes(self):
        """ut-night-claude-order:截断发生在 stage1 之后、首个探针之前。"""
        result, c, _ = self._run("claude", loaded_log=ALLOWED_LOG)
        kinds = c.calls
        stage1_at = next(i for i, k in enumerate(kinds) if k[0] == "stage1")
        truncate_at = next(i for i, k in enumerate(kinds)
                           if k == ("exec", _TRUNCATE_CMD))
        probe_at = next(i for i, k in enumerate(kinds) if k[0] == "probe")
        self.assertGreater(truncate_at, stage1_at)
        self.assertLess(truncate_at, probe_at)
        self.assertEqual(result["resident_audit"]["result"], "PASS")

    def test_non_claude_no_truncate_no_audit_key(self):
        """ut-night-nonclaude-clean:非 claude 端不截断不审计,汇总无 resident_audit 键。"""
        result, c, cp = self._run("codex")
        cmds = [cmd for kind, cmd in c.calls if kind == "exec"]
        self.assertNotIn(_TRUNCATE_CMD, cmds)
        self.assertNotIn("cat /home/tester/project/loaded.log", cmds)
        self.assertNotIn("resident_audit", result)
        cp.assert_called_once_with(c, agent="codex")


if __name__ == "__main__":
    unittest.main()
