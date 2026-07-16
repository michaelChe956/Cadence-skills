---
name: knowledge-base-context
description: "Use before any project-specific 需求澄清、Design/技术设计、Plan/实施计划、Coding/编码、Testing/测试、Review/评审或 Debug/调试 task when Schema 3.0 KnowledgeBase exists and the task must be grounded in both KnowledgeBase and current source code, DDL, and configuration; also use when the user asks to load, retrieve, or organize project KnowledgeBase context."
---

# KnowledgeBase 任务上下文

## 概述

从用户当前任务出发，同时沿 KnowledgeBase 与当前源码两条证据路径渐进读取，生成足以支持下游工作的最小任务上下文包。本 Skill 是原始任务的前置上下文阶段，不代替需求、Design、Plan、Coding、Testing、Review 或 Debug，也不调用或依赖 `cadence-workflow`。

上下文准备完成后，调用方必须继续处理用户原始任务；只有用户明确只要求加载、整理或保存上下文时才在上下文包处结束。

## 手动入口

- Claude Code 插件：`/cadence-init:knowledge-base-context`
- Codex（Skill 已安装或被项目发现）：`$knowledge-base-context`

自动触发依赖 Frontmatter `description`。Manifest 只在触发后提供 Schema、范围和基线，不参与 Skill 发现或触发。

当本 Skill 与需求、设计、计划、实现、测试、评审或调试类 Skill 同时适用时，先执行本 Skill 的上下文阶段，再进入其他 Skill。

## 必读资源

- 执行渐进读取前读取 `references/progressive-retrieval-guide.md`。
- 识别主辅画像后读取 `references/task-profiles.md` 中对应画像。
- 需要核对完整输出形状时读取 `references/demo.md`。
- 只有用户明确要求保存任务上下文时，使用 `assets/task-context-template.md`。

## 强制边界

- 每次都同时读取 KnowledgeBase 与相关源码、DDL、配置；两条路径同等重要，不互为降级方案。
- 只在 Manifest 声明的工程与领域范围内读取，不因任务相关性自行越界。
- 默认只把上下文返回当前会话，不创建任务文件。
- 不连接数据库、中间件、配置中心或远程环境，不启动应用，不下载依赖。
- 不修改业务代码、KnowledgeBase、Manifest 或下游交付物。
- 不复制完整源码或整篇知识库文档，只保留摘要、稳定 ID、精确位置和必要短片段。
- 工作区未提交修改属于当前实现证据，不清理、不覆盖、不恢复。

## 工作流程

### 0. 前置校验

1. 读取当前项目适用的 `AGENTS.md`、`CLAUDE.md` 和项目规则。
2. 定位 `cadence/knowledge-base/manifest.yaml`，确认 `schema_version: "3.0"`。
3. 读取 Manifest 中的工程范围、领域状态、用户输入来源和 `baseline_commit`。
4. 获取当前分支、提交和工作区状态，仅用于识别基线漂移。

Manifest 缺失或 Schema 不是 `3.0` 时停止，报告缺失路径或版本，并引导执行 `knowledge-base-bootstrap`。不得回退为普通全仓分析。

### 1. 识别任务画像

固定画像只有七类：需求澄清、Design、Plan、Coding、Testing、Review、Debug。选择一个主画像，可附加最多两个辅助画像。

从用户请求提取：业务词、已知页面/API/服务/表/配置/文件/错误信息、明确范围和期望交付物。期望交付物只决定上下文深度，不由本 Skill 执行。

### 2. 双轨种子获取

并行建立两个种子集合：

```text
KnowledgeBase：README → 领域索引 → 稳定 ID → 关系矩阵与证据索引
当前实现：用户点名对象 → 文件/符号/路由/SQL/配置/测试入口
```

优先使用用户明确点名对象；其次使用业务术语和稳定 ID。不得只读 KnowledgeBase 后停止，也不得只扫源码后忽略业务语义。

### 3. 一跳关系扩展

围绕种子读取直接关系：

```text
ROUTE → PAGE → API → SERVICE/MODULE → TABLE/MIDDLEWARE/EXTERNAL
TEST → 被测符号 → Fixture/Mock/配置
```

默认只扩展一跳。画像必需字段仍缺关键证据时再扩展下一跳；公共工具类、通用异常、日志和框架基础设施不无限传播。

### 4. 画像定向深化

按 `references/task-profiles.md` 补齐主画像和辅助画像的专属上下文。某一方向信息已经足以支持下游判断时立即停止该方向读取。

### 5. 双轨证据对照

每项关键结论必须同时记录 KnowledgeBase 证据和当前源码、DDL 或配置证据。证据状态只使用：

- `一致`
- `KnowledgeBase 缺失`
- `源码缺失`
- `基线漂移`
- `来源冲突`
- `待确认`

当前行为以当前提交中的可验证实现描述；业务语义和预期保留 KnowledgeBase 与用户资料定义。两侧不一致时写明差异和任务影响，不静默覆盖任一方。

### 6. 停止并输出

同时满足以下条件后停止读取：

- 任务边界和目标实体已确定。
- 入口、直接依赖和主要影响面已覆盖。
- 主辅画像必需字段已有可定位证据。
- 关键冲突、漂移和缺口已经显式记录。
- 继续扩展只会进入公共基础设施或无关业务。

停止读取表示上下文收集完成，不表示用户原始任务结束。输出上下文包后，将控制权交回当前代理，由其继续原始任务或使用其他适用 Skill；不得因为本 Skill 自动命中而吞掉 Design、Plan、Coding、Testing、Review 或 Debug 请求。

## 异常处理

| 情况 | 处理 |
|------|------|
| Manifest 声明领域不适用 | 不读取该领域，记录范围限制 |
| 当前提交晚于基线 | 比较任务相关文件和符号；发生变化才标记 `基线漂移`，无相关变化只记录基线较旧 |
| KnowledgeBase 文档缺失 | 继续读取相关实现，标记 `KnowledgeBase 缺失` |
| 源码位置失效 | 通过稳定 ID、关系矩阵和文本检索定位候选 |
| 同名实体无法唯一匹配 | 列出候选并询问，不按名称猜测 |
| 来源冲突会改变任务方向 | 保留双侧证据并询问用户 |
| 请求超出 Manifest 范围 | 停止越界读取，说明需要新的用户授权范围 |
| 敏感配置 | 只记录配置键、用途和值类型，值写为 `<redacted>` |

需要结构化提问时，Claude Code 使用 `AskUserQuestion`；Codex 工具可用时使用 `request_user_input`；工具不可用时使用普通文本提问。范围和实体已经明确时不得重复确认。

## 工具策略

- 大范围关系和影响面优先使用可用 CodeGraph。
- 精确类、方法、路由和配置结构优先使用 `ast-grep outline`。
- 已知名称、稳定 ID、路径和配置键使用 `rg` 与定向读取。
- 结构化工具不可用时降级为文本检索，但不得扩大为无边界扫描。

## 输出契约

输出固定包含十节：

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

就绪状态只使用：

- `就绪`：关键上下文完整，没有影响方向的未决冲突。
- `有条件就绪`：存在非阻断缺口，可以在明确假设下继续。
- `阻断`：关键规则缺失、目标无法确定或冲突会改变任务方向。

用户明确要求复用、交接或审计时，按模板保存到：

```text
cadence/knowledge-base/task-contexts/
YYYY-MM-DD_任务上下文_任务名称_v1.0.md
```

任务快照记录 Manifest 基线和当前提交，但不加入 Manifest，也不反向更新领域知识库。

## 完成条件

- 已识别一个主画像和不超过两个辅助画像。
- KnowledgeBase 与当前实现均实际参与证据收集。
- 所有关键结论具有稳定 ID 或精确文件、符号位置。
- 关系扩展停在与任务直接相关的最小充分范围。
- 冲突、漂移、缺口和就绪状态明确。
- 已将上下文交回调用方继续原始任务，或用户明确只要求上下文。
- 本 Skill 未绑定、调用或修改 `cadence-workflow`。
