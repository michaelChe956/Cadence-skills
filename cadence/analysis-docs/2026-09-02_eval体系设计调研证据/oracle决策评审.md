# rule-eval-p0 决策评审：业内一致性、更优方案与拍板点

## 继承决策基线（不推翻的部分）

E1 不测触发识别 / E2 夜间 self-hosted 复用本机登录态 / E3 确定性判分为主 judge 仅 Tier-2 / E4 PR 车道零真实 CLI / E5 弱模型必入矩阵 / E6 业内 10 条全量并入；R9 纯新增子系统不动 install.sh 与 rule-config。本次评审不动这七条中的任何一条，全部建议都在其框架内。

取证方法说明：结论建立在本机四端真实 session 数据（claude 362 个 jsonl / codex 1143 个 rollout / pi 4857 个 session / kimi 313MB wire.jsonl）与仓库现状之上，非文档推演。

---

## 1. 业内一致性判定

### 一致（业内标准，我们已吸收）

§6 的 10 条增补**全部**是业内已验证做法的移植，没有一条是发明。逐条溯源清晰：确定性文件系统断言（claudemd-check / skillgrade 双 grader / cae 的 git-diff + test_cmd 重跑）、幂等双跑（jarvy `default_hook_idempotency.rs`）、假绿 gate（Backgrind 一手实测）、fake MCP（agenteval）、mock 冒烟前置（cae mock adapter / skillgrade `--smoke`）、基线具名 diff（claudemd-check）、断点续跑 + 成本熔断 + 版本双 pin（cae / Backgrind）、adapter 抽象（Harbor adapters / cae `AgentAdapter` 协议）、env 注入 prompt、排除规则原文防假阳（claudemd-check）。

判定：**业内一致性很高**，这部分不需要再论证。

### 增量（业内无先例，我们独有）

- slash command 执行后的产物断言（调研 Gap 1 已确认无公开实现）
- 多端规则遵循矩阵（Gap 4：claudemd-check / rulebench / agents-md-evals 均单端 Claude Code）
- 两阶段耦合：把"装得对"与"用得对"串成一条因果链，业内两类 harness 各做一半
- 弱模型保证度作为一等度量（业内多数只测强模型或 SWE-bench 分数）
- 与强制面（p1 deny 投影）版本对比的 A/B 标尺

### 缺口（业内已有，我们没吸收）

| # | 缺口 | 来源 | 严重度 |
|---|---|---|---|
| 1 | **无"未安装 Cadence"对照组**。只有 pre-p1 → post-p1 纵向对比，能回答"p1 有没有让数字变好"，回答不了"规则到底有没有用" | rulebench 的 trap 测试、agents-md-evals 的规则 vs 无规则 A/B | **高**，且补齐成本最低 |
| 2 | **跨端对比未固定模型**。任务集与判分固定了（符合 HarnessBench 要求），但四端默认模型不同，实测 naruto 单项目就出现 glm-5.3(2541)/glm-5.2(774)/deepseek-v4-flash(76)/glm-5.3-flash(2) 四种 model 值 | Scaffold Effect 论文 / HarnessBench：harness 效应与模型效应必须分离 | **高**，直接影响第④问可归因性 |
| 3 | 不测规则的**边际价值**（哪条规则只耗 context 不改行为）。7 个规则文件 + p1 内联投影已占上下文，无机制识别可删条款 | agents-md-evals | 中 |
| 4 | 事后审计既有 transcript 作为零成本数据源 | agent-rules | 中（见 §2-d，实测已产出可用结论） |
| 5 | transcript **保留策略**。规格只说"全量留存"。实测本机已累积 codex 1.2GB / pi 1.6GB / kimi 313MB / claude 52MB | 官方 SessionStore 归档 + cae 的跳过复用语义 | 中 |

R3（judge 仅 Tier-2）不算缺口，是有意取舍；但要承认确定性断言测不了产物**质量**——mcp-configuration 是 668 行纯 prose、零脚本，其输出质量只有部分可确定性断言。

---

## 2. 更优方案排查

### a) Harbor 式 Docker 每任务容器 → **不换**

Harbor 的容器是为"数千并行 + 执行不可信任务代码 + 可复现 OS 基线"设计的。我们被测对象是文档与配置写入，无编译、无长依赖链，OS 基线不是变量。

决定性阻碍是 E2：四端登录态在 `~/.claude`、`~/.codex/auth.json`、`~/.pi/agent/auth.json`、`~/.kimi-code/credentials`。上容器必须把凭证挂进容器（扩大密钥暴露面，与"密钥不出本机"相冲）或容器内重新登录（订阅制 CLI 基本不可行）。**换容器等于重开 E2。**

仓库已有可复用先例：`tests/test-install.sh`（367 行）已用 `mktemp -d` + `snapshot_home`，CI 已在跑 `HOME="$test_home" bash tests/test-install.sh`。

不换必须自付的两笔账（容器方案本来免费送）：

1. 临时目录不隔离**全局态**。四端会读 `~/.claude/settings.json`、`~/.codex/config.toml`、`~/.pi/agent/settings.json`、全局 `AGENTS.md`。L0 探针实验的发现 4 已证明 Codex 复述被跨源污染（多出的"不引导 knowledge-base-bootstrap"来源不明）。阶段二必须显式快照全局态并在与基线不一致时报告标注，否则维护者本机的配置漂移会静默改变矩阵。
2. 现有 `run_eval.py` 把合成 command 写进项目 `.claude/commands/`——新 harness 不得沿用这种污染式写入。

### b) per-探针基线 → **换成 per-(规则条款 × 探针) 双键**

探针是测量工具，不是可修对象。`▼ P1检索@Codex: 100%→60%` 红灯后，维护者不知道该改哪个规则文件、哪条元数据——P1 同时压 code-reading 与 mcp-servers 两条，P5 同时压 document-storage 与 markdown-format。

更关键的对齐理由：p1 的规则元数据（`preferred`/`fallback`/`when`）**已经**是 per-条款的结构化对象，deny 区块也按条款生成。基线以条款为键才能与之同源，直接回答"改了 code-reading 的 preferred 之后该条款遵循率变了多少"。

代价：tasks 3.1 的"各自断言规则绑定"要升级为显式条款 ID 而非隐式；报告出两张 diff（条款维度 + 探针维度），约 +0.5 人日；条款需稳定 ID，重命名要走基线键迁移。不换的代价更大：矩阵能报警但不能定位，每次红灯都要人肉回读 transcript。

### c) VCR/回放（AgentHound/agentreplay）→ **不加**

回放的收益是零 API 成本的确定性回归，但我们成本本来就≈0（吃订阅），收益分母很小。

回放的真实价值场景是**断言器自身的回归**（改了断言逻辑，历史 run 判定会不会变）。这个不需要 VCR 层：transcript 全量留存（E6-3 已有）+ 断言器只消费统一中间格式（spec 已锁）= 拿历史 transcript 离线重跑断言器，拿到 VCR 90% 的收益，零额外架构。

反对加层的硬理由来自实测：四端格式差异极大且**同端跨版本会变**。Codex 一个会话工具名是 `function_call:exec_command`（1001 次），另一个会话是 `custom_tool_call:exec`（36 次）；Kimi wire 协议自带 `protocol_version: 1.4`；pi 允许会话中途 `model_change`。VCR 要 bit-exact 回放模型 API + 工具 + 时钟，等于为四个各自演进的私有格式维护四套录制回放桩，维护成本随 CLI 升级线性增长——而 CLI 升级是本项目的常态输入。这层会成为最脆的一环。

要补的一条：把"断言器对任意历史 transcript 目录离线重跑并输出判定对比"做成 Tier-0 的一个 job。用留存的**真实** transcript 作 golden 输入，比 mock 冒烟更强。

### d) agent-rules 式事后审计 → **加，定位为第五张观测表，不进 gate**

这条我实测了，数据支持力度最强。

存量真实且免费：claude 362 个 session jsonl（17 个项目目录，naruto 单项目 242 个）、codex 1143 个 rollout、pi 4857 个 session、kimi 313MB。这是**真实生产分布**——长上下文、真实任务复杂度、人工中断、真实弱模型混用，探针给不出这些。

实测已经产出一个能改设计的结论。naruto 242 个 claude 会话工具分布：Read 382 / Bash 346 / Skill 314 / `mcp__codegraph__codegraph_explore` 82 / AskUserQuestion 73 / Edit 25 / Write 21 / `mcp__sequential-thinking` 4。Bash 命令头分布：`ls` 114、`find` 20、`grep` **仅 4**。

也就是说 codegraph 确实在被用（82 次），而"检索优先级"的真实违规形态是 `ls`/`find` 漫游（合计 134 次），不是裸 `grep`（4 次）。**P1 探针"无大范围裸 grep"的断言靶子选错了。** 这个纠正在探针设计阶段拿不到，只有审计既有 transcript 才拿得到。

互补性也被实测证明：242 个会话里只有 **9 个**真正产生 Edit/Write，所以"时序合规"（P3）类违规在真实数据里样本极稀疏，靠探针制造样本是必要的。审计与探针互补而非替代。

审计表天然带模型标签（实测同目录 4 种 model 值），能低成本给出"弱模型保证度"的真实分布参照。

不进 gate 的理由：样本非受控（任务不同、上下文不同、人工干预），不可比不可复现，做门禁必然 flaky；且是业务项目私有数据，不能进公共报告基线。

代价：需要"本地 session 文件 → 统一中间格式"的四端离线解析，但这与 Tier-1 适配器**同一套代码**，只换输入源，边际约 +0.5 人日。输出落 `cadence/reports/eval/audit/` 且不入 git（含业务项目路径与任务内容）。附带收益：这套解析正是 c) 里离线重跑的 golden 输入源，一份代码两处用。

### e) 结果 JSON schema 版本化 → **现在就定，只定最小契约**

基线是要长期跨版本比对的资产（R7 具名 diff 依赖它）。基线一旦提交，schema 变更就成了数据迁移问题；事后补版本号需要回填或废弃历史基线，而历史基线正是"p1 提升百分比"的唯一凭据——废掉它等于废掉本体系的核心交付。

实测支持：四端格式本身在漂（Codex 工具名跨会话不同、Kimi 自带 protocol_version），适配器输出的中间格式必然跟着改，结果 JSON 的 `tool_calls` 形状随之变。没有版本号，去年的基线与今年的结果无法判断是否可比。

范围控制在三件事：

1. 顶层 `schema_version`（如 `"1.0"`）
2. 稳定键：`run_id` / `agent` / `model`（**从 transcript 实测回读**，不是启动参数）/ `cli_version` / `probe_id` / `rule_clause_ids` / `verdict` / `fail_reason` / `denials` / `transcript_path` / `started_at` / `duration_s`
3. 一条读取规则：主版本不匹配的基线不参与 diff，报告显式标"基线 schema 不兼容，本次不比对"，而不是静默错比

其余字段放 `details` 子对象自由演进，不受版本约束。代价约 0.2 人日 + 一条兼容性测试。仓库已有先例可沿用：`cadence/knowledge-base/manifest.yaml` 的 `schema_version: "4.0"` 门禁（AGENTS.md 明写仅当为 4.0 才可选择）。

---

## 3. 结构性风险 top3

### 风险 1：假绿 gate 与 p1 deny 机制正面冲突（设计层硬矛盾，最高优先）

`eval-trajectory-scoring` spec：断言器 MUST gate `permission_denials`，任一非空即判该 run 失败。

`permission-gate-projection` spec 场景"模型撞墙后自动改道"：模型尝试被 deny 的 Grep → 被拦 → 从上下文查优先级链 → 改用 codegraph → 任务继续。

**这正是 p1 定义的成功路径，却会被 eval 判 FAIL。**

根因：Backgrind 的假绿教训针对"未配置 allowlist 导致 agent 什么都没干成"的 denial；p1 把 denial 变成了**预期的控制流信号**。两者语义不同，共用一个 gate 必然误判。

后果：p1 越有效（拦得越多、改道越多），eval 的遵循率越低。四张矩阵会给出与事实相反的结论，"p1 提升百分比"变成"p1 下降百分比"——这是会直接误导拍板的错误。

对策：gate 分两类。

- **预期 deny**（拦截规则属于 `cadence-managed:permission-gate` 区块内条目）：不判 FAIL，转入"改道率"子度量。拦截后 N 步内改用 preferred 工具 = PASS 且计入 deny 有效性；改道失败或放弃 = FAIL。
- **意外 deny**（拦截规则在受管区块外，如 Edit/Write 未放行）：FAIL 且标记为 harness 配置错误，与 agent 遵循率**分离统计**。

实现要求：断言器需读 fixture 的 `.claude/settings.json` 受管区块以判定 deny 归属，因此该快照必须进结果 JSON。

附加实测警示：本机 **242 个真实 claude 会话中 `permission_denial` 出现 0 次**。这个字段的真实结构没有任何本地样本可对照，现有断言是照博客描述写的。落地前必须先在 fixture 里人为造一次真实 denial 取证字段结构。否则 gate 可能对着不存在的字段名判定、永远为空，退化成"没 gate"——而这恰是 Backgrind 教训要防的东西。

### 风险 2：跨端一致性矩阵测的是"端 × 模型"混合效应，不可归因

实测证据：naruto 单项目的 claude 会话出现 glm-5.3 / glm-5.2 / deepseek-v4-flash / glm-5.3-flash 四种 model 值；pi 支持会话内 `model_change`（一个会话观察到 2 次）；L0 探针实验中 claude CLI 实跑 `glm-5.3-flash` 并 stderr 报 `unrecognized_model`。

四端默认模型与可用模型集不同。若"强模型/弱模型"在四端不是同一个模型，跨端极差与方差就是 harness 效应 + 模型效应 + 路由效应之和，无法回答第④问。E6-10 的 pin 是防漂移，**不等于跨端同模型**。

对策：

1. 定义跨端**锚点模型**（四端都能显式指定的至少一个），跨端一致性矩阵只用锚点行；其余模型行只进各端纵向趋势。
2. `model` 从 transcript 实测回读（claude 在 `message.model`、pi 在 `model_change.modelId`、codex 在 `turn_context`/`session_meta`、kimi 在 `config.update`/`usage.record`），与启动参数不一致时标 `MODEL_DRIFT` 且该 run 出矩阵。**只 pin 不核验挡不住实测已发生的漂移。**
3. pi 会话内若发生 `model_change`，该 run 直接作废。

### 风险 3：Tier-1 量级与单机夜间窗口不匹配，且提速路径被 E2 锁死

实测时长（242 个真实 claude 会话）：**median 2.5 min、p25 1.4、p75 3.7、p90 5.7 min**，241/242 在 30 min 内。其中仅 9 个会话真正做了 Edit/Write，即多数样本是短问答——做真实工作的探针会落在分布上端。

矩阵量级：阶段二 8 探针 × 4 端 × 2 模型 × 3 runs = 192 会话，加阶段一 16 次安装（每次串跑四 command，rule-config 是 4342 行脚本 + agent 编排，单次显著长于探针）。按 3 min/会话 ≈ **10.4h**，按 p90 5.7 min ≈ **19.8h**。**串行跑不完一夜。**

提速的自然手段是并行，但四端凭证与状态都在单一 `$HOME`，E2 又锁定复用本机登录态。多进程共享同一 HOME 会争抢状态——实测 codex 有 `state_5.sqlite` + `-wal` + `thread-writer-locks/`，pi/kimi 各有 sqlite 与 session 树。要隔离 HOME 就丢登录态。**这是 E2 的隐含代价，设计文档没有算。**

第二笔没算的账：transcript 体量。实测 codex 1.2GB/1143 会话（≈1MB/会话）、pi 1.6GB/4857 会话、kimi 313MB、claude 52MB/362 会话。夜间 208 会话按 0.5–1MB 估 ≈100–200MB/夜，无保留策略数月即数十 GB，且落在维护者本机。

对策：

1. **首轮砍到窗口内能跑完**：3 runs → 2 runs；先只跑锚点模型；8 探针分夜轮转（奇数夜 P1/P3/P5/P7，偶数夜 P2/P4/P6/P8）。`eval-ci-matrix` 中"每夜运行 MUST 产出四张矩阵"需放宽为"滚动 7 夜窗口 MUST 产出"，否则 spec 与物理时间冲突。
2. 每端单会话实测时长进 dashboard，用真实数据而非估算定规模。
3. 并行只在**四端之间**做（4 路），同端内串行；先验证同端并行是否引发状态冲突，不确定就纯串行 + 砍量级。
4. 保留策略：失败 run 全量留存；通过的 run 只留中间格式 + 摘要，原始 jsonl 保留 N 夜后清理。

---

## 4. 维护者拍板点（4 个）

### 拍板点 1：假绿 gate 如何处理 p1 受管 deny

**推荐**：分两类——受管区块内 deny 不判 FAIL 转入"改道率"子度量，区块外 deny 判 FAIL 并归类 harness 配置错误。启用 gate 前先在 fixture 造一次真实 denial 取证字段结构。

**代价**：断言器需读 fixture 的 settings.json 受管区块，与 p1 产物形成耦合（p1 改区块标记名，eval 要跟着改）；多一个子度量的实现与报告列，约 +0.5 人日。

**不做的代价**：四张矩阵会把 p1 的成功读成失败。这个点必须先定，它决定 tasks 2.4 的实现语义。

### 拍板点 2：跨端一致性的模型锚点

**推荐**：选定一个四端都能显式指定的锚点模型，跨端矩阵只用锚点行；`model` 从 transcript 实测回读并与启动参数核验，不一致标 `MODEL_DRIFT` 且出矩阵。

**代价**：若四端找不到共同可指定模型，第④问（跨端差异）的度量要降级为"各端纵向趋势 + 定性对比"，只能得到弱答案。**这是需要维护者确认能否接受的取舍。**

### 拍板点 3：Tier-1 首轮规模与"每夜四矩阵"规格放宽

**推荐**：砍到锚点模型 + 2 runs + 探针分夜轮转；四矩阵改滚动 7 夜聚合；并行只在四端之间（4 路）。首夜实测时长回填最终规模。

**代价**：单夜信噪比下降（2 runs 的 flaky 容忍度低于 3 runs）；基线建立周期从 1 夜拉长到约 1 周；"某夜某探针无数据"成为常态，报告要能表达缺测而不是判红。

**依据**：median 2.5 / p90 5.7 min × 208 会话 = 10–20h 串行，超出夜间窗口；E2 锁死了靠隔离 HOME 并行提速的路。

### 拍板点 4：是否纳入"未安装 Cadence"对照组 + 事后审计表

**推荐**：都纳入。fixture 加第四变体"未安装 Cadence"跑同一批探针（进 Tier-1）；审计表复用同一套四端解析器读本机既有 session（进 Tier-2，不进 gate、不入 git）。

**理由**：现有设计只有纵向对比，回答不了"规则到底有没有用"这个更根本的问题；rulebench / agents-md-evals 都以有规则 vs 无规则为基本对照。对照组成本极低（fixture 少写东西比多写便宜），却是唯一能证明整个 Cadence 分发链路有效的实验。

**代价**：对照组把阶段二从 192 提到 288 会话，**与拍板点 3 的砍量级直接打架**——两个点要一起定。建议对照组只跑锚点模型 + 只跑规则相关的 4 个探针，增量 ≈16–32 会话。审计表输出含业务项目路径与任务内容，必须留本机不入 git。

**依据**：审计实测已产出能改设计的结论（naruto 裸 `grep` 仅 4 次 vs `ls` 114 + `find` 20 次，P1 探针靶子选错）。

---

## 顺手发现（非评审项，但影响阶段一断言）

`rule-config/SKILL.md` 正文写"升级到当前 **v2**（受支持旧版 v0、v1）"，而 `references/rules/l0-history/` 已有 v1/v2/v3，p1 WP3 要升 v4，`eval-pipeline` spec 断言的是"L0 v4 区块"。SKILL.md 正文与实际版本已有漂移。阶段一断言表以 v4 为准之前，这处 prose 需要同步，否则安装断言的期望值来源不唯一。

另：`test_rule_config.py` 有 4009 行、已含大量幂等单测（`test_rerun_is_idempotent`、`authoritative-idempotent`、`ut-norm-idempotent`、`ut-gitignore-idempotent-exact` 等），但 `.github/workflows/ci.yml` **当前未接入 pytest**（p1 tasks 6.1 才接）。E6-2 的流水线级幂等双跑与这些单测有覆盖重叠——重叠不是坏事（一个测脚本纯函数、一个测端到端 workspace），但估算里 0.5d 可以按"复用现有单测断言语义"压缩。

---

## 执行交接

**不建议现在做 worker 实施交接。** 本轮产出的是四个待拍板的契约级问题，其中拍板点 1（假绿 gate 与 p1 deny 的冲突）是 spec 之间的硬矛盾，拍板点 3 与 4 相互耦合。维护者定完这四点后，需要的是对 `openspec/changes/rule-eval-p0/` 契约四件套的定向修订（`eval-trajectory-scoring` 的 gate 需求、`eval-ci-matrix` 的"每夜四矩阵"与模型锚点、`eval-pipeline` 的第四 fixture 变体、tasks 的条款 ID 绑定与 schema 版本化），而不是进入实现。

需要维护者回答的是上述四个拍板点；在拍板点 1 有结论前，tasks 2.4 无法给出正确的实现语义。