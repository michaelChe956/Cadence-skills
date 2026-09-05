"""capture-baseline.sh 的 git 版本门禁测试。"""
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[4]
SOURCE_SCRIPT = Path(__file__).resolve().parent / "helpers" / "capture-baseline.sh"


class TestCaptureBaselineGitVersion(unittest.TestCase):
    def _sandbox_script(self, root: Path) -> Path:
        """复制采集器及其相对资源，避免测试触碰冻结基线目录。"""
        tests_dir = root / "tests"
        helper_dir = tests_dir / "helpers"
        helper_dir.mkdir(parents=True)
        script = helper_dir / SOURCE_SCRIPT.name
        shutil.copy2(SOURCE_SCRIPT, script)
        shutil.copytree(
            REPO_ROOT / "cadence-init/skills/pre-check/scripts/mirrors",
            root / "scripts/mirrors",
        )
        shutil.copy2(
            REPO_ROOT / "cadence-init/skills/pre-check/SKILL.md",
            root / "SKILL.md",
        )
        return script

    def _run_with_fake_git(self, version: str, version_rc: int = 0):
        with tempfile.TemporaryDirectory(prefix="capture-baseline-test-") as td:
            root = Path(td)
            script = self._sandbox_script(root)
            fake_bin = root / "bin"
            fake_bin.mkdir()
            call_log = root / "git-calls.log"
            fake_git = fake_bin / "git"
            fake_git.write_text(
                "#!/bin/sh\n"
                "printf '%s\\n' \"$*\" >> \"$FAKE_GIT_LOG\"\n"
                "if [ \"${1:-}\" = \"--version\" ]; then\n"
                "  printf '%s\\n' \"$FAKE_GIT_VERSION\"\n"
                "  exit \"$FAKE_GIT_VERSION_RC\"\n"
                "fi\n"
                "exit 0\n",
                encoding="utf-8",
            )
            fake_git.chmod(0o755)
            env = os.environ.copy()
            env["PATH"] = str(fake_bin) + os.pathsep + env.get("PATH", "")
            env["FAKE_GIT_LOG"] = str(call_log)
            env["FAKE_GIT_VERSION"] = version
            env["FAKE_GIT_VERSION_RC"] = str(version_rc)
            proc = subprocess.run(
                ["bash", str(script)],
                cwd=str(REPO_ROOT),
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            return {
                "returncode": proc.returncode,
                "stdout": proc.stdout,
                "stderr": proc.stderr,
                "git_calls": call_log.read_text(encoding="utf-8").splitlines()
                if call_log.exists() else [],
                "baseline_exists": (root / "tests/baselines/precheck-v2").exists(),
            }

    def test_old_git_fails_before_creating_baseline_output(self):
        result = self._run_with_fake_git("git version 2.21.0")

        self.assertEqual(result["returncode"], 2)
        self.assertIn("2.22", result["stderr"])
        self.assertRegex(result["stderr"], r"git.*版本|版本.*git")
        self.assertFalse(result["baseline_exists"])
        self.assertEqual(result["git_calls"], ["--version"])

    def _run_without_git(self):
        with tempfile.TemporaryDirectory(prefix="capture-baseline-test-") as td:
            root = Path(td)
            script = self._sandbox_script(root)
            fake_bin = root / "bin"
            fake_bin.mkdir()
            for command in ("dirname", "mktemp", "rm", "sed", "awk"):
                command_path = shutil.which(command)
                self.assertIsNotNone(command_path, f"测试依赖命令不可用：{command}")
                (fake_bin / command).symlink_to(command_path)
            env = os.environ.copy()
            env["PATH"] = str(fake_bin)
            proc = subprocess.run(
                ["/bin/bash", str(script)],
                cwd=str(REPO_ROOT),
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            return {
                "returncode": proc.returncode,
                "stdout": proc.stdout,
                "stderr": proc.stderr,
                "git_calls": [],
                "baseline_exists": (root / "tests/baselines/precheck-v2").exists(),
            }

    def test_missing_git_fails_closed_before_creating_baseline_output(self):
        result = self._run_without_git()

        self.assertEqual(result["returncode"], 2)
        self.assertIn("错误：", result["stderr"])
        self.assertIn("git", result["stderr"])
        self.assertIn("2.22", result["stderr"])
        self.assertFalse(result["baseline_exists"])
        self.assertEqual(result["git_calls"], [])

    def test_unparseable_git_version_fails_closed_before_creating_baseline_output(self):
        result = self._run_with_fake_git("git version unknown-dev")

        self.assertEqual(result["returncode"], 2)
        self.assertIn("错误：", result["stderr"])
        self.assertIn("git", result["stderr"])
        self.assertIn("2.22", result["stderr"])
        self.assertFalse(result["baseline_exists"])
        self.assertEqual(result["git_calls"], ["--version"])

    def test_parseable_git_version_command_failure_is_rejected(self):
        result = self._run_with_fake_git("git version 2.30.0", version_rc=1)

        self.assertEqual(result["returncode"], 2)
        self.assertIn("错误：", result["stderr"])
        self.assertIn("git", result["stderr"])
        self.assertIn("2.22", result["stderr"])
        self.assertEqual(result["git_calls"], ["--version"])
        self.assertFalse(result["baseline_exists"])

    def test_supported_real_git_is_not_rejected_by_version_gate(self):
        with tempfile.TemporaryDirectory(prefix="capture-baseline-test-") as td:
            root = Path(td)
            script = self._sandbox_script(root)
            proc = subprocess.run(
                ["bash", str(script)],
                cwd=str(REPO_ROOT),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertNotIn("需要 git >= 2.22", proc.stderr)
            self.assertTrue((root / "tests/baselines/precheck-v2").exists())


if __name__ == "__main__":
    unittest.main()
