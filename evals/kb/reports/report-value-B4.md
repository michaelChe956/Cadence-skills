# KnowledgeBase 价值报告（同端配对实验）

- **批次**：`B4`
- **对比条件**：同一 agent `kimi`、同一 model `default`、同一源码快照、同一任务 prompt
- **代码规模**：fixture `large`
- **唯一变量**：是否提供知识库环境（KB 产物 + AGENTS.md 导航）
- **说明**：检查项为确定性判据，报告同时附回答原文供人工复核；“提问”两侧完全一致。

## 一、总览

| 场景 | 案例 | 无 KB | 有 KB | 核心差异 | 耗时（无→有）|
|------|------|-------|-------|----------|--------------|
| 能力组合发现… | S1-A 基本信息 + 账户信息组合 | 3/4 | 4/4 | 补齐 1 项 | 57s → 1m15s |
| 能力组合发现… | S1-B 用户全景报表方案（跨三域） | 3/3 | 3/3 | 质量持平 | 54s → 1m13s |
| 业务规则引用… | S2-A 已取消订单要求发货 | 4/4 | 4/4 | 质量持平 | 23s → 30s |
| 变更影响分析… | S3-A user_name 长度 64 → 128 影响分析 | 4/4 | 4/4 | 质量持平 | 34s → 46s |
| 故障排查：找… | S4-A 账户余额出现负数 | 4/4 | 4/4 | 质量持平 | 47s → 50s |
| 架构与方案评… | S5-A 评审：发货条件放宽为 PAID 或 CREATED | 3/3 | 3/3 | 质量持平 | 52s → 1m14s |
| 架构与方案评… | S5-B 评审：零业务侵入的全景 API 提案 | 3/3 | 3/3 | 质量持平 | 42s → 1m4s |

**合计**：无 KB **24/25** 项检查通过 → 有 KB **25/25** 项（提升 **1** 项）

- 总耗时：无 KB **5m9s** → 有 KB **6m54s**（增加 1m45s（34% ↑））
- 总费用：无 KB **未提供** → 有 KB **未提供**（kimi CLI 未上报 usage，无法比较；如需费用维度可用 claude 端补测）

## 二、逐场景明细

### 场景 S1：能力组合发现：从分散接口发现可复用的新能力

#### S1-A 基本信息 + 账户信息组合

**用户实际问了什么**：

> 运营希望按用户查看「基本信息 + 账户信息」。请基于当前项目说明：已有能力如何组合、各自真实入口、关联字段、是否已有可直接调用的聚合接口，以及上线前必须确认的限制。不要实现代码；每项结论请给可核查来源。

**无 KB 实际回答**（耗时 57s，tokens —，费用 未提供）：

> • I'll start with a quick reconnaissance of the repo layout, then delegate deeper reads.
> 
> • Small codebase — I'll read the core files directly.
> 
> • <thinking>Key observations: account-service's DB is a different host/database: 10.20.31.14/demo_account vs user-service localhost/demo_user. That's a cross-database limitation. account-service uses `SELECT *` with implicit mapping — field mapping depends on column names; no resultMap. balance/status — need to check DB schema in db/noise/legacy-account-service.sql and db/init.sql.
> 
>   Now, legacy-account-service — a possible hook: legacy has an AccountController too. Maybe the legacy one is the one actually wired to prod data, or has different endpoint. Also check admin-service (only OpLog - no user aggregation). And web-portal api/index.js and AccountPage.vue to see what the frontend calls.
> 
>   Also db/init.sql for schema and t_user / t_user_account definitions.
> 
>   Let me read those.</thinking>
> 
> • <thinking>Now key: is there any aggregation interface? Check admin-service, other services for a composite endpoint. Let me grep for "aggregat", "composite", "/detail", "UserDetail", "api/user" across the repo. Also web-portal/src/api/index.js and AccountPage.vue / UserList.vue to see front-end wiring.
> 
>   Also check account-service README, user-service has no README. And check other services for user-related joins (member-service, order-service).
> 
>   Let me grep.</thinking>
> 
> …（完整回答：`transcripts/S1-A.log`）

**有 KB 实际回答**（耗时 1m15s，tokens —，费用 未提供）：

> • I'll start by reading the KnowledgeBase navigation as the project instructions require.
> 
> • Now let me verify the key claims against the actual source code.
> 
> • The KB baseline commit `1f867b9` doesn't exist in this repo — and there are far more services here than the KB claims to cover. Let me investigate.
> 
> • <thinking>Now this is a big deal. There are many more services. The key question: is there an aggregate endpoint that returns "用户基本信息 + 账户信息"?
> 
>   Candidates:
>   - member-service: MemberController — 会员服务. Might aggregate member + points.
>   - legacy-user-service: UserBasicController (deprecated)
>   - legacy-account-service: AccountController — 积分账户
>   - admin-service: no controller
>   - report-service: 运营日报与导出任务登记
> 
>   Let me look at MemberController and other controllers to see if any aggregates user + account.
> 
>   Let me read the controllers of all services.
> …（完整回答：`transcripts/S1-A.log`）

| 检查项 | 无 KB | 有 KB |
|--------|-------|-------|
| 找对两个真实入口（用户基本信息 / 账户查询） | ✅ 通过 | ✅ 通过 |
| 指出 userId 为关联键 | ✅ 通过 | ✅ 通过 |
| 明确当前没有可直接调用的聚合接口（可组合 ≠ 已实现） | ❌ 未达 | ✅ 通过 |
| 指出账户记录基数/唯一性未证实（限制项） | ✅ 通过 | ✅ 通过 |

**证据密度**：引用不同文件 无 KB 30 个/有 KB 27 个；行号定位 无 KB 40 处/有 KB 28 处
**本案例投入**：耗时 57s → 1m15s（增加 18s（32% ↑））；费用 未提供 → 未提供（数据不足）

#### S1-B 用户全景报表方案（跨三域）

**用户实际问了什么**：

> 需要一份「用户基本信息 + 账户 + 订单」的运营全景报表。请设计最小数据获取方案：哪些现有能力可复用、如何关联、关联基数和缺失数据如何处理、哪些关键问题目前还没有证据。不要把尚未实现的能力当成现成 API。

**无 KB 实际回答**（耗时 54s，tokens —，费用 未提供）：

> • I'll start with a quick recon of the repo structure, then delegate deeper exploration.
> 
> • Small codebase. Let me read the core services directly.
> 
> • <thinking>Now the critical part: the mapper XMLs — do they expose list queries? The order-service mapper interface only has selectById and updateStatus. So no "list orders by user" API. That's a key gap.
> 
>   Let me read the mapper XMLs, application.yml, db/init.sql, report-service, and the legacy services, plus READMEs.
> 
>   Key questions:
>   - user-service: API-A /api/user/basic/{userId} — returns single user.
>   - account-service: API-B /api/account/{userId} — single account by userId.
>   - order-service: only /api/order/{orderId}/ship (POST) and /api/order/export (POST) — NO query-by-user API. OrderMapper only selectById.
>   - report-service: only a mapper/entity, no controller/service? Let me check.
>   - legacy-user-service, legacy-account-service, legacy-trade-service: need to check for older APIs (maybe they hold the join or batch abilities).
>   - admin-service: only OpLog mapper.
> 
>   Let me read all these.</thinking>
>   Now the critical parts: mapper XMLs (do they support list/batch?), report-service, legacy services, and the DB schema.
> …（完整回答：`transcripts/S1-B.log`）

**有 KB 实际回答**（耗时 1m13s，tokens —，费用 未提供）：

> • Now let me verify against actual source code.
> 
> • Now let me check the many other service directories on disk (they're outside the KB's scope) and enumerate every endpoint.
> 
> • Several services exist on disk beyond the KB's scope. Let me check whether any are relevant (especially `report-service`) or are decoys.
> 
> • These out-of-scope services contain placeholder tokens (`{var}`, `{Ent}`, SQL types like `BIGINT member_id`) — they are non-compiling noise. Let me confirm `report-service` (most relevant by name) and the frontend.
> 
> • Let me verify a couple of absence claims before writing up.
> 
> • 已完成核对（知识库 + 三个在范围内的服务源码 + 其余目录）。下面是基于证据的最小数据获取方案。
> 
>   ## 结论先说
> 
>   - **能直接复用的只有 2 个查询**：用户基本信息、账户信息，且都是**按单个 userId 查一条**。
>   - **订单没有任何读取能力**。`order-service` 只有"发货"（写）和"导出"（空存根），没有订单查询接口，内部 Mapper 也只按 `orderId` 单条查，没有"按用户查订单"。
>   - **没有任何"列表/枚举"能力**：无法列出全部用户或全部订单，只能逐个 id 查（前端就是把 id 硬编码成 `1`）。
>   - **没有任何跨服务聚合能力**：三个后端都没有 Feign/RestTemplate/WebClient/RPC，知识库里的组合能力 `CAP-user-full-info` 状态是 `proposed`（仅用户诉求，无实现），不能当 API 用。
> …（完整回答：`transcripts/S1-B.log`）

| 检查项 | 无 KB | 有 KB |
|--------|-------|-------|
| 覆盖三个数据域 | ✅ 通过 | ✅ 通过 |
| 明确订单维组合无现成能力或需新增 | ✅ 通过 | ✅ 通过 |
| 给出关联键 | ✅ 通过 | ✅ 通过 |

**证据密度**：引用不同文件 无 KB 18 个/有 KB 9 个；行号定位 无 KB 20 处/有 KB 15 处
**本案例投入**：耗时 54s → 1m13s（增加 20s（37% ↑））；费用 未提供 → 未提供（数据不足）

### 场景 S2：业务规则引用与遵守：避免为满足需求而破坏业务约束

#### S2-A 已取消订单要求发货

**用户实际问了什么**：

> 运营要求已取消的订单也能直接点击「发货」，理由是货物已经打包。请判断当前系统是否允许，说明涉及的状态前置条件和证据，并给出不绕过现有业务约束的处理建议。不要修改代码。

**无 KB 实际回答**（耗时 23s，tokens —，费用 未提供）：

> • 我先定位订单发货相关的代码与状态机。
> 
> • 核心状态机已找到。再核对数据库约束、前端入口与测试证据。
> 
> • ## 结论：当前系统不允许
> 
>   已取消（`CANCELLED`）的订单无法发货。发货动作在服务层被状态机显式拒绝，前端按钮即使能点，后端也会报错。
> 
>   ## 涉及的状态前置条件
> 
>   订单状态机定义在 `order-service/.../entity/OrderStatus.java:3`：
> 
>   ```
>   CREATED → PAID → SHIPPED → COMPLETED；任意非终态 → CANCELLED
>   ```
> 
>   `OrderService.ship()`（`order-service/.../service/OrderService.java:25-35`）的两道前置校验，顺序如下：
> 
> …（完整回答：`transcripts/S2-A.log`）

**有 KB 实际回答**（耗时 30s，tokens —，费用 未提供）：

> • ## 结论
> 
>   **当前系统不允许已取消（`CANCELLED`）的订单发货**——这是服务层的硬性拒绝，不是前端拦截。但要区分两个层面：
> 
>   - 「点击」：页面按钮**没有任何状态判断或 `disabled` 绑定**，所以取消单照样能点（`web-portal/src/views/OrderPage.vue:4`）。
>   - 「发货成功」：请求发到后端后被状态机拒绝，抛 `IllegalStateException`，不写库。
> 
>   ## 状态前置条件与证据
> 
>   唯一发货入口 `POST /api/order/{orderId}/ship` → `OrderService#ship`，判定如下：
> 
>   | 当前状态 | 结果 | 证据 |
>   |---|---|---|
>   | `CANCELLED` | 抛 `IllegalStateException("已取消订单不可发货")`，不写库 | `order-service/src/main/java/com/demo/order/service/OrderService.java:28-30` |
>   | `CREATED`/`SHIPPED`/`COMPLETED` | 抛 `IllegalStateException("仅已支付订单可发货")` | `OrderService.java:31-33` |
>   | `PAID` | `updateStatus(orderId, SHIPPED)`，返回 `ok` | `OrderService.java:34`、`OrderMapper.xml:7-9` |
> 
>   也就是说，发货的**唯一合法前置条件是 `status == PAID`**；`CANCELLED` 被单列一条分支明确拒绝。
> …（完整回答：`transcripts/S2-A.log`）

| 检查项 | 无 KB | 有 KB |
|--------|-------|-------|
| 明确拒绝：已取消订单不可直接发货 | ✅ 通过 | ✅ 通过 |
| 指出现有发货前置条件为 PAID | ✅ 通过 | ✅ 通过 |
| 给出不绕过约束的处理建议 | ✅ 通过 | ✅ 通过 |
| 不提出绕过约束的直接改状态方案 | ✅ 通过 | ✅ 通过 |

**证据密度**：引用不同文件 无 KB 9 个/有 KB 11 个；行号定位 无 KB 10 处/有 KB 12 处
**本案例投入**：耗时 23s → 30s（增加 7s（31% ↑））；费用 未提供 → 未提供（数据不足）

### 场景 S3：变更影响分析：一次找到跨层影响，降低遗漏

#### S3-A user_name 长度 64 → 128 影响分析

**用户实际问了什么**：

> 计划将用户姓名字段 user_name 的最大长度从 64 调整为 128。请只做变更影响分析：列出数据库、实体/映射、查询接口、前端页面等需要修改或需要核验的具体位置，说明每个位置的依赖关系和验证建议；没有长度限制的地方不要硬说必须修改。

**无 KB 实际回答**（耗时 34s，tokens —，费用 未提供）：

> • I'll analyze the codebase for all `user_name` length-related locations.
> 
> • <thinking>The db/noise/legacy-user-service.sql has nickname VARCHAR(128), not user_name. Let me check that file to be sure whether it has user_name. Grep showed only lines 6-8. Let me read it.
> 
>   Also let me check web-portal/src/api/index.js, request.js, and other views for user_name/name/maxlength. And check README files for API contracts mentioning length. And check other services' code (account-service, order-service, legacy-user-service) for use of userName/user_name.
> 
>   Let me do broad searches for "name" and "maxlength"/"maxLength"/"length".</thinking>
> 
> • <thinking>No length validations anywhere. Let me check other services' code (account-service, order-service, legacy-user-service) for use of userName/user_name. Let me grep across all java/sql/vue/xml files for "name" broadly. But the initial grep for user_name|userName|username already covered whole repo, and found only db/init.sql, web-portal UserList.vue, and yml files (username credentials), UserMapper.xml, UserEntity.java. So there are no other Java references.
> 
>   But wait — the search may have missed things like `name` columns or DTO fields named differently. Let me grep for "姓名" and "name" in java files. Also check README files for API contract that documents user_name length. Let me search README files.
> 
>   Also check web-portal other views for name.
> 
>   Let me search for "姓名" and "name" across repo.</thinking>
> 
> • <thinking>Let me read the legacy-user-service files (entity, mapper xml, service, controller) to see if they reference user_name or nickname. The legacy DB schema is t_legacy_user_profile with nickname VARCHAR(128), mobile_no. So this is a different field (nickname), not user_name. This is likely noise / distractor. Need to mention it's NOT the same field.
> 
> …（完整回答：`transcripts/S3-A.log`）

**有 KB 实际回答**（耗时 46s，tokens —，费用 未提供）：

> • I'll start with the project knowledge base navigation and a broad search for the field.
> 
> • <thinking>Now clear: legacy-user-service is a decoy (different table t_legacy_user_profile, nickname VARCHAR(128), no user_name). It's marked noise. Note its code is also syntactically broken (pseudo-code `private BIGINT id;`, `{var}`, `{Ent}`) — it's intentionally noise/garbage that doesn't compile. Actually the files contain invalid Java (BIGINT type, {var} placeholders). So legacy-user-service won't even compile. That's a signal it's noise. But I shouldn't over-claim; I should note it has no user_name field, so not affected.
> 
>   Now the real chain: db/init.sql t_user.user_name VARCHAR(64) → UserMapper.xml (SELECT user_name AS userName) → UserEntity.userName → UserBasicController → API-user-basic → web-portal UserList.vue.
> 
>   Let me read web-portal files and the KB docs. Also check account-service/order-service for user_name usage (grep found none — order-service uses user_id only).
> 
>   Let me read web-portal: UserList.vue, api/index.js, and other views to see if user name displayed elsewhere (PointsPage, CouponPage, LegacyOrderPage, OrderPage, AccountPage). Grep for userName earlier found only UserList.vue in web-portal. Let me verify with a case-insensitive grep for "name" across web-portal.
> 
>   Also check KB docs for the field: TABLE-t_user.md, API-user-basic_...参数与报文.md, PAGE-user-list.md, CAP-user-full-info.md, FLOW-user-basic-query.md, and open-questions / interfaces README.
> 
>   Also check order-service (export may include user name?). Grep said no user_name in order-service. Let me double check by grepping for "name" in order-service and account-service.
> 
>   Let me do parallel: read web-portal UserList.vue + api/index.js, and grep for name-related in all java/xml.</thinking>
> 
> • 已完成影响分析。范围结论:**真正要改的只有 1  ／ 处 DDL + 2 处知识库文档;代码链路(实体、Mapper、接口、前端)都没有长度约束,属于"核验"而非"必改"。**仓库里另有 11 个服务与 `db/noise/` 下的 SQL 属于历史遗留/干扰模块,不含 `user_name`,不在影响范围内。
> 
> …（完整回答：`transcripts/S3-A.log`）

| 检查项 | 无 KB | 有 KB |
|--------|-------|-------|
| 定位 DDL 中 VARCHAR(64) 定义 | ✅ 通过 | ✅ 通过 |
| 覆盖数据层与代码层影响 | ✅ 通过 | ✅ 通过 |
| 覆盖实体/Mapper 或接口层 | ✅ 通过 | ✅ 通过 |
| 覆盖前端页面层 | ✅ 通过 | ✅ 通过 |

**证据密度**：引用不同文件 无 KB 20 个/有 KB 19 个；行号定位 无 KB 18 处/有 KB 13 处
**本案例投入**：耗时 34s → 46s（增加 12s（34% ↑））；费用 未提供 → 未提供（数据不足）

### 场景 S4：故障排查：找到规则来源，同时克制根因臆断

#### S4-A 账户余额出现负数

**用户实际问了什么**：

> 测试发现账户余额出现负数。请基于项目排查：余额非负规则在哪里定义，当前数据库和已提供的代码是否真正保证它，哪些事实已经确认，哪些写入路径或运行数据还需要补充。给出下一步排查顺序，不要把未看到的扣款逻辑写成已确认根因。

**无 KB 实际回答**（耗时 47s，tokens —，费用 未提供）：

> • I'll start by mapping the rule definition and the write paths.
> 
> • Rule found so far: only in comments, no DB constraint. Now I need the write paths.
> 
> • <thinking>The "balance" grep results seem truncated? It listed only some files. Wait, the first grep pattern included many alternatives, so files matching any. Note it did NOT list payment-service. Interesting.
> 
>   Let me now read the key write-path candidates:
>   - legacy-account-service/src/main/java/com/demo/legacy/account/service/AccountService.java
>   - legacy-account-service mapper xml
>   - order-service OrderMapper.xml
>   - payment-service PaymentService.java + mapper xml
>   - PointsPage.vue, legacy-account README
> 
>   Let me read them in parallel.
> 
>   Also need legacy-account-service.sql fully, and check for any other sql noise files with account/balance write paths.
> 
>   Let me read a batch.</thinking>
> …（完整回答：`transcripts/S4-A.log`）

**有 KB 实际回答**（耗时 50s，tokens —，费用 未提供）：

> • 我先按项目约定读取 KnowledgeBase 导航，再定位余额非负规则的定义位置。
> 
> • 找到了 `RULE-account-balance-non-negative.md` 与对账相关文档。我并行读取规则、表模型、对账流程，并直接在代码/DDL 中搜索余额写入路径。
> 
> • KB 只覆盖 4 个服务，但仓库里有 16 个模块，这本身是重要线索。我直接看 DDL、噪声目录，并全仓搜索余额写入。
> 
> • DDL 只在表注释里写了约束，没有 `CHECK`；全仓 Java 代码里只在 `AccountEntity` 出现 `balance`。我继续核实噪声目录、待确认项与仓库里其他服务的账户代码。
> 
> • 全仓只有 `t_order` 有 UPDATE，`t_user_account` 任何地方都没有写语句。我继续核实 account-service 源码、各服务数据源指向、以及是否存在可复现的运行数据。
> 
> • 账户服务的数据源指向远端 `10.20.31.14`，本机没有 MySQL 客户端。我核实是否有 `CHECK` 约束、调度启用、以及谁引用了账户表。
> 
> • 核实运行态与其余模块：是否有测试夹具、其他 `@Scheduled`、以及 user-input 清单。
> 
> • 关键点已基本清晰。最后确认 git 历史里是否有被删除/未合并的余额扣减代码。
> 
> • ## 结论速览
> 
> …（完整回答：`transcripts/S4-A.log`）

| 检查项 | 无 KB | 有 KB |
|--------|-------|-------|
| 找到非负规则来源（余额表注释，非积分/库存等影子域） | ✅ 通过 | ✅ 通过 |
| 指出 DDL 未声明 CHECK 约束（注释≠强制） | ✅ 通过 | ✅ 通过 |
| 不臆断扣款逻辑为已确认根因 | ✅ 通过 | ✅ 通过 |
| 给出下一步排查方向 | ✅ 通过 | ✅ 通过 |

**证据密度**：引用不同文件 无 KB 21 个/有 KB 12 个；行号定位 无 KB 17 处/有 KB 11 处
**本案例投入**：耗时 47s → 50s（增加 4s（8% ↑））；费用 未提供 → 未提供（数据不足）

### 场景 S5：架构与方案评审：用规则基线拦住危险方案

#### S5-A 评审：发货条件放宽为 PAID 或 CREATED

**用户实际问了什么**：

> 评审下面的变更提案：把发货条件从「仅 PAID」放宽为「PAID 或 CREATED」，其他流程不变，以提升履约速度。请给出是否可直接上线的结论、违反的现有约束、受影响的业务路径、必须补充的设计和验证。请区分现有代码事实、规则基线和待业务确认事项。

**无 KB 实际回答**（耗时 52s，tokens —，费用 未提供）：

> • I'll start by establishing the code facts before assessing the proposal.
> 
> • Small codebase — I'll read the relevant files directly.
> 
> • 已完成代码勘察（order / logistics / payment / inventory / web-portal / db / 各 README）。结论如下。
> 
>   ## 结论
> 
>   **不可直接上线。** 该变更不是"某流程放宽"，而是**修改订单状态机的核心不变量**：它新增了一条 `CREATED → SHIPPED` 迁移，使 `PAID` 从"发货的必要前置"变为"可跳过"。仅凭一行判断改动就能实现，但会把"先货后款"引入资金链路，并且会立刻暴露一个现有的未防护回退路径（`markPaid` 无条件改写状态）。必须补齐设计和验证后才能进入评审通过。另外注意：**"其他流程不变"在效果上不成立** —— 相关代码一行不改，但 `markPaid` 会在一个新的当前状态下被调用，语义已经改变。
> 
>   ## 一、变更的准确形态（现有代码事实）
> 
>   发货准入只在一个地方实现，是单点：
> 
>   - `order-service/src/main/java/com/demo/order/service/OrderService.java:31-33` —— `if (current != OrderStatus.PAID) throw new IllegalStateException("仅已支付订单可发货")`；:28-30 先拦截 `CANCELLED`。
>   - 入口 `order-service/.../controller/OrderController.java:17-21` `POST /api/order/{orderId}/ship`；前端 `web-portal/src/views/OrderPage.vue:4` 的发货按钮**无状态门禁**，`web-portal/src/api/index.js:4` 直连该接口 → 规则完全由后端这一处承担。
>   - `ship()` **不发布任何事件**：`OrderEventProducer.java:10-11,19-21` 只定义了 `order.exchange` / `order.paid`，没有 `order.shipped`。发货动作对下游不可见。
> 
> …（完整回答：`transcripts/S5-A.log`）

**有 KB 实际回答**（耗时 1m14s，tokens —，费用 未提供）：

> • I'll start by reading the project's knowledge base navigation, then dig into the actual code.
> 
> • Now let me read the ship flow doc and explore the knowledge base structure.
> 
> • Now let me read the actual source code and the open questions.
> 
> • Now let me check for discrepancies: the directory lists many more services than the knowledge base documents, plus the open questions and the frontend.
> 
> • Now let me examine the open questions, frontend, and the paid-event path — plus whether the out-of-scope services touch order state.
> 
> • <thinking>Good — the noise modules are explicitly labeled noise (噪声模块) and are not part of the real order flow. payment-service's PaymentService is broken code (references `paymentMapper` undefined) — clearly noise/fixture. logistics-service similarly broken. legacy-trade is explicitly "与新订单服务的现货订单无关". So they are decoys. However, payment-service README says "支付与退款（订单支付状态的下游）" — a claim. But it's noise per db/noise and the api/index.js comment. Also payment-service has no status-update to t_order. So no real coupling. I'll note it as a boundary: no cross-service code writes t_order.status.
> 
>   Important: `db/noise/payment-service.sql` — let me check whether the payment table records order status. Let me quickly look at payment-service.sql and its README, plus logistics README. Actually, worth a quick check to be able to state confidently: "no code outside order-service writes t_order.status". The grep already confirmed: only order-service references t_order and OrderStatus. Good. Note: grep for "t_order" found only order-service + db/init.sql. Good.
> 
>   Now, is there a payment record concept tied to order? Let me check payment-service entity/sql briefly — it may have order_id and status. That's relevant to the argument "no authoritative payment source to check whether a CREATED order is actually paid." Let me check.
> 
>   Also check: business/README.md for rule/flow states & counting, and check the capabilities dir. And check the data-model doc for t_order (TABLE-t_order.md) and the interfaces README. And check page doc PAGE-order-manage.md.
> 
> …（完整回答：`transcripts/S5-A.log`）

| 检查项 | 无 KB | 有 KB |
|--------|-------|-------|
| 结论：不可直接上线 | ✅ 通过 | ✅ 通过 |
| 指出 CREATED 未满足已支付前提 | ✅ 通过 | ✅ 通过 |
| 要求业务批准/流程重设计而非仅改代码 | ✅ 通过 | ✅ 通过 |

**证据密度**：引用不同文件 无 KB 19 个/有 KB 23 个；行号定位 无 KB 19 处/有 KB 22 处
**本案例投入**：耗时 52s → 1m14s（增加 22s（42% ↑））；费用 未提供 → 未提供（数据不足）

#### S5-B 评审：零业务侵入的全景 API 提案

**用户实际问了什么**：

> 评审一项「零业务侵入」的用户全景 API 提案：直接用 user_id 拼接用户、账户和订单查询结果，宣称现有接口足以保证每人只有一个账户、不会缺失记录，因此无需补充约束或验证。请逐项判断哪些承诺有证据，哪些没有，并给出上线门禁。

**无 KB 实际回答**（耗时 42s，tokens —，费用 未提供）：

> • I'll gather evidence from the actual schema and services before judging any of these claims.
> 
> • Critical schema fact already: `t_user_account` has a unique key only on `account_no`, not on `user_id`. Let me read the service-layer code.
> 
> • Now the legacy services and cross-cutting `user_id` semantics — the riskiest part of a claim like this.
> 
> • 已把提案依赖的每个事实在代码和 DDL 里核过一遍。结论：**三项承诺里，只有一项在半狭义上成立；「每人只有一个账户」被 schema 直接否证，「不会缺失记录」无任何证据，「现有接口足以」还自相矛盾**——订单侧根本不存在按 user_id 查询的能力。
> 
>   ## 逐项判定
> 
>   | 承诺 | 证据 | 判定 |
>   |---|---|---|
>   | 现有接口足以支撑拼接 | 订单侧只有 `OrderMapper.selectById(orderId)` / `updateStatus`（`order-service/src/main/java/com/demo/order/mapper/OrderMapper.java:10-11`），SQL 是 `WHERE order_id = #{orderId}`（`OrderMapper.xml:5`），Controller 只有 `POST /{orderId}/ship`。全仓 grep `selectByUserId|selectByUser` 只命中 account 一处 | **否证**。没有任何「按 user_id 查订单」的接口 |
>   | 每人只有一个账户 | DDL 只有 `UNIQUE KEY uk_account_no (account_no)`，**user_id 上没有唯一约束**（`db/init.sql:15-22`）；`UserBasicService`/`AccountService` 无任何校验；本仓没有任何插入 account 的代码路径 | **否证**（只是「当前数据恰好如此」的假设） |
>   | 不会缺失记录 | 三表分属三个库（`demo_user`/`demo_account`/`demo_order`，`db/init.sql:2,12,24`）且主机不同（user 指向 `localhost`，account 指向 `10.20.31.14`，见各自 `application.yml`）；无外键、无分布式事务；`queryAccount` 直接透传 mapper 结果、无 null 处理（`AccountService.java:18-20`） | **无证据** |
>   | 零业务侵入 | account 接口注释自称「对内 REST，供聚合能力复用」（`AccountController.java:18`），这一条腿成立 | **仅局部成立**。订单腿要么新增按用户查询（侵入），要么跨库直读别人的表（更糟） |
> 
>   补充两条会被忽略的坑：
> …（完整回答：`transcripts/S5-B.log`）

**有 KB 实际回答**（耗时 1m4s，tokens —，费用 未提供）：

> • I'll start by reading the project knowledge base navigation, then dig into the actual schemas and interfaces the proposal depends on.
> 
> • Interesting — there's already a capability doc for exactly this (`CAP-user-full-info`). Let me read the core evidence: the capability, the three tables, and the two query interfaces.
> 
> • Now let me read the interfaces index, the open questions, the user request, and the actual source/DDL that the claims rest on.
> 
> • Now let me verify the claims against actual source — especially the account mapper's row semantics and whether any order-query-by-user interface exists.
> 
> • Let me check the Maven dependencies (MyBatis starter, test deps), the remaining mappers/mq, and grep the KB for any "one account per user" evidence.
> 
> • The KB already documents the exact failure modes. Let me check the business rules and glossary for any account-cardinality or referential-integrity statement.
> 
> • Let me confirm the entity accessors (a factor in whether fields survive serialization) and the front-end consumption pattern.
> 
> • 已完成对提案的证据核验。核验范围：`capabilities/CAP-user-full-info.md`、三张表文档、两个来源接口文档、`open-questions.md`、`db/init.sql` 及 `user/account/order` 三个服务的实际源码。
> 
>   ## 结论
> 
> …（完整回答：`transcripts/S5-B.log`）

| 检查项 | 无 KB | 有 KB |
|--------|-------|-------|
| 指出「每人一个账户」的承诺无证据 | ✅ 通过 | ✅ 通过 |
| 指出「不会缺失记录」的承诺无证据 | ✅ 通过 | ✅ 通过 |
| 给出上线门禁项 | ✅ 通过 | ✅ 通过 |

**证据密度**：引用不同文件 无 KB 6 个/有 KB 18 个；行号定位 无 KB 7 处/有 KB 17 处
**本案例投入**：耗时 42s → 1m4s（增加 23s（54% ↑））；费用 未提供 → 未提供（数据不足）

## 三、结论

- 运行案例：7 个（5 场景）
- 机械判据质量：有 KB 提升 **1** 个；持平 **6** 个；退化 **0** 个（通过率 无 KB 24/25 → 有 KB 25/25）
- 证据密度：引用不同文件 无 KB 123 → 有 KB 119；行号定位 无 KB 131 → 有 KB 118

**解读**（本轮实测，非通用结论）：

1. **质量持平的成因**：本 fixture 仅 5 个服务/4 张表，裸代码 1-2 分钟即可 grep 完，无 KB 端已把检查项全部答对——机械判据达到上限，区分不出两臂。
2. **可观测的真实差异是证据纪律**：有 KB 回答平均引用文件数为无 KB 的 1.0 倍、行号定位 0.9 倍，且每条结论带四类证据交叉核验（知识库/当前代码/数据模型/配置）与开放问题编号（如 Q-M9 关联待确认），可直接追溯。
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

**规模放大未改变质量结论**：两批机械判据均满分，说明无 KB 端在本题集上不存在「找不到/漏掉」；规模增大只体现为耗时代价放大。
