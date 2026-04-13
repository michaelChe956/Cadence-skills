# exploration-flow Skill

## 概述

`exploration-flow` 是探索流程 Skill，包含 4 个节点 + 迭代，适用于新技术验证、技术选型和创新功能。

## 如何单独使用

### 命令调用

```bash
/exploration-flow
```

### 自动触发

当检测到以下场景时自动触发：
- 技术调研
- 技术选型
- POC（概念验证）
- 创新功能探索

## 流程节点

```
1. Brainstorm (需求探索)
   ↓
2. Analyze (存量分析)
   ↓
3. Git Worktrees (创建隔离环境)
   ↓
4. Subagent Development (原型开发 + 测试)
   ↓
   评估阶段 → 4 种结局：
   - ✅ 结局1: 转标准流程 - 功能可行 + 需要正式实现
   - 🔄 结局2: 继续探索 - 功能可行但需要调整
   - 📚 结局3: 技术储备完成 - 功能可行但暂不需要
   - ❌ 结局4: 记录教训 - 功能不可行
```

## 具体使用案例

### 案例 1：技术选型 - GraphQL vs REST

**用户输入**：
```
我们应该使用 GraphQL 还是 REST？
```

**执行流程**：

#### 1️⃣ Brainstorm（需求探索）
```
理解目标：
- 新 API 项目
- 需要支持多客户端（Web、移动端）
- 数据关系复杂
- 需要灵活的查询

探索选项：
- GraphQL：灵活查询、类型安全、单端点
- REST：简单、成熟、工具丰富
- tRPC：类型安全、自动类型推导
- gRPC：高性能、强类型、双向流

建议：GraphQL
理由：
- 复杂数据关系适合 GraphQL
- 多客户端可按需查询
- 类型安全减少错误

保存文档：.claude/docs/2026-03-02_探索PRD_GraphQL技术选型_v1.0.md
```

**用户确认**：✅ 继续下一步

#### 2️⃣ Analyze（存量分析）
```
分析现有代码：

发现：
- ✅ 已有 REST API（可参考）
- ✅ 已有数据库模型
- ❌ 缺少 GraphQL Schema
- ❌ 缺少 GraphQL 服务器

关键技术点：
- GraphQL 服务器选型：Apollo Server
- Schema 设计：User, Post 类型
- 数据库：PostgreSQL + Prisma

保存文档：.claude/analysis/2026-03-02_简化分析_GraphQL技术分析_v1.0.md
```

**用户确认**：✅ 继续下一步

#### 3️⃣ Git Worktrees（创建隔离环境）
```
创建 POC 环境：

Worktree 信息：
- 位置：../project-poc-graphql
- 分支：poc/graphql-vs-rest
- 测试：✅ 基础测试通过

是否确认环境就绪？
用户：✅ 确认
```

#### 4️⃣ Subagent Development（原型开发）
```
启动原型开发：

POC 目标：
- 验证 GraphQL 基础功能
- 实现简单的 Query（users, posts）
- 测试性能和开发体验

开发结果：
- ✅ Apollo Server 设置完成
- ✅ 基础 Schema 定义完成
- ✅ 简单查询实现完成
- ⚠️ 性能测试：5个并发用户，延迟<100ms

是否确认原型完成？
用户：✅ 确认
```

#### 5️⃣ 评估阶段（选择结局）
```
探索评估：

1. 功能是否可行？ ✅ 是
2. 是否需要正式实现？ ✅ 是
3. 是否有技术价值？ ✅ 是

建议结局：结局1 - 转标准流程

后续动作：
1. 清理 POC 代码（归档到 poc-archive/graphql-vs-rest）
2. 生成 POC 报告
3. 从 Design 节点开始正式实现

是否现在开始技术设计？
用户：✅ 是

→ 调用 design skill，进入完整流程
```
```
POC 任务：

Task 1: 设置 Apollo Server（15分钟）
Task 2: 定义 GraphQL Schema（20分钟）
Task 3: 实现基本 Query（30分钟）
Task 4: 连接数据库（20分钟）
Task 5: 测试查询（15分钟）

总计：约 2 小时

## 关键特性

### 1. 允许失败和迭代

探索流程允许失败，可以从任何节点回到之前的节点。

### 2. 4 种结局（评估阶段）

Subagent Development 完成后进入评估阶段，有 4 种结局：

- **✅ 结局1: 转标准流程** - 功能可行 + 需要正式实现
  - 清理 POC 代码
  - 从 Design 节点开始正式实现
  - 生成 POC 报告

- **🔄 结局2: 继续探索** - 功能可行但需要调整
  - 调整需求
  - 再次循环 Subagent Development
  - 保存迭代记录

- **📚 结局3: 技术储备完成** - 功能可行但暂不需要
  - 清理 POC 代码
  - 记录技术方案到 `.claude/docs/`
  - 生成技术储备文档

- **❌ 结局4: 记录教训** - 功能不可行
  - 清理 POC 代码
  - 记录失败原因和教训
  - 生成失败分析报告

### 3. 支持 POC

鼓励创建 POC（概念验证）来验证技术可行性。

### 4. 保守决策

如果探索发现技术不适合，可以随时放弃。

### 5. 原型质量要求较低

原型代码质量要求较低，但必须能验证核心想法。基础测试即可，不要求 ≥ 80% 覆盖率。

## 适用场景

### ✅ 适合 Exploration Flow

- 技术调研
- 技术选型
- POC（概念验证）
- 创新功能探索
- 不确定的技术方案

### ❌ 不适合 Exploration Flow

- 明确的功能开发 → 使用 Full Flow 或 Quick Flow
- 紧急修复 → 使用 Quick Flow

## 时间预估

| 节点 | 预估时间 |
|------|---------|
| Brainstorm | 20-40 分钟 |
| Analyze | 10-20 分钟 |
| Git Worktrees | 5 分钟 |
| Subagent Development | 30-60 分钟（每次迭代）|
| 评估阶段 | 5-10 分钟 |
| **总计（1次迭代）** | **70-135 分钟** |

注：可能需要多次迭代（结局2）

## 迭代模式

### 结局2: 继续探索（迭代）

```
Subagent Development → (评估) → 需要调整 → 调整需求 → 再次 Subagent Development
```

### 结局4: 记录教训（放弃）

```
Brainstorm → Analyze → Git Worktrees → Subagent Development → (评估) → 功能不可行 → 记录教训
```

### 结局1: 转标准流程

```
探索成功 → 清理 POC 代码 → 从 Design 开始正式实现（进入 Full Flow）
```

## 最佳实践

### 1. 创建 POC

不要只停留在理论分析，创建 POC 验证技术可行性。

### 2. 保持开放心态

探索流程允许失败，不要过早决策。

### 3. 充分调研

利用 Analyze 阶段充分调研现有方案和技术栈。

### 4. 及时止损

如果发现技术不适合，及时放弃，不要强行继续。

## 相关 Skills

- **full-flow** - 完整流程（8 节点）
- **quick-flow** - 快速流程（4 节点）
- **brainstorming** - 需求探索
- **analyze** - 存量分析
- **using-git-worktrees** - 环境隔离
- **subagent-development** - 代码实现
