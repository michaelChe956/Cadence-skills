# 技术方案：MCP 图片识别路由规则引入与 CodeGraph 规则按项目类型分发修复

- 日期：2026-08-27
- 版本：v1.0
- 状态：待评审
- 修订记录：
  - v1.0 初稿。基于 scout 侦察、oracle 两轮终评（X/Y/X+Y 对比终评置信度 0.95；D1 置信度 0.97；D2 置信度 0.92）与用户对三项关键决策的显式确认成文。
- 关联技能：`cadence-init/skills/rule-config`、`cadence-init/skills/mcp-configuration`
- 关联分支：`feat-b-0827-mcp-rule-fix`（worktree：`.worktrees/feat-b-0827-mcp-rule-fix`）

## 1. 背景与问题

优化 rule-config 与 mcp-configuration 中 MCP 相关规则配置的两个缺陷：

1. **图片识别路由缺失**：`mcp-servers.md` 已有智普视觉理解与 MiniMax `understand_image` 工具说明，但缺少三条全局语义——(a) 模型自身具备多模态能力时应优先原生识图；(b) 模型无法直接识图时才使用智普（zai-mcp-server）或 MiniMax MCP，且**两者之间无固定优先级**；(c) 调用任一 MCP 前必须确认其可用性并**记录标记**，后续依据标记判断，避免重复探测与无意义重试。
2. **非代码项目误用 CodeGraph**：本仓库为纯文档/Skills 项目，却在 worktree 中出现 `.codegraph/codegraph.db`（未跟踪现场证据）。

### 1.1 根因

| 问题 | 根因 |
|---|---|
| 2 | **信号不对称**：`rule-config.py` S8 早有正确的项目类型判断（仅 `project_type=coding` 或显式 `--enable-codegraph` 才安装初始化 CodeGraph；`managed-rule-lifecycle` spec 契约亦同）；但 `code-reading.md` 位于无差别分发清单 `ORDINARY_RULE_FILES` 中，正文「全新 worktree 必须先初始化 CodeGraph」「项目必须先执行 codegraph init」无条件生效，且入口摘要第 7 条同步为死文本。Agent 进入新 worktree 后照章办事即产生 `.codegraph/`。仓库中已有成熟的类型感知分发先例（`CODE_USAGE_SOURCE_MAP` 双来源单选 code-usage），但 `code-reading` 从未纳入该机制——当年 spec Scenario「非 Coding 项目仍获得代码阅读规则」只把类型感知用于"装不装工具"，未用于"正文内容"。 |
| 1 | 智普/MiniMax 小节各自描述工具，但没有任何跨供应商的统一路由入口：agent 可能在模型本身可识图时仍调 MCP、在两个 MCP 间形成隐式顺序、每次任务重复探测、失败后无限重试。另有漂移风险：`mcp-configuration/SKILL.md:395-407` 残留旧流程「将智普/MiniMax 规则追加到 `.claude/rules/mcp-servers.md` 末尾」，与 rule-config 受管权威覆盖机制冲突（双写者）。 |

## 2. 设计决策（已与用户确认）

| 决策点 | 结论 |
|---|---|
| 修复方向 | **X+Y 组合**：Y 为主——`code-reading` 照 `code-usage` 先例做双来源单选；X 为辅——共享 `mcp-servers.md` 内 CodeGraph 小节条件化（覆盖显式启用场景的指引需求） |
| D1：`--enable-codegraph` 显式例外 | **保留**（现有 spec 条款与 `it-s8-codegraph-explicit-enable` 测试已锁定契约）；附加边界：只能由用户明确提出触发，Agent 不得自行推断；参数只控制 S8 安装步骤，不改变最终 project_type、两个规则来源的选择及入口摘要 |
| D2：MCP 可用性标记载体 | **`cadence/cache/mcp-availability/<task-scope-id>.json`**（运行时缓存语义；不采用 `cadence/reports/` —— 该目录定义为开发进度报告/阶段总结，放运行时状态属语义错位；不新建 `.cadence/` 第二命名空间） |
| no-code 版正文定位 | 面向 Markdown/YAML/JSON/配置/规则文档的结构化阅读指引；不为整个仓库构建 CodeGraph；对 `ast-grep outline` 保留窄例外（仅在当前任务明确涉及辅助源码文件时可用） |
| 规则所有权 | `.claude/rules/mcp-servers.md` 唯一权威源 = rule-config references 模板；mcp-configuration 仅负责 `.mcp.json`、`.codex/config.toml` 等配置交接，禁止写入/追加任何受管规则文件 |

## 3. 行为矩阵（目标态，全象限闭合）

| 最终 project_type | `--enable-codegraph` | code-reading 来源 | S8 CodeGraph | 使用指引出处 | 第 7 条摘要 |
|---|---|---|---|---|---|
| coding | 否 | coding 版 | 默认执行 | coding 版正文 | coding 文案 |
| non-coding | 否 | non-coding 版 | 跳过 | 不适用（正文无代码图要求） | non-coding 文案 |
| non-coding | 是（用户显式） | **仍为 non-coding 版** | 显式执行 | `mcp-servers.md` 条件化 CodeGraph 小节 | **不变**（non-coding 文案） |
| 检测 non-coding + 普通模式 CLI 提升 coding | 否 | coding 版 | 执行 | coding 版正文 | coding 文案 |
| 检测 non-coding + no-interrupt 携带 CLI coding | 否 | non-coding 版 | 跳过 | 同默认 non-coding | non-coding 文案 |

实现铁律（两条，违者复审）：

1. **单一信号源**：模板选择、入口第 7 条摘要渲染、S8 判断均只消费最终 `plan["project_type"]`；禁止旁路读取 `detected_type` 或其他信号选择模板。
2. **no-interrupt 语义不变**：`_compute_final_project_type()` 裁决逻辑一行不改；no-interrupt 下 CLI `--project-type` 依旧被完全忽略、零打断、结果确定。

## 4. 改动 1：code-reading 双来源单选（缺陷 2 主修）

### 4.1 模板层

- 新增 `cadence-init/skills/rule-config/references/rules/code-reading-coding.md`：由现行 `code-reading.md` 正文迁移（保持「先 init 后阅读」在 Coding 项目语境下的原有约束），并补一句项目类型前提。
- 新增 `code-reading-noncoding.md`：
  - 默认阅读对象：Markdown、YAML、JSON、配置与规则文件、需求/设计/计划/OpenSpec 文档；
  - 默认方式：先看入口/README/manifest/索引；小文件直读；大文件按标题与关键词定向区间读取；YAML/JSON 用 `jq`/`yq` 等结构感知工具验证，不以文本命中代替结构结论；
  - 明文禁止：默认执行 `codegraph init`、创建 `.codegraph/`、要求"大范围检索优先 CodeGraph"；
  - ast-grep 窄例外：仅当任务明确涉及单个辅助源码文件时允许对该文件 outline，不作为文档阅读前置；
  - 提示：项目性质实质变为 Coding 时应重跑 rule-config，而非靠阅读规则长期绕行。
- 移除原单文件 `references/rules/code-reading.md`（与 code-usage 双来源模式一致）。

### 4.2 脚本层（rule-config.py）

```python
CODE_READING_SOURCE_MAP = {
    "coding": "code-reading-coding.md",
    "non-coding": "code-reading-noncoding.md",
}
CODE_READING_TARGET = "code-reading.md"
```

- `ORDINARY_RULE_FILES` 移除 `code-reading.md`（5→4 个普通规则），受管落地文件总数**不变（7 个）**；
- S3 按 `plan["project_type"]` 单选来源追加 `(target, selected_source, False)`，`template_source` 记录实际来源；
- drift 比较、幂等判断均针对当前类型对应来源模板；
- 原 `CODEGRAPH_RULE_FILE` 常量更名中性化；
- 模板完整性检查（locate_templates 失败关闭）纳入两份新来源，防止"S3 静默 skip 而 S4 写摘要"再造悬空引用；
- 入口第 7 条摘要仿 `RULE2_TEXT_*` 先例做双文案渲染（coding：CodeGraph+ast-grep 语义；non-coding：文档结构化定向阅读语义）。

### 4.3 本仓库根副本

本仓库检测为 non-coding，根副本 `.claude/rules/code-reading.md` 应与 `code-reading-noncoding.md` 逐字同步；同步校验逻辑需支持"来源映射"而非同名比较。

## 5. 改动 2：共享 mcp-servers.md（缺陷 1 主修 + 缺陷 2 辅修）

### 5.1 新增独立小节「图片识别路由与 MCP 可用性状态」

置于智普视觉理解与 MiniMax 小节之前，定义统一决策序：

1. **模型能力三分**：`multimodal`（客户端实际把图片暴露给模型，非品牌推断）/ `text-only` / `unknown`；
2. multimodal 且图片可直接访问 → 用模型原生能力，不调用、不探测两家 MCP；
3. text-only / 无法直接访问 → 分别读取智普、MiniMax 的 task-scope 状态；无状态或 unknown 的 provider 各探测一次并记录；不可用者不再无条件重试；
4. **无固定优先级**：两者皆可用时按任务适配度任选，明文声明章节顺序不代表优先级；一个不可用可改用另一个；全部不可用时如实报告；
5. 探测结论 = 客户端能发现 server + 图片工具可见 + 最小能力确认，三者齐备方记 `available`；
6. 智普/MiniMax 两 provider **状态独立记录**，禁止合并总布尔值。

既有智普/MiniMax 小节保留各自工具说明，各加一句交叉引用（"图片任务必须先遵循路由小节，不得依本节位置推断优先级"）。

### 5.2 可用性状态缓存（D2）

路径：`cadence/cache/mcp-availability/<task-scope-id>.json`（scope id 于任务开始时生成并在上下文中复用）：

```json
{
  "schema_version": "1",
  "scope_id": "<task-scope-id>",
  "created_at": "<ISO-8601>",
  "providers": {
    "zhipu":   { "status": "available",   "checked_at": "...", "probe": "tool-availability", "reason": "ok" },
    "minimax": { "status": "unavailable", "checked_at": "...", "probe": "tool-availability", "reason": "tool-not-exposed" }
  }
}
```

约束：`status ∈ {unknown, available, unavailable}`；同一 scope 每 provider 至多探测一次；配置变更/重连/用户重检时标记失效；损坏、版本不识别、scope 不匹配一律视作 `unknown`；**禁止记录 API Key、Authorization、原始错误响应、图片内容、MCP 返回正文、敏感 URL**。`.gitignore` 精确追加 `cadence/cache/mcp-availability/` 一行（幂等），不得忽略整个 `cadence/cache/`。

### 5.3 CodeGraph 小节条件化（缺陷 2 辅修）

`mcp-servers.md` 中「项目必须先执行 `codegraph init`」等无条件表述改为：「CodeGraph 仅适用于 Coding 项目；non-coding 项目仅当用户明确启用 `--enable-codegraph` 时才允许初始化，且该开关不改变项目类型与规则模板选择」。此为显式启用场景的唯一指引出口（因 non-coding 项目不会收到 coding 版 code-reading）。

## 6. 改动 3：mcp-configuration 职责收缩

- 删除 SKILL.md:395-407 「将智普/MiniMax 规则追加到 `.claude/rules/mcp-servers.md` 文件末尾（已有段落则跳过）」旧流程；
- 明确：受管规则唯一来源为 rule-config 权威模板，本 Skill 只维护 `.mcp.json` / Codex config / gitignore 等配置交接，引用 canonical rule 时指向 `.claude/rules/mcp-servers.md`；
- 大段复制到 SKILL.md 的视觉/图片说明收敛为指向路由小节的简述，避免第二事实源。

## 7. OpenSpec delta 清单

单一 change 提案，含以下条款变更：

| Capability | 变更 |
|---|---|
| `managed-rule-lifecycle` | 重写「非 Coding 项目仍获得代码阅读规则」→「代码阅读规则按最终项目类型单选来源」+「非 Coding 项目获得无代码图要求的阅读规则」（含：双来源 MUST、落地名固定、source 不落地、non-coding 正文无默认 CodeGraph 要求、摘要同步、只消费 final project_type）；补显式例外补充条款（`--enable-codegraph` 不改变类型/来源/摘要，指引由共享条件化小节提供） |
| `rule-config-scripted-execution` | 明确 code-reading 来源与第 7 条摘要纳入最终 project_type 连带语义；no-interrupt 行为不变；显式例外独立于类型裁决 |
| `framework-authoritative-rule-files` | 受管目标仍为固定 `code-reading.md`；drift/幂等以当前类型所选来源为准 |
| `progressive-context-routing` | 不再对所有项目统一暗示 CodeGraph/ast-grep；按项目类型对应的阅读规则选择工具 |
| （新增场景归属以上 capability） | MCP 图片输入路由契约：原生优先 / 探测前置 / task-scope 缓存 schema / 无固定优先级 / 安全字段禁令 / mcp-configuration 不再写受管规则 |

## 8. 测试影响（精确更新，不放宽红线）

- 仿 `TestCodeUsageSingleSource` 新增 code-reading 双来源测试（fixed target / selected template_source / source 不落地）；
- S3 create / drift / no-interrupt 权威覆盖按所选来源断言；
- 第 7 条双文案测试；修正硬编码 CodeGraph 摘要与"结果包含 CodeGraph"类旧期望（拆分为 coding/non-coding 两期望）;
- 可选规则完整性检查解除"code-reading ≙ CodeGraph 规则"假设；
- `verify-managed-lifecycle.sh`：converged fixtures 按类型取双来源；显式启用用例断言"S8 执行但 code-reading 仍为 non-coding 来源"；no-interrupt / CLI 提升 / 检测 coding 三类下游一致性；根副本特殊来源映射；
- 新增静态契约：SKILL.md 不再出现「追加到 `.claude/rules/mcp-servers.md` 文件末尾」；模板存在原生优先/探测/task scope/无优先级/安全字段关键词；
- 回归命令：unittest 全量、`verify-managed-lifecycle.sh` 全量、`openspec validate --strict`、`git diff --check`；
- 既有现场 `.codegraph/`：不提交；确认为误初始化产物后一次性手动删除；脚本不得自动清理历史索引。

## 9. 风险表

| 风险 | 等级 | 缓解 |
|---|---:|---|
| 混合仓库（文档为主含少量脚本）类型表达不完美 | 中 | no-code 版保留 ast-grep 单文件窄例外；实质转编码应重跑 rule-config |
| 旁路信号导致文案/工具割裂复发 | 高 | 铁律一写入 spec MUST；reviewer 专项核对 detected_type 引用 |
| 状态缓存过期误导 | 中 | scope 隔离 + checked_at + 失效三条件（损坏/版本/scope 不匹配 → unknown） |
| 缓存泄密 | 高 | schema 白名单字段；安全禁令进静态测试 |
| 重跑 rule-config 权威覆盖既有项目旧版文件 | 低 | 归档屏障机制既有，行为不变 |
| S3/S4 时序造成摘要悬空 | 中 | 模板完整性失败关闭纳入新来源 |
| SKILL 收缩漏掉必要配置职责 | 中 | 仅删除规则写入职责，`.mcp.json`/Codex/gitignore 流程原样保留并保留测试 |
