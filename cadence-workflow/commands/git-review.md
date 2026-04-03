---
description: Review git commits for code quality, security, performance, and standards
---

# Git Review Command

Review git commits using static rules and AI analysis.

## Usage

```bash
/git-review [options]
```

## Options

| 选项 | 简写 | 说明 | 示例 |
|------|------|------|------|
| `--since <date>` | - | 审查从指定日期开始的提交 | `--since "2026-03-01"` |
| `--until <date>` | - | 审查到指定日期结束 | `--until "2026-03-04"` |
| `--number <count>` | `-n` | 审查最近 N 个提交 | `-n 10` |
| `--author <name>` | - | 仅审查指定作者的提交 | `--author "Alice"` |
| `--branch <name>` | - | 仅审查指定分支的提交 | `--branch main` |

**注意**: `--since` 和 `--number` 至少提供其中一个。

## Examples

### Review Recent Commits

```bash
# 审查最近 10 个提交
/git-review -n 10

# 审查最近 5 个提交
/git-review --number 5
```

### Review Date Range

```bash
# 审查指定日期范围
/git-review --since "2026-03-01" --until "2026-03-04"

# 审查从某个日期到现在
/git-review --since "2026-03-01"
```

### Review by Branch

```bash
# 审查某个分支的提交
/git-review --branch feature-xyz --since "2026-03-01"

# 审查 main 分支最近 20 个提交
/git-review --branch main -n 20
```

### Review by Author

```bash
# 审查某个作者的提交
/git-review --author "Alice" --since "2026-03-01"
```

## Workflow

1. **Parse Arguments**: 解析命令行参数
2. **Get Commits**: 执行 `git log` 获取提交列表
3. **Get Diffs**: 对每个提交执行 `git diff`
4. **Run Review**: 调用 `git-review` Skill 执行审查
5. **Generate Report**: 输出结构化报告

## Output

生成的报告包含：

### 1. 审查摘要

```
📊 审查摘要
┌──────────────┬────────┬──────────────────────┐
│ 严重级别     │ 数量   │ 类型                 │
├──────────────┼────────┼──────────────────────┤
│ 🔴 Critical  │ 2      │ 安全漏洞、严重 Bug   │
│ 🟡 Important │ 5      │ 性能问题、代码质量   │
│ 🟢 Minor     │ 10     │ 规范问题、建议改进   │
└──────────────┴────────┴──────────────────────┘
```

### 2. 详细问题列表

按严重级别分组，每个问题包含：
- 文件路径和行号
- 提交信息（SHA、作者、日期）
- 问题描述
- 修复建议

### 3. 统计信息

- 审查的提交数量
- 审查的文件数量
- 静态规则检测数量
- AI 分析调用次数
- 审查耗时

### 4. 下一步建议

- Critical Issues: 立即修复
- Important Issues: 优先修复
- Minor Issues: 可延后

## Report Example

````markdown
# Git Review Report

**审查时间**: 2026-03-04 14:30:00
**提交范围**: abc123..def456
**总提交数**: 10
**总文件数**: 25
**审查模式**: Static + AI

---

## 📊 审查摘要

| 严重级别 | 数量 | 类型 |
|---------|------|------|
| 🔴 Critical | 2 | 安全漏洞、严重 Bug |
| 🟡 Important | 5 | 性能问题、代码质量 |
| 🟢 Minor | 10 | 规范问题、建议改进 |

**总计**: 17 个问题

---

## 🔴 Critical Issues (2)

### 1. SQL Injection Vulnerability

- **文件**: `src/db/queries.js:45`
- **提交**: `abc123` by Alice (2026-03-01)
- **来源**: Static
- **规则**: SEC002
- **描述**: 使用字符串拼接构造 SQL 查询

**问题代码**:
```javascript
const query = "SELECT * FROM users WHERE id = " + userId;
```

**建议修复**:
```javascript
const query = "SELECT * FROM users WHERE id = ?";
db.execute(query, [userId]);
```

---

## 🟡 Important Issues (5)

### 3. Performance: N+1 Query

- **文件**: `src/services/order.js:120`
- **提交**: `def456` by Bob (2026-03-02)
- **来源**: AI
- **规则**: PERF003
- **描述**: 循环内执行数据库查询

**建议**: 使用 JOIN 或批量查询

---
````

## Tips

### 1. 定期审查

建议每天或每周定期运行，及时发现和修复问题：

```bash
# 每日审查
/git-review --since "yesterday"

# 每周审查
/git-review --since "1 week ago"
```

### 2. 分支审查

在合并分支前审查：

```bash
# 审查 feature 分支的所有提交
/git-review --branch feature-xyz --since "2026-03-01"
```

### 3. 作者审查

审查自己的提交：

```bash
/git-review --author "$(git config user.name)" --since "today"
```

## Integration

### With Git Hooks

在 pre-push hook 中使用：

```bash
#!/bin/bash
# .git/hooks/pre-push

# 审查最近 5 个提交
/git-review -n 5

# 如果发现 Critical Issues，阻止 push
# (需要实现自动检查逻辑)
```

### With CI/CD

在 CI pipeline 中使用：

```yaml
# .gitlab-ci.yml
code_review:
  stage: test
  script:
    - /git-review --since "1 day ago"
  allow_failure: true
```

## Troubleshooting

### No commits found

**检查**:
- 日期格式是否正确（YYYY-MM-DD）
- 提交数量是否 > 0
- 分支名称是否正确

### Too many issues

**建议**:
- 优先处理 Critical Issues
- 分批修复，逐步改进
- 调整规则严格度

### AI analysis unavailable

**解决**:
- 仅使用静态规则结果
- 检查网络连接
- 确认 AI 服务可用

## See Also

- **Skill**: `git-review` - 审查逻辑实现
- **Static Rules**: `skills/git-review/analyzers/static-rules.md`
- **AI Prompts**: `skills/git-review/analyzers/ai-prompts.md`
- **Report Template**: `skills/git-review/templates/review-report.md`
