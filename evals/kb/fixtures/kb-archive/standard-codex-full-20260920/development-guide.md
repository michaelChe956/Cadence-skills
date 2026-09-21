# 项目开发与验证指南

## 文档元数据

- 适用分支：master
- 基线提交：1f867b9fcdf95f2e11808454898f333d7d512e90
- 已确认环境：本地开发（配置快照 `baseline-config-v1`，fixture 本地快照，环境名“开发”）
- 未确认环境：测试、预发、生产（未提供任何环境配置或部署资料）

## 1. 工具版本

| 工具 | 版本 | 来源 |
|------|------|------|
| JDK | 17（`java.version`） | `user-service/pom.xml:12`、`account-service/pom.xml:12`、`order-service/pom.xml:12` |
| Maven | 未声明（未发现 `mvnw`/`.mvn`，按系统 Maven 使用） | 三个 `pom.xml`；工程内无 wrapper |
| Spring Boot | 3.2.5（parent） | 三个 `pom.xml:4-8` |
| Node.js / npm | 未声明（无 `.nvmrc`、`engines`、锁文件） | `web-portal/package.json:1-6` |
| Vite | 声明 `^5.2.0` | `web-portal/package.json:6` |

## 2. 模块构建顺序

1. `user-service`、`account-service`、`order-service` 为三个相互独立的 Maven 工程（各自 `pom.xml`，无聚合根 `pom.xml`），无强制构建顺序。
2. `web-portal` 为独立 npm 工程，与后端无构建依赖。
3. 未发现聚合模块、私有仓库或版本联动机制。

## 3. 本地依赖

| 依赖 | 用途 | 必需性 | 来源 |
|------|------|--------|------|
| MySQL（三库 demo_user / demo_account / demo_order） | 后端数据存储 | 启动后端必需 | `db/init.sql`、各 `application.yml` 数据源键 |
| RabbitMQ（`order.exchange` / `order.paid` / `order.paid.queue`） | order-service 事件收发 | order-service 消息链路必需 | `order-service/pom.xml:17`、`order-service/src/main/java/com/demo/order/mq/**` |
| Node.js 运行环境 | 前端开发与构建 | 构建前端必需 | `web-portal/package.json` |

本地连接的地址、账号与口令均属于敏感值，本指南不记录实际值；实际取值见授权快照（只读）与各服务配置文档的脱敏清单。

## 4. 配置与 Profile

### 当前开发与测试配置基线

| 环境 | Profile | 快照标识 | 发布批次 | 最终快照指纹 | 范围摘要 | 适用服务 | 状态 |
|------|---------|----------|----------|--------------|----------|----------|------|
| 开发（fixture 本地快照） | 未声明（Spring Boot 默认 default） | baseline-config-v1 | fixture-batch-001 | 92bb968da5721d10403cbe72a128a492ea6c5fa2220788b736f9adab743aa71b | 三服务 application.yml 全量纳入（3 文件） | user-service、account-service、order-service | 已核实（首次计算 == 结束计算 == Manifest 授权指纹） |

### 允许读取的配置来源

| 来源 | 授权范围 | 读取方式 | 允许用途 | 禁止操作 | 证据 |
|------|----------|----------|----------|----------|------|
| 外部不可变快照 `/home/tester/work/snapshots/baseline-config` | `baseline-config-v1`，3 个 `application.yml` 文件 | 只读 | 配置键分析与脱敏记录 | 复制进 KnowledgeBase、写入/重命名/删除/格式化、跟随符号链接越界 | `manifest.yaml` `evidence.configuration_snapshots.baseline` |
| 工程内 `*/src/main/resources/application.yml` | 三后端服务 | 只读 | 与快照交叉核对（本次核对结果：内容一致） | 作为生产配置事实 | 各服务 `application.yml` |

外部配置快照只读且不得复制进 KnowledgeBase。不得连接配置中心或远程环境补取配置，不得写入、重命名、删除或格式化原始快照。

### 安全验证配置变更

| 变更场景 | 安全验证方式 | 工作目录或工具 | 前置条件 | 禁止事项 | 来源 |
|----------|--------------|----------------|----------|----------|------|
| 修改后端配置键 | 静态比对配置文件与文档键清单（键数、键名、脱敏值） | 仓库根，只读文本检索 | 无（离线） | 连接数据库/配置中心、执行启动脚本 | 本 Skill 配置分析规则 |
| 修改数据源相关配置键 | 核对配置与该服务 Mapper 使用的库/Schema 是否一致 | 仓库根，只读阅读 | 无（离线） | 直接连库验证连通性 | `application.yml`、各 `*Mapper.xml` |
| 修改 RabbitMQ 相关配置键 | 核对配置键与代码中 exchange/queue/routing key 常量是否一致 | 仓库根，只读阅读 | 无（离线） | 向真实 MQ 发送消息 | `order-service/src/main/java/com/demo/order/mq/**` |

只记录离线、静态可验证的方式；本指南不提供部署、发布或启动脚本，也不要求执行它们。

## 5. 后端构建和启动

- 构建（三个服务各自执行）：`mvn -f user-service/pom.xml package`、`mvn -f account-service/pom.xml package`、`mvn -f order-service/pom.xml package` [来源：各 `pom.xml`]。
- 启动：未发现 `spring-boot-maven-plugin` 声明、启动脚本或部署描述，启动命令待确认（不可从现有资料确认为 `mvn spring-boot:run` 或 `java -jar`）。
- 依赖解析需要访问外部 Maven 仓库；本次分析为只读离线，未执行任何构建。

## 6. 前端构建和启动

- 安装依赖：`npm install`（工作目录 `web-portal`）[来源：`web-portal/package.json:4-6`；未声明锁文件，解析版本待确认]。
- 开发服务器：`npm run dev`；生产构建：`npm run build`（工作目录 `web-portal`）[来源：`web-portal/package.json:4`]。
- 开发服务器对 `/api` 前缀配置了代理，目标为内部端点（值 `<redacted>`）；该配置不在授权配置范围内，仅作为前端联调证据（见 `open-questions.md` Q-L4）。

## 7. 测试与静态检查

| 场景 | 命令 | 工作目录 | 前置条件 | 来源 |
|------|------|----------|----------|------|
| order-service 状态机规格测试 | `mvn -f order-service/pom.xml test` | 仓库根 | 需先补充测试依赖（Q-H1）；依赖可联网解析 | `order-service/src/test/java/com/demo/order/OrderServiceTest.java:8` |
| user-service / account-service 测试 | 未发现测试源码与测试依赖 | - | - | 两个工程无 `src/test` |
| 前端测试与 lint | 未发现脚本或配置 | - | - | `web-portal/package.json:1-6` |

未发现 CI 配置、静态检查插件或代码格式化配置。

## 8. 数据库迁移

- 未发现 Flyway、Liquibase 或自定义迁移代码/脚本；`evidence.data_model_sources.migrations` 为空列表。
- 结构证据来自 `db/init.sql`（DDL，包含 demo_user / demo_account / demo_order 三库共 4 张表）与三个 Mapper XML。
- 该 DDL 的执行顺序在单文件内由 `CREATE DATABASE` / `USE` 语句显式给出 [代码证据]；但未发现其被自动执行的证据，实际执行方式待确认。
- 禁止执行任何迁移脚本（本次分析未执行）。

## 9. 常见修改场景验证

| 场景 | 验证方式 | 证据链路 |
|------|----------|----------|
| 新增/修改用户基本信息字段 | 同步检查 DDL、`UserMapper.xml` 显式 `AS` 映射、`UserEntity` 字段与 `data-models/DB-demo_user/TABLE-t_user.md` | `db/init.sql:3-11`、`user-service/src/main/resources/mapper/UserMapper.xml:5` |
| 修改订单状态机 | 同步检查 `OrderStatus`、`OrderService` 约束与 `OrderServiceTest` 规格 | `order-service/src/main/java/com/demo/order/service/OrderService.java:21-41`、`entity/OrderStatus.java`、`src/test/java/com/demo/order/OrderServiceTest.java` |
| 修改订单导出保留期 | 同步检查 `ExportService.RETENTION_DAYS` 与 `t_export_file` 表注释 | `order-service/src/main/java/com/demo/order/service/ExportService.java:9-10`、`db/init.sql:22-28` |
| 调整对账任务 | 同步检查 `@Scheduled` cron、`reconcile.*` 配置键与绑定代码（当前缺绑定） | `account-service/src/main/java/com/demo/account/job/ReconcileJob.java:11-17`、`account-service/src/main/resources/application.yml:10-12` |

## 10. 禁止直接执行的脚本

| 脚本或类型 | 证据位置 | 仅允许用途 | 禁止原因 | 安全替代方式 |
|------------|----------|------------|----------|--------------|
| 数据库初始化 DDL | `db/init.sql` | 作为结构与业务规则只读证据 | 会创建/变更数据库对象 | 静态阅读 DDL 并比对字段级文档 |
| 应用启动（`spring-boot` 启动类） | 三个 `*Application.java` | 作为入口识别证据 | 会连接真实数据源与消息中间件 | 静态阅读装配与配置键 |
| 未发现的部署/发布脚本 | 工程内未发现 | - | 不存在可比对内容 | 不适用 |

## 11. 待确认项

- Q-H1：order-service 测试依赖未声明，测试命令无法确认。
- Q-L3：构建与测试命令均未在本次只读离线分析中执行验证。
- Q-L4：前端代理目标与后端端口映射未确认（代理目标已脱敏）。
- 其余项见 `open-questions.md`（blocking 0、high 1、medium 6、low 5）。
