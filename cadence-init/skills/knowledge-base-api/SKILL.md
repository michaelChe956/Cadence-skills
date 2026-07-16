---
name: knowledge-base-api
description: "Use when 需要按用户提供的对外能力清单和工程范围，全量盘点或指定深挖 REST、RPC、消息、Redis 队列、文件交换、定时任务与批处理能力。"
---

# KnowledgeBase API 与集成能力

## 概述

同时承担项目级能力盘点和单能力调用链深挖。用户提供的对外能力清单决定对外分类；工程范围内发现但未登记的能力归入对内能力。不得用单接口 Demo 替代全量盘点。

## 必读资源

- 执行前读取 `references/api-analysis-guide.md`。
- 生成能力主文件时使用 `assets/api-capabilities-template.md`。
- 生成请求响应配套文件时使用 `assets/api-parameters-message-template.md`。
- 分析用户清单中的对外能力时，成品格式参考 `references/demo.md` 和 `references/demo_参数与报文.md`。
- 分析工程扫描发现的对内前端 REST 时，成品格式参考 `references/demo_对内REST.md` 和 `references/demo_对内REST_参数与报文.md`。

## 前置输入

必须读取：

- `cadence/knowledge-base/manifest.yaml`
- Manifest 中登记的工程范围
- Manifest 中登记的对外能力清单
- Manifest 中登记的 API 状态、执行模式和指定能力
- 用户提供的 DDL、中间件和页面范围

Manifest 不存在、Schema 不是 `3.0` 或 API 输入未通过 Bootstrap 校验时停止，并引导执行 `knowledge-base-bootstrap`。

## 对外与对内分类

### 对外能力

用户 `api-scope.md` 中登记的全部能力是对外能力的权威清单：

- 保持对外分类，不因代码暂时无法定位而改判为对内。
- 代码用于核实实现、装配、暴露状态、调用链和副作用。
- 清单与代码冲突时保留对外分类，将实现冲突写入待确认项。

### 对内能力

在工程范围内发现但未登记的以下能力归为对内能力：

- 内部前端 REST API
- 服务间 REST API
- RPC Provider 与 Consumer
- 消息生产与消费
- Redis Pub/Sub、Stream、List 等队列式能力
- FTP、SFTP、对象存储和文件交换
- 定时任务、批处理和异步作业

疑似对外但未登记的能力标记为对内候选或待确认，不自动升级为对外。

### 成品案例选择

| 可观察条件 | 分类 | 参考案例 | 入口分析重点 |
|------------|------|----------|--------------|
| 能力登记在用户对外能力清单中 | 对外 | `demo.md`、`demo_参数与报文.md` | 对外清单、开放网关、能力编码、协议转换、Provider、外部鉴权与暴露状态 |
| 工程范围发现前端或内部系统 REST，且未登记在对外清单中 | 对内 | `demo_对内REST.md`、`demo_对内REST_参数与报文.md` | 页面或内部调用方、请求封装、BFF/内部网关、Controller、权限和服务调用链 |

Demo 只约束文档形状，不提供目标项目事实。不得因为对内 REST 与某个对外能力业务名称相似，就复用对外分类、能力编码、调用方或网关结论。

## 执行模式

### 全量模式

1. 在 Manifest 工程范围内扫描所有能力类型。
2. 先建立 `cadence/knowledge-base/interfaces/README.md` 总索引。
3. 索引分为“对外能力”和“对内能力”。
4. 对每项能力记录稳定 ID、类型、状态、实现位置、证据和明细链接。
5. 再逐项生成能力主文件；请求响应能力同时生成参数与报文文件。

### 指定模式

1. 只分析 Manifest 中的指定能力。
2. 允许追踪完成调用链所需的内部依赖。
3. 不盘点与指定能力无关的接口。
4. 指定能力不在对外清单时默认归为对内。

用户明确选择全量或多个能力后连续执行，不在每完成一项后重复询问是否继续。

## 能力状态

每项能力分别判断：

- 已声明
- 已实现
- 已装配
- 已暴露
- 条件启用
- 已废弃
- 测试专用
- 代码存在但不可达
- 状态未知

对外清单只能证明对外设计分类，不能单独证明当前代码已实现或运行环境已暴露。

## 工作流程

### 1. 读取范围并建立索引

读取 Manifest 和对外能力清单，生成或更新：

```text
cadence/knowledge-base/interfaces/README.md
```

索引至少包含：

| ID | 能力名称 | 分类 | 类型 | 状态 | 实现位置 | 主文件 | 参数与报文 | 证据 |
|----|----------|------|------|------|----------|--------|------------|------|

### 2. 发现能力入口

根据项目实际技术栈识别：

- Spring MVC、WebFlux 和自定义路由
- Feign、RestTemplate、WebClient 和自定义 HTTP Client
- Dubbo、gRPC、HSF 或其他 RPC
- 消息 Producer、Listener 和 Consumer
- Redis 队列式使用
- 文件上传、下载、交换和对象存储
- 调度注解、调度框架、批处理和异步任务

大范围关系优先使用 CodeGraph；具体文件先用 `ast-grep outline` 获取结构，再定向阅读。工具不可用时使用文本检索降级。

Mapper XML、配置和资源目录必须根据项目结构探测，不假设固定位置。

### 3. 核实调用链

对每项能力核实：

1. 入口定义、实现、装配和暴露证据
2. 参数、响应、错误和鉴权
3. Service、DAO、RPC、消息和文件调用
4. 分支条件、开关和环境差异
5. 数据表、缓存、中间件和外部系统副作用
6. 调用方、消费者、页面和任务关系

间接调用必须逐跳追踪。无法唯一映射时列出候选并标记待确认。

### 4. 核实数据库证据

只使用：

- 用户提供的 DDL
- Entity、Mapper、SQL 和迁移文件
- 数据源与 Schema 配置
- 用户明确说明

禁止连接数据库或查询在线元数据。无法确认 Schema、表归属或环境时标记待确认，不使用工程名代替数据库名。

### 5. 生成能力文档

请求响应能力生成：

```text
cadence/knowledge-base/interfaces/{标识}_{接口名称}_{API名称}.md
cadence/knowledge-base/interfaces/{标识}_{接口名称}_{API名称}_参数与报文.md
```

消息、文件、任务等非请求响应能力只生成主文件；没有参数与报文时不创建空配套文件。

主文件遵循 11 节结构。字段处理：

- 有证据：填写真实值和来源。
- 用户未提供：填写 `未提供`。
- 扫描未发现：填写 `未发现`。
- 不适用于能力：填写 `不适用`。
- 单个字段缺失不阻断文档生成。

### 6. 更新关系与进度

更新：

- `interfaces/README.md`
- `manifest.yaml`
- `evidence/source-index.md`
- `evidence/traceability-matrix.md`
- `open-questions.md`

进度只记录在 Manifest 和索引中，不使用运行时任务或记忆目录。

## 交互规则

范围、同名能力或证据冲突确实无法判断时：

- Claude Code 使用 `AskUserQuestion`。
- Codex 工具可用时使用 `request_user_input`。
- 工具不可用时使用普通文本提问。

用户范围已经明确时不得重复确认。

## 禁止行为

- 不根据 Controller 名称判断对外属性。
- 不凭 API 名称猜实现工程或能力集。
- 不把依赖声明视为能力实际使用。
- 不把同 JVM 本地调用误写成网络 RPC。
- 不根据 DAO 名猜表名，必须核对 SQL 或 DDL。
- 不连接数据库、中间件或远程环境。
- 不输出凭证、完整连接串和未脱敏敏感值。
- 不把定时任务内部方法当成 REST API。
- 不自动写入 `cadence/project-rules/`。

## 完成条件

- 对外能力完全来自用户清单。
- 工程内未登记能力已归类为对内。
- 全量或指定模式符合 Manifest。
- REST、RPC、消息、队列、文件和任务按范围纳入。
- 核心能力具有稳定 ID、状态、证据和可信度。
- 数据副作用能够关联 DDL、代码和配置证据。
- 不确定项进入待确认清单。
