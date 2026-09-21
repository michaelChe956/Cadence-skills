# KnowledgeBase 价值报告（同端配对实验）

- **批次**：`B5`
- **对比条件**：同一 agent `kimi`、同一 model `default`、同一源码快照、同一任务 prompt
- **代码规模**：fixture `standard`
- **唯一变量**：是否提供知识库环境（KB 产物 + AGENTS.md 导航）
- **说明**：检查项为确定性判据，报告同时附回答原文供人工复核；“提问”两侧完全一致。

## 一、总览

| 场景 | 案例 | 无 KB | 有 KB | 核心差异 | 耗时（无→有）|
|------|------|-------|-------|----------|--------------|
| 调度与配置一… | V1-A 每日对账到底在不在跑 | 4/4 | 4/4 | 质量持平 | 18s → 25s |
| 规则存在但执… | V2-A 导出文件到期谁清理 | 3/3 | 3/3 | 质量持平 | 18s → 20s |
| 跨域检索可行… | V3-A 按手机号跨域查用户记录 | 3/4 | 3/4 | 质量持平 | 37s → 1m14s |

**合计**：无 KB **10/11** 项检查通过 → 有 KB **10/11** 项（提升 **0** 项）

- 总耗时：无 KB **1m12s** → 有 KB **2m0s**（增加 48s（66% ↑））
- 总费用：无 KB **未提供** → 有 KB **未提供**（kimi CLI 未上报 usage，无法比较；如需费用维度可用 claude 端补测）

## 二、逐场景明细

### 场景 V1：调度与配置一致性（词汇不通：问『在不在跑』，代码里无此表述）

#### V1-A 每日对账到底在不在跑

**用户实际问了什么**：

> 运营问：账户的每日对账任务到底有没有在跑？请给出结论与依据，并说明若不生效缺什么。不要修改代码。

**无 KB 实际回答**（耗时 18s，tokens —，费用 未提供）：

> • 我来调查一下账户服务的每日对账任务。先看项目结构和相关代码。
> 
> • 找到关键文件了，读一下对账任务和启动类。
> 
> • 关键证据已现。再确认全项目是否有 `@EnableScheduling`，以及配置项是否被读取。
> 
> • ## 结论
> 
>   **没有在跑。** 账户服务的每日对账任务是不生效的——`@Scheduled` 方法是"死注解"，永远不会被触发。
> 
>   ## 依据
> 
>   **1. 任务定义本身是有的**
>   - `account-service/src/main/java/com/demo/account/job/ReconcileJob.java:14` 有 `@Scheduled(cron = "0 0 2 * * ?")`（即每天 02:00），类上有 `@Component`（同文件 :11）。
> 
>   **2. 但调度功能没有开启（根因）**
>   - 启动类 `AccountApplication.java:7` 只有 `@SpringBootApplication`，**没有 `@EnableScheduling`**。
>   - 全仓库搜索 `EnableScheduling`：**零匹配**。
> …（完整回答：`transcripts/V1-A.log`）

**有 KB 实际回答**（耗时 25s，tokens —，费用 未提供）：

> • 我先读项目知识库导航，同时并行探查账户服务里与对账相关的代码。
> 
> • 知识库里直接有 `JOB-reconcile` 与 `FLOW-account-reconcile` 条目。我读这些，并同时核对 account-service 的实际源码。
> 
> • 知识库条目本身行号引用就不一致（`JOB` 文档说 11-17 行，`FLOW` 文档说 49-59 行）。我直接核对源码与全工程调度配置。
> 
> • `@EnableScheduling` 在全工程 Java 源码里零命中（只在知识库文档里出现）。再确认几件事：有没有其他启用调度的装配方式（`spring.factories` / 自动配置）、配置键有没有任何读取点、以及该文件的历史。
> 
> • ## 结论
> 
>   **没有在跑，而且是"从设计上就不可能跑"**——不是"可能没跑"的待确认状态。即使调度真的被触发，也只会执行一个空方法，不产生任何对账动作。知识库把它登记为"代码存在但不可达"（Q-M1/Q-M2）是准确的；我逐条核对了源码，结论一致。
> 
>   ## 依据
> 
>   三个各自独立、任一成立即导致不生效的缺口：
> 
>   **1. 调度根本没启用（决定"是否被触发"）**
> 
> …（完整回答：`transcripts/V1-A.log`）

| 检查项 | 无 KB | 有 KB |
|--------|-------|-------|
| 指出调度未被启用（缺 @EnableScheduling） | ✅ 通过 | ✅ 通过 |
| 指出 @Scheduled 存在但不会执行 | ✅ 通过 | ✅ 通过 |
| 引用配置键 reconcile.enabled / retry-times | ✅ 通过 | ✅ 通过 |
| 不武断断言任务正常运行 | ✅ 通过 | ✅ 通过 |

**证据密度**：引用不同文件 无 KB 4 个/有 KB 11 个；行号定位 无 KB 6 处/有 KB 8 处
**本案例投入**：耗时 18s → 25s（增加 7s（41% ↑））；费用 未提供 → 未提供（数据不足）

### 场景 V2：规则存在但执行缺失（词汇不通：问『谁清理』，代码里只有保留期常量）

#### V2-A 导出文件到期谁清理

**用户实际问了什么**：

> 运维问：订单导出文件保留 7 天这条规则在哪定义？到期后是谁清理的、现在有没有真的在执行？

**无 KB 实际回答**（耗时 18s，tokens —，费用 未提供）：

> • I'll investigate this across the repo — where the rule lives, what cleans up, and whether it actually runs.
> 
> • The export logic is concentrated in `order-service`. Let me read the relevant files.
> 
> • Now let me find who actually cleans up expired files, and whether any job is wired up and enabled.
> 
> • Let me sweep the rest of the repo for any cleanup implementation, docs, or scheduled tasks I might have missed.
> 
> • ## 结论
> 
>   这条规则**只有"定义"，没有"执行者"**——保留 7 天写在常量、注释和表注释里，但全项目没有任何清理代码，所以现在**并没有真的在执行**。
> 
>   ## 规则在哪定义
> 
>   三处，全是"声明性"的，彼此只是文字重复：
> 
>   - `order-service/src/main/java/com/demo/order/service/ExportService.java:10` — `public static final int RETENTION_DAYS = 7;`，这是唯一的代码级定义。
>   - `order-service/src/main/java/com/demo/order/controller/ExportController.java:5` — 类注释"文件保留 7 天（ExportService.RETENTION_DAYS）"。
> …（完整回答：`transcripts/V2-A.log`）

**有 KB 实际回答**（耗时 20s，tokens —，费用 未提供）：

> • I'll start with the knowledge base navigation, then trace the rule and its implementation.
> 
> • Found `RULE-order-export-retention.md`. Let me read it along with the related file/interface docs.
> 
> • Knowledge base claims this rule is declaration-only. I need to verify against the actual source — the KB may be stale.
> 
> • The grep is comprehensive. Let me read the actual source files to confirm the current state directly.
> 
> • Confirmed: the constant and DDL comment exist, no cleanup code. Let me verify the git history and check nothing elsewhere (scripts, schedulers) performs the cleanup.
> 
> • 已核实源码与知识库。结论：**这条规则只有"声明"，没有任何清理实现，目前不会执行。**
> 
>   ## 规则定义在哪
> 
>   只有两处声明，都是"写法"而非"实现"：
> 
>   | 位置 | 内容 | 性质 |
>   |------|------|------|
> …（完整回答：`transcripts/V2-A.log`）

| 检查项 | 无 KB | 有 KB |
|--------|-------|-------|
| 定位保留期来源 | ✅ 通过 | ✅ 通过 |
| 指出不存在清理实现（需断言缺失） | ✅ 通过 | ✅ 通过 |
| 指出导出端点为存根 | ✅ 通过 | ✅ 通过 |

**证据密度**：引用不同文件 无 KB 4 个/有 KB 8 个；行号定位 无 KB 4 处/有 KB 4 处
**本案例投入**：耗时 18s → 20s（增加 3s（16% ↑））；费用 未提供 → 未提供（数据不足）

### 场景 V3：跨域检索可行性（词汇不通：问『所有系统』，代码里只有 userId 关联）

#### V3-A 按手机号跨域查用户记录

**用户实际问了什么**：

> 客服拿到一个手机号，想一次看到这个用户在我们所有系统里的记录（用户信息、账户、订单）。做得到吗？需要什么？有哪些还没有证据的地方？

**无 KB 实际回答**（耗时 37s，tokens —，费用 未提供）：

> • <thinking>Now order-service.</thinking>
> 
> • <thinking>Now remaining: ExportController, ExportService, ReconcileJob, OrderEventListener, OrderEventProducer, test, App.vue, main.js, pom files. Let me read the rest.
> 
>   Note vite proxy targets localhost:8080 — a gateway that's not in the repo. That's evidence of a gateway existing (or expected), but no gateway code here. Important for "what's needed / missing evidence".
> 
>   Let's read the remaining files.</thinking>
> 
> • <thinking>Now let me check git history for relevant context — maybe there's a task/spec, or other branches. Also check for AGENTS.md files (none per prompt), .git for recent commits, and any docs.
> 
>   Let me check git log and any other files (hidden).
> 
>   Key note: `vite.config.js` proxies to `http://localhost:8080` — a "网关" (gateway) that isn't present in the repo. Request.js comment says baseURL goes through vite proxy to backend gateway. So a gateway is referenced but no code. Ports: user 8081, account 8082, order 8083, gateway 8080. But when the portal calls `/user/basic/1`, `/account/1`, `/order/...`, the gateway would need to route. This is evidence of an expected gateway component not in the repo — a "no evidence" area.
> 
>   Let me check git log to see if there's more context.</thinking>
> 
> • ## 结论
> 
> …（完整回答：`transcripts/V3-A.log`）

**有 KB 实际回答**（耗时 1m14s，tokens —，费用 未提供）：

> • I'll start with the project's knowledge base, then dig into the three services.
> 
> • The KB has a capability doc named `CAP-user-full-info` — that's likely exactly this scenario. Let me read it plus the interface docs.
> 
> • The capability that matches this scenario already exists as a design doc. Now I need the gaps: phone → userId mapping, and orders. Let me read the relevant docs and verify against source in parallel.
> 
> • Now let me verify claims against actual source and read the user's original requirement + open questions.
> 
> • ## 结论
> 
>   **做不到。** 现有系统里没有任何一条链路能把手机号变成数据。
> 
>   要从手机号看到全景，得走两步：`手机号 → userId` 和 `userId → 用户信息/账户/订单`。第一步完全没有；第二步只走通了一半（用户、账户能查，订单不能）。
> 
>   ## 现状证据
> 
>   三个后端一共只有 4 个 HTTP 端点，全部按**数值 ID** 查，没有一个接受手机号：
> 
> …（完整回答：`transcripts/V3-A.log`）

| 检查项 | 无 KB | 有 KB |
|--------|-------|-------|
| 指出手机号只在用户库 | ✅ 通过 | ✅ 通过 |
| 关联必须经 userId | ✅ 通过 | ✅ 通过 |
| 无现成跨域聚合能力 | ❌ 未达 | ❌ 未达 |
| 账户唯一性/基数未证实 | ✅ 通过 | ✅ 通过 |

**证据密度**：引用不同文件 无 KB 19 个/有 KB 12 个；行号定位 无 KB 21 处/有 KB 12 处
**本案例投入**：耗时 37s → 1m14s（增加 38s（102% ↑））；费用 未提供 → 未提供（数据不足）

## 三、结论

- 运行案例：3 个（5 场景）
- 机械判据质量：有 KB 提升 **0** 个；持平 **3** 个；退化 **0** 个（通过率 无 KB 10/11 → 有 KB 10/11）
- 证据密度：引用不同文件 无 KB 27 → 有 KB 31；行号定位 无 KB 31 → 有 KB 24

**解读**（本轮实测，非通用结论）：

1. **质量持平的成因**：本 fixture 仅 5 个服务/4 张表，裸代码 1-2 分钟即可 grep 完，无 KB 端已把检查项全部答对——机械判据达到上限，区分不出两臂。
2. **可观测的真实差异是证据纪律**：有 KB 回答平均引用文件数为无 KB 的 1.1 倍、行号定位 0.8 倍，且每条结论带四类证据交叉核验（知识库/当前代码/数据模型/配置）与开放问题编号（如 Q-M9 关联待确认），可直接追溯。
3. **代价**：有 KB 单任务耗时约为无 KB 的 2.3 倍（读 KB 有固定开销）；KB 首次构建另计（历史实测约 60 分钟）。
4. **适用边界**：KB 价值主张在于大代码库/跨模块/新人接手/规则沉淀场景；本 fixture 规模不足以体现「找不到」与「漏掉」的差距，属实验下限。

## 四、边界与说明

- 判据为确定性关键词/实体核验（可审计），开放性问题标注“待复核”；
- 费用来自 CLI 上报的实际 usage，缺失显示“未提供”，不折算为 0；
- 单轮配对实验，不声称统计显著；KB 首次构建成本（约 60min）未计入单任务耗时；
- 完整回答原文见 `results/exp/<批次>/<agent>-<arm>/transcripts/`。

## 附：代码规模对比（同 agent、同案例、同判据）

| 批次 | fixture (文件数) | 无 KB 通过 | 有 KB 通过 | 无 KB 耗时 | 有 KB 耗时 | 耗时倍数 | 证据文件数 |
|------|------------------|-----------|-----------|-----------|-----------|---------|-----------|
| `B1` | standard (—) | 25/25 | 25/25 | 10.6m | 24.3m | 2.30× | 54 → 114 (2.1×) |
| `B2` | large (172) | 25/25 | 25/25 | 11.4m | 22.0m | 1.93× | 57 → 79 (1.4×) |
| `B4` | large (—) | 24/25 | 25/25 | 5.2m | 6.9m | 1.34× | 123 → 119 (1.0×) |
| `B5` | standard (—) | 10/11 | 10/11 | 1.2m | 2.0m | 1.66× | 27 → 31 (1.1×) |

**已有批次出现质量提升**：`B4` 无 KB 24/25 → 有 KB 25/25；其余 3 批持平（`B1`、`B2`、`B5`）。
