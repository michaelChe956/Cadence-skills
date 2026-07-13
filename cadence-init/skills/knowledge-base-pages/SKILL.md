---
name: knowledge-base-pages
description: "Use when 需要为 Vue 或 React 存量前端分析页面、静态与动态路由、菜单、权限守卫、状态管理、API 调用及后端数据映射，并生成 KnowledgeBase 页面能力文档。"
---

# KnowledgeBase 页面能力

## 概述

从路由资料和前端代码中建立页面能力模型，关联页面、路由、权限、状态、API、后端服务和数据实体。无法通过静态代码还原的动态行为必须标记运行时限制，不得补造完整路由表。

## 必读资源

- 执行前读取 `references/page-analysis-guide.md`。
- 生成页面文档时使用 `assets/page-capabilities-template.md`。
- 需要参考 Vue/React 综合案例时读取 `references/demo.md`。

## 前置输入

优先读取：

- `cadence/knowledgeBase/manifest.yaml`
- `cadence/knowledgeBase/01-base-information.md`
- `cadence/knowledgeBase/02-api-capabilities.md`
- 用户提供的路由、菜单、角色和权限资料
- Vue/React 路由、页面、状态管理和请求模块代码

API 文档缺失或页面调用无法定位时，记录待确认，不得根据按钮名称猜测后端接口。

## 强制规则

- 为页面和路由分别生成稳定 ID。
- 区分静态路由、动态路由、后端下发路由和运行时注入路由。
- 区分路由存在、组件存在、页面可达和用户有权访问。
- 页面调用的 API 必须关联到 `02-api-capabilities.md` 中的 API ID；未登记接口先标记候选。
- 权限结论必须结合路由元数据、守卫、菜单、状态和后端鉴权资料。
- 测试页面、Storybook、Demo 和开发工具页面单独标记。
- 动态 Import、别名和懒加载路径必须解析到实际组件或标记未知。

## 工作流程

### 1. 确认前端应用边界

识别：

- Vue 2、Vue 3 或 React 应用
- Monorepo、微前端或多入口应用
- 路由库、状态管理和请求封装
- 构建工具、路径别名和环境变量
- 管理端、用户端、移动 Web 等应用边界

为前端应用和模块复用基础信息中的稳定 ID。

### 2. 收集路由来源

按来源分类：

- 代码静态路由
- 模块自动注册路由
- 后端菜单或权限接口下发
- 运行时 `addRoute`、`addRoutes` 或配置注入
- 文件系统路由
- 微前端基座注册
- 用户提供的路由或菜单文档

记录每个来源的文件、函数、配置键或接口证据。

### 3. 构建路由树

组合：

- 父子路径
- 路由名称
- 重定向
- Layout 和嵌套出口
- 动态参数和可选参数
- 路由别名
- 懒加载组件
- KeepAlive、缓存或元数据

为路由生成 `ROUTE-*`，为业务页面生成 `PAGE-*`。同一页面被多个路由引用时保留一个页面实体和多个路由关系。

### 4. 判断页面状态

记录：

- 已声明：存在路由或页面注册
- 组件存在：能够定位页面组件
- 已装配：路由进入有效路由树
- 可达：存在导航、菜单、重定向或已知入口
- 条件启用：依赖权限、Feature Flag、环境或后端菜单
- 已废弃：明确废弃或被替代
- 代码存在但不可达：组件存在但没有有效入口
- 测试专用：仅测试、Demo 或 Storybook 使用
- 状态未知：动态来源无法确认

### 5. 分析权限与导航

识别：

- 登录状态和 Token 恢复
- 全局与局部路由守卫
- 角色、权限码、菜单码和数据权限
- 白名单、免登录页和错误页
- 后端菜单转换逻辑
- 权限状态存储和刷新流程
- 按钮、操作和组件级权限

前端隐藏按钮不等于后端完成授权，必须分别记录前端控制与后端鉴权。

### 6. 分析页面能力

对每个页面记录：

- PAGE 与 ROUTE ID
- 页面名称和业务用途
- 页面组件、布局和入口
- 主要查询、创建、修改、删除、导入、导出等操作
- 表单字段、校验和状态来源
- Store、Context、Hook 或 Composable
- 调用 API 及调用条件
- 上传、下载、WebSocket 或消息能力
- Feature Flag 和环境差异
- 可达性、生命周期、证据和可信度

只描述能够由代码或用户资料证明的业务用途。

### 7. 关联 API 和数据

按调用链建立：

```text
ROUTE → PAGE → API → SERVICE/MODULE → TABLE/MIDDLEWARE
```

需要考虑：

- 请求封装添加的统一前缀
- 环境变量和代理重写
- BFF 或网关路径
- 动态参数和请求工厂
- 同一 API 被多个页面复用
- 页面只消费 Store，而 Store 发起 API 请求

无法唯一映射时列出候选并标记待确认。

### 8. 识别异常项

记录：

- 有路由但组件缺失
- 组件存在但没有路由或入口
- 菜单指向未知路由
- 页面调用未登记 API
- 路由权限与按钮权限冲突
- 文档路由与代码路由不一致
- 已删除页面仍被菜单或重定向引用

### 9. 输出

生成或更新：

- `cadence/knowledgeBase/03-page-capabilities.md`
- `cadence/knowledgeBase/pages/`，仅大型项目使用
- `cadence/knowledgeBase/evidence/source-index.md`
- `cadence/knowledgeBase/evidence/traceability-matrix.md`
- `cadence/knowledgeBase/manifest.yaml`
- `cadence/knowledgeBase/07-open-questions.md`

## 禁止行为

- 不把文件目录直接当成路由结构。
- 不把组件存在视为页面可达。
- 不把前端权限控制视为后端鉴权证明。
- 不根据按钮文字猜测 API 路径。
- 不把开发工具、Demo 和 Storybook 页面混入生产页面。
- 不为动态路由补造运行时返回结果。
- 不复制大段组件源码到知识库。

## 降级规则

- 缺少路由资料：以代码路由为主，动态和后端路由标记未覆盖。
- 缺少 API 能力文档：生成 API 候选引用并要求后续 API 技能校对。
- 路径别名无法解析：记录别名配置缺口和候选文件。
- 微前端子应用不在当前仓库：记录远程应用边界和未知页面范围。
- 工具不可用：按路由、Import、请求函数和组件引用模式检索。

## 完成条件

- 所有已发现路由均有来源和状态。
- 页面和路由使用独立稳定 ID。
- 页面、API、服务和数据之间能够导航。
- 动态、权限和运行时限制已经明确。
- 孤立、不可达和冲突项进入待确认清单。

