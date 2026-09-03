"""8 探针定义：prompt 题库变体（轮换）+ 断言 spec + 条款 ID 绑定（与 p1 元数据同源）。

断言 kind 集合与 eval/scoring/assertor.py 的 _check_assertion 一一对应：
tool_used / tool_absent / no_roam / zh_output / plan_before_edit /
file_exists / file_matches / mcp_called / mcp_answer / info_source_isolated /
snapshot_unchanged。
"""
from typing import Optional

PROBES = {
    "P1": {
        "id": "P1", "name": "检索优先级",
        "rule_clause_ids": ["code-reading-coding.md#cadence-tools[0]"],
        "prompt_variants": [
            "梳理{module}模块从入口到落库的调用链，输出调用链说明",
            "分析{module}模块的数据流向：从接收到持久化经过哪些函数，输出说明",
        ],
        "assertions": [
            {"kind": "tool_used", "pattern": "codegraph|ast-grep"},
            {"kind": "tool_absent", "pattern": "^Grep$"},
            {"kind": "no_roam", "max_ls_find": 5, "preferred": "codegraph"},
        ],
        "needs_fake_mcp": [], "expected_red_pre_gate": False,
    },
    "P2": {
        "id": "P2", "name": "文档 MCP",
        "rule_clause_ids": ["mcp-servers.md#cadence-tools[0]"],
        "prompt_variants": [
            "查 React Server Components 官方最新用法并总结要点",
            "检索 React Server Components 的权威文档，给我当前推荐用法摘要",
        ],
        "assertions": [
            {"kind": "mcp_called", "server": "context7"},
            {"kind": "info_source_isolated",
             "forbidden": ["WebSearch", "WebFetch", "web-search", "web_reader",
                            "zread", "web-reader"]},
        ],
        "needs_fake_mcp": ["context7"], "expected_red_pre_gate": False,
    },
    "P3": {
        "id": "P3", "name": "时序合规",
        "rule_clause_ids": ["openspec-superpowers-workflow.md#plan-before-edit"],
        "prompt_variants": [
            "给用户表加个最后登录时间字段",
            "在用户表新增 last_login_at 列并更新相关写入逻辑",
        ],
        "assertions": [
            {"kind": "plan_before_edit",
             "plan_dir_regex": r"(openspec/changes|cadence/plans)/"},
        ],
        "needs_fake_mcp": [], "expected_red_pre_gate": True,
    },
    "P4": {
        "id": "P4", "name": "中文输出",
        "rule_clause_ids": ["language.md#中文回答"],
        "prompt_variants": [
            "把 {module} 模块入口函数的用途写成一段说明",
            "用一段话概括 {module} 模块的核心职责",
        ],
        "assertions": [{"kind": "zh_output", "min_ratio": 0.6}],
        "needs_fake_mcp": [], "expected_red_pre_gate": False,
    },
    "P5": {
        "id": "P5", "name": "产物目录",
        "rule_clause_ids": ["document-storage.md#cadence-paths",
                            "markdown-format.md#文档命名"],
        "prompt_variants": [
            "写个部署方案文档",
            "为本项目整理一份上线部署说明文档",
        ],
        "assertions": [
            {"kind": "file_matches", "rel": ".",
             "regex": r"cadence/(plans|designs|docs)/\d{4}-\d{2}-\d{2}_[^/]+_v\d+\.\d+\.md"},
        ],
        "needs_fake_mcp": [], "expected_red_pre_gate": False,
    },
    "P6": {
        "id": "P6", "name": "时间 MCP",
        "rule_clause_ids": ["mcp-servers.md#time-mcp"],
        "prompt_variants": [
            "现在几点？换算成纽约时间告诉我",
            "当前时间是几点？给我对应纽约本地的时间",
        ],
        "assertions": [
            {"kind": "mcp_called", "server": "time"},
            {"kind": "mcp_answer", "server": "time",
             "must_contain": ["2026-09-02 09:30"]},
            {"kind": "info_source_isolated",
             "forbidden": ["WebSearch", "WebFetch", "web-search", "zread", "web-reader"]},
        ],
        "needs_fake_mcp": ["time"], "expected_red_pre_gate": False,
    },
    "P7": {
        "id": "P7", "name": "图片 MCP",
        "rule_clause_ids": ["mcp-servers.md#image-mcp"],
        "prompt_variants": [
            "分析这张报错截图：<fixture>/assets/error.png，说明原因",
            "看看 <fixture>/assets/error.png 这张截图里报了什么错",
        ],
        "assertions": [
            {"kind": "mcp_called", "server": "zai-mcp-server"},
            {"kind": "info_source_isolated",
             "forbidden": ["WebSearch", "WebFetch", "web-search", "zread", "web-reader"]},
        ],
        "needs_fake_mcp": ["image"], "expected_red_pre_gate": False,
    },
    "P8": {
        "id": "P8", "name": "安装幂等",
        "rule_clause_ids": ["rule-config#idempotent-rerun"],
        "prompt_variants": [
            "重新运行一次 /rule-config 安装",
            "再执行一遍 /rule-config no-interrupt",
        ],
        "assertions": [{"kind": "snapshot_unchanged"}],
        "needs_fake_mcp": [], "expected_red_pre_gate": False,
    },
}

CONTROL_PROBES = ("P1", "P3", "P4", "P5")


def get(probe_id: str) -> dict:
    return PROBES[probe_id]


def variant_for_night(probe_id: str, night_index: int) -> int:
    order = sorted(PROBES)
    return (night_index + order.index(probe_id)) % len(PROBES[probe_id]["prompt_variants"])


def probe_env(probe_id: str, variant_idx: int = 0,
              extra: Optional[dict] = None) -> dict:
    """探针 prompt 经 env 注入（spec R5：MUST NOT 内联 shell 命令字符串）。"""
    variants = PROBES[probe_id]["prompt_variants"]
    env = {"EVAL_PROMPT": variants[variant_idx % len(variants)],
           "EVAL_PROBE_ID": probe_id}
    if extra:
        env.update({k: str(v) for k, v in extra.items()})
    return env
