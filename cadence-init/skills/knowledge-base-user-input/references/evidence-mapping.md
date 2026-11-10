# 证据映射

本文件给出 9 个输入文件各自的只读证据探测方法。通用要求：

- 每条结论保留 `文件:行号`；行号对应当前 HEAD。
- 找不到证据时写 `【待确认】` 并说明缺口，不推测补写。
- 只读：禁止执行迁移、部署、发布、启动脚本；禁止连接数据库或配置中心。
- 大范围关系用 CodeGraph，精确结构用 `ast-grep outline`，两者不可用时用有边界的文本检索。

## 工程信息 → `project-scope.md`

| 探测目标 | 判据 |
| --- | --- |
| 候选工程 | 递归查找 `pom.xml`、`build.gradle`、`build.gradle.kts`、`settings.gradle`、`settings.gradle.kts`、`package.json`（排除 `node_modules`、`target`、`dist`、`build`、`.git`） |
| Java 后端 | 构建文件存在且同级存在 `src/main/java` 或 `src/main/kotlin` |
| Vue/React 前端 | `package.json` 存在，且 `dependencies`/`devDependencies` 含 `vue`、`react`、`vue-router`、`react-router`、`@vue/cli`、`vite` 等 |
| 配置工程 | 构建文件存在但无 `src/main` 源码目录，或工程名含 `config`/`configuration` |
| 测试工程 | 路径含 `test`/`tests` 且无 `src/main` |
| 已下线工程 | README、构建配置或注释中出现 `下线`、`已废弃`、`deprecated`、`archived` 标记；不得仅凭名称排除 |
| Git 仓库 | 子目录内含 `.git` → 独立仓库，否则归属父仓库 |
| 本地路径 | 相对项目根的路径，必须存在且可读 |

工程标识使用稳定、可读的短名（如 `order-service`），并在备注中说明纳入/排除理由。排除的工程也要登记并标注 `纳入分析: 否`，避免下游误判范围。服务监听端口写入备注作为服务标识（不含主机部分）；带主机部分的地址不写入。

## 数据模型 → `data-model-scope.md`

结构证据按以下顺序探测，命中任意一种即可登记：

| 证据类型 | 判据 |
| --- | --- |
| DDL | `*.sql` 中的建表语句（`CREATE TABLE`） |
| 数据库迁移文件 | `src/main/resources/db/migration/**`、`db/migration/**`、`liquibase/**` 下的迁移脚本 |
| Entity | `*Entity.java` 或含 `@Entity`、`@Table` 注解的类 |
| Mapper 接口 | `*Mapper.java`、`*Dao.java` 或含 `@Mapper` 注解的接口 |
| Mapper XML | `*Mapper.xml`、`resources/mapper/*.xml` |
| 普通 SQL | 资源目录中的查询 SQL 文件 |
| 人工资料 | 用户提供的结构说明文档 |

其他规则：

- 数据库与 Schema：从 `application*.yml`/`application*.properties` 的 `spring.datasource.url` 提取库名与 Schema 线索，只写库名与 Schema，完整连接串与口令一律不写。
- 分库分表：检索 `sharding`、`ShardingSphere`、`分库分表`、`ds0`/`ds1` 等线索，命中即登记并标 `【待确认】`。
- 结构来源冲突（同一表在不同文件定义不一致）不在草稿阶段裁决，登记到确认清单交用户判断。
- 一个可定位结构证据都没有时，数据模型状态为 `不适用`，原因写“未发现可定位结构证据，请确认或补充”。

## 配置 → `configuration-scope.md`

| 探测目标 | 判据 |
| --- | --- |
| 配置目录 | `src/main/resources/**/application*.yml|yaml|properties`、`config/**`、`*.conf` |
| 纳入文件数量 | 上述范围内按默认排除规则（`.idea`、`.gitkeep`、空文件、历史备份）计数 |
| 文件规则摘要 | 默认排除项、Mapper XML 归入数据模型证据、部署/启动脚本仅作加载链路证据 |
| 服务摘要 | 按工程标识列出配置所在服务 |

锁定依据是用户权威项：本地工作目录不是不可变快照，因此状态默认 `不适用`，原因写明该限制并记录上述证据。用户给出固定提交、标签或导出快照目录后，才可改为 `全量` 或 `指定` 并补齐快照标识、环境、发布批次、外部目录、锁定依据、范围摘要、纳入文件数量或清单摘要、服务摘要、文件规则摘要。

快照指纹由 `knowledge-base-bootstrap` 在分析前后计算，草稿不预填指纹值。

## 中间件 → `middleware-scope.md`

| 中间件 | 依赖或配置线索 |
| --- | --- |
| Redis | `spring-boot-starter-data-redis`、`jedis`、`redisson`、`spring.redis`、`spring.data.redis` |
| Kafka | `spring-kafka`、`kafka-clients`、`spring.kafka`、`bootstrap.servers` |
| RabbitMQ | `spring-boot-starter-amqp`、`amqp-client`、`spring.rabbitmq` |
| RocketMQ | `rocketmq`、`rocketmq-spring-boot-starter` |
| Elasticsearch | `elasticsearch`、`spring-boot-starter-data-elasticsearch` |
| 数据库 | `mysql-connector-j`、`postgresql`、`ojdbc`、`spring.datasource` |
| 对象存储 | `minio`、`aws-java-sdk-s3`、`aliyun-sdk-oss` |
| FTP/SFTP | `commons-net`、`jsch`、`sftp` |
| 配置中心 | `nacos`、`apollo`、`spring-cloud-config` |
| 调度平台 | `quartz`、`xxl-job`、`elastic-job` |

只登记有可定位证据的条目。版本、环境、生产者、消费者、Topic/Queue/Key 未知时留空并在备注说明未知项。中间件判为 `不适用` 时不生成任何中间件条目。

## 接口 → `api-scope.md`

| 能力类型 | 探测目标 |
| --- | --- |
| REST API | `@RestController`、`@Controller` 类，及其 `@RequestMapping`、`@GetMapping`、`@PostMapping`、`@PutMapping`、`@DeleteMapping`、`@PatchMapping` 方法 |
| RPC Provider | `@DubboService`、`@DubboServiceReference`、`@GrpcService`、Feign 服务端声明 |
| RPC Consumer | `@FeignClient`、`@DubboReference` |
| 消息生产 | `kafkaTemplate.send`、`rabbitTemplate.convertAndSend`、`rocketMQTemplate` 等发送调用 |
| 消息消费 | `@KafkaListener`、`@RabbitListener`、`@RocketMQMessageListener`、`@JmsListener` |
| Redis 队列 | Redis Stream、`@StreamListener`、`@RedisKeyValue` 轮询消费 |
| 文件交换 | 上传下载接口、对象存储读写、FTP/SFTP 读写方法 |
| 定时任务 | `@Scheduled`、`xxl-job` 任务类、`Quartz` Job |
| 批处理 | 批量导入导出入口、批处理任务入口 |

规则：

- 清单必须列全探测到的入口。契约规定未登记的能力归入对内能力，漏登记会改变对外/对内分类结果。
- 需求或规划文档（`docs/issue-*.md`、PRD、设计稿）描述但代码中尚未实现的能力不计入已实现清单，只在清单后的说明段落登记为规划项，并标注待用户裁决。
- 标识用 `API-<业务名>`，同一控制器多个方法按业务能力拆分，不按方法数堆行。
- 状态列写 `待确认`；调用方未知留空；落地方写工程标识。
- 在文件中提示用户逐项裁决对外属性，未裁决项在 bootstrap 阶段按对内能力处理。

## 页面 → `page-scope.md`

| 探测目标 | 判据 |
| --- | --- |
| 前端应用 | `package.json` 所在目录，技术栈取 `vue`/`react` 等依赖 |
| 路由定义 | vue-router：`createRouter`、`routes:` 数组、`src/router/**`；react-router：`<Route path=`、`createBrowserRouter` |
| 菜单 | `src/layout/**/menu*`、`mock/menu*`、`permission*`、`asyncRoutes`、`constantRoutes` |
| 页面组件 | `src/views/**`、`src/pages/**` |

页面标识用 `PAGE-<业务名>`，路由或菜单列写实际路径。权限说明未知时留空并标 `【待确认】`。项目无前端工程时页面状态为 `不适用`，不生成 `page-scope.md`。前端存在但未引入路由库时，登记单页应用并写明未发现路由定义，路由列标 `【待确认】`，不虚构路由。

## DDL → `database-ddl.sql`

只复制单一权威 DDL 文件内容（如 `db/init.sql`、`schema.sql`、`db/schema/*.sql`），复制前做敏感信息检查。多个候选 DDL 且内容冲突时，不合并、不裁决，登记到确认清单。找不到权威 DDL 时只写一行说明，结构证据指向 `data-model-scope.md`。

## 产品信息 → `product.md`

来源顺序：用户提供的 PRD 或产品文档 → README 标题与简介 → 前端应用的 `package.json` 描述。来源不可靠时四节写 `未提供（待用户补充）`。引用 README 表述时在节末标注来源文件位置。

## 业务知识证据（`base-info.md` 可选章节）

| 键 | 判据 |
| --- | --- |
| `test_sources` | 存在 `src/test/**` 的工程目录清单；为空时留空数组 |
| `adr_sources` | 存在 `docs/adr/**`、`adr/**`、`docs/decisions/**` 时登记；否则留空数组 |
| `git_history` | 默认 `enabled: false`；启用时 `range` 必须本地可解析，填写 `起点提交..结束提交` |

三个键全缺省时初始化正常继续，不产生待确认项。
