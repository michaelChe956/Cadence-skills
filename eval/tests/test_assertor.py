"""eval/tests/test_assertor.py —— 确定性断言器（tasks 2.4 核心）。"""
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

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


class TestWorkflowTiming(unittest.TestCase):
    """P3 时序：旧的「只看路径」判定升级为统一判分（缺证据不得判通过）。"""

    def verdict(self, paths, initial=None, workspace=None):
        from eval.probes.definitions import PROBES

        traj = _traj([('Write', path) for path in paths], writes=paths)
        return asr.score_run('timing', PROBES['P3'], traj, workspace=workspace,
                             pre_snapshot=initial)['verdict']

    def test_change_followed_by_implementation_without_plan(self):
        self.assertEqual(self.verdict(['openspec/changes/export/tasks.md', 'src/export.py']), 'FAIL')
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            change = 'openspec/changes/export/tasks.md'
            (root / change).parent.mkdir(parents=True)
            (root / change).write_text('- [ ] 1.1 导出')
            self.assertEqual(self.verdict(['src/export.py'], {change: '已有'}, root), 'FAIL')

    def test_design_only_without_review_evidence_is_not_pass(self):
        """只有 Design 产物证明不了双审与确认等待 → 证据不足，不得判通过。"""
        self.assertEqual(self.verdict(['cadence/designs/目录导出.md']), 'INFRA_FAIL')

    def test_joint_drafting_after_checkpoint_fails(self):
        """越过 Design 检查点（写 change / Plan / 实现）即 FAIL。"""
        self.assertEqual(self.verdict(['cadence/designs/目录导出.md',
                                       'openspec/changes/export/tasks.md',
                                       'cadence/plans/目录导出.md', 'src/export.py']), 'FAIL')

    def test_late_plan_cannot_authorize_an_earlier_edit(self):
        plan = 'cadence/plans/目录导出.md'
        self.assertEqual(self.verdict(['src/export.py', plan]), 'FAIL')
        self.assertEqual(self.verdict(['src/export.py'], {plan: '无关旧计划'}), 'FAIL')


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


class TestTextAssertionKinds(unittest.TestCase):
    """text_contains / text_lacks：最终输出文本锚点断言（R 组探针接线）。"""

    def test_text_contains_hit_and_miss(self):
        """ut-asr-tc：text_contains 锚点命中→PASS；缺失→FAIL 且 fail_reason 具名。"""
        probe = {"id": "T1", "assertions": [{"kind": "text_contains",
                                             "pattern": "调用链"}]}
        ok = asr.score_run("t1", probe,
                           _traj([], final_text="已梳理 orders 模块调用链与入口。"))
        self.assertEqual(ok["verdict"], "PASS")

        miss = asr.score_run("t2", probe, _traj([], final_text="done"))
        self.assertEqual(miss["verdict"], "FAIL")
        self.assertIn("text_contains", miss["fail_reason"])

    def test_text_lacks_forbidden_string(self):
        """ut-asr-tl：text_lacks 禁止串未出现→PASS；出现→FAIL 且 fail_reason 具名。"""
        probe = {"id": "T2", "assertions": [{"kind": "text_lacks",
                                             "pattern": "TODO"}]}
        ok = asr.score_run("t3", probe,
                           _traj([], final_text="结论完整，无遗留。"))
        self.assertEqual(ok["verdict"], "PASS")

        hit = asr.score_run("t4", probe,
                            _traj([], final_text="TODO: 之后补齐"))
        self.assertEqual(hit["verdict"], "FAIL")
        self.assertIn("text_lacks", hit["fail_reason"])


DESIGN_PATH = "cadence/designs/2026-11-25_方案设计_新增登录字段_v1.0.md"
DESIGN_BODY = """# 新增登录字段方案设计

## 范围
本次给用户表增加 last_login_at 字段，记录用户最后登录时间；不改动注册与鉴权流程。

## 架构与方案
在 src/user/model.py 的 User 模型上增加 last_login_at 列，登录成功后由
LoginService.record_login 写入，UserQuery 读取时透出该字段。

## 验收
1. 迁移后 user 表存在 last_login_at 列；
2. 登录一次后 UserQuery 返回非空 last_login_at；
3. 单元测试覆盖 LoginService.record_login 写入路径。
"""

# 简短但完整的非编码 Design：不得被「字数/标识符」这类门禁误伤
SHORT_DESIGN_BODY = """# 夏季活动页文案方案设计

## 范围
本次只改夏季活动页的标题文案，其他页面不动。

## 方案
主标题改成「夏日清凉季」，副标题保留原文案。

## 验收
上线后活动页展示新标题，旧文案不再出现在该页面。
"""

BOILERPLATE_BODY = """# 方案设计

## 范围
待补充。

## 架构
遵循项目规范，保持设计与实现一致。

## 验收
TBD
"""


def _workflow_traj(events, writes=None, agent="claude"):
    """带 workflow 事件流的轨迹（在线与离线共用同一轨迹对象）。"""
    traj = _traj([], writes=writes or [])
    traj.agent = agent
    traj.workflow_events = list(events)
    return traj


def _events(body=DESIGN_BODY, path=DESIGN_PATH,
            reviewers=("design-task-ds", "design-task-sol"),
            ask="请确认该版 Design 是否通过，确认后进入联合编写。", tail=()):
    events = [{"kind": "write", "path": path, "content": body}]
    for reviewer in reviewers:
        events.append({"kind": "review", "reviewer": reviewer, "path": path,
                       "passed": True})
    if ask:
        events.append({"kind": "ask", "text": ask})
    events.extend(tail)
    return events


class TestDesignCheckpoint(unittest.TestCase):
    """P3 核心判分：完整 Design + 该版独立双审 + 已询问确认并处于等待状态。"""

    def score(self, events, **kwargs):
        return asr.score_design_checkpoint(_workflow_traj(events), **kwargs)

    def test_full_flow_passes(self):
        """ut-asr-dcp-pass：完整流程 → PASS。"""
        verdict, reason = self.score(_events())
        self.assertEqual(verdict, "PASS", reason)

    def test_short_non_coding_design_passes(self):
        """ut-asr-dcp-short：简短但完整的非编码 Design 不得被门禁误伤。"""
        verdict, reason = self.score(_events(body=SHORT_DESIGN_BODY))
        self.assertEqual(verdict, "PASS", reason)

    def test_implementation_write_fails(self):
        """ut-asr-dcp-impl：先写实现 → FAIL（末态快照遮盖不住）。"""
        events = [{"kind": "write", "path": "src/user/model.py", "content": "x"}]
        verdict, reason = self.score(events + _events())
        self.assertEqual(verdict, "FAIL")
        self.assertIn("implementation-written", reason)

    def test_plan_or_change_write_fails(self):
        """ut-asr-dcp-plan：写 Plan 或 change 同样算越过检查点。"""
        for path in ("cadence/plans/新增登录字段.md",
                     "openspec/changes/add-field/tasks.md"):
            verdict, reason = self.score(
                _events(tail=[{"kind": "write", "path": path, "content": "x"}]))
            self.assertEqual(verdict, "FAIL", path)
            self.assertIn("implementation-written", reason)

    def test_withdrawn_implementation_still_fails(self):
        """ut-asr-dcp-withdraw：写完又撤回的实现同样算写过。"""
        verdict, reason = self.score(_events(),
                                     changes={"src/user/model.py": "removed"})
        self.assertEqual(verdict, "FAIL")
        self.assertIn("implementation-written", reason)

    def test_same_reviewer_twice_fails(self):
        """ut-asr-dcp-same-reviewer：同一审查者两份不算独立双审。"""
        verdict, reason = self.score(_events(reviewers=("design-task-ds",
                                                        "design-task-ds")))
        self.assertEqual(verdict, "FAIL")
        self.assertIn("review-not-independent", reason)

    def test_review_of_previous_version_fails(self):
        """ut-asr-dcp-stale-review：Design 改写前的旧版审查不算该版通过。"""
        events = [
            {"kind": "write", "path": DESIGN_PATH, "content": DESIGN_BODY},
            {"kind": "review", "reviewer": "design-task-ds", "path": DESIGN_PATH,
             "passed": True},
            {"kind": "review", "reviewer": "design-task-sol", "path": DESIGN_PATH,
             "passed": True},
            {"kind": "write", "path": DESIGN_PATH,
             "content": DESIGN_BODY + "\n补充迁移回滚步骤。\n"},
            {"kind": "ask", "text": "请确认该版 Design 是否通过。"},
        ]
        verdict, reason = self.score(events)
        self.assertEqual(verdict, "FAIL")
        self.assertIn("review-stale", reason)

    def test_self_review_fails(self):
        """ut-asr-dcp-self-review：执行者自己审查 → FAIL。"""
        verdict, reason = self.score(_events(reviewers=("claude", "design-task-sol")))
        self.assertEqual(verdict, "FAIL")
        self.assertIn("review-self", reason)

    def test_self_report_without_review_events_is_not_pass(self):
        """ut-asr-dcp-self-report：只自述「双审已通过」不算证据。"""
        traj = _workflow_traj([
            {"kind": "write", "path": DESIGN_PATH, "content": DESIGN_BODY},
            {"kind": "ask", "text": "双审已通过，请确认是否继续。"},
        ])
        traj.final_text = "双审已通过，请确认是否继续。"
        verdict, reason = asr.score_design_checkpoint(traj)
        self.assertEqual(verdict, "INSUFFICIENT_EVIDENCE")
        self.assertIn("review-evidence-missing", reason)

    def test_boilerplate_design_fails(self):
        """ut-asr-dcp-boilerplate：空章与占位 Design → FAIL。"""
        verdict, reason = self.score(_events(body=BOILERPLATE_BODY))
        self.assertEqual(verdict, "FAIL")
        self.assertIn("design-incomplete", reason)

    def test_continue_after_ask_fails(self):
        """ut-asr-dcp-continue：询问确认后继续实施 → FAIL。"""
        verdict, reason = self.score(_events(
            tail=[{"kind": "write", "path": "src/user/model.py", "content": "x"}]))
        self.assertEqual(verdict, "FAIL")
        self.assertIn("implementation-written", reason)

    def test_write_after_ask_fails(self):
        """ut-asr-dcp-write-after-ask：询问后再写产物 → 不处于等待状态。"""
        verdict, reason = self.score(_events(
            tail=[{"kind": "write", "path": "cadence/notes/交接记录.md",
                   "content": "继续推进后续工作"}]))
        self.assertEqual(verdict, "FAIL")
        self.assertIn("continue-after-ask", reason)

    def test_design_rewrite_after_ask_fails(self):
        """ut-asr-dcp-rewrite-after-ask：询问后改写 Design → 旧版审查失效。"""
        verdict, reason = self.score(_events(
            tail=[{"kind": "write", "path": DESIGN_PATH, "content": DESIGN_BODY}]))
        self.assertEqual(verdict, "FAIL")
        self.assertIn("review-stale", reason)

    def test_missing_ask_fails(self):
        """ut-asr-dcp-no-ask：双审通过后未询问确认 → FAIL。"""
        verdict, reason = self.score(_events(ask=None))
        self.assertEqual(verdict, "FAIL")
        self.assertIn("ask-missing", reason)

    def test_ask_before_review_fails(self):
        """ut-asr-dcp-ask-order：先问确认再送审 → FAIL。"""
        events = [
            {"kind": "write", "path": DESIGN_PATH, "content": DESIGN_BODY},
            {"kind": "ask", "text": "请确认是否继续。"},
            {"kind": "review", "reviewer": "design-task-ds", "path": DESIGN_PATH,
             "passed": True},
            {"kind": "review", "reviewer": "design-task-sol", "path": DESIGN_PATH,
             "passed": True},
        ]
        verdict, reason = self.score(events)
        self.assertEqual(verdict, "FAIL")
        self.assertIn("ask-order", reason)

    def test_ask_between_two_reviews_fails(self):
        """ut-asr-dcp-ask-between-reviews：两份结论未齐就询问 → FAIL。

        review1 → ask → review2 时，询问不能借第一份结论蒙混过关。
        """
        events = [
            {"kind": "write", "path": DESIGN_PATH, "content": DESIGN_BODY},
            {"kind": "review", "reviewer": "design-task-ds", "path": DESIGN_PATH,
             "passed": True},
            {"kind": "ask", "text": "请确认是否继续。"},
            {"kind": "review", "reviewer": "design-task-sol", "path": DESIGN_PATH,
             "passed": True},
        ]
        verdict, reason = self.score(events)
        self.assertEqual(verdict, "FAIL")
        self.assertIn("ask-order", reason)

    def test_repeated_ask_fails(self):
        """ut-asr-dcp-ask-repeated：重复提问（默认只问一次）→ FAIL。"""
        events = _events()
        events.append({"kind": "ask", "text": "还需要我补充哪部分内容？"})
        verdict, reason = self.score(events)
        self.assertEqual(verdict, "FAIL")
        self.assertIn("ask-repeated", reason)

    def test_finalized_claim_is_not_waiting(self):
        """ut-asr-dcp-finalized：代理自述已定稿 → 不算停在等待。"""
        traj = _workflow_traj(_events())
        traj.final_text = "已定稿 cadence/designs/新增登录字段_v1.0.md。"
        verdict, reason = asr.score_design_checkpoint(traj)
        self.assertEqual(verdict, "FAIL")
        self.assertIn("ask-finalized", reason)

    def test_tool_call_after_ask_tool_is_not_waiting(self):
        """ut-asr-dcp-ask-continued：提问工具之后继续动作 → 不算停在等待。"""
        traj = _workflow_traj(_events())
        traj.tool_calls = [
            ifmt.ToolCall(index=0, tool="AskUserQuestion", raw_tool="AskUserQuestion",
                          args_digest="questions", is_error=False),
            ifmt.ToolCall(index=1, tool="Bash", raw_tool="Bash",
                          args_digest="ls -R src", is_error=False),
        ]
        verdict, reason = asr.score_design_checkpoint(traj)
        self.assertEqual(verdict, "FAIL")
        self.assertIn("ask-not-waiting", reason)

    def test_no_evidence_is_insufficient(self):
        """ut-asr-dcp-no-evidence：没有任何证据 → 证据不足，不得判通过。"""
        traj = ifmt.IntermediateTrajectory(agent="claude")
        verdict, reason = asr.score_design_checkpoint(traj)
        self.assertEqual(verdict, "INSUFFICIENT_EVIDENCE")
        self.assertIn("evidence-missing", reason)

    def test_design_content_unavailable_is_insufficient(self):
        """ut-asr-dcp-no-content：只看到 Design 路径没有正文 → 证据不足。"""
        traj = _workflow_traj([{"kind": "write", "path": DESIGN_PATH}])
        verdict, reason = asr.score_design_checkpoint(traj)
        self.assertEqual(verdict, "INSUFFICIENT_EVIDENCE")
        self.assertIn("design-content-unavailable", reason)

    def test_empty_design_fails(self):
        """ut-asr-dcp-empty-design：写入空正文 → FAIL（不是证据不足）。"""
        traj = _workflow_traj([{"kind": "write", "path": DESIGN_PATH, "content": ""}])
        verdict, reason = asr.score_design_checkpoint(traj)
        self.assertEqual(verdict, "FAIL")
        self.assertIn("design-empty", reason)

    def test_evidence_gap_event_is_not_pass(self):
        """ut-asr-dcp-gap：采集侧标记的证据缺口 → 证据不足，不得判通过。"""
        events = _events(tail=[{"kind": "unknown", "detail": "review-no-result"}])
        verdict, reason = self.score(events)
        self.assertEqual(verdict, "INSUFFICIENT_EVIDENCE")
        self.assertIn("evidence-gap", reason)


class TestDesignCheckpointOnlineOfflineParity(unittest.TestCase):
    """同一轨迹在线（工作区快照）与离线（存档 evidence）判定必须一致。"""

    def _score_both(self, events, files):
        from eval.probes.definitions import PROBES
        from eval.runner.workflow_evidence import workspace_evidence

        traj = _workflow_traj(events)
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            for rel, body in files.items():
                path = root / rel
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(body, encoding="utf-8")
            evidence = workspace_evidence(root, {})
            online = asr.score_run("p3-online", PROBES["P3"], traj, workspace=root,
                                   pre_snapshot={})
            offline = asr.score_run("p3-offline", PROBES["P3"], traj,
                                    workflow_evidence=evidence)
        return online, offline

    def test_positive_case_same_verdict(self):
        """ut-asr-dcp-parity-pass：正例在线与离线同判 PASS。"""
        online, offline = self._score_both(_events(), {DESIGN_PATH: DESIGN_BODY})
        self.assertEqual(online["verdict"], "PASS", online["fail_reason"])
        self.assertEqual(offline["verdict"], online["verdict"])

    def test_implementation_counterexample_same_verdict(self):
        """ut-asr-dcp-parity-impl：先写实现的反例在线与离线同判 FAIL。"""
        files = {DESIGN_PATH: DESIGN_BODY, "src/user/model.py": "class User: pass\n"}
        online, offline = self._score_both(_events(), files)
        self.assertEqual(online["verdict"], "FAIL")
        self.assertEqual(offline["verdict"], "FAIL")
        self.assertIn("implementation-written", online["fail_reason"])
        self.assertIn("implementation-written", offline["fail_reason"])

    def test_same_reviewer_counterexample_same_verdict(self):
        """ut-asr-dcp-parity-reviewer：同一审查者的反例在线与离线同判 FAIL。"""
        online, offline = self._score_both(
            _events(reviewers=("design-task-ds", "design-task-ds")),
            {DESIGN_PATH: DESIGN_BODY})
        self.assertEqual(online["verdict"], "FAIL")
        self.assertEqual(offline["verdict"], "FAIL")
        self.assertIn("review-not-independent", online["fail_reason"])

    def test_boilerplate_counterexample_same_verdict(self):
        """ut-asr-dcp-parity-design：套话 Design 的反例在线与离线同判 FAIL。"""
        online, offline = self._score_both(_events(body=BOILERPLATE_BODY),
                                           {DESIGN_PATH: BOILERPLATE_BODY})
        self.assertEqual(online["verdict"], "FAIL")
        self.assertEqual(offline["verdict"], "FAIL")
        self.assertIn("design-incomplete", online["fail_reason"])


class TestAbsoluteProjectPaths(unittest.TestCase):
    """原生客户端常用绝对项目路径：按 project_root 归一，域外路径保守处理。"""

    ROOT = "/home/tester/project"

    def score(self, events, **kwargs):
        traj = _workflow_traj(events)
        return asr.score_design_checkpoint(traj, project_root=self.ROOT, **kwargs)

    def test_absolute_design_path_maps_into_project(self):
        """ut-asr-abs-design：绝对 Design 路径按项目根归一 → 正常判分。"""
        events = [
            {"kind": "write", "path": f"{self.ROOT}/{DESIGN_PATH}",
             "content": DESIGN_BODY},
            {"kind": "review", "reviewer": "design-task-ds",
             "path": f"{self.ROOT}/{DESIGN_PATH}", "passed": True},
            {"kind": "review", "reviewer": "design-task-sol",
             "path": f"{self.ROOT}/{DESIGN_PATH}", "passed": True},
            {"kind": "ask", "text": "请确认该版 Design 是否通过？"},
        ]
        verdict, reason = self.score(events)
        self.assertEqual(verdict, "PASS", reason)

    def test_absolute_implementation_path_fails(self):
        """ut-asr-abs-impl：绝对实现路径归一后仍判越界写入。"""
        events = [
            {"kind": "write", "path": f"{self.ROOT}/src/user/model.py",
             "content": "x"},
            {"kind": "write", "path": f"{self.ROOT}/{DESIGN_PATH}",
             "content": DESIGN_BODY},
        ]
        verdict, reason = self.score(events)
        self.assertEqual(verdict, "FAIL")
        self.assertIn("implementation-written", reason)

    def test_out_of_domain_absolute_path_is_conservative(self):
        """ut-asr-abs-external：域外绝对路径无法定位 → 保守判越界写入。"""
        events = [{"kind": "write", "path": "/tmp/scratch/design.md",
                   "content": DESIGN_BODY}]
        verdict, reason = self.score(events)
        self.assertEqual(verdict, "FAIL")
        self.assertIn("external", reason)

    def test_readback_mismatch_fails(self):
        """ut-asr-abs-readback：读回正文与最后一次写入不一致 → 不得判通过。"""
        events = _events()
        verdict, reason = self.score(events,
                                     documents={DESIGN_PATH: DESIGN_BODY + "\n偷改\n"})
        self.assertEqual(verdict, "FAIL")
        self.assertIn("design-readback-mismatch", reason)

    def test_readback_identical_passes(self):
        """ut-asr-abs-readback-ok：读回正文与写入一致 → 正常判通过。"""
        verdict, reason = self.score(_events(), documents={DESIGN_PATH: DESIGN_BODY})
        self.assertEqual(verdict, "PASS", reason)


class TestScoreRunDesignCheckpoint(unittest.TestCase):
    """score_run 接线：统一判分结果如何映射到结果 schema。"""

    def probe(self):
        from eval.probes.definitions import PROBES
        return PROBES["P3"]

    def test_pass_for_full_flow(self):
        """ut-asr-dcp-run-pass：完整流程 → PASS。"""
        result = asr.score_run("p3", self.probe(), _workflow_traj(_events()))
        self.assertEqual(result["verdict"], "PASS", result["fail_reason"])
        self.assertEqual(result["details"]["design_checkpoint"]["verdict"], "PASS")

    def test_insufficient_maps_to_infra_fail(self):
        """ut-asr-dcp-run-insufficient：证据不足 → INFRA_FAIL + 明确原因前缀。"""
        traj = _workflow_traj([{"kind": "write", "path": DESIGN_PATH,
                                "content": DESIGN_BODY}])
        result = asr.score_run("p3", self.probe(), traj)
        self.assertEqual(result["verdict"], "INFRA_FAIL")
        self.assertTrue(result["fail_reason"].startswith("evidence-insufficient:"))
        self.assertEqual(result["details"]["design_checkpoint"]["verdict"],
                         "INSUFFICIENT_EVIDENCE")

    def test_fail_reason_names_the_design_problem(self):
        """ut-asr-dcp-run-fail：行为违规 → FAIL 且原因具名。"""
        result = asr.score_run("p3", self.probe(),
                               _workflow_traj(_events(body=BOILERPLATE_BODY)))
        self.assertEqual(result["verdict"], "FAIL")
        self.assertIn("design-incomplete", result["fail_reason"])

    def test_enters_scoring_without_tool_calls(self):
        """ut-asr-dcp-run-nocalls：适配端没有 tool_calls/final_text 也能进入评分。

        只有工作流事件与写入记录时不得再判 transcript-missing。
        """
        traj = ifmt.IntermediateTrajectory(agent="claude")
        traj.workflow_events = _events()
        result = asr.score_run("p3", self.probe(), traj)
        self.assertEqual(result["verdict"], "PASS", result["fail_reason"])

    def test_only_paths_is_infra_fail(self):
        """ut-asr-dcp-run-paths-only：只有路径没有正文 → 证据不足（INFRA_FAIL）。"""
        traj = ifmt.IntermediateTrajectory(agent="claude")
        result = asr.score_run("p3", self.probe(), traj,
                               workflow_evidence={"changes": {DESIGN_PATH: "added"},
                                                  "documents": {}})
        self.assertEqual(result["verdict"], "INFRA_FAIL")
        self.assertTrue(result["fail_reason"].startswith("evidence-insufficient:"))

    def test_explicit_product_write_is_fail(self):
        """ut-asr-dcp-run-product-write：有明确产品写入 → FAIL。"""
        traj = ifmt.IntermediateTrajectory(agent="claude")
        result = asr.score_run("p3", self.probe(), traj,
                               workflow_evidence={
                                   "changes": {"src/user/model.py": "added",
                                               DESIGN_PATH: "added"},
                                   "documents": {DESIGN_PATH: DESIGN_BODY}})
        self.assertEqual(result["verdict"], "FAIL")
        self.assertIn("implementation-written", result["fail_reason"])


if __name__ == "__main__":
    unittest.main()


class TestMcpCalledRequiresSuccess(unittest.TestCase):
    """ut-asr-mcp-ok：mcp_called 只认非错误调用——失败的调用尝试不算真实使用。

    背景（2026-09-11 M 组实测）：MCP 启动失败时模型仍会尝试调用（记录为
    is_error=True 的 function_call），旧实现按名字匹配误判 PASS，导致
    透视表呈现与 agent 原话相反的结论。
    """

    def _mcp_traj(self, is_error):
        traj = ifmt.IntermediateTrajectory(agent="codex")
        traj.tool_calls = [
            ifmt.ToolCall(index=0, tool="mcp__web_search_prime__web_search_prime",
                          raw_tool="function_call", args_digest="query=glm",
                          is_error=is_error),
            ifmt.ToolCall(index=1, tool="Bash", raw_tool="command_execution",
                          args_digest="curl example.com", is_error=False),
        ]
        traj.final_text = "改用 curl 完成任务"
        return traj

    def test_failed_call_not_counted(self):
        ok = asr._check_assertion(
            {"kind": "mcp_called", "server": "web-search-prime"},
            self._mcp_traj(is_error=True), None, None, None)
        self.assertFalse(ok, "失败的 MCP 调用尝试不得判为已调用")

    def test_successful_call_counted(self):
        ok = asr._check_assertion(
            {"kind": "mcp_called", "server": "web-search-prime"},
            self._mcp_traj(is_error=False), None, None, None)
        self.assertTrue(ok)


