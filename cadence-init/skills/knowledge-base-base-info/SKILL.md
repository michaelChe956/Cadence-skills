---
name: knowledge-base-base-info
description: "Use when 需要为 Java 与 Vue/React 存量项目分析技术栈、模块、DDL、配置、中间件、横切机制、构建测试方式，或生成 KnowledgeBase 基础信息与开发指南。"
---

# KnowledgeBase 基础信息

## 概述

从代码、DDL、配置和用户资料中建立项目的基础事实模型，生成 `base-information.md` 和 `development-guide.md`。重要结论必须可定位、可区分事实与推断，并能被 API、页面和增量技能复用。

## 必读资源

- 执行前读取 `references/java-bs-analysis-guide.md`。
- 生成基础信息时使用 `assets/base-information-template.md`。
- 生成工程指南时使用 `assets/development-guide-template.md`。
- 需要参考完整示例时读取 `references/demo.md`。

## 前置输入

优先读取：

- `cadence/knowledge-base/manifest.yaml`（必须为 Schema 3.0）
- `cadence/knowledge-base/input-inventory.md`
- 用户提供的 DDL、配置和中间件清单
- 项目构建文件、配置文件和代码结构

Manifest 不存在或 Schema 不是 3.0 时停止并引导使用 `knowledge-base-bootstrap`。只分析 Manifest 声明的工程、DDL 和中间件范围，不得自行扩大范围。

## 强制规则

- 读取项目规则后再分析。
- 重要事实使用 `[代码事实]`、`[DDL事实]`、`[配置事实]` 或 `[用户提供]`。
- 间接结论使用 `[合理推断]` 并标注可信度。
- DDL、ORM、Mapper、SQL 和用户说明冲突时使用 `[来源冲突]`。
- 只记录敏感配置键、用途和值类型，实际值写为 `<redacted>`。
- 依赖声明只能证明“可能使用”，必须结合配置、装配和调用证据判断实际使用。
- 测试、Mock、示例和生成代码必须单独标记。
- 不运行应用、迁移、部署或生产脚本。

## 工作流程

### 1. 建立项目边界

识别：

- 仓库、Git 子模块和前后端目录
- Maven 父子模块或 Gradle 多项目结构
- Spring Boot 启动类和服务入口
- Vue/React 应用入口、构建工具和包管理器
- 公共模块、业务模块、基础设施模块和生成代码目录

为仓库、服务和模块生成稳定 ID，例如：

```text
REPO-commerce
SERVICE-order-service
MODULE-order-core
```

### 2. 分析技术栈

从构建文件、锁文件、插件、Import 和实际配置中提取：

- Java、JDK、Spring Boot、Spring Cloud、Dubbo 版本
- Maven、Gradle 与关键插件
- ORM、数据库驱动和迁移工具
- Vue、React、路由、状态管理、请求库和构建工具版本
- 测试、代码质量和生成工具

无法从锁文件或有效依赖管理确认的版本不得编造。

### 3. 分析数据模型

按数据库和 Schema 分组处理：

- 表、字段、类型、默认值和注释
- 主键、外键、唯一约束和索引
- 序列、自增和 ID 生成方式
- 分区、分库分表、路由键和物理表规则
- 视图、触发器、存储过程和函数
- 软删除、租户、版本号和审计字段
- DDL 与 Entity、Mapper、JPA、MyBatis XML、迁移文件的差异

为数据表生成稳定 ID，例如 `TABLE-order`。没有显式外键时，不得仅根据字段同名断言表关系。

### 4. 分析配置

建立配置来源和生效链路：

- Properties、YAML 和 Profile
- 环境变量与占位符
- Nacos、Apollo、Consul、Spring Cloud Config
- 配置命名空间、分组、加载顺序和覆盖关系
- `@ConfigurationProperties`、`@Value`、条件装配和 Feature Flag
- 数据源、网关、缓存、消息、任务和外部系统配置

记录配置键、用途、值类型、适用环境、代码绑定位置和敏感级别，不复制敏感值。

### 5. 分析中间件

对每个中间件记录：

- 稳定 ID、名称、版本和环境
- 业务用途
- 所属模块、生产者和消费者
- Topic、Queue、Consumer Group、Key 或缓存命名规则
- 序列化和数据模型
- 顺序、重复、幂等、重试和死信策略
- 超时、连接池、熔断和降级
- 条件装配与 Profile

判断状态：已声明、已实现、已装配、条件启用、测试专用或状态未知。

### 6. 分析横切关注点

梳理：

- 认证、授权、租户和数据权限
- 本地事务、分布式事务和补偿
- 缓存、失效和一致性
- 幂等、重试、超时、熔断和限流
- 分布式锁与并发控制
- 统一异常、错误码和响应包装
- 日志、指标、链路追踪和审计
- 数据脱敏、隐私和软删除

横切机制必须关联配置、框架装配和实际调用位置。

### 7. 生成开发指南

从构建文件、脚本、CI 配置和项目文档中整理：

- JDK、Node.js、Maven、Gradle 和包管理器版本
- 模块构建顺序
- 本地启动顺序和依赖服务
- Profile、环境变量和前端代理
- 测试、格式检查、静态检查和构建命令
- 测试目录、类型和环境依赖
- 数据库迁移方式
- 常见修改场景对应的验证命令
- 不应在本地直接执行的生产脚本

只记录能够从项目资料确认的命令，不为缺失项目脚本创造虚假命令。

### 8. 建立关系与证据

至少建立：

- 服务 → 模块
- 模块 → 数据表
- 模块 → 配置组
- 模块 → 中间件
- 横切机制 → 配置与实现位置

将详细来源写入 `cadence/knowledge-base/evidence/source-index.md`，将关系写入 `cadence/knowledge-base/evidence/traceability-matrix.md`。

### 9. 输出

生成或更新：

- `cadence/knowledge-base/base-information.md`
- `cadence/knowledge-base/development-guide.md`
- `cadence/knowledge-base/evidence/source-index.md`
- `cadence/knowledge-base/evidence/traceability-matrix.md`
- `cadence/knowledge-base/manifest.yaml`
- `cadence/knowledge-base/open-questions.md`

大型项目按服务或 Schema 拆分到 `services/` 和 `data-models/`。

## 降级规则

- 缺少 DDL：分析 Entity、Mapper、SQL 和迁移文件，明确数据库模型不完整。
- 缺少中间件清单：从依赖、配置和调用生成候选，不认定依赖即使用。
- 缺少生产配置：只描述已知环境，不把开发配置推广到生产。
- 工具不可用：文本检索定位候选后定向阅读。
- 无法确认版本：写 `unknown` 或待确认，不选择近似版本。

## 完成条件

- 项目、服务和模块边界已经记录。
- DDL、配置和中间件资料状态明确。
- 核心实体具有稳定 ID、证据和可信度。
- 来源冲突和未覆盖范围进入待确认清单。
- 开发指南中的命令均有来源。
- 未输出明文敏感值。
