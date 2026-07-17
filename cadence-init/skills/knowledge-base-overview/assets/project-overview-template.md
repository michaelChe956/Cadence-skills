# 项目概览

## 文档元数据

- 生成时间：
- Git 分支：
- 基线提交：
- 执行模式：
- 覆盖范围：
- 未覆盖范围：

## 项目摘要

用简短文字说明项目定位、系统边界、主要仓库或应用、当前基线和覆盖范围。这里只保留摘要，不复制字段清单、全部配置键或领域文档正文。

## 一级导航

> 按 Manifest 条件渲染：`scope.api.status` 或 `scope.pages.status` 为 `不适用` 时，对应行的入口使用无链接纯文本 `interfaces：不适用（原因）` 或 `pages：不适用（原因）`；适用时才使用下方链接。不得生成指向不存在 README 的链接。

| 入口 | 内容 |
|------|------|
| [`base-information.md`](base-information.md) | 项目基础信息与系统边界 |
| [`development-guide.md`](development-guide.md) | 开发、验证与运行指南 |
| {{接口入口：适用时为 [`interfaces/README.md`](interfaces/README.md)，不适用时为无链接文本}} | 对外、对内和服务间接口，或不适用原因 |
| {{页面入口：适用时为 [`pages/README.md`](pages/README.md)，不适用时为无链接文本}} | 页面、路由、权限和字段映射，或不适用原因 |
| [`services/`](services/) | 服务与模块导航 |
| [`data-models/README.md`](data-models/README.md) | 字段级数据模型与表导航 |
| [`configurations/README.md`](configurations/README.md) | 服务配置、Profile、Feature Flag 与中间件配置导航 |
| [`evidence/`](evidence/) | 当前源码、结构和配置快照证据 |
| [`change-history.md`](change-history.md) | KnowledgeBase 变更历史 |
| [`open-questions.md`](open-questions.md) | 待确认项 |

## 核心业务流程

稳定主链：

```text
PAGE → API → SERVICE/MODULE → TABLE → CONFIGURATION/MIDDLEWARE
```

每条流程只保留稳定 ID、摘要和领域文档链接；步骤、字段、配置键和证据明细留在对应领域文档。

## 常见修改场景

| 场景 | 必读文档 | 主要实体 | 影响检查 | 验证入口 |
|------|----------|----------|----------|----------|
| 字段变更 | `data-models/README.md`、字段级表文档、当前结构证据 | TABLE、COLUMN | API、页面、SQL/Mapper、服务 | `development-guide.md` |
| SQL/Mapper 变更 | 字段级表文档、SQL/Mapper 证据、服务文档 | TABLE、MAPPER、SERVICE/MODULE | 字段映射、事务、查询调用方 | `development-guide.md` |
| 配置键变更 | `configurations/README.md`、服务配置文档、当前快照证据 | CONFIGURATION | Profile、Feature Flag、服务和中间件 | `development-guide.md` |
| Profile/Feature Flag | 服务配置文档、当前快照证据 | PROFILE、FEATURE_FLAG | 环境差异、默认值、启用条件 | `development-guide.md` |
| API 参数变更 | 接口适用时读取 `interfaces/README.md`、接口主文档、服务和数据模型文档；不适用时记录原因 | API、PARAMETER | 调用方、页面、服务、表 | `development-guide.md` |
| 页面字段变更 | 页面适用时读取 `pages/README.md`、页面文档、接口和数据模型文档；不适用时记录原因 | PAGE、FIELD | API 参数、字段映射、校验 | `development-guide.md` |
| 中间件配置变化 | 配置文档、中间件证据、依赖服务文档 | MIDDLEWARE、CONFIGURATION | 连接、路由、消费和部署环境 | `development-guide.md` |

## 高风险区域

仅摘要列出高风险入口，详情链接到对应领域文档和证据。

## 待确认项

仅列出数量和最高优先级摘要，完整内容见 [`open-questions.md`](open-questions.md)。
