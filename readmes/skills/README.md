# Cadence Skills 使用指南

## Skills 总览（15 个）

Cadence 的能力以 Skill 形式提供。安装后，Claude Code 通过 `~/.claude/skills/` 消费，pi、Codex、Kimi Code 和 omp 通过共享的 `~/.agents/skills/` 消费；Codex 同时提供扁平的 `~/.codex/skills/<skill>` 用户技能层投影（与 Codex 自带的 `~/.codex/skills/.system/` 并列、互不覆盖）。

### KnowledgeBase Skills（8 个）

| Skill | 用途 | 指南 |
| --- | --- | --- |
| `knowledge-base-api` | 分析 API、消息、队列、文件交换和集成能力 | — |
| `knowledge-base-base-info` | 建立工程、服务、数据模型、配置和开发方式基础信息 | — |
| `knowledge-base-bootstrap` | 校验输入并初始化 Schema 4.0 KnowledgeBase | [指南](knowledge-base-bootstrap.md) |
| `knowledge-base-context` | 按任务画像提供最小 KnowledgeBase 上下文 | [指南](knowledge-base-context.md) |
| `knowledge-base-overview` | 生成知识库入口、关系导航、术语和项目规则 | — |
| `knowledge-base-pages` | 分析 Vue/React 页面、路由、权限、状态和 API 关系 | — |
| `knowledge-base-update` | 依据完整变更包增量更新已有 KnowledgeBase | [指南](knowledge-base-update.md) |
| `knowledge-base-user-input` | 依据目标项目证据生成 9 个输入文件草稿并交用户确认 | [指南](knowledge-base-user-input.md) |

### 初始化与规则 Skills（4 个）

| Skill | 用途 |
| --- | --- |
| `mcp-configuration` | 创建或维护项目 MCP 配置并交接客户端设置（确定性脚本 `scripts/mcp-config.py`，可重复执行） |
| `pre-check` | 检查开发环境、基础工具和初始化前置条件 |
| `project-rules-examples` | 创建项目个性化规则模板（确定性脚本 `scripts/apply.py`，重复执行不改写人工正文） |
| `rule-config` | 配置规则、入口文件、`cadence/` 目录和 OpenSpec 协作入口 |

### 兼容与创建 Skills（2 个）

| Skill | 用途 | 指南 |
| --- | --- | --- |
| `legacy-bootstrap` | 使用兼容流程为 legacy 项目建立 Cadence 项目认知 | — |
| `skill-creator` | 创建、校验、打包和优化 Skill | [指南](skill-creator.md) |

### 开发环境 Skills（1 个）

| Skill | 用途 | 指南 |
| --- | --- | --- |
| `devbox-stack` | devbox 容器内中间件/应用的唯一运维入口（环境检测，非 devbox 自动不适用） | [指南](devbox-stack.md) |

## 五端 Agent 的消费路径

| Agent | 消费路径 | 说明 |
| --- | --- | --- |
| Claude Code | `~/.claude/skills/` | 消费 Claude Code 个人层的 skill 级链接 |
| pi | `~/.agents/skills/` | 读取共享层 |
| Codex | `~/.agents/skills/`；用户技能层 `~/.codex/skills/` | 优先共享层，同时提供用户技能层 |
| Kimi Code | `~/.agents/skills/` | 读取共享层 |
| omp（oh-my-pi） | `~/.agents/skills/` | 读取共享层 |

三层链接由根目录 `install.sh` 维护。omp 与 pi 一样消费共享层，安装脚本不创建 `.omp/skills` 软链；`~/.pi/agent/skills` 是 Superpowers 或 pi 自身的目录，不属于 Cadence 安装脚本创建的层。

## 快速导航

### 创建或维护技能

- 创建或优化 Skill：调用 `/skill-creator`，见 [skill-creator 指南](skill-creator.md)。
- 检查环境：调用 `/pre-check`。
- 配置项目规则：调用 `/rule-config`。

### 使用现有项目知识

- 尚未准备知识库输入：调用 `/knowledge-base-user-input` 生成输入草稿并逐项确认。
- 首次建立知识库：调用 `/knowledge-base-bootstrap`。
- 任务前获取上下文：调用 `/knowledge-base-context`。
- 项目事实变化后更新：调用 `/knowledge-base-update`。

## 相关资源

- [Commands 使用指南](../commands/README.md)
- [项目 README 的网络安装章节](../../README.md#安装-cadence-skills)
- [开发者项目知识文档](../../cadence/readmes/2026-09-01_README_项目知识文档_v1.0.md)

## 获取帮助

- 问题反馈：https://github.com/michaelChe956/Cadence-skills/issues
- 文档问题：提交 Issue 或 Pull Request，并附上 Agent、Skill 名称和实际错误信息。
