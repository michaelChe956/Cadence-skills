# Java B/S 项目基础分析指南

## 目录

- 仓库与模块信号
- Java 分析重点
- 前端分析重点
- DDL 分析重点
- 配置与中间件
- 横切关注点
- 常见误判

## 仓库与模块信号

| 信号 | 可能含义 | 需要继续确认 |
|------|----------|--------------|
| 根 `pom.xml` 含 `<modules>` | Maven 多模块 | 子模块是否独立服务 |
| 多个启动类 | 多服务或测试入口 | 是否在生产构建中启用 |
| `settings.gradle` | Gradle 多项目 | include 与目录映射 |
| 多个 `package.json` | 多前端或 Monorepo | workspace 和部署单元 |
| Gateway 配置 | 可能存在外部路由 | 实际 Profile 与部署配置 |

## Java 分析重点

### 启动与装配

- `@SpringBootApplication` 的扫描范围
- `@EnableConfigurationProperties`
- `@Conditional*` 条件
- AutoConfiguration 和 SPI
- Profile、Feature Flag 和外部配置

### 数据访问

- JPA Entity、Repository 和命名查询
- MyBatis Mapper、XML 和动态 SQL
- MyBatis-Plus Wrapper 和逻辑删除
- JDBC Template 和手写 SQL
- Flyway、Liquibase 和自定义迁移

### 隐式调用

- AOP 切面
- 事件监听器
- 反射、SPI、动态代理
- Spring Bean 名称查找
- 注解驱动的消息、缓存、事务和调度

## 前端分析重点

- 锁文件用于确认实际依赖版本
- 构建配置用于确认别名、代理和环境变量
- 路由与菜单可能分别来自代码和后端
- 请求封装可能统一注入 Token、租户和错误处理
- 状态管理可能控制权限、Feature Flag 和动态路由

## DDL 分析重点

按数据库方言识别：

- 标识符大小写与引用方式
- 自增、序列或触发器生成 ID
- 索引类型、分区和表空间
- 字段注释与表注释
- 视图、函数、过程和触发器依赖

跨文件 DDL 必须先确定执行顺序和所属 Schema。分库分表需要区分逻辑表与物理表，不重复把每个物理分片当成独立业务实体。

## 配置与中间件

配置值的存在不等于生效。结合以下证据判断：

1. Profile 或配置中心加载范围
2. Bean 条件装配
3. 调用、Listener、Producer 或客户端创建
4. 网关、部署或运行资料

## 横切关注点

重点寻找：

- Spring Security Chain、权限注解和自定义鉴权
- `@Transactional`、事务管理器和事件边界
- `@Cacheable`、RedisTemplate 和本地缓存
- Resilience4j、Sentinel、Hystrix 或自定义重试
- 全局异常处理和错误码枚举
- 日志 Trace ID、Micrometer、OpenTelemetry 或 SkyWalking

## 常见误判

- 依赖存在即认定实际使用
- Controller 存在即认定外部暴露
- 同名字段即认定外键关系
- 开发配置即认定生产配置
- 测试启动类即认定生产服务
- Entity 结构即认定数据库实际结构
- README 中的旧版本说明即认定当前版本

