## Serena 使用规则

> **项目分析工具规范**

- **禁止分析 .git 目录** - 当使用 Serena MCP 工具分析项目时，必须跳过 `.git/` 目录及其所有内容。
- **使用 Git 命令获取版本信息** - 如果需要获取 Git 相关信息（如提交历史、分支信息、文件变更等），必须使用 Git 命令（如 `git log`、`git branch`、`git diff` 等），而不是通过 Serena 分析 `.git/` 目录。
- **原因说明**：
  - `.git/` 目录包含版本控制的元数据和对象文件，分析这些内容没有实际意义
  - 避免不必要的资源消耗和性能浪费
  - Git 命令提供了更高效、更准确的版本信息查询方式

**正确做法示例**：
```bash
# ✅ 正确：使用 git 命令获取提交历史
git log --oneline -10

# ✅ 正确：使用 git 命令查看分支信息
git branch -a

# ✅ 正确：使用 git 命令查看文件变更
git diff HEAD~1
```

**错误做法示例**：
```bash
# ❌ 错误：使用 Serena 分析 .git 目录
serena analyze .git/

# ❌ 错误：使用 Serena 读取 .git 目录下的文件
serena read .git/objects/...
```