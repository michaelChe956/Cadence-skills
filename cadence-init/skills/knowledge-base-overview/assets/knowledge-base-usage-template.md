# KnowledgeBase 使用规则

## 强制要求

1. 进行需求澄清、Design、Plan、Coding、Testing、Review 或 Debug 时，先使用 `knowledge-base-context` 获取最小任务上下文。
2. 修改代码前读取 `cadence/knowledge-base/README.md`。
3. 先确认 `manifest.yaml` 为 Schema 3.0，再按任务范围读取相关服务、API、页面、数据和开发指南文档。
4. KnowledgeBase 与当前源码、DDL、配置同等重要；冲突时同时保留双方证据，以可验证实现描述当前行为，不静默覆盖业务语义。
5. `[合理推断]`、`[来源冲突]` 和 `[待人工确认]` 不得作为确定事实使用。
6. 修改 API、页面、DDL、配置、中间件或核心流程后，执行 `knowledge-base-update`。
7. 大型知识库按导航渐进加载，不一次读取全部子文档或全仓源码。

## 知识库定位

知识库是项目事实索引和代码导航，不替代源码、DDL、有效配置、测试和用户确认。

## 调用方式

- 自然语言任务由代理根据 `knowledge-base-context` 的 Skill Description 自动选择。
- Claude Code 插件手动调用：`/cadence-init:knowledge-base-context`。
- Codex 在 Skill 已安装或被项目发现后手动调用：`$knowledge-base-context`。
- Manifest 只提供 Schema、范围和基线，不参与 Skill 触发。
- 上下文准备完成后继续用户原始任务，不因该 Skill 自动命中而停止 Design、Plan、Coding、Testing、Review 或 Debug。

## 修改场景读取顺序

| 修改场景 | 必读文档 |
|----------|----------|
| 页面或路由 | `pages/README.md`、相关 API 文档 |
| REST 或 RPC | `interfaces/README.md`、对应接口主文件、基础信息和数据文档 |
| 数据模型 | `base-information.md`、API 和页面影响关系 |
| 配置或中间件 | `base-information.md`、`development-guide.md` |
| 跨模块流程 | `README.md`、关系矩阵和相关领域文档 |
