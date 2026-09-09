"""fake MCP server：time / context7 / 图片（agenteval 先例，E6-9）。

stdio JSON-RPC 最小实现（标准库）：initialize / notifications/initialized /
tools/list / tools/call。种子状态固定；每次 tools/call 追加调用记录到
--log 指定的 jsonl——断言只看该记录与轨迹事件，不触真实网络。
server 名与真实 .mcp.json 一致（time / context7 / zai-mcp-server）。
"""
import argparse
import json
import sys
import time
from pathlib import Path

ROLES = ("time", "context7", "image")
SERVER_NAMES = {"time": "time", "context7": "context7", "image": "zai-mcp-server"}

SEEDS = {
    "time": {"now": "2026-09-02 21:30", "new_york": "2026-09-02 09:30"},
    "context7": {"doc_id": "react-server-components-latest",
                 "summary": "RSC 官方最新用法摘要（种子）"},
    "image": {"analysis": "报错截图分析：依赖冲突（种子）"},
}

TOOLS = {
    "time": [
        {"name": "get_time", "description": "返回种子时间"},
        {"name": "convert_time", "description": "换算目标时区（种子口径）"},
    ],
    "context7": [
        {"name": "resolve-library-id", "description": "解析库名到种子 doc_id"},
        {"name": "get-library-docs", "description": "返回种子文档摘要"},
    ],
    "image": [
        {"name": "analyze_screenshot", "description": "返回种子图片分析"},
    ],
}


def _answer(role: str, tool: str, args: dict) -> str:
    seed = SEEDS[role]
    if role == "time":
        return seed["new_york"] if tool == "convert_time" else seed["now"]
    if role == "context7":
        return seed["summary"] if tool == "get-library-docs" else seed["doc_id"]
    return seed["analysis"]


def serve(role: str, log_path: str) -> None:
    server = SERVER_NAMES[role]
    log_file = Path(log_path)
    log_file.parent.mkdir(parents=True, exist_ok=True)
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except ValueError:
            continue
        method = req.get("method")
        req_id = req.get("id")
        if method == "initialize":
            reply = {"jsonrpc": "2.0", "id": req_id,
                     "result": {"protocolVersion": "2024-11-05",
                                "capabilities": {"tools": {}}}}
        elif method == "tools/list":
            reply = {"jsonrpc": "2.0", "id": req_id,
                     "result": {"tools": TOOLS[role]}}
        elif method == "tools/call":
            params = req.get("params") or {}
            tool = str(params.get("name") or "")
            args = params.get("arguments") or {}
            with log_file.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps({"server": server, "tool": tool,
                                     "args": args, "ts": time.time()},
                                    ensure_ascii=False) + "\n")
            reply = {"jsonrpc": "2.0", "id": req_id,
                     "result": {"content": [{"type": "text",
                                             "text": _answer(role, tool, args)}]}}
        else:
            reply = None  # notifications 或未知方法不回应答
        if reply is not None:
            sys.stdout.write(json.dumps(reply, ensure_ascii=False) + "\n")
            sys.stdout.flush()


def fixture_mcp_config(roles, log_dir: Path) -> dict:
    """生成 .mcp.json 的 mcpServers 片段（stdio 指向本模块）。"""
    servers = {}
    for role in roles:
        server = SERVER_NAMES[role]
        servers[server] = {
            "command": sys.executable, "args": [
                "-m", "eval.mcp.fake_servers", "--role", role,
                "--log", str(Path(log_dir) / f"{server}-calls.jsonl")]}
    return servers


def read_calls(log_dir: Path) -> list:
    calls = []
    for path in sorted(Path(log_dir).glob("*-calls.jsonl")):
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                try:
                    calls.append(json.loads(line))
                except ValueError:
                    continue
    return calls


def main(argv=None):
    parser = argparse.ArgumentParser(description="fake MCP server（eval 专用）")
    parser.add_argument("--role", required=True, choices=list(ROLES))
    parser.add_argument("--log", required=True)
    args = parser.parse_args(argv)
    serve(args.role, args.log)
    return 0


if __name__ == "__main__":
    sys.exit(main())
