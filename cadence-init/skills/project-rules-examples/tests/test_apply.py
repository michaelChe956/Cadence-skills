#!/usr/bin/env python3
"""apply.py 确定性章节合并测试（单元 + 端到端）。

运行：python3 tests/test_apply.py   （或经 tests/test-apply.sh 统一入口）
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))

import apply as prx  # noqa: E402

REFS = Path(__file__).resolve().parent.parent / "references" / "project-rules"
TEMPLATES = {tmpl_rel: (REFS / tmpl_rel).read_text(encoding="utf-8") for tmpl_rel, _ in prx.TARGETS}
PROJECT_RELS = [rel for _, rel in prx.TARGETS]


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def drop_section(text: str, title_contains: str) -> str:
    """从模板文本中删除标题含 token 的章节，构造'缺失章节'夹具。"""
    sections = prx._sections(text)
    keep = [raw for _level, _key, _title, raw in sections if title_contains not in _title]
    assert len(keep) < len(sections), f"未找到章节：{title_contains}"
    return "\n".join("\n".join(raw) for raw in keep).rstrip() + "\n"


class PrxTestCase(unittest.TestCase):
    def make_root(self) -> Path:
        tmp = tempfile.TemporaryDirectory(prefix="prx-apply-pytest.")
        self.addCleanup(tmp.cleanup)
        return Path(tmp.name)

    def write_target(self, root: Path, rel: str, text: str) -> None:
        path = root / "cadence" / "project-rules" / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def run_apply(self, root: Path, env: dict[str, str] | None = None) -> subprocess.CompletedProcess:
        """真实 CLI 调用；默认剔除 CADENCE_SKILL_RUN_ID，env 中的变量原样设置（空串也算设置）。"""
        child_env = os.environ.copy()
        child_env.pop("CADENCE_SKILL_RUN_ID", None)
        if env:
            child_env.update(env)
        return subprocess.run(
            [sys.executable, str(SCRIPTS / "apply.py"), "--project-root", str(root)],
            capture_output=True,
            text=True,
            check=False,
            env=child_env,
        )

    def state_of(self, stdout: str, rel: str) -> str:
        """按行尾目标路径取状态；rel 可为模板相对路径（如 README.md）。"""
        for line in stdout.splitlines():
            parts = line.split(" ", 1)
            if len(parts) == 2 and (parts[1] == rel or parts[1].endswith(f"/{rel}")):
                return parts[0]
        return ""


class UnitTests(PrxTestCase):
    def test_fence_aware_parsing(self):
        text = "# 标题\n\n正文\n\n```text\n# 围栏内不是标题\n```\n\n## 第二节\n\n- x\n"
        self.assertEqual([t for _l, _k, t, _r in prx._sections(text)], ["标题", "第二节"])

    def test_multilevel_numbering_no_collision_drop(self):
        """6.2/7.2 等多级编号章节互不相同，不得因编号归一丢章节。"""
        text = "### 6.2 规则\n\n- a\n\n### 7.2 规则\n\n- b\n"
        merged, changed = prx.merge_missing_sections(text, text)
        self.assertFalse(changed)
        self.assertEqual(merged, text)

    def test_missing_appended_and_renumbered_matched(self):
        template = "## 1. 总体原则\n\n- a\n\n## 2. 编码规则\n\n- b\n"
        merged, changed = prx.merge_missing_sections(
            "## 1. 总体原则\n\n- 用户改写\n", template)
        self.assertTrue(changed)
        self.assertIn("## 2. 编码规则\n\n- b\n", merged)
        # 用户重编号：去编号标题按 (级别, key) 配对，不误判缺失
        _merged2, changed2 = prx.merge_missing_sections(
            "## 3. 总体原则\n\n- 用户改写\n\n## 9. 编码规则\n\n- b\n", template)
        self.assertFalse(changed2)

    def test_append_prefix_preserved(self):
        ours = "# 用户文档\n\n## 我的章节\n\n- 用户行\n\n\n"  # 尾部空行必须保留
        template = ours + "## 模板新章节\n\n- 模板行\n\n- 另一行\n"
        merged, changed = prx.merge_missing_sections(ours, template)
        self.assertTrue(changed)
        self.assertTrue(merged.startswith(ours), "既有字节必须零改动（仅追加）")
        self.assertIn("## 模板新章节", merged)
        self.assertIn("- 模板行\n\n- 另一行\n", merged)

    def test_append_empty_and_crlf(self):
        template = "## 新章节\n\n- 行\n"
        merged, changed = prx.merge_missing_sections("", template)
        self.assertTrue(changed)
        self.assertTrue(merged.startswith("## 新章节"))
        crlf = "# 文档\r\n\r\n## 节\r\n"
        merged_crlf, _ = prx.merge_missing_sections(crlf, template.replace("\n", "\r\n"))
        self.assertTrue(merged_crlf.startswith(crlf))
        self.assertIn("\r\n## 新章节\r\n\r\n- 行\r\n", merged_crlf)

    def test_guards_unparseable_kept(self):
        headingless = "纯文本说明，没有任何 Markdown 标题。\n第二行。\n"
        merged, changed = prx.merge_missing_sections(headingless, TEMPLATES["README.md"])
        self.assertFalse(changed)
        self.assertEqual(merged, headingless)
        unclosed = "# 标题\n\n```text\n未闭合\n"
        merged2, changed2 = prx.merge_missing_sections(unclosed, TEMPLATES["README.md"])
        self.assertFalse(changed2)
        self.assertEqual(merged2, unclosed)


class EndToEndTests(PrxTestCase):
    def test_fresh_project_created_and_entries_reported(self):
        root = self.make_root()
        result = self.run_apply(root)
        self.assertEqual(result.returncode, 0, result.stderr)
        for rel in PROJECT_RELS:
            self.assertEqual(self.state_of(result.stdout, rel), "created", rel)
        for entry in prx.ENTRY_FILES:
            self.assertEqual(self.state_of(result.stdout, entry), "needs-rule-config")
            self.assertFalse((root / entry).exists(), f"{entry} 不得被创建")
        for tmpl_rel, rel in prx.TARGETS:
            self.assertEqual((root / rel).read_bytes(), (REFS / tmpl_rel).read_bytes(), rel)
        self.assertFalse((root / "cadence" / "legacy").exists(), "全新项目无备份")

    def test_rerun_pristine_zero_backup(self):
        root = self.make_root()
        self.run_apply(root)
        result = self.run_apply(root)
        self.assertEqual(result.returncode, 0, result.stderr)
        for rel in PROJECT_RELS:
            self.assertEqual(self.state_of(result.stdout, rel), "pristine", rel)
        self.assertFalse((root / "cadence" / "legacy").exists())

    def test_customized_without_missing_unchanged(self):
        root = self.make_root()
        rel = "examples/coding-standards.md"
        customized = (
            TEMPLATES[rel].replace("**版本**: v1.0", "**版本**: v9.9-用户版")
            + "\n## 我的团队约定\n\n| 键 | 值 |\n|---|---|\n| 提交 | 必须跑回归 |\n"
        )
        self.write_target(root, rel, customized)
        result = self.run_apply(root)
        self.assertEqual(self.state_of(result.stdout, rel), "unchanged", result.stdout)
        self.assertEqual(
            (root / "cadence" / "project-rules" / rel).read_text(encoding="utf-8"),
            customized,
            "用户段落必须逐字保留",
        )
        self.assertFalse((root / "cadence" / "legacy").exists())

    def test_customized_without_base_is_not_appended(self):
        root = self.make_root()
        rel = "README.md"
        original = (
            drop_section(TEMPLATES[rel], "💡 提示")
            + "\n## 用户独有章节\n\n| 键 | 值 |\n|---|---|\n| 回归 | 必跑 |\n\n```text\n# 围栏里的伪标题\n```\n"
        )
        self.write_target(root, rel, original)
        result = self.run_apply(root)
        self.assertEqual(self.state_of(result.stdout, rel), "unchanged", result.stdout)
        merged = (root / "cadence" / "project-rules" / rel).read_text(encoding="utf-8")
        self.assertEqual(merged, original, "无基线且含用户内容时不得追加模板章节")
        self.assertFalse((root / "cadence" / "legacy").exists())

    def test_entry_files_untouched(self):
        root = self.make_root()
        claude = root / "CLAUDE.md"
        agents = root / "AGENTS.md"
        claude.write_text(
            "# CLAUDE.md\n\n## 项目个性化规则\n\n引用 cadence/project-rules/README.md\n",
            encoding="utf-8",
        )
        agents.write_text("# AGENTS.md\n\n普通内容，没有引用。\n", encoding="utf-8")
        hash_c, hash_a = sha(claude.read_text()), sha(agents.read_text())
        result = self.run_apply(root)
        self.assertEqual(self.state_of(result.stdout, "CLAUDE.md"), "skipped")
        self.assertEqual(self.state_of(result.stdout, "AGENTS.md"), "needs-rule-config")
        self.assertEqual(sha(claude.read_text()), hash_c, "CLAUDE.md 哈希必须不变")
        self.assertEqual(sha(agents.read_text()), hash_a, "AGENTS.md 哈希必须不变")

    def test_second_run_zero_writes(self):
        root = self.make_root()
        rel = "examples/test-standards.md"
        self.write_target(root, rel, drop_section(TEMPLATES[rel], "快照测试"))
        first = self.run_apply(root)
        self.assertEqual(self.state_of(first.stdout, rel), "merged")
        cadence = root / "cadence"
        snapshot = {
            str(p): sha(p.read_text(encoding="utf-8")) for p in cadence.rglob("*") if p.is_file()
        }
        legacy_before = {p.name for p in (cadence / "legacy").iterdir()}
        second = self.run_apply(root)
        self.assertEqual(second.returncode, 0, second.stderr)
        for line in second.stdout.splitlines():
            if line.startswith("{"):  # 收尾报告行（machine-readable），不是状态行
                continue
            self.assertIn(
                line.split(" ", 1)[0], {"unchanged", "pristine", "skipped", "needs-rule-config"},
                f"第二次运行不得再写入：{line}",
            )
        snapshot_after = {
            str(p): sha(p.read_text(encoding="utf-8")) for p in cadence.rglob("*") if p.is_file()
        }
        self.assertEqual(snapshot, snapshot_after, "第二次运行文件内容必须零变化")
        self.assertEqual(
            legacy_before, {p.name for p in (cadence / "legacy").iterdir()}, "第二次运行零备份"
        )

    def test_unclosed_fence_unchanged(self):
        root = self.make_root()
        rel = "examples/design-template.md"
        text = TEMPLATES[rel] + "\n```text\n未闭合围栏\n"
        self.write_target(root, rel, text)
        result = self.run_apply(root)
        self.assertEqual(self.state_of(result.stdout, rel), "unchanged")
        self.assertEqual((root / "cadence" / "project-rules" / rel).read_text(encoding="utf-8"), text)

    def test_headingless_file_unchanged(self):
        root = self.make_root()
        rel = "README.md"
        text = "纯文本说明，没有任何 Markdown 标题。\n第二行。\n"
        self.write_target(root, rel, text)
        result = self.run_apply(root)
        self.assertEqual(self.state_of(result.stdout, rel), "unchanged")
        self.assertEqual((root / "cadence" / "project-rules" / rel).read_text(encoding="utf-8"), text)

    def test_empty_file_merged(self):
        root = self.make_root()
        rel = "README.md"
        self.write_target(root, rel, "")
        result = self.run_apply(root)
        self.assertEqual(self.state_of(result.stdout, rel), "merged", result.stdout)
        merged = (root / "cadence" / "project-rules" / rel).read_text(encoding="utf-8")
        self.assertIn("# 项目个性化规则文档", merged)
        second = self.run_apply(root)
        self.assertEqual(self.state_of(second.stdout, rel), "pristine")

    def test_missing_root_exit_2(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPTS / "apply.py"), "--project-root", "/nonexistent-prx-xyz"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 2)



def recipe_report_verdict(tool_output: str) -> str:
    """逐字镜像 cadence-aria `recipe_report_verdict`（coordinator_turn_output.inc.rs）：
    找每个带引号的 "overall" 字段，取其后 64 字符窗口：含 failed → failed；
    含 success 且此前无结论 → success；没有字段 → absent。"""
    field, window, verdict = '"overall"', 64, "absent"
    rest = tool_output
    while True:
        index = rest.find(field)
        if index < 0:
            return verdict
        win = rest[index + len(field):][:window]
        if "failed" in win:
            verdict = "failed"
        elif "success" in win and verdict == "absent":
            verdict = "success"
        rest = rest[index + 1:]


class ReportContractTests(PrxTestCase):
    """stdout 末尾收尾报告契约：单行 JSON；六字段回执契约与明细字段同层，`"overall"` 取值 success|failed。"""

    def last_report(self, stdout: str) -> dict:
        lines = [ln for ln in stdout.splitlines() if ln.strip()]
        self.assertTrue(lines and lines[-1].startswith("{"), f"最后一行必须是报告 JSON：{stdout!r}")
        return json.loads(lines[-1])

    def assert_receipt(self, report: dict, action: str | None, exit_code: int) -> None:
        """六字段回执契约：schema/skill/action/run_id/exit_code/overall，overall 为最后一个键。"""
        self.assertEqual(report["schema"], "cadence.skill-receipt/v1")
        self.assertEqual(report["skill"], "project-rules-examples")
        self.assertEqual(report["action"], action)
        self.assertEqual(report["exit_code"], exit_code)
        self.assertIsInstance(report["exit_code"], int)
        self.assertEqual(report["overall"], "failed" if exit_code != 0 else "success")
        self.assertEqual(list(report)[-1], "overall", "overall 必须是最后一个键")

    def test_fresh_run_reports_success_and_keeps_status_lines(self):
        root = self.make_root()
        result = self.run_apply(root)
        self.assertEqual(result.returncode, 0, result.stderr)
        report = self.last_report(result.stdout)
        self.assertEqual(report["overall"], "success")
        self.assertEqual(report["counts"]["created"], len(prx.TARGETS))
        self.assertEqual(report["counts"]["needs-rule-config"], len(prx.ENTRY_FILES))
        self.assertEqual(sorted(report["needs_rule_config"]), sorted(prx.ENTRY_FILES))
        self.assertEqual(report["exit_code"], 0)
        self.assertEqual(recipe_report_verdict(result.stdout), "success")
        for rel in PROJECT_RELS:  # 逐行输出保持不变
            self.assertEqual(self.state_of(result.stdout, rel), "created", rel)
        # 铺设分支：action=apply；未设置 CADENCE_SKILL_RUN_ID 时 run_id 为 null
        self.assert_receipt(report, action="apply", exit_code=result.returncode)
        self.assertIsNone(report["run_id"])

    def test_idempotent_rerun_zero_write_reports_success(self):
        root = self.make_root()
        self.write_entries(root)
        self.run_apply(root)
        cadence = root / "cadence"
        before = {str(p): sha(p.read_text(encoding="utf-8")) for p in cadence.rglob("*") if p.is_file()}
        second = self.run_apply(root)
        after = {str(p): sha(p.read_text(encoding="utf-8")) for p in cadence.rglob("*") if p.is_file()}
        self.assertEqual(before, after, "重跑必须零写入")
        self.assertEqual(second.returncode, 0, second.stderr)
        report = self.last_report(second.stdout)
        self.assertEqual(report["overall"], "success")
        self.assertEqual(report["counts"]["pristine"], len(prx.TARGETS))
        self.assertEqual(report["counts"]["skipped"], len(prx.ENTRY_FILES))
        self.assertEqual(report["counts"]["created"] + report["counts"]["merged"], 0)
        self.assertEqual(recipe_report_verdict(second.stdout), "success")
        # 零改动重跑仍属 apply 分支
        self.assert_receipt(report, action="apply", exit_code=second.returncode)

    def write_entries(self, root: Path) -> None:
        for entry in prx.ENTRY_FILES:
            (root / entry).write_text(
                f"# {entry}\n\n## 项目个性化规则\n\n引用 cadence/project-rules/README.md\n",
                encoding="utf-8",
            )

    def test_missing_template_exit_3_reports_failed(self):
        root = self.make_root()
        skill_copy = self.make_root() / "skill"
        shutil.copytree(
            SCRIPTS.parent, skill_copy, ignore=shutil.ignore_patterns("__pycache__", "tests")
        )
        (skill_copy / "references" / "project-rules" / "examples" / "design-template.md").unlink()
        result = subprocess.run(
            [sys.executable, str(skill_copy / "scripts" / "apply.py"), "--project-root", str(root)],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 3, result.stderr)
        report = self.last_report(result.stdout)
        self.assertEqual(report["overall"], "failed")
        self.assertEqual(report["exit_code"], 3)
        self.assertIn("design-template.md", report["failure"]["file"])
        self.assertEqual(recipe_report_verdict(result.stdout), "failed")
        # 失败前已完成的文件仍以逐行状态输出并计入 completed
        self.assertEqual(self.state_of(result.stdout, "README.md"), "created")
        self.assertIn("cadence/project-rules/README.md", report["completed"])
        # 已进入业务的错误仍属 apply 分支，故障描述原样保留
        self.assert_receipt(report, action="apply", exit_code=result.returncode)
        self.assertTrue(report["failure"]["reason"])
        self.assertTrue(report["failure"]["recovery"])

    def test_backup_failure_exit_3_reports_failed_not_traceback(self):
        root = self.make_root()
        rel = "README.md"
        self.write_target(root, rel, drop_section(TEMPLATES[rel], "💡 提示"))
        legacy = root / "cadence" / "legacy"
        legacy.write_text("占位文件使备份目录无法创建", encoding="utf-8")
        result = self.run_apply(root)
        self.assertEqual(result.returncode, 3, result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        report = self.last_report(result.stdout)
        self.assertEqual(report["overall"], "failed")
        self.assertEqual(report["failure"]["file"], "cadence/project-rules/README.md")
        self.assertEqual(recipe_report_verdict(result.stdout), "failed")
        # 备份失败属已进入业务的错误：action 仍为 apply
        self.assert_receipt(report, action="apply", exit_code=result.returncode)

    def test_usage_error_exit_2_reports_failed(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPTS / "apply.py"), "--project-root", "/nonexistent-prx-xyz"],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 2)
        report = self.last_report(result.stdout)
        self.assertEqual(report["overall"], "failed")
        self.assertEqual(report["exit_code"], 2)
        # 根不存在发生在业务分支内：action 仍为 apply，故障描述保留
        self.assert_receipt(report, action="apply", exit_code=result.returncode)
        self.assertIn("项目根不存在", report["failure"]["reason"])

    def test_unknown_flag_exit_2_reports_failed(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPTS / "apply.py"), "--unknown-flag"],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 2)
        report = self.last_report(result.stdout)
        self.assertEqual(report["overall"], "failed")
        # 用法错误无法确定分支：action 为 null
        self.assert_receipt(report, action=None, exit_code=result.returncode)

    def test_help_prints_no_report(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPTS / "apply.py"), "--help"],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 0)
        self.assertNotIn('"overall"', result.stdout)
        # --help 只输出原有帮助，不输出回执
        self.assertIn("usage:", result.stdout)
        self.assertNotIn("cadence.skill-receipt/v1", result.stdout)

    def test_run_id_from_environment(self):
        """run_id：未设置→null；空串→""（算已设置）；特殊字符原样保留。

        末行按 json.dumps 默认 ensure_ascii 转义输出：U+2028/U+0085 不落到实际字符上，
        消费端 splitlines() 仍只看到一行；PYTHONIOENCODING=ascii 下也能回传中文。
        """
        root = self.make_root()
        special = 'run-"x"\\y 空格' + chr(0x2028) + chr(0x0085)
        for value, expected in ((None, None), ("", ""), (special, special)):
            with self.subTest(run_id=value):
                env = {"PYTHONIOENCODING": "ascii"}
                if value is not None:
                    env["CADENCE_SKILL_RUN_ID"] = value
                result = self.run_apply(root, env=env)
                self.assertEqual(result.returncode, 0, result.stderr)
                report = self.last_report(result.stdout)
                self.assertEqual(report["run_id"], expected)

if __name__ == "__main__":
    unittest.main(verbosity=1)
