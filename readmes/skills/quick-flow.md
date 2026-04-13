# quick-flow Skill

## 概述

`quick-flow` 是快速流程 Skill，包含 4 个核心节点，适用于简单功能开发、原型验证和 Bug 修复。

## 如何单独使用

### 命令调用

```bash
/quick-flow
```

### 自动触发

当检测到以下场景时自动触发：
- 简单功能开发（预估 <2 小时）
- Bug 修复
- 快速原型验证

## 流程节点

```
1. Requirement (需求分析)
   ↓
2. Plan (实现计划)
   ↓
3. Git Worktrees (创建隔离环境)
   ↓
4. Subagent Development (代码实现)
```

## 具体使用案例

### 案例 1：修复登录 Bug

**用户输入**：
```
修复登录页面的验证错误
```

**执行流程**：

#### 1️⃣ Requirement（需求分析）
```
问题描述：
- 登录时验证码校验失败
- 错误信息："验证码已过期"

预期行为：
- 验证码应在 5 分钟内有效
- 错误时应给出明确提示

根本原因：
- 验证码过期时间设置错误（1 分钟 → 5 分钟）

保存文档：cadence/docs/2026-03-02_Bug修复_登录验证码_v1.0.md
```

**用户确认**：✅ 继续下一步

#### 2️⃣ Plan（实现计划）
```
Task 1: 修改验证码过期时间（5分钟）
  - 修改 config.js
  - 验证码过期时间：1分钟 → 5分钟
  - 验证：单元测试通过

Task 2: 添加错误提示（5分钟）
  - 修改 login.js
  - 添加明确的错误提示
  - 验证：单元测试通过

Task 3: 更新测试用例（10分钟）
  - 更新验证码测试
  - 添加过期场景测试
  - 验证：所有测试通过
```

**用户确认**：✅ 继续下一步

#### 3️⃣ Git Worktrees（创建隔离环境）
```
创建新 Worktree：
- 分支：bugfix/login-captcha-expiry
- 目录：../project-bugfix-login
- 状态：干净的工作区

验证：✅ 可以开始修复
```

**用户确认**：✅ 继续下一步

#### 4️⃣ Subagent Development（代码实现）
```
Implementer 实现 3 个任务
Spec Reviewer 审查规范符合性
Code Quality Reviewer 审查代码质量

结果：
✅ 所有任务完成
✅ 所有测试通过
✅ 测试覆盖率：90%
✅ Bug 已修复
```

**用户确认**：✅ 完成修复

## 与 Full Flow 的区别

| 特性 | Full Flow | Quick Flow |
|------|-----------|-----------|
| **节点数** | 8 | 4 |
| **时间** | 6-14 小时 | 1-2 小时 |
| **探索阶段** | ✅ Brainstorm, Analyze | ❌ 跳过 |
| **审查阶段** | ✅ Design Review | ❌ 跳过 |
| **适用场景** | 复杂功能 | 简单功能、Bug 修复 |

## 适用场景

### ✅ 适合 Quick Flow

- 简单功能开发（预估 <2 小时）
- Bug 修复
- 快速原型验证
- 明确的小改动
- 紧急修复

### ❌ 不适合 Quick Flow

- 复杂功能开发 → 使用 Full Flow
- 需要探索需求 → 使用 Full Flow
- 技术调研 → 使用 Exploration Flow

## 时间预估

| 节点 | 预估时间 |
|------|---------|
| Requirement | 15-30 分钟 |
| Plan | 15-30 分钟 |
| Git Worktrees | 5 分钟 |
| Subagent Development | 30-90 分钟 |
| **总计** | **1-2 小时** |

## 最佳实践

### 1. 保持简单

Quick Flow 适用于简单任务，不要过度设计。

### 2. 仍然保持 TDD

即使快速开发，也要保持 TDD 实践，测试覆盖率 ≥ 80%。

### 3. 明确需求

虽然跳过探索阶段，但 Requirement 阶段仍然要明确需求。

### 4. 小任务优先

Quick Flow 最适合小任务，大任务使用 Full Flow。

## 相关 Skills

- **full-flow** - 完整流程（8 节点）
- **exploration-flow** - 探索流程（4 节点 + 迭代）
- **requirement** - 需求分析
- **plan** - 实现计划
- **using-git-worktrees** - 环境隔离
- **subagent-development** - 代码实现
