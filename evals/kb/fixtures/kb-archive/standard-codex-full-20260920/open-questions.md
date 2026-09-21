# KnowledgeBase 待确认事项

## 元数据

| 项目 | 内容 |
|------|------|
| 证据基线 | 1f867b9fcdf95f2e11808454898f333d7d512e90（分支 master） |
| 最后更新 | 2026-09-20（base-info 建立；api 追加 Q-H2、Q-M7～Q-M11；pages 追加 Q-H3、Q-M12、Q-L6～Q-L8；overview 追加 Q-M13、Q-L9 并将 Q-L5 转入已解决） |
| 状态取值 | `未解决`、`已解决`；已解决条目不计入四级计数 |

## 计数摘要

| 级别 | 数量 | Manifest 字段 |
|------|------|---------------|
| 阻断 | 0 | `open_questions.blocking` |
| 高 | 3 | `open_questions.high` |
| 中 | 13 | `open_questions.medium` |
| 低 | 8 | `open_questions.low` |

计数只统计下列未解决条目，并与 `manifest.yaml` 同批写入。

## 阻断

| ID | 问题 | 影响 | 证据 | 建议资料或确认方式 | 状态 |
|----|------|------|------|--------------------|------|
| - | 无未解决条目 | - | - | - | - |

## 高优先级

| ID | 问题 | 影响 | 证据 | 建议资料或确认方式 | 状态 |
|----|------|------|------|--------------------|------|
| Q-H1 | order-service 测试源码使用 JUnit 5，但三个 `pom.xml` 均未声明测试依赖（无 `spring-boot-starter-test` 或 JUnit 依赖） | `mvn test` 可能无法编译测试；状态机行为规格无法作为可执行验证 | `order-service/src/test/java/com/demo/order/OrderServiceTest.java:8`；`order-service/pom.xml:13-18` | 由开发方补充测试依赖声明，或提供可执行的验证命令与运行记录 | 未解决 |
| Q-H2 | 用户对外清单声明 `API-order-export` 状态为“使用中”，但代码只有存根：`ExportController#export` 无入参、未调用 `ExportService`、返回字面量 `taskId`；无文件生成、无 `t_export_file` 登记、无结果查询方式 | 对外能力无法完成端到端链路核实；对外契约（入参、结果、文件交付）缺失，调用方无法获知导出结果 | `user-input/api-scope.md:13`；`order-service/src/main/java/com/demo/order/controller/ExportController.java:36-44`；`service/ExportService.java:5-11`；`db/init.sql:35-40` | 由用户确认导出契约与实现范围，或按 `knowledge-base-update` 变更包更新对外清单与知识库 | 未解决 |
| Q-H3 | `web-portal` 仓库内（含 git 跟踪文件）未发现 Vite 入口 `index.html`，而 `main.js:16` 执行 `mount('#app')`；构建与部署入口无法确认 | 前端应用可能无法构建/启动，三个页面的运行时可达性无法证明 | `web-portal/package.json:4`、`web-portal/src/main.js:16`；全仓未发现 `index.html` | 由前端负责人提供入口文件或部署方式说明 | 未解决 |

## 中优先级

| ID | 问题 | 影响 | 证据 | 建议资料或确认方式 | 状态 |
|----|------|------|------|--------------------|------|
| Q-M1 | account-service 未见 `@EnableScheduling` 或等效启用证据 | `@Scheduled` 对账任务可能未注册执行 | `account-service/src/main/java/com/demo/account/job/ReconcileJob.java:49`；`AccountApplication.java:6-12` | 由开发方确认调度启用方式，或提供运行态任务触发证据 | 未解决 |
| Q-M2 | `reconcile.enabled`、`reconcile.retry-times` 无代码绑定，仅 `ReconcileJob` 类注释声明 | 配置是否生效无法确认；重试行为无实现证据 | `account-service/src/main/resources/application.yml:10-12`；`ReconcileJob.java:48-52` | 由开发方确认配置消费代码归属与实际生效链路 | 未解决 |
| Q-M3 | `AccountMapper.xml` 使用 `SELECT *` 且未维护 `resultMap`，`account_no → accountNo`、`user_id → userId` 依赖隐式驼峰映射，而授权配置中无 mybatis 映射设置 | 账户查询字段可能映射失败或为空 | `account-service/src/main/resources/mapper/AccountMapper.xml:4-7`；`application.yml`（无 mybatis 配置项） | 提供运行态响应样例或映射配置证据 | 未解决 |
| Q-M4 | `t_export_file` 仅存在 DDL 与 `RETENTION_DAYS` 常量，未发现持久化调用或 Mapper；`t_order` 也未见建单/取消写入路径 | 导出登记与订单生命周期链路不可确认 | `db/init.sql:26-40`；`order-service/src/main/java/com/demo/order/service/ExportService.java:9-10`；`mapper/OrderMapper.xml:7-9` | 由业务方确认订单生命周期与导出登记的实现范围 | 未解决 |
| Q-M5 | 三库 `user_id` 同名与注释同源说明不能证明数据库外键；DDL 未声明任何 `FOREIGN KEY` | 跨库关联只能作为候选关系，不能作为约束事实 | `db/init.sql:5,17,28`；`AccountEntity.java:5-6`；`OrderEntity.java:6-7` | 由 DBA 或数据负责人确认跨库关联约束来源 | 未解决 |
| Q-M6 | 授权配置快照仅覆盖开发环境；order-service 的 `application.yml` 不含 `spring.datasource.*`，但 `pom.xml` 声明 MySQL 驱动且 Mapper 查询 `t_order` | 非开发环境配置与 order-service 数据源来源未知，不能升级为生产事实 | `manifest.yaml`（环境：开发）；`order-service/src/main/resources/application.yml:1-9`；`order-service/pom.xml:16` | 提供 order-service 数据源配置来源与非开发环境配置（脱敏） | 未解决 |
| Q-M7 | `AccountController` 类注释自称“对外能力 API-B”，但用户对外能力清单未登记该能力 | 对外/对内分类冲突：本知识库按用户清单保留为对内能力 `API-account-query`；若确为对外能力需更新清单 | `account-service/src/main/java/com/demo/account/controller/AccountController.java:15`；`user-input/api-scope.md:12-13` | 由用户确认该能力的对外属性；变更时按变更包执行 `knowledge-base-update` | 未解决 |
| Q-M8 | 对外能力与对内 REST 均未发现鉴权实现：三个后端无 Spring Security 等安全依赖、无过滤器、无网关工程，而 `API-user-basic` 响应含姓名/手机号/邮箱，`API-account-query` 响应含账户余额 | 对外能力的暴露面与鉴权要求无法确认；存在敏感数据未受保护暴露的风险 | `user-service/pom.xml:13-17`、`account-service/pom.xml:13-17`、`order-service/pom.xml:13-18`；`UserBasicController.java:26-30`、`AccountController.java:26-30` | 由用户确认鉴权要求与部署层保护措施 | 未解决 |
| Q-M9 | 组合诉求“全部用户信息”的 `JOIN_KEY`（`userId`）端到端映射未闭合：user 侧已确认，account 侧请求条件已确认但响应字段依赖隐式驼峰映射，且跨库同源仅有注释无外键 | 组合能力 `CAP-user-full-info` 的连接键与结果字段完整性不可断言，状态只能为 `proposed` | `user-service/src/main/resources/mapper/UserMapper.xml:4-7`；`account-service/src/main/resources/mapper/AccountMapper.xml:5-7`（Q-M3）；`db/init.sql:5,17`（Q-M5）；`capabilities/CAP-user-full-info.md#7` | 与 Q-M3 同源：提供账户响应字段映射证据后闭合连接键 | 未解决 |
| Q-M10 | `EVENT-order-paid` 生产触发点 `OrderService#markPaid` 在全工程无调用方，也无 REST 入口；消费者 `@RabbitListener` 已装配但方法体为空 | 事件生产链路在当前代码中不可达，事件能力与订单支付场景无法连通 | `order-service/src/main/java/com/demo/order/service/OrderService.java:37-41`；`mq/OrderEventProducer.java:19-21`；`mq/OrderEventListener.java:31-41` | 由开发方确认支付回调入口与支付后处理的预期语义 | 未解决 |
| Q-M11 | `API-order-ship` 读状态与写状态为两次独立操作，未使用 `@Transactional`、无乐观锁或条件更新（`WHERE status='PAID'`） | 并发发货场景下可能重复更新或状态覆盖；异常路径返回框架默认 500 而非业务错误码 | `order-service/src/main/java/com/demo/order/service/OrderService.java:25-35`；`mapper/OrderMapper.xml:7-9` | 由开发方确认并发与事务策略 | 未解决 |
| Q-M12 | 前端无鉴权与导航入口：无登录态/Token、无路由守卫、无权限码，`App.vue` 仅 `router-view`（无菜单与跳转入口），三个页面可直接以 URL 访问，其中“发货/导出”为高影响操作、账户页展示余额 | 页面访问控制边界与生产可达性无法确认；与后端鉴权缺失（Q-M8）叠加后敏感操作暴露面不清楚 | `web-portal/src/main.js:10-16`、`web-portal/src/App.vue:1`、`web-portal/src/views/OrderPage.vue:4-5`、`web-portal/src/views/AccountPage.vue:4` | 由用户确认页面访问控制、菜单来源与生产网关保护 | 未解决 |
| Q-M13 | 组合能力 `CAP-user-full-info` 仅有用户诉求，无聚合端点实现；输出字段清单未收敛（`mobile`、`email`、`balance` 等敏感字段是否允许公开未确认），`identity_mapping`、`tenant_isolation`、`failure_policy` 均未定义 | 组合能力的字段范围、敏感字段暴露面与失败语义无法确认，只能是 `proposed`；“全部用户信息”有被误读为默认涵盖敏感字段的风险 | `user-input/api-scope.md:19-21`；`capabilities/CAP-user-full-info.md#5`、`#6`、`#7`；`interfaces/README.md#能力组合` | 由用户确认组合输出字段清单、允许公开范围与失败策略 | 未解决 |

## 低优先级

| ID | 问题 | 影响 | 证据 | 建议资料或确认方式 | 状态 |
|----|------|------|------|--------------------|------|
| Q-L1 | `web-portal/package.json` 依赖为 caret 范围且无锁文件 | 实际解析版本未知，构建可重复性无法确认 | `web-portal/package.json:5-6`；未发现 `package-lock.json`/`pnpm-lock.yaml` | 提供锁文件或说明依赖固定策略 | 未解决 |
| Q-L2 | 仓库根 `README.md` 自述过时，仅描述 user-service | 误导项目导航；以代码与 Manifest 范围为准 | `README.md:1-5` | 由维护方更新或删除过时说明 | 未解决 |
| Q-L3 | 构建与测试命令未在只读离线分析中执行验证（Maven 依赖需联网解析） | 命令有效性仅有 `pom.xml` 声明证据 | 三个 `pom.xml`；`development-guide.md` 第 5、7 节 | 在联网环境执行验证并记录结果 | 未解决 |
| Q-L4 | 前端开发代理指向单一后端端点（值已脱敏），而三个后端端口不同且未发现网关工程 | 前端到具体服务的路由方式未确认 | `web-portal/vite.config.js:3`；三服务 `server.port` 键 | 提供生产网关或反向代理路径（脱敏） | 未解决 |
| Q-L6 | 关系类型词表（`knowledge-base-base-info` 的 `assets/relation-types.md`）未提供 `PAGE → API`、`ROUTE → PAGE` 枚举，页面-API-路由关系只能写入 `pages/` 文档，追溯矩阵无法直接表达该边 | 矩阵无法直接表达页面调用接口的关系边，关系图不覆盖页面-API 关系 | `knowledge-base-base-info/assets/relation-types.md`；`evidence/traceability-matrix.md`；`pages/PAGE-user-list.md#4` | 经 `knowledge-base-update` 变更包扩展词表后补写关系边 | 未解决 |
| Q-L7 | 三个页面的请求参数均为硬编码 `1`（`queryUserBasic(1)`、`queryAccount(1)`、`shipOrder(1)`），且未使用路由参数，页面只处理单个资源 | 页面是否具备真实运营能力（多用户/多订单/参数化查询）无法确认，疑为示例或调试残留 | `web-portal/src/views/UserList.vue:12`、`AccountPage.vue:12`、`OrderPage.vue:10-11` | 由前端负责人确认页面参数化需求 | 未解决 |
| Q-L8 | `services/README.md:11-12` 的“API 阶段状态/页面阶段状态”行仍写“进行中”，与 Manifest `coverage.initialization.completed_stages`（base-info、api、pages、overview）不一致 | 服务索引与待确认计数和实际状态不一致，可能误导后续导航与验收 | `services/README.md:11-12`；`manifest.yaml` `coverage.initialization.completed_stages` | 由后续阶段或 Update 修正该索引的阶段状态行 | 未解决 |
| Q-L9 | 业务域证据强度不足：规则 `RULE-order-status-transition`、`RULE-account-balance-non-negative`、`RULE-order-export-retention` 与流程 `FLOW-order-export`、`FLOW-order-paid-event`、`FLOW-account-reconcile` 均为 `ai-draft`，缺少用户权威输入、可执行测试或端到端实现证据 | 业务规则与流程不得作为确定语义使用；相关结论仍需人工裁决 | `business/README.md#计数摘要`；`business/rules/`、`business/flows/`；`db/init.sql:19,22,39`；`ExportService.java:9-10` | 由业务方确认规则口径与流程范围，或补充实现与测试证据 | 未解决 |

## 已解决

| ID | 结论 | 解决时间 | 更新文档 | 依据 |
|----|------|----------|----------|------|
| Q-L5 | overview 阶段已把三项业务规则候选登记为规则卡（`RULE-account-balance-non-negative`、`RULE-order-export-retention`、`RULE-order-status-transition`），并在原文档位置追加规则卡链接，原文未删除 | 2026-09-20 | `business/rules/RULE-account-balance-non-negative.md`、`business/rules/RULE-order-export-retention.md`、`business/rules/RULE-order-status-transition.md`、`data-models/DB-demo_account/TABLE-t_user_account.md`、`data-models/DB-demo_order/TABLE-t_order.md`、`interfaces/API-order-export_订单导出_export.md`、`interfaces/FILE-order-export-file_订单导出文件.md` | overview 阶段 business 域产物；规则实现缺口另登记 Q-H2、Q-M4、Q-L9 |
