---
skill: transaction-utils
---

# Transaction Utils - 事务性保证工具

提供事务性保证，通过"备份+回滚"机制确保多步操作的原子性。

## 使用场景

- 保存 Checkpoint（需要更新多个数据）
- 更新 Progress（可能涉及多个阶段）
- 批量更新索引（需要保证一致性）
- 任何需要原子性的多步写入操作

## 主要功能

### 1. 开始事务 (Begin Transaction)

在执行多步操作前创建备份点。

**流程**：
1. 识别关键资源（列出所有将被修改的资源）
2. 备份所有关键资源（读取并保存现有数据）
3. 验证备份完整性（确认所有备份都已创建）

### 2. 回滚事务 (Rollback Transaction)

在操作失败时恢复备份。

**流程**：
1. 反向遍历所有备份
2. 恢复每个备份
3. 验证回滚结果
4. 记录回滚日志

### 3. 提交事务 (Commit Transaction)

在操作成功后清理备份（可选）。

**流程**：
1. 确认所有操作成功
2. 清理临时备份（可选）
3. 标记事务完成

## 使用示例

### 标准流程（开始事务 → 执行操作 → 提交/回滚）

```markdown
# Step 1: 开始事务（创建备份）
调用 transaction-utils skill (Begin Transaction)
Parameters:
  critical_resources:
    - "progress-user-auth"
    - "index-user-auth-checkpoints-by-time"
    - "index-user-auth-checkpoints-by-phase"
  operation_description: "checkpoint-design"

IF 备份创建失败:
  → 停止操作
  → 返回错误

# Step 2: 执行关键操作
try:
  2.1 保存 Checkpoint
      - write_memory(checkpoint_id, checkpoint_data)

  2.2 更新 Progress
      - progress_data.phases[phase].status = "completed"
      - write_memory(progress_id, progress_data)

  2.3 更新索引
      - update_checkpoints_index(project_id, checkpoint_id)

  → 所有操作成功
  → Continue to Step 3

except 操作失败:
  → Continue to Step 4 (回滚)

# Step 3: 提交事务（成功）
调用 transaction-utils skill (Commit Transaction)
  → 清理临时备份（可选）
  → 记录事务完成

# Step 4: 回滚事务（失败）
调用 transaction-utils skill (Rollback Transaction)
  → 恢复所有备份
  → 验证回滚结果
  → 记录回滚日志
```

## 备份数据模型

```yaml
Backup:
  resource_name: string       # 原资源名称
  backup_data: object | null  # 备份数据（null表示新创建）
  backup_at: timestamp        # 备份时间
  operation: string           # 操作描述
```

## 重要提示

⚠️ **必须备份所有关键资源**：只备份部分会导致回滚不完整

⚠️ **必须验证备份**：不验证可能导致回滚时发现备份不存在

⚠️ **回滚顺序很重要**：反向回滚，先恢复被依赖的资源

⚠️ **区分新创建和已存在**：新创建资源回滚时删除，已存在资源回滚时恢复

## 与锁机制的配合

推荐同时使用锁机制和事务机制：

```markdown
## 完整流程

1. 获取锁 (lock-utils)
2. 开始事务 (transaction-utils)
3. 执行操作
4. IF 成功 → 提交事务
   IF 失败 → 回滚事务
5. 释放锁 (lock-utils)
```

## 详细文档

查看完整 Skill 文档：[transaction-utils/SKILL.md](../skills/transaction-utils/SKILL.md)
