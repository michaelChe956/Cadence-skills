"""四端 CLI 调用封装：env 注入 prompt、HOME 覆写、超时与轨迹捕获。"""
import json
import os
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Optional

INVOCATIONS = {
    "claude": {
        "argv": ["claude", "-p", "{prompt}", "--output-format", "stream-json",
                 "--verbose", "--model", "{model}", "--max-turns", "{turns}"],
        "capture": "stdout",
    },
    "codex": {
        "argv": ["codex", "exec", "--json", "--model", "{model}", "{prompt}"],
        "capture": "stdout",
    },
    "pi": {"argv": ["pi", "-p", "{prompt}", "--model", "{model}"], "capture": "session"},
    "kimi": {"argv": ["kimi", "-p", "{prompt}", "--model", "{model}"], "capture": "session"},
}

# 各端配置重定向（skill_env）同时会带走凭证目录——真实模式需把真实凭证
# 符号链接进 fixture 配置目录（本体不动，temp 清理自动回收）。
AUTH_LINKS = {
    "claude": [(".claude/settings.json", ".claude/settings.json"),
               (".claude/.credentials.json", ".claude/.credentials.json")],
    "codex": [(".codex/auth.json", ".codex/auth.json")],
    "pi": [(".pi/agent/auth.json", ".pi/agent/auth.json")],
    "kimi": [(".kimi-code/credentials", ".kimi-code/credentials"),
             (".kimi-code/oauth", ".kimi-code/oauth")],
}


def link_agent_auth(agent: str, fixture) -> int:
    """把真实 HOME 的凭证文件软链进 fixture 隔离目录；返回成功链接数。

    源文件不存在时跳过（该端可能未登录或路径名有出入——首夜 Runbook 核定项）。
    """
    import os
    linked = 0
    for rel_src, rel_dst in AUTH_LINKS.get(agent, []):
        src = Path.home() / rel_src
        dst = Path(fixture.home) / rel_dst
        if not src.is_file():
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        if dst.exists() or dst.is_symlink():
            continue
        os.symlink(src, dst)
        linked += 1
    return linked


DEFAULT_TURNS = 40
PROMPT_ENV = "EVAL_PROMPT"

SESSION_PATTERNS = {
    "pi": [".pi/agent/sessions/**/run-*/session.jsonl"],
    "kimi": [".kimi-code/sessions/**/agents/*/wire.jsonl"],
}


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
    for part in template:
        for key, value in fills.items():
            if key in part:
                part = part.replace(key, value)
        argv.append(part)
    return argv


def _find_newest(home: Path, patterns: list, since_ts: float) -> Optional[Path]:
    best, best_mt = None, -1.0
    for pattern in patterns:
        for p in home.glob(pattern):
            try:
                mt = p.stat().st_mtime
            except OSError:
                continue
            if mt >= since_ts and mt > best_mt:
                best, best_mt = p, mt
    return best


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
    session_root（mock 冒烟语义）才跳过定位。
    stdout 捕获文件写入 out_dir（缺省系统临时目录），不落 fixture 根。
    shell=False + 列表 argv，杜绝 shell 展开污染。
    """
    env = dict(os.environ)
    if home is not None:
        env["HOME"] = str(home)
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
    proc = subprocess.Popen(
        argv, cwd=str(cwd), env=env, shell=False,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.DEVNULL)
    try:
        out, err = proc.communicate(timeout=timeout_s)
        returncode, timed_out = proc.returncode, False
    except subprocess.TimeoutExpired:
        proc.kill()
        out, err = proc.communicate()
        returncode, timed_out = -9, True
    duration = time.time() - started
    stdout_file.write_bytes(out or b"")
    transcript = str(stdout_file)
    if INVOCATIONS[agent]["capture"] == "session":
        search_root = home if home is not None else session_root
        found = (_find_newest(Path(search_root), SESSION_PATTERNS[agent], started - 1)
                 if search_root is not None else None)
        if found is None:
            found = stdout_file  # mock/兜底：未定位到 session 文件时回退 stdout 捕获
        transcript = str(found)
    return {"returncode": returncode, "stdout_path": str(stdout_file),
            "stderr": (err or b"").decode("utf-8", "replace")[-2000:],
            "duration_s": duration, "transcript_path": transcript,
            "timed_out": timed_out}


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
