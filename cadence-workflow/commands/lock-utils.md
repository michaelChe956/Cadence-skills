---
skill: lock-utils
---

# Lock Utils - 并发控制工具

提供资源锁机制，防止并发写入导致的数据损坏。

## 使用场景

- 在保存 Checkpoint 前获取资源锁
- 在更新 Progress 记录前获取资源锁
- 在执行任何需要并发保护的写入操作前

## 主要功能

### 1. 获取锁 (Acquire Lock)

在执行写入操作前获取资源锁。

**流程**：
1. 检查锁状态
2. 检查锁是否超时
3. 获取锁
4. 验证锁

### 2. 释放锁 (Release Lock)

在完成写入操作后释放资源锁。

**流程**：
1. 检查锁状态
2. 验证持有者
3. 释放锁
4. 验证释放

## 使用示例

### 完整流程（获取锁 → 执行操作 → 释放锁）

```markdown
# Step 1: 获取锁
resource_name = "progress-user-auth"
task_id = "checkpoint-brainstorm"

使用 lock-utils skill (获取锁)
IF 获取失败:
  → 返回错误

# Step 2: 执行关键操作
try:
  保存 Checkpoint
  更新 Progress
  更新索引

# Step 3: 释放锁 (finally)
finally:
  使用 lock-utils skill (释放锁)
```

## 锁数据模型

```yaml
Lock:
  resource: string          # 资源标识
  locked: boolean           # 是否锁定
  locked_by: string         # 锁持有者
  locked_at: timestamp      # 锁定时间
  ttl: number               # 锁超时时间(秒)
```

## 重要提示

⚠️ **必须验证锁**：获取锁后必须验证，防止并发竞争

⚠️ **必须释放锁**：无论操作成功或失败，都必须释放锁

⚠️ **只有持有者可释放**：不是锁的持有者不能释放锁

## 详细文档

查看完整 Skill 文档：[lock-utils/SKILL.md](../skills/lock-utils/SKILL.md)
