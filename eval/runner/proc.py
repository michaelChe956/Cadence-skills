"""四端 CLI 调用封装：env 注入 prompt、HOME 覆写、超时与轨迹捕获。"""
import json
import os
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Optional

PROMPT_ENV = "EVAL_PROMPT"

INVOCATIONS = {
    "claude": {
        "argv": ["claude", "-p", "{prompt}", "--output-format", "stream-json",
                 "--verbose", "--model", "{model}", "--max-turns", "{turns}"],
        "capture": "stdout",
    },
    "codex": {
        # -s danger-full-access：对齐 claude 的全放行语义（用户已拍板）——
        # read-only 沙箱下 HOME（cwd 外）不可写，HOME 隔离端安装流水线
        # （pi install 等写 $HOME）会全部失败
        "argv": ["codex", "exec", "--json", "-s", "danger-full-access",
                 "--model", "{model}", "{prompt}"],
        "capture": "stdout",
    },
    "pi": {"argv": ["pi", "-p", "{prompt}", "--model", "{model}"], "capture": "session"},
    "kimi": {"argv": ["kimi", "-p", "{prompt}", "--model", "{model}"], "capture": "session"},
}

# 各端配置重定向（skill_env）同时会带走凭证目录——真实模式需把真实凭证
# 符号链接进 fixture 配置目录（本体不动，temp 清理自动回收）。
# AUTH_LINKS 已删除——Docker 容器化后不再需要假 HOME 链入
UTH_LINKS = {
    "claude": [(".claude/settings.json", ".claude/settings.json"),
               (".claude/.credentials.json", ".claude/.credentials.json")],
    "codex": [(".codex/auth.json", ".codex/auth.json"),
              (".codex/config.toml", ".codex/config.toml"),
              (".codex/models.json", ".codex/models.json"),
              (".gitconfig", ".gitconfig")],
    "pi": [(".pi/agent/auth.json", ".pi/agent/auth.json"),
           (".pi/agent/settings.json", ".pi/agent/settings.json"),
           (".pi/agent/models.json", ".pi/agent/models.json"),
           # pi 首启 bootstrap 缓存（必需，否则首启崩溃）：pi 按 settings.json 的
           # packages 清单把扩展物化到 HOME 下这两个目录（npm install ×3 + git
           # clone）。fixture HOME 为空时每次首启都重跑，顺利也要 26~40s；网络
           # 失败则抛未捕获 Node 异常、rc=1 退出，stdout 全空且 session 文件
           # 根本没创建——正是夜测 pre-check/mcp-configuration 的失败签名。
           # 目录源一律复制（见 link_agent_auth）：软链会让 pi install 写穿宿主。
           (".pi/agent/npm", ".pi/agent/npm"),
           (".pi/agent/git", ".pi/agent/git"),
           (".gitconfig", ".gitconfig")],
    "kimi": [(".kimi-code/credentials", ".kimi-code/credentials")],
}


# link_agent_auth 已删除——Docker 容器化后不再需要
DEFAULT_TURNS = 40

# 会话文件定位模式（transcript 捕获为 session 型的端）——从假 HOME 清理中恢复
SESSION_PATTERNS = {
    "pi": [".pi/agent/sessions/**/run-*/session.jsonl",
           ".pi/agent/sessions/**/*.jsonl"],
    "kimi": [".kimi-code/sessions/**/agents/*/wire.jsonl"],
}


def link_agent_auth(agent, fixture):
    """已废弃 no-op：Docker 容器化后认证由容器 copy_in 注入，无需假 HOME 链入。"""


def build_argv(agent, model, max_turns=None, prompt="", prompt_env=PROMPT_ENV):
    """按端模板组装 argv；prompt 作为单独参数传入，不内联 shell。

    显式传入的非空 prompt 优先；未传入时才回退读取环境变量，以兼容
    直接调用 build_argv 的旧用法。
    """
    template = list(INVOCATIONS[agent]["argv"])
    prompt = prompt if prompt else os.environ.get(prompt_env, "")
    fills = {"{prompt}": prompt, "{model}": model,
             "{turns}": str(max_turns if max_turns is not None else DEFAULT_TURNS)}
    argv = []
    skip_next = False
    for part in template:
        if skip_next:
            skip_next = False
            continue
        # 空模型时不传 --model {model}（用 CLI 默认配置）
        if not fills["{model}"] and part == "--model":
            skip_next = True
            continue
        for key, value in fills.items():
            if key in part:
                part = part.replace(key, value)
        argv.append(part)
    return argv


def _scan_sessions(root: Path, patterns: list) -> dict:
    """按 patterns 扫描 root 下的候选 session 文件，返回 {path: mtime}。"""
    found = {}
    for pattern in patterns:
        for path in root.glob(pattern):
            try:
                found[path] = path.stat().st_mtime
            except OSError:
                continue
    return found


def _pick_new_session(before: dict, after: dict) -> Optional[Path]:
    """从前后两次扫描中选出本次调用新建或被追写的最新 session。

    旧实现用 ``mtime >= started - 1`` 时间窗，反向宽放 1 秒会把上一轮
    （阶段一或上一个探针）刚写完的会话误归为本次轨迹——r5 实测
    P1-installed-0 就是这样拿到阶段一收尾会话。改为前后快照差分后，
    归属只依赖文件自身是否在本次调用期间发生变化。
    """
    best, best_mt = None, -1.0
    for path, mtime in after.items():
        if path in before and mtime <= before[path]:
            continue  # 本次调用未动过的旧会话
        if mtime > best_mt:
            best, best_mt = path, mtime
    return best


def _find_newest(home: Path, patterns: list, since_ts: float) -> Optional[Path]:
    best, best_mt = None, -1.0
    for path, mtime in _scan_sessions(Path(home), patterns).items():
        if mtime >= since_ts and mtime > best_mt:
            best, best_mt = path, mtime
    return best


def effective_home(home, skill_env=None, env=None) -> Path:
    """返回实际继承的 HOME；home 非 None 时由调用方覆写。"""
    if home is not None:
        return Path(home)
    environ = os.environ if env is None else env
    return Path(environ.get("HOME") or Path.home())


def run_cli(agent, prompt, cwd, home, pins, timeout_s, env_extra=None,
            bin_dir=None, out_dir=None, skill_env=None, session_root=None,
            argv_extra=None):
    """执行一次端调用并捕获轨迹。返回 dict（见 Interfaces）。

    ``argv_extra`` 会追加到 ``build_argv`` 生成的 argv 末尾，用于真实模式按
    调用目的附加权限参数；mock 模式可忽略此参数。

    env 注入：EVAL_PROMPT 由本函数写入子进程 env；PATH 前置 bin_dir（mock 模式）。
    HOME 策略：home 非 None 时覆写 HOME（mock/隔离模式）；home=None 时不覆写
    （真实 HOME，登录态可用），并以 skill_env 注入 skill 发现路径（b 方案）。
    session 搜索根（capture=session 的 pi/kimi）：home 非 None 时即 home；
    home=None 且 skill_env 注入（真实模式）时用 session_root——调用方传
    fixture.home（skill_env 已把 config-dir 重定向到 fixture 根，session
    落其下，SESSION_PATTERNS 相对路径可命中）；仅 home=None 且未传
    session_root（mock 冒烟语义）才跳过定位。归属取调用前后两次目录
    快照的差分（新建或 mtime 变大的文件），不用壁钟时间窗。
    stdout 捕获文件写入 out_dir（缺省系统临时目录），不落 fixture 根。
    shell=False + 列表 argv，杜绝 shell 展开污染。
    """
    env = dict(os.environ)
    actual_home = effective_home(home, env=env)
    if home is not None:
        env["HOME"] = str(actual_home)
    if skill_env:
        env.update({k: str(v) for k, v in skill_env.items()})
    env[PROMPT_ENV] = prompt
    if env_extra:
        env.update({k: str(v) for k, v in env_extra.items()})
    if bin_dir is not None:
        env["PATH"] = str(bin_dir) + os.pathsep + env.get("PATH", "")
    argv = build_argv(agent, pins.get("pinned_model", ""), pins.get("max_turns"),
                      prompt=env[PROMPT_ENV])
    if argv_extra:
        argv.extend(argv_extra)
    started = time.time()
    capture_dir = Path(out_dir) if out_dir is not None else Path(tempfile.gettempdir())
    capture_dir.mkdir(parents=True, exist_ok=True)
    stdout_file = capture_dir / f".eval-{agent}-{os.getpid()}-{int(started * 1000)}-stdout.jsonl"
    # session 定位根与启动前快照（必须在 Popen 之前取，才能做前后差分）
    _session_root = home if home is not None else session_root
    _sessions_before = (
        _scan_sessions(Path(_session_root), SESSION_PATTERNS[agent])
        if INVOCATIONS[agent]["capture"] == "session" and _session_root is not None
        else None)
    proc = subprocess.Popen(
        argv, cwd=str(cwd), env=env, shell=False,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.DEVNULL,
        start_new_session=True)  # 独立进程组：超时可整组 kill，防 CLI 孙进程成孤儿空转
    try:
        out, err = proc.communicate(timeout=timeout_s)
        returncode, timed_out = proc.returncode, False
    except subprocess.TimeoutExpired:
        import signal
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)  # 整组清杀（孙进程不留）
        except (ProcessLookupError, PermissionError):
            proc.kill()
        out, err = proc.communicate()
        returncode, timed_out = -9, True
    duration = time.time() - started
    stdout_file.write_bytes(out or b"")
    transcript = str(stdout_file)
    if INVOCATIONS[agent]["capture"] == "session":
        found = (_pick_new_session(
            _sessions_before,
            _scan_sessions(Path(_session_root), SESSION_PATTERNS[agent]))
            if _sessions_before is not None else None)
        if found is None:
            found = stdout_file  # mock/兜底：未定位到 session 文件时回退 stdout 捕获
        transcript = str(found)
    return {"returncode": returncode, "stdout_path": str(stdout_file),
            "stderr": (err or b"").decode("utf-8", "replace")[-2000:],
            "duration_s": duration, "transcript_path": transcript,
            "timed_out": timed_out, "actual_home": str(actual_home)}


def cli_version_check(agent, pins, bin_dir=None):
    """CLI 版本锁核验：pins['cli_version'] 非空才强制（空=只记录不锁，Task 20 固化）。"""
    locked = (pins or {}).get("cli_version") or ""
    if not locked:
        return True, ""
    env = dict(os.environ)
    if bin_dir is not None:
        env["PATH"] = str(bin_dir) + os.pathsep + env.get("PATH", "")
    try:
        out = subprocess.run([INVOCATIONS[agent]["argv"][0], "--version"],
                             capture_output=True, text=True, timeout=30, env=env,
                             shell=False).stdout
    except (OSError, subprocess.TimeoutExpired) as exc:
        return False, f"version-check-failed: {exc}"
    ok = locked in out
    return ok, "" if ok else f"cli 版本漂移：期望含 {locked}，实际 {out.strip()[:80]}"


def extract_final_text(agent, transcript_path):
    """阶段一轻量终文本：claude/mock 轨迹取 result.result；其余取最后一条 assistant 文本。

    仅供断言表消费（"诊断报告产出"类弱断言）；判分权威是组 2 适配器。
    mock 轨迹与 claude stream-json 同构（含 result 行）；真实 codex/pi/kimi
    轨迹无 result 行，故对所有端接受 result 行均无副作用。
    """
    if not transcript_path:
        return ""
    try:
        with open(transcript_path, encoding="utf-8", errors="replace") as fh:
            lines = [ln for ln in fh.read().splitlines() if ln.strip()]
    except OSError:
        return ""
    final = ""
    for ln in lines:
        try:
            d = json.loads(ln)
        except ValueError:
            continue
        # codex stdout 流：{"type":"item.completed","item":{"type":"agent_message","text":...}}
        if (d.get("type") == "item.completed"
                and isinstance(d.get("item"), dict)
                and d["item"].get("type") == "agent_message"
                and isinstance(d["item"].get("text"), str)):
            final = d["item"]["text"]
            continue
        if d.get("type") == "result" and isinstance(d.get("result"), str):
            final = d["result"]
        elif isinstance(d.get("message"), dict):
            content = d["message"].get("content")
            if isinstance(content, list):
                texts = [c.get("text", "") for c in content
                         if isinstance(c, dict) and c.get("type") == "text"]
                if texts:
                    final = "\n".join(t for t in texts if t)
    return final
