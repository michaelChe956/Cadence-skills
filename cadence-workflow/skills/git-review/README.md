# Git Review Skill

基于 Git 提交记录的代码审查 Skill，使用静态规则 + AI 深度分析的混合模式。

## 快速开始

### 安装

此 Skill 已集成到 Cadence-skills 项目中，无需单独安装。

### 使用

```bash
# 审查最近 10 个提交
/git-review -n 10

# 审查指定日期范围
/git-review --since "2026-03-01" --until "2026-03-04"

# 审查某个分支
/git-review --branch main -n 20
```

## 功能特性

### ✅ 静态规则检查（快速）

- **代码质量**: 命名规范、函数长度、代码重复
- **安全性**: 敏感信息、SQL 注入、XSS
- **性能**: 算法复杂度、资源使用、N+1 查询
- **项目规范**: Commit message 格式、文件组织

### ✅ AI 深度分析（复杂问题）

- 复杂逻辑正确性验证
- 安全上下文分析
- 性能瓶颈识别
- 最佳实践评估

### ✅ 结构化报告

- 按严重级别分类（Critical/Important/Minor）
- 详细的文件位置和代码片段
- 可执行的修复建议
- 统计信息和趋势分析

## 文档结构

```
skills/git-review/
├── SKILL.md                        # 核心 Skill 文档
├── analyzers/
│   ├── static-rules.md             # 静态规则定义（23 条）
│   └── ai-prompts.md               # AI 分析提示词（4 场景）
└── templates/
    └── review-report.md           # 报告模板

commands/
└── git-review.md                   # /git-review 命令文档
```

## 使用场景

### 每日审查

```bash
# 审查今天的提交
/git-review --since "today"
```

### 代码合并前审查

```bash
# 审查 feature 分支
/git-review --branch feature-xyz --since "2026-03-01"
```

### 发布前全面审查

```bash
# 审查最近 50 个提交
/git-review -n 50
```

## 报告示例

````markdown
# Git Review Report

**审查时间**: 2026-03-04 14:30:00
**总提交数**: 10
**总文件数**: 25

## 📊 审查摘要

| 严重级别 | 数量 | 类型 |
|---------|------|------|
| 🔴 Critical | 2 | 安全漏洞 |
| 🟡 Important | 5 | 性能问题 |
| 🟢 Minor | 10 | 规范问题 |

## 🔴 Critical Issues

### 1. SQL Injection Vulnerability
- **文件**: `src/db/queries.js:45`
- **描述**: 使用字符串拼接构造 SQL 查询
- **建议**: 使用参数化查询
````

## 配置

### 静态规则

查看和修改规则: `analyzers/static-rules.md`

### AI 分析

查看和调整提示词: `analyzers/ai-prompts.md`

### 报告模板

自定义报告格式: `templates/review-report.md`

## 最佳实践

1. **定期审查**: 每天或每周运行
2. **分级处理**: Critical → Important → Minor
3. **持续改进**: 根据项目调整规则

## 限制

- 不支持项目级自定义规则（v1.0）
- AI 分析有调用次数限制（10 次/审查）
- 静态规则可能有误报

## 路线图

### v2.0 计划

- [ ] 支持项目级自定义规则（`.git-review/`）
- [ ] 自动修复简单问题
- [ ] 集成到 CI/CD pipeline
- [ ] 生成 HTML 报告
- [ ] 支持更多编程语言

## 相关资源

- [设计文档](../../.claude/plans/2026-03-04_计划文档_GitReviewSkill_v1.0.md)
- [实现计划](../../docs/plans/2026-03-04-git-review-skill.md)
- [Command 文档](../../commands/git-review.md)

## 许可

MIT License

## 版本历史

- **v1.0** (2026-03-04): Initial release
