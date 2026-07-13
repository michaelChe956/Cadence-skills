---
name: knowledge-base-api
description: "Use when 需要从 API 文档和代码盘点 Java 项目的 REST、Feign、Dubbo、消息、Redis 队列、FTP、文件交换、定时任务等能力，并区分对外、对内和服务间接口。"
---

# KnowledgeBase API 能力

## 概述

建立系统能力清单和可追溯调用链，而不只是罗列 Controller。结合 API 文档、网关、鉴权、框架装配和实现代码，明确能力分类、可用状态、调用方、数据副作用和证据可信度。

## 必读资源

- 执行前读取 `references/api-analysis-guide.md`。
- 生成文档时使用 `assets/api-capabilities-template.md`。
- 需要对照综合场景时读取 `references/demo.md`。

## 前置输入

优先读取：

- `cadence/knowledgeBase/manifest.yaml`
- `cadence/knowledgeBase/01-base-information.md`
- `cadence/knowledgeBase/evidence/source-index.md`
- OpenAPI、Swagger、Knife4j 或用户 API 文档
- 网关、鉴权、RPC、消息、文件和任务资料

API 文档缺失时允许从代码生成，但必须标记“代码生成，待人工校对”。

## 强制分类

每项能力必须属于以下类别之一：

1. 对外公开 REST API
2. 合作方或受限外部 REST API
3. 内部前端 REST API
4. 服务间 REST API
5. RPC Provider 或 Consumer
6. 消息生产或消费能力
7. Redis Pub/Sub、Stream 或队列能力
8. FTP、SFTP、对象存储或文件交换
9. 定时任务、批处理或异步作业
10. 状态未知，待人工确认

禁止把“对外 API”和“项目内部存在的 REST 接口”混为一类。

## 工作流程

### 1. 确认 API 资料范围

记录 API 文档版本、环境、维护时间和覆盖服务。文档与代码不一致时分别保留“设计描述”和“当前实现”。

### 2. 扫描 REST 入口

识别：

- Spring MVC、WebFlux 路由
- 类级和方法级路径组合
- HTTP 方法、Consumes、Produces
- 参数绑定、校验和响应模型
- Context Path、Servlet Path 和版本前缀
- 网关路由、重写、StripPrefix 和外部域入口

为 API 生成稳定 ID，例如 `API-order-create`。

### 3. 判断能力状态

分别判断：

- 已声明：存在路由或接口声明
- 已实现：存在具体实现
- 已装配：位于有效扫描、Bean 或配置范围
- 已暴露：通过网关、路由或部署配置可访问
- 条件启用：依赖 Profile、开关或环境
- 已废弃：有废弃标记或替代能力
- 测试专用：仅存在测试或 Mock 范围
- 代码存在但不可达：缺少有效入口
- 状态未知：证据不足

Controller 存在不能单独证明对外暴露。

### 4. 分析 REST 语义

记录：

- 分类和稳定 ID
- HTTP 方法与完整路径
- 网关或上下文前缀
- 鉴权、角色、权限和租户约束
- Header、Path、Query、Form 和 Body 参数
- 请求、响应、分页和错误模型
- 幂等、限流、版本和缓存语义
- Controller、Service 和下游调用
- 数据表、缓存、消息和文件副作用
- 调用方、消费者和已知使用页面

不复制大量源码或完整生成模型，只记录理解接口所需结构与来源。

### 5. 分析服务间能力

识别：

- Feign Client
- RestTemplate、WebClient 和自定义 HTTP Client
- Dubbo、gRPC 或项目自定义 RPC
- Provider、Consumer、注册名、版本、分组和超时
- 重试、负载、熔断和降级

接口定义存在但没有装配或调用证据时，标记为已声明或状态未知。

### 6. 分析消息和队列能力

识别：

- Producer、Listener 和 Consumer
- Topic、Queue、Exchange、Routing Key 和 Consumer Group
- Redis Pub/Sub、Stream、List 或其他队列式用法
- 消息模型、序列化、顺序、重复和幂等
- 重试、回退、死信和补偿
- 消费副作用和事务边界

配置值需脱敏，逻辑名称可保留，生产地址和凭证不得输出。

### 7. 分析文件和任务能力

文件能力记录协议、目录或 Bucket 逻辑名、文件格式、触发方、接收方、重试和归档规则。

任务能力记录：

- JOB 稳定 ID
- 调度框架
- Cron 或触发方式
- 所属模块和处理入口
- 输入、输出和数据副作用
- 并发、锁、分片、重试和补偿
- 外部调用方或运维入口

### 8. 与基础信息交叉验证

检查：

- 数据源和表是否存在于基础信息
- 中间件、Topic 和配置键是否已登记
- 鉴权、事务和异常模型是否一致
- API 文档版本是否与代码依赖和网关配置匹配

冲突写入 `07-open-questions.md`，不得静默修正文档或代码。

### 9. 建立关系矩阵

至少写入：

```text
API → Controller/RPC → Service → TABLE/MIDDLEWARE
EVENT → Producer → Consumer → 副作用
JOB → 入口 → Service → TABLE/API/MIDDLEWARE
```

关系包含来源 ID、关系类型、目标 ID、证据和可信度。

### 10. 输出

生成或更新：

- `cadence/knowledgeBase/02-api-capabilities.md`
- `cadence/knowledgeBase/apis/`，仅大型项目使用
- `cadence/knowledgeBase/evidence/source-index.md`
- `cadence/knowledgeBase/evidence/traceability-matrix.md`
- `cadence/knowledgeBase/manifest.yaml`
- `cadence/knowledgeBase/07-open-questions.md`

## 禁止行为

- 不根据 Controller 名称判断对外属性。
- 不把 Feign Consumer 写成系统对外 Provider。
- 不把依赖存在视为消息或 RPC 实际使用。
- 不猜测请求字段业务含义、错误码或鉴权规则。
- 不输出凭证、生产地址和真实敏感样例。
- 不把定时任务的内部处理方法当成 REST API。

## 降级规则

- 缺少 API 文档：代码生成并标记待人工校对。
- 缺少网关资料：接口暴露状态写为未知或内部候选。
- 动态路由无法还原：记录配置入口和运行时限制。
- 只有接口定义无调用：标记已声明，不认定已使用。
- 工具不可用：按注解、配置和调用模式进行文本检索后定向阅读。

## 完成条件

- 能力分类明确。
- 对外和对内 REST 已分开。
- 非 HTTP 能力已纳入清单。
- 核心能力具有稳定 ID、状态、证据和可信度。
- 数据副作用与基础信息能够关联。
- 暴露范围不确定的能力进入待确认清单。

