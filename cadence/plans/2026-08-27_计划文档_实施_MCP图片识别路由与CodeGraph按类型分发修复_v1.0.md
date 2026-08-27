# 实施计划：MCP 图片识别路由规则引入与 CodeGraph 规则按项目类型分发修复

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让非代码项目从物理上不再收到含 CodeGraph 要求的阅读规则，并为图片输入建立「原生优先 / 探测前置 / 双 MCP 无固定优先级」的路由契约。

**Architecture:** 复用已验证的 code-usage 双来源单选机制（SOURCE_MAP→固定落地名→drift 按所选来源比较）；共享 mcp-servers.md 增加独立图片路由小节并对 CodeGraph 小节条件化；mcp-configuration 收缩为纯配置交接者。

**Tech Stack:** Python 3 标准库（unittest）、bash 生命周期 harness（verify-managed-lifecycle.sh）、openspec CLI、diff/grep 校验工具。

**Spec:** `cadence/designs/2026-08-27_技术方案_MCP图片识别路由与CodeGraph按类型分发修复_v1.0.md`（主设计）＋ `openspec/changes/2026-08-27-mcp-image-route-and-codegraph-typed-source/`（proposal/specs/design/tasks）

## Global Constraints

- **禁止 git commit**：产物自动提交开关=关闭（CLAUDE.md 权威）。全部只改工作区。
- **铁律①**：code-reading 来源选择与入口第 7 条摘要渲染只消费最终 `plan["project_type"]`；禁止读取 detected_type 或其他旁路信号。
- **铁律②**：`_compute_final_project_type()` 函数逻辑一行不改（no-interrupt=检测结果、CLI 忽略、普通模式仅提升）。
- 落地名恒定 `.claude/rules/code-reading.md`；source 模板不得落地；受管落地文件总数维持 **7** 个不变。
- `.claude/rules/` 受管文件语义：改权威模板必同步根副本（本仓库 non-coding → code-reading 根副本对 `code-reading-noncoding.md`）。
- 非 Coding 版不得出现：「全新 worktree 必须先初始化 CodeGraph」「大范围检索优先使用 CodeGraph」或任何默认 `codegraph init` 要求。
- 状态缓存安全禁令：不记录 API Key、Authorization、原始错误响应、图片内容、MCP 返回正文、敏感 URL。
- 工作目录：`/home/michaelche/workspace/github/Cadence-skills/.worktrees/feat-b-0827-mcp-rule-fix`（下文相对路径均基于此）。
- 归档历史（`openspec/changes/archive/**`、`cadence/archive/**`）一律不修改；grep 终检时排除。

---

### Task 1: code-reading 双来源失败测试（TDD-RED）

**Files:**
- Modify: `cadence-init/skills/rule-config/tests/test_rule_config.py`
- Test: 同上文件新增两个测试类

**Interfaces:**
- Consumes: 现有 `_intents(...)` 辅助函数、`TestCodeUsageSingleSource`（约 L898 起）的写法范式、`rc.step_s3_rules_files(root, intents, plan, {})` 调用形式（同文件 L1244/L1285/L1349 已有示例）
- Produces: `TestCodeReadingSingleSource`、`TestCodeReadingSummaryDualText` 两个测试类的断言面（Task 2/3 实现后转 GREEN）

- [ ] **Step 1.1 阅读 code-usage 先例测试**：通读 `test_rule_config.py` 中 `TestCodeUsageSingleSource` 全部用例，记录其 fixture 准备方式、plan 字段构造、template_source 断言写法
- [ ] **Step 1.2 写 TestCodeReadingSingleSource**（新类，紧邻 CodeUsage 类之后）：至少覆盖
  ```python
  def test_coding_project_gets_coding_source(self):
      # plan project_type="coding" 执行 S3 后：
      # (a) .claude/rules/code-reading.md 内容 == references/rules/code-reading-coding.md
      # (b) report/steps 中该文件的 template_source == "code-reading-coding.md"
      # (c) .claude/rules/ 下不存在 code-reading-coding.md / code-reading-noncoding.md
  def test_noncoding_project_gets_noncoding_source(self):  # 对称用例（noncoding 来源）
      # 追加断言：(d) 内容不含 "codegraph init"（大小写不敏感）且不含「大范围检索优先」字样
  def test_source_template_not_landed(self):               # source 文件不落地的独立断言
  def test_drift_compared_against_selected_source(self):
      # 预置落地内容=coding 版，当前类型=non-coding → drift=True 且覆盖后为 noncoding 版
  ```
- [ ] **Step 1.3 写 TestCodeReadingSummaryDualText**：仿现行 RULE2 双文案测试（在入口渲染测试组中检索"代码使用规则"定位范式），断言 coding 渲染出 CodeGraph 大范围检索文案、noncoding 渲染出文档定向阅读文案且不含 CodeGraph 引导语；再对硬编码旧期望（第 7 条固定 CodeGraph 文案处，检索"大范围检索"在测试文件中的所有出现）逐处标记改写点——本步只记录行号清单供 Task 3 使用，不修改旧期望
- [ ] **Step 1.4 显式启用联动断言**（并入 SingleSource 类）：non-coding intent + `enable_codegraph=True` 执行 S3+S8 后，断言 code-reading 落地仍为 noncoding 来源
- [ ] **Step 1.5 RED 验证**
  Run: `python3 -m unittest cadence-init/skills/rule-config/tests/test_rule_config.py.TestCodeReadingSingleSource -v && python3 -m unittest cadence-init/skills/rule-config/tests/test_rule_config.py.TestCodeReadingSummaryDualText -v`
  Expected: FAIL/ERROR（来源映射不存在、模板不存在）

### Task 2: code-reading 双来源模板与脚本实现（TDD-GREEN）

**Files:**
- Create: `cadence-init/skills/rule-config/references/rules/code-reading-coding.md`
- Create: `cadence-init/skills/rule-config/references/rules/code-reading-noncoding.md`
- Delete: `cadence-init/skills/rule-config/references/rules/code-reading.md`
- Modify: `cadence-init/skills/rule-config/scripts/rule-config.py`（L136-150 常量区、S3 选择逻辑、drift 比较、locate_templates 清单）

**Interfaces:**
- Consumes: Task 1 断言面
- Produces: `CODE_READING_SOURCE_MAP = {"coding": "code-reading-coding.md", "non-coding": "code-reading-noncoding.md"}`、`CODE_READING_TARGET = "code-reading.md"`；S3 目标三元组 `(CODE_READING_TARGET, selected_source, False)`；后续 Task 依赖常量名 `RULE7_TEXT_CODING/RULE7_TEXT_NONCODING`（Task 3 定义）

- [ ] **Step 2.1 建 coding 版模板**：以现行 `references/rules/code-reading.md` 全文为基础迁移，仅在标题下追加一行适用范围说明（Coding 项目前提与显式开关提示）；正文其余保持原样
- [ ] **Step 2.2 建 non-coding 版模板**（全文如下，直接创建）

````markdown
## 文档阅读规则

> **结构化优先，避免盲读整片内容**

### 核心原则

- **先确认权威入口** - 开始阅读前，优先查看 README、CLAUDE.md/AGENTS.md 入口区块、manifest、索引类文件，建立目录结构与权威来源视图，再决定读什么。
- **小文件可直接完整读取** - 单文件在一屏内或明显自足时直接读取，无需额外定位步骤。
- **大型 Markdown 先定位后区间阅读** - 通过标题层级、目录链接、目标关键词确定相关章节范围，仅读取命中区间及其必要上下文，避免整篇顺序盲读造成 token 浪费。
- **YAML/JSON 用结构感知方式校验** - 优先使用 `jq`、`yq` 或项目现有校验器检查结构与字段，不得把纯文本搜索命中当作结构结论。
- **跨文档关系定向追踪** - 通过路径、链接、标识符与 schema 字段建立引用关系，不依赖行号猜测。
- **不构建代码图** - 本项目为非编码项目：默认不得执行 `codegraph init`、不得创建 `.codegraph/` 目录、不存在"大范围检索优先使用 CodeGraph"的要求。

### 结构化大纲（ast-grep outline）使用边界

- 仅当当前任务明确涉及某个辅助源码文件时，允许对该单个文件执行 `ast-grep outline` 快速了解其结构；这不是文档阅读的前置步骤，也不得据此为整个项目构建代码图。
- 若项目性质已实质转为编码项目，应重新运行 rule-config 更新项目配置，而不是长期依靠例外绕行。

### 适用场景判断

- ✅ **鼓励**：从入口区块出发建立全局视图后再深入具体文档。
- ✅ **鼓励**：核对 YAML/JSON 结构时使用专用解析工具输出键路径。
- ⚠️ **需说明**：跳过定位直接整篇读取大型文档时，应在汇报中说明原因。
- ❌ **避免**：在没有进入编码任务的背景下初始化任何代码索引工具。

### 参考资源

- YAML/JSON 解析：`jq --help`、`yq --help`
- 项目协作规则总览：`.claude/rules/` 目录与入口文件强制规则区块
````

- [ ] **Step 2.3 移除旧单文件模板**：`git rm` 或删除 `references/rules/code-reading.md`（注意：先确认 Step 2.1 已将其内容完整迁移）
- [ ] **Step 2.4 改脚本常量区**：按 Interfaces 区精确字样新增两个常量；将 `"code-reading.md"` 从 `ORDINARY_RULE_FILES` 元组移除（5→4，同步修订其上方注释“5 个”改为“4 个”）；将原 `CODEGRAPH_RULE_FILE` 常量更名为 `CODE_READING_TARGET` 并全量替换引用点
- [ ] **Step 2.5 改 S3 选择逻辑**：仿 code-usage 的单选分支，S3 组装目标时追加 `(CODE_READING_TARGET, CODE_READING_SOURCE_MAP[project_type], False)`；确认 template_source 记录的是 MAP 取值而非 target 名
- [ ] **Step 2.6 改 drift 比较**：找到对 code-reading 做 diff/哈希比较的路径，确保基准改为 `SKILL_DIR/references/rules/CODE_READING_SOURCE_MAP[project_type]`
- [ ] **Step 2.7 改 locate_templates 完备清单**：必备模板列表加入两份新来源（缺失任一即 TemplateError 失败关闭），同时移除已删除的单文件名
- [ ] **Step 2.8 GREEN 验证**
  Run: `python3 -m unittest cadence-init/skills/rule-config/tests/test_rule_config.py.TestCodeReadingSingleSource -v`
  Expected: PASS（4 用例）

### Task 3: 入口第 7 条摘要双文案（TDD）

**Files:**
- Modify: `cadence-init/skills/rule-config/scripts/rule-config.py`（L269-301 CANONICAL_RULES/RULE2 区域、S4 渲染路径）
- Modify: `cadence-init/skills/rule-config/tests/test_rule_config.py`（Task 1.3 记录的行号清单）

**Interfaces:**
- Consumes: 最终 project_type 在渲染上下文中的现有传递链（与 RULE2 相同入参）
- Produces: 第 7 条渲染双文案 `RULE7_TEXT_CODING="- **大范围检索使用 CodeGraph，精确结构阅读优先使用 ast-grep outline** → 详见 \`.claude/rules/code-reading.md\`"`、`RULE7_TEXT_NONCODING="- **文档阅读遵循结构化定向原则** → 详见 \`.claude/rules/code-reading.md\`"`

- [ ] **Step 3.1 按 RULE2_TEXT_* 同模式定义两常量并在 render_mandatory_section/替换逻辑中按 project_type 选择**
- [ ] **Step 3.2 将 Task 1.3 记录的旧硬编码期望逐处精确更新为新双文案期望（禁止删除断言）**
- [ ] **Step 3.3 GREEN 验证**
  Run: `python3 -m unittest discover -s cadence-init/skills/rule-config/tests -p "test_*.py" -k Summary -v`
  Expected: PASS

### Task 4: mcp-servers.md 图片路由小节 + CodeGraph 条件化 + 根副本同步

**Files:**
- Modify: `cadence-init/skills/rule-config/references/rules/mcp-servers.md`（智普视觉理解小节之前、CodeGraph 小节内）
- Modify: `.claude/rules/mcp-servers.md`（同步副本）

**Interfaces:**
- Consumes: 无脚本改动，纯模板契约（契约文本 = 新 capability spec `mcp-image-input-routing`）
- Produces: 落地规则中的固定小节标题 `### 图片识别路由与 MCP 可用性状态`（Task 5.2 静态测试与其联动）

- [ ] **Step 4.1 插入路由小节**（置于 `### 智普视觉理解 MCP（可选）` 标题之前；要点逐条对应 spec 五个 Requirement：能力三分、原生优先禁多余调用、探测前置/至多一探/unavailable 不重试/失效三条件视 unknown、缓存路径 `cadence/cache/mcp-availability/<task-scope-id>.json` 与 status 三态、双 provider 独立记录与无固定优先级明示、白名单字段与敏感信息禁令、全不可用如实报告）
- [ ] **Step 4.2 条件化 CodeGraph 小节**：第 79 行「项目必须先执行 `codegraph init`……」改写为
  ```markdown
  1. CodeGraph 仅适用于 Coding 项目：仅当最终 `project_type=coding`，或用户明确启用 `--enable-codegraph` 时，才允许在项目根目录执行 `codegraph init`（存在 `.codegraph/` 后 CodeGraph MCP 才提供工具）。`project_type=non-coding` 默认跳过安装、初始化与配置，且开关不改变项目类型与规则模板选择。
  2. Coding 项目在 CodeGraph 已启用且可用时，大范围检索优先使用 CodeGraph。
  3. 精确结构阅读优先使用 `ast-grep outline`。
  4. `ast-grep outline` 与 CodeGraph 结果冲突时，以 `ast-grep outline` 为准。
  ```
- [ ] **Step 4.3 智普/MiniMax 两小节头部各加一句**：`图片任务必须先遵循"图片识别路由与 MCP 可用性状态"小节；本节排列顺序不代表服务优先级。`
- [ ] **Step 4.4 同步根副本并校验**：Run: `cp cadence-init/skills/rule-config/references/rules/mcp-servers.md .claude/rules/mcp-servers.md && diff -q cadence-init/skills/rule-config/references/rules/mcp-servers.md .claude/rules/mcp-servers.md`
  Expected: 无输出（一致）
- [ ] **Step 4.5 模板静态断言适配**：运行 test_rule_config.py 中 mcp-servers 相关静态用例，若有对旧文本的断言则按新契约精确更新；Expected: 相关用例 PASS

### Task 5: mcp-configuration 所有权收缩 + gitignore

**Files:**
- Modify: `cadence-init/skills/mcp-configuration/SKILL.md`（L395-407 及重复说明区域）
- Test: `test_rule_config.py` 内新增 SKILL.md 静态契约用例（或在既有静态测试类中添加方法）

- [ ] **Step 5.1 RED 静态测试**：新增断言——SKILL.md 全文 NOT 匹配 `追加到 \`.claude/rules/mcp-servers.md\` 文件末尾`，NOT 匹配 `已有段落则跳过`；必须匹配 `唯一` + `rule-config` 的规则来源表述；Must 匹配缓存目录字符串 `cadence/cache/mcp-availability/`
- [ ] **Step 5.2 改写 395-407 行**：删除追加流程；替换为「`.claude/rules/mcp-servers.md` 由 rule-config 权威模板统一生成，本技能不得向其中追加或修改任何内容；本技能职责＝`.mcp.json`、Codex config 配置写入 + `.gitignore` 幂等追加 `cadence/cache/mcp-availability/` 一行 + 指引用户查阅 canonical 规则」
- [ ] **Step 5.3 收敛重复说明**：将 L196-245、L354-392 两段完整智普/MiniMax 说明压缩为各保留配置示例（.mcp.json/Codex 片段必需的环境变量与端点）＋一句「识图决策以 `.claude/rules/mcp-servers.md` 路由小节为准」；删除与 canonical 冲突的自创调用规则表述
- [ ] **Step 5.4 gitignore 条目**：确认 mcp-configuration 的 .gitignore 交接说明含 `cadence/cache/mcp-availability/` 单行精确条目（幂等：已存在则不重复）
- [ ] **Step 5.5 GREEN 验证**: Step 5.1 测试 PASS

### Task 6: 集成 harness 更新与全量回归

**Files:**
- Modify: `cadence-init/skills/rule-config/tests/verify-managed-lifecycle.sh`（fixtures 构造、显式启用用例、根副本校验循环）
- Modify: `cadence-init/skills/rule-config/tests/skill-clause-map.md`、`cadence-init/skills/rule-config/references/merge-semantics.md`
- Modify: `.claude/rules/code-reading.md`（本仓库根副本重生成）
- Delete: `.codegraph/`（本 worktree 现场，人工一次性清理）

**Interfaces:**
- Consumes: Task 2 常量与文件布局
- Produces: 全绿回归基线

- [ ] **Step 6.1 fixtures 双来源化**：定位 `mk_converged_rules`（约 L310-325）与硬编码 converged 内容处，kind 映射同时给 code-usage 与 code-reading 选择来源文件；空项目/drift/幂等各用例的期望内容随之按当前类型取源
- [ ] **Step 6.2 显式启用用例改造**（`it-s8-codegraph-explicit-enable` 约 L1210-1223）：保留「S8 安装执行」断言，新增「.claude/rules/code-reading.md 内容仍为 noncoding 来源、不含 codegraph init 要求」断言
- [ ] **Step 6.3 下游一致性用例**（no-interrupt 忽略提升 / 普通模式提升 / 检测 coding 三类，约 L1235-1306）：断言文案摘要与落地模板随同一 project_type 变化
- [ ] **Step 6.4 根副本特殊映射**（约 L1942-1947 同名校验循环）：code-reading 改为与 `code-reading-noncoding.md` 比较；其余文件保持同名比较
- [ ] **Step 6.5 文档对账**：skill-clause-map.md 涉及 code-reading/DF/S8 行改为新来源描述与新用例 ID；merge-semantics.md「固定落地名+按类型单选来源」补一段 code-reading 说明
- [ ] **Step 6.6 重生成本仓库根副本**：运行 `python3 cadence-init/skills/rule-config/scripts/rule-config.py --help` 确认 CLI 后执行最贴近实际的覆盖方式（或直接 `cp references/rules/code-reading-noncoding.md .claude/rules/code-reading.md`），随后 `diff -q` 校验
- [ ] **Step 6.7 全量回归**
  Run:
  ```bash
  python3 -m unittest cadence-init/skills/rule-config/tests/test_rule_config.py
  bash cadence-init/skills/rule-config/tests/verify-managed-lifecycle.sh
  openspec validate 2026-08-27-mcp-image-route-and-codegraph-typed-source --strict
  git diff --check
  ```
  Expected: unittest OK、harness 退出码 0、validate valid、diff --check 无 whitespace 错误
- [ ] **Step 6.8 终检与现场清理**
  Run:
  ```bash
  git ls-files | grep -E '\.codegraph|mcp-availability' ; # Expected: 空
  grep -RInE '全新 worktree 必须先初始化 CodeGraph|项目必须先执行 .codegraph init|追加到 \`.claude/rules/mcp-servers.md\` 文件末尾' \
    cadence-init/skills/rule-config/references cadence-init/skills/mcp-configuration .claude/rules ; # Expected: 空或仅历史归档外无命中
  rm -rf .codegraph && git status --short
  ```
  Expected: 未跟踪缓存/代码图不入库；活动文件无残留；`.codegraph/` 已清理；改动清单与本计划 Files 区吻合

## Self-Review 结论

- **Spec coverage**：design §4→T2/T6.6；§5→T4；§6→T5；§7 delta 条款→T2/T3/T5/T6 断言面；§8 回归命令→T6.7/T6.8。无遗漏。
- **Placeholder scan**：模板/常量/命令均为实文实码；无 TBD/TODO。
- **Type consistency**：`CODE_READING_SOURCE_MAP`/`CODE_READING_TARGET`/`RULE7_TEXT_*`/路由小节标题在 T1-T6 间命名一致。
