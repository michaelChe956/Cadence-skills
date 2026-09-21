# KnowledgeBase 价值报告（同端配对实验）

- **批次**：`B2`
- **对比条件**：同一 agent `pi`、同一 model `default`、同一源码快照、同一任务 prompt
- **代码规模**：fixture `large`（172 个文件）
- **唯一变量**：是否提供知识库环境（KB 产物 + AGENTS.md 导航）
- **说明**：检查项为确定性判据，报告同时附回答原文供人工复核；“提问”两侧完全一致。

## 一、总览

| 场景 | 案例 | 无 KB | 有 KB | 核心差异 | 耗时（无→有）|
|------|------|-------|-------|----------|--------------|
| 能力组合发现… | S1-A 基本信息 + 账户信息组合 | 4/4 | 4/4 | 质量持平 | 2m0s → 3m33s |
| 能力组合发现… | S1-B 用户全景报表方案（跨三域） | 3/3 | 3/3 | 质量持平 | 1m51s → 3m42s |
| 业务规则引用… | S2-A 已取消订单要求发货 | 4/4 | 4/4 | 质量持平 | 1m7s → 2m16s |
| 变更影响分析… | S3-A user_name 长度 64 → 128 影响分析 | 4/4 | 4/4 | 质量持平 | 1m19s → 2m36s |
| 故障排查：找… | S4-A 账户余额出现负数 | 4/4 | 4/4 | 质量持平 | 1m19s → 3m45s |
| 架构与方案评… | S5-A 评审：发货条件放宽为 PAID 或 CREATED | 3/3 | 3/3 | 质量持平 | 1m46s → 2m54s |
| 架构与方案评… | S5-B 评审：零业务侵入的全景 API 提案 | 3/3 | 3/3 | 质量持平 | 1m59s → 3m8s |

**合计**：无 KB **25/25** 项检查通过 → 有 KB **25/25** 项（提升 **0** 项）

- 总耗时：无 KB **11m24s** → 有 KB **21m58s**（增加 10m33s（93% ↑））
- 总费用：无 KB **未提供** → 有 KB **未提供**（pi CLI 未上报 usage，无法比较；如需费用维度可用 claude 端补测）

## 二、逐场景明细

### 场景 S1：能力组合发现：从分散接口发现可复用的新能力

#### S1-A 基本信息 + 账户信息组合

**用户实际问了什么**：

> 运营希望按用户查看「基本信息 + 账户信息」。请基于当前项目说明：已有能力如何组合、各自真实入口、关联字段、是否已有可直接调用的聚合接口，以及上线前必须确认的限制。不要实现代码；每项结论请给可核查来源。

**无 KB 实际回答**（耗时 2m0s，tokens —，费用 未提供）：

> 调研完成（已核实全部结论均来自仓库内代码/配置/DDL，非文档转述）。结论如下：
> 
> ## 一、已有能力与真实入口
> 
> | 能力 | 真实入口 | 返回字段 | 数据源 |
> |---|---|---|---|
> | 基本信息（API-A） | `GET /api/user/basic/{userId}`，user-service，端口 8081 | userId、userName、mobile、email | `demo_user.t_user` |
> | 账户信息（API-B） | `GET /api/account/{userId}`，account-service，端口 8082 | userId、accountNo、balance、status | `demo_account.t_user_account` |
> 
> 来源：
> - `user-service/src/main/java/com/demo/user/controller/UserBasicController.java:9,15-21`（`@RequestMapping("/api/user")` + `@GetMapping("/basic/{userId}")`）；SQL 见 `user-service/src/main/resources/mapper/UserMapper.xml:5-7`（显式 `AS` 别名映射）；端口/库见 `user-service/src/main/resources/application.yml`
> - `account-service/src/main/java/com/demo/account/controller/AccountController.java:9,14-21`，注释明确写了「对内 REST，供聚合能力复用」；SQL 见 `account-service/src/main/resources/mapper/AccountMapper.xml:3-6`；端口/库见 `account-service/src/main/resources/application.yml`
> 
> ## 二、关联字段
> 
> - **关联键：`user_id`**。DDL 注释显式声明同源：`db/init.sql` 中 `t_user_account.user_id ... COMMENT '用户唯一标识，同 t_user.user_id'`；`AccountEntity.java` 注释亦注明「与 t_user.user_id 同源」。
> - 两表分属**不同数据库实例**（`demo_user@localhost:3306` vs `demo_account@10.20.31.14:3306`，见两服务 application.yml）→ **SQL JOIN 不可行，只能在应用层按 userId 二次调用后合并**。
> 
> …（完整回答：`transcripts/S1-A.log`）

**有 KB 实际回答**（耗时 3m33s，tokens —，费用 未提供）：

> 上下文收集完成（四条证据路径均已核验）。以下为面向该需求的结论，每项附可核查来源；未实现任何代码，也未修改知识库。
> 
> ---
> 
> # 「按用户查看 基本信息+账户信息」能力组合分析
> 
> ## 1. 已有能力如何组合（设计已存在，未实现）
> 
> - 知识库已将该诉求登记为组合能力 **`CAP-user-full-info`（全部用户信息）**，状态 **`proposed`**（=设计已确认、未实现）
>   - 编排：`parallel_join`，两来源能力以 **`userId`** 为连接键并行调用；输出按命名空间合并（`profile:` 承载基本信息、`accounts:` 承载账户信息），禁覆盖同名字段；失败策略登记为 `partial`（单侧失败返回已成功部分——此策略为诉求未定义项，见 Q-M13）
>   - 来源：`cadence/knowledge-base/capabilities/CAP-user-full-info.md` §3/§4/§8；诉求原始声明 `cadence/knowledge-base/user-input/api-scope.md:19-21`
> - 两个来源能力（互不感知，分属两个服务、两个库，无跨服务调用）：
>   - `API-user-basic`（查询用户基本信息，**对外** REST）
>   - `API-account-query`（账户信息查询，**对内** REST）
>   - 来源：`cadence/knowledge-base/interfaces/README.md`「对外能力」「对内能力」「能力组合」分区
> 
> ## 2. 各自真实入口（当前代码已逐一复核）
> 
> …（完整回答：`transcripts/S1-A.log`）

| 检查项 | 无 KB | 有 KB |
|--------|-------|-------|
| 找对两个真实入口（用户基本信息 / 账户查询） | ✅ 通过 | ✅ 通过 |
| 指出 userId 为关联键 | ✅ 通过 | ✅ 通过 |
| 明确当前没有可直接调用的聚合接口（可组合 ≠ 已实现） | ✅ 通过 | ✅ 通过 |
| 指出账户记录基数/唯一性未证实（限制项） | ✅ 通过 | ✅ 通过 |

**证据密度**：引用不同文件 无 KB 18 个/有 KB 23 个；行号定位 无 KB 13 处/有 KB 26 处
**本案例投入**：耗时 2m0s → 3m33s（增加 1m32s（77% ↑））；费用 未提供 → 未提供（数据不足）

#### S1-B 用户全景报表方案（跨三域）

**用户实际问了什么**：

> 需要一份「用户基本信息 + 账户 + 订单」的运营全景报表。请设计最小数据获取方案：哪些现有能力可复用、如何关联、关联基数和缺失数据如何处理、哪些关键问题目前还没有证据。不要把尚未实现的能力当成现成 API。

**无 KB 实际回答**（耗时 1m51s，tokens —，费用 未提供）：

> 分析完成。三个目标域的代码、DDL、前端调用面、legacy 服务都已核实。以下是设计方案。
> 
> ---
> 
> # 「用户 + 账户 + 订单」运营全景报表 —— 最小数据获取方案
> 
> ## 一、可复用的现有能力（有代码证据）
> 
> | 能力 | 入口 | 证据 | 局限 |
> |---|---|---|---|
> | 用户基本信息单查 | `GET /api/user/basic/{userId}` | `UserBasicController`，SQL 显式 `AS` 映射，返回 userId/姓名/手机/邮箱 | 仅按已知 ID 单查，**无列表、无批量、无分页** |
> | 账户单查 | `GET /api/account/{userId}` | `AccountController` → `selectByUserId` | 同上；且见下方「复用风险」 |
> | 订单支付事件 | RabbitMQ `order.exchange` / `order.paid` | `OrderEventProducer`，`markPaid` 后发布 | 消息体只有 orderId，监听器是空实现；只能做增量信号，不是查询能力 |
> | 三表数据模型 | `db/init.sql` | `t_user` / `t_user_account` / `t_order`，跨库以 `user_id` 逻辑关联 | 分属 demo_user / demo_account / demo_order 三个库、不同数据源实例 |
> 
> ## 二、不能当成现成能力的（防踩坑）
> 
> 1. **report-service 不可用**：README 宣称“运营日报与导出任务登记”，但代码只有 Entity + Mapper，**无 Controller、无 Service**；且 `ReportEntity` 字段类型写的是 `BIGINT`/`VARCHAR(32)`（非 Java 类型，**无法编译**）。不存在任何报表生成 API。
> …（完整回答：`transcripts/S1-B.log`）

**有 KB 实际回答**（耗时 3m42s，tokens —，费用 未提供）：

> 四条证据路径均已闭合。按 skill 输出任务上下文包（13 节精简版），随后给出方案设计。
> 
> ---
> 
> # 一、任务上下文包（Design 主画像 / 需求澄清辅助）
> 
> **1. 任务识别**：设计「用户基本信息 + 账户 + 订单」运营全景报表的最小数据获取方案；主画像 Design，辅助画像 需求澄清。
> 
> **2. 任务理解**：不新建业务库表为前提，识别可复用能力、关联方式、基数与缺失数据处理、无证据的关键问题；明确区分“已实现”与“仅声明/存根/proposed”。
> 
> **3. 核心实体**：`API-user-basic`、`API-account-query`、`API-order-ship`、`API-order-export`（存根）、`CAP-user-full-info`（proposed）、`TABLE-t_user`(DB-demo_user)、`TABLE-t_user_account`(DB-demo_account)、`TABLE-t_order`(DB-demo_order)、`TABLE-t_export_file`、`CONFIGGROUP-user/account/order-datasource`。
> 
> **4. 四类证据矩阵**
> 
> | 结论 | KnowledgeBase | 当前代码 | DDL/数据模型 | 配置快照 | 状态 |
> |---|---|---|---|---|---|
> | 用户查询仅单笔 by userId | API-user-basic 主文件+报文文档 | `UserBasicController.java:19-22`、`UserMapper.xml:4-7` | `t_user` 仅 PK，无二级索引 | `application.yml:6-9` 数据源存在 | 一致 |
> | 账户查询仅单笔 by userId，字段映射隐式 | Q-M3 记录 | `AccountMapper.xml:4-7`（`SELECT *` 无 resultMap） | DDL 已确认；`user_id` 无唯一约束 | 数据源存在（值 `<redacted>`，非本机地址） | 一致（映射风险=待确认 Q-M3） |
> …（完整回答：`transcripts/S1-B.log`）

| 检查项 | 无 KB | 有 KB |
|--------|-------|-------|
| 覆盖三个数据域 | ✅ 通过 | ✅ 通过 |
| 明确订单维组合无现成能力或需新增 | ✅ 通过 | ✅ 通过 |
| 给出关联键 | ✅ 通过 | ✅ 通过 |

**证据密度**：引用不同文件 无 KB 3 个/有 KB 7 个；行号定位 无 KB 2 处/有 KB 14 处
**本案例投入**：耗时 1m51s → 3m42s（增加 1m51s（100% ↑））；费用 未提供 → 未提供（数据不足）

### 场景 S2：业务规则引用与遵守：避免为满足需求而破坏业务约束

#### S2-A 已取消订单要求发货

**用户实际问了什么**：

> 运营要求已取消的订单也能直接点击「发货」，理由是货物已经打包。请判断当前系统是否允许，说明涉及的状态前置条件和证据，并给出不绕过现有业务约束的处理建议。不要修改代码。

**无 KB 实际回答**（耗时 1m7s，tokens —，费用 未提供）：

> ## 结论：当前系统**不允许**已取消订单发货
> 
> 「已取消（CANCELLED）」在订单状态机中是**终态**，`ship` 操作对它有显式硬校验，后端会直接抛异常拒绝。
> 
> ## 状态前置条件（发货的唯一合法路径）
> 
> 状态机定义（`order-service/src/main/java/com/demo/order/entity/OrderStatus.java:3`）：
> 
> ```
> CREATED → PAID → SHIPPED → COMPLETED；任意非终态 → CANCELLED
> ```
> 
> `ship` 的前置条件（`order-service/src/main/java/com/demo/order/service/OrderService.java:26-34`）：
> 1. 当前状态 ≠ `CANCELLED` —— 否则抛 `IllegalStateException("已取消订单不可发货")`（第 28-30 行）
> 2. 当前状态 == `PAID` —— 否则抛 `IllegalStateException("仅已支付订单可发货")`（第 31-33 行）
> 
> 即唯一合法迁移是 **PAID → SHIPPED**，CANCELLED 没有任何出边。
> 
> …（完整回答：`transcripts/S2-A.log`）

**有 KB 实际回答**（耗时 2m16s，tokens —，费用 未提供）：

> 四条证据路径已闭合（配置方向经检查确认与本任务无直接关系，未读取外部快照）。以下为任务上下文包与结论。
> 
> ---
> 
> ## 一、结论：当前系统**不允许**已取消订单发货
> 
> 前端按钮本身无条件可点，但请求会被后端状态机拦截，**不产生任何数据变更**，最终以异常（HTTP 500）失败。
> 
> **状态前置条件（唯一放行路径）**：`t_order.status` 必须为 `PAID`，才允许流转为 `SHIPPED`。`CANCELLED` 被单独、优先地拒绝。
> 
> ## 二、证据矩阵
> 
> | 结论 | KnowledgeBase | 当前代码 | DDL/数据模型 | 配置快照 | 状态 |
> |------|---------------|----------|--------------|----------|------|
> | 已取消订单不可发货 | `RULE-order-ship-constraint`（confirmed）规则卡 | `OrderService.java:28-30` 抛 `IllegalStateException("已取消订单不可发货")` | `db/init.sql:32` 表注释“状态迁移受 OrderService 状态机约束” | 无直接关系 | 一致 |
> | 仅 `PAID` 可发货 | `FLOW-order-ship` §4 状态流转表 | `OrderService.java:31-34`：非 `PAID` 抛异常，仅 `PAID` 执行 `updateStatus` | `TABLE-t_order.md` §5 `status` 状态机约束行 | 无直接关系 | 一致 |
> | 状态机 5 态、`CANCELLED` 为终态 | `RULE-order-status-transition`（**ai-draft，未经人工核准**） | `OrderStatus.java:3-9` 枚举与类注释 | `db/init.sql:29` 列注释列 5 个取值 | 无直接关系 | 一致 |
> | 拦截发生在服务层，DB/SQL 层无防线 | `FLOW-order-ship` §6 | `OrderMapper.xml:7-9` UPDATE 无 `WHERE status` 前置条件 | DDL 无 CHECK/触发器（`TABLE-t_order.md` §4） | 无直接关系 | 一致 |
> …（完整回答：`transcripts/S2-A.log`）

| 检查项 | 无 KB | 有 KB |
|--------|-------|-------|
| 明确拒绝：已取消订单不可直接发货 | ✅ 通过 | ✅ 通过 |
| 指出现有发货前置条件为 PAID | ✅ 通过 | ✅ 通过 |
| 给出不绕过约束的处理建议 | ✅ 通过 | ✅ 通过 |
| 不提出绕过约束的直接改状态方案 | ✅ 通过 | ✅ 通过 |

**证据密度**：引用不同文件 无 KB 9 个/有 KB 8 个；行号定位 无 KB 7 处/有 KB 8 处
**本案例投入**：耗时 1m7s → 2m16s（增加 1m08s（101% ↑））；费用 未提供 → 未提供（数据不足）

### 场景 S3：变更影响分析：一次找到跨层影响，降低遗漏

#### S3-A user_name 长度 64 → 128 影响分析

**用户实际问了什么**：

> 计划将用户姓名字段 user_name 的最大长度从 64 调整为 128。请只做变更影响分析：列出数据库、实体/映射、查询接口、前端页面等需要修改或需要核验的具体位置，说明每个位置的依赖关系和验证建议；没有长度限制的地方不要硬说必须修改。

**无 KB 实际回答**（耗时 1m19s，tokens —，费用 未提供）：

> 分析完成。全库检索范围：SQL DDL、Java 实体/Mapper XML/Controller/Service、MQ 消息、导出逻辑、前端 Vue/JS。以下是变更影响分析。
> 
> ## 一、字段流转链路（依赖关系总览）
> 
> ```
> db/init.sql (t_user.user_name VARCHAR(64))
>   └─ user-service UserMapper.xml（SELECT user_name AS userName，只读查询）
>        └─ UserEntity.userName（String，无校验注解）
>             └─ UserBasicService → UserBasicController GET /api/user/basic/{userId}
>                  └─ web-portal api/index.js queryUserBasic（axios 透传）
>                       └─ UserList.vue 插值展示 u.userName
> ```
> 
> ## 二、必须修改的位置（仅 1 处）
> 
> | # | 位置 | 说明 |
> |---|------|------|
> | 1 | `db/init.sql:6` — `user_name VARCHAR(64) NOT NULL` | **全代码库唯一的长度硬约束**，改为 `VARCHAR(128)`。注意 init.sql 只覆盖全新环境；存量环境需补一条迁移脚本：`ALTER TABLE demo_user.t_user MODIFY COLUMN user_name VARCHAR(128) NOT NULL COMMENT '用户姓名';` |
> …（完整回答：`transcripts/S3-A.log`）

**有 KB 实际回答**（耗时 2m36s，tokens —，费用 未提供）：

> 四类证据路径与基线核对完成，上下文收集停止（继续扩展仅会进入无关表/公共设施）。以下先给出任务上下文包（紧凑版），再交付变更影响分析。
> 
> ---
> 
> ## 任务上下文包（主画像 Plan，辅助 Design）
> 
> | 节 | 内容 |
> |---|---|
> | 1 任务识别 | `user_name` 最大长度 64→128 的变更影响分析（只分析，不改码） |
> | 2 任务理解 | 定位所有携带长度语义的位置与纯传递/纯展示位置，区分"必须改/仅核验" |
> | 3 核心实体 | `TABLE-t_user`（DB-demo_user）、`API-user-basic`、`PAGE-user-list`、`MODULE-user-basic`、`CODE-UserEntity`、`CODE-UserMapperXml-selectById` |
> | 4 证据矩阵 | 见下文影响表各行状态列（四类来源均已核对） |
> | 5 关系与影响面 | `PAGE-user-list → API-user-basic → MODULE-user-basic → TABLE-t_user`（FLOW-user-basic-query，confirmed）；关系图 `relation-graph.yaml` 一跳边已核 |
> | 6 数据模型 | `user_name VARCHAR(64) NOT NULL`，`db/init.sql:6`；无索引在 user_name（仅 PRIMARY(user_id)，init.sql:5）；无迁移文件（manifest `migrations: []`） |
> | 7 配置 | **无直接配置关系**：user_name 长度非配置键，`CONFIGGROUP-user-datasource` 仅为连接配置，不受列宽影响；未读取外部快照 |
> | 8 相关变更包 | `last_change_package`/`processed_packages` 均为空，无已处理变更包 |
> | 9 画像专属 | 变更单元/依赖顺序/验证入口见下文；写链路缺失是关键缺口 |
> | 10 约束与模式 | 显式 `AS` 别名映射模式；Entity 无注解无 getter/setter；响应为 Entity 直接序列化 |
> …（完整回答：`transcripts/S3-A.log`）

| 检查项 | 无 KB | 有 KB |
|--------|-------|-------|
| 定位 DDL 中 VARCHAR(64) 定义 | ✅ 通过 | ✅ 通过 |
| 覆盖数据层与代码层影响 | ✅ 通过 | ✅ 通过 |
| 覆盖实体/Mapper 或接口层 | ✅ 通过 | ✅ 通过 |
| 覆盖前端页面层 | ✅ 通过 | ✅ 通过 |

**证据密度**：引用不同文件 无 KB 10 个/有 KB 13 个；行号定位 无 KB 1 处/有 KB 11 处
**本案例投入**：耗时 1m19s → 2m36s（增加 1m17s（97% ↑））；费用 未提供 → 未提供（数据不足）

### 场景 S4：故障排查：找到规则来源，同时克制根因臆断

#### S4-A 账户余额出现负数

**用户实际问了什么**：

> 测试发现账户余额出现负数。请基于项目排查：余额非负规则在哪里定义，当前数据库和已提供的代码是否真正保证它，哪些事实已经确认，哪些写入路径或运行数据还需要补充。给出下一步排查顺序，不要把未看到的扣款逻辑写成已确认根因。

**无 KB 实际回答**（耗时 1m19s，tokens —，费用 未提供）：

> 排查完成。以下结论严格区分“已确认”与“待补充”，不预设根因。
> 
> ## 一、余额非负规则定义在哪（已确认）
> 
> 规则**只以文档/注释形式存在**，共两处：
> 
> | 位置 | 内容 |
> |---|---|
> | `db/init.sql:19` | 列注释：`balance DECIMAL(18,2) NOT NULL DEFAULT 0 COMMENT '账户余额；业务规则：余额不可为负'` |
> | `db/init.sql:22` | 表注释：`'用户账户表；本表余额字段不允许出现负值（业务硬约束）'` |
> | `account-service/.../entity/AccountEntity.java:9` | 实体 Javadoc 复述同一规则 |
> 
> 类比规则（非资金）：`db/noise/legacy-account-service.sql` 中 `t_legacy_points_account.points` "积分不可为负”——那是遗留**积分**账户，与本次资金余额无关，勿混淆。
> 
> ## 二、数据库是否真正保证（部分确认）
> 
> - **仓库内 DDL：不保证。** `init.sql` 的 `t_user_account` 没有 `CHECK (balance >= 0)`、没有触发器、`DECIMAL(18,2)` 为有符号。`NOT NULL DEFAULT 0` 只约束空值，不约束负数。注释不具强制力。
> - **线上库（10.20.31.14/demo_account）：无法核实。** 本环境无 mysql 客户端、devbox-stack 门禁不满足，实际建表语句可能与仓库不一致（例如手工加过 CHECK，且 MySQL <8.0.16 时 CHECK 也不生效）。此为待补充项。
> …（完整回答：`transcripts/S4-A.log`）

**有 KB 实际回答**（耗时 3m45s，tokens —，费用 未提供）：

> 四条证据路径已闭合（配置快照门禁失败已记录为阻断）。以下先给任务上下文包（十三节），再给排查结论与下一步顺序。
> 
> ---
> 
> ## 任务上下文包
> 
> **1. 任务识别**：主画像 Debug，辅助画像 Plan。症状：测试中账户余额出现负数。
> 
> **2. 任务理解**：回答四个问题——非负规则定义位置；DDL+已提供代码是否真正保证；已确认事实 vs 待补事实；下一步排查顺序。明确约束：不得将未见过的扣款逻辑写成已确认根因。
> 
> **3. 核心实体**：`RULE-account-balance-non-negative`（ai-draft）、`TABLE-t_user_account`、`SERVICE-account-service`/`MODULE-account-core`、`JOB-reconcile`、`EVENT-order-paid`、`CONFIGGROUP-account-datasource`/`account-reconcile`。
> 
> **4. 四类证据矩阵**
> 
> | 结论 | KnowledgeBase | 当前代码 | DDL/数据模型 | 配置快照 | 状态 | 任务影响 |
> |------|---------------|----------|--------------|----------|------|----------|
> | 非负规则仅存在于 DDL 注释 | 规则卡 ai-draft | 无任何校验代码 | `db/init.sql:19,22` 注释 | 无直接关系 | 一致（Q-L9） | 规则无强制力 |
> | DDL 无 CHECK/触发器/外键 | 表文档第 4/10 节 | — | `db/init.sql:15-22` | — | 一致 | DB 层不保证非负 |
> …（完整回答：`transcripts/S4-A.log`）

| 检查项 | 无 KB | 有 KB |
|--------|-------|-------|
| 找到非负规则来源（余额表注释，非积分/库存等影子域） | ✅ 通过 | ✅ 通过 |
| 指出 DDL 未声明 CHECK 约束（注释≠强制） | ✅ 通过 | ✅ 通过 |
| 不臆断扣款逻辑为已确认根因 | ✅ 通过 | ✅ 通过 |
| 给出下一步排查方向 | ✅ 通过 | ✅ 通过 |

**证据密度**：引用不同文件 无 KB 5 个/有 KB 7 个；行号定位 无 KB 3 处/有 KB 11 处
**本案例投入**：耗时 1m19s → 3m45s（增加 2m26s（185% ↑））；费用 未提供 → 未提供（数据不足）

### 场景 S5：架构与方案评审：用规则基线拦住危险方案

#### S5-A 评审：发货条件放宽为 PAID 或 CREATED

**用户实际问了什么**：

> 评审下面的变更提案：把发货条件从「仅 PAID」放宽为「PAID 或 CREATED」，其他流程不变，以提升履约速度。请给出是否可直接上线的结论、违反的现有约束、受影响的业务路径、必须补充的设计和验证。请区分现有代码事实、规则基线和待业务确认事项。

**无 KB 实际回答**（耗时 1m46s，tokens —，费用 未提供）：

> # 变更提案评审：发货条件 PAID → PAID 或 CREATED
> 
> ## 一、结论：**不可直接上线**
> 
> 提案「其他流程不变」与现有代码存在**硬冲突**：`markPaid()` 会无条件把状态改写为 PAID。若在 CREATED 状态发货（→SHIPPED），随后支付回调到达，状态将从 SHIPPED **倒退回 PAID**，状态机被破坏且重复发布 `order.paid` 事件。此外存在资损风险敞口（先货后款无风控）和多处规格基线（枚举注释、测试即规格、DDL 埋点注释）未同步。必须补齐下述设计与验证后方可上线。
> 
> ---
> 
> ## 二、现有代码事实（以代码为准）
> 
> | 位置 | 事实 |
> |---|---|
> | `order-service/.../OrderService.java` `ship()` | 先拦 CANCELLED，再要求 `current == PAID`，否则抛「仅已支付订单可发货」；仅改状态，不发事件 |
> | 同文件 `markPaid()` | **无条件** `updateStatus(PAID)` 并发布 `order.paid` 事件，无前置状态校验、无 CAS |
> | `OrderMapper.xml` `updateStatus` | `UPDATE t_order SET status=#{status} WHERE order_id=#{orderId}`，**无状态条件**，非幂等、无并发保护 |
> | `OrderStatus.java` | 枚举注释定义状态机：CREATED → PAID → SHIPPED → COMPLETED；任意非终态 → CANCELLED |
> | `OrderServiceTest.java` | 类注释「测试即规格」，现有用例仅覆盖 CANCELLED 不可发货 |
> | `db/init.sql` | t_order 表注释「状态迁移受 OrderService 状态机约束」（F6 埋点约定：业务规则写在表注释） |
> …（完整回答：`transcripts/S5-A.log`）

**有 KB 实际回答**（耗时 2m54s，tokens —，费用 未提供）：

> # 一、任务上下文包（Review 主画像 / Design 辅助画像）
> 
> **1. 任务识别**：评审变更提案——发货前置状态从「仅 PAID」放宽为「PAID 或 CREATED」，其余流程不变，目标是提升履约速度。
> **2. 任务理解**：修改 `API-order-ship` 状态机校验分支，使 `CREATED` 状态订单可流转为 `SHIPPED`；判断可上线性、违反约束、影响面与必补设计/验证。
> **3. 核心实体**：`RULE-order-ship-constraint`、`RULE-order-status-transition`、`FLOW-order-ship`、`API-order-ship`、`MODULE-order-core`、`TABLE-t_order`、`EVENT-order-paid`、`PAGE-order-manage`（均已读文件确认存在，relation-graph 命中 `evidence/relation-graph.yaml:234,344,404`）。
> **4. 四类证据矩阵**：
> 
> | 结论 | KnowledgeBase | 当前代码 | DDL/数据模型 | 配置快照 | 状态 | 任务影响 |
> |---|---|---|---|---|---|---|
> | 仅 PAID 可发货 | RULE-order-ship-constraint（confirmed） | `OrderService.java:25-35`（CANCELLED/非PAID 两级拒绝） | `db/init.sql:32` 表注释 | 无直接配置关系 | 一致 | 提案直接改写该分支 |
> | 状态取值与迁移链 | RULE-order-status-transition（**ai-draft，未经人工核准**） | `OrderStatus.java:3-9`（5 状态） | `db/init.sql:29` 列注释 | — | 一致 | `CREATED→SHIPPED` 将跳过 `PAID` |
> | 支付入口不存在 | EVENT-order-paid 文档（Q-M10） | `markPaid` 全工程无调用方（`OrderService.java:38-41`）；监听器空体 | — | — | 一致 | 放宽后所有现存订单事实上均可发货 |
> | 无条件更新 | Q-M11 | `OrderMapper.xml:7-9`（无 `WHERE status=` 前置条件、无事务/锁） | DDL 无 CHECK 约束，仅主键 | — | 一致 | 新增竞态窗口 |
> | 测试规格不可执行 | Q-H1 | `OrderServiceTest.java:14-28` 存在，但 `pom.xml` 未声明测试依赖 | — | — | 一致 | 回归门禁缺失 |
> 
> **5. 关系与影响面**：`PAGE-order-manage → ROUTE-web-portal-orders → API-order-ship → MODULE-order-core → TABLE-t_order`；旁路 `EVENT-order-paid`（仅 `markPaid` 触发，发货链路不发事件）。导出（`ExportService` 仅 `RETENTION_DAYS=7` 常量）与账户域在代码上不依赖订单状态。
> **6. 数据模型上下文**：`t_order.status VARCHAR(16) NOT NULL`，取值 5 个（`db/init.sql:29`）；无 CHECK/外键/二级索引；无 INSERT 建单路径（Q-M4）。**无 schema 变更需求**。
> **7. 配置上下文**：发货状态规则无配置键承载（无 Feature Flag 机制），判定**无直接配置关系**，按门禁停止配置方向，未读取外部快照。
> …（完整回答：`transcripts/S5-A.log`）

| 检查项 | 无 KB | 有 KB |
|--------|-------|-------|
| 结论：不可直接上线 | ✅ 通过 | ✅ 通过 |
| 指出 CREATED 未满足已支付前提 | ✅ 通过 | ✅ 通过 |
| 要求业务批准/流程重设计而非仅改代码 | ✅ 通过 | ✅ 通过 |

**证据密度**：引用不同文件 无 KB 7 个/有 KB 8 个；行号定位 无 KB 0 处/有 KB 11 处
**本案例投入**：耗时 1m46s → 2m54s（增加 1m08s（64% ↑））；费用 未提供 → 未提供（数据不足）

#### S5-B 评审：零业务侵入的全景 API 提案

**用户实际问了什么**：

> 评审一项「零业务侵入」的用户全景 API 提案：直接用 user_id 拼接用户、账户和订单查询结果，宣称现有接口足以保证每人只有一个账户、不会缺失记录，因此无需补充约束或验证。请逐项判断哪些承诺有证据，哪些没有，并给出上线门禁。

**无 KB 实际回答**（耗时 1m59s，tokens —，费用 未提供）：

> 证据收集完毕。以下是逐项评审结论。
> 
> ---
> 
> ## 评审结论：三项核心承诺均无代码证据，且“零业务侵入”前提本身不成立
> 
> ### 承诺逐项判定
> 
> | # | 提案承诺 | 判定 | 证据 |
> |---|---------|------|------|
> | 0 | “现有接口足以用 user_id 拼接三方结果” | ❌ **不成立** | 用户、账户链路存在：`UserBasicController` `GET /api/user/basic/{userId}`、`AccountController` `GET /api/account/{userId}`。但 **order-service 不存在任何按 user_id 查询的接口**：`OrderMapper.xml` 仅有 `selectById(orderId)`/`updateStatus`，`OrderController` 仅有 `POST /{orderId}/ship`，`ExportController` 仅有导出。订单链路必须新建接口——与“零业务侵入”直接矛盾 |
> | 1 | “现有接口保证每人只有一个账户” | ❌ **无证据** | ① `db/init.sql:21` 唯一键是 `uk_account_no(account_no)`，**user_id 上没有任何唯一约束**；② `AccountService.queryAccount` 返回单个实体，MyBatis 语义是“多于一行抛 `TooManyResultsException`”——这是**假设唯一并在违约时崩溃**，不是保证唯一；③ 账户有 `NORMAL/FROZEN/CLOSED` 三态但代码库中无任何账户生命周期/重开逻辑防重；④ `ReconcileJob` 虽有启用证据（`@Scheduled` + `reconcile.enabled=true`），但实现为空壳（“实现省略”），无证据校验 1:1 覆盖 |
> | 2 | “不会缺失记录” | ❌ **无证据** | ① 三表分属 `demo_user`/`demo_account`/`demo_order` 三个库，**跨库无外键可能**，无任何机制保证用户必有账户行——无账户时 `queryAccount` 返回 `null`，聚合层直接 NPE/空字段透出；② **账户接口存在隐性字段丢失缺陷**：`AccountMapper.xml` 用 `SELECT *` + resultType、无别名无 resultMap（注释自认“依赖隐式约定”），且三个服务 `application.yml` 均未开 `map-underscore-to-camel-case`，`user_id`/`account_no` 映射不到 `userId`/`accountNo`，**记录存在但关键字段恒为 null**；③ 订单经 RabbitMQ 异步流转（`order.paid`），无读时一致性承诺；④ 唯一测试 `OrderServiceTest` 只覆盖发货状态机，无任何覆盖聚合/缺失场景的测试 |
> | 3 | “无需补充约束或验证” | ❌ 不成立 | 由 #1、#2 推出：唯一性无约束支撑、完整性无对账支撑，二者恰是最需补充的部分 |
> 
> 另注（顺带发现，非本提案焦点）：`account-service/application.yml` 明文含生产库口令与内网 IP；README 自认过时。文档级承诺一律不采信，以上判定均以代码与 DDL 为准。
> 
> ### 上线门禁（G1–G7，全部通过方可上线）
> …（完整回答：`transcripts/S5-B.log`）

**有 KB 实际回答**（耗时 3m8s，tokens —，费用 未提供）：

> 证据收集完成，四条路径均已闭合。以下先给出任务上下文包（十三节），再给出评审结论与上线门禁。
> 
> ---
> 
> ## 一、任务上下文包
> 
> **1. 任务识别**：评审「零业务侵入用户全景 API」提案——用 `user_id` 直接拼接用户/账户/订单查询结果，声称现有接口保证「一人一账户、不缺记录、无需补充约束或验证」。
> **2. 任务理解**：主画像 Review，辅助 Design。需逐项判定提案承诺的证据成立性，并输出上线门禁。
> **3. 核心实体**：`API-user-basic`、`API-account-query`、`API-order-ship`、`API-order-export`、`CAP-user-full-info`（proposed）、`TABLE-t_user`、`TABLE-t_user_account`、`TABLE-t_order`、`JOIN_KEY: userId`（Q-M9）。
> **4. 四类证据矩阵**（关键行，状态为八枚举之一）：
> 
> | 结论 | KnowledgeBase | 当前代码 | DDL/数据模型 | 配置 | 状态 |
> |------|---------------|----------|--------------|------|------|
> | 不存在按 user_id 查订单的接口/SQL | `interfaces/README.md` 对内 5 项无订单查询 | `OrderMapper.xml` 仅 `selectById(orderId)`/`updateStatus`；Controller 仅 ship/export | `TABLE-t_order` §6-7 读写服务无按用户查询 | order-service `application.yml` 无 `spring.datasource.*`（Q-M6） | 一致（不存在） |
> | `user_id` 无唯一约束 | `TABLE-t_user_account` §4 | `AccountMapper.xml` 单对象返回 | `db/init.sql:16-21` 仅 PK(id)+`uk_account_no` | 无直接关系 | 一致（无约束） |
> | 跨库无外键，仅注释同源 | Q-M5 | 各 Entity 无关联注解 | `db/init.sql` 无 `FOREIGN KEY` | 无直接关系 | 待确认（Q-M5） |
> | 账户响应依赖隐式驼峰映射 | Q-M3 | `AccountMapper.xml:4-7` `SELECT *` 无 resultMap | `AccountEntity.java:3-12` | account `application.yml` 无 mybatis 映射项（HEAD 已复核） | 一致（映射风险成立） |
> | user 侧 JOIN_KEY 闭环 | `CAP-user-full-info` §7 | `UserMapper.xml:4-7` 显式 `AS` | `t_user.user_id` PK | 无直接关系 | 一致 |
> …（完整回答：`transcripts/S5-B.log`）

| 检查项 | 无 KB | 有 KB |
|--------|-------|-------|
| 指出「每人一个账户」的承诺无证据 | ✅ 通过 | ✅ 通过 |
| 指出「不会缺失记录」的承诺无证据 | ✅ 通过 | ✅ 通过 |
| 给出上线门禁项 | ✅ 通过 | ✅ 通过 |

**证据密度**：引用不同文件 无 KB 5 个/有 KB 13 个；行号定位 无 KB 2 处/有 KB 14 处
**本案例投入**：耗时 1m59s → 3m8s（增加 1m09s（58% ↑））；费用 未提供 → 未提供（数据不足）

## 三、结论

- 运行案例：7 个（5 场景）
- 机械判据质量：有 KB 提升 **0** 个；持平 **7** 个；退化 **0** 个（通过率 无 KB 25/25 → 有 KB 25/25）
- 证据密度：引用不同文件 无 KB 57 → 有 KB 79；行号定位 无 KB 28 → 有 KB 95

**解读**（本轮实测，非通用结论）：

1. **质量持平的成因**：本 fixture 仅 5 个服务/4 张表，裸代码 1-2 分钟即可 grep 完，无 KB 端已把检查项全部答对——机械判据达到上限，区分不出两臂。
2. **可观测的真实差异是证据纪律**：有 KB 回答平均引用文件数为无 KB 的 1.4 倍、行号定位 3.4 倍，且每条结论带四类证据交叉核验（知识库/当前代码/数据模型/配置）与开放问题编号（如 Q-M9 关联待确认），可直接追溯。
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

**规模放大未改变质量结论**：两批机械判据均满分，说明无 KB 端在本题集上不存在「找不到/漏掉」；规模增大只体现为耗时代价放大。
