# AI Analysis Prompts

AI 深度分析提示词模板，用于处理静态规则无法判断的复杂问题。

---

## 1. Analysis Scenarios

### Scenario 1: Complex Logic Analysis

**触发条件**: 静态规则发现复杂嵌套逻辑（≥3层）

**Prompt Template**:

```
你是一位资深代码审查专家。请分析以下复杂逻辑的正确性：

**文件**: {file_path}
**函数**: {function_name}
**代码片段**:
```
{code_snippet}
```

**审查重点**:
1. 边界条件是否完整？
2. 异常情况是否处理？
3. 逻辑分支是否全覆盖？
4. 是否存在死循环或无限递归？

**详细规则检查项**:

| 规则项 | 检查内容 | 严重级别 |
|--------|---------|---------|
| 空值处理 | null/undefined/空数组/空对象的处理是否完善 | Critical |
| 空集合遍历 | 遍历前是否检查集合为空或空 | Critical |
| 状态机完整性 | 枚举值是否全覆盖switch/if分支 | Important |
| 事务边界 | 数据库操作的事务是否正确开启/提交/回滚 | Critical |
| 资源获取释放 | lock/connect/stream等是否配对释放 | Critical |
| 浮点数比较 | 是否使用==直接比较浮点数 | Important |
| 除零检查 | 除法运算前是否检查除数非零 | Critical |
| 整数溢出 | 大数运算是否考虑溢出风险 | Important |
| 递归终止 | 递归函数是否有明确的终止条件 | Critical |
| 并发安全 | 多线程共享变量是否正确同步 | Critical |

**输出格式** (JSON):

```json
{
  "meta": {
    "analyzer": "complex-logic",
    "analyzedAt": "{timestamp}",
    "totalIssues": {n}
  },
  "issues": [
    {
      "id": "{scenario}-{001}",
      "source": "AI",
      "severity": "Critical|Important|Minor",
      "type": "Bug|Logic|EdgeCase",
      "confidence": {0.0-1.0},
      "location": {
        "file": "{file_path}",
        "line": {n},
        "endLine": {n},
        "function": "{function_name}"
      },
      "description": "{问题描述}",
      "suggestion": "{修复建议}",
      "codeSnippet": "{相关代码片段}",
      "rule": "{匹配的规则项}",
      "fixComplexity": "Low|Medium|High"
    }
  ],
  "summary": {
    "total": {n},
    "critical": {n},
    "important": {n},
    "minor": {n},
    "analysis": "{整体评估说明}"
  }
}
```

---

### Scenario 2: Security Context Analysis

**触发条件**: 发现可能的敏感信息或安全风险

**Prompt Template**:

```
你是一位安全专家。请深度分析以下代码的安全性：

**文件**: {file_path}
**上下文**:
```
{code_snippet}
```

**审查重点**:
1. 是否泄露敏感信息？
2. 是否存在注入风险？
3. 是否有权限检查？
4. 是否符合安全最佳实践？

**输出格式** (JSON):

```json
{
  "meta": {
    "analyzer": "security",
    "analyzedAt": "{timestamp}",
    "totalIssues": {n}
  },
  "issues": [
    {
      "id": "{scenario}-{001}",
      "source": "AI",
      "severity": "Critical|Important|Minor",
      "type": "Security",
      "confidence": {0.0-1.0},
      "location": {
        "file": "{file_path}",
        "line": {n},
        "endLine": {n}
      },
      "description": "{安全问题描述}",
      "suggestion": "{修复建议}",
      "codeSnippet": "{相关代码片段}",
      "cwe": "CWE-{xxx}",
      "cvss": {0.0-10.0},
      "attackVector": "Network|Local|Physical"
    }
  ],
  "summary": {
    "total": {n},
    "critical": {n},
    "important": {n},
    "minor": {n},
    "analysis": "{安全评估说明}"
  }
}
```

---

### Scenario 3: Performance Bottleneck Analysis

**触发条件**: 发现性能问题模式（嵌套循环、N+1 等）

**Prompt Template**:

```
你是一位性能优化专家。请分析以下代码的性能问题：

**文件**: {file_path}
**代码**:
```
{code_snippet}
```

**审查重点**:
1. 算法复杂度分析（Big O）
2. 资源使用优化（内存、CPU、IO）
3. 并发安全性
4. 内存泄漏风险

**详细规则检查项**:

| 规则项 | 检查内容 | 严重级别 |
|--------|---------|---------|
| N+1查询 | 循环内是否查询数据库 | Critical |
| 全表扫描 | 查询是否缺少索引条件 | Important |
| 大对象序列化 | Session中是否存放大对象 | Important |
| 频繁GC | 是否大量创建短期对象 | Important |
| 同步阻塞 | 主线程是否进行IO操作 | Important |
| 重复计算 | 是否重复计算可缓存结果 | Minor |
| 字符串拼接 | 循环内是否用+拼接字符串 | Important |
| 批量操作 | 是否使用批量操作替代循环单条 | Important |
| 深拷贝 | 不必要的深拷贝导致性能损耗 | Minor |
| 正则预编译 | 正则表达式是否在循环内重复创建 | Important |
| 懒加载过度 | 过度使用懒加载导致频繁空判断 | Minor |
| 同步原语 | 是否存在不必要的synchronized块 | Important |

**输出格式** (JSON):

```json
{
  "meta": {
    "analyzer": "performance",
    "analyzedAt": "{timestamp}",
    "totalIssues": {n}
  },
  "issues": [
    {
      "id": "{scenario}-{001}",
      "source": "AI",
      "severity": "Critical|Important|Minor",
      "type": "Performance",
      "confidence": {0.0-1.0},
      "location": {
        "file": "{file_path}",
        "line": {n},
        "endLine": {n},
        "function": "{function_name}"
      },
      "description": "{性能问题描述}",
      "suggestion": "{优化建议}",
      "codeSnippet": "{相关代码片段}",
      "complexity": "O(n)|O(n²)|O(n³)|O(2^n)",
      "hotspot": "CPU|Memory|IO|Network",
      "estimatedImpact": "High|Medium|Low"
    }
  ],
  "summary": {
    "total": {n},
    "critical": {n},
    "important": {n},
    "minor": {n},
    "analysis": "{性能评估说明}"
  }
}
```

---

### Scenario 4: Best Practices Evaluation

**触发条件**: 代码质量不达标（函数过长、参数过多等）

**Prompt Template**:

```
你是一位代码质量专家。请评估以下代码是否符合最佳实践：

**文件**: {file_path}
**项目技术栈**: {tech_stack}
**代码**:
```
{code_snippet}
```

**审查重点**:
1. 设计模式应用
2. 代码可读性
3. 可维护性
4. 测试覆盖率建议

**详细规则检查项**:

| 规则项 | 检查内容 | 严重级别 |
|--------|---------|---------|
| 空catch块 | 是否存在捕获异常但什么都不做 | Critical |
| 捕获异常过宽 | 是否捕获Exception/Throwable而非具体异常 | Important |
| 魔法数字 | 是否存在未提取为常量的数字 | Important |
| 魔法字符串 | 是否存在未提取为常量的字符串 | Important |
| 参数过多 | 函数参数是否超过4个 | Important |
| 函数过长 | 单函数是否超过50行 | Important |
| 重复代码 | 是否存在重复代码块 | Important |
| 圈复杂度 | 条件分支是否过于复杂（>10） | Important |
| 注释质量 | 注释是否解释Why而非What | Minor |
| 命名规范 | 变量/函数命名是否清晰 | Minor |
| SOLID原则 | 是否违反单一职责/开闭等原则 | Important |
| 测试覆盖 | 关键业务逻辑是否有单元测试 | Minor |
| 日志规范 | 日志级别使用是否恰当 | Minor |
| 异常链断裂 | 抛出新异常是否保留原异常信息 | Important |
| 资源未关闭 | IO资源是否在finally中关闭 | Critical |

**输出格式** (JSON):

```json
{
  "meta": {
    "analyzer": "best-practices",
    "analyzedAt": "{timestamp}",
    "totalIssues": {n}
  },
  "issues": [
    {
      "id": "{scenario}-{001}",
      "source": "AI",
      "severity": "Critical|Important|Minor",
      "type": "Maintainability|Readability",
      "confidence": {0.0-1.0},
      "location": {
        "file": "{file_path}",
        "line": {n},
        "endLine": {n},
        "function": "{function_name}"
      },
      "description": "{代码质量问题描述}",
      "suggestion": "{改进建议}",
      "codeSnippet": "{相关代码片段}",
      "ruleId": "{规则项名称}",
      "refactoring": "Easy|Medium|Hard"
    }
  ],
  "testSuggestions": [
    "{测试建议}"
  ],
  "summary": {
    "total": {n},
    "critical": {n},
    "important": {n},
    "minor": {n},
    "analysis": "{最佳实践评估说明}"
  }
}
```

---

## 2. AI Call Strategy

### 2.1 Rate Limiting

- **最大调用次数**: 10 次/审查
- **单次最大 token**: 4000 tokens
- **超时设置**: 30 秒

### 2.2 Fallback Strategy

如果 AI 不可用或达到限制：
1. 仅输出静态规则结果
2. 在报告中标注 "AI 分析不可用"
3. 建议人工审查复杂问题

### 2.3 Caching Strategy

- **缓存键**: `{file_path}:{content_hash}`
- **缓存时长**: 24 小时
- **缓存位置**: `.claude/cache/ai-analysis/`

---

## 3. Prompt Optimization

### 3.1 上下文提供

为了提高 AI 分析准确性，提供以下上下文：
- **文件路径**: 帮助 AI 理解代码组织
- **函数签名**: 理解接口契约
- **前后代码**: 3-5 行上下文
- **依赖信息**: 相关 import/require

### 3.2 输出格式控制

强制要求 JSON 格式输出：
- 便于解析和合并到报告中
- 结构化数据，易于分类和排序
- 支持自动生成修复建议

---

## 4. Integration Points

### 4.1 与静态规则集成

```python
# 伪代码示例
def analyze_file(file_path, diff_content):
    # Step 1: 静态规则检查
    static_issues = run_static_rules(file_path, diff_content)

    # Step 2: 识别需要 AI 分析的问题
    complex_issues = filter_complex_issues(static_issues)

    # Step 3: AI 深度分析
    if len(complex_issues) > 0 and ai_calls < MAX_AI_CALLS:
        ai_issues = call_ai_analysis(file_path, complex_issues)
        static_issues.extend(ai_issues)

    return static_issues
```

### 4.2 报告生成集成

AI 分析结果合并到最终报告：
- 按严重级别排序
- 标注来源（Static/AI）
- 提供详细的修复建议

---

## 5. Quality Assurance

### 5.1 AI 结果验证

- **格式验证**: 确保返回有效 JSON
- **内容验证**: 确保包含必需字段
- **合理性验证**: 确保建议切实可行

### 5.2 性能监控

- 记录每次 AI 调用耗时
- 统计 AI 调用成功率
- 监控 token 消耗

---

## 6. Best Practices

### 6.1 何时调用 AI

**应该调用**:
- 复杂逻辑判断（静态规则无法确定）
- 上下文相关问题
- 架构设计建议
- 最佳实践评估

**不应调用**:
- 简单的命名规范检查
- 明确的安全漏洞（正则已匹配）
- 格式问题

### 6.2 Prompt 编写原则

- **明确目标**: 清晰说明要分析什么
- **提供上下文**: 给出足够的信息
- **指定格式**: 要求结构化输出
- **限制范围**: 避免 AI 偏离主题
