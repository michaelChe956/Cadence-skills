# knowledge-base-context Skill

## 概述

`knowledge-base-context` 是现有项目 KnowledgeBase 的任务消费入口。

当用户进行需求澄清、Design、Plan、Coding、Testing、Review 或 Debug 时，它先从当前任务出发，同时读取 KnowledgeBase 与相关源码、DDL、配置，生成最小任务上下文包，再将控制权交回当前 Agent 继续用户原始任务。

该 Skill 不负责初始化或更新 KnowledgeBase，也不依赖 `cadence-workflow`。

## 使用前提

目标项目必须已经存在：

```text
cadence/knowledge-base/manifest.yaml
```

并且 Manifest 包含：

```yaml
schema_version: "3.0"
```

如果 Manifest 不存在或版本不是 `3.0`，Skill 会停止上下文读取，并提示先执行 `knowledge-base-bootstrap`。

## 如何使用

### 自然语言自动触发

当项目已经建立 Schema 3.0 KnowledgeBase，并且项目规则已经由 `knowledge-base-overview` 接入后，可以直接提出任务：

```text
帮我澄清订单取消需求在现有系统中的边界。
```

```text
设计库存预占方案，需要结合当前接口和数据模型。
```

```text
实现订单导出并补充异常测试。
```

```text
评审当前改动是否遗漏调用方。
```

```text
定位订单状态没有更新的问题。
```

Agent 应先使用 `knowledge-base-context` 获取任务上下文，再继续原始工作。

### Claude Code 手动调用

通过 `cadence-init` 插件调用：

```bash
/cadence-init:knowledge-base-context
```

也可以在命令后描述任务：

```text
/cadence-init:knowledge-base-context 实现订单导出并补异常测试
```

### Codex 手动调用

在 Skill 已安装或被当前项目发现后使用：

```text
$knowledge-base-context 实现订单导出并补异常测试
```

`agents/openai.yaml` 只提供 Codex 展示名称和默认提示，不负责安装或触发注册。

## 七类固定任务画像

每次任务选择一个主画像，最多附加两个辅助画像。

| 画像 | 典型请求 | 上下文重点 |
|------|----------|------------|
| 需求澄清 | “这个需求的边界是什么？” | 已有能力、业务规则、系统边界、冲突和澄清问题 |
| Design | “结合现有系统设计方案” | 架构、API、数据模型、中间件、扩展点和设计风险 |
| Plan | “制定实施计划” | 文件范围、符号依赖、修改顺序、风险和验证入口 |
| Coding | “实现或修改功能” | 精确修改入口、调用链、SQL、配置、边界条件和测试入口 |
| Testing | “补异常和回归测试” | 业务分支、错误码、Fixture、Mock、断言依据和执行命令 |
| Review | “评审是否遗漏影响” | Git Diff、调用方、测试、配置变化和 KnowledgeBase 漂移 |
| Debug | “定位为什么没有生效” | 失败路径、日志位置、开关、异常、并发和数据访问 |

组合任务示例：

- 实现接口并补测试：`Coding + Testing`
- 评审设计是否可实施：`Review + Design`
- 排查问题并准备修复计划：`Debug + Plan`

画像是固定集合，不支持用户新增或动态注册画像。

## Schema 3.0 Manifest

### Manifest 是什么

Schema 3.0 Manifest 是 KnowledgeBase 的目录卡、范围控制文件和生成基线，不是数据库 Schema。

文件位置：

```text
cadence/knowledge-base/manifest.yaml
```

它记录：

- KnowledgeBase Schema 版本。
- 生成 Skill 和版本。
- 用户允许分析的工程范围。
- 数据库、中间件、API 和页面的分析模式及范围。
- 对外能力清单来源。
- Git 分支和基线提交。
- 已生成文档、覆盖情况和待确认项。

### 用户需要自己配置吗

不需要手工编写或维护 Manifest。

用户需要提供的是：

```text
cadence/knowledge-base/user-input/
├── base-info.md
├── project-scope.md
├── database-ddl.sql
├── middleware-scope.md
├── api-scope.md
└── page-scope.md
```

其中 `base-info.md` 是强制入口。用户在其中声明各领域是 `全量`、`指定` 还是 `不适用`，并引用其他输入文件。

`knowledge-base-bootstrap` 校验输入后自动生成：

```text
cadence/knowledge-base/input-inventory.md
cadence/knowledge-base/manifest.yaml
```

范围发生变化时，应更新 `user-input` 文档并重新执行 Bootstrap 或后续 KnowledgeBase Update，不建议直接修改生成后的 Manifest。

### Manifest 不负责什么

- 不参与自然语言自动触发。
- 不代替 KnowledgeBase 领域文档。
- 不代替当前源码、DDL、有效配置和测试。
- 不授权 Agent 扫描用户未提供的工程或领域范围。

Skill 是否自动触发由 `SKILL.md` Description 和项目规则决定。Manifest 只在触发后提供 Schema、范围和 Git 基线。

## 双轨渐进读取

KnowledgeBase 与源码、DDL、配置同等重要，不存在主从关系。

```text
KnowledgeBase 路径
README → 领域索引 → 稳定 ID → 关系矩阵和证据索引

当前实现路径
任务关键词 → 文件/符号/路由/SQL/配置/测试入口
```

默认围绕任务种子扩展一跳：

```text
ROUTE → PAGE → API → SERVICE/MODULE → TABLE/MIDDLEWARE/EXTERNAL
TEST → 被测符号 → Fixture/Mock/配置
```

只有画像必需信息不足时才继续扩展。公共工具类、通用日志、基础异常和框架启动链不会被无限展开。

## 证据与冲突

关键结论同时记录 KnowledgeBase 和当前实现证据，状态固定为：

- `一致`
- `KnowledgeBase 缺失`
- `源码缺失`
- `基线漂移`
- `来源冲突`
- `待确认`

当前提交晚于 Manifest 基线不代表一定发生漂移。只有任务相关文件或符号在基线后确实变化时，才标记 `基线漂移`。

冲突会改变任务方向时，Skill 保留双方证据并询问用户，不会静默选择其中一方。

## 输出内容

任务上下文包固定包含：

1. 任务识别
2. 任务理解
3. 核心实体
4. 双轨证据矩阵
5. 关系与影响面
6. 画像专属上下文
7. 约束与现有模式
8. 冲突、缺口与待确认项
9. 下游使用建议
10. 就绪状态

就绪状态包括：

| 状态 | 含义 |
|------|------|
| `就绪` | 关键上下文完整，没有影响方向的未决冲突 |
| `有条件就绪` | 存在非阻断缺口，可以在明确假设下继续 |
| `阻断` | 关键规则缺失、目标无法确定或冲突会改变任务方向 |

## 持久化规则

默认只在当前会话中使用任务上下文，不创建文件。

只有用户明确要求复用、交接或审计时，才保存到：

```text
cadence/knowledge-base/task-contexts/
YYYY-MM-DD_任务上下文_任务名称_v1.0.md
```

任务快照不是新的事实知识库，不自动加入 Manifest，也不自动更新领域文档。

## 完整使用流程

```text
1. 用户填写 cadence/knowledge-base/user-input/
2. 执行 knowledge-base-bootstrap
3. Bootstrap 自动生成 Manifest 3.0 和领域 KnowledgeBase
4. knowledge-base-overview 将使用规则接入 AGENTS.md / CLAUDE.md
5. 用户直接提出需求、设计、计划、编码、测试、评审或调试任务
6. knowledge-base-context 自动获取任务上下文
7. 当前 Agent 继续处理用户原始任务
8. 项目事实发生变化后执行 knowledge-base-update
```

## 常见问题

### Q: 没有 Manifest 可以直接扫描源码吗

不可以。Manifest 缺失或版本不是 `3.0` 时，Skill 会停止并引导执行 `knowledge-base-bootstrap`，不会回退为无范围的全仓扫描。

### Q: 使用这个 Skill 会查询数据库吗

不会。它只使用用户提供的 DDL、KnowledgeBase、源码、SQL、配置和测试，不连接数据库、中间件、配置中心或远程环境。

### Q: KnowledgeBase 和源码冲突时相信谁

两边证据都会保留。当前行为依据当前提交中的可验证实现描述，业务语义与预期保留 KnowledgeBase 和用户资料定义；如果冲突会改变任务方向，则询问用户。

### Q: 自动触发后会不会只返回上下文，不继续开发

不会。该 Skill 是前置上下文阶段。完成后调用方必须继续原始任务，除非用户明确只要求加载、整理或保存上下文。

### Q: 存量项目升级插件后如何获得自动触发规则

重新执行 `knowledge-base-overview`，或在下一次 `knowledge-base-update` 编排 Overview 时刷新稳定管理区块。

## 相关 Skills

- `knowledge-base-bootstrap`：校验用户输入并初始化 Schema 3.0 KnowledgeBase。
- `knowledge-base-base-info`：生成工程、数据、中间件和开发方式信息。
- `knowledge-base-api`：分析对外能力和工程内对内能力。
- `knowledge-base-pages`：分析页面、路由、权限和 REST API 关联。
- `knowledge-base-overview`：生成知识库入口、关系导航和项目使用规则。
- `knowledge-base-update`：根据 Git 和增量资料更新 KnowledgeBase。

## 技术细节

- [Skill 定义](../../cadence-init/skills/knowledge-base-context/SKILL.md)
- [渐进读取指南](../../cadence-init/skills/knowledge-base-context/references/progressive-retrieval-guide.md)
- [任务画像](../../cadence-init/skills/knowledge-base-context/references/task-profiles.md)
- [完整案例](../../cadence-init/skills/knowledge-base-context/references/demo.md)
