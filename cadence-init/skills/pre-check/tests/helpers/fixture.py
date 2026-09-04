"""pre-check 隔离 fixture、运行器和快照辅助函数。"""
import contextlib
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

TEST_DIR = Path(__file__).resolve().parents[1]
SCRIPT = TEST_DIR.parent / "scripts" / "pre-check.sh"
FAKE_BIN = Path(__file__).resolve().parent / "fake-bin"


class Fixture:
    """封装一次隔离项目、HOME 和 fake 命令目录。"""

    def __init__(self, root: Path, fixture_name=None):
        self.root = root
        self.project = root / "project"
        self.home = root / "home"
        self.bin = root / "bin"
        self.project.mkdir()
        self.home.mkdir()
        shutil.copytree(FAKE_BIN, self.bin)
        fake_openspec = TEST_DIR / "helpers" / "fake-openspec.sh"
        if fake_openspec.exists():
            shutil.copy2(fake_openspec, self.bin / "openspec")
        fake_git = TEST_DIR / "helpers" / "fake-git.sh"
        if fake_git.exists():
            shutil.copy2(fake_git, self.bin / "git")
        fake_timeout = TEST_DIR / "helpers" / "fake-timeout.sh"
        if fake_timeout.exists() and fixture_name != "superpowers-timeout":
            shutil.copy2(fake_timeout, self.bin / "timeout")
        if fixture_name == "base-tools-failure":
            shutil.copy2(TEST_DIR / "helpers" / "fake-failing-tool.sh", self.bin / "npx")
        for path in self.bin.iterdir():
            path.chmod(path.stat().st_mode | 0o111)
        self.calls = root / "calls"
        self.calls.touch()
        self.git_args = root / "git-args"
        self.git_args.touch()
        self.tmp = root / "tmp"
        self.tmp.mkdir()
        self.fixture_name = fixture_name
        self._prepare_git_fixture(fixture_name)
        self._prepare_openspec_fixture(fixture_name)

    def _prepare_git_fixture(self, fixture_name):
        """创建本地 bare 源，并按 fixture 覆盖 Superpowers 目录/候选。"""
        self.git_source = self.root / "superpowers-source.git"
        worktree = self.root / "superpowers-worktree"
        subprocess.run(["git", "init", "--bare", "-q", str(self.git_source)], check=True)
        subprocess.run(["git", "init", "-q", "-b", "main", str(worktree)], check=True)
        subprocess.run(["git", "-C", str(worktree), "config", "user.email", "fixture@example.invalid"], check=True)
        subprocess.run(["git", "-C", str(worktree), "config", "user.name", "fixture"], check=True)
        (worktree / "skills").mkdir(parents=True)
        (worktree / "skills" / "README.md").write_text("fixture superpowers\\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(worktree), "add", "skills"], check=True)
        subprocess.run(["git", "-C", str(worktree), "commit", "-qm", "fixture superpowers"], check=True)
        subprocess.run(["git", "-C", str(worktree), "remote", "add", "origin", str(self.git_source)], check=True)
        subprocess.run(["git", "-C", str(worktree), "push", "-q", "-u", "origin", "main"], check=True)
        subprocess.run(["git", "--git-dir", str(self.git_source), "symbolic-ref", "HEAD", "refs/heads/main"], check=True)

        target = self.home / ".agents" / "superpowers"
        if fixture_name == "superpowers-non-git":
            target.mkdir(parents=True)
            (target / "not-git.txt").write_text("not a repository\\n", encoding="utf-8")
        elif fixture_name != "superpowers-source-missing":
            # 让默认 fixture 覆盖更新路径；clone fixture 通过删除该目录进入冷启动路径。
            if fixture_name not in ("superpowers-timeout", "superpowers-zsh-multiple-candidates"):
                shutil.copytree(worktree, target)

        if fixture_name in {
            "links-correct", "links-correct-direct", "links-correct-layered",
            "links-non-symlink-conflict", "links-pi-missing-cadence",
        }:
            # 链接 fixture 使用 14 个动态 Superpowers 条目，避免实现依赖固定总数。
            shutil.rmtree(target / "skills")
            (target / "skills").mkdir()
            for index in range(1, 15):
                (target / "skills" / ("skill-%02d" % index)).mkdir()
            agents_layer = self.home / ".agents" / "skills"
            codex_layer = self.home / ".codex" / "skills" / "skills"
            claude_layer = self.home / ".claude" / "skills"
            pi_layer = self.home / ".pi" / "agent" / "skills"
            layers = (agents_layer, codex_layer, claude_layer, pi_layer)
            for layer in layers:
                layer.mkdir(parents=True)
            if fixture_name == "links-non-symlink-conflict":
                (agents_layer / "skill-01").write_text("sentinel\n", encoding="utf-8")
                for name in ("skill-02", "skill-03"):
                    (agents_layer / name).symlink_to(target / "skills" / name)
            else:
                for name in ("skill-01", "skill-02", "skill-03", "skill-04", "skill-05", "skill-06", "skill-07", "skill-08", "skill-09", "skill-10", "skill-11", "skill-12", "skill-13", "skill-14"):
                    (agents_layer / name).symlink_to(target / "skills" / name)
                    if fixture_name == "links-correct-layered":
                        for layer in (codex_layer, claude_layer, pi_layer):
                            (layer / name).symlink_to(agents_layer / name)
                    else:
                        for layer in (codex_layer, claude_layer, pi_layer):
                            (layer / name).symlink_to(target / "skills" / name)
            if fixture_name == "links-correct":
                (agents_layer / "third-party").mkdir()
                (agents_layer / "third-party" / "KEEP").write_text("user\n", encoding="utf-8")
            elif fixture_name == "links-pi-missing-cadence":
                for layer in (agents_layer, codex_layer, claude_layer):
                    (layer / "cadence-init").mkdir()
                    (layer / "cadence-init" / "SKILL.md").write_text("cadence\n", encoding="utf-8")


    def _prepare_openspec_fixture(self, fixture_name):
        """按名称复制 OpenSpec 投影 fixture；默认 fixture 为四端齐全。"""
        template = (
            TEST_DIR / "fixtures" / fixture_name / "project"
            if fixture_name
            else None
        )
        if template is not None and template.is_dir():
            for source in template.iterdir():
                destination = self.project / source.name
                if source.is_dir():
                    shutil.copytree(source, destination)
                else:
                    shutil.copy2(source, destination)
        self.project.joinpath("project-sentinel.txt").touch()

    def env(self):
        env = os.environ.copy()
        env["HOME"] = str(self.home)
        env["PATH"] = str(self.bin) + os.pathsep + env.get("PATH", "")
        env["FAKE_OPENSPEC_CALLS"] = str(self.calls)
        env["FAKE_GIT_ARGS"] = str(self.git_args)
        env["FAKE_GIT_CLONE_SOURCE"] = "file://" + str(self.git_source)
        env["CADENCE_TEST_GIT_CANDIDATES"] = str(self.git_source)
        if self.fixture_name == "superpowers-source-missing":
            env["CADENCE_TEST_GIT_CANDIDATES"] = "one two three"
            env["FAKE_GIT_FAIL"] = "clone"
        elif self.fixture_name == "superpowers-zsh-multiple-candidates":
            env["CADENCE_TEST_GIT_CANDIDATES"] = "one two"
            env["FAKE_GIT_FAIL"] = "clone"
        elif self.fixture_name == "superpowers-timeout":
            env["FAKE_GIT_BLOCK"] = "clone"
            env["FAKE_GIT_BLOCK_SECONDS"] = "300"
            env["CADENCE_TEST_GIT_PHASE_BUDGET_S"] = "5"
        env["REAL_GIT"] = shutil.which("git") or "/usr/bin/git"
        env["TMPDIR"] = str(self.tmp)
        env["FAKE_TIMEOUT_LOG"] = str(self.root / "timeouts")
        return env


@contextlib.contextmanager
def isolated_fixture(_name=None):
    """创建仓外临时 fixture；名称选择预置 OpenSpec 投影状态。"""
    with tempfile.TemporaryDirectory(prefix="precheck-fixture-") as td:
        root = Path(td)
        yield Fixture(root, _name)


def run_precheck(fixture, *args):
    """在隔离项目根执行 pre-check，返回 (CompletedProcess, JSON 报告)。"""
    proc = subprocess.run(
        ["bash", str(SCRIPT), *args],
        cwd=fixture.project,
        env=fixture.env(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        report = json.loads(proc.stdout)
    except json.JSONDecodeError:
        report = {}
    return proc, report


def run_precheck_under_shell(fixture, *args):
    """通过指定 shell 执行，验证外层 shell 不参与候选参数拼接。"""
    shell = "bash"
    if args and args[0] in {"bash", "zsh", "sh"}:
        shell, args = args[0], args[1:]
    command = 'cd "$1" && shift && exec bash "$@"'
    proc = subprocess.run(
        [shell, "-c", command, "pre-check", str(fixture.project), str(SCRIPT), *args],
        cwd=fixture.root,
        env=fixture.env(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        report = json.loads(proc.stdout)
    except json.JSONDecodeError:
        report = {}
    return proc, report


def normalize_snapshot_text(text: str, isolation_root) -> str:
    """将随机隔离根转换为 Task 8 稳定占位符后再做文本 diff。"""
    root = str(isolation_root)
    return text.replace(root, "<ISOLATION_ROOT>")


def normalize_snapshot_file(source, destination, isolation_root):
    """规范化快照文件，供基线与新实现对照复用。"""
    source_text = Path(source).read_text(encoding="utf-8")
    Path(destination).write_text(
        normalize_snapshot_text(source_text, isolation_root),
        encoding="utf-8",
    )


def phase_by_name(report, name):
    """按固定 phase 名称选择报告项。"""
    return next(phase for phase in report["phases"] if phase["phase"] == name)


def snapshot_tree(root):
    """返回不含 .git 的确定性文件/软链快照，供幂等测试比较。"""
    root = Path(root)
    snapshot = {}
    for path in sorted(root.rglob("*")):
        rel = path.relative_to(root).as_posix()
        if rel == ".git" or rel.startswith(".git/"):
            continue
        if path.is_symlink():
            snapshot[rel] = "link:" + os.readlink(path)
        elif path.is_file():
            snapshot[rel] = hashlib.sha256(path.read_bytes()).hexdigest()
    return snapshot
