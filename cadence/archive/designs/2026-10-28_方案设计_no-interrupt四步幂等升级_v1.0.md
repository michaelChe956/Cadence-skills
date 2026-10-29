# no-interrupt 四步初始化幂等升级方案设计

> **实施状态（2026-10-29）**：核心闭环已实现，并通过样例实跑与全量测试；P1 的入口 per-unit 基线、历史模板快照、模型裁决层（`decisions.json`）与 `review` 闭环按用户裁决**不实现**。工具只保证「不丢内容 + 写前备份 + 幂等」，初始化完成后由用户自行比对文件。

- 状态：核心已实现；P1 增强项按用户裁决不实现（见上方说明）
- 日期：2026-10-28
- 适用步骤：`pre-check`、`mcp-configuration`、`rule-config`、`project-rules-examples`
- 关联证据：`/tmp/test-center-java`（重跑前）、`/tmp/cadence-rerun-copy.gv4wXW`（真实执行 `rule-config apply --no-interrupt` 后的副本）

## 1. 背景

全新项目以 `--no-interrupt` 完成四步初始化后，用户会修改规则：入口 `CLAUDE.md` / `AGENTS.md`、`.claude/rules/*.md`、`cadence/project-rules/**`、MCP 配置等。之后 Skills 升级或用户误操作，再次执行同样的四步 no-interrupt，期望：

1. 框架受管内容与最新 Cadence-skills 一致；
2. 人工修改的规则优先级高于最新框架要求；
3. 全程不提问，零静默丢失，失败可恢复。

当前实现不满足。实测在项目副本上执行 `rule-config apply --no-interrupt`：

| 项 | 结果 |
|---|---|
| 退出码 / overall | `0` / `ok` |
| `CLAUDE.md` / `AGENTS.md` | `updated` / `skip-backfill` |
| `report.backups` | `[]` |
| `cadence/legacy/` 新增归档 | 无 |
| 用户引用表行 | 被删除 |
| `CLAUDE.md` 规则 6 的 `.claude/rules/` | 被覆盖为 `rules/` |

这不是单点删除分支的问题，而是缺少“上次框架版本基线”和稳定“单元身份”。现有四套机制各自为政：

| 机制 | 现状 | 根因 |
|---|---|---|
| L0 / codex-inline 标记区块 | drift 整块替换 | 无法区分区块内用户改动与框架旧文 |
| `.claude/rules/*.md` | 内容不等于模板即整文件覆盖 | 无 base，用户改过与框架旧版同样处理 |
| project-rules 模板 | 模型执行“模板权威合并” | 非确定性、无成功备份、会重写用户正文 |
| MCP | 缺失即加回；同名传输字段框架胜 | 无法区分“没装过”与“用户删除” |

## 2. 目标与非目标

### 2.1 目标

- 四步 no-interrupt 可重复执行；第二次运行零写入、零备份。
- 任何改变既有文件字节的写入，写入前都有归档。
- 用户编辑 `.claude/rules` 不丢：框架文件保持纯净，用户差异自动抽取到 overlay。
- 入口中的用户新增内容不被删除、不被重排、不被压缩空行。
- project-rules 模板不再由模型做语义合并；脚本确定性合并，用户正文优先。
- MCP 缺失的默认 server 重跑补回；已有同名 server 的用户值优先。
- 存量项目无基线时，按保守模式保留用户内容并报告框架更新 pending。
- dry-run 与 apply 的写集合一致；失败可回滚。

### 2.2 非目标

- 不改变 KnowledgeBase 的初始化/更新语义。
- 不在本期实现跨客户端 include 的统一加载协议。
- 不自动判断语义冲突（例如新增框架规则与用户规则含义矛盾）；只报告 `pending`。
- 不删除、不改写用户显式保留的 `cadence/project-rules/` 顶层文件。

## 3. 用户裁决

| # | 决策 | 落地方式 |
|---|---|---|
| D1 | `.claude/rules` 框架文件保持纯净，用户修改自动抽取到 overlay | 7 个框架文件逐字节等于当前模板；差异写入 `.claude/rules/user-<name>.md` |
| D2 | project-rules 采用“章节清单框架保证 + 正文用户所有” | 只补缺失章节；已存在章节正文用户优先；取消“项目补充” |
| D3 | 安全类单元框架优先 | `.gitignore` 保护项、permission deny 等框架胜，强警告；提供显式逃生口 |
| D4 | 状态文件本地保存，不提交 VCS | `cadence/framework-state/` 本地目录，内部 `.gitignore` 忽略内容 |
| D5 | 缺失默认 MCP server 重跑补回 | 每次重跑补回；报告 `MCP_SERVER_RESTORED`；用户删除不是持久禁用 |

## 4. 不变量

| ID | 不变量 | 检验 |
|---|---|---|
| I1 | 框架最新：用户未改的单元运行后等于当前模板 | 单元级 sha 对比 |
| I2 | 用户优先：用户改动区域运行后原样存在；冲突时用户胜，框架新文本进 `pending` | 判定表 + 夹具 |
| I3 | 零静默丢失：被删除的行必须能证明属于框架已知文本/历史/退役清单/计划内删除，否则中止 | loss guard |
| I4 | 确定性：输出只取决于磁盘、模板、状态、显式标志；合并路径不含模型与时间戳 | 同输入双跑字节一致 |
| I5 | 幂等：第二次运行写集合为空、归档为空 | 双跑 diff |
| I6 | 可恢复：任何改变既有文件字节的写入先归档到 `cadence/legacy/<ts>/<rel>`，失败按 journal 回滚 | 故障注入 |
| I7 | 失败关闭：归档、发布、manifest、loss guard 失败时零净变更并非零退出 | 注入测试 |
| I8 | 不提问：no-interrupt 全程无交互；冲突由 `pending` 承载 | 报告无问题通道 |

## 5. 目标架构

### 5.1 资产分类

| 类别 | 资产 | 策略 |
|---|---|---|
| F 框架文件（用户可改但文件保持纯净） | `.claude/rules/{language,code-usage,document-storage,markdown-format,mcp-servers,code-reading,openspec-superpowers-workflow,playwright}.md` | 未改自动升级；改过抽取到 overlay；文件本体始终等于当前模板 |
| R 共享入口区块 | L0 路由区块、`## 强制规则` 的 H3 条目、`## 项目配置` 开关 | H3 条目级三方合并；条目外用户内容逐字保留；冲突用户胜 |
| T 模板型 | `cadence/project-rules/README.md`、`examples/*.md` | 章节级三方合并；章节清单框架保证，正文用户所有 |
| S 结构化键集合 | `.mcp.json`、`.codex/config.toml`、`openspec/config.yaml`、settings 权限、`.gitignore` | 按键/行判定；用户值优先；安全单元例外由 D3 决定 |
| D 纯派生 | codex-inline 区块、`.omp/AGENTS.md`、`.agents/rules` 软链 | 从源重生成；用户手改先归档并报告 |
| U 用户独占 | `cadence/project-rules/` 顶层文件、额外 MCP server、`cadence/**` 产物 | 不碰 |

### 5.2 状态与基线

```text
cadence/framework-state/
├── .gitignore              # 内容固定：*\n!.gitignore\n
├── manifest.json           # schema、模板摘要、单元状态
├── base/<sha256>           # 框架渲染文本基线；不含用户内容与密钥
├── pending/<unit>/<sha>    # 被用户挡住的最新框架文本
├── journal.json            # 本次运行前像/后像哈希
└── .lock
```

manifest 单元示例：

```json
{
  "schema": 1,
  "skill": {"release": "2026-10-28", "templates_digest": "..."},
  "units": {
    "entry:CLAUDE.md:mandatory:项目个性化规则": {
      "class": "R",
      "path": "CLAUDE.md",
      "locator": "## 强制规则/### 6. 项目个性化规则",
      "base_sha": "...",
      "last_user_sha": "...",
      "disposition": "managed"
    },
    "rules:language.md": {
      "class": "F",
      "path": ".claude/rules/language.md",
      "base_sha": "...",
      "disposition": "managed"
    }
  }
}
```

基线来源优先级：

1. manifest 中记录的 `base_sha` 与 `base/` 快照；
2. 入口受管块的内联 `v` + `sha` 标记，按 skill 侧历史版本回放；
3. `cadence/legacy/` 中最近一次含该文件的归档；
4. 当前模板与当前文件的内容精确匹配某历史版本；
5. 以上皆无 → 保守模式，`base = null`，报告 `UNIT_UNKNOWN_BASE_KEPT`。

禁止把“当前模板”或“当前文件”直接当 base：

- 以当前模板为 base 会把所有差异误判为用户修改，导致框架旧文永远不升级。
- 以当前文件为 base 会把所有模板变化误判为框架新变更，导致用户修改被覆盖。

### 5.3 三方判定表

| # | 关系 | 动作 | 报告 |
|---|---|---|---|
| 1 | `D == L` | 不动 | `unchanged` |
| 2 | `D == B`，`L != B` | 写入 `L` | `upgraded` |
| 3 | `D != B`，`L == B` | 保留 `D` | 无 |
| 4 | `D`、`B`、`L` 两两不同，改动不重叠 | 合并两边 | `merged` |
| 5 | 双方改同一区域 | 用户行保留，框架新版进 `pending` | `UNIT_CONFLICT_USER_WINS` |
| 6 | 双方在同一锚点纯插入 | 框架在前、用户在后，均保留 | `merged` |
| 7 | 框架新增单元 | 插入 | `added` |
| 8 | 用户删除单元 | 不加回（安全单元除外，见 D3） | `UNIT_TOMBSTONED` |
| 9 | 框架移除单元，`D == B` | 删除并归档 | `removed` |
| 10 | 框架移除单元，`D != B` | 保留为用户内容 | `UNIT_ORPHANED_KEPT` |
| 11 | 无基线 | 保守：保留 `D`，框架更新进 `pending` | `UNIT_UNKNOWN_BASE_KEPT` |
| 12 | 无法解析 | 单元不动，整体 `degraded` | `UNIT_UNPARSEABLE` |

冲突优先级：

```text
显式状态（pinned/tombstone/alias/detached） > 用户改动 D > 框架新版 L > 基线 B
```

## 6. `.claude/rules`：纯净框架文件 + overlay

### 6.1 文件布局

```text
.claude/rules/
├── language.md                    # 框架文件，逐字节等于当前模板
├── code-usage.md
├── document-storage.md
├── markdown-format.md
├── mcp-servers.md
├── code-reading.md
├── openspec-superpowers-workflow.md
├── user-language.md               # 用户覆盖 overlay
├── user-code-usage.md
└── ...
```

规则：

- 框架文件只由 `rule-config` 写入，内容等于当前模板；用户直接修改后，下一次运行抽取差异并恢复框架文件。
- overlay 命名为 `user-<框架文件名>`，放在 `.claude/rules/` 平级，确保 Claude Code 自动加载、omp 桥接（`.agents/rules/*.md`）和 Codex 内联投影都能看到。
- overlay 是用户可见文件；自动抽取区之外的内容不被框架改写。
- 策略同步变更：`.claude/rules/` 从“仅框架文件”扩展为“框架文件 + `user-*.md` overlay”。规则 6 与 `.claude/rules/document-storage.md` 的文案必须同步改为“禁止修改 7 个框架文件；用户覆盖写入 `user-*.md`”，否则新机制与现行“禁止在 `.claude/rules` 添加用户规则”冲突。
- `cadence/project-rules/` 仍是长期项目规则的推荐目录；`user-*.md` 只承载对框架文件的局部覆盖，不替代 project-rules。

### 6.2 overlay 结构

```markdown
<!-- cadence-user-overlay: rule=language base=v2026-10-28 -->
# 用户覆盖：language.md

> 本文件内容优先级高于 `.claude/rules/language.md` 中对应规则。

<!-- cadence-overlay:extracted:start -->
## 用户新增
...

## 用户替换
### 框架原文
...
### 用户文本
...

## 用户禁用
- `<稳定行 ID 或原文哈希>`
<!-- cadence-overlay:extracted:end -->

<!-- 用户手写区：以下内容不会被自动改写 -->
...
```

抽取规则：

- `D == B`：无用户改动，不生成/不改写 overlay。
- `D != B`：计算 `diff(B, D)`：
  - 插入 → “用户新增”；
  - 修改 → “用户替换”，同时保留框架原文与用户文本；
  - 删除 → “用户禁用”，记录稳定行 ID；无稳定 ID 时记录原文哈希。
- 抽取完成后，框架文件 `:= L`，写入前归档。
- `diff` 失败或无基线：把 `D` 与 `L` 的全部差异放入“用户新增/替换”，标 `provisional`，报告 `BASE_MISSING`，不删除任何用户行。
- overlay 已存在且已有自动抽取区：更新该区，保留区外手写内容；抽取区内容按 `base` + 文本哈希去重。
- 第二次运行：框架文件 `== L`，overlay 不变，零写入。

### 6.3 客户端可见性

- Claude Code：`.claude/rules/*.md` 平级扫描，overlay 可见。
- omp：`.agents/rules/` 桥接源为 `.claude/rules/*.md`（排除 `README.md`），overlay 自动建链。
- Codex：`AGENTS.md` 的 codex-inline 区块由 `.claude/rules/*.md` 渲染，overlay 会进入投影；超过 60 行预算时沿用现有截断并报告 `CODEX_INLINE_TRUNCATED`，全文仍在 `.claude/rules/`。
- 其他客户端：通过入口规则 6 的说明“用户覆盖见 `.claude/rules/user-*.md`”引导读取。

## 7. 入口 CLAUDE.md / AGENTS.md

### 7.1 所有权

- L0 区块：框架受管，标记对圈定；用户改动进入三方合并，冲突进 `pending`。
- `## 强制规则`：按 H3 条目切分。H3 标题去编号、去尾部括号后与规范标题匹配：
  - 匹配 → 受管条目，三方合并框架正文与用户追加内容；
  - 不匹配 → 用户条目，整块逐字保留，不重排、不改编号。
- `## 项目配置`：只管理“产物自动提交”开关行；其他内容逐字保留。
- 章节外内容：逐字保留。

### 7.2 关键修复

1. owner 判定只看 H3 标题，不再用 marker 子串。任何用户行出现 `cadence/project-rules/`、`.claude/rules/<file>` 都不得触发删除。
2. 用户块按原始行序列保留，包括空行、表格、围栏代码块；仅在段边界归一为恰好一个空行。
3. `RULE6_BLOCK_CLAUDE` 的 `rules/` 改为 `.claude/rules/`，与 AGENTS 版及 `document-storage.md` 对齐；规则 6 文案同步改为“7 个框架文件不得修改；用户覆盖写入 `.claude/rules/user-*.md`”。
4. 开关值支持 `开启/打开/启用/on` 与 `关闭/关掉/禁用/off`；原值不改写，报告 `TOGGLE_ALIAS_KEPT`。
5. 双入口开关值不一致时，以 CLAUDE.md 为准同步 AGENTS.md，报告 `ENTRY_TOGGLE_PROPAGATED`。
6. 用户自定义 H3 编号冲突时保留用户编号，报告 `USER_HEADING_NUMBER_COLLISION`。

### 7.3 冲突呈现

同一受管条目内用户与框架改同一行时：

- 受管条目保留最新框架正文；
- 用户行追加到该条目的“用户覆盖”引用块，声明优先级高于上方框架条目；
- 框架新版被挡住的文本写入 `pending/`，报告 `UNIT_CONFLICT_USER_WINS`。

## 8. project-rules / examples

### 8.1 职责重划

- `project-rules-examples` 只拥有 `cadence/project-rules/README.md` 与 `examples/*.md`。
- **不再写 `CLAUDE.md` / `AGENTS.md`**；入口规则 6 由 `rule-config` 唯一拥有，消除两个所有者冲突。
- 目标不存在：创建模板，记录 `base = 模板`。
- 目标存在：脚本执行章节级三方合并，不再由模型做语义合并。

### 8.2 合并规则

- 章节身份：标题级别 + 去编号标题文本（沿用 NB-01），去尾部括号限定。
- 必备章节清单由框架保证：缺失的章节从模板追加，报告 `framework-section-added`。
- 已存在章节：
  - 正文 `== base` → 升级为最新模板正文；
  - 正文 `!= base` → 保留用户正文；模板该章节的新增行进 `pending`。
- 用户独有章节：保留。
- 不再生成“项目补充”章节。
- Markdown 无法可靠解析：保留原文件，整体 `degraded`，不写标准结构。
- 任何写入前归档到 `cadence/legacy/<ts>/cadence/project-rules/...`。

### 8.3 项目事实定制

- 只对**本次新建**的 `design-template.md` 等文件做项目事实定制。
- 已存在文件不重写、不重新定制。
- 定制后的内容视为用户修改；`base` 仍保持为框架模板，不能把定制结果当 base，否则下次升级会误判为用户未改而丢失定制。

## 9. MCP

### 9.1 合并行为

| 场景 | 动作 |
|---|---|
| 文件不存在 | 创建全部默认 server，建立 manifest |
| 缺失默认 server | **补回**，报告 `MCP_SERVER_RESTORED`（按 D5） |
| 同名 server 的 `type/command/url` | 用户值优先；框架值进 `pending` |
| `args` | 框架必需参数在前，项目不重复参数追加 |
| `env/headers/http_headers/扩展字段` | 按键合并；用户非占位值优先；用户是占位符则取框架值 |
| 项目额外 server | 保留 |
| 无法解析 | 不写、不重建；保持原文件，整体 `degraded`，候选进 `pending` |

### 9.2 备份与安全

- 任何对 `.mcp.json` / `.codex/config.toml` 的写入前归档到 `cadence/legacy/<ts>/<rel>`。
- 废弃根目录 `<file>.cadence-backup-<ts>` 备份方式，统一到 `cadence/legacy`。
- 报告中不输出真实密钥，只输出变量名与“已保留非占位值”。
- 用户删除默认 server 不是持久禁用；重跑会补回。若需持久禁用，后续以显式配置/标志扩展，不在本期实现。

## 10. 派生区块与 omp

- codex-inline：每次从 `.claude/rules/*.md`（含 `user-*.md`）重生成；用户手改区块时先归档并报告 `DERIVED_BLOCK_EDITED`。
- `.omp/AGENTS.md`：整文件受管，重生成；改动前归档。
- `.agents/rules/`：软链桥，源为 `.claude/rules/*.md`；同名普通文件归档后替换并报告 `OMP_BRIDGE_USER_FILE_KEPT`；非管线文件逐字保留。
- `pre-check`：不写项目规则。运行 OpenSpec/Superpowers 投影前后记录哈希；用户改过的投影被外部命令覆盖时，归档并报告 `EXTERNAL_PROJECTION_USER_EDIT_OVERWRITTEN`。

## 11. 安全单元

以下单元按 D3 框架优先：

- `.gitignore` 中保护 `.mcp.json`、`.codex/config.toml`、`.worktrees/`、`cadence/cache/mcp-availability/` 的条目；
- `settings.json` 的受管 deny 条目。

行为：

- 框架条目保留；用户反向允许规则被移除或不被采纳；
- 报告 `SECURITY_UNIT_FRAMEWORK_WINS`，列出被覆盖的用户行；
- 提供显式逃生口 `--allow-security-override`，仅在用户明确调用时按用户值执行，并在报告中标记高风险。

## 12. no-interrupt 事务语义

1. **计划**：读取全部资产，计算候选内容、写集合、备份集合；dry-run 与 apply 共用同一计划函数。
2. **备份屏障**：写集合中任何既有文件，先复制到 `cadence/legacy/<ts>/<相对路径>`，并写 journal（前像/后像哈希）。任一备份失败 → 零写入、退出 1。
3. **发布**：按固定顺序原子写入；每次写后回读校验。
4. **回滚**：任一写入失败，按 journal 恢复已写文件，退出 1。
5. **loss guard**：对每个文本文件，`D 中有而 M 中没有` 的行必须属于 base/history/退役清单/journal 的 `intended_removals`；否则中止。
6. **manifest**：全部成功后最后写入。
7. **幂等**：第二次运行 `D == L` 或 `D == last_user`，写集合为空、备份为空。

报告扩展现有 schema：

- 保留 `overall`、`steps[]`、`actions[]`、`backups[]`、`warnings[]`、`failure{}`；
- 新增 `pending[]`、`overrides[]`、`ownership[]`、`base_status[]`、`loss_guard`；
- 新增 warning code：`BASE_MISSING`、`UNIT_CONFLICT_USER_WINS`、`UNIT_TOMBSTONED`、`UNIT_UNKNOWN_BASE_KEPT`、`UNIT_UNPARSEABLE`、`MCP_SERVER_RESTORED`、`MCP_USER_VALUE_KEPT`、`SECURITY_UNIT_FRAMEWORK_WINS`、`DERIVED_BLOCK_EDITED`、`TOGGLE_ALIAS_KEPT`、`CODEX_INLINE_TRUNCATED`。

退出码保持 0/1/2/77。内容级冲突不失败关闭，`overall=ok` 且 `attention_required>0`；无法解析/外部工具失败为 `degraded`；基础设施失败为 `fail` + 退出 1。

## 13. 存量迁移

### 13.1 顺序

1. **只读预检**：清点受管/共享资产与哈希，生成 dry-run 预览。
2. **全量归档**：`CLAUDE.md`、`AGENTS.md`、`.claude/rules/*`、`.mcp.json`、`.codex/config.toml`、`openspec/config.yaml`、`.claude/settings.json`、`cadence/project-rules/**`、`.gitignore` 全部复制到 `cadence/legacy/<ts>/`，写 `MIGRATION.json`。任一归档失败 → 零写入。
3. **基线推断**：
   - 精确匹配 skill 历史模板 → 该版本为 base；
   - 最近祖先相似度匹配 → 该版本为 base；
   - `cadence/legacy` 有最近归档 → 归档为 base；
   - 以上皆无 → 保守模式。
4. **逐单元合并**，写 manifest。
5. **校验**：用户内容零丢失；立即第二次运行必须零写入。

### 13.2 保守模式

- 入口：H3 标题归属；用户条目逐字保留；受管条目按最新模板重建，用户行保留为追加/覆盖。
- `.claude/rules`：当前文件与当前模板的差异全部抽到 `user-<name>.md`，框架文件重置为模板；报告 `BASE_MISSING`。
- project-rules：只补缺失章节，已有正文全部保留。
- MCP：缺失默认 server 补回；已有 server 用户值优先。
- 保守模式的代价：无法区分“旧框架文本”和“用户修改”，可能把旧框架文本抽进 overlay；但不会丢用户字节。后续有基线后收敛。

## 14. 测试与验收

### 14.1 单元

- H3 标题归属：用户行含 `cadence/project-rules/` 不被删除。
- 用户表格/围栏/空行逐字保留。
- `RULE6_BLOCK_CLAUDE` 含 `.claude/rules/`，与 AGENTS 版一致。
- overlay 抽取：新增、替换、禁用；二次运行不变。
- 开关别名 `打开`；双入口同步。
- skip-backfill 写入必须进入备份集合。
- MCP 缺失默认补回；同名用户值保留；占位符/密钥规则。
- project-rules 章节合并：缺失补齐、正文用户优先、无“项目补充”。
- 安全单元框架优先与警告。
- loss guard：未归属删除行必须中止。

### 14.2 集成

- 样例副本 `/tmp/test-center-java`：重跑后两张引用表完整、规则 6 为 `.claude/rules/`、自定义规则 8 保留、`打开` 保留。
- 首次重跑：`cadence/legacy/<ts>/CLAUDE.md` 与 `AGENTS.md` 存在。
- 第二次重跑：零写入、零备份、全部 `unchanged`。
- `rule-config`、`mcp-configuration`、`project-rules-examples` 串行四步两次：第二次全部无写。
- 故障注入：备份失败、发布失败、manifest 损坏、lock 争用、非法 JSON/TOML/YAML。

### 14.3 验收

I1–I8 全部自动化断言；样例 S-01–S-20 通过；`merge-semantics.md` 与 `skill-clause-map.md` 同步更新。

## 15. 分期

| 期 | 内容 | 验收 |
|---|---|---|
| P0 止血 | H3 归属、空行/围栏保留、规则 6 路径、凡写即备份、开关别名、最小 loss guard；project-rules 停止模型合并/停止写入口；MCP 缺失默认补回、同名用户值优先 | 样例零丢失；首次重跑有归档；第二次零写入 |
| P1 基线与三方 | manifest、base 快照、history、overlay 抽取、三方判定、pending、dry-run 对账、journal 回滚 | 框架升级与用户修改正确区分；冲突不静默 |
| P2 迁移与收口 | 存量迁移、legacy 反推 base、保守模式、文档/条款表更新、完整回归 | 存量项目可重复迁移且幂等 |

P0 先独立交付，保证“不丢、不静默覆盖”；P1 才实现“未改动的框架旧文精确升级”。

## 16. 风险

| 风险 | 缓解 |
|---|---|
| 无基线时把旧框架文本抽进 overlay | 只影响 overlay 噪声，不丢用户字节；`BASE_MISSING` 报告；有基线后收敛 |
| overlay 与框架文件重复导致内容冗余 | overlay 仅在用户改动时生成；报告 `overrides[]`；用户可清理 |
| Codex 60 行预算截断 overlay | 现有截断行为；报告 `CODEX_INLINE_TRUNCATED`；全文保留在 `.claude/rules/` |
| 安全单元框架优先破坏用户工作流 | 强警告 + `--allow-security-override` 显式逃生口 |
| 状态目录本地导致换机后回到保守模式 | 保守模式仍零丢失；可选后续提供状态导出/导入 |
| `rule-config.py` 单文件重构面大 | P0 先局部修；P1 新模块化文件；测试先行 |
| 外部 CLI 覆盖投影 | pre-check 记录哈希并归档报告；本期不保留合并 |

## 17. 实现细节与默认选择

以下为实现默认值，不再阻塞设计评审：

1. overlay 命名与位置：`.claude/rules/user-<框架文件名>`；框架文件保持纯净，overlay 与框架文件平级，保证三端可见。
2. 入口用户覆盖呈现：受管 H3 条目内优先三方合并；只有同一行冲突时才在该条目后追加“用户覆盖”块。
3. 安全逃生口：提供 `--allow-security-override`，默认关闭；使用后报告高风险。
4. MCP 持久禁用：本期不提供；按 D5，缺失默认 server 每次重跑补回。后续如需持久禁用，再以显式配置扩展。
