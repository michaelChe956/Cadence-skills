"""适配器注册表：新增端=新增适配器文件+在此注册。"""
from eval.adapters.base import AGENTS, AgentAdapter, args_digest, normalize_tool


def get_adapter(name: str) -> AgentAdapter:
    if name == "claude":
        from eval.adapters.claude import ClaudeAdapter
        return ClaudeAdapter()
    if name == "codex":
        from eval.adapters.codex import CodexAdapter
        return CodexAdapter()
    if name == "pi":
        from eval.adapters.pi import PiAdapter
        return PiAdapter()
    if name == "kimi":
        from eval.adapters.kimi import KimiAdapter
        return KimiAdapter()
    raise ValueError(f"未知端：{name}")
