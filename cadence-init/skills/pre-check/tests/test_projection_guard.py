"""pre-check 投影保护测试：外部命令覆盖用户投影时归档并报告。

契约（设计 §10 / 计划 Task 6）：
- `openspec init/update` 前后记录投影文件哈希；被外部命令改写且改前内容
  并非本次命令预期内容的文件，改前内容复制到
  `cadence/legacy/<14位时间戳>/<相对路径>`，报告
  `EXTERNAL_PROJECTION_USER_EDIT_OVERWRITTEN`。
- 投影内容未变（幂等）时零归档、零警告。
- guard 自身失败不得阻断 pre-check 主流程，只记录 `PROJECTION_GUARD_FAILED`。
"""

import json
import re
import subprocess
import unittest
from pathlib import Path

from helpers.fixture import SCRIPT, isolated_fixture, run_precheck

WARNING_CODE = "EXTERNAL_PROJECTION_USER_EDIT_OVERWRITTEN"
GUARD_FAILED_CODE = "PROJECTION_GUARD_FAILED"
ARCHIVE_PATTERN = re.compile(r"^cadence/legacy/\d{14}/")

# 覆盖行为由测试用的 openspec 替身按环境变量执行，避免依赖 helpers 中
# 既有 fake-openspec 的 init 语义（本测试只走 ready 分支的 update）。
FAKE_OPENSPEC = """#!/usr/bin/env bash
set -u
if [ "${1:-}" = "--version" ]; then
  printf 'openspec 1.2.0\\n'
  exit 0
fi
if [ "${1:-}" = "update" ] && [ "$#" -eq 1 ]; then
  _target="${FAKE_PROJECTION_OVERWRITE_FILE:-}"
  if [ -n "$_target" ]; then
    mkdir -p "$PWD/$(dirname "$_target")"
    printf '%s' "${FAKE_PROJECTION_OVERWRITE_TEXT:-}" > "$PWD/$_target"
  fi
  exit 0
fi
exit 2
"""


FAKE_OPENSPEC_INIT = """#!/usr/bin/env bash
set -u
_CALLS="${FAKE_OPENSPEC_CALLS:-}"
if [ -n "$_CALLS" ]; then
  printf '%s\\n' "$*" >> "$_CALLS"
fi
if [ "${1:-}" = "--version" ]; then
  printf 'openspec 1.2.0\\n'
  exit 0
fi
if [ "${1:-}" = "init" ] && [ "${2:-}" = "--tools" ]; then
  _target="${FAKE_PROJECTION_OVERWRITE_FILE:-}"
  if [ -n "$_target" ]; then
    printf '%s' "${FAKE_PROJECTION_OVERWRITE_TEXT:-}" > "$PWD/$_target"
  fi
  # 补齐被初始化端，使脚本的四端数量复核通过。
  case ",${3:-}," in
    *,pi,*)
      mkdir -p "$PWD/.pi/skills/openspec-extra"
      printf 'pi filled\\n' > "$PWD/.pi/skills/openspec-extra/SKILL.md" ;;
  esac
  case ",${3:-}," in
    *,kimi,*)
      mkdir -p "$PWD/.kimi-code/skills/openspec-extra"
      printf 'kimi filled\\n' > "$PWD/.kimi-code/skills/openspec-extra/SKILL.md" ;;
  esac
  exit 0
fi
if [ "${1:-}" = "update" ] && [ "$#" -eq 1 ]; then
  exit 0
fi
exit 2
"""


def install_fake_openspec_init(fixture):
    """安装实现 --version/init/update 的 openspec 替身（缺失分支用）。"""
    path = fixture.bin / "openspec"
    path.write_text(FAKE_OPENSPEC_INIT, encoding="utf-8")
    path.chmod(0o755)
    return path


def install_fake_openspec(fixture):
    """安装只实现 --version/update 的 openspec 替身。"""
    path = fixture.bin / "openspec"
    path.write_text(FAKE_OPENSPEC, encoding="utf-8")
    path.chmod(0o755)
    return path


def env_with_overwrite(fixture, rel, text):
    env = fixture.env()
    env["FAKE_PROJECTION_OVERWRITE_FILE"] = rel
    env["FAKE_PROJECTION_OVERWRITE_TEXT"] = text
    return env


def run_with_env(fixture, env, *args):
    proc = subprocess.run(
        ["bash", str(SCRIPT), *args],
        cwd=fixture.project,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        report = json.loads(proc.stdout)
    except json.JSONDecodeError:
        report = {}
    return proc, report


def warnings_with(report, code):
    return [w for w in report.get("warnings", []) if w.get("code") == code]


class TestProjectionGuard(unittest.TestCase):
    def test_overwritten_user_edit_is_archived_and_reported(self):
        """用户在投影上的手改被 openspec update 覆盖 → 归档 + 报告。"""
        rel = ".claude/commands/opsx/propose.md"
        user_text = "# 用户手改的 opsx propose 命令\n"
        canonical_text = "# openspec canonical propose\n"
        with isolated_fixture("openspec-ready") as fx:
            target = fx.project / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(user_text, encoding="utf-8")
            install_fake_openspec(fx)
            env = env_with_overwrite(fx, rel, canonical_text)
            proc, doc = run_with_env(fx, env, "run", "--no-interrupt")

            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertEqual(target.read_text(encoding="utf-8"), canonical_text)

            archives = sorted((fx.project / "cadence" / "legacy").glob("*" + "/" + rel))
            self.assertEqual(len(archives), 1, "覆盖前内容必须归档且只归档一次")
            self.assertEqual(archives[0].read_text(encoding="utf-8"), user_text)
            self.assertRegex(
                archives[0].relative_to(fx.project).as_posix(),
                ARCHIVE_PATTERN.pattern,
            )

            warnings = warnings_with(doc, WARNING_CODE)
            self.assertEqual(len(warnings), 1, doc.get("warnings"))
            self.assertEqual(warnings[0]["path"], rel)
            self.assertRegex(warnings[0]["archive"], ARCHIVE_PATTERN.pattern)
            self.assertEqual(warnings[0]["archive"], archives[0].relative_to(fx.project).as_posix())
            self.assertEqual(doc.get("backups"), [{
                "path": rel,
                "archive": archives[0].relative_to(fx.project).as_posix(),
                "reason": "projection-user-edit-overwritten",
            }])
            # 归档目录按 rule-config 约定忽略全部内容，只保留 .gitignore。
            self.assertEqual(
                (fx.project / "cadence/legacy/.gitignore").read_text(encoding="utf-8"),
                "*\n!.gitignore\n",
            )

    def test_overwritten_nested_skill_projection_is_archived(self):
        """嵌套投影（.pi/skills/openspec-*）同样按相对路径归档。"""
        rel = ".pi/skills/openspec-plan/SKILL.md"
        user_text = "user edited pi skill\n"
        with isolated_fixture("openspec-ready") as fx:
            (fx.project / rel).write_text(user_text, encoding="utf-8")
            install_fake_openspec(fx)
            env = env_with_overwrite(fx, rel, "pi canonical skill\n")
            proc, doc = run_with_env(fx, env, "run", "--no-interrupt")

            self.assertEqual(proc.returncode, 0, proc.stderr)
            archives = sorted((fx.project / "cadence" / "legacy").glob("*" + "/" + rel))
            self.assertEqual(len(archives), 1)
            self.assertEqual(archives[0].read_text(encoding="utf-8"), user_text)
            self.assertEqual(warnings_with(doc, WARNING_CODE)[0]["path"], rel)

    def test_init_branch_overwrite_is_archived(self):
        """缺失分支：openspec init 改写的既有投影同样归档。"""
        rel = ".pi/skills/openspec-execute/SKILL.md"
        user_text = "user edited pi skill before init\n"
        with isolated_fixture("openspec-wrong-pi-count") as fx:
            (fx.project / rel).write_text(user_text, encoding="utf-8")
            install_fake_openspec_init(fx)
            env = env_with_overwrite(fx, rel, "init canonical pi skill\n")
            proc, doc = run_with_env(fx, env, "run", "--no-interrupt")

            self.assertEqual(proc.returncode, 0, proc.stderr)
            calls = fx.calls.read_text(encoding="utf-8")
            self.assertIn("init --tools pi,kimi", calls)
            archives = sorted((fx.project / "cadence" / "legacy").glob("*" + "/" + rel))
            self.assertEqual(len(archives), 1)
            self.assertEqual(archives[0].read_text(encoding="utf-8"), user_text)
            self.assertEqual(warnings_with(doc, WARNING_CODE)[0]["path"], rel)

    def test_unchanged_projection_creates_no_archive(self):
        """幂等：外部命令写回相同内容时零归档、零警告。"""
        rel = ".pi/prompts/opsx-plan.md"
        with isolated_fixture("openspec-ready") as fx:
            current = (fx.project / rel).read_text(encoding="utf-8")
            install_fake_openspec(fx)
            env = env_with_overwrite(fx, rel, current)
            proc, doc = run_with_env(fx, env, "run", "--no-interrupt")

            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertFalse((fx.project / "cadence" / "legacy").exists())
            self.assertEqual(warnings_with(doc, WARNING_CODE), [])
            self.assertEqual(doc.get("backups"), [])

    def test_no_overwrite_creates_no_archive(self):
        """外部命令未改写任何投影时零归档（默认 mock update 为空操作）。"""
        with isolated_fixture("openspec-ready") as fx:
            proc, doc = run_precheck(fx, "run", "--no-interrupt")
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertFalse((fx.project / "cadence").exists())
            self.assertEqual(doc.get("warnings"), [])
            self.assertEqual(doc.get("backups"), [])

    def test_check_mode_does_not_run_guard(self):
        """check 模式不执行外部命令 → 不归档、不警告。"""
        rel = ".claude/commands/opsx/propose.md"
        with isolated_fixture("openspec-ready") as fx:
            target = fx.project / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("user content\n", encoding="utf-8")
            install_fake_openspec(fx)
            env = env_with_overwrite(fx, rel, "canonical\n")
            # check 模式不安装/不改写，普通模式下部分失败仍以 0 结束。
            proc, doc = run_with_env(fx, env, "check")

            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertEqual(target.read_text(encoding="utf-8"), "user content\n")
            self.assertFalse((fx.project / "cadence").exists())
            self.assertEqual(doc.get("warnings"), [])
            self.assertEqual(doc.get("backups"), [])

    def test_guard_failure_does_not_block_precheck(self):
        """归档失败只记录 warning，不阻断主流程。"""
        rel = ".claude/commands/opsx/propose.md"
        with isolated_fixture("openspec-ready") as fx:
            target = fx.project / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("user content\n", encoding="utf-8")
            # 让 cadence/legacy 无法创建：cadence 路径被普通文件占用。
            (fx.project / "cadence").write_text("blocked\n", encoding="utf-8")
            install_fake_openspec(fx)
            env = env_with_overwrite(fx, rel, "canonical\n")
            proc, doc = run_with_env(fx, env, "run", "--no-interrupt")

            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertEqual(target.read_text(encoding="utf-8"), "canonical\n")
            self.assertTrue(warnings_with(doc, GUARD_FAILED_CODE), doc.get("warnings"))
            self.assertEqual(warnings_with(doc, WARNING_CODE), [])
            self.assertEqual(doc.get("backups"), [])


if __name__ == "__main__":
    unittest.main()
