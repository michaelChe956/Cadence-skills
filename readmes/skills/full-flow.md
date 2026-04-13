# full-flow Skill

## 概述

`full-flow` 是完整流程 Skill，包含 8 个核心节点，适用于复杂功能开发、团队协作项目和企业级应用。

## 如何单独使用

### 命令调用

```bash
/full-flow
```

### 自动触发

当检测到以下场景时自动触发：
- 复杂功能开发（预估 >2 小时）
- 企业级项目
- 需要完整审计追踪的任务

## 流程节点

```
1. Brainstorm (需求探索)
   ↓
2. Analyze (存量分析)
   ↓
3. Requirement (需求分析)
   ↓
4. Design (技术设计)
   ↓
5. Design Review (设计审查)
   ↓
6. Plan (实现计划)
   ↓
7. Git Worktrees (创建隔离环境)
   ↓
8. Subagent Development (代码实现 + 单元测试)
```

## 具体使用案例

### 案例 1：电商系统购物车功能

**用户输入**：
```
帮我实现购物车功能
```

**执行流程**：

#### 1️⃣ Brainstorm（需求探索）
```
理解需求：
- 购物车基本功能：添加、删除、修改数量
- 持久化：跨设备同步
- 库存检查：实时库存验证
- 优惠计算：优惠券、促销活动

保存文档：.claude/designs/2026-03-02_需求文档_购物车功能_v1.0.md
```

**用户确认**：✅ 继续下一步

#### 2️⃣ Analyze（存量分析）
```
使用 Serena MCP 分析现有代码：

发现：
- ✅ 已有用户认证模块（可复用）
- ✅ 已有商品管理模块（可复用）
- ❌ 缺少购物车数据模型
- ❌ 缺少库存服务

建议：
- 复用现有认证和商品模块
- 新建购物车数据模型
- 集成第三方库存服务

保存文档：.claude/analysis/2026-03-02_分析报告_购物车存量分析_v1.0.md
```

**用户确认**：✅ 继续下一步

#### 3️⃣ Requirement（需求分析）
```
功能需求：
1. 添加商品到购物车
2. 删除购物车商品
3. 修改商品数量
4. 计算总价和优惠
5. 库存实时检查
6. 跨设备同步

非功能需求：
- 性能：响应时间 < 200ms
- 可用性：99.9%
- 并发：支持 1000 QPS

边界条件：
- 库存不足时的处理
- 商品下架时的处理
- 用户未登录时的处理

保存文档：.claude/docs/2026-03-02_需求文档_购物车功能详细_v1.0.md
```

**用户确认**：✅ 继续下一步

#### 4️⃣ Design（技术设计）
```
技术方案：
- 前端：React + Redux
- 后端：Node.js + Express
- 数据库：PostgreSQL
- 缓存：Redis
- 消息队列：RabbitMQ

数据模型：
- Cart（购物车）
- CartItem（购物车商品）
- Discount（优惠规则）

API 设计：
- POST /api/cart/items（添加商品）
- DELETE /api/cart/items/:id（删除商品）
- PUT /api/cart/items/:id（修改数量）
- GET /api/cart（获取购物车）

保存文档：.claude/designs/2026-03-02_技术方案_购物车功能_v1.0.md
```

**用户确认**：✅ 继续下一步

#### 5️⃣ Design Review（设计审查）
```
审查维度：

1. 功能完整性 ✅
   - 所有需求都有对应设计

2. 技术方案符合性 ✅
   - 符合项目技术栈规范

3. 边界条件处理 ✅
   - 库存不足、商品下架等都有处理

4. 测试覆盖率 ✅
   - 单元测试、集成测试、E2E 测试

审查结果：通过 ✅

保存文档：.claude/analysis/2026-03-02_审查报告_购物车设计审查_v1.0.md
```

**用户确认**：✅ 继续下一步

#### 6️⃣ Plan（实现计划）
```
任务分解：

Task 1: 创建数据模型（15分钟）
  - 创建 Cart 模型
  - 创建 CartItem 模型
  - 创建 Discount 模型
  - 验证：运行数据库迁移

Task 2: 实现购物车 API（30分钟）
  - POST /api/cart/items
  - DELETE /api/cart/items/:id
  - PUT /api/cart/items/:id
  - GET /api/cart
  - 验证：API 测试通过

Task 3: 实现库存检查（20分钟）
  - 集成库存服务
  - 实时库存验证
  - 验证：库存检查测试通过

Task 4: 实现优惠计算（20分钟）
  - 优惠券逻辑
  - 促销活动逻辑
  - 验证：优惠计算测试通过

Task 5: 实现前端组件（40分钟）
  - Cart 组件
  - CartItem 组件
  - 总价计算组件
  - 验证：E2E 测试通过

保存文档：.claude/plans/2026-03-02_实现计划_购物车功能_v1.0.md
```

**用户确认**：✅ 继续下一步

#### 7️⃣ Git Worktrees（创建隔离环境）
```
创建新 Worktree：
- 分支：feature/shopping-cart
- 目录：../project-shopping-cart
- 状态：干净的工作区

验证：
✅ 所有测试通过
✅ 工作区干净
✅ 可以开始开发
```

**用户确认**：✅ 继续下一步

#### 8️⃣ Subagent Development（代码实现）
```
启动 3 个 Subagent：

Implementer (8.1) - 代码实现
  - 按照 Plan 实现 5 个任务
  - TDD 强制执行
  - 测试覆盖率 ≥ 80%

Spec Reviewer (8.2) - 规范审查
  - 验证功能完整性
  - 验证技术方案符合性
  - 验证边界条件处理
  - 验证测试覆盖率

Code Quality Reviewer (8.3) - 代码质量审查
  - 代码规范
  - 代码质量
  - 安全性
  - 性能
  - 可维护性

两阶段审查：
第一阶段：Spec Review ✅ 通过
第二阶段：Code Quality Review ✅ 通过

最终结果：
✅ 所有任务完成
✅ 所有测试通过
✅ 测试覆盖率：85%
✅ 代码质量：A 级
```

**用户确认**：✅ 完成开发

## 关键特性

### 1. 每个节点完成后人工确认

确保每个阶段都符合预期，避免后期返工。

### 2. 支持断点续传

每个节点完成后自动创建检查点，可以随时恢复。

```bash
/status    # 查看当前进度
/resume    # 恢复进度
/checkpoint # 创建检查点
```

### 3. 两阶段审查

- **Spec Reviewer**: 验证规范符合性（4 个维度）
- **Code Quality Reviewer**: 验证代码质量（5 个维度）

### 4. TDD 强制执行

测试覆盖率 ≥ 80%，未达标不通过审查。

## 适用场景

### ✅ 适合 Full Flow

- 复杂功能开发（预估 >2 小时）
- 企业级项目
- 团队协作项目
- 需要完整审计追踪
- 高风险功能

### ❌ 不适合 Full Flow

- 简单 Bug 修复 → 使用 Quick Flow
- 快速原型验证 → 使用 Quick Flow
- 技术调研 → 使用 Exploration Flow

## 时间预估

| 节点 | 预估时间 |
|------|---------|
| Brainstorm | 30-60 分钟 |
| Analyze | 30-60 分钟 |
| Requirement | 60-90 分钟 |
| Design | 90-120 分钟 |
| Design Review | 30-60 分钟 |
| Plan | 60-90 分钟 |
| Git Worktrees | 5-10 分钟 |
| Subagent Development | 2-8 小时 |
| **总计** | **6-14 小时** |

## 最佳实践

### 1. 不要跳过节点

每个节点都有其价值，跳过会增加后期返工风险。

### 2. 充分利用审查

Design Review 可以发现设计问题，不要视为形式。

### 3. 保持 Plan 的粒度

每个任务 2-5 分钟，太大会难以跟踪进度。

### 4. 使用进度追踪

定期使用 `/status` 查看进度，使用 `/checkpoint` 创建检查点。

## 相关 Skills

- **quick-flow** - 快速流程（4 节点）
- **exploration-flow** - 探索流程（4 节点 + 迭代）
- **brainstorming** - 需求探索
- **analyze** - 存量分析
- **requirement** - 需求分析
- **design** - 技术设计
- **design-review** - 设计审查
- **plan** - 实现计划
- **using-git-worktrees** - 环境隔离
- **subagent-development** - 代码实现

## 进度管理

### 查看进度

```bash
/status
```

输出示例：
```
当前流程：Full Flow
当前节点：4/8 (Design)
已完成：Brainstorm ✅, Analyze ✅, Requirement ✅
当前任务：技术设计
下一步：Design Review
```

### 恢复进度

```bash
/resume
```

### 创建检查点

```bash
/checkpoint
```

## 常见问题

### Q: 可以跳过 Design Review 吗？

A: 不建议。Design Review 可以发现设计问题，避免后期返工。

### Q: 如果某个节点不通过怎么办？

A: 回到上一个节点重新设计或修改。例如，Design Review 不通过可以回到 Design 重新设计。

### Q: 可以在中间退出吗？

A: 可以。使用 `/checkpoint` 创建检查点，下次使用 `/resume` 恢复。
