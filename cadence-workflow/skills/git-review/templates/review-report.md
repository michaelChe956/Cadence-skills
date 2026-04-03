# Git Review Report

**审查时间**: {timestamp}
**提交范围**: {commit_range}
**总提交数**: {commit_count}
**总文件数**: {file_count}
**审查模式**: {mode} (Static + AI)

---

## 📊 审查摘要

| 严重级别 | 数量 | 类型 |
|---------|------|------|
| 🔴 Critical | {critical_count} | 安全漏洞、严重 Bug |
| 🟡 Important | {important_count} | 性能问题、代码质量 |
| 🟢 Minor | {minor_count} | 规范问题、建议改进 |

**总计**: {total_issues} 个问题

---

## 🔴 Critical Issues ({critical_count})

<!-- BEGIN CRITICAL_ISSUES -->

### {issue_number}. {issue_title}

- **文件**: `{file_path}:{line_number}`
- **提交**: `{commit_sha}` by {author} ({date})
- **来源**: {source} (Static/AI)
- **规则**: {rule_id}
- **描述**: {description}

**问题代码**:
```
{code_snippet}
```

**建议修复**:
```
{suggested_fix}
```

---

<!-- END CRITICAL_ISSUES -->

## 🟡 Important Issues ({important_count})

<!-- BEGIN IMPORTANT_ISSUES -->

### {issue_number}. {issue_title}

- **文件**: `{file_path}:{line_number}`
- **提交**: `{commit_sha}` by {author} ({date})
- **来源**: {source} (Static/AI)
- **规则**: {rule_id}
- **描述**: {description}

**建议**: {suggestion}

---

<!-- END IMPORTANT_ISSUES -->

## 🟢 Minor Issues ({minor_count})

<!-- BEGIN MINOR_ISSUES -->

### {issue_number}. {issue_title}

- **文件**: `{file_path}:{line_number}`
- **提交**: `{commit_sha}` by {author} ({date})
- **规则**: {rule_id}
- **建议**: {suggestion}

---

<!-- END MINOR_ISSUES -->

## 📋 Review Details

### 审查的提交

<!-- BEGIN COMMITS -->

1. `{commit_sha}` - {commit_message} ({author}, {date})
2. ...

<!-- END COMMITS -->

### 审查的文件

<!-- BEGIN FILES -->

1. `{file_path}` - {additions} additions, {deletions} deletions
2. ...

<!-- END FILES -->

---

## 💡 Recommendations

### Critical Issues (必须修复)

<!-- BEGIN CRITICAL_RECOMMENDATIONS -->

- **Issue #{issue_number}**: {recommendation}

<!-- END CRITICAL_RECOMMENDATIONS -->

### Important Issues (建议修复)

<!-- BEGIN IMPORTANT_RECOMMENDATIONS -->

- **Issue #{issue_number}**: {recommendation}

<!-- END IMPORTANT_RECOMMENDATIONS -->

### Minor Issues (可选修复)

<!-- BEGIN MINOR_RECOMMENDATIONS -->

- **Issue #{issue_number}**: {recommendation}

<!-- END MINOR_RECOMMENDATIONS -->

---

## 📈 Statistics

- **静态规则检测**: {static_issues_count} 个问题
- **AI 深度分析**: {ai_issues_count} 个问题
- **AI 调用次数**: {ai_calls} / 10
- **审查耗时**: {duration}

---

## ✅ Next Steps

1. **Critical Issues**: 立即修复，阻止合并
2. **Important Issues**: 优先修复，建议在合并前完成
3. **Minor Issues**: 可延后到后续迭代

---

**生成时间**: {generation_time}
**工具版本**: Git Review Skill v1.0
