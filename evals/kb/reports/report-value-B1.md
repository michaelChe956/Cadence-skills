# KnowledgeBase 价值报告（同端配对实验）

- **批次**：`B1`
- **对比条件**：同一 agent `pi`、同一 model `default`、同一源码快照、同一任务 prompt
- **唯一变量**：是否提供知识库环境（KB 产物 + AGENTS.md 导航）
- **说明**：检查项为确定性判据，报告同时附回答原文供人工复核；“提问”两侧完全一致。

## 一、总览

| 场景 | 案例 | 无 KB | 有 KB | 核心差异 | 耗时（无→有）|
|------|------|-------|-------|----------|--------------|
| 能力组合发现… | S1-A 基本信息 + 账户信息组合 | 4/4 | 4/4 | 质量持平 | 1m43s → 3m46s |
| 能力组合发现… | S1-B 用户全景报表方案（跨三域） | 3/3 | 3/3 | 质量持平 | 1m57s → 5m24s |
| 业务规则引用… | S2-A 已取消订单要求发货 | 4/4 | 4/4 | 质量持平 | 55s → 2m0s |
| 变更影响分析… | S3-A user_name 长度 64 → 128 影响分析 | 4/4 | 4/4 | 质量持平 | 1m3s → 3m19s |
| 故障排查：找… | S4-A 账户余额出现负数 | 4/4 | 4/4 | 质量持平 | 1m31s → 3m15s |
| 架构与方案评… | S5-A 评审：发货条件放宽为 PAID 或 CREATED | 3/3 | 3/3 | 质量持平 | 1m37s → 3m5s |
| 架构与方案评… | S5-B 评审：零业务侵入的全景 API 提案 | 3/3 | 3/3 | 质量持平 | 1m46s → 3m28s |

**合计**：无 KB **25/25** 项检查通过 → 有 KB **25/25** 项（提升 **0** 项）

- 总耗时：无 KB **10m34s** → 有 KB **24m19s**（增加 13m44s（130% ↑））
- 总费用：无 KB **未提供** → 有 KB **未提供**（pi CLI 未上报 usage，无法比较；如需费用维度可用 claude 端补测）

## 二、逐场景明细

### 场景 S1：能力组合发现：从分散接口发现可复用的新能力

#### S1-A 基本信息 + 账户信息组合

**用户实际问了什么**：

> 运营希望按用户查看「基本信息 + 账户信息」。请基于当前项目说明：已有能力如何组合、各自真实入口、关联字段、是否已有可直接调用的聚合接口，以及上线前必须确认的限制。不要实现代码；每项结论请给可核查来源。

**无 KB 实际回答**（耗时 1m43s，tokens —，费用 未提供）：

> 分析完成。以下结论全部基于仓库实际代码（`/home/tester/work/project`），每项附可核查来源。
> 
> ---
> 
> ## 一、结论总览
> 
> 「基本信息 + 账户信息」目前**没有现成的聚合接口**，只能由**两个独立 REST API 组合**实现；且两条链路上各存在会直接导致上线故障的缺陷（序列化、字段映射），必须先修复/确认。
> 
> ---
> 
> ## 二、已有能力与真实入口
> 
> | 能力 | 入口 | 调用链 | 数据源 |
> |---|---|---|---|
> | 用户基本信息 | `GET /api/user/basic/{userId}`，端口 **8081** | `UserBasicController#queryBasic` → `UserBasicService#queryBasic` → `UserMapper.selectById` | `demo_user.t_user` |
> | 账户信息 | `GET /api/account/{userId}`，端口 **8082** | `AccountController#queryAccount` → `AccountService#queryAccount` → `AccountMapper.selectByUserId` | `demo_account.t_user_account` |
> 
> 来源：
> …（完整回答：`transcripts/S1-A.log`）

**有 KB 实际回答**（耗时 3m46s，tokens —，费用 未提供）：

> 四类证据路径全部闭合。以下先给任务上下文包（紧凑版），再给结论回答。
> 
> ---
> 
> ## 任务上下文包（需求澄清 · 主画像，无辅助画像）
> 
> **1. 任务识别**：运营按用户查看「基本信息 + 账户信息」——是否可由现有能力组合、入口、关联字段、聚合接口有无、上线限制。
> 
> **2. 任务理解**：知识库中已存在与该诉求一一对应的组合能力实体 `CAP-user-full-info`「全部用户信息」（用户诉求登记于 `cadence/knowledge-base/user-input/api-scope.md:19-21`，期望输出即“用户基本信息+账户信息”、连接键 `userId`）。
> 
> **3. 核心实体**：`CAP-user-full-info`（proposed）、`API-user-basic`（对外）、`API-account-query`（对内）、`TABLE-t_user`（DB-demo_user）、`TABLE-t_user_account`（DB-demo_account）、`PAGE-user-list`/`PAGE-account-query`。
> 
> **4. 四类证据矩阵**（关键行）：
> 
> | 结论 | KnowledgeBase | 当前代码 | DDL/数据模型 | 配置快照 | 状态 |
> |---|---|---|---|---|---|
> | 两个查询能力已实现并暴露 | `interfaces/README.md` 对外/对内清单 | `UserBasicController.java:19-21`、`AccountController.java:19-22` 逐字核对一致 | `UserMapper.xml:4-7`、`AccountMapper.xml:5-7` 一致 | 端口 8081/8082 与 `application.yml:1-2` 一致 | 一致 |
> | 无聚合端点 | `CAP-user-full-info.md#8` `implementation_api_ids` 为空 | 两服务仅 2 个 Controller；无 Feign/RestTemplate/WebClient（pom + 源码 grep 无命中） | 不适用 | 不适用 | 一致 |
> …（完整回答：`transcripts/S1-A.log`）

| 检查项 | 无 KB | 有 KB |
|--------|-------|-------|
| 找对两个真实入口（用户基本信息 / 账户查询） | ✅ 通过 | ✅ 通过 |
| 指出 userId 为关联键 | ✅ 通过 | ✅ 通过 |
| 明确当前没有可直接调用的聚合接口（可组合 ≠ 已实现） | ✅ 通过 | ✅ 通过 |
| 指出账户记录基数/唯一性未证实（限制项） | ✅ 通过 | ✅ 通过 |

**证据密度**：引用不同文件 无 KB 12 个/有 KB 30 个；行号定位 无 KB 3 处/有 KB 39 处
**本案例投入**：耗时 1m43s → 3m46s（增加 2m02s（119% ↑））；费用 未提供 → 未提供（数据不足）

#### S1-B 用户全景报表方案（跨三域）

**用户实际问了什么**：

> 需要一份「用户基本信息 + 账户 + 订单」的运营全景报表。请设计最小数据获取方案：哪些现有能力可复用、如何关联、关联基数和缺失数据如何处理、哪些关键问题目前还没有证据。不要把尚未实现的能力当成现成 API。

**无 KB 实际回答**（耗时 1m57s，tokens —，费用 未提供）：

> 分析完成。以下方案全部基于仓库内代码证据，未实现的能力均标注为缺口，不当作现成 API。
> 
> # 「用户 + 账户 + 订单」运营全景报表 · 最小数据获取方案
> 
> ## 一、现有能力盘点（可复用部分）
> 
> | 能力 | 入口 | 证据 | 报表可用性 |
> |---|---|---|---|
> | 用户基本信息单查 | `GET /api/user/basic/{userId}`（user-service :8081） | `UserBasicController` + `UserMapper.xml` selectById，查 `demo_user.t_user` | ✅ 可复用，返回 userId/userName/mobile/email |
> | 账户单查 | `GET /api/account/{userId}`（account-service :8082） | `AccountController` + `AccountMapper.xml` selectByUserId，查 `demo_account.t_user_account` | ⚠️ 可复用但有映射隐患（见四-3） |
> | 订单查询 | **不存在** | `OrderController` 仅有 `POST /{orderId}/ship`（动作）；`selectById` 只是 ship 的内部依赖 | ❌ 缺口 |
> | 订单导出 | `POST /api/order/export` | `ExportController` 返回硬编码 `"taskId"`，`ExportService` 仅一个常量；`t_export_file` 无任何读写代码 | ❌ 桩代码，不可当数据通道 |
> | MQ `order.paid` | — | `OrderEventListener.onOrderPaid` 空实现 | ❌ 无派生数据 |
> | 每日对账 | `ReconcileJob`（2:00，enabled=true） | 实现体省略（fixture） | ❌ 不可作数据源 |
> 
> ## 二、关联模型与基数
> 
> **关联键**：`user_id` 三表同源（`db/init.sql` 注释与实体注释均声明"同 `t_user.user_id`"）。
> …（完整回答：`transcripts/S1-B.log`）

**有 KB 实际回答**（耗时 5m24s，tokens —，费用 未提供）：

> 四条证据路径已闭合。输出上下文包并继续原始任务。
> 
> ---
> 
> # 一、任务上下文包
> 
> **1. 任务识别**：主画像 Design、辅助画像 需求澄清。Manifest 校验通过（`manifest.yaml` schema_version "4.0"）；数据基线 `1f867b9f`（master），当前 `main@e98b1b2`，`git diff 基线..HEAD` 为空 → **无任务对象基线漂移**（仅分支名差异，另未跟踪文件仅 `AGENTS.md` 与 `cadence/` 本身）。
> 
> **2. 任务理解**：为「用户基本信息 + 账户 + 订单」运营全景报表设计**最小数据获取方案**——可复用能力、关联方式、基数与缺失处理、无证据问题；硬约束：未实现能力不得当作现成 API。
> 
> **3. 核心实体**：`API-user-basic`、`API-account-query`、`API-order-export`、`CAP-user-full-info`、`FILE-order-export-file`、`TABLE-t_user`、`TABLE-t_user_account`、`TABLE-t_order`、`TABLE-t_export_file`、`CONFIGGROUP-{user,account,order}-datasource`。
> 
> **4. 四类证据矩阵**
> 
> | 结论 | KnowledgeBase | 当前代码 | DDL/数据模型 | 配置 | 状态 |
> |---|---|---|---|---|---|
> | 用户查询能力已实现，仅单用户 path 参数、无列表/分页 | `interfaces/API-user-basic_..参数与报文.md` | `UserBasicController.java:19-21`；全仓端点扫描仅 4 个 | `UserMapper.xml:4-7` 仅 selectById | 无直接关系 | 一致 |
> | 账户查询能力已实现，仅单用户；响应字段依赖隐式驼峰映射 | `interfaces/API-account-query_..参数与报文.md` | `AccountController.java:19-22` | `AccountMapper.xml:4-7`（SELECT *，无 resultMap） | 无直接关系 | 一致（映射本身待确认 Q-M3） |
> …（完整回答：`transcripts/S1-B.log`）

| 检查项 | 无 KB | 有 KB |
|--------|-------|-------|
| 覆盖三个数据域 | ✅ 通过 | ✅ 通过 |
| 明确订单维组合无现成能力或需新增 | ✅ 通过 | ✅ 通过 |
| 给出关联键 | ✅ 通过 | ✅ 通过 |

**证据密度**：引用不同文件 无 KB 5 个/有 KB 18 个；行号定位 无 KB 8 处/有 KB 20 处
**本案例投入**：耗时 1m57s → 5m24s（增加 3m26s（176% ↑））；费用 未提供 → 未提供（数据不足）

### 场景 S2：业务规则引用与遵守：避免为满足需求而破坏业务约束

#### S2-A 已取消订单要求发货

**用户实际问了什么**：

> 运营要求已取消的订单也能直接点击「发货」，理由是货物已经打包。请判断当前系统是否允许，说明涉及的状态前置条件和证据，并给出不绕过现有业务约束的处理建议。不要修改代码。

**无 KB 实际回答**（耗时 55s，tokens —，费用 未提供）：

> ## 结论：当前系统**不允许**对已取消订单发货
> 
> 前端「发货」按钮可以点击（无状态限制），但请求会在后端被状态机拦截，抛出 `IllegalStateException`，发货不会成功。
> 
> ## 状态前置条件
> 
> `ship()` 的唯一合法入口状态是 **PAID（已支付）**，目标状态 SHIPPED；**CANCELLED 是终态**，状态机规格为 `CREATED → PAID → SHIPPED → COMPLETED；任意非终态 → CANCELLED`（`OrderStatus.java:3`）。
> 
> ## 证据
> 
> | 层 | 位置 | 内容 |
> |---|---|---|
> | 服务层（实际约束点） | `order-service/.../service/OrderService.java:25-34` | `if (current == CANCELLED) throw "已取消订单不可发货"`；`if (current != PAID) throw "仅已支付订单可发货"` |
> | 状态机规格 | `order-service/.../entity/OrderStatus.java:3` | CANCELLED 为终态，无出边 |
> | 测试即规格 | `order-service/src/test/.../OrderServiceTest.java:14-27` | `cancelledOrderCannotShip` 断言 CANCELLED 订单调用 `ship` 必抛 `IllegalStateException` |
> | 接口注释 | `order-service/.../controller/OrderController.java:6` | 明示「已取消订单不可发货」由 OrderService 状态机约束 |
> | 数据库 | `db/init.sql:26-33` | `t_order` 表注释「状态迁移受 OrderService 状态机约束」 |
> | 前端 | `web-portal/src/views/OrderPage.vue:4,10` | 按钮未做状态禁用，点击即调 `POST /api/order/{id}/ship`（且硬编码 orderId=1），被后端拒绝 |
> …（完整回答：`transcripts/S2-A.log`）

**有 KB 实际回答**（耗时 2m0s，tokens —，费用 未提供）：

> 上下文收集完成（四类路径均闭环），先给出任务上下文包，再回答原始问题。
> 
> ## 任务上下文包（主画像：需求澄清）
> 
> 1. **任务识别**：判断「已取消（`CANCELLED`）订单能否发货」，属现有能力边界澄清；不修改代码。
> 2. **任务理解**：核实发货入口的状态前置条件与实现层约束，评估运营诉求与现有业务约束的冲突及合规处理路径。
> 3. **核心实体**：`FLOW-order-ship`(confirmed)、`RULE-order-ship-constraint`(confirmed)、`RULE-order-status-transition`(ai-draft，未经人工核准)、`API-order-ship`、`PAGE-order-manage`、`MODULE-order-core`、`TABLE-t_order`。
> 4. **四类证据矩阵**：
> 
> | 结论 | KnowledgeBase | 当前代码 | DDL/数据模型 | 配置 | 状态 |
> |------|---------------|----------|--------------|------|------|
> | 仅 `PAID` 可发货，`CANCELLED` 拒绝 | RULE-order-ship-constraint；FLOW-order-ship §4 | `OrderService.java:25-35` | `TABLE-t_order.md:82`（状态机在服务层，SQL 无前置条件） | 无直接配置关系（OrderService 无任何配置绑定） | 一致 |
> | 前端按钮无状态门禁 | FLOW-order-ship 步骤 1、Q-L7 | `OrderPage.vue:4,10`（按钮恒可点，`orderId` 硬编码 `1`） | 无直接关系 | 无直接关系 | 一致 |
> | 无事务/条件更新（并发可绕过检查） | Q-M11 | `OrderMapper.xml:7-9`（UPDATE 仅 `WHERE order_id`） | `db/init.sql`（无 CHECK 约束，仅注释） | 无直接关系 | 一致 |
> 
> 5. **关系与影响面**：`PAGE-order-manage → API-order-ship(POST /api/order/{orderId}/ship) → OrderService#ship → t_order.status`；规则由 `RULE-order-status-transition` 提供状态链。
> 6. **数据模型上下文**：`t_order.status VARCHAR(16) NOT NULL`，取值 `CREATED/PAID/SHIPPED/COMPLETED/CANCELLED`（`db/init.sql:29,32`）；约束完全在服务层，DB 无强制。
> 7. **配置上下文**：发货规则无配置开关/Feature Flag → 无直接配置关系，停止该方向，未读取外部快照。
> …（完整回答：`transcripts/S2-A.log`）

| 检查项 | 无 KB | 有 KB |
|--------|-------|-------|
| 明确拒绝：已取消订单不可直接发货 | ✅ 通过 | ✅ 通过 |
| 指出现有发货前置条件为 PAID | ✅ 通过 | ✅ 通过 |
| 给出不绕过约束的处理建议 | ✅ 通过 | ✅ 通过 |
| 不提出绕过约束的直接改状态方案 | ✅ 通过 | ✅ 通过 |

**证据密度**：引用不同文件 无 KB 8 个/有 KB 11 个；行号定位 无 KB 7 处/有 KB 15 处
**本案例投入**：耗时 55s → 2m0s（增加 1m05s（119% ↑））；费用 未提供 → 未提供（数据不足）

### 场景 S3：变更影响分析：一次找到跨层影响，降低遗漏

#### S3-A user_name 长度 64 → 128 影响分析

**用户实际问了什么**：

> 计划将用户姓名字段 user_name 的最大长度从 64 调整为 128。请只做变更影响分析：列出数据库、实体/映射、查询接口、前端页面等需要修改或需要核验的具体位置，说明每个位置的依赖关系和验证建议；没有长度限制的地方不要硬说必须修改。

**无 KB 实际回答**（耗时 1m3s，tokens —，费用 未提供）：

> 核查完成，全代码链路已通读（user-service 读链、account/order 服务、web-portal、db）。以下是 `user_name` 长度 64 → 128 的变更影响分析。**未做任何代码修改。**
> 
> ## 字段链路
> 
> `t_user.user_name` → `UserMapper.xml`（SELECT 别名映射）→ `UserEntity.userName` → `UserBasicController GET /api/user/basic/{userId}` → `web-portal/api/index.js queryUserBasic` → `UserList.vue`（纯展示）
> 
> 该链路**只有查询，没有写入路径**（`UserMapper` 仅 `selectById`，无 INSERT/UPDATE），因此长度约束只存在于数据库层。
> 
> ## 一、必须修改（存在硬性长度限制）
> 
> | # | 位置 | 现状 | 说明 |
> |---|------|------|------|
> | 1 | `db/init.sql:6` | `user_name VARCHAR(64) NOT NULL` | **全代码库唯一的长度硬约束**，改为 `VARCHAR(128)` |
> 
> - **依赖关系**：数据库是链路的唯一事实源；init.sql 只影响新建环境，存量环境需单独执行 `ALTER TABLE demo_user.t_user MODIFY COLUMN user_name VARCHAR(128) NOT NULL COMMENT '用户姓名';`
> - **验证建议**：
>   - `SHOW CREATE TABLE t_user;` 确认列类型已变更；
>   - 测试环境插入 128 字符姓名应成功、129 字符应报错（1406 Data too long）；
> …（完整回答：`transcripts/S3-A.log`）

**有 KB 实际回答**（耗时 3m19s，tokens —，费用 未提供）：

> 四条证据路径已走完且可互证。先按 skill 输出压缩版任务上下文包，再交付影响分析本体。
> 
> ---
> 
> ## 任务上下文包（压缩）
> 
> **1-2. 任务识别/理解**：`t_user.user_name` 长度 64→128 变更影响分析（只分析不改码）。主画像 `Plan`，辅助 `Design`。
> **3. 核心实体**：`TABLE-t_user`（DB-demo_user）、字段 `user_name`、`CODE-UserEntity`、`CODE-UserMapperXml-selectById`、`API-user-basic`（GET /api/user/basic/{userId}）、`PAGE-user-list`、`SERVICE-user-service`/`MODULE-user-basic`、`FLOW-user-basic-query`。
> **4. 四类证据矩阵**：
> 
> | 结论 | KnowledgeBase | 当前代码 | DDL/数据模型 | 配置快照 | 状态 |
> |---|---|---|---|---|---|
> | user_name 唯一长度约束在 DDL | TABLE-t_user.md:26 | `db/init.sql:6` | VARCHAR(64) NOT NULL，仅主键索引 | 无直接关系 | 一致 |
> | Entity/Mapper/Controller/前端无长度限制 | 同上文档 §6-8 | UserEntity.java:7（无注解）、UserMapper.xml:5（仅 SELECT+AS）、Controller:19-21、UserList.vue:4（纯展示） | 表无写入语句（INSERT/UPDATE 未发现） | 无直接关系 | 一致 |
> | 全仓 user_name/userName 仅 4 处命中 | relation-graph.yaml | grep 全仓：DDL、Entity、Mapper XML、UserList.vue | t_user_account/t_order 仅引用 user_id | 无直接关系 | 一致 |
> 
> **5. 影响面**：`t_user` →（SELECT）→ `API-user-basic` → `PAGE-user-list`，单向只读链，无反向依赖。
> **6. 数据模型上下文**：`db/init.sql` 是唯一 DDL（Manifest `migrations: []`，无迁移体系、无 Entity 注解）；user_name 无二级索引/唯一约束（TABLE-t_user.md §4），NOT NULL。
> …（完整回答：`transcripts/S3-A.log`）

| 检查项 | 无 KB | 有 KB |
|--------|-------|-------|
| 定位 DDL 中 VARCHAR(64) 定义 | ✅ 通过 | ✅ 通过 |
| 覆盖数据层与代码层影响 | ✅ 通过 | ✅ 通过 |
| 覆盖实体/Mapper 或接口层 | ✅ 通过 | ✅ 通过 |
| 覆盖前端页面层 | ✅ 通过 | ✅ 通过 |

**证据密度**：引用不同文件 无 KB 10 个/有 KB 15 个；行号定位 无 KB 6 处/有 KB 22 处
**本案例投入**：耗时 1m3s → 3m19s（增加 2m16s（216% ↑））；费用 未提供 → 未提供（数据不足）

### 场景 S4：故障排查：找到规则来源，同时克制根因臆断

#### S4-A 账户余额出现负数

**用户实际问了什么**：

> 测试发现账户余额出现负数。请基于项目排查：余额非负规则在哪里定义，当前数据库和已提供的代码是否真正保证它，哪些事实已经确认，哪些写入路径或运行数据还需要补充。给出下一步排查顺序，不要把未看到的扣款逻辑写成已确认根因。

**无 KB 实际回答**（耗时 1m31s，tokens —，费用 未提供）：

> 排查完成。以下是完整结论（当前环境无 MySQL 客户端、无 /cadence/stack，运行库 10.20.31.14 无法从本机直接查询，结论仅基于仓库内代码、DDL 与 git 历史）。
> 
> ## 一、"余额非负"规则定义在哪里（已确认，共 3 处，全部是注释级）
> 
> | 位置 | 内容 | 性质 |
> |---|---|---|
> | `db/init.sql:19` | 列注释 `balance ... 业务规则：余额不可为负` | 仅注释 |
> | `db/init.sql:22` | 表注释 `本表余额字段不允许出现负值（业务硬约束）` | 仅注释 |
> | `account-service/.../entity/AccountEntity.java:9` | 字段注释 `业务规则见表注释：余额不可为负` | 仅注释 |
> 
> ## 二、当前数据库和代码是否真正保证它 —— **都不能保证**
> 
> **数据库层（init.sql）：**
> - `balance DECIMAL(18,2) NOT NULL DEFAULT 0` —— 有符号 DECIMAL，天然接受负数；
> - 无 `CHECK (balance >= 0)`、无 UNSIGNED、无触发器、无存储过程。所谓"硬约束"只存在于注释里。
> 
> **应用层（本仓库快照）：**
> - account-service **只有一条读路径**：`AccountMapper.selectByUserId`（`SELECT *`），无任何 INSERT/UPDATE；
> …（完整回答：`transcripts/S4-A.log`）

**有 KB 实际回答**（耗时 3m15s，tokens —，费用 未提供）：

> 四条证据路径已闭合。先给上下文包（十三节），再给排查结论与下一步顺序。
> 
> ---
> 
> ## 任务上下文包（主画像 Debug，辅画像 Plan）
> 
> **1. 任务识别** 测试发现 `t_user_account.balance` 出现负数；定位非负规则定义、核验 DB 与代码是否保证、分离已确认事实与待补证据、给出排查顺序。
> **2. 任务理解** 不是修复任务，是事实核查 + 根因排查启动；严禁把未观察到的扣款逻辑写成已确认根因。
> **3. 核心实体** `RULE-account-balance-non-negative`、`TABLE-t_user_account`、`SERVICE-account-service`、`MODULE-order-event`、`JOB-reconcile`、`EVENT-order-paid`、`CONFIGGROUP-account-datasource`/`account-reconcile`。
> **4. 四类证据矩阵**
> 
> | 结论 | KnowledgeBase | 当前代码 | DDL/数据模型 | 配置 | 状态 |
> |---|---|---|---|---|---|
> | 规则仅定义于 DDL 注释 | `RULE-account-balance-non-negative.md`（ai-draft，未经人工核准） | `db/init.sql:19,22` 注释存在 | 同左 | 无直接关系 | 一致 |
> | DB 层无 CHECK/UNSIGNED/触发器 | `TABLE-t_user_account.md` §4、§10 | `db/init.sql:15-22` 仅 PK + `uk_account_no` | `balance DECIMAL(18,2)` 有符号 | — | 一致 |
> | 全仓无 `t_user_account` 写语句 | 表文档 §6“写入链路缺失” | 全仓 grep：唯一 `<update>` 是 `OrderMapper.xml:7`（写 `t_order`） | — | — | 一致 |
> | 对账任务不可能写库 | `FLOW-account-reconcile.md`（ai-draft，未经人工核准） | `ReconcileJob.java:14-17` 方法体为空 | — | `AccountApplication.java` 无 `@EnableScheduling` | 一致 |
> | MQ 消费者不写账户 | `FLOW-order-paid-event.md`（ai-draft，未经人工核准；Q-M10） | `OrderEventListener.java:19-28` 空方法体 | — | 见第 7 节 | 一致 |
> …（完整回答：`transcripts/S4-A.log`）

| 检查项 | 无 KB | 有 KB |
|--------|-------|-------|
| 找到非负规则来源（表注释） | ✅ 通过 | ✅ 通过 |
| 指出 DDL 未声明 CHECK 约束（注释≠强制） | ✅ 通过 | ✅ 通过 |
| 不臆断扣款逻辑为已确认根因 | ✅ 通过 | ✅ 通过 |
| 给出下一步排查方向 | ✅ 通过 | ✅ 通过 |

**证据密度**：引用不同文件 无 KB 4 个/有 KB 13 个；行号定位 无 KB 5 处/有 KB 15 处
**本案例投入**：耗时 1m31s → 3m15s（增加 1m43s（113% ↑））；费用 未提供 → 未提供（数据不足）

### 场景 S5：架构与方案评审：用规则基线拦住危险方案

#### S5-A 评审：发货条件放宽为 PAID 或 CREATED

**用户实际问了什么**：

> 评审下面的变更提案：把发货条件从「仅 PAID」放宽为「PAID 或 CREATED」，其他流程不变，以提升履约速度。请给出是否可直接上线的结论、违反的现有约束、受影响的业务路径、必须补充的设计和验证。请区分现有代码事实、规则基线和待业务确认事项。

**无 KB 实际回答**（耗时 1m37s，tokens —，费用 未提供）：

> 已完成对 order-service、account-service、web-portal、db 及测试的全面核查。以下为评审结论。
> 
> ---
> 
> ## 一、结论：**不可直接上线**
> 
> 该提案不是简单的条件放宽，而是**改写订单状态机的核心不变量（先付款、后发货）**，且现有实现存在无状态前置条件的 UPDATE 和无守卫的支付回调，放宽后将引入状态回退竞态、资金风险与对账口径破坏。必须先补齐设计与验证（见第五、六节）。
> 
> ---
> 
> ## 二、现有代码事实（基于代码，非推断）
> 
> | # | 事实 | 证据 |
> |---|------|------|
> | F1 | 发货守卫：`CANCELLED` 拒绝；`!= PAID` 拒绝（含 CREATED），仅 `PAID → SHIPPED` | `order-service/.../service/OrderService.java` `ship()`，异常文案「仅已支付订单可发货」 |
> | F2 | 状态机以注释形式定义为规格：`CREATED → PAID → SHIPPED → COMPLETED`；任意非终态 → CANCELLED | `OrderStatus.java` 枚举注释 |
> | F3 | 测试即规格：现有测试仅钉住「CANCELLED 不可发货」，**未**钉住 CREATED 不可发货（测试覆盖有缺口） | `OrderServiceTest.java` 类注释 + `cancelledOrderCannotShip()` |
> | F4 | `updateStatus` 为**无条件 UPDATE**（`SET status=#{status} WHERE order_id=...`），无 `WHERE status=...` 前置条件，且 `ship()` 不检查返回的影响行数 | `OrderMapper.xml`、`OrderService.ship()` |
> …（完整回答：`transcripts/S5-A.log`）

**有 KB 实际回答**（耗时 3m5s，tokens —，费用 未提供）：

> 四条证据路径（知识库语义 / 当前代码 / 数据模型 / 配置）均已核查完毕。以下为评审结论。
> 
> ---
> 
> # 变更提案评审：发货条件由「仅 PAID」放宽为「PAID 或 CREATED」
> 
> **评审基线**：Manifest `schema_version 4.0`；知识库 Git 基线 `1f867b9` 在当前仓库不可解析（`git` 报 "Not a valid commit name"），当前 HEAD 为 `e98b1b2`。任务相关 6 个文件（`OrderService.java`、`OrderController.java`、`OrderMapper.xml`、`OrderStatus.java`、`OrderServiceTest.java`、`db/init.sql`）内容与知识库文档逐字一致，判定为 **Manifest 元数据漂移、内容无冲突**（`基线漂移`，非阻断）。无已处理变更包（`processed_packages: []`）。
> 
> ## 一、结论：**不可直接上线（阻断）**
> 
> 理由（满足任一即阻断，本提案同时命中四条）：
> 
> 1. 直接违反 **confirmed** 级规则 `RULE-order-ship-constraint`，提案未附带规则卡、测试规格（测试即规格）与流程文档的修订方案；
> 2. 未处理 `OrderService#markPaid` 无状态前置校验的缺陷——放宽后一旦支付入口接入，已发货订单会被**回退为 PAID** 并误发 `order.paid` 事件；
> 3. 未补并发条件更新，Q-M11 的竞态从「重复发货」扩大为「**支付状态被发货覆盖丢失**」；
> 4. 行为规格当前不可执行（JUnit 5 未在 `order-service/pom.xml` 声明，Q-H1），无回归验证手段。
> 
> ## 二、现有代码事实（当前提交 e98b1b2 逐条核对）
> …（完整回答：`transcripts/S5-A.log`）

| 检查项 | 无 KB | 有 KB |
|--------|-------|-------|
| 结论：不可直接上线 | ✅ 通过 | ✅ 通过 |
| 指出 CREATED 未满足已支付前提 | ✅ 通过 | ✅ 通过 |
| 要求业务批准/流程重设计而非仅改代码 | ✅ 通过 | ✅ 通过 |

**证据密度**：引用不同文件 无 KB 11 个/有 KB 15 个；行号定位 无 KB 0 处/有 KB 26 处
**本案例投入**：耗时 1m37s → 3m5s（增加 1m27s（90% ↑））；费用 未提供 → 未提供（数据不足）

#### S5-B 评审：零业务侵入的全景 API 提案

**用户实际问了什么**：

> 评审一项「零业务侵入」的用户全景 API 提案：直接用 user_id 拼接用户、账户和订单查询结果，宣称现有接口足以保证每人只有一个账户、不会缺失记录，因此无需补充约束或验证。请逐项判断哪些承诺有证据，哪些没有，并给出上线门禁。

**无 KB 实际回答**（耗时 1m46s，tokens —，费用 未提供）：

> 核查完毕。以下是基于代码证据的逐项评审。
> 
> ## 结论摘要
> 
> 提案的两项核心承诺——**「每人只有一个账户」**和**「不会缺失记录」**——均无代码/DDL 证据支持，且各有结构性反证；「零业务侵入」的前提不成立：**订单侧根本不存在按 user_id 查询的接口**，拼接方案所需的查询能力首先就得新开发。
> 
> ## 逐项判定
> 
> | # | 提案承诺 | 判定 | 证据 |
> |---|---------|------|------|
> | 1 | user_id 可作为三表关联键 | ✅ 有证据 | `db/init.sql`：三表均有 `user_id` 且注释标注「同 t_user.user_id」；`t_user.user_id` 为主键，用户表侧 1:1 成立 |
> | 2 | 现有接口保证每人只有一个账户 | ❌ 无证据，有反证 | 见下文 A |
> | 3 | 不会缺失记录 | ❌ 无证据，有决定性反证 | 见下文 B |
> | 4 | 零业务侵入、无需补充约束 | ❌ 不成立 | 见下文 C |
> 
> ### A.「一人一账户」——无约束、无校验、查询会炸
> 
> - **DDL 不保证**：`t_user_account` 仅有 `UNIQUE KEY uk_account_no (account_no)`，`user_id` 上**没有任何唯一约束**（`db/init.sql`）。
> …（完整回答：`transcripts/S5-B.log`）

**有 KB 实际回答**（耗时 3m28s，tokens —，费用 未提供）：

> 四条证据路径读取完成，证据充分，停止扩展。以下先给出任务上下文包（十三节），随后是评审结论本体。
> 
> ---
> 
> ## 任务上下文包（Review 主画像 + Design 辅助画像）
> 
> **1. 任务识别**：评审「零业务侵入用户全景 API」提案——用 `user_id` 直接拼接用户/账户/订单查询结果，宣称①现有接口保证每人只有一个账户②不会缺失记录③无需补充约束或验证。
> 
> **2. 任务理解**：对提案三项承诺逐项做证据判定，并输出上线门禁。注意：知识库已登记的组合能力 `CAP-user-full-info`（proposed）仅含用户+账户两源，**不含订单**；提案实际是对既有 proposed 组合的范围扩展。
> 
> **3. 核心实体**：`CAP-user-full-info`、`API-user-basic`、`API-account-query`、`TABLE-t_user`、`TABLE-t_user_account`、`TABLE-t_order`、`JOIN_KEY(userId)`。
> 
> **4. 四类证据矩阵**
> 
> | 结论 | KnowledgeBase | 当前代码 | DDL/数据模型 | 配置快照 | 状态 |
> |---|---|---|---|---|---|
> | `t_user_account.user_id` 无唯一约束 | `TABLE-t_user_account.md#4` | `AccountMapper.java:10`（单对象返回） | `db/init.sql:16-21`（仅 PK `id`、`uk_account_no(account_no)`） | 无直接关系 | 一致 |
> | 无"一人一户"业务规则 | `business/rules/`（仅 4 条规则，无账户唯一性）；grep 无命中 | 无写入口（无 INSERT） | DDL 无 CHECK/触发器 | — | 一致（规则不存在） |
> …（完整回答：`transcripts/S5-B.log`）

| 检查项 | 无 KB | 有 KB |
|--------|-------|-------|
| 指出「每人一个账户」的承诺无证据 | ✅ 通过 | ✅ 通过 |
| 指出「不会缺失记录」的承诺无证据 | ✅ 通过 | ✅ 通过 |
| 给出上线门禁项 | ✅ 通过 | ✅ 通过 |

**证据密度**：引用不同文件 无 KB 4 个/有 KB 12 个；行号定位 无 KB 3 处/有 KB 8 处
**本案例投入**：耗时 1m46s → 3m28s（增加 1m41s（95% ↑））；费用 未提供 → 未提供（数据不足）

## 三、结论

- 运行案例：7 个（5 场景）
- 机械判据质量：有 KB 提升 **0** 个；持平 **7** 个；退化 **0** 个（通过率 无 KB 25/25 → 有 KB 25/25）
- 证据密度：引用不同文件 无 KB 54 → 有 KB 114；行号定位 无 KB 32 → 有 KB 145

**解读**（本轮实测，非通用结论）：

1. **质量持平的成因**：本 fixture 仅 5 个服务/4 张表，裸代码 1-2 分钟即可 grep 完，无 KB 端已把检查项全部答对——机械判据达到上限，区分不出两臂。
2. **可观测的真实差异是证据纪律**：有 KB 回答平均引用文件数为无 KB 的 2.1 倍、行号定位 4.5 倍，且每条结论带四类证据交叉核验（知识库/当前代码/数据模型/配置）与开放问题编号（如 Q-M9 关联待确认），可直接追溯。
3. **代价**：有 KB 单任务耗时约为无 KB 的 2.3 倍（读 KB 有固定开销）；KB 首次构建另计（历史实测约 60 分钟）。
4. **适用边界**：KB 价值主张在于大代码库/跨模块/新人接手/规则沉淀场景；本 fixture 规模不足以体现「找不到」与「漏掉」的差距，属实验下限。

## 四、边界与说明

- 判据为确定性关键词/实体核验（可审计），开放性问题标注“待复核”；
- 费用来自 CLI 上报的实际 usage，缺失显示“未提供”，不折算为 0；
- 单轮配对实验，不声称统计显著；KB 首次构建成本（约 60min）未计入单任务耗时；
- 完整回答原文见 `results/exp/<批次>/<agent>-<arm>/transcripts/`。
