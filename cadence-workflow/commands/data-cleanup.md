---
skill: data-cleanup
---

# Data Cleanup - 清理过期数据

归档旧的Checkpoint数据并删除过期的数据，维护Serena memory性能。

## 使用场景
- Checkpoint数据超过30天
- Serena memory存储过大
- 定期维护清理

## 调用方式
```
/cleanup [--dry-run]
```

## 选项
- `--dry-run`: 预览清理操作而不实际执行

## 详细文档
查看完整 Skill 文档：[data-cleanup/SKILL.md](../skills/data-cleanup/SKILL.md)
