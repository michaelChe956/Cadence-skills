证据核对完毕。现有 `run_eval.py` 只测"skill 描述是否被触发"，且硬绑定 `claude -p` CLI + `--model`，不测 workflow 顺序、不测工具选择、不支持 codex/pi/kimi。这决定了目标B 的路线是"扩展它"而非"另建"。

---

# 决策咨询结论

## 继承的既定决策（作为基线契约）

| 已定决策 | 出处 |
|---|---|
| L0 路由内核瘦身至 ≤2KB，删姿态条款、只留可判定门禁 | `archive/2026-08-21-slim-l0-routing-kernel-v3`；实测 `agent-routing-kernel.md` = 2501 B |
| 规则文件"框架权威全覆盖"，drift 即覆盖，不做章节合并 | `2026-08-01-framework-authoritative-rule-files` |
| 规则下发脚本化（`rule-config.py` dry-run/apply、原子写、备份） | `2026-07-31-script-rule-config-for-speed` |
| CI 明确不启动真实四客户端 CLI job | `.github/workflows/ci.yml` 注释 |
| 本仓库是非编码项目，不建代码图 | `.claude/rules/code-reading.md` |
| 四 harness 平权分发（Claude Code / Codex / pi / Kimi） | `install.sh` 三层软链 |

**核心历史结论**：仓库对"遵循率"的唯一系统性回应是 —— 可判定门禁 > 姿态类约束。你的目标A 必须建在这个结论上，而不是重新写更长的规则。

## 诊断

三类违规不是同一个病，混在一起治会白花工。

```
①跳 workflow    ←→ 时序约束（改代码前必须已有 spec/plan）→ 可用文件系统状态判定 → 可硬拦截
②不用 codegraph  ←→ 工具偏好（有更省事的 grep 可用）→ 可用工具白名单判定 → 可硬拦截（Claude/Cursor）
③不用 MCP        ←→ 同②，但 MCP 工具名可枚举 → 权限层最容易强制
```

三者都属于 researcher 引的官方定调："CLAUDE.md 是上下文，不是强制配置；要真正阻断动作请用 PreToolUse hook"。而 scout 已确认：**本仓库当前没有任何 hook、git hook 或 CI 门禁拦截 agent 行为**，硬约束全部集中在安装/下发脚本层（install.sh 所有权证明、rule-config.py 退出码）。这是空白点，也是最高性价比的着手处。

一个你可能没意识到的杠杆：`②③` 的失败模式很可能不是"agent 不听话"，而是**规则根本没被加载**。researcher 给出 Cursor 场景的实证（frontmatter 挂载模式配错 = 规则完全没加载）。你的分发链路有四层软链 + rule-config 写入 + L0 区块版本升级（v1/v2/v3），任一环节 drift 都表现为"agent 不遵循"。**在归因到模型不听话之前，必须先证明规则确实进了上下文。**

## 漂移 / 矛盾检查

- **矛盾1（重要）**：目标B 想要"跨 agent × 跨 model 测试"，但 `.github/workflows/ci.yml` 里有明文决策"不启动真实四客户端 CLI job"。这条决策必须被显式修订，否则目标B 无法落地。建议的修订方式不是推翻它，而是**收窄它**：PR 车道继续不跑真实 CLI，夜间/手动车道允许跑。
- **矛盾2**：目标A 若走 hook 路线，会与"四 harness 平权"发生张力。Claude Code 有 PreToolUse（exit 2 硬阻断，连 bypassPermissions 都绕不过），Cursor 1.7+ 可直接复用 Claude Code hooks；但 **Codex 无 hooks，只有 sandbox/approval_policy；pi 无公开文档**。所以"同一门禁跨四端"做不到，必须接受**分级保护**（Claude/Cursor 硬拦截，Codex/pi 退化为软约束 + 事后 CI 检查）。这是本次最需要你拍板的取舍。
- **重叠**：researcher 推荐"搬 Anthropic skill-creator 的 eval 框架"，实际上**它已经在你仓库里**（`cadence-init/skills/skill-creator/scripts/run_eval.py` + `eval_set.skill-creator.20.json`）。这不是新引入，是扩展已有资产。scout 漏报了这一点（它把 skill-creator 只当分发对象，没检查里面有 eval 能力）。
- **缺口**：`run_eval.py` 只解决"skill 是否被触发"，无法回答你的三类违规。它硬编码 `claude -p`，无 codex/pi provider；也无轨迹断言（不知道 agent 实际调了哪些工具）。

---

## 目标A：干预方案（按性价比排序）

### 方案1｜规则加载自检（短期速赢，先做这个）

- **机制类型**：流程结构改造（诊断层，非拦截）
- **遵循率影响**：中—高。理由：若部分违规其实源于规则未加载/版本漂移，这一步直接消除误判，且立刻把"玄学问题"变成可测量数字。不做这步，后面所有干预都测不准归因。
- **工作量**：4–8 人时。扩展 `rule-config.py` 增加 `--verify` 子命令：检查业务项目 L0 区块版本是否为 v3、7 个受管规则文件哈希是否与模板一致、四层软链是否解析到 Cadence 源，输出结构化报告 + 非零退出码。
- **风险**：低。纯只读检查，复用已有 dry-run 基础设施。唯一风险是发现漂移量比预期大，需要额外修复工作。

### 方案2｜Claude Code PreToolUse 门禁（短期速赢，最高确定性）

- **机制类型**：hook 硬拦截
- **遵循率影响**：高。理由：exit 2 是官方唯一确定性阻断，模型无法"决定"绕过；覆盖三类违规中时序判定最清晰的①。
- **工作量**：12–20 人时。新增受管产物 `.claude/settings.json` 的 hooks 段 + 一个自包含判定脚本：`Edit|Write` 命中实现文件时，检查 `openspec/changes/*/` 与 `cadence/plans/` 是否存在对应在办契约，缺失则 exit 2 并回吐提示。②③ 用 deny 规则（非 codegraph/ast-grep 的检索工具在 coding 项目里降级为 ask）。
- **风险**：中。① 误伤合法场景（改 README、纯问答、紧急 hotfix）→ 必须内置逃逸阀（如 `CADENCE_BYPASS=1` + 记录）。② 与"框架权威全覆盖"策略冲突：settings.json 常含用户自定义内容，不能整文件覆盖，必须做区块级受管（类似 L0 的 `cadence-managed:` 标记）。③ 只保护 Claude Code + Cursor，Codex/pi 无效。

### 方案3｜MCP / 工具权限层强制（短期速赢，投入最小）

- **机制类型**：hook 硬拦截（权限配置，非脚本）
- **遵循率影响**：中—高，但只针对②③。理由：`mcp__server__tool` 全名可做 allow/deny/ask，把非合规检索路径 deny 掉后，模型只剩合规路径可走 —— 不依赖它"想起"规则。
- **工作量**：4–6 人时（纯配置模板 + rule-config 下发）。是三个速赢里最便宜的。
- **风险**：中。deny 过严会让 agent 卡死（该用 grep 的场景也被堵）；建议起步用 `ask` 而非 `deny`，观察一到两周再收紧。同样只覆盖 Claude/Cursor。

### 方案4｜UserPromptSubmit 每轮重申 + Stop 自检（中期）

- **机制类型**：提示词软约束，但由系统注入而非依赖模型记忆
- **遵循率影响**：中。理由：直接对治长上下文遗忘（AgentIF/IFScale 证据：指令密度↑遵循率↓，且 agentic 长指令下约束遗漏严重）。把"要求模型记得回执"变成"系统每轮替它重申当前阶段"。Stop hook 可阻止在无验证证据时结束。
- **工作量**：8–12 人时。
- **风险**：中。每轮注入吃 token，与 L0 瘦身决策方向相反 —— 必须极短（建议 ≤200 字符，只注入"当前阶段 + 下一步唯一允许动作"）。若写长，会重演 v3 之前的失败。

### 方案5｜Codex/pi 的等价硬约束（长期改造）

- **机制类型**：流程结构改造
- **遵循率影响**：低—中。理由：Codex 只有 sandbox/approval_policy，粒度是文件/网络边界，无法表达"必须先有 plan"这类时序语义；pi 无公开文档，需实测。现实做法是退化为"事后检查"：在 CI 或 git pre-commit 阶段校验 commit 是否有对应 spec/plan 引用。
- **工作量**：20–40 人时（含 pi 实测摸底）。
- **风险**：高。事后拦截体验差（工作已完成才被拒），且 git hook 可被 `--no-verify` 绕过。

**排序逻辑**：1 → 3 → 2 是最优起手顺序。先证明规则加载正常（1），再用最便宜的权限层拿下②③（3），再上时序 hook 攻①（2）。4 和 5 等前三个有了数据再决定。

---

## 目标B：测试体系路线

**选型：双层，不引入 promptfoo 作为主框架。**

理由：你已经有 `run_eval.py`（触发率 eval，train/test split 防过拟合、多 run 统计方差）。它的缺口是 provider 单一 + 无轨迹断言，而不是架构不对。引入 promptfoo 意味着两套 eval 并存、eval_set 格式分裂。建议：

- **L1 确定性层（自建，扩展现有）**：把每条规则编译成程序化断言，跑在 fixture 项目上。判定对象是**产物状态**而非模型输出 —— 例如"跑完任务后，若有实现文件变更则必须存在对应 plan 文件"。这层无 LLM 评委，零 flaky，可进 PR 门禁。参考 IFEval 的可验证指令范式。
- **L2 行为层（扩展 `run_eval.py`）**：抽象出 provider 接口（`claude -p` / `codex exec` / pi / kimi 各一个 adapter），并把断言从"是否触发"扩展到"轨迹是否合规"（实际调了哪些工具、顺序如何）。轨迹取证优先用各 harness 的 JSON 流式输出（Claude 已有 `--output-format stream-json`，`run_eval.py` 已在用）。

**矩阵设计（分级，不做全笛卡尔）**：

| 层级 | agent × model | 跑什么 | 频率 |
|---|---|---|---|
| Tier-0 冒烟 | Claude Code × 1 个中档模型 | L1 全量断言 + 5 条触发正负例 | 每次 PR（仅规则/skill 文件变更时） |
| Tier-1 主矩阵 | Claude Code、Codex × 各 2 个模型（1 强 1 弱） | L1 全量 + L2 触发矩阵 | 夜间 cron |
| Tier-2 全量 | 四 harness × 弱模型为主 | L2 全量 + 过程评审 | 手动 / 周度 |

**弱模型必须在矩阵里**：仓库自己的历史结论就是"弱模型遵循率低"，只测强模型会让 L0 瘦身的收益无法验证。

**CI 触发策略**：PR 只跑 Tier-0，且用路径过滤（`cadence-init/skills/**`、`references/rules/**` 变更才触发）。Tier-1 走 `schedule: cron`，多次采样取均值 + 容差阈值判定，不用单次 pass/fail。这是 flaky 治理的关键：eval 是测量不是断言，单次判定的重门禁会在几周内被降级为 non-required。

**成本量级**：Tier-0 每次 PR 约 $0.1–0.3（几十次短调用，可缓存）。Tier-1 夜间约 $2–5/晚 → **每月 $60–150**。Tier-2 手动，单次 $10–20。这是量级估算，不是实测值 —— 实际取决于每个 eval case 的任务长度，建议先跑一晚测真实成本再定阈值。

**必须你拍板的取舍点**：

1. **是否修订"CI 不跑真实客户端"这条决策？** 我建议收窄而非推翻：PR 车道保持不跑，夜间车道允许。不改这条，目标B 只能做到 L1。
2. **接受 harness 保护不平权吗？** Claude/Cursor 能硬拦截，Codex/pi 只能软约束 + 事后检查。这打破"四 harness 平权分发"的隐含假设。要么接受分级，要么把门禁降到四端最低公分母（等于放弃硬拦截）。
3. **API 成本谁付、密钥怎么进 CI？** 夜间跑真实 CLI 需要在 GitHub Actions 存 API key，属安全面变更。若不愿意，Tier-1 只能本地手动跑。
4. **hook 误伤的容忍度**：宁可挡住合法操作（严），还是宁可漏过违规（松）？这决定 ② ③ 起步用 `deny` 还是 `ask`。

---

## 两份证据的矛盾、重叠与缺口

- **scout 漏报**：仓库内 `skill-creator/scripts/run_eval.py` + `run_loop.py` + 两个 eval_set 样例已存在，scout 说"B 目前完全空白"不准确。我已核实：eval 能力存在，但只测触发率、硬绑 `claude -p`、无轨迹断言。这把目标B 的性质从"从零建"改为"扩展"，工作量估计应下调。
- **researcher 重复推荐已有资产**：建议"搬 Anthropic skill-creator eval 框架"—— 它就是你仓库里那份的上游。这不是新增依赖。
- **researcher 明确缺口（我认同，无法从代码消解）**：pi harness 无公开文档，是否有 hooks/权限等价物只能实测；"输出回执提升遵循率"无同行评审实证，属工程共识 —— 你的 L0 v3 依赖这个假设，值得自己 A/B 验证。
- **两份证据一致的地方**（可信度高）：软指令无强制力、可判定门禁优于姿态条款、双车道 CI 控成本。scout 从仓库历史归档得出，researcher 从官方文档与论文得出，两条独立路径同结论。

**建议补充的验证实验（按优先级）**：

1. **规则加载实证**：在一个真实业务项目里，让四个 harness 各自回答"复述你当前生效的 L0 铁律全文" —— 直接验证规则是否进上下文、版本是否 v3。半天可做完，结论决定后续所有投入方向。
2. **归因拆分实验**：同一任务在强模型/弱模型各跑 10 次，记录三类违规频次。若弱模型违规率显著更高 → 是模型能力问题，硬拦截收益大；若两者接近 → 是规则表述或加载问题，先改规则更划算。
3. **L0 v3 的 A/B**：v2（含姿态条款）vs v3（瘦身）在弱模型上的遵循率对比。你的瘦身决策目前是推理得出的，没有测量支撑。有了 L2 eval 就能补上。
4. **pi hooks 摸底**：本机就有 pi 环境，直接查其配置面是否支持工具拦截。决定方案5 的可行性。

## 需要主 agent / 维护者决策的点

上面四个拍板点里，**第 1 和第 2 是阻塞性的** —— 不定"是否允许 CI 跑真实客户端"和"是否接受 harness 保护不平权"，目标A 的方案2/3 和目标B 的 Tier-1 都无法进入实施。其余两点可以边做边定。

## 执行交接建议

暂不建议直接进 worker 实施。理由：方案1–3 都属于"新行为 + 公共契约变化"（新增受管产物 `.claude/settings.json` 区块、新增 `rule-config --verify` 子命令、修订 CI 决策），按仓库铁律必须先 brainstorming → OpenSpec 契约 → 确认后才 writing-plans。当前只有咨询结论，没有契约。

建议下一步：就"规则加载自检 + 权限层强制"这一最小切片进 brainstorming，产出 OpenSpec change 提案，把上述四个拍板点作为提案里的 open questions 交给维护者裁决。实验1（规则加载实证）属只读调查，不受此门禁约束，可以立刻单独做。