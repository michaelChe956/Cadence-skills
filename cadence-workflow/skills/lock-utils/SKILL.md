---
name: lock-utils
description: Use when performing concurrent write operations on shared resources to prevent data corruption
---

# Lock Utils - 并发控制工具

## 概述

**核心原则**：通过锁机制防止并发写入导致的数据损坏，确保同一时间只有一个任务可以修改共享资源。

**关键洞察**：Serena memory 不支持原子性操作，需要通过锁机制实现并发控制。

## 何时使用

**使用场景**：
- ✅ 保存 Checkpoint 前获取锁
- ✅ 更新 Progress 记录前获取锁
- ✅ 更新索引数据前获取锁
- ✅ 任何需要并发保护的写入操作

**不使用场景**：
- ❌ 只读操作（不需要锁）
- ❌ 单用户、单会话、顺序操作场景
- ❌ 不涉及共享资源的操作

## 锁数据模型

### Lock 结构

```yaml
Lock:
  resource: string          # 资源标识(如: progress-user-auth)
  locked: boolean           # 是否锁定
  locked_by: string         # 锁持有者(如: checkpoint-brainstorm)
  locked_at: timestamp      # 锁定时间(ISO 8601)
  ttl: number               # 锁超时时间(秒)
```

### 存储位置

- **格式**：`lock-{resource_name}`
- **示例**：`lock-progress-user-auth`

### 示例数据

```yaml
lock-progress-user-auth:
  resource: "progress-user-auth"
  locked: true
  locked_by: "checkpoint-brainstorm"
  locked_at: "2026-03-06T14:30:00Z"
  ttl: 300  # 5分钟
```

## 锁操作流程

### 1. 获取锁 (Acquire Lock)

**用途**：在执行写入操作前获取资源锁，防止并发冲突。

#### Step 1: 检查锁状态

**读取锁数据**：
```
使用 Serena read_memory 工具
Memory名称: "lock-{resource_name}"
```

**判断逻辑**：
```markdown
IF 锁不存在 (返回 null):
  → 锁不存在,可以获取
  → 跳转到 Step 3

IF 锁存在但 locked == false:
  → 锁未激活,可以获取
  → 跳转到 Step 3

IF 锁存在且 locked == true:
  → 锁已激活,需要检查超时
  → 跳转到 Step 2
```

#### Step 2: 检查锁是否超时

**计算超时**：
```markdown
获取当前时间戳:
  current_time = get_current_timestamp()

计算锁过期时间:
  lock_expiry_time = lock_data.locked_at + lock_data.ttl

判断是否超时:
  IF current_time > lock_expiry_time:
    → 锁已超时,可以强制获取
    → 跳转到 Step 3
  ELSE:
    → 锁未超时,资源被占用
    → 返回失败
```

**工具使用**：
- 使用 Bash 工具获取当前时间戳
  - Linux/macOS: `date -u +"%Y-%m-%dT%H:%M:%SZ"`
  - 解析 ISO 8601 时间戳并计算差值

#### Step 3: 获取锁

**创建锁数据**：
```yaml
new_lock_data:
  resource: "{resource_name}"
  locked: true
  locked_by: "{task_id}"
  locked_at: "{current_timestamp}"
  ttl: 300  # 5分钟
```

**保存锁数据**：
```
使用 Serena write_memory 工具
Memory名称: "lock-{resource_name}"
数据: new_lock_data
```

#### Step 4: 验证锁

**读取并验证**：
```markdown
读取刚保存的锁:
  verify_lock = read_memory("lock-{resource_name}")

验证持有者:
  IF verify_lock.locked_by == "{task_id}":
    → 锁获取成功
    → 返回成功
  ELSE:
    → 锁获取失败(被其他任务抢占)
    → 返回失败
```

**🔴 重要**：必须执行验证步骤，防止并发场景下的竞争条件。

### 2. 释放锁 (Release Lock)

**用途**：在完成写入操作后释放资源锁，允许其他任务访问。

#### Step 1: 检查锁状态

**读取锁数据**：
```
使用 Serena read_memory 工具
Memory名称: "lock-{resource_name}"
```

**判断逻辑**：
```markdown
IF 锁不存在 (返回 null):
  → 锁不存在,无需释放
  → 返回成功

IF 锁存在:
  → 继续验证持有者
```

#### Step 2: 验证持有者

**验证权限**：
```markdown
IF lock_data.locked_by != "{task_id}":
  → 不是锁的持有者
  → 无权释放
  → 记录警告日志
  → 返回失败

IF lock_data.locked_by == "{task_id}":
  → 是锁的持有者
  → 可以释放
  → 继续下一步
```

**🔴 重要**：只有锁的持有者才能释放锁，防止误释放。

#### Step 3: 释放锁

**更新锁数据**：
```yaml
new_lock_data:
  resource: "{resource_name}"
  locked: false
  locked_by: null
  locked_at: null
  ttl: 0
```

**保存锁数据**：
```
使用 Serena write_memory 工具
Memory名称: "lock-{resource_name}"
数据: new_lock_data
```

#### Step 4: 验证释放

**读取并验证**：
```markdown
读取刚更新的锁:
  verify_lock = read_memory("lock-{resource_name}")

验证释放:
  IF verify_lock.locked == false:
    → 锁释放成功
    → 返回成功
  ELSE:
    → 锁释放失败
    → 记录错误日志
    → 返回失败
```

### 3. 检查锁超时 (Is Lock Expired)

**用途**：检查锁是否超时，用于决定是否强制获取锁。

#### 执行步骤

**Step 1: 检查锁状态**
```markdown
IF lock_data.locked == false:
  → 锁未激活,不算超时
  → 返回 false
```

**Step 2: 计算超时**
```markdown
获取当前时间戳:
  current_time = get_current_timestamp()

计算锁过期时间:
  lock_expiry_time = lock_data.locked_at + lock_data.ttl

判断是否超时:
  IF current_time > lock_expiry_time:
    → 锁已超时
    → 返回 true
  ELSE:
    → 锁未超时
    → 返回 false
```

## 锁超时策略

### 推荐TTL设置

| 资源类型 | 推荐TTL | 说明 |
|---------|---------|------|
| **Progress** | 300秒(5分钟) | 写入操作较快 |
| **Checkpoint** | 300秒(5分钟) | 写入操作较快 |
| **Session Summary** | 600秒(10分钟) | 可能包含大量数据 |

### 为什么需要超时？

1. **防止死锁**：任务崩溃后锁未释放
2. **允许恢复**：超时后其他任务可以获取锁
3. **避免阻塞**：长时间运行的任务不会永久阻塞其他任务

## 完整使用示例

### 场景：保存 Checkpoint

```markdown
## 保存 Checkpoint 的完整流程

### Step 1: 准备参数
resource_name = "progress-user-auth"
task_id = "checkpoint-brainstorm"
ttl = 300  # 5分钟

### Step 2: 获取锁
调用 lock-utils skill (获取锁)

IF 获取锁失败:
  → 记录错误日志
  → 返回失败

### Step 3: 执行关键操作
try:
  3.1 保存 Checkpoint
      - 生成 Checkpoint ID
      - write_memory(checkpoint_id, checkpoint_data)

  3.2 更新 Progress
      - progress_data = read_memory("progress-user-auth")
      - 更新 progress_data.phases[phase].status = "completed"
      - write_memory("progress-user-auth", progress_data)

  3.3 更新索引
      - update_checkpoints_index(project_id, checkpoint_id)

  → 所有操作成功
  → 返回成功

except 操作失败:
  → 记录错误日志
  → 返回失败

### Step 4: 释放锁 (finally)
调用 lock-utils skill (释放锁)

注意：无论操作成功或失败,都必须释放锁
```

## 快速参考

### 获取锁流程

| 步骤 | 操作 | 工具 | 说明 |
|------|------|------|------|
| 1 | 检查锁状态 | Serena read_memory | 读取 lock-{resource} |
| 2 | 检查超时 | Bash date | 计算是否超时 |
| 3 | 获取锁 | Serena write_memory | 写入新锁数据 |
| 4 | 验证锁 | Serena read_memory | 确认获取成功 |

### 释放锁流程

| 步骤 | 操作 | 工具 | 说明 |
|------|------|------|------|
| 1 | 检查锁状态 | Serena read_memory | 读取 lock-{resource} |
| 2 | 验证持有者 | 比较 locked_by | 确认有权释放 |
| 3 | 释放锁 | Serena write_memory | 更新锁状态 |
| 4 | 验证释放 | Serena read_memory | 确认释放成功 |

### 锁状态判断

| 锁状态 | 条件 | 操作 |
|--------|------|------|
| **不存在** | read_memory 返回 null | 可以获取 |
| **未激活** | locked == false | 可以获取 |
| **已超时** | current_time > locked_at + ttl | 可以强制获取 |
| **被占用** | locked == true 且未超时 | 等待或失败 |

## 常见错误

### ❌ 错误1：忘记验证锁

**问题**：获取锁后不验证，导致并发竞争

```markdown
# ❌ 错误做法
write_memory("lock-{resource}", lock_data)
# 没有验证，直接继续操作

# ✅ 正确做法
write_memory("lock-{resource}", lock_data)
verify_lock = read_memory("lock-{resource}")
IF verify_lock.locked_by != task_id:
  → 锁被其他任务抢占
  → 返回失败
```

### ❌ 错误2：忘记释放锁

**问题**：操作完成后不释放锁，导致死锁

```markdown
# ❌ 错误做法
acquire_lock(...)
执行操作
# 忘记释放锁

# ✅ 正确做法
acquire_lock(...)
try:
  执行操作
finally:
  release_lock(...)  # 必须释放
```

### ❌ 错误3：释放不属于自己的锁

**问题**：释放其他任务持有的锁

```markdown
# ❌ 错误做法
lock_data = read_memory("lock-{resource}")
write_memory("lock-{resource}", {locked: false})
# 没有验证持有者，可能释放了其他任务的锁

# ✅ 正确做法
lock_data = read_memory("lock-{resource}")
IF lock_data.locked_by != task_id:
  → 无权释放
  → 返回失败
write_memory("lock-{resource}", {locked: false})
```

### ❌ 错误4：TTL设置过短

**问题**：锁超时时间太短，操作未完成就超时

```markdown
# ❌ 错误做法
ttl = 30  # 30秒太短

# ✅ 正确做法
ttl = 300  # 5分钟，足够完成操作
```

## Red Flags

**🔴 STOP if**:
- 锁获取失败 → 不要继续执行写入操作
- 锁验证失败 → 不要继续执行写入操作
- 不是锁的持有者 → 不要尝试释放锁
- 操作异常失败 → 确保在 finally 中释放锁

## 测试清单

### 单元测试

- [ ] 锁不存在时可以获取
- [ ] 锁未激活时可以获取
- [ ] 锁已超时时可以强制获取
- [ ] 锁被占用时获取失败
- [ ] 锁验证失败时返回失败
- [ ] 只有持有者可以释放锁
- [ ] 释放锁后状态变为未激活
- [ ] TTL计算正确

### 集成测试

- [ ] 获取锁 → 执行操作 → 释放锁（正常流程）
- [ ] 获取锁 → 操作失败 → 释放锁（异常流程）
- [ ] 两个任务并发获取同一锁（竞争测试）
- [ ] 锁超时后可以强制获取

### 并发测试

- [ ] 多个任务同时获取锁（只有一个成功）
- [ ] 获取锁后其他任务等待
- [ ] 释放锁后其他任务可以获取
- [ ] 锁超时后自动释放

## 实施注意事项

### 与现有Skills集成

**需要使用锁的Skills**：
1. **checkpoint skill** - 保存Checkpoint时获取锁
2. **status skill** - 读取Progress时可能需要考虑锁（只读操作通常不需要）
3. **resume skill** - 恢复Progress时可能需要考虑锁

### 性能考虑

- **锁粒度**：锁的资源范围要合理（如：`progress-{project_id}`）
- **锁持有时间**：尽量缩短锁持有时间
- **锁超时时间**：根据操作复杂度设置合理的TTL

### 错误处理

- **锁获取失败**：记录日志，返回明确的错误信息
- **锁释放失败**：记录错误日志，但不影响主流程
- **锁验证失败**：立即停止操作，释放锁（如果已获取）

## 相关文档

- **设计文档**：`cadence/docs/2026-03-05_设计文档_可靠性保障系统_v1.0.md`
- **实施计划**：`cadence/plans/2026-03-04_计划文档_项目任务追踪优化_v1.0.md`
- **相关Skills**：
  - checkpoint skill - 使用锁保护Checkpoint保存
  - status skill - 读取Progress数据
  - resume skill - 恢复Progress数据

---

**Skill创建日期**: 2026-03-06
**Skill版本**: v1.0
**创建者**: Claude Sonnet 4.6
**状态**: ✅ 已完成
