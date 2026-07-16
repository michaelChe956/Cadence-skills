# 中间件分析范围

## 范围规则

- 填写本次需要分析的中间件及其已知用途。
- 未知版本、环境或调用方可以留空，不得猜测。
- 不得填写密码、Token、完整连接串或生产凭证。

## 中间件清单

| 标识 | 名称 | 类型 | 版本 | 业务用途 | 生产者 | 消费者 | Topic/Queue/Key | 环境 | 状态 | 备注 |
|------|------|------|------|----------|--------|--------|-----------------|------|------|------|
| MIDDLEWARE-example-cache | 示例缓存 | Redis |  | 缓存示例数据 | example-service | example-service | example:* | 测试 | 使用中 |  |

## 类型参考

- Redis
- Kafka
- RabbitMQ
- RocketMQ
- 数据库
- Elasticsearch
- 对象存储
- FTP/SFTP
- 配置中心
- 调度平台
