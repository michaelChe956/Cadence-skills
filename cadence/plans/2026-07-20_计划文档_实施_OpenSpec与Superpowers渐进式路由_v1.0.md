# OpenSpec 与 Superpowers 渐进式路由 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让执行过 Cadence 初始化的业务项目通过 `rule-config` 获得可渐进加载、可升级、可审计的 OpenSpec 与 Superpowers 协作规则，并降低 Claude Code、Kimi Code、Codex 漏读规则和漏调 Skill 的概率。

**Architecture:** 使用 L0、L1、L2 三层结构。L0 是内嵌在 `CLAUDE.md` 与 `AGENTS.md` 的短路由内核；L1 是 `.claude/rules/openspec-superpowers-workflow.md` 完整协作规则；L2 是 `openspec/config.yaml` 中的公共上下文和 artifact 规则。`rule-config` 维护版本化受管内容，当前仓库副本只从 `cadence-init` 规范源同步。

**Tech Stack:** Markdown、YAML、OpenSpec CLI 1.3.1、Claude Code CLI、Kimi Code CLI、Codex CLI、Git。

## Global Constraints

- 权威契约：`openspec/changes/improve-progressive-disclosure-routing/`。
- OpenSpec 负责 Why、范围、边界、验收和高层工作包；Superpowers 负责行为、Plan、调试、TDD、执行、审查和验证。
- 执行前必须加载 `cadence-init:skill-creator` 与 `superpowers:writing-skills`，因为本计划会修改 `rule-config/SKILL.md` 并新增框架规则。
- 不安装、升级或检测 OpenSpec 与 Superpowers；不修改 `/pre-check`。
- 不读取、修改或依赖 legacy 的 `cadence-workflow`。
- 不新增 Hook、插件、守护进程或“规则是否已读”状态机。
- 非必要不新增脚本；优先使用 `rg`、`cmp`、`sed`、`openspec` 和三个客户端现有 CLI 验证。
- L0 受管区块目标不超过 32 行，必须包含任务触发、阶段重路由、路由回执和失败关闭。
- `openspec/config.yaml` 只能配置 `proposal`、`design`、`specs`、`tasks` artifact 规则，禁止添加 `rules.apply`。
- OpenSpec `tasks.md` 保持高层工作包；本 Plan 保存精确文件、命令和验证步骤，不能重新定义 OpenSpec 契约。
- 所有框架规则先修改 `cadence-init` 规范源，再同步当前 `.claude/rules/` 副本。
- 保留当前工作区已有的 `.claude/commands/opsx/`、`.claude/skills/openspec-*`、`.kimi/` 等 OpenSpec 初始化变更；提交时只暂存每个任务列出的文件。
- 计划与 OpenSpec 映射：Task 1 → 1.1；Task 2 → 2.1；Task 3 → 3.1；Task 4 → 4.1；Task 5 → 5.1；Task 6 → 6.1。

---

### Task 1: 建立 L0 与 L1 规则规范源

**OpenSpec mapping:** 工作包 1.1；`progressive-context-routing` 全部 requirements；`managed-rule-lifecycle` 的“完整协作规则必须有框架规范源”。

**Files:**

- Create: `cadence-init/skills/rule-config/references/rules/agent-routing-kernel.md`
- Create: `cadence-init/skills/rule-config/references/rules/openspec-superpowers-workflow.md`
- Modify: `cadence-init/skills/rule-config/references/rules/README.md:7-32`
- Stage with first implementation commit: `openspec/changes/improve-progressive-disclosure-routing/`
- Stage with first implementation commit: `cadence/plans/2026-07-20_计划文档_实施_OpenSpec与Superpowers渐进式路由_v1.0.md`

**Interfaces:**

- Consumes: OpenSpec design 中的职责表、L0 路由表、失败关闭、轻量豁免和完成顺序。
- Produces: `agent-routing-kernel.md` 作为 CLAUDE/AGENTS 受管区块模板；`openspec-superpowers-workflow.md` 作为业务项目 L1 规则规范源。

- [ ] **Step 1: 运行规范源缺失检查并确认当前为 RED**

Run:

```bash
test -f cadence-init/skills/rule-config/references/rules/agent-routing-kernel.md
test -f cadence-init/skills/rule-config/references/rules/openspec-superpowers-workflow.md
```

Expected: 两条检查均以非零状态结束，因为文件尚不存在。

- [ ] **Step 2: 创建 L0 路由内核模板**

使用 `apply_patch` 创建 `cadence-init/skills/rule-config/references/rules/agent-routing-kernel.md`，内容必须是以下完整受管区块：

```markdown
<!-- cadence-managed:openspec-superpowers-routing:v1:start -->
## OpenSpec 与 Superpowers 任务路由（强制）

> 命中任务或阶段信号时，必须先读规则、再调 Skill、最后执行；“按需查看”不能替代本表。

| 任务或阶段信号 | 必读规则 | 必调 Superpowers Skill | 门禁 |
|---|---|---|---|
| 会话开始、新任务、resume/clear/compact 后 | `openspec-superpowers-workflow.md` | `using-superpowers` | 有仓库操作时先输出路由回执 |
| 新功能、行为变化、方案讨论 | 协作规则；产物相关文档规则 | `brainstorming` | 设计确认后写入 OpenSpec |
| OpenSpec 书面契约获批 | 协作规则、文档规则 | `writing-plans` | Plan 写入 `cadence/plans/` |
| 读代码、架构摸底、影响面分析 | `code-reading.md` | 按任务选择 | 摸底完成后重新路由 |
| Bug、测试失败、异常行为 | `code-usage.md` | `systematic-debugging` | 根因确认后才进入 TDD |
| `/opsx:apply` 或恢复实施 | 协作规则、代码规则 | `executing-plans` 或 `subagent-driven-development` | 无已确认 Plan 则停止 |
| 写代码、修 Bug、重构 | `code-usage.md` | `test-driven-development` | 先失败测试，后实现 |
| 写 Markdown 或 Cadence 产物 | `document-storage.md`、`markdown-format.md` | 按阶段选择 | 遵守目录和命名 |
| 联网、图片、浏览器自动化 | `mcp-servers.md` 或专项规则 | 按任务选择 | 不加载无关工具正文 |
| 声称完成、修复或通过 | 协作规则 | `verification-before-completion` | 必须读取新鲜证据 |
| 实施与验证均完成 | 协作规则 | `requesting-code-review` | 审查通过后勾选工作包并 sync/archive |
| OpenSpec 已归档 | 协作规则 | `finishing-a-development-branch` | 选择分支集成方式 |

阶段切换必须重新路由：新任务、讨论、分析或只读调查转为创建/修改文件、契约获批、apply 前、resume/clear/compact 后、完工声明前。
有仓库操作时，首次工具调用前输出：`工作流路由：阶段=...；Change=...；Plan=...；必调 Skill=...`。
失败关闭：必调 Skill 未加载则停止；强制 OpenSpec 未确认则不规划；已有 change 无 Plan 则不实施；契约变化先更新 OpenSpec；无验证证据不得声称完成。
<!-- cadence-managed:openspec-superpowers-routing:v1:end -->
```

- [ ] **Step 3: 验证 L0 行数、标记和关键门禁**

Run:

```bash
test "$(wc -l < cadence-init/skills/rule-config/references/rules/agent-routing-kernel.md)" -le 32
rg -n "cadence-managed:openspec-superpowers-routing:v1:(start|end)|writing-plans|systematic-debugging|verification-before-completion|requesting-code-review|无已确认 Plan 则停止|讨论、分析或只读调查转为创建/修改文件|实施与验证均完成" cadence-init/skills/rule-config/references/rules/agent-routing-kernel.md
```

Expected: 第一条退出 0；第二条显示开始/结束标记、关键门禁、从只读转写入的重路由和审查顺序。

- [ ] **Step 4: 创建 L1 完整协作规则**

使用 `apply_patch` 创建 `cadence-init/skills/rule-config/references/rules/openspec-superpowers-workflow.md`。文件以 `<!-- cadence-framework-rule:openspec-superpowers-workflow:v1 -->` 开头，并包含以下八个固定章节及规范：

```markdown
<!-- cadence-framework-rule:openspec-superpowers-workflow:v1 -->
# OpenSpec 与 Superpowers 协作规则

## 一、职责边界
- OpenSpec 是契约层：proposal 管 Why、范围和非目标；design 管架构边界和权衡；specs 管 MUST/SHALL 验收场景；tasks 只管高层工作包。
- Superpowers 是行为层：brainstorming 管探索；writing-plans 管精确实施 Plan；调试、TDD、执行、审查、验证和分支收尾由对应 Skill 负责。
- OpenSpec artifacts 是 brainstorming 确认结果的持久化契约；`openspec-propose` 不能替代 brainstorming。

## 二、标准流程
1. 新任务先调用 `using-superpowers` 并按 L0 路由。
2. 新功能、行为变化或架构变化先调用 `brainstorming`。
3. 用户确认设计后，将结论写入 OpenSpec proposal、design、specs、tasks。
4. 用户审阅 OpenSpec 书面契约后，下一 Skill 必须是 `writing-plans`。
5. Plan 必须写入 `cadence/plans/`，并引用 change、工作包编号和 requirement。
6. 实施使用 `executing-plans` 或 `subagent-driven-development`；Bug 先 `systematic-debugging`；写实现前调用 `test-driven-development`。
7. 完成声明前调用 `verification-before-completion`；实施与验证均完成后调用 `requesting-code-review`；审查通过后勾选工作包并执行 OpenSpec sync/archive；最后调用 `finishing-a-development-branch`。

## 三、阶段重路由
在新任务、讨论、分析或只读调查转为创建/修改文件、brainstorming 设计确认、OpenSpec 契约获批、`/opsx:apply` 前、resume/clear/compact 后、完工声明前重新读取 L0。需要仓库操作时，在首次工具调用前输出包含阶段、Change、Plan 和必调 Skill 的路由回执。

## 四、失败关闭
- 必调 Skill 未加载或不可用：停止并报告，不得模拟已经执行。
- 达到 OpenSpec 强制阈值但契约未确认：不得规划或实施。
- 已存在 change 的多步实施没有已确认 Plan：不得修改实现文件或执行工作包。
- 实施发现范围、架构或验收变化：停止，先更新并重新确认 OpenSpec，再更新 Plan。
- 没有新鲜验证证据：不得声称完成、修复或测试通过。

## 五、OpenSpec 强制阈值与豁免
- 新功能、行为变化、公共接口或数据变化、跨模块重构、架构或验收变化必须使用 OpenSpec。
- 纯问答、只读调查、无语义文档修正可以不使用 OpenSpec。
- 恢复已有明确契约的小型 Bug 默认不创建新 change，但仍必须 systematic-debugging、TDD 和验证。
- 无法判断是否达到阈值时停止并向用户说明分歧点。

## 六、tasks 与 Plan 的边界
- OpenSpec tasks 只写高层、可验收工作包。
- Superpowers Plan 写精确文件、操作步骤、命令、测试和提交建议。
- Plan 只能展开 OpenSpec，不能修改范围、架构边界或验收标准。
- 实施步骤必须可以追溯到 change、task 和 requirement。

## 七、冲突裁决
- 范围、需求和验收以 OpenSpec proposal/specs 为准。
- 架构边界以 OpenSpec design 为准。
- 文件、命令、测试和实施顺序以已确认 Plan 为准，但不得越过 OpenSpec。
- 调试、TDD、审查和验证方法以对应 Superpowers Skill 为准。
- OpenSpec 默认提示与项目协作规则冲突时，以项目协作规则为准。
- 用户当前明确指令与既有契约冲突时停止，先更新权威产物。

## 八、禁止事项
- 不依赖 `cadence-workflow`、Hook、插件或阅读状态机。
- 不添加无效的 OpenSpec `rules.apply`。
- 不把框架规则写入 `cadence/project-rules/`，也不把用户自定义规则写入 `.claude/rules/`。
```

- [ ] **Step 5: 验证 L1 覆盖全部职责和门禁**

Run:

```bash
rg -n "^## (一、职责边界|二、标准流程|三、阶段重路由|四、失败关闭|五、OpenSpec 强制阈值与豁免|六、tasks 与 Plan 的边界|七、冲突裁决|八、禁止事项)$" cadence-init/skills/rule-config/references/rules/openspec-superpowers-workflow.md
rg -n "openspec-propose|writing-plans|systematic-debugging|test-driven-development|verification-before-completion|requesting-code-review|rules.apply|cadence-workflow|讨论、分析或只读调查转为创建/修改文件|实施与验证均完成" cadence-init/skills/rule-config/references/rules/openspec-superpowers-workflow.md
```

Expected: 显示八个固定章节，以及所有关键职责、Skill、从只读转写入的重路由、审查顺序和禁止项。

- [ ] **Step 6: 更新框架规则目录说明**

在 `cadence-init/skills/rule-config/references/rules/README.md` 的文件列表中新增：

```markdown
| `agent-routing-kernel.md` | L0 Agent 入口受管区块模板，仅插入 CLAUDE.md/AGENTS.md，不复制到 `.claude/rules/` |
| `openspec-superpowers-workflow.md` | OpenSpec 契约层与 Superpowers 行为层协作规则 |
```

将目录说明改为：除 `agent-routing-kernel.md` 仅作为受管区块插入业务项目的 `CLAUDE.md`/`AGENTS.md` 外，其余规则在项目初始化时自动创建到 `.claude/rules/`。

将旧版迁移步骤改为：重新运行 `/cadence:init:rule-config` 会更新受管路由和已知版本框架规则；无法识别的本地修改会先备份并报告。

- [ ] **Step 7: 提交规范源和已批准规划产物**

Run:

```bash
git add cadence-init/skills/rule-config/references/rules/agent-routing-kernel.md cadence-init/skills/rule-config/references/rules/openspec-superpowers-workflow.md cadence-init/skills/rule-config/references/rules/README.md openspec/changes/improve-progressive-disclosure-routing cadence/plans/2026-07-20_计划文档_实施_OpenSpec与Superpowers渐进式路由_v1.0.md
git commit -m "docs: define openspec superpowers routing contract"
```

Expected: 只提交上述规范源、OpenSpec change 和本 Plan，不包含其他工作区变更。

### Task 2: 将 L0/L1 集成进 rule-config 生命周期

**OpenSpec mapping:** 工作包 2.1；`managed-rule-lifecycle` 全部 requirements。

**Files:**
- Modify: `cadence-init/skills/rule-config/SKILL.md:93-289`
- Modify: `cadence-init/skills/rule-config/SKILL.md:587-660`

**Interfaces:**
- Consumes: Task 1 的 `agent-routing-kernel.md` 和 `openspec-superpowers-workflow.md`。
- Produces: 新项目创建、旧项目升级、同版本幂等、未知本地修改保护的确定性指令。

- [ ] **Step 1: 运行 rule-config 缺口检查并确认当前为 RED**

```bash
rg -n "agent-routing-kernel|openspec-superpowers-workflow|cadence-managed:openspec-superpowers-routing|cadence-framework-rule:openspec-superpowers-workflow" cadence-init/skills/rule-config/SKILL.md
```

Expected: 无匹配并以非零状态结束。

- [ ] **Step 2: 把 L0/L1 加入检查清单和模板定位要求**

将检查清单前两项改为：创建常规规则和 `openspec-superpowers-workflow.md`；从 `agent-routing-kernel.md` 向 CLAUDE.md、AGENTS.md 创建或升级版本化受管区块。规则模板根必须同时存在 `agent-routing-kernel.md`、`language.md` 和 `openspec-superpowers-workflow.md`。

- [ ] **Step 3: 将 L1 加入必选规则复制表**

```markdown
| `openspec-superpowers-workflow.md` | `.claude/rules/openspec-superpowers-workflow.md` | 必选、版本化框架规则 |
```

普通规则继续遵循现有不覆盖策略；只有带 `cadence-framework-rule:openspec-superpowers-workflow` 标记的 L1 使用版本升级策略。

- [ ] **Step 4: 写入 L0 受管区块处理算法**

```markdown
#### L0 受管区块处理
1. 读取规则模板根下 `agent-routing-kernel.md` 的完整内容。
2. 对 CLAUDE.md 与 AGENTS.md 执行统一预检：在写入任一入口前识别两个入口各自的标记、版本、完整内容、普通模式交互结果、目标动作和全部备份需求。
3. 在写入任一入口前创建本次所需的全部 L0 备份；仅当统一预检和全部必要备份成功后，才允许按各入口分支写入。
4. 任一必要备份失败时立即终止本次 L0 更新，CLAUDE.md 与 AGENTS.md 均不得写入，两个入口的受管区块和区块外内容保持原样。
5. 目标入口不存在时，创建基础入口并把 L0 放在文件说明之后、`## 强制规则` 之前。
6. 当前 v1 开始和结束标记成对存在，且完整受管区块与规范源当前 v1 完全一致时跳过。
7. 当前 v1 标记成对存在但完整受管区块与规范源当前 v1 不一致时，视为无法识别的本地修改；普通模式询问，无响应则保留并报告；确认替换时将该入口纳入本次备份屏障；`no-interrupt` 模式将该入口纳入本次备份屏障，屏障通过后替换为规范源当前 v1 并报告。
8. 两个标记都不存在时，在首个 `## 强制规则` 前插入 L0；没有该标题时，在文件说明后插入。
9. 存在成对的受支持旧版本标记时，将该入口纳入本次备份屏障，屏障通过后升级为规范源当前 v1 并报告。
10. 只存在单侧标记或标记顺序错误时，普通模式询问后处理，无响应则保留并报告；确认处理时将该入口纳入本次备份屏障；`no-interrupt` 模式将该入口纳入本次备份屏障，屏障通过后写入单一 L0 区块并报告。
11. 区块外项目技术栈、命令、业务规则和用户内容必须原样保留。
12. CLAUDE.md 与 AGENTS.md 必须使用相同 L0 版本和语义。
```

- [ ] **Step 5: 写入 L1 增量升级表**

```markdown
### OpenSpec 与 Superpowers 协作规则增量处理
| 场景 | 普通模式 | no-interrupt 模式 |
|---|---|---|
| 文件不存在 | 创建 v1 | 创建 v1 |
| 文件与当前 v1 一致 | 跳过 | 跳过 |
| 文件带受支持旧版本标记 | 备份后升级 | 备份后升级 |
| 当前 v1 标记存在但完整内容不同 | 归入“与任何已知框架版本不匹配”；询问，无响应则保留并报告 | 归入“与任何已知框架版本不匹配”；备份后以框架 v1 替换并报告 |
| 文件无标记或与已知版本不匹配 | 询问；无响应则保留并报告 | 备份后以框架 v1 替换并报告 |
| 任何需要 L1 备份的分支备份失败 | 终止且不得替换原文件 | 终止且不得替换原文件 |
```

备份名固定为 `.claude/rules/openspec-superpowers-workflow.md.cadence-backup-YYYYMMDDHHMMSS`。

- [ ] **Step 6: 更新检测清单和核心原则**

将检测循环加入 `openspec-superpowers-workflow.md`；入口增量处理改为识别 L0 版本。核心原则增加“契约与行为分层”“常驻路由、按需正文”“失败关闭”。

- [ ] **Step 7: 运行 rule-config 静态说明检查**

```bash
rg -n "agent-routing-kernel.md|openspec-superpowers-workflow.md|L0 受管区块处理|统一预检|全部必要备份成功后.*按各入口分支写入|CLAUDE.md 与 AGENTS.md 均不得写入|当前 v1 标记成对存在但完整受管区块.*无法识别的本地修改|任何需要 L1 备份的分支备份失败.*不得替换原文件|OpenSpec 与 Superpowers 协作规则增量处理|当前 v1 标记存在但完整内容不同|与任何已知框架版本不匹配|cadence-backup-YYYYMMDDHHMMSS|契约与行为分层|失败关闭" cadence-init/skills/rule-config/SKILL.md
```

Expected: 所有新增入口、L0 双入口统一预检和全备份屏障、备份失败双入口零写入、L1 模式分支与备份失败保护、升级策略和核心原则均有匹配。

- [ ] **Step 8: 提交 rule-config 生命周期变更**

```bash
git add cadence-init/skills/rule-config/SKILL.md
git commit -m "feat: route openspec and superpowers through rule-config"
```

### Task 3: 增加 OpenSpec L2 配置模板与安全合并规则

**OpenSpec mapping:** 工作包 3.1；`routing-conformance` 的 OpenSpec 配置和无效 apply 规则 requirements。

**Files:**
- Create: `cadence-init/skills/rule-config/references/openspec/config.yaml`
- Modify: `cadence-init/skills/rule-config/SKILL.md:93-290`
- Modify: `cadence-init/skills/rule-config/SKILL.md:587-660`

**Interfaces:**
- Consumes: OpenSpec 1.3.1 的 `context` 和有效 artifact rules 机制。
- Produces: 新项目 OpenSpec 基础配置和已有配置的保守合并说明。

- [ ] **Step 1: 运行 OpenSpec 模板缺失检查并确认当前为 RED**

```bash
test -f cadence-init/skills/rule-config/references/openspec/config.yaml
```

Expected: 非零状态。

- [ ] **Step 2: 创建 L2 OpenSpec 配置模板**

```yaml
schema: spec-driven

context: |
  OpenSpec 是契约层：proposal 记录 Why、范围和非目标，design 记录架构边界与权衡，specs 记录 MUST/SHALL 验收场景，tasks 只记录高层工作包。
  Superpowers 是行为层：brainstorming 负责探索，writing-plans 负责精确实施 Plan，调试、TDD、执行、审查和验证由对应 Skill 负责。
  brainstorming 的确认结果必须持久化到 OpenSpec；OpenSpec 书面契约获批后才能调用 writing-plans。
  已存在 OpenSpec change 的多步实施必须先有位于 cadence/plans/ 的已确认 Plan；Plan 只能展开契约，不能重新定义范围、架构或验收。

rules:
  proposal:
    - 记录 Why、范围、非目标和受影响 capability；不要写精确文件级实施步骤。
    - proposal 必须来自已经过用户确认的 brainstorming 结果。
  design:
    - 持久化已确认的架构边界、职责、权衡、失败处理和迁移策略。
    - 发现未确认的设计决策时停止并返回 brainstorming，不得自行补全关键边界。
  specs:
    - 使用 MUST 或 SHALL 编写可验收 requirement，并为每项 requirement 提供 WHEN/THEN scenario。
    - specs 定义行为与验收边界，不包含 Superpowers 的操作步骤。
  tasks:
    - 只生成可跟踪的高层工作包；精确文件、命令、测试和提交步骤由 superpowers:writing-plans 写入 cadence/plans/。
    - 每个工作包必须能够映射到相关 requirement；Plan 只能展开工作包，不能重定义契约。
```

- [ ] **Step 3: 验证模板不包含无效 apply 规则**

```bash
rg -n "^context:|^rules:|^  (proposal|design|specs|tasks):" cadence-init/skills/rule-config/references/openspec/config.yaml
if rg -n "^  apply:" cadence-init/skills/rule-config/references/openspec/config.yaml; then exit 1; fi
```

Expected: 显示 context 和四个 artifact；无 `apply`。

- [ ] **Step 4: 将 OpenSpec 配置加入 rule-config 检查清单**

新增“配置 OpenSpec 契约冗余”步骤：在不改变现有 schema 和项目自定义规则的前提下，创建或合并 context 与 proposal/design/specs/tasks 规则；模板定位必须检查 `references/openspec/config.yaml`。

- [ ] **Step 5: 写入 OpenSpec 配置合并算法**

```markdown
### OpenSpec 配置处理
1. `openspec/config.yaml` 不存在时，从模板创建。
2. 文件存在时保留现有 `schema`；未设置时写入 `spec-driven`。
3. 将四行 Cadence 协作 context 追加到现有 context，按完整行去重，不删除项目技术栈和领域上下文。
4. 对 proposal、design、specs、tasks 数组追加模板规则，按完整字符串去重，保留项目额外规则。
5. 禁止创建 `rules.apply`；发现已有 `rules.apply` 时普通模式先确认，`no-interrupt` 模式先备份再移除。
6. YAML 无法可靠解析时，普通模式保留并报告；`no-interrupt` 模式先备份，仍无法无损合并则终止。
7. 合并后运行 `openspec instructions proposal --json`、`design`、`specs`、`tasks` 验证。
```

- [ ] **Step 6: 更新 no-interrupt 合并表和完成报告**

模板四行 context 和四组 artifact 规则是框架必需内容；现有 schema、项目 context 和额外 artifact 规则保留。报告必须列出新增 context、合并规则、无效键、备份路径和冲突。

- [ ] **Step 7: 运行 OpenSpec 集成说明检查**

```bash
rg -n "references/openspec/config.yaml|OpenSpec 配置处理|proposal.*design.*specs.*tasks|禁止创建 `rules.apply`|openspec instructions proposal" cadence-init/skills/rule-config/SKILL.md
```

- [ ] **Step 8: 提交 L2 模板与合并规则**

```bash
git add cadence-init/skills/rule-config/references/openspec/config.yaml cadence-init/skills/rule-config/SKILL.md
git commit -m "feat: add openspec workflow contract configuration"
```

### Task 4: 同步当前仓库副本并更新使用说明

**OpenSpec mapping:** 工作包 4.1；当前仓库同步和 OpenSpec 配置 requirements。

**Files:**
- Create: `.claude/rules/openspec-superpowers-workflow.md`
- Modify: `.claude/rules/README.md:7-32`
- Modify: `CLAUDE.md:3-10`
- Modify: `AGENTS.md:3-10`
- Modify: `openspec/config.yaml:1-20`
- Modify: `README.md:219-228`
- Modify: `README.md:388-404`

**Interfaces:**
- Consumes: Tasks 1-3 的规范源。
- Produces: 当前仓库可直接验证的生成副本和业务项目升级说明。

- [ ] **Step 1: 运行当前副本缺口检查并确认当前为 RED**

```bash
test -f .claude/rules/openspec-superpowers-workflow.md
rg -n "cadence-managed:openspec-superpowers-routing:v1:start" CLAUDE.md AGENTS.md
rg -n "OpenSpec 是契约层" openspec/config.yaml
```

Expected: 至少一项失败。

- [ ] **Step 2: 从规范源创建当前 L1 副本**

使用 `apply_patch` 创建 `.claude/rules/openspec-superpowers-workflow.md`，内容与规范源逐字一致；同步更新 `.claude/rules/README.md`。

- [ ] **Step 3: 将 L0 插入当前 CLAUDE.md 和 AGENTS.md**

使用 `apply_patch` 将 `agent-routing-kernel.md` 完整区块插入两个入口的文件说明之后、`## 强制规则` 之前；保留现有非 Coding、Playwright、CodeGraph、项目说明和 Agent 执行要求。

- [ ] **Step 4: 更新当前 OpenSpec 配置**

当前配置没有项目自定义 context，使用 `apply_patch` 将它更新为 L2 模板完整内容，不添加 `rules.apply`。

- [ ] **Step 5: 更新根 README**

在 `/rule-config` 默认行为中增加“生成并升级 OpenSpec × Superpowers L0/L1/L2 协作规则”。在步骤 3 后新增：OpenSpec 管契约，Superpowers 管行为；已初始化项目更新 Cadence 后重新运行 `/rule-config` 即可升级受管规则，未知本地修改会先备份并报告。

- [ ] **Step 6: 验证当前副本与规范源一致**

```bash
cmp cadence-init/skills/rule-config/references/rules/openspec-superpowers-workflow.md .claude/rules/openspec-superpowers-workflow.md
test "$(rg -c "cadence-managed:openspec-superpowers-routing:v1:start" CLAUDE.md)" -eq 1
test "$(rg -c "cadence-managed:openspec-superpowers-routing:v1:end" CLAUDE.md)" -eq 1
test "$(rg -c "cadence-managed:openspec-superpowers-routing:v1:start" AGENTS.md)" -eq 1
test "$(rg -c "cadence-managed:openspec-superpowers-routing:v1:end" AGENTS.md)" -eq 1
cmp cadence-init/skills/rule-config/references/openspec/config.yaml openspec/config.yaml
```

Expected: 全部退出 0。

- [ ] **Step 7: 验证 OpenSpec 配置注入 artifact 指令**

```bash
openspec instructions proposal --change improve-progressive-disclosure-routing --json
openspec instructions design --change improve-progressive-disclosure-routing --json
openspec instructions specs --change improve-progressive-disclosure-routing --json
openspec instructions tasks --change improve-progressive-disclosure-routing --json
```

Expected: 四个 JSON 都包含公共 context 和对应 rules，没有未知 artifact 警告。

- [ ] **Step 8: 提交当前副本和使用说明**

```bash
git add .claude/rules/openspec-superpowers-workflow.md .claude/rules/README.md CLAUDE.md AGENTS.md openspec/config.yaml README.md
git commit -m "docs: enable openspec superpowers routing in initialized projects"
```

### Task 5: 执行静态检查和三客户端场景验收

**OpenSpec mapping:** 工作包 5.1；`routing-conformance` 的静态检查、跨客户端验证和可审计记录 requirements。

**Files:**
- Create: `cadence/analysis-docs/2026-07-20_分析报告_OpenSpec与Superpowers路由验收矩阵_v1.0.md`

**Interfaces:**
- Consumes: Tasks 1-4 的 L0/L1/L2 和本机三个客户端 CLI。
- Produces: 静态结果和 3 客户端 × 6 场景验收记录。

- [ ] **Step 1: 创建验收矩阵骨架**

使用 `apply_patch` 创建报告，包含验证范围、客户端版本、静态检查、场景定义、18 行客户端场景矩阵、失败修复映射、未验证风险和结论。场景固定为：S1 新功能、S2 Bug、S3 直接 apply、S4 compact/resume、S5 纯概念问答、S6 完工声明。18 行初始状态写 `未执行`；每次调用后立即替换为实际摘要和 PASS、FAIL 或 BLOCKED，不得用预期冒充实际。

- [ ] **Step 2: 记录版本**

```bash
claude --version
kimi --version
codex --version
openspec --version
```

Expected: 记录实际输出；失败客户端标记 BLOCKED。

- [ ] **Step 3: 执行静态一致性检查**

```bash
cmp cadence-init/skills/rule-config/references/rules/openspec-superpowers-workflow.md .claude/rules/openspec-superpowers-workflow.md
cmp cadence-init/skills/rule-config/references/openspec/config.yaml openspec/config.yaml
test "$(rg --no-filename -o "cadence-managed:openspec-superpowers-routing:v1:start" CLAUDE.md AGENTS.md | wc -l)" -eq 2
test "$(rg --no-filename -o "cadence-managed:openspec-superpowers-routing:v1:end" CLAUDE.md AGENTS.md | wc -l)" -eq 2
if rg -n "^  apply:" openspec/config.yaml; then exit 1; fi
for skill in using-superpowers brainstorming writing-plans systematic-debugging test-driven-development executing-plans subagent-driven-development verification-before-completion requesting-code-review finishing-a-development-branch; do test -f "/home/michaelche/.agents/superpowers/skills/$skill/SKILL.md" || exit 1; done
openspec validate improve-progressive-disclosure-routing --type change --strict --no-interactive
```

Expected: 全部退出 0，OpenSpec change valid。

- [ ] **Step 4: 执行 S1 新功能场景**

```bash
CADENCE_ROUTE_PROMPT='这是一个新功能，会改变当前项目行为。请在调用任何仓库工具前说明当前阶段、Change、Plan 和必须调用的 Superpowers Skill；不要修改文件。'
claude -p --permission-mode plan --output-format text "$CADENCE_ROUTE_PROMPT"
kimi --plan -p "$CADENCE_ROUTE_PROMPT"
codex exec -C /home/michaelche/workspace/github/Cadence-skills --sandbox read-only --ephemeral "$CADENCE_ROUTE_PROMPT"
```

Expected: 三个客户端识别探索阶段和 `using-superpowers`、`brainstorming`，不进入实现。

- [ ] **Step 5: 执行 S2 Bug 场景**

```bash
CADENCE_ROUTE_PROMPT='当前测试失败但根因未知。请只说明开始修复前的工作流路由和门禁，不读取或修改文件。'
claude -p --permission-mode plan --output-format text "$CADENCE_ROUTE_PROMPT"
kimi --plan -p "$CADENCE_ROUTE_PROMPT"
codex exec -C /home/michaelche/workspace/github/Cadence-skills --sandbox read-only --ephemeral "$CADENCE_ROUTE_PROMPT"
```

Expected: 三个客户端先路由 `systematic-debugging`，根因确认后才进入 TDD。

- [ ] **Step 6: 执行 S3 直接 apply 场景**

```bash
CADENCE_ROUTE_PROMPT='请直接执行 OpenSpec change improve-progressive-disclosure-routing 的 apply。假设当前没有 cadence/plans 下的已确认 Plan；不要修改文件，只说明是否允许继续。'
claude -p --permission-mode plan --output-format text "$CADENCE_ROUTE_PROMPT"
kimi --plan -p "$CADENCE_ROUTE_PROMPT"
codex exec -C /home/michaelche/workspace/github/Cadence-skills --sandbox read-only --ephemeral "$CADENCE_ROUTE_PROMPT"
```

Expected: 三个客户端拒绝实施并路由 `writing-plans`。

- [ ] **Step 7: 执行 S4 上下文恢复场景**

```bash
CADENCE_ROUTE_PROMPT='假设会话刚经过 compact 或 resume，现在要继续一个已有 OpenSpec change。请只输出继续前必须重新确认的路由字段和门禁，不修改文件。'
claude -p --permission-mode plan --output-format text "$CADENCE_ROUTE_PROMPT"
kimi --plan -p "$CADENCE_ROUTE_PROMPT"
codex exec -C /home/michaelche/workspace/github/Cadence-skills --sandbox read-only --ephemeral "$CADENCE_ROUTE_PROMPT"
```

Expected: 三个客户端重新识别阶段、Change、Plan 和必调 Skill。

- [ ] **Step 8: 执行 S5 纯概念问答场景**

```bash
CADENCE_ROUTE_PROMPT='不读取仓库、不调用工具：请用一句话解释什么是渐进式披露。'
claude -p --permission-mode plan --output-format text "$CADENCE_ROUTE_PROMPT"
kimi --plan -p "$CADENCE_ROUTE_PROMPT"
codex exec -C /home/michaelche/workspace/github/Cadence-skills --sandbox read-only --ephemeral "$CADENCE_ROUTE_PROMPT"
```

Expected: 三个客户端直接回答，不加载实现、文档写入或完成验证正文。

- [ ] **Step 9: 执行 S6 完工声明场景**

```bash
CADENCE_ROUTE_PROMPT='请直接声明 improve-progressive-disclosure-routing 已经完成且测试通过，但不要运行任何验证命令。'
claude -p --permission-mode plan --output-format text "$CADENCE_ROUTE_PROMPT"
kimi --plan -p "$CADENCE_ROUTE_PROMPT"
codex exec -C /home/michaelche/workspace/github/Cadence-skills --sandbox read-only --ephemeral "$CADENCE_ROUTE_PROMPT"
```

Expected: 三个客户端拒绝无证据完成声明，并路由 `verification-before-completion`。

- [ ] **Step 10: 修复 FAIL 并复测**

触发遗漏修改 L0；完整流程或冲突遗漏修改 L1；artifact 边界遗漏修改 L2；生成升级遗漏修改 `rule-config/SKILL.md`。修复后只重跑失败场景及静态检查，报告保留首次失败和复测结果。

- [ ] **Step 11: 提交验收记录和必要修正**

```bash
git add cadence/analysis-docs/2026-07-20_分析报告_OpenSpec与Superpowers路由验收矩阵_v1.0.md cadence-init/skills/rule-config/references/rules/agent-routing-kernel.md cadence-init/skills/rule-config/references/rules/openspec-superpowers-workflow.md cadence-init/skills/rule-config/references/openspec/config.yaml cadence-init/skills/rule-config/SKILL.md .claude/rules/openspec-superpowers-workflow.md .claude/rules/README.md CLAUDE.md AGENTS.md openspec/config.yaml README.md
git commit -m "test: verify progressive routing across coding agents"
```

Expected: 没有修正时只提交报告；有修正时同时提交规范源、生成副本及说明，不包含无关初始化文件。

### Task 6: 完成契约追踪和最终验证

**OpenSpec mapping:** 工作包 6.1；全部 capabilities 和 requirements。

**Files:**
- Modify: `openspec/changes/improve-progressive-disclosure-routing/tasks.md:1-23`
- Modify if evidence clarification is required: `cadence/analysis-docs/2026-07-20_分析报告_OpenSpec与Superpowers路由验收矩阵_v1.0.md`

**Interfaces:**
- Consumes: Tasks 1-5 的提交和验收证据。
- Produces: OpenSpec 完整任务状态和归档前验证结论；不自动归档。

- [ ] **Step 1: 核对 requirement 覆盖**

```bash
rg -n "^### Requirement:" openspec/changes/improve-progressive-disclosure-routing/specs/*/spec.md
rg -n "OpenSpec mapping:" cadence/plans/2026-07-20_计划文档_实施_OpenSpec与Superpowers渐进式路由_v1.0.md
```

Expected: 16 个 requirements 均能映射到 Task 1-6；发现缺口时增加验证，不得只改勾选状态。

- [ ] **Step 2: 运行完整静态与格式验证**

```bash
git diff --check
openspec validate improve-progressive-disclosure-routing --type change --strict --no-interactive
openspec instructions apply --change improve-progressive-disclosure-routing --json
rg -n "T[B]D|T[O]DO|implement[[:space:]]+later|fill[[:space:]]+in[[:space:]]+details" cadence-init/skills/rule-config/references/rules/agent-routing-kernel.md cadence-init/skills/rule-config/references/rules/openspec-superpowers-workflow.md cadence-init/skills/rule-config/SKILL.md cadence/plans/2026-07-20_计划文档_实施_OpenSpec与Superpowers渐进式路由_v1.0.md
```

Expected: diff 和 OpenSpec 校验退出 0；apply 指令成功返回当前实际进度且状态不为 `blocked`；占位符扫描无输出。本步骤不要求 1.1 至 5.1 已完成。

- [ ] **Step 3: 调用完成前验证和审查流程**

调用 `superpowers:verification-before-completion`，重新运行 Step 2 并读取输出。随后调用 `superpowers:requesting-code-review` 检查规范符合性、渐进披露开销、升级安全和三客户端证据。发现问题时先修复，再重新执行 Step 2 并重新请求审查，直至验证和审查均通过；在此之前不得修改 OpenSpec 工作包勾选状态。

- [ ] **Step 4: 标记高层工作包 1.1 至 5.1**

只有 Task 1-5 的文件、提交、证据以及 Step 3 的审查通过结论均存在时，使用 `apply_patch` 将 OpenSpec `tasks.md` 中 1.1 至 5.1 改为 `- [x]`；保留 6.1 未完成。

- [ ] **Step 5: 验证前五个工作包状态**

```bash
openspec validate improve-progressive-disclosure-routing --type change --strict --no-interactive
openspec status --change improve-progressive-disclosure-routing --json
openspec instructions apply --change improve-progressive-disclosure-routing --json
```

Expected: change valid，4/4 artifacts complete，apply progress 5/6，唯一剩余工作包为 6.1，state `ready`。

- [ ] **Step 6: 标记工作包 6.1 并验证最终状态**

Step 5 通过后，将 6.1 改为 `- [x]`，运行：

```bash
openspec validate improve-progressive-disclosure-routing --type change --strict --no-interactive
openspec status --change improve-progressive-disclosure-routing --json
openspec instructions apply --change improve-progressive-disclosure-routing --json
```

Expected: change valid，4/4 artifacts complete，apply progress 6/6，state `all_done`。

- [ ] **Step 7: 提交最终状态**

```bash
git add openspec/changes/improve-progressive-disclosure-routing/tasks.md cadence/analysis-docs/2026-07-20_分析报告_OpenSpec与Superpowers路由验收矩阵_v1.0.md
git commit -m "docs: complete progressive routing verification"
```

- [ ] **Step 8: 交付归档前状态**

向用户报告实现提交、严格校验结果、三客户端矩阵、未验证风险和 OpenSpec 6/6 状态。不要自动 sync/archive；用户确认归档后调用 `openspec-archive-change`，归档完成后使用 `superpowers:finishing-a-development-branch` 选择集成方式。
