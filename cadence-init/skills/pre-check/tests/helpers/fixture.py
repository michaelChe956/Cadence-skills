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

    def __init__(self, root: Path):
        self.root = root
        self.project = root / "project"
        self.home = root / "home"
        self.bin = root / "bin"
        self.project.mkdir()
        self.home.mkdir()
        shutil.copytree(FAKE_BIN, self.bin)
        for path in self.bin.iterdir():
            path.chmod(path.stat().st_mode | 0o111)

    def env(self):
        env = os.environ.copy()
        env["HOME"] = str(self.home)
        env["PATH"] = str(self.bin) + os.pathsep + env.get("PATH", "")
        return env


@contextlib.contextmanager
def isolated_fixture(_name=None):
    """创建仓外临时 fixture；name 为未来负向 fixture 预留。"""
    with tempfile.TemporaryDirectory(prefix="precheck-fixture-") as td:
        root = Path(td)
        yield Fixture(root)


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
    """通过独立 bash shell 执行，验证 cwd/HOME/PATH 不依赖调用方状态。"""
    command = 'cd "$1" && shift && exec bash "$@"'
    proc = subprocess.run(
        ["bash", "-c", command, "pre-check", str(fixture.project), str(SCRIPT), *args],
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
