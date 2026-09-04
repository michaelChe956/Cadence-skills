"""阶段一四 command prompt 表（维护者直接 command 调用形态；no-interrupt 确定性）。"""
STAGE1_COMMANDS = [
    {"name": "pre-check", "prompt": "/pre-check"},
    {"name": "mcp-configuration", "prompt": "/mcp-configuration no-interrupt"},
    {"name": "rule-config", "prompt": "/rule-config no-interrupt"},
    {"name": "project-rules-examples", "prompt": "/project-rules-examples no-interrupt"},
]
