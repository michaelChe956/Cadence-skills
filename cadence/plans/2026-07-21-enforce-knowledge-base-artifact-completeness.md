# KnowledgeBase 技能产物完整性强制 实施 Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为 5 个 KnowledgeBase Skill 补齐模板符合性硬验收、pages→api 候选交接契约与 global-validation 内容完整性维度，使 5 类已知产物缺口在下次执行时必然被拦下。

**Architecture:** 三层强制——产生层（各领域 SKILL.md 完成条件+工作流程）、交接层（api/pages 双侧写死的七字段候选清单契约）、验收层（bootstrap global-validation 四检查）。只改 Markdown，不改 assets 模板与 demo，不写代码。

**Tech Stack:** Markdown 文档编辑；验证用 `grep`/`openspec validate --strict`；回溯验收输入为 `/tmp/knowledge-base-3`（只读，不修改）。

**OpenSpec 契约:** `openspec/changes/2026-07-21-enforce-knowledge-base-artifact-completeness/`（proposal/design/specs/tasks）。本 Plan 只展开该契约的工作包，不重定义范围与验收。

## Global Constraints

- 只修改以下 5 个文件（必要时同步同目录 `references/` 指南以避免冲突）：`cadence-init/skills/{knowledge-base-api,knowledge-base-base-info,knowledge-base-pages,knowledge-base-context,knowledge-base-bootstrap}/SKILL.md`
- 禁止修改：`assets/`、`references/demo*.md`、`knowledge-base-overview`、`knowledge-base-update`、`/tmp/knowledge-base-3`（只读验证输入）
- 新增条目必须可机械判定（每条能客观回答"是/否"），禁止"尽量""视情况"等歧义措辞
- 新增文字全部使用中文，遵循 `.claude/rules/markdown-format.md`（嵌套代码块外层 4 反引号）
- api 与 pages 两侧的候选清单七字段必须逐字段一致：`候选 ID、HTTP Method、标准 Path、前端应用、调用位置（文件+行号）、请求封装链、来源 PAGE/ROUTE ID`
- 每个 Task 完成后单独 commit，commit message 前缀 `docs(openspec-change):`

---

### Task 1: 强化 knowledge-base-api（OpenSpec 工作包 1）

**Files:**
- Modify: `cadence-init/skills/knowledge-base-api/SKILL.md`（"执行模式"、"工作流程 6. 生成能力文档"、"完成条件"三节）

**Interfaces:**
- Consumes: OpenSpec spec 中"配套文件/模板结构/索引双分区/页面链路模式/候选格式"5 条 requirement
- Produces: 候选清单七字段格式（Task 3 的 pages 侧必须逐字段一致）；`API-CANDIDATE-*` 命名

- [ ] **Step 1: 在"执行模式"节"指定模式"之后插入第三模式"页面链路模式"**

在 `### 指定模式` 小节的 4 条之后、`## 能力状态` 之前插入：

```markdown
### 页面链路模式

1. 触发条件：`interfaces/README.md` 对内分区存在 pages 阶段登记的 `API-CANDIDATE-*` 候选清单。
2. 只深挖候选清单内的对内 REST：核实 Controller、路由、服务调用链与数据副作用，按 `references/demo_对内REST.md` 与 `references/demo_对内REST_参数与报文.md` 的格式生成正式接口主文件与配套参数报文文件。
3. 候选升级为稳定 API ID 并回写索引；无法唯一映射的保持候选状态并进入待确认，不凭名称相似度补造正式接口。
4. 不扩大为全量对内盘点，不分析清单外能力；写入门禁与对外/对内分类规则与全量模式一致。

候选清单条目固定七字段（pages 侧写入格式必须与本格式逐字段一致）：

| 候选 ID | HTTP Method | 标准 Path | 前端应用 | 调用位置 | 请求封装链 | 来源 PAGE/ROUTE ID |
|---------|-------------|-----------|----------|----------|------------|---------------------|

标准 Path 必须合并 baseURL、开发代理、BFF 与网关重写规则；调用位置必须含文件与行号。
```

- [ ] **Step 2: 在"工作流程 6. 生成能力文档"追加模板对照自检**

在该节"单个字段缺失不阻断文档生成。"之后追加：

```markdown

### 输出前模板对照自检（强制）

每个接口文档落盘前必须逐节与 assets 模板对照：主文件节序必须等于 `assets/api-capabilities-template.md` 的 11 节（无内容节按规则填`未提供`、`未发现`或`不适用`），配套文件节序必须等于 `assets/api-parameters-message-template.md` 的 5 节。禁止用自创节结构替代模板；自检不通过的文件不得落盘为最终产物。
```

- [ ] **Step 3: 在"完成条件"追加 4 条硬验收**

在 `## 完成条件` 列表中"对外能力完全来自用户清单。"之前插入：

```markdown
- 范围内每个请求响应能力同时存在主文件与 `{标识}_{接口名称}_{API名称}_参数与报文.md` 配套文件，索引"参数与报文"列链接可导航到实际文件；消息、文件、任务等非请求响应能力不创建空配套文件。
- 每个接口主文件遵循 11 节模板结构、配套文件遵循 5 节模板结构，输出前模板对照自检已通过；不存在自创节结构的产物。
- `interfaces/README.md` 同时存在"对外能力"与"对内能力"两个分区；指定模式下无对内盘点结果时，对内分区写明"未盘点"及执行模式原因，不允许整块缺失。
- 存在 `API-CANDIDATE-*` 候选清单时，已进入页面链路模式逐条处理：升级、保持候选并待确认，两种结果均有记录。
```

- [ ] **Step 4: 静态验证**

Run: `grep -c "页面链路模式\|参数与报文.md\|对内能力" cadence-init/skills/knowledge-base-api/SKILL.md`
Expected: ≥ 6；并人工通读新增段落确认无歧义措辞（每条可机械回答是/否）

- [ ] **Step 5: Commit**

```bash
git add cadence-init/skills/knowledge-base-api/SKILL.md
git commit -m "docs(openspec-change): knowledge-base-api 补配套文件/模板结构/双分区硬验收与页面链路模式"
```

---

### Task 2: 强化 knowledge-base-base-info（OpenSpec 工作包 2）

**Files:**
- Modify: `cadence-init/skills/knowledge-base-base-info/SKILL.md`（配置工作流程、"禁止行为"、"完成条件"）

**Interfaces:**
- Consumes: OpenSpec spec 中"配置键完整性/脱敏不省略/模板结构"3 条 requirement
- Produces: 元数据字段名`来源文件键数`、`文档收录键数`（Task 5 的 global-validation 键数一致性检查依赖这两个字段名，必须逐字一致）

- [ ] **Step 1: 在配置工作流程"逐服务记录配置键"步骤后追加键数核对**

找到"逐服务记录配置来源与加载顺序、Profile、配置键、代码绑定、生效条件……"所在步骤，在其后追加：

```markdown
5.1 键数核对（强制）：统计每个来源配置文件的实际键数（按本 Skill 既有去重与合并口径；相同内容文件合并分析时按合并后全集计），与配置文档第 4 节"配置键清单"行数比对；两个数字分别以`来源文件键数`与`文档收录键数`写入该文档元数据表。两者不一致时不得进入下一阶段，先查明并补齐遗漏键。
```

（若原步骤编号序列因此冲突，将后续步骤编号顺延。）

- [ ] **Step 2: 在"禁止行为"或敏感值规则处追加脱敏边界澄清**

在敏感值规则（"所有敏感值和敏感内部地址统一写为 `<redacted>`……"）之后追加：

```markdown
脱敏对象是值而不是键：敏感配置的键名、用途、值类型与敏感级别必须逐键列出，仅值写 `<redacted>`；禁止以敏感为由整条省略配置键，也禁止只写"共 N 个敏感键"的总数替代逐键条目。
```

- [ ] **Step 3: 在"完成条件"追加 3 条硬验收**

在配置相关完成条件处追加（若无配置专节则加在完成条件列表末尾）：

```markdown
- 每个服务配置文档遵循 `assets/service-configuration-template.md` 的 10 节结构（无内容节按规则填`未发现`或`未提供`，不允许整节消失或自创节结构），输出前已逐节与模板对照自检。
- 每个服务配置文档第 4 节配置键清单逐键完整：`来源文件键数` == `文档收录键数`，两个数字已写入元数据表可供机械比对。
- 敏感配置逐键列出键名、用途、值类型与敏感级别，仅值写 `<redacted>`；不存在以敏感为由省略的键。
```

- [ ] **Step 4: 静态验证**

Run: `grep -c "来源文件键数\|文档收录键数\|脱敏对象是值" cadence-init/skills/knowledge-base-base-info/SKILL.md`
Expected: ≥ 4；通读确认无歧义

- [ ] **Step 5: Commit**

```bash
git add cadence-init/skills/knowledge-base-base-info/SKILL.md
git commit -m "docs(openspec-change): knowledge-base-base-info 补配置键完整性/脱敏边界/10节模板硬验收"
```

---

### Task 3: 强化 knowledge-base-pages（OpenSpec 工作包 3）

**Files:**
- Modify: `cadence-init/skills/knowledge-base-pages/SKILL.md`（"前置输入"之后的执行模式相关节、"工作流程 6/7"、"输出"、"完成条件"）

**Interfaces:**
- Consumes: Task 1 的候选清单七字段格式（必须逐字段一致）、`API-CANDIDATE-*` 命名
- Produces: pages 对 `interfaces/README.md` 对内分区的写入授权声明（与 Task 1 api 侧表述一致）

- [ ] **Step 1: 新增"指定模式对象粒度"节**

在"前置输入"节之后（或现有执行模式描述处）插入：

```markdown
## 指定模式对象粒度（强制分流）

Manifest `scope.pages.selected` 条目按粒度分流：

| 粒度 | 处理路径 |
|------|----------|
| 应用级（整个前端应用） | 应用概览文档 + 路由树 + 路由清单 |
| 路由/菜单级（点名菜单 ID、菜单名称或路由 path） | 必须逐路由深挖；只产出应用级概览视为未完成 |

路由/菜单级条目的强制步骤：

1. 菜单→路由定位：按菜单名称或 ID 在路由表、菜单配置与导航代码中定位候选路由，记录定位证据（文件+行号）；无法唯一匹配时列出候选并向用户提问，不凭名称猜测。
2. 每条点名路由生成 `PAGE-*` 页面实体与 `ROUTE-*` 路由实体，单页面文档必须含模板第 3 节（页面能力清单）与第 4.1~4.5 节。
3. 页面全部请求（含经 Store、Hook、Composable、Thunk、Service 与请求封装的间接调用）逐条追踪到 HTTP Method + 标准 Path；已登记的匹配稳定 API ID 并链接 `../interfaces/` 主文件；未登记的按"候选登记契约"处理。

### 候选登记契约（pages 唯一获准写 interfaces/ 的位置）

页面调用但索引中不存在的 REST，必须按以下七字段格式在 `interfaces/README.md` 的"对内能力"分区登记 `API-CANDIDATE-*`（与 knowledge-base-api 页面链路模式的消费格式逐字段一致）：

| 候选 ID | HTTP Method | 标准 Path | 前端应用 | 调用位置 | 请求封装链 | 来源 PAGE/ROUTE ID |
|---------|-------------|-----------|----------|----------|------------|---------------------|

标准 Path 必须合并 baseURL、开发代理、BFF 与网关重写规则；调用位置必须含文件与行号。页面文档链接候选条目，不补造正式接口主文件链接；候选由 knowledge-base-api 页面链路模式升级为正式文档。
```

- [ ] **Step 2: 在"完成条件"追加 3 条硬验收**

```markdown
- 指定模式含路由/菜单级条目时：每条点名路由存在 `PAGE-*`+`ROUTE-*` 稳定 ID、单页面文档与 4.1 映射表（或候选登记记录）；菜单→路由定位证据齐全，定位失败项已经用户澄清或用户明确放弃。
- 全部页面文档中页面→API 引用不得为零链接：每个引用要么是 `../interfaces/` 可导航链接，要么是 `API-CANDIDATE-*` 候选条目链接。
- 候选条目只写入 `interfaces/README.md` 对内分区且为七字段格式；pages 未写 interfaces/ 下任何其他位置。
```

- [ ] **Step 3: 契约一致性检查（与 Task 1 对接）**

Run: `grep -A2 "候选 ID | HTTP Method" cadence-init/skills/knowledge-base-api/SKILL.md cadence-init/skills/knowledge-base-pages/SKILL.md`
Expected: 两个文件的七字段表逐字段一致（候选 ID、HTTP Method、标准 Path、前端应用、调用位置、请求封装链、来源 PAGE/ROUTE ID）

- [ ] **Step 4: Commit**

```bash
git add cadence-init/skills/knowledge-base-pages/SKILL.md
git commit -m "docs(openspec-change): knowledge-base-pages 补指定模式粒度分流/逐路由深挖/候选登记契约"
```

---

### Task 4: 强化 knowledge-base-context（OpenSpec 工作包 4）

**Files:**
- Modify: `cadence-init/skills/knowledge-base-context/SKILL.md`（frontmatter description、"强制边界"、"工作流程 2/7"、"输出契约"、"完成条件"）

**Interfaces:**
- Consumes: OpenSpec spec 中"逐层摘要/输出门禁/准确性自查"3 条 requirement
- Produces: 无下游依赖

- [ ] **Step 1: 强化 frontmatter description 触发语义**

将 description 调整为与其他 Skill 一致的强制语义：

```yaml
description: "MUST use when an agent is about to perform project-specific 需求澄清、Design、Plan、Coding、Testing、Review 或 Debug work and an existing Schema 4.0 KnowledgeBase must ground the task context."
```

- [ ] **Step 2: 在"强制边界"追加逐层门禁条款**

```markdown
- 四条证据路径逐层执行：每层必须输出本层证据摘要（来源、精确位置、本层结论、停止原因）后才允许进入下一层；四条路径各自必须有证据或停止原因，禁止留白方向。
- 默认只扩展一跳；画像必需字段仍缺关键证据时才扩第二跳，扩跳必须记录触发理由。
```

- [ ] **Step 3: 在"输出契约"节追加输出门禁与准确性自查**

在"输出固定包含十三节"列表之后追加：

```markdown
### 输出门禁（强制）

输出上下文包前必须逐项自检：

1. 十三节逐节必填；无内容节写明`无直接关系`或`证据缺失+原因`，不得省略整节。
2. 每个关键结论必须挂稳定 ID + 精确文件/行号，或显式状态（`一致`/`KnowledgeBase 缺失`/`代码缺失`/`数据模型证据缺失`/`配置证据缺失`/`基线漂移`/`来源冲突`/`待确认`）；无载体的结论不得出现在上下文包中。
3. 就绪状态硬性判定：目标实体无法唯一确定、关键冲突会改变任务方向、任务依赖的实际配置不可验证，满足其一时必须判`阻断`。

### 输出前准确性自查（强制，留痕）

1. 稳定 ID 解析复核：引用的每个稳定 ID 读文件确认存在，不凭记忆写 ID。
2. 逐字一致复核：Method+Path、表名、字段名、配置键与来源逐字一致。
3. 候选强制：无法唯一匹配时列出候选清单，禁止挑一个写。
4. 证据矩阵必填：每行结论必须含状态列，状态只使用上述八种枚举。
```

- [ ] **Step 4: 在"完成条件"追加 2 条**

```markdown
- 四条路径均已输出本层证据摘要或停止原因；扩跳均记录了触发理由。
- 输出门禁三项自检与准确性自查四步已通过并留痕；十三节无省略。
```

- [ ] **Step 5: 静态验证**

Run: `grep -c "输出门禁\|准确性自查\|证据摘要" cadence-init/skills/knowledge-base-context/SKILL.md`
Expected: ≥ 6；通读确认无歧义

- [ ] **Step 6: Commit**

```bash
git add cadence-init/skills/knowledge-base-context/SKILL.md
git commit -m "docs(openspec-change): knowledge-base-context 补逐层门禁/输出门禁/准确性自查"
```

---

### Task 5: 强化 knowledge-base-bootstrap global-validation（OpenSpec 工作包 5）

**Files:**
- Modify: `cadence-init/skills/knowledge-base-bootstrap/SKILL.md`（global-validation 检查清单，约 116-119 行所在节）

**Interfaces:**
- Consumes: Task 2 的元数据字段名`来源文件键数`/`文档收录键数`（逐字一致）
- Produces: Task 6 回溯验收使用的四检查清单

- [ ] **Step 1: 在 global-validation 检查清单追加内容完整性维度**

在现有检查条目（"必须核对 Manifest 与输入清单的六领域范围……模板占位符和敏感信息"与"必须显式检索全部服务文档中的待补/已验证为空状态"）之后追加：

```markdown
- `global-validation` 必须追加内容完整性检查，任一不过即判 `failed`（沿用现有失败处理：保持 `in_progress` 与空 `completed_at`，只报告缺失项，不删除产物）：
  1. API 领域适用时：`interfaces/` 下每个请求响应能力主文件存在配套 `_参数与报文.md`；`interfaces/README.md` 同时含"对外能力"与"对内能力"分区（允许"未盘点+原因"，不允许整块缺失）。
  2. 配置为全量或指定时：每个服务配置文档元数据中的`来源文件键数`等于`文档收录键数`。
  3. Pages 适用且 selected 含路由/菜单级条目时：每条点名路由存在 `PAGE-*`+`ROUTE-*` 实体与单页面文档；页面文档的 API 引用不得为零链接（`../interfaces/` 链接或 `API-CANDIDATE-*` 候选条目链接）。
  4. 模板节结构符合性：在占位符检查外增加节序比对——接口主文件 11 节、参数报文 5 节、服务配置文档 10 节、页面文档含第 3/4 节；自创节结构判 `failed`。
```

- [ ] **Step 2: 静态验证**

Run: `grep -c "内容完整性\|来源文件键数\|PAGE-\*" cadence-init/skills/knowledge-base-bootstrap/SKILL.md`
Expected: ≥ 4

- [ ] **Step 3: Commit**

```bash
git add cadence-init/skills/knowledge-base-bootstrap/SKILL.md
git commit -m "docs(openspec-change): bootstrap global-validation 增加内容完整性四检查"
```

---

### Task 6: 回溯验收验证与交付（OpenSpec 工作包 6）

**Files:**
- Read-only: `/tmp/knowledge-base-3/knowledge-base/`（禁止修改）
- Modify: `openspec/changes/2026-07-21-enforce-knowledge-base-artifact-completeness/tasks.md`（勾选工作包）

- [ ] **Step 1: 用新版四检查对旧产物执行回溯验收，逐项记录**

```bash
KB=/tmp/knowledge-base-3/knowledge-base
# 检查1a：请求响应能力主文件是否有配套 _参数与报文.md
ls $KB/interfaces/ | grep -c "_参数与报文"        # 预期 0 → 缺口A命中
# 检查1b：索引是否含对内分区
grep -c "^## 对内" $KB/interfaces/README.md       # 预期 0 → 缺口B命中
# 检查2：CONF-bss 键数一致性
grep -oE '^[A-Za-z0-9_.-]+=' /tmp/env.properties | sort -u | wc -l   # 预期 587
grep -c "来源文件键数\|文档收录键数" $KB/configurations/CONF-bss.md   # 预期 0 → 缺口C命中
# 检查3：PAGE/ROUTE 实体存在性
grep -rl "PAGE-\|ROUTE-" $KB/pages/ | wc -l       # 预期 0 → 缺口D命中
# 检查4：接口主文件节序（11节模板比对）
grep -c "^## " $KB/interfaces/API-3.1-qryUrl.md   # 预期 ≠ 11 → 缺口E命中
```

Expected: 五项检查全部判 `failed`，且缺口 A~E 分别命中"缺配套参数报文/缺对内分区/无键数核对（587 vs 实际收录 27）/无 PAGE 实体/主文件非 11 节"。**任何一项已知缺口漏报，回到对应 Task 修订检查条目后重跑本步骤。**

- [ ] **Step 2: 新增完成条件可判定性审查**

通读 Task 1-5 全部新增条目，逐条确认可机械回答"是/否"；发现"尽量/视情况/必要时"等措辞就地改为硬性表述。

- [ ] **Step 3: 契约一致性复查**

Run: `grep -h "候选 ID | HTTP Method" cadence-init/skills/knowledge-base-api/SKILL.md cadence-init/skills/knowledge-base-pages/SKILL.md | sort -u | wc -l`
Expected: `1`（两侧表头逐字段一致）

- [ ] **Step 4: OpenSpec 校验与任务勾选**

```bash
openspec validate 2026-07-21-enforce-knowledge-base-artifact-completeness --strict
```

Expected: `is valid`。随后在 `tasks.md` 勾选 1.1~6.1 全部工作包。

- [ ] **Step 5: Commit**

```bash
git add openspec/changes/2026-07-21-enforce-knowledge-base-artifact-completeness/tasks.md
git commit -m "docs(openspec-change): 回溯验收通过（failed 命中全部五类已知缺口），勾选全部工作包"
```

---

## Self-Review 记录

- **Spec 覆盖**：14 条 requirement → Task 1（4 条）、Task 2（3 条）、Task 3（3 条）、Task 4（3 条）、Task 5（1 条）、Task 6（1 条），无遗漏。
- **占位符扫描**：无 TBD/TODO；所有插入文本为完整内容。
- **一致性**：候选七字段、`来源文件键数`/`文档收录键数`、`API-CANDIDATE-*` 命名在 Task 1/2/3/5/6 间逐字一致。
