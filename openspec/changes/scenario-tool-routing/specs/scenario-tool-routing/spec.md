## Purpose

九类开发任务场景的工具路由规范：以场景（任务目标+对象类型+范围+时效性）驱动工具选择，Markdown 路由矩阵为唯一规范源，规则文件与 CLAUDE.md 决策卡为其投影；取代"按工具名全局优先/禁用"的旧口径。

## ADDED Requirements

### Requirement: 九类场景路由矩阵必须作为规范源

规则体系 MUST 以九类场景路由矩阵为工具选择的规范源，每场景 MUST 定义：场景标识、典型任务、首选工具链、次选、判断信号（模型可操作的任务特征）。九场景与首选链：

| 场景 | 首选链 |
|---|---|
| D 库/API/框架文档 | Context7（resolve→docs）；已知官方 URL 用 WebFetch |
| R 开放调研/实时信息 | WebSearch→WebFetch 精读；子代理或不可用时 webSearchPrime/MiniMax 搜索 MCP |
| C 代码结构/调用链 | CodeGraph（大范围）→ ast-grep outline（单文件结构）→ 定向 Read |
| M Markdown/配置文本 | 路径已知直接 Read；找位置用 rg/Grep；文件发现用 Glob |
| S Shell/日志排查 | Bash（tail/sed/jq/awk）；已知路径 Read |
| G Git 历史考古 | Bash git log/blame/show/diff |
| T 测试失败定位 | Bash 跑测试→Read/rg 错误→转 C 场景工具 |
| F 文件路径发现 | Glob；小范围 find |
| U 已知 URL 精读 | WebFetch；GitHub 仓库用 zread；结构化提取用 webReader |

#### Scenario: 配置文本检索路由到 rg

- **WHEN** 任务为在 YAML/Markdown/JSON 等配置或文档文本中定位明确字符串（M 场景判断信号成立）
- **THEN** 模型按矩阵首选 rg/Grep 或直接 Read，MUST NOT 因代码检索类规则而改用 CodeGraph/ast-grep

#### Scenario: 库文档路由到 Context7

- **WHEN** 任务涉及具体库名/import 语句/框架 API 用法（D 场景信号）
- **THEN** 首选 Context7 解析与取文档；用户直接给出官方 URL 时 WebFetch 优先

### Requirement: 场景冲突必须按固定优先级裁决

多场景信号同时命中时 MUST 按优先级裁决：任务目标 > 对象类型 > 范围 > 时效性。场景链 MUST 允许组合（如 T 场景先 Bash 后转 C 工具）；判断信号不足以裁决时 MUST 选择误伤面更小的原生工具路径。

#### Scenario: 跨文件代码问题不被配置规则误导

- **WHEN** 任务为跨文件调用链分析（C 信号）但目标仓库含大量 Markdown 文档
- **THEN** 按任务目标（代码结构）优先裁决走 C 场景链，MUST NOT 因对象库含文档而降级为 rg 全文检索

### Requirement: 路由矩阵必须单源投影且不漂移

九场景矩阵 MUST 以规则文件（`.claude/rules/`）正文中的 Markdown 表格为唯一规范源；CLAUDE.md MUST 投影一张 ≤12 行的极简决策卡（场景→首选工具的速查），MUST NOT 在决策卡中引入矩阵没有的工具或场景；规则文件顶部机器元数据 MUST 仅保留稳定字段（schema_version、default_mode、recommended_profile），MUST NOT 再携带 fallback deny 列表。规则修改后决策卡与矩阵 MUST 同步（快照校验）。

#### Scenario: 决策卡与矩阵一致性校验

- **WHEN** 维护者修改矩阵中某场景的首选工具并重新分发规则
- **THEN** CLAUDE.md 决策卡同步更新且一致性校验通过；两处不一致时校验 MUST 失败并指出漂移位置
