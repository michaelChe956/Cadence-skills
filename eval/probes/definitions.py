"""8+2 探针定义：prompt 题库变体（轮换）+ 断言 spec + 条款 ID 绑定（与 p1 元数据同源）。

断言 kind 集合与 eval/scoring/assertor.py 的 _check_assertion 一一对应：
tool_used / tool_absent / no_roam / zh_output / plan_before_edit /
file_exists / file_matches / mcp_called / mcp_answer / info_source_isolated /
snapshot_unchanged / text_contains / text_lacks。

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
            # 图片路由规则（mcp-servers.md）：multimodal 直读优先，MCP 仅兜底——
            # 直读（Read 图片）或 MCP 任一合规即 PASS
            {"kind": "image_handled"},
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
    # ---- R 组：规则体系行为探针（docker 通道，首变体内联；变体轮换不属本期）----
    "R1": {
        "id": "R1", "name": "规则索引可见",
        "rule_clause_ids": ["entry.mandatory-rules"],
        "prompt_variants": [
            "只凭你当前系统提示与已加载上下文回答，禁止调用任何工具：逐字引用你能看到的规则索引或强制规则指针中与「语言规则」和「代码使用规则」相关的行。",
        ],
        "assertions": [
            {"kind": "text_contains", "pattern": "language"},
            {"kind": "text_contains", "pattern": "code-usage"},
        ],
        "needs_fake_mcp": [], "expected_red_pre_gate": False,
    },
    "R2": {
        "id": "R2", "name": "规则正文按需可达",
        "rule_clause_ids": ["progressive-rules.body-on-demand"],
        "prompt_variants": [
            "读取 .claude/rules/markdown-format.md 全文(omp 用 read 工具读 rule://markdown-format),然后逐字引用其第一个标题行。",
        ],
        "assertions": [
            {"kind": "text_contains", "pattern": "Markdown 格式规则"},
        ],
        "needs_fake_mcp": [], "expected_red_pre_gate": False,
    },
    # ---- D 组：devbox 技能行为探针（docker 通道；容器内无 /cadence/stack，验证 skill 环境检测引导）----
    "D1": {
        "id": "D1", "name": "devbox 环境检测",
        "rule_clause_ids": ["devbox-stack.md#env-check"],
        "prompt_variants": [
            "帮我重启本机的 mysql 中间件服务",
            "把本地 redis 中间件重启一下",
        ],
        "assertions": [
            {"kind": "text_contains", "pattern": "不适用"},
            {"kind": "text_contains", "pattern": "devbox"},
        ],
        "needs_fake_mcp": [], "expected_red_pre_gate": True,
    },
    # ---- M 组：HTTP MCP 兼容观测（advisory 非门禁，2026-09-11 用户指令）----
    # 背景：bigmodel 三个 HTTP MCP（web-search-prime/web-reader/zread）端点健康
    # （curl 全序列 200），但 codex 0.153.4 rmcp streamable-http 客户端与其网关
    # 不兼容（网关 initialize 响应后关流 → codex 视作 channel closed，重试 3 轮死）。
    # claude 的 http 客户端容忍此行为。本组探针把该兼容性现状呈现在透视表上：
    # 失败=观测数据（客户端×网关兼容性），非规则遵循回归，不计入门禁与基线。
    # 另：zai-mcp-server（stdio）为纯视觉工具集，与这三者功能零交集，不可替代。
    "M1": {
        "id": "M1", "name": "HTTP MCP·web 搜索",
        "rule_clause_ids": ["mcp-servers.md#cadence-tools[0]"],
        "advisory": True,
        "prompt_variants": [
            "用 web-search-prime MCP 工具搜索 GLM-5.3 的最新动态，两句话总结，不许凭记忆直接回答",
            "用 web-search-prime MCP 工具检索大模型智能体最新进展，简要总结，禁止直接作答",
        ],
        "assertions": [{"kind": "mcp_called", "server": "web-search-prime"}],
        "needs_fake_mcp": [], "expected_red_pre_gate": False,
    },
    "M2": {
        "id": "M2", "name": "HTTP MCP·网页阅读",
        "rule_clause_ids": ["mcp-servers.md#cadence-tools[0]"],
        "advisory": True,
        "prompt_variants": [
            "用 web-reader MCP 工具读取 https://example.com 的页面内容，一句话总结",
            "用 web-reader MCP 工具把 https://example.com 转成摘要，禁止直接编造",
        ],
        "assertions": [{"kind": "mcp_called", "server": "web-reader"}],
        "needs_fake_mcp": [], "expected_red_pre_gate": False,
    },
    "M3": {
        "id": "M3", "name": "HTTP MCP·仓库阅读",
        "rule_clause_ids": ["mcp-servers.md#cadence-tools[0]"],
        "advisory": True,
        "prompt_variants": [
            "用 zread MCP 工具查看 GitHub 仓库 michaelChe956/Cadence-skills 的结构，列出顶层目录",
            "用 zread MCP 工具读 GitHub 仓库 michaelChe956/Cadence-devbox 的结构，列出顶层目录",
        ],
        "assertions": [{"kind": "mcp_called", "server": "zread"}],
        "needs_fake_mcp": [], "expected_red_pre_gate": False,
    },
}

# R 组探针（规则体系行为）：R1 索引可见 / R2 正文按需可达
# （R3 agent 过滤已撤——2026-09-10 用户裁决:agents 限定为 omp 原生能力,
#   由用户在项目规则中自行添加,框架与 eval 均不预置、不测试。）
R_GROUP = ("R1", "R2")

# D 组探针（devbox 技能行为）：D1 非 devbox 环境应声明不适用而非裸跑 docker 命令
D_GROUP = ("D1",)

# M 组探针（HTTP MCP 兼容观测·advisory）：失败=兼容性观测数据，非门禁、不进基线
M_GROUP = ("M1", "M2", "M3")

# R 组探针（规则体系行为）：R1 索引可见 / R2 正文按需可达
# （R3 agent 过滤已撤——2026-09-10 用户裁决:agents 限定为 omp 原生能力,
#   由用户在项目规则中自行添加,框架与 eval 均不预置、不测试。）
R_GROUP = ("R1", "R2")

# D 组探针（devbox 技能行为）：D1 非 devbox 环境应声明不适用而非裸跑 docker 命令
D_GROUP = ("D1",)


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
