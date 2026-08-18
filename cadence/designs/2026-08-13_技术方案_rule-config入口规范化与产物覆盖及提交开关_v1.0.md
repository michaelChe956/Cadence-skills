# 技术方案：rule-config 入口文件规范化、产物路径覆盖与自动提交开关

- 日期：2026-08-13
- 版本：v1.2
- 状态：待评审
- 修订记录：
  - v1.1 按 reviewer（deepseek-v4-pro）审查意见修正——L0 v1→v2 升级路径未接线（补前置脚本改动）；失效行删除准则收紧为显式退役清单；根因表述改为"易漂移的结构性风险"；补边界语义与计数同步。
  - v1.2 按 reviewer（gpt-5.6-terra）第二轮审查意见修正——L0 v2 契约链闭合到全部权威文档与测试；L0 迁移补混合标记/重复区块/唯一性不变量；无章节入口的顺序矛盾改为"L0 插入位置修正"解法；规则 6 稳定身份判定；Playwright 条件项接入 create 路径；开关插入算法精确化；新增统一 `warnings` 报告契约；规则 2 全文替换移除（改为章节内渲染）；测试清单补齐。文中行号引用均为撰写时定位，长期契约以符号名为准。
- 关联技能：`cadence-init/skills/rule-config`

## 1. 背景与问题

使用当前 skills 初始化项目后，入口文件（CLAUDE.md / AGENTS.md）与 Superpowers 工作流存在三个问题：

1. **入口文件生成不正确**：目标项目已存在非 Cadence 风格入口文件时，生成的 AGENTS.md 缺失强制规则 1-7；CLAUDE.md 残留已退役规则（Serena）、编号错乱（1-9 vs 权威 1-7）；双入口技术栈检测结果不一致（AGENTS.md 全为"未检测到"）。
2. **文档存放规则优先级不足**：`document-storage.md` 仅为普通规则文本，Superpowers 的 `brainstorming`/`writing-plans` Skill 正文硬编码 `docs/superpowers/specs/` 等默认路径，Agent 常跟随 Skill 正文，产物未按项目规则存放。
3. **design/plan 自动 commit 不可选**：Superpowers Skill 写完方案后自动 `git commit`，部分项目需要、部分项目不需要，缺少项目级开关。

### 1.1 根因

| 问题 | 根因 |
|---|---|
| 1 | `rule-config.py` 的 `_ensure_summary_lines` 为"只增不删不建"的追加逻辑：无 `## 强制规则` 章节时直接返回；只补缺失引用、从不删除失效引用、不重排编号；`BASE_CLAUDE_MD`/`BASE_AGENTS_MD` 与补全常量为两份事实源，存在易漂移的结构性风险（当前逐字一致，但无机制保证持续一致）。另：`_compose_entry` 步骤 2 对**全文**执行规则 2 文案 `str.replace`，会误改章节外用户内容。 |
| 2 | 无权威的"路径映射覆盖"声明；Skill 正文与项目规则冲突时缺乏明确优先级链。 |
| 3 | Skill 行为全局写死，无项目级配置载体。 |

## 2. 设计决策（已与用户确认）

| 决策点 | 结论 |
|---|---|
| 已存在非 Cadence 风格入口文件的处理 | **规范化合并**：保留用户原有内容，强制建立/修复 `## 强制规则` 章节（权威注入、失效清理、重新编号） |
| 存放规则优先级方案 | **规则层覆盖**：L0 路由区块 + `document-storage.md` 加入显式路径映射覆盖表；不改写全局 Superpowers Skill |
| 设计文档路径 | `cadence/designs/` |
| Plan 路径 | `cadence/plans/`（复数，现行目录不变） |
| OpenSpec 产物 | 保持 `openspec/` 目录不动 |
| 开关载体 | 入口文件 `## 项目配置` 章节新增一行配置 |
| 开关默认值 | `关闭` |
| 开关粒度 | 一个总开关同时控制 design + plan |
| 章节外孤立规则 6 H2（含废除文案） | 保留 + warnings 报告 |
| 章节内用户自定义行 | 保留在权威条目之后 + warnings 报告 |

## 3. 改动 1：入口文件规范化合并

### 3.1 权威清单单一事实源

在 `rule-config.py` 定义有序常量 `CANONICAL_RULES`，每项含：身份 marker、标题、CLAUDE/AGENTS 双文案：

```python
CANONICAL_RULES = [
    # (identity_markers, 标题, claude_text, agents_text)
    (["language.md"],         "语言规则",           ..., ...),
    (["code-usage.md"],       "代码使用规则",        ..., ...),  # 文案随 project_type
    (["document-storage.md"], "文档存储规则",        ..., ...),
    (["markdown-format.md"],  "Markdown 格式规则",   ..., ...),
    (["mcp-servers.md"],      "MCP Server 使用规则", ..., ...),
    (["cadence/project-rules/"], "项目个性化规则",   RULE6_BLOCK_CLAUDE, RULE6_BLOCK_AGENTS),
    (["code-reading.md"],     "代码阅读规则",        ..., ...),
]
# 条件项：playwright.md 仅当项目 .claude/rules/playwright.md 实际存在时加入清单
```

- **身份判定**：规则 1-5、7 以规则文件名子串匹配（沿用现行机制）；**规则 6 无规则文件**，以内容 marker `cadence/project-rules/` 作为稳定身份判定（同时兼容旧 CLAUDE 文案 `rules/` 目录措辞与旧 AGENTS 文案 `.claude/rules/` 措辞——两类旧块均含 `cadence/project-rules/README.md` 行，可可靠识别并整体替换为权威块，同时修正"（强制规则）"命名不一致）。
- `RETIRED_RULE_FILES`：脚本内显式枚举常量，初始值 `["serena-usage.md"]`；随框架规则退役手工维护；空清单时无删除行为。
- `BASE_CLAUDE_MD` / `BASE_AGENTS_MD` 改为由 `CANONICAL_RULES` 渲染生成（消除双事实源漂移）；**create 路径接收 `existing_rule_files`**，条件项（Playwright）参与渲染——目标项目已有 `.claude/rules/playwright.md` 而入口文件不存在时，新建入口即含 Playwright 条目。

### 3.2 规范化算法

`_ensure_summary_lines` 重写为 `_normalize_mandatory_rules(text, entry_name, project_type, existing_rule_files)`，返回规范化文本与变更明细。`_compose_entry` 中**移除现有的全文级规则 2 文案替换步骤**（规则 2 由章节内权威渲染产出，全文替换会破坏章节外逐字保留语义）。

**步骤 1：定位/创建章节**
- 找到 `## 强制规则`（H2 精确匹配，**首个匹配**为准；若存在多个同名 H2，仅规范化首个，其余保留并记 warning `DUPLICATE_H2`）→ 步骤 2。
- 找不到 → 创建全新章节（引导引用块 + 权威条目），插入点为 **L0 end 标记之后**（`_compose_entry` 先做 L0，故 L0 必定存在）。

**步骤 2：章节内逐行分类**（`## 强制规则` 至下一个 H1/H2 之间）
- **权威行**：命中任一 `identity_markers` 的行，及其所属 `### N.` 标题/续行块。
- **失效行**：命中 `RETIRED_RULE_FILES` 的引用行 → 连同其 `### N.` 标题一起删除。**不做"文件不存在即删"的泛化判定**（避免误删用户前瞻引用）；引用其他不存在文件但未在退役清单的行按用户行处理。
- **用户行**：其余行；**用户 H3 自定义小节（标题+正文）识别为整体块**。

**步骤 3：重建章节**
- 权威条目按清单顺序、重新编号渲染，标题与文案全部使用权威版本（含规则 6 命名修正、规则 2 按 project_type 选文案）。
- 同一规则多引用去重，保留首个（沿用现行语义）。
- 用户行/用户 H3 块原顺序附加在权威条目之后，块内结构不变，记 warning `USER_LINES_KEPT`。
- 幂等：规范化输出再次运行逐字不变。

**步骤 4：章节外内容**
- 逐字保留。
- 例外（仅报告）：章节外检测到孤立规则 6 H2——判定条件为"章节外 H2 标题行含 `项目个性化规则`"（确定性字符串匹配，不用模糊"雷同"）→ 保留 + warning `ORPHAN_RULE6`。

### 3.3 L0 插入位置修正与全局顺序

现状问题：`_insert_l0_block` 在无 `## 强制规则` 时把 L0 追加到**文件末尾**（与 docstring"文件说明后"不符），导致"用户内容 → L0 → 强制规则"的错乱顺序，与目标全局顺序矛盾；而"章节外逐字保留"又不允许搬移用户内容。

**解法（不搬移任何用户内容）**：修正 `_insert_l0_block` 的无章节分支——无 `## 强制规则` 时，L0 插入到**文件 H1 标题及首个简介段落之后**（即 docstring 原本承诺的位置），而非文件末尾；新 `## 强制规则` 章节紧随其后。由此全局顺序自然成立：

```text
H1 + 文件说明 → L0 区块 → ## 强制规则 → 用户原有内容 → ## 项目配置（缺失时追加到文件末尾）
```

### 3.4 技术栈双入口一致性

- 排查 AGENTS.md 技术栈全为"未检测到"的根因（疑似 skip 分支或旧版本运行混合结果），补复现测试并修复，保证双入口写入同一份 `tech_stack`。

### 3.5 warnings 报告契约（新增，统一落点）

报告 JSON 新增顶层字段 `warnings`：数组，元素为：

```json
{"code": "USER_LINES_KEPT", "file": "AGENTS.md", "message": "...", "detail": {"lines": 3}}
```

- 错误码枚举：`USER_LINES_KEPT`（章节内非框架条目）、`DUPLICATE_H2`（多个同名章节）、`ORPHAN_RULE6`（章节外孤立规则 6）、`INVALID_TOGGLE`（开关非法值）、`ENTRY_TOGGLE_MISMATCH`（双入口开关不一致）、`L0_DEDUP`（重复 L0 区块归并）。
- warning **不影响 `overall`**（仍为 `ok`/`degraded`/`fail` 原语义）；dry-run 与 apply 产出一致的 planned/actual warnings；no-interrupt 模式同样产出（warnings 不需要 decisions）。
- 归属：入口文件类 warnings 记入 S4 step 的同时汇总到顶层 `warnings`。

### 3.6 双模式与合并语义

- 规范化为确定性整理动作，两模式同动作，不产生新冲突、不需要 decisions（沿用 SM 先例）。
- `references/merge-semantics.md` §6 重写：SM-01~03 → **SM-01~05**（幂等跳过 / 章节缺失创建 / 失效引用删除 / 重排重编号 / 用户行保留并报告），文首行数合计 62 → 64 同步更新。
- `tests/skill-clause-map.md`（第 13、368 行附近）与 `SKILL.md`（第 129 行附近）中的"62 行"计数同步改为 64，条款对账同步更新。

### 3.7 测试（新增 `TestNormalizeMandatoryRules`）

1. 无章节创建：英文 KB 版 AGENTS.md fixture，验证全局顺序（H1/说明 → L0 → 强制规则 → 用户内容）
2. Serena 残留删除（退役清单命中）
3. 前瞻引用保留：引用不存在文件但不在 `RETIRED_RULE_FILES` 的行**不删除**（与用例 2 对照）
4. 编号 1-9 错乱 → 重排 1-7
5. 同规则多引用去重
6. 幂等重跑逐字不变
7. coding / non-coding 规则 2 文案切换
8. Playwright 条件项有无（含 create 路径：有/无 playwright.md 时新建入口的结果）
9. 用户自定义行 + 用户 H3 小节整体平移 + `USER_LINES_KEPT` warning
10. 章节外孤立规则 6 H2 保留 + `ORPHAN_RULE6` warning
11. 多个 `## 强制规则` 仅规范化首个 + `DUPLICATE_H2` warning
12. 规则 6 旧文案（CLAUDE `rules/` 措辞版 / AGENTS `.claude/rules/` 措辞版）识别并替换为权威块
13. 章节外含规则 2 旧文案的用户内容**不被修改**（回归全文替换移除）
14. 双入口技术栈一致性
15. CLAUDE / AGENTS 文案差异渲染
16. BASE 渲染与 CANONICAL_RULES 一致性（防再次漂移）
17. `RETIRED_RULE_FILES` 为空时无删除行为

## 4. 改动 2：产物路径覆盖表与 L0 v2

### 4.1 内核内容变更

`agent-routing-kernel.md` 增加显式路径映射覆盖表，版本 **v1 → v2**：

| Skill 默认路径 | 本项目强制路径 |
|---|---|
| `docs/superpowers/specs/`（design/spec） | `cadence/designs/` |
| `docs/superpowers/plans/`（plan） | `cadence/plans/` |

附声明："本表优先级高于任何 Skill 正文中的路径指示；OpenSpec 产物仍放 `openspec/` 目录。"
另加强制条款（改动 3）："调用 `brainstorming` / `writing-plans` 完成文档写入后，必须读取入口文件'产物自动提交'开关；为 `关闭` 时禁止 `git commit`，只汇报产物路径并等待用户确认。"

`document-storage.md` 同步加入同一张映射表。**跨源一致性**：映射表在脚本中定义单一常量，测试断言 kernel v2、`document-storage.md`、脚本常量三者逐字一致。

### 4.2 L0 v1→v2 脚本接线（前置必做，当前未支持）

现状（撰写时行号）：`L0_BEGIN`/`L0_END` 硬编码 v1（`rule-config.py:108-109`）；`l0_block` 旧版检测仅枚举 v0（`:905,920`）；`_remove_l0_block_pair` 仅 `versions=["v1","v0"]`（`:2477`）。v1 区块对 v2 规范源判 `drift`（普通模式落入用户决策），而非确定性 `upgrade`。

实施内容：
- 当前版本常量升为 v2（`L0_BEGIN`/`L0_END`）；旧版集合（`l0_block` 检测循环、`_remove_l0_block_pair` versions）加入 v1。
- 升级路径走 L0-04 确定性 upgrade，两模式同动作、不经用户决策。

### 4.3 L0 迁移不变量（补缺）

- **升级后唯一性**：任何迁移/升级完成后，入口文件恰好含一个当前版本区块。实现：upgrade/drift 路径统一为"移除全部旧版区块对 + 剥离孤立当前版本单侧标记行 + 插入一个规范区块"。
- **混合标记**："成对旧版区块 + 残留单侧当前版本 marker"场景——先移除旧版区块对，再剥离单侧 marker 行，最后插入规范区块（修复"检测到当前 begin 即幂等返回导致 broken 残留"的漏洞）。
- **重复当前版本区块**：多个完整当前版本区块时，保留首个（内容与规范源一致时）并移除其余，记 warning `L0_DEDUP`；首个与规范源不一致按 drift 处理。

### 4.4 L0 v2 契约链闭合（影响面全清单）

版本切换必须同步更新，保证文档与测试对账一致：
- `rule-config.py`：版本常量、旧版集合、迁移不变量逻辑（§4.2/§4.3）。
- `merge-semantics.md`：L0 表中"当前 v1"相关表述更新为 v2（第 117-123 行附近）。
- `tests/test_rule_config.py`：`V1_START`/`V1_END` 等硬编码 marker 常量（第 32-34、195-204 行附近）改为版本参数化，覆盖 v1→v2 与 v2 幂等。
- `tests/verify-managed-lifecycle.sh`：硬编码 v1 marker（第 169 行附近）同步。
- `tests/skill-clause-map.md`：L0 条款对账更新。
- 不改写全局 Superpowers Skill 本体。

## 5. 改动 3：产物自动提交开关

- 开关行：`- **产物自动提交（design/plan）**：关闭`，**双入口均写入**。
- **插入算法（确定性）**：
  1. 定位首个 `## 项目配置`（H2）；不存在则在**文件末尾**创建（此时全局顺序见 §3.3，项目配置恒在末尾）。
  2. 章节内已存在开关行（以 `- **产物自动提交（design/plan）**：` 前缀匹配）→ 保留首个、移除重复行并记 warning；不存在的引用见下。
  3. 不存在开关行 → 插入到该章节**末尾**（下一个 H2 之前或 EOF），即 `### 项目技术栈` 块之后；不并入技术栈字段列表。
  4. 多个 `## 项目配置`：仅处理首个，记 warning `DUPLICATE_H2`。
- **独立于 `tech_stack`**：`tech_stack` 为空时 `_ensure_techstack_block` 提前返回（`rule-config.py:2619`），开关由独立函数 `_ensure_commit_toggle` 负责，保证必然落位。
- **取值语义**：仅精确值 `开启` 视为启用；`关闭` 或任何其他值均按关闭处理；非法值**保留原文不改写**，记 warning `INVALID_TOGGLE`。
- **双入口读取**：以 CLAUDE.md 为准、AGENTS.md 为兜底（CLAUDE.md 缺失时读 AGENTS.md）；两者值不一致时按 `关闭` 处理并记 warning `ENTRY_TOGGLE_MISMATCH`。
- **脚本语义**：首次写默认值 `关闭`；之后保留用户手改值，不受框架覆盖。

## 6. 测试总览

- 改动 1：`TestNormalizeMandatoryRules` 17 用例（见 §3.7）。
- 改动 2：v1→v2 确定性 upgrade（两模式同动作）；v2 幂等 skip；混合标记（旧版成对 + 当前单侧残留）；重复当前版本区块归并 + `L0_DEDUP`；升级后区块唯一性；kernel/脚本常量/document-storage 三源映射表逐字一致；备份屏障失败时零写入（沿用既有备份测试模式）。
- 改动 3：默认值写入；`开启`/`关闭` 保留；非法值保留原文 + `INVALID_TOGGLE`；重复开关行归并；已有 `## 项目配置`（有/无 `### 项目技术栈`）时落点；多个 `## 项目配置`；`tech_stack` 为空时开关仍落位；CLAUDE.md 缺失时读 AGENTS.md；双入口不一致按关闭 + `ENTRY_TOGGLE_MISMATCH`。
- warnings 契约：dry-run/apply 一致；no-interrupt 下产出；`overall` 不受 warning 影响。
- 既有 160 个 unittest 全量回归（含版本参数化改造）；`verify-managed-lifecycle.sh` 通过。

## 7. 不做的事（YAGNI）

- 不改全局 Superpowers Skill 本体。
- 不动 `openspec/` 目录产物结构。
- 不做 design / plan 分开的独立开关。
- 不删除章节外用户内容（仅报告）。
- 不做"文件不存在即删"的泛化失效判定。

## 8. 影响面

| 文件 | 改动 |
|---|---|
| `cadence-init/skills/rule-config/scripts/rule-config.py` | `CANONICAL_RULES`（含规则 6 marker）、`RETIRED_RULE_FILES`、`_normalize_mandatory_rules`、BASE 渲染（含 create 路径 `existing_rule_files`）、移除全文规则 2 替换、`_insert_l0_block` 无章节分支位置修正、`_ensure_commit_toggle`、`warnings` 报告契约、技术栈一致性修复、L0 版本接线与迁移不变量（§4.2/§4.3） |
| `cadence-init/skills/rule-config/references/rules/agent-routing-kernel.md` | L0 v2：路径覆盖表 + 自动提交条款 |
| `cadence-init/skills/rule-config/references/rules/document-storage.md` | 路径映射表（与 kernel/脚本常量逐字一致） |
| `cadence-init/skills/rule-config/references/merge-semantics.md` | SM 表重写（SM-01~05）、L0 表"当前版本"表述 v1→v2、行数合计 62→64 |
| `cadence-init/skills/rule-config/tests/test_rule_config.py` | 新增用例；L0 marker 常量版本参数化 |
| `cadence-init/skills/rule-config/tests/skill-clause-map.md` | 条款对账与计数同步（62→64） |
| `cadence-init/skills/rule-config/tests/verify-managed-lifecycle.sh` | v1 marker 硬编码同步为 v2 |
| `cadence-init/skills/rule-config/SKILL.md` | 流程描述同步（规范化语义、开关说明、计数 62→64） |
