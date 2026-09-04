"""fixture 生成器：四变体 + 临时目录 + 隔离 HOME（eval-pipeline tasks 1.1）。

变体：fresh 全新 / v3 已初始化（含 v3 L0，测升级链）/ mcp_pre 已配
.mcp.json+codegraph（测防重写）/ control 未安装 Cadence 对照组。
fixture 项目在临时目录全新生成，文件内容不含 Cadence 仓库路径（防泄漏）。
P7 探针的截图占位 assets/error.png（1x1 PNG）随项目生成。
"""
import base64
import hashlib
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path

VARIANTS = ("fresh", "v3", "mcp_pre", "control")

# 1x1 灰度 PNG（67 字节，魔数 \x89PNG\r\n\x1a\n）——P7 图片 MCP 探针的确定性占位
ERROR_PNG_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAAAAAA6fptVAAAACklEQVR4nGNoAAAAggCBd81ytg"
    "AAAABJRU5ErkJggg==")

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
    _write_bytes(root / "assets" / "error.png", base64.b64decode(ERROR_PNG_B64))
    _write(root / "src" / theme / "entry.py",
           f"from src.{theme}.service import handle\n\n\ndef main() -> None:\n    handle(payload={{}})\n")
    _write(root / "src" / theme / "service.py",
           f"from src.{theme}.repo import save\n\n\ndef handle(payload: dict) -> None:\n    save(payload)\n")
    _write(root / "src" / theme / "repo.py",
           "def save(payload: dict) -> None:\n    print('saved')\n")


def _git_init(root: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.email", "eval@fixture.local"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "eval-fixture"], cwd=root, check=True)
    subprocess.run(["git", "add", "-A"], cwd=root, check=True)
    subprocess.run(["git", "commit", "-qm", "fixture init", "--allow-empty"],
                   cwd=root, check=True)


def _install_skills(repo_root: Path, home: Path) -> None:
    """复刻 install.sh 三层软链布局（共享层→claude/codex 投影），源指向 Cadence 检出。"""
    shared = home / ".agents" / "skills"
    shared.mkdir(parents=True, exist_ok=True)
    for skill_dir in sorted((repo_root / "cadence-init" / "skills").iterdir()):
        if (skill_dir / "SKILL.md").is_file():
            target = shared / skill_dir.name
            if not target.exists():
                target.symlink_to(skill_dir)
    for layer in (home / ".claude" / "skills", home / ".codex" / "skills" / "skills"):
        layer.mkdir(parents=True, exist_ok=True)
        for entry in sorted(shared.iterdir()):
            link = layer / entry.name
            if not link.exists():
                link.symlink_to(entry)


def make_superpowers_source(home: Path, count: int = 14) -> Path:
    """构造隔离的有效 Superpowers Git work tree，另置非目标 sentinel。"""
    source = Path(home) / ".agents" / "superpowers"
    skills = source / "skills"
    skills.mkdir(parents=True, exist_ok=True)
    for index in range(count):
        _write(skills / f"superpower-{index + 1}" / "SKILL.md", f"# fixture skill {index + 1}\n")
    _write(skills / "knowledge-base-context" / "SKILL.md", "# non-target sentinel\n")
    if not (source / ".git").is_dir():
        _git_init(source)
    remote = source.parent / "superpowers-origin.git"
    if not (remote / "HEAD").is_file():
        subprocess.run(["git", "init", "--bare", "-q", str(remote)], check=True)
    existing_origin = subprocess.run(["git", "remote", "get-url", "origin"], cwd=source,
                                     capture_output=True, text=True).stdout.strip()
    if not existing_origin:
        subprocess.run(["git", "remote", "add", "origin", str(remote)], cwd=source, check=True)
    subprocess.run(["git", "branch", "-M", "main"], cwd=source, check=True)
    subprocess.run(["git", "push", "-q", "-u", "origin", "main"], cwd=source, check=True)
    return source


def make_superpowers_layers(home: Path, source: Path) -> tuple:
    """为四个消费层建立 source 条目的软链，保留非目标 sentinel 不投影。"""
    source = Path(source) / "skills"
    names = [p.name for p in sorted(source.iterdir()) if p.name != "knowledge-base-context"]
    layers = tuple(Path(home) / rel for rel in (
        ".agents/skills", ".codex/skills/skills", ".claude/skills", ".pi/agent/skills"))
    for layer in layers:
        layer.mkdir(parents=True, exist_ok=True)
        for name in names:
            target = layer / name
            if not target.exists() and not target.is_symlink():
                target.symlink_to(source / name)
    return layers


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
                 theme: str = "orders", install: bool = True) -> FixturePaths:
    if variant not in VARIANTS:
        raise ValueError(f"未知 fixture 变体：{variant}")
    if variant == "control":
        install = False  # 对照组定义即未安装
    root = base_dir / "fixture"
    home = base_dir / "home"
    root.parent.mkdir(parents=True, exist_ok=True)
    _project_files(root, theme)
    if variant == "v3":
        v3 = (repo_root / "cadence-init/skills/rule-config/references/rules/l0-history"
              / "agent-routing-kernel-v3.md").read_text(encoding="utf-8")
        _write(root / "CLAUDE.md", v3 + "\n## 团队约定\n\n- 提交前跑 `npm test`。\n")
    elif variant == "mcp_pre":
        _write(root / ".mcp.json", json.dumps({"mcpServers": {
            "existing-server": {"command": "echo", "args": ["hi"]},
            "codegraph": {"command": "codegraph-server", "args": ["stdio"]},
        }}, ensure_ascii=False, indent=2) + "\n")
        _write(root / ".codex" / "config.toml",
               "[mcp_servers.existing-server]\ncommand = \"echo\"\n"
               "args = [\"hi\"]\n\n[mcp_servers.codegraph]\ncommand = \"codegraph-server\"\n")
    _git_init(root)
    if install:
        _install_skills(repo_root, home)
        source = make_superpowers_source(home)
        make_superpowers_layers(home, source)
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
