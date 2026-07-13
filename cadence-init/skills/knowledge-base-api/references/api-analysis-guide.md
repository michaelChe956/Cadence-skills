# API 与集成能力分析指南

## 目录

- REST 入口
- 外部暴露判断
- 服务间调用
- 消息与任务
- 语义字段
- 常见误判

## REST 入口

常见入口包括：

- `@RestController`、`@Controller`
- `@RequestMapping`、`@GetMapping`、`@PostMapping` 等
- WebFlux RouterFunction
- 项目自定义组合注解
- 网关和 BFF 层转发

完整路径需要组合类路径、方法路径、Context Path、网关前缀和重写规则。

## 外部暴露判断

按证据强度判断：

1. API 文档明确标注对外，并有网关或部署证据
2. 网关路由指向接口且安全策略允许外部访问
3. 用户明确说明合作方或公网调用
4. 只有 Controller：不能证明对外

鉴权白名单不等于公网暴露，仍需结合部署边界。

## 服务间调用

### Feign

记录服务名、路径、Fallback、超时和调用位置。接口类没有调用引用时标记已声明。

### Dubbo

记录接口、Provider/Consumer、版本、分组、协议、超时、重试和注册中心。接口定义不能证明 Provider 已发布。

### 自定义客户端

识别 RestTemplate、WebClient、OkHttp、Apache HttpClient 和封装客户端，结合基础地址配置与调用代码判断目标系统。

## 消息与任务

### 消息

- Kafka：Topic、Group、Partition Key、事务和重试
- RabbitMQ：Exchange、Queue、Binding、Routing Key、ACK 和 DLQ
- RocketMQ：Topic、Tag、Group、顺序和延迟消息
- Redis：Channel、Stream、Group、List 和阻塞消费

### 任务

- `@Scheduled`
- Quartz Job
- XXL-JOB Handler
- Spring Batch Job
- 自定义任务注册中心

Cron 配置可能来自外部配置中心，不要仅记录注解默认值。

## 语义字段

每项能力至少回答：

- 谁调用或触发？
- 通过什么协议？
- 输入和输出是什么？
- 是否需要鉴权？
- 修改哪些数据或状态？
- 失败、重试和幂等如何处理？
- 哪个环境或条件下启用？
- 证据在哪里？

## 常见误判

- Controller 等于对外 API
- Feign 接口等于 Provider
- Topic 配置等于存在 Producer 和 Consumer
- Cron 注解等于所有环境启用
- API 文档等于当前实现
- 方法返回类型等于最终响应结构，忽略统一包装和异常处理
- 测试 Mock Server 等于外部依赖

