---
name: transaction-utils
description: Use when performing multi-step write operations that need atomicity guarantees to ensure data consistency
---

# Transaction Utils - 事务性保证工具

## 概述

**核心原则**：通过"写入前备份+失败时回滚"机制确保多步操作的原子性，保证数据一致性。

**关键洞察**：大多数场景只需要备份+回滚，不需要完整的事务管理器。

## 何时使用

**使用场景**：
- ✅ 保存 Checkpoint（需要更新多个数据）
- ✅ 更新 Progress（可能涉及多个阶段）
- ✅ 批量更新索引（需要保证一致性）
- ✅ 任何需要原子性的多步写入操作

**不使用场景**：
- ❌ 单步操作（不需要事务）
- ❌ 只读操作（不需要备份）
- ❌ 可以容忍不一致的场景

## 事务模型

### 简化版事务（推荐）

**核心思想**：写入前备份 + 失败时回滚

```yaml
Backup-Before-Write Pattern:
  1. 备份现有数据
  2. 执行写入操作
  3. IF 失败 → 恢复备份
  4. IF 成功 → 清理备份（可选）
```

**备份数据结构**：
```yaml
Backup:
  resource_name: string       # 资源名称
  backup_data: object         # 备份数据
  backup_at: timestamp        # 备份时间
  operation: string           # 操作描述
```

**存储位置**：
- 临时备份：`backup-{resource_name}-{timestamp}`
- 示例：`backup-progress-user-auth-20260306-143000`

---

## 事务执行流程

### 1. 开始事务（Begin Transaction）

**用途**：准备执行多步操作，创建备份点。

#### Step 1: 识别关键资源

**列出所有将被修改的资源**：
```markdown
示例：保存 Checkpoint 操作

将被修改的资源:
  1. progress-{project_id} - Progress记录
  2. index-{project_id}-checkpoints-by-time - 时间索引
  3. index-{project_id}-checkpoints-by-phase - 阶段索引
```

#### Step 2: 备份所有关键资源

**读取并保存现有数据**：
```markdown
FOR each resource IN critical_resources:

  ## 读取现有数据
  existing_data = call Serena read_memory
    memory_name: "{resource_name}"

  IF existing_data 存在:
    ## 创建备份
    backup_name = "backup-{resource_name}-{timestamp}"
    call Serena write_memory
      memory_name: "{backup_name}"
      content: {
        resource_name: "{resource_name}",
        backup_data: existing_data,
        backup_at: get_current_timestamp(),
        operation: "checkpoint-{phase}"
      }

  ELSE:
    ## 记录资源不存在（首次创建）
    backup_data = null
```

**示例**：
```yaml
# 备份 Progress 记录
backup-progress-user-auth-20260306-143000:
  resource_name: "progress-user-auth"
  backup_data:
    metadata:
      version: "1.0"
      project_id: "user-auth"
    phases:
      - phase_name: "brainstorm"
        status: "completed"
      - phase_name: "design"
        status: "in_progress"
  backup_at: "2026-03-06T14:30:00Z"
  operation: "checkpoint-design"
```

#### Step 3: 验证备份完整性

**确认所有备份都已创建**：
```markdown
FOR each backup IN created_backups:
  verify = call Serena read_memory
    memory_name: "{backup_name}"

  IF verify 失败:
    → 备份不完整
    → 停止操作
    → 返回错误
```

**🔴 重要**：必须验证备份，确保可以回滚。

---

### 2. 执行操作（Execute Operations）

**用途**：在备份保护下执行多步操作。

#### 执行流程

```markdown
try:
  ## 执行步骤1: 保存 Checkpoint
  call Serena write_memory
    memory_name: "checkpoint-{project_id}-{phase}-{uuid}"
    content: {checkpoint_data}

  IF 写入失败:
    → 抛出异常，触发回滚

  ## 执行步骤2: 更新 Progress
  progress_data = call Serena read_memory
    memory_name: "progress-{project_id}"

  progress_data.phases[phase].status = "completed"
  progress_data.phases[phase].end_time = get_current_timestamp()

  call Serena write_memory
    memory_name: "progress-{project_id}"
    content: {progress_data}

  IF 写入失败:
    → 抛出异常，触发回滚

  ## 执行步骤3: 更新索引
  call update_index(...)

  IF 更新失败:
    → 抛出异常，触发回滚

  → 所有操作成功
  → 返回成功

except Exception as e:
  → 记录错误日志
  → 触发回滚（Step 3）
  → 返回失败
```

**关键要点**：
- ✅ 每一步都可能失败
- ✅ 任何失败都应触发回滚
- ✅ 使用 try-except 确保回滚

---

### 3. 回滚事务（Rollback Transaction）

**用途**：操作失败时恢复到备份状态。

#### Step 1: 反向遍历所有备份

**按创建的相反顺序恢复**：
```markdown
FOR backup IN reverse(created_backups):

  ## 读取备份数据
  backup_data = call Serena read_memory
    memory_name: "{backup_name}"

  IF backup_data.backup_data == null:
    ## 资源是新创建的，删除即可
    call Serena delete_memory
      memory_name: "{backup_data.resource_name}"

  ELSE:
    ## 恢复原始数据
    call Serena write_memory
      memory_name: "{backup_data.resource_name}"
      content: backup_data.backup_data
```

#### Step 2: 验证回滚完整性

**确认所有资源都已恢复**：
```markdown
FOR each resource IN critical_resources:
  current_data = call Serena read_memory
    memory_name: "{resource_name}"

  ## 对比备份数据和当前数据
  IF current_data != backup_data.backup_data:
    → 回滚不完整
    → 记录错误日志
    → 继续尝试恢复其他资源
```

#### Step 3: 清理备份数据

**删除临时备份**：
```markdown
FOR backup IN created_backups:
  call Serena delete_memory
    memory_name: "{backup_name}"

  IF 删除失败:
    → 记录警告日志
    → 不影响主流程（备份有TTL会自动过期）
```

#### Step 4: 记录回滚日志

**记录回滚详情**：
```markdown
log_info:
  operation: "checkpoint-{phase}"
  status: "rolled_back"
  resources_restored: ["progress-user-auth", "index-..."]
  rollback_time: get_current_timestamp()
  error_message: "{original error message}"
```

---

### 4. 提交事务（Commit Transaction）

**用途**：所有操作成功后清理备份。

#### Step 1: 验证所有操作成功

**确认所有步骤都已完成**：
```markdown
checklist:
  - [x] Checkpoint 已保存
  - [x] Progress 已更新
  - [x] 索引已更新
  - [x] 所有操作无错误
```

#### Step 2: 清理备份数据

**删除临时备份（可选）**：
```markdown
FOR backup IN created_backups:
  call Serena delete_memory
    memory_name: "{backup_name}"

  IF 删除失败:
    → 记录警告日志
    → 不影响主流程（备份会自动过期）
```

**为什么不强制清理？**
- 备份数据有 TTL，会自动过期
- 清理失败不影响事务结果
- 可以用于故障排查

---

## 完整使用示例

### 场景：保存 Checkpoint（完整流程）

```markdown
## ========== Phase 1: 准备阶段 ==========

### Step 1: 识别关键资源
critical_resources = [
  "progress-user-auth",
  "index-user-auth-checkpoints-by-time",
  "index-user-auth-checkpoints-by-phase"
]

### Step 2: 获取锁（如果需要）
call lock-utils skill (Acquire Lock)
  resource_name: "progress-user-auth"
  task_id: "checkpoint-design"

## ========== Phase 2: 备份阶段 ==========

### Step 3: 备份所有关键资源
created_backups = []

FOR resource IN critical_resources:
  ## 读取现有数据
  existing_data = call Serena read_memory
    memory_name: "{resource}"

  ## 创建备份
  backup_name = "backup-{resource}-{timestamp}"
  call Serena write_memory
    memory_name: "{backup_name}"
    content: {
      resource_name: resource,
      backup_data: existing_data,
      backup_at: get_current_timestamp(),
      operation: "checkpoint-design"
    }

  created_backups.append(backup_name)

### Step 4: 验证备份完整性
FOR backup IN created_backups:
  verify = call Serena read_memory
    memory_name: "{backup}"

  IF verify 失败:
    → 返回错误："备份不完整，无法继续"

## ========== Phase 3: 执行阶段 ==========

try:
  ### Step 5: 保存 Checkpoint
  checkpoint_id = "checkpoint-user-auth-design-{uuid}"
  call Serena write_memory
    memory_name: "{checkpoint_id}"
    content: {checkpoint_data}

  IF 写入失败:
    → 抛出异常："Checkpoint 保存失败"

  ### Step 6: 更新 Progress
  progress_data = call Serena read_memory
    memory_name: "progress-user-auth"

  progress_data.phases["design"].status = "completed"
  progress_data.phases["design"].end_time = get_current_timestamp()

  call Serena write_memory
    memory_name: "progress-user-auth"
    content: {progress_data}

  IF 写入失败:
    → 抛出异常："Progress 更新失败"

  ### Step 7: 更新索引
  ## 更新时间索引
  time_index = call Serena read_memory
    memory_name: "index-user-auth-checkpoints-by-time"

  today = get_current_date()
  time_index[today].append(checkpoint_id)

  call Serena write_memory
    memory_name: "index-user-auth-checkpoints-by-time"
    content: {time_index}

  ## 更新阶段索引
  phase_index = call Serena read_memory
    memory_name: "index-user-auth-checkpoints-by-phase"

  phase_index["design"].append(checkpoint_id)

  call Serena write_memory
    memory_name: "index-user-auth-checkpoints-by-phase"
    content: {phase_index}

  → 所有操作成功

except Exception as e:
  ### Step 8: 回滚事务
  log_error(f"操作失败: {e}")

  ## 反向遍历所有备份
  FOR backup IN reverse(created_backups):
    backup_data = call Serena read_memory
      memory_name: "{backup}"

    IF backup_data.backup_data == null:
      ## 资源是新创建的，删除
      call Serena delete_memory
        memory_name: "{backup_data.resource_name}"
    ELSE:
      ## 恢复原始数据
      call Serena write_memory
        memory_name: "{backup_data.resource_name}"
        content: backup_data.backup_data

  → 返回失败

## ========== Phase 4: 清理阶段 ==========

finally:
  ### Step 9: 清理备份数据（可选）
  FOR backup IN created_backups:
    call Serena delete_memory
      memory_name: "{backup}"

  ### Step 10: 释放锁（如果已获取）
  call lock-utils skill (Release Lock)
    resource_name: "progress-user-auth"
    task_id: "checkpoint-design"

## ========== Phase 5: 确认阶段 ==========

IF 所有操作成功:
  → 显示成功消息
  → 返回 Checkpoint ID

IF 操作失败且已回滚:
  → 显示失败消息
  → 说明已回滚到操作前状态
```

---

## 快速参考

### 事务流程

| 阶段 | 步骤 | 操作 | 工具 |
|------|------|------|------|
| **准备** | 1 | 识别资源 | 分析操作 |
| **准备** | 2 | 获取锁 | lock-utils |
| **备份** | 3 | 创建备份 | Serena write_memory |
| **备份** | 4 | 验证备份 | Serena read_memory |
| **执行** | 5-7 | 执行操作 | Serena write_memory |
| **回滚** | 8 | 恢复备份（失败时） | Serena write_memory |
| **清理** | 9 | 删除备份 | Serena delete_memory |
| **清理** | 10 | 释放锁 | lock-utils |

### 备份命名规范

| 类型 | 格式 | 示例 |
|------|------|------|
| **Progress备份** | `backup-progress-{project_id}-{timestamp}` | backup-progress-user-auth-20260306-143000 |
| **Index备份** | `backup-index-{project_id}-{type}-{timestamp}` | backup-index-user-auth-checkpoints-by-time-20260306-143000 |

### 备份数据结构

```yaml
Backup:
  resource_name: string       # 原资源名称
  backup_data: object | null  # 备份数据（null表示新创建）
  backup_at: timestamp        # 备份时间
  operation: string           # 操作描述
```

---

## 常见错误

### ❌ 错误1：忘记备份关键资源

**问题**：只备份了部分资源，回滚不完整

```markdown
# ❌ 错误做法
只备份 progress-user-auth
忘记备份 index-user-auth-checkpoints-by-time

如果操作失败:
  → Progress 可以恢复
  → Index 无法恢复
  → 数据不一致
```

**正确做法**：识别所有将被修改的资源
```markdown
# ✅ 正确做法
将被修改的资源:
  1. progress-user-auth
  2. index-user-auth-checkpoints-by-time
  3. index-user-auth-checkpoints-by-phase

全部备份 → 全部可恢复
```

### ❌ 错误2：不验证备份

**问题**：备份失败但没有发现，无法回滚

```markdown
# ❌ 错误做法
创建备份
→ 不验证
→ 直接执行操作
→ 操作失败
→ 尝试回滚
→ 发现备份不存在
→ 无法恢复
```

**正确做法**：验证备份完整性
```markdown
# ✅ 正确做法
创建备份
→ 验证备份存在
→ 验证备份数据完整
→ 才开始执行操作
```

### ❌ 错误3：回滚顺序错误

**问题**：回滚顺序不对，导致依赖关系错误

```markdown
# ❌ 错误做法
备份顺序: Progress → Index
回滚顺序: Progress → Index

问题:
  Index 可能引用了 Progress
  先恢复 Progress，Index 的引用可能错误
```

**正确做法**：反向回滚
```markdown
# ✅ 正确做法
备份顺序: Progress → Index
回滚顺序: Index → Progress (反向)

先恢复 Index（被依赖）
再恢复 Progress（依赖方）
```

### ❌ 错误4：不处理新创建的资源

**问题**：新创建的资源备份为 null，回滚时不知道如何处理

```markdown
# ❌ 错误做法
backup_data = read_memory("new-resource")
# backup_data = null (新资源)

回滚时:
  write_memory("new-resource", null)
  → 错误：不应该写入 null
```

**正确做法**：区分新创建和已存在
```markdown
# ✅ 正确做法
IF backup_data.backup_data == null:
  ## 资源是新创建的
  delete_memory("new-resource")
ELSE:
  ## 资源已存在，恢复原始数据
  write_memory("new-resource", backup_data.backup_data)
```

---

## Red Flags

**🔴 STOP if**:
- 备份创建失败 → 不要继续操作
- 备份验证失败 → 不要继续操作
- 关键资源未备份 → 不要继续操作
- 回滚失败 → 记录详细错误，需要人工干预

**🟡 WARNING if**:
- 备份清理失败 → 不影响主流程，记录警告
- 部分资源备份失败 → 检查是否关键资源

---

## 测试清单

### 单元测试

- [ ] 备份创建成功
- [ ] 备份验证通过
- [ ] 备份数据完整
- [ ] 新创建资源的备份为 null
- [ ] 已存在资源的备份包含原始数据

### 集成测试

- [ ] 操作成功 → 提交事务
- [ ] 操作失败 → 回滚事务
- [ ] 回滚成功 → 数据恢复到操作前状态
- [ ] 回滚顺序正确（反向）
- [ ] 新创建资源回滚后被删除
- [ ] 已存在资源回滚后恢复原始数据

### 故障测试

- [ ] 备份创建失败 → 停止操作
- [ ] 操作中途失败 → 完整回滚
- [ ] 回滚中途失败 → 记录错误
- [ ] 备份清理失败 → 不影响事务结果

### 性能测试

- [ ] 备份创建时间 < 1秒
- [ ] 回滚时间 < 2秒
- [ ] 备份数据大小合理（< 原始数据 2倍）

---

## 实施注意事项

### 与锁机制的配合

**推荐组合使用**：
```markdown
## 标准流程

### Step 1: 获取锁
call lock-utils skill (Acquire Lock)

### Step 2: 开始事务（创建备份）
call transaction-utils skill (Begin Transaction)

### Step 3: 执行操作
try:
  执行关键操作

### Step 4: 回滚（如果失败）
except:
  call transaction-utils skill (Rollback)

### Step 5: 清理备份和释放锁
finally:
  call transaction-utils skill (Commit)
  call lock-utils skill (Release Lock)
```

### 性能考虑

- **备份数量**：只备份真正会被修改的资源
- **备份大小**：大资源考虑增量备份
- **备份清理**：成功后清理，失败保留用于排查

### 错误处理

- **备份失败**：立即停止，返回错误
- **操作失败**：触发回滚，记录详细日志
- **回滚失败**：记录 CRITICAL 错误，需要人工干预
- **清理失败**：记录警告，不影响主流程

---

## 相关文档

- **设计文档**：`cadence/docs/2026-03-05_设计文档_可靠性保障系统_v1.0.md` (第378-730行)
- **实施计划**：`cadence/plans/2026-03-04_计划文档_项目任务追踪优化_v1.0.md`
- **相关Skills**：
  - lock-utils skill - 并发控制
  - checkpoint skill - 保存 Checkpoint
  - status skill - 读取 Progress

---

**Skill创建日期**: 2026-03-06
**Skill版本**: v1.0
**创建者**: Claude Sonnet 4.6
**状态**: ✅ 已完成
