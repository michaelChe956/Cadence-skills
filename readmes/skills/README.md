# Cadence Skills 使用指南

本目录包含所有 Cadence Skills 的详细使用文档。

## Skills 分类

### 元 Skills（1个）

- [skill-creator](skill-creator.md) - 创建、校验、打包并优化 Claude Code skills

### KnowledgeBase Skills（7个）

- [knowledge-base-bootstrap](knowledge-base-bootstrap.md) - 校验用户输入、初始化 Schema 4.0 KnowledgeBase 并编排领域分析
- `knowledge-base-base-info` - 生成工程、服务、数据、中间件和开发方式信息
- `knowledge-base-api` - 分析对外能力和工程内对内能力
- `knowledge-base-pages` - 分析页面、路由、权限和 REST API 关联
- `knowledge-base-overview` - 生成知识库入口、导航和项目使用规则
- [knowledge-base-update](knowledge-base-update.md) - 消费完整变更包，幂等更新已有 KnowledgeBase
- [knowledge-base-context](knowledge-base-context.md) - 从任务出发，同时读取 KnowledgeBase 与当前实现并生成最小上下文

## 快速导航

### 我要创建或维护技能

- **创建/维护技能** → [skill-creator](skill-creator.md)

### 我要使用现有项目知识

- **首次建立 KnowledgeBase** → [knowledge-base-bootstrap](knowledge-base-bootstrap.md)
- **需求、设计、计划、编码、测试、评审或调试前获取上下文** → [knowledge-base-context](knowledge-base-context.md)
- **项目事实发生变化后更新 KnowledgeBase** → [knowledge-base-update](knowledge-base-update.md)

## 相关资源

- [Commands 使用指南](../commands/)
- [项目 README](../../README.md)

## 获取帮助

- **问题反馈**: https://github.com/michaelChe956/Cadence-skills/issues
- **文档问题**: 提交 Issue 或 PR
