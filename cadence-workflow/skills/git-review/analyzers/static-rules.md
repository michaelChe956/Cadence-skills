# Static Rules

静态代码分析规则，用于快速检测常见问题。

---

## 1. Code Quality Rules

### 1.1 Naming Conventions

#### 变量命名
- **规则**: 禁止单字母变量名（循环变量除外）
- **正则**: `\bvar\s+[a-z]\b` (简化示例)
- **严重级别**: Minor
- **建议**: 使用描述性名称

#### 函数命名
- **规则**: 函数名应以动词开头，使用驼峰命名
- **正则**: `function\s+[a-z][a-zA-Z0-9]*\s*\(`
- **严重级别**: Minor
- **建议**: `function getUserName() {}`

#### 类命名
- **规则**: 类名应使用帕斯卡命名法（PascalCase）
- **正则**: `class\s+[A-Z][a-zA-Z0-9]*\s*{`
- **严重级别**: Minor
- **建议**: `class UserManager {}`

### 1.2 Function Length

#### 函数长度限制
- **规则**: 函数不应超过 40 行
- **检测方式**: 统计函数体行数
- **严重级别**: Important
- **建议**: 拆分为多个小函数

#### 参数数量限制
- **规则**: 函数参数不应超过 5 个
- **正则**: `function\s+\w+\s*\([^)]{0,200}\)` (简化)
- **严重级别**: Minor
- **建议**: 使用对象参数或重构

### 1.3 Code Duplication

#### 重复代码检测
- **规则**: 检测 6 行或以上相同代码
- **检测方式**: 逐行比对
- **严重级别**: Important
- **建议**: 提取为公共函数

### 1.4 Comments Quality

#### TODO/FIXME 规范
- **规则**: TODO/FIXME 必须指定负责人
- **正则**: `(TODO|FIXME)(?!.*@)`
- **严重级别**: Minor
- **建议**: `TODO @username: description`

#### 复杂逻辑注释
- **规则**: 超过 10 行的逻辑块应有注释
- **检测方式**: 检测无注释的长代码块
- **严重级别**: Minor
- **建议**: 添加解释性注释

---

## 2. Security Rules

### 2.1 Secrets Detection

#### API Key 泄露
- **规则**: 检测硬编码的 API Key
- **正则**: `api[_-]?key\s*[:=]\s*['"][^'"]+['"]`
- **严重级别**: Critical
- **建议**: 使用环境变量

#### Password 泄露
- **规则**: 检测硬编码的密码
- **正则**: `password\s*[:=]\s*['"][^'"]+['"]`
- **严重级别**: Critical
- **建议**: 使用环境变量

#### Token 泄露
- **规则**: 检测硬编码的 Token
- **正则**: `token\s*[:=]\s*['"][^'"]+['"]`
- **严重级别**: Critical
- **建议**: 使用环境变量

### 2.2 SQL Injection

#### 字符串拼接 SQL
- **规则**: 检测字符串拼接构造 SQL 查询
- **正则**: `["'].*SELECT.*\+.*["']`
- **严重级别**: Critical
- **建议**: 使用参数化查询

#### 未参数化查询
- **规则**: 检测 execute + 字符串拼接
- **正则**: `execute\(.*\+.*\)`
- **严重级别**: Critical
- **建议**: 使用参数绑定

### 2.3 XSS Prevention

#### innerHTML 赋值
- **规则**: 检测 innerHTML 直接赋值用户输入
- **正则**: `\.innerHTML\s*=\s*[^;]*\+`
- **严重级别**: Critical
- **建议**: 使用 textContent 或 DOM API

#### eval 使用
- **规则**: 检测 eval 函数使用
- **正则**: `eval\(.*\)`
- **严重级别**: Critical
- **建议**: 使用 JSON.parse 或其他安全方式

---

## 3. Performance Rules

### 3.1 Algorithm Complexity

#### 嵌套循环
- **规则**: 检测 3 层及以上嵌套循环
- **检测方式**: 统计 for/while 嵌套层数
- **严重级别**: Important
- **建议**: 优化算法或使用数据结构优化

#### O(n²) 模式
- **规则**: 检测循环内调用 O(n) 操作
- **检测方式**: 上下文分析
- **严重级别**: Important
- **建议**: 使用 Map/Set 优化查找

### 3.2 Resource Usage

#### 未关闭连接
- **规则**: 检测 Connection/Stream 未调用 close()
- **正则**: `(Connection|Stream).*new.*(?!.*close\(\))`
- **严重级别**: Important
- **建议**: 使用 try-with-resources 或 finally

#### 大对象循环
- **规则**: 检测循环内创建大对象
- **检测方式**: 上下文分析
- **严重级别**: Minor
- **建议**: 将对象创建移至循环外

### 3.3 Database Performance

#### N+1 查询
- **规则**: 检测循环内执行数据库查询
- **正则**: `for\s*\(.*\{[\s\S]*?(execute|query)\(.*\}`
- **严重级别**: Important
- **建议**: 使用 JOIN 或批量查询

---

## 4. Project Standards Rules

### 4.1 Commit Message

#### 格式检查
- **规则**: Commit message 必须符合约定格式
- **正则**: `^(feat|fix|docs|style|refactor|test|chore): .{10,}`
- **严重级别**: Minor
- **建议**: `feat: add user authentication`

### 4.2 File Organization

#### 文件命名
- **规则**: 文件名应符合项目约定
- **检测方式**: 根据语言规范检查
- **严重级别**: Minor
- **建议**: 遵循项目命名规范

---

## 5. Rule Execution Strategy

### 5.1 执行顺序

1. **快速扫描**: 使用正则表达式快速匹配（所有文件）
2. **逐行分析**: 对变更文件逐行检查
3. **上下文分析**: 对检测到的复杂问题进行上下文分析

### 5.2 降级策略

- 如果检测到大量匹配（>100），仅报告前 20 个
- 对于误报率高的规则，降低严重级别

---

## 6. Rule Categories Summary

| 类别 | 规则数量 | 典型严重级别 |
|------|---------|-------------|
| Code Quality | 8 | Minor/Important |
| Security | 8 | Critical |
| Performance | 5 | Important |
| Project Standards | 2 | Minor |

**总计**: 23 条静态规则
