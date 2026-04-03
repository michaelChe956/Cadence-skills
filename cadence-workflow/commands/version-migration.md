---
skill: version-migration
---

# Version Migration - 版本迁移

检测并迁移旧版本数据到当前版本，确保数据格式兼容性。

## 使用场景
- 读取旧版本Progress数据
- 读取旧版本Checkpoint数据
- 数据格式升级

## 调用方式
```
/migrate {memory_name} [--dry-run]
```

## 选项
- `--dry-run`: 预览迁移操作而不实际执行

## 详细文档
查看完整 Skill 文档：[version-migration/SKILL.md](../skills/version-migration/SKILL.md)
