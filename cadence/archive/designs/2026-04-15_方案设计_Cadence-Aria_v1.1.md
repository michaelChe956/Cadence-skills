# Cadence-Aria 方案设计

## 概述

`Cadence-Aria` 定位为本仓库的第三个插件，对外以 `Claude Code plugin` 形式发布，对内提供一层正式的 `Codex runtime` 资源层，用于编排 `Claude Code -> Codex` 的完整任务流。

一期目标不是替代现有全部开发基础设施，而是建立一个以 `issue` 为最小闭环单位的多角色编排系统：

- `Claude Code` 负责 `intake / spec / plan / dispatch / review / test`
- `Codex` 负责 `exec / patch`
- `OpenSpec` 负责正式任务的边界与工件主线
- `superpowers` 负责规划、并行、验证、调试等方法层能力
- `Vibe Kanban` 只负责 `issue / workspace / worktree / 执行入口 / 状态展示`

一期必须做到：

1. 能从 `Vibe Kanban` 或 `Aria` 原生命令入口统一接收任务
2. 所有正式任务强制进入 `OpenSpec` 主线
3. `Claude Code` 能驱动 `Codex` 并行执行 `exec`
4. `Claude Code` 能独立完成 `review` 和 `test`
5. `Codex` 能根据 `review/test` 结果执行 `patch`
6. `Aria` 能输出结构化状态与闭环摘要

## 背景与目标

当前仓库已有两个插件：

- `cadence-init`
- `cadence-workflow`

本次设计明确要求：

- 新方案与当前项目已有两个插件的实现逻辑无关
- 不复用、不改写、不耦合已有两个插件的内部内容
- 在仓库中新增第三个独立插件：`Cadence-Aria`

目标是形成一个长期可扩展的编排方案，方向尽量参考 `oh-my-claudecode`，但不把 `Vibe Kanban` 扩展成重型编排器。

### 设计目标

1. 建立清晰的多角色协作模型
2. 让 `Claude Code` 成为唯一主编排入口
3. 让 `Codex` 成为正式执行端与修补端
4. 让 `OpenSpec` 成为正式任务强制主线
5. 让 `superpowers` 成为方法层依赖，而不是内嵌副本
6. 让 `Aria` 能接入 `Vibe Kanban`，也能脱离 `Vibe Kanban` 独立运行
7. 一期完成 `issue` 级闭环，同时预留 `branch / PR` 扩展接口

## 外部参考

本方案优先参考以下现成项目的思路：

| 参考项目 | 参考点 | 使用方式 |
|--------|--------|---------|
| `oh-my-claudecode` | teams-first 编排、工作流入口、长期 orchestration 方向 | 作为 `Aria` 编排风格参考 |
| `oh-my-codex` | `Codex runtime` 层、角色化执行、Codex 侧资源组织 | 作为 `Aria` 的 `Codex runtime` 结构参考 |
| `codex-plugin-cc` | `Claude Code -> Codex` 桥接入口 | 作为 Claude 侧触发 Codex 的桥接参考 |

参考链接：

- <https://github.com/Yeachan-Heo/oh-my-claudecode>
- <https://github.com/Yeachan-Heo/oh-my-codex>
- <https://github.com/openai/codex-plugin-cc>

### 不采纳的方向

以下方向不作为一期方案：

1. 把 `Vibe Kanban` 做成主编排器
2. 把 `OpenSpec` 或 `superpowers` 内嵌进 `Aria`
3. 做成 `Claude` 与 `Codex` 双发行物或双主入口
4. 在一期内引入 `merge / release / archive` 等交付后角色

## 总体架构

`Cadence-Aria` 采用四层结构：

1. `Vibe Kanban`：任务来源层
2. `OpenSpec`：正式任务 contract 层
3. `superpowers`：方法层
4. `Cadence-Aria`：编排控制层

### 分层职责

#### 1. Vibe Kanban

负责：

- `issue`
- `workspace`
- `worktree`
- 执行入口
- 状态展示

不负责：

- 子任务代理系统
- 多角色编排
- 审查与测试闭环
- 重型状态机

#### 2. OpenSpec

负责：

- 正式任务 change 身份
- `proposal / design / tasks`
- 范围边界
- 非目标
- 正式任务升级目标

不负责：

- 具体执行调度
- review/test/patch 运行时协议
- Claude/Codex 角色编排

#### 3. superpowers

负责：

- brainstorming
- writing-plans
- 并行调度方法
- 执行计划方法
- 代码审查方法
- 验证与调试方法

不负责：

- 正式任务立项
- change 身份
- 运行时状态机
- 工件归档事实

#### 4. Cadence-Aria

负责：

- 统一接收任务
- 驱动 `OpenSpec`
- 在合适状态调用 `superpowers`
- 驱动 `Claude -> Codex` 工作流
- 汇总 `review + test`
- 生成 `patch contract`
- 输出闭环结果

## 耦合原则

`Cadence-Aria` 必须与 `OpenSpec` 和 `superpowers` 保持协议级松耦合，不做代码级内嵌。

### 约束

1. `OpenSpec` 和 `superpowers` 都是前置 plugin
2. 两者必须安装在：
   - `Claude Code`
   - `Codex`
3. `Aria` 只依赖：
   - 能力存在
   - 入口可探测
   - 角色到能力映射可配置
4. `Aria` 不复制：
   - OpenSpec 工件体系
   - superpowers skill 内容

### 兼容策略

1. 采用最小依赖面
2. 优先做能力检测
3. 提供推荐版本范围，但不内嵌固定版本
4. 不兼容时必须明确报错能力缺失点

## 前置依赖与检查机制

`Cadence-Aria` 启动时必须先完成前置依赖检查，再允许进入正式流或 `fast-lane`。

### 前置依赖

1. `OpenSpec plugin`
2. `superpowers plugin`
3. `Codex` 可执行入口
4. Git worktree 能力

### 检查项

| 检查项 | 检查方式 | 失败处理 |
|------|---------|---------|
| `OpenSpec` 可用 | 探测命令入口与核心产物能力 | 阻断正式流，提示安装或修复 |
| `superpowers` 可用 | 探测关键 skill 是否存在 | 阻断对应角色流转 |
| `Codex` 可用 | 探测 `codex` 执行入口与最小调用能力 | 阻断 `aria:run` 与 `aria:fast` |
| Git worktree 可用 | 探测 Git 仓库状态与 worktree 能力 | 阻断并行执行，允许退化为串行 |

### 兼容声明

`Aria` 只声明“推荐版本范围”，不锁死具体版本。兼容性文档中至少要包含：

1. 推荐的 `OpenSpec` 版本范围
2. 推荐的 `superpowers` 版本范围
3. 当前测试通过的 `Codex` 版本范围
4. 当能力探测失败时的可解释错误信息

### 降级策略

1. `OpenSpec` 缺失：正式流阻断，`fast-lane` 仅允许低风险原生任务
2. `superpowers` 缺失：阻断对应角色；不允许伪造“兼容实现”
3. `Codex` 缺失：阻断 `exec / patch`
4. Git worktree 缺失：允许单任务串行模式，不允许并行模式

## 角色模型

一期采用 `8+1` 角色模型：

- 8 个正式业务角色
- 1 个特殊入口
- 1 个系统控制层

### 正式业务角色

1. `intake`
2. `spec`
3. `plan`
4. `dispatch`
5. `exec`
6. `review`
7. `test`
8. `patch`

### 特殊入口

9. `fast-lane`

### 系统控制层

- `orchestrator`

`orchestrator` 不是普通业务角色，而是 `Aria` 的控制面，负责状态流转、角色编排、结果汇总与外部同步。

### orchestrator 细化定义

`orchestrator` 应被实现为 `Aria runtime` 的核心调度逻辑，而不是单独暴露给用户的命令或业务角色。

它负责：

1. 驱动状态转换
2. 在状态节点调用相应角色
3. 维护任务上下文与运行时状态
4. 汇总 `review + test`
5. 生成 `dispatch contract` 与 `patch contract`
6. 处理超时、取消、失败与恢复
7. 同步 `Vibe Kanban` 与 Aria 内部状态

### orchestrator 调用关系

```text
user command
  -> orchestrator
    -> intake
    -> spec
    -> plan
    -> dispatch
    -> exec
    -> review + test
    -> patch
    -> closure
```

`orchestrator` 自身是有状态的。状态以任务为单位持久化，而不是全局单例内存态。

## 角色职责矩阵

| 角色 | 所属端 | 主要输入 | 主要输出 | 应使用的能力 | 不允许做的事 |
|---|---|---|---|---|---|
| `intake` | Claude Code | issue、命令入口、任务描述、Vibe Kanban 上下文 | 标准化任务卡、任务分类、风险初判、流转目标 | Aria 自身入口协议；必要时轻量 `brainstorming` | 直接规划、直接执行、跳过正式流判定 |
| `spec` | Claude Code | intake 任务卡、背景上下文、用户目标 | OpenSpec change、proposal、design、tasks 的最小完整集合 | `OpenSpec`；必要时 `brainstorming`、`openspec-explore` | 直接派发 exec；绕过 OpenSpec 把正式任务送去执行 |
| `plan` | Claude Code | OpenSpec 工件、约束、非目标、验收目标 | 执行计划、依赖图、验收策略、质量门、并行候选 | `writing-plans`；辅用 `brainstorming`、`openspec-explore` | 直接调度 worker；擅自修改 OpenSpec 边界 |
| `dispatch` | Claude Code | 执行计划、OpenSpec tasks、依赖关系 | 执行队列、并行批次、ownership 切分、回收/重派策略 | `dispatching-parallel-agents`；辅用 `subagent-driven-development` | 重写 plan；自行放宽质量门；直接修代码 |
| `exec` | Codex | dispatch contract、任务边界、实现目标、局部验收标准 | 实现结果、变更说明、执行记录、自检结果 | `executing-plans`、`subagent-driven-development`；代码类任务可条件性用 `test-driven-development` | 修改 spec/plan；自行扩 scope；跳过回报直接宣告完成 |
| `review` | Claude Code | exec 结果、OpenSpec 边界、plan 验收标准 | 结构化 review 报告、问题级别、是否退回 patch | `requesting-code-review` | 直接改代码；替代 test；改动正式边界 |
| `test` | Claude Code | exec 结果、plan 验证策略、任务类型分级规则 | 验证报告、失败证据、通过/退回结论 | `verification-before-completion`；失败定位时辅用 `systematic-debugging` | 直接修复问题；替代 review；重写验收口径 |
| `patch` | Codex | review/test 报告、失败证据、原任务边界 | 修补结果、修补说明、重新提交验证 | `systematic-debugging`、`receiving-code-review`；代码类任务可条件性用 `test-driven-development` | 擅自改 spec/plan；借修补扩 scope；跳过复检 |
| `fast-lane` | 特殊入口 | 小修小补请求、低风险判定 | 轻量执行记录、完成摘要，或升级到正式流 | 轻量 planning + verification；必要时转正式 OpenSpec 流 | 处理高风险任务；长期绕过正式流 |

## 状态机与任务流转

### 状态持久化方案

一期建议采用“文件级运行时状态”方案，而不是仅依赖内存态。

状态存储位置建议为：

```text
cadence/cache/aria/
  tasks/
    <task-id>/
      state.yaml
      intake-card.md
      plan-brief.md
      dispatch-contract.yaml
      review-report.md
      test-report.md
      patch-contract.yaml
      verification-summary.md
      closure-summary.md
```

### 持久化原则

1. 一个任务一个目录
2. 一个状态文件 `state.yaml`
3. 运行时工件按轮次写入任务目录
4. 多任务之间完全隔离
5. 关闭 Claude Code 后可根据 `task-id` 恢复

### `state.yaml` 最小字段

```yaml
task_id: aria-20260415-001
source: vk | native
flow_type: formal | fast-lane
status: planned
current_round: 1
active_exec_units: []
review_status: pending
test_status: pending
patch_round: 0
created_at: "2026-04-15T10:00:00+08:00"
updated_at: "2026-04-15T10:30:00+08:00"
workspace_ref: ""
worktree_ref: ""
```

### 恢复机制

1. `aria:status` 可列出活跃任务与最后状态
2. `aria:run` 支持基于 `task-id` 继续执行
3. 当存在未完成任务时，`orchestrator` 优先提示恢复而不是重建
4. 若运行时工件与状态不一致，以状态文件为主，并报告损坏

### 正式任务通道

正式任务状态机如下：

`intake -> spec-required -> spec-approved -> planned -> dispatched -> executing -> review/testing -> patching -> verified -> done`

### 状态定义

| 状态 | 含义 |
|------|------|
| `intake` | 任务进入 Aria，由 `intake` 标准化与分类 |
| `spec-required` | 任务被判定为正式任务，必须进入 OpenSpec |
| `spec-approved` | OpenSpec 主线工件达到最小完整集合 |
| `planned` | Claude 完成执行计划、依赖图、验收策略与质量门定义 |
| `dispatched` | Claude 将计划转换为执行单元与并行/串行图 |
| `executing` | Codex `exec` 按派发协议执行 |
| `review/testing` | Claude `review` 与 `test` 并行执行并汇总 |
| `patching` | 因 review 或 test 失败进入修补循环 |
| `verified` | 当前任务满足既定质量门 |
| `done` | 输出闭环摘要并完成状态同步 |

### fast-lane 轻量通道

轻量状态机如下：

`intake -> fast-triage -> execute -> review/testing-lite -> done`

### 升级规则

当出现以下情况之一时，必须从 `fast-lane` 升级回正式任务通道：

1. 影响范围超过单模块
2. 需要新增设计决策
3. 需要并行拆分
4. 出现多轮 `patch`
5. 需要长期保留正式边界

## Codex 触发与执行机制

`Claude Code 驱动 Codex` 在一期中采用“`orchestrator` 生成执行协议，Claude 侧调用 Codex CLI 执行”的模式。

### 触发机制

1. `dispatch` 生成 `dispatch contract`
2. `orchestrator` 为每个执行单元创建独立工作目录上下文
3. `orchestrator` 调用 `Codex CLI`
4. `Codex` 读取对应 contract 后执行 `exec` 或 `patch`
5. 执行结果写回任务目录，再由 `orchestrator` 汇总

### 一期执行模型

1. 一个执行单元对应一个 `Codex` 运行实例
2. 并行执行通过多个独立 `Codex` 实例实现
3. `review` 与 `test` 在 Claude 侧并行进行

### 生命周期管理

`orchestrator` 负责：

1. 创建执行单元
2. 启动 Codex 进程
3. 监控退出状态
4. 记录 stdout/stderr 摘要
5. 处理超时与取消
6. 标记成功、失败、超时、取消状态

### 超时与失败

| 场景 | 处理方式 |
|------|---------|
| Codex 启动失败 | 标记执行单元失败，阻断依赖单元 |
| Codex 超时 | 标记超时，允许用户重试或取消 |
| Codex 异常退出 | 记录错误摘要，生成失败报告 |
| 执行结果缺失 | 视为失败，不进入 review/test |

### 不采纳的机制

一期不设计：

1. Codex 内部多任务并行
2. 基于远程 API 的执行编排
3. 由 Codex 自主管理其他 Codex 实例

## 并行模型与资源隔离

### 并行粒度

一期采用混合粒度：

1. 默认按 `OpenSpec tasks` 并行
2. 单个 task 过大时，再拆为模块 ownership 并行

### 隔离策略

1. 每个执行单元独占一个 worktree
2. 每个执行单元只写自己的 ownership 范围
3. 禁止多个执行单元同时修改同一文件
4. review/test 总是在汇总结果后执行，不与同一单元的 patch 并发

### 并行上限

一期建议默认上限：

1. `exec` 并行数默认 `2`
2. 可配置上限 `4`
3. 超出上限的单元进入等待队列

### 背压策略

1. 当 worktree 资源不足时，自动退回串行
2. 当同层任务存在文件 ownership 冲突时，强制串行
3. 当上游依赖失败时，阻断其下游执行

## fast-lane 准入标准

只有满足以下条件的任务，才允许进入 `fast-lane`：

1. 单文件或单一明确 ownership 范围
2. 不引入新设计决策
3. 不需要 OpenSpec 正式变更边界
4. 不需要并行拆分
5. 预计一轮 `exec + review/testing-lite` 可闭环
6. 不涉及跨模块接口修改
7. 不涉及状态迁移、数据迁移或发布策略

### 典型适用场景

1. 文档小改
2. 规则文案修正
3. 单点配置修补
4. 小范围脚本参数修复

### 禁止场景

1. 新增功能
2. 跨模块重构
3. 多文件联动改动
4. 需要多轮 patch 的复杂 bug
5. 需要正式设计评审的任务

### 执行主体

`fast-lane` 仍由 `orchestrator` 驱动，执行主体默认仍是 `Codex exec`，不是 Claude 直接代替执行。

## 运行时工件格式

一期建议采用“Markdown 承载说明 + YAML 承载结构字段”的混合格式。

### 格式选择

| 工件 | 格式 | 理由 |
|------|------|------|
| `task intake card` | Markdown + YAML front matter | 兼顾可读性与结构化 |
| `plan brief` | Markdown + YAML front matter | 需要人读，也需要解析 |
| `dispatch contract` | YAML | 面向执行契约，结构优先 |
| `review report` | Markdown + YAML front matter | 便于人读审查问题 |
| `test report` | Markdown + YAML front matter | 需要记录证据与结论 |
| `patch contract` | YAML | 面向修补契约，结构优先 |
| `verification summary` | Markdown | 面向汇总展示 |
| `closure summary` | Markdown | 面向最终闭环展示 |

### 工件引用关系

```text
task intake card
  -> plan brief
    -> dispatch contract
      -> exec result
        -> review report
        -> test report
          -> patch contract
            -> verification summary
              -> closure summary
```

### `dispatch contract` 最小字段

```yaml
task_id: aria-20260415-001
exec_unit_id: exec-01
parent_task: task-a
scope:
  files_allowed:
    - path/to/file.md
  files_blocked:
    - path/to/other.md
goal: ""
acceptance:
  - ""
dependencies: []
worktree_ref: ""
timeout_minutes: 30
retry_allowed: true
```

### `patch contract` 最小字段

```yaml
task_id: aria-20260415-001
patch_unit_id: patch-01
source_exec_unit: exec-01
based_on_dispatch_contract: dispatch-contract.yaml
must_fix:
  - review-issue-1
  - test-failure-1
must_not_change:
  - scope boundary
  - unrelated files
acceptance:
  - review issues resolved
  - tests pass
timeout_minutes: 20
```

### `dispatch contract` 与 `patch contract` 的关系

1. `patch contract` 继承原 `dispatch contract` 的边界
2. `patch contract` 只追加修补要求，不重写原任务目标
3. 若 patch 需要扩大边界，必须退回 `plan` 或升级正式流

## 质量门定义

质量门由 `plan` 角色定义，`orchestrator` 负责执行与校验。

### 质量门分层

1. 全局默认质量门
2. 任务类型质量门
3. 单任务覆盖性质量门

### 默认质量门

| 任务类型 | 质量门 |
|--------|-------|
| 文档/规则/配置 | 格式正确、引用有效、结构一致、必要 dry-run 通过 |
| 脚本/自动化 | 命令可运行、关键路径验证通过 |
| 代码类 | 变更符合边界、验证命令通过、必要测试通过 |

### 质量门归属

1. `plan` 定义任务级质量门
2. `review` 校验实现质量
3. `test` 校验验证质量
4. `orchestrator` 汇总是否满足“通过”条件

## 错误处理策略

### 错误分类

1. 前置依赖错误
2. OpenSpec 工件错误
3. Codex 执行错误
4. review/test 失败
5. 状态损坏错误
6. 用户取消

### 处理规则

| 错误类型 | 处理方式 |
|---------|---------|
| 前置依赖错误 | 阻断流转，给出明确缺失项 |
| OpenSpec 创建失败 | 回退到 `spec-required`，等待修复 |
| Codex 执行失败 | 标记执行单元失败，可重试 |
| review/test 失败 | 进入 `patching` |
| 状态损坏 | 停止继续执行，要求人工恢复或重建 |
| 用户取消 | 标记为 `cancelled`，保留当前工件 |

### patch 循环上限

为避免无限修补循环，一期建议：

1. 默认最多 `2` 轮 patch
2. 超过上限后必须退回 `plan`
3. 若边界已失效，则退回 `spec`

## 多任务上下文与命令行为

### 任务标识

每个任务必须有唯一 `task-id`。所有 `status`、`result`、恢复、取消操作都以 `task-id` 为主键。

### `aria:start`

`aria:start` 的结束状态固定为 `planned`。用户确认计划后，由 `aria:run --task-id <id>` 进入 `dispatched`。

### `aria:run`

`aria:run` 的第一步就是 `planned -> dispatched` 的转换，因此不单独暴露“确认计划”命令。

### `aria:status`

默认行为：

1. 若只有一个活跃任务，显示该任务
2. 若有多个活跃任务，先列出任务摘要
3. 可通过 `task-id` 精确查询

### `aria:result`

1. 默认显示最近完成的任务
2. 多任务场景必须支持 `task-id`
3. 未完成任务只能返回当前摘要，不能返回最终结果

## 验证与验收策略

### 一期最简验收场景

至少要验证以下 3 类场景：

1. `native intake -> formal flow -> done`
2. `vk intake -> formal flow -> patch -> verified`
3. `fast-lane -> done` 与 `fast-lane -> upgrade`

### 端到端验证目标

1. 状态能跨会话恢复
2. `dispatch contract` 与 `patch contract` 可被正确消费
3. review/test 报告能驱动 patch
4. 多任务状态不会串扰
5. 失败与取消可正确落盘

## 与现有目录规则的关系

`cadence-aria/` 作为插件源码目录，不属于 `cadence/` 文档产物目录。

### 边界

1. `cadence-aria/`：插件源码、命令、skill、runtime 模板
2. `cadence/`：设计文档、计划文档、评审文档、运行阶段输出文档

### 运行时状态目录

一期建议将运行时状态落在：

`cadence/cache/aria/`

原因：

1. 符合当前项目对 Cadence 产物的集中存储约束
2. 避免将运行时状态散落在插件源码目录
3. 便于后续清理、恢复与调试

## OpenSpec 与 superpowers 的结合方式

`Aria` 不是二选一使用 `OpenSpec` 与 `superpowers`，而是按职责层分工结合使用。

### 总原则

`OpenSpec` 定义正式任务是否合法、边界在哪里。  
`superpowers` 定义任务如何被高质量地思考、拆解、执行、验证。  
`Cadence-Aria` 负责在正确状态下编排两者。

### 角色到能力映射

| 角色 | OpenSpec 使用方式 | superpowers 使用方式 |
|------|-------------------|----------------------|
| `intake` | 不直接产出 OpenSpec 工件 | 必要时轻量 `brainstorming` |
| `spec` | 强制进入正式 change 主线 | `brainstorming`、`openspec-explore` 作为澄清补充 |
| `plan` | 读取 proposal/design/tasks | 主用 `writing-plans`，辅用 `brainstorming`、`openspec-explore` |
| `dispatch` | 读取 tasks 和 plan 输出 | 主用 `dispatching-parallel-agents`，辅用 `subagent-driven-development` |
| `exec` | 遵守既定边界，不改写工件 | 主用 `executing-plans`、`subagent-driven-development`；代码类任务可用 `test-driven-development` |
| `review` | 以 OpenSpec 边界为审查基线 | 主用 `requesting-code-review` |
| `test` | 以 plan 验证策略为验证基线 | 主用 `verification-before-completion`；失败定位可用 `systematic-debugging` |
| `patch` | 服从原边界，不改写工件 | 主用 `systematic-debugging`、`receiving-code-review`；代码类任务可用 `test-driven-development` |

## 目录结构建议

建议为 `Cadence-Aria` 建立独立目录：

```text
cadence-aria/
  commands/
  skills/
  references/
  templates/
  runtime/
    contracts/
    states/
    reports/
  codex/
    roles/
    prompts/
    workflows/
    templates/
  docs/
```

### 目录职责

| 目录 | 职责 |
|------|------|
| `commands/` | 用户可见的工作流入口 |
| `skills/` | Aria 自己的编排 skill |
| `references/` | 角色矩阵、兼容说明、依赖说明 |
| `templates/` | Aria 自有运行时工件模板 |
| `runtime/contracts/` | 角色输入输出协议 |
| `runtime/states/` | 状态机与升级规则 |
| `runtime/reports/` | 汇总与闭环摘要格式 |
| `codex/roles/` | Codex 侧角色定义 |
| `codex/prompts/` | Codex 侧角色提示与边界约束 |
| `codex/workflows/` | Codex 执行与修补流程 |
| `codex/templates/` | Codex 输出模板 |

## 工件边界

### OpenSpec 工件

`OpenSpec` 继续负责：

- `proposal`
- `design`
- `tasks`

这些工件是正式任务的源事实。

### Aria 运行时工件

`Aria` 应定义自己的运行时工件：

1. `task intake card`
2. `plan brief`
3. `dispatch contract`
4. `review report`
5. `test report`
6. `patch contract`
7. `verification summary`
8. `closure summary`

这些工件回答的是运行时问题，而不是正式边界问题。

## 命令面与最小可用工作流

一期命令面遵循以下原则：

1. 命令少而稳
2. 命令表达阶段，不直接暴露内部角色
3. 角色由 `Aria` 内部编排

### 一期命令集

| 命令 | 作用 |
|------|------|
| `aria:intake` | 统一任务入口，决定 formal 或 fast-lane 建议 |
| `aria:start` | 启动正式流，驱动 `intake -> spec -> plan` |
| `aria:run` | 启动或继续正式执行流，驱动 `dispatch -> exec -> review/test -> patch` |
| `aria:fast` | 启动小修小补轻量流 |
| `aria:status` | 查看当前任务状态、质量门状态、来源与阻塞点 |
| `aria:result` | 输出当前任务闭环摘要 |

### 正式流

1. 用户进入 `aria:intake`
2. `Aria` 判定任务类型
3. 正式任务进入 `aria:start`
4. `Aria` 驱动 `spec` 与 `plan`
5. 用户确认计划后执行 `aria:run`
6. `Aria` 驱动 `dispatch`
7. `Codex exec` 执行
8. `Claude review` 与 `Claude test` 并行
9. 失败则生成 `patch contract`
10. `Codex patch` 修补
11. 回到 `review/test`
12. 通过后生成 `verification summary` 与 `closure summary`

### fast-lane 流

1. 用户执行 `aria:fast`
2. `Aria` 做低风险判定
3. 通过后直接生成轻量执行协议
4. `Codex exec` 执行
5. `Claude review/testing-lite`
6. 成功后输出轻量闭环摘要
7. 超界则升级到正式流

## 与 Vibe Kanban 的关系

`Vibe Kanban` 在一期中只承担三类角色：

1. 任务来源
2. 工作区容器
3. 状态映射目标

为满足“既能接入，也能脱离”的目标，`Aria` 需要支持两类入口：

1. `vk intake`
2. `native intake`

两类入口统一汇入 `aria:intake`。

## 扩展接口预留

一期只完成 `issue` 级闭环，但必须预留：

1. `branch lifecycle`
2. `PR lifecycle`

建议通过以下位置预留扩展位：

- `runtime/contracts/branch-*.md`
- `runtime/contracts/pr-*.md`
- `runtime/states/extensions.md`

这样后续可向 `oh-my-claudecode` 风格的更完整 orchestrator 演进，而不推翻一期目录与状态机。

## 一期边界

### 一期纳入范围

1. `issue` 级任务闭环
2. `Claude -> Codex` 角色编排
3. `OpenSpec` 正式任务强制主线
4. `superpowers` 方法层编排
5. `Vibe Kanban` 接入与原生入口双支持
6. review/test/patch 闭环
7. 闭环结果摘要输出

### 一期不纳入范围

1. `merge`
2. `release`
3. `archive`
4. PR 自动化
5. 分支治理自动化
6. 把 `Vibe Kanban` 变成总控编排器
7. 内嵌或 fork `OpenSpec` 与 `superpowers`

## 成功标准

一期成功标准定义如下：

1. 能统一接收来自 `Vibe Kanban` 与原生命令的任务
2. 正式任务不能绕过 `OpenSpec`
3. `Claude Code` 能驱动 `Codex` 并行执行
4. `review` 与 `test` 能独立并行出报告
5. `patch` 能形成闭环修补循环
6. `Aria` 能输出结构化状态与结果摘要
7. `Aria` 与 `OpenSpec/superpowers` 保持松耦合升级关系

## 结论

`Cadence-Aria` 一期应被定义为：

- 一个新的 `Claude Code plugin`
- 带有正式 `Codex runtime` 资源层
- 以 `issue` 为最小闭环单位
- 强制正式任务进入 `OpenSpec`
- 在编排层显式调用 `superpowers`
- 接入但不吞并 `Vibe Kanban`
- 预留 `branch / PR` 扩展接口

这一定位能够同时满足：

1. 当前希望快速建立 Claude/Codex 协作工作流
2. 中期希望把 `Vibe Kanban` 的基础能力收拢进 `Aria`
3. 长期希望向 `oh-my-claudecode` 风格的 orchestration 方向演进
