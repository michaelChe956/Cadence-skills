"""fixture 生成器：四变体 + 临时目录 + 隔离 HOME（eval-pipeline tasks 1.1）。

变体：fresh 全新 / v3 已初始化（含 v3 L0，测升级链）/ mcp_pre 已配
.mcp.json+codegraph（测防重写）/ control 未安装 Cadence 对照组。
fixture 项目在临时目录全新生成，文件内容不含 Cadence 仓库路径（防泄漏）。
P7 探针的截图 assets/error.png 随项目生成（用户提供真报错截图，JPEG 数据、PNG 文件名——Read 按内容嗅探）。
"""
import hashlib
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path

VARIANTS = ("fresh", "v3", "mcp_pre", "control")

# 1x1 灰度 PNG（67 字节，魔数 \x89PNG\r\n\x1a\n）——P7 图片 MCP 探针的确定性占位
# ERROR_PNG_B64 已删除——Docker 容器内动态生成
# rule-config 标准安装清单（fresh 无意图参数）：4 普通规则 + code-usage/code-reading
# 双源单选落地名 + L1 工作流。README.md 是仓库自有文档、playwright.md 是
# 可选规则（意图参数/已存在才装），均不属必断言清单。
RULES_FILES = [
    "code-reading.md", "code-usage.md", "document-storage.md",
    "language.md", "markdown-format.md", "mcp-servers.md",
    "openspec-superpowers-workflow.md",
]

GLOBAL_CONFIG_FILES = (
    ".claude/settings.json", ".claude/CLAUDE.md", ".codex/config.toml",
    ".codex/AGENTS.md", ".pi/agent/settings.json", ".kimi-code/mcp.json",
)


@dataclass
class FixturePaths:
    root: Path   # fixture 项目根
    home: Path   # 隔离 HOME
    repo: Path   # Cadence 检出根（软链源）


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _write_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def _project_files(root: Path, theme: str) -> None:
    """同构小型 coding 工程：entry→service→repo 调用链（P1 探针的检索对象）。"""
    _write(root / "package.json",
           '{"name": "fixture-app", "version": "1.0.0", "scripts": {"test": "jest"}}\n')
    # error.png 由 Docker 容器内动态生成（session.py PROJECT_INIT_SCRIPT）
    _write(root / "src" / theme / "entry.py",
           f"from src.{theme}.service import handle\n\n\ndef main() -> None:\n    handle(payload={{}})\n")
    _write(root / "src" / theme / "service.py",
           f"from src.{theme}.repo import save\n\n\ndef handle(payload: dict) -> None:\n    save(payload)\n")
    _write(root / "src" / theme / "repo.py",
           "def save(payload: dict) -> None:\n    print('saved')\n")
    # P3 探针任务前提：用户表存在（加 last_login_at 列类任务有表可改）
    _write(root / "src" / theme / "schema.sql",
           "CREATE TABLE users (\n"
           "  id INTEGER PRIMARY KEY,\n"
           "  username TEXT NOT NULL,\n"
           "  created_at TEXT NOT NULL\n"
           ");\n")


def _git_init(root: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.email", "eval@fixture.local"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "eval-fixture"], cwd=root, check=True)
    subprocess.run(["git", "add", "-A"], cwd=root, check=True)
    subprocess.run(["git", "commit", "-qm", "fixture init", "--allow-empty"],
                   cwd=root, check=True)


def snapshot_superpowers_state(home: Path) -> dict:
    """快照源、四层软链及非目标条目，供 eval runner/断言消费。"""
    home = Path(home)
    out = {}
    for rel in (".agents/superpowers", ".agents/skills", ".codex/skills/skills",
                ".claude/skills", ".pi/agent/skills"):
        base = home / rel
        if not base.exists() and not base.is_symlink():
            continue
        for p in sorted(base.rglob("*")) if base.is_dir() else []:
            child = p.relative_to(home).as_posix()
            if p.is_symlink():
                out[child] = {"type": "link", "target": str(p.readlink())}
            elif p.is_file():
                out[child] = {"type": "file", "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
    return out


def make_fixture(variant: str, base_dir: Path, repo_root: Path,
                 theme: str = "orders") -> FixturePaths:
    """Docker 容器化后简化版——只创建目录骨架并返回路径。

    完整 fixture（项目文件/1×1 图/预置配置）由 eval/docker/session.py 的
    PROJECT_INIT_SCRIPT 在容器内生成；本函数仅服务旧 runner 的 smoke/
    stage1 命令所需的最小目录契约。
    """
    if variant not in VARIANTS:
        raise ValueError(f"未知 fixture 变体：{variant}")
    root = base_dir / "project"
    home = base_dir / "home"
    root.mkdir(parents=True, exist_ok=True)
    home.mkdir(parents=True, exist_ok=True)
    return FixturePaths(root=root, home=home, repo=repo_root)


def expected_rules_files() -> list:
    return list(RULES_FILES)


def snapshot_global_configs(home: Path) -> dict:
    out = {}
    for rel in GLOBAL_CONFIG_FILES:
        p = home / rel
        if p.is_file():
            out[str(p)] = hashlib.sha256(p.read_bytes()).hexdigest()
    return out


def diff_global_configs(before: dict, after: dict) -> list:
    changed = [p for p, h in after.items() if before.get(p) != h]
    return sorted(changed)
