## 代码阅读规则

> **结构化优先，避免盲读整片代码**

### 核心原则

- **优先使用 `ast-grep outline` 获取结构化大纲** - 在阅读、检索、理解代码时，必须优先使用 `ast-grep outline` 命令获取文件或目录的结构化大纲（函数、类、结构体、导入导出、成员及其源码区间），再基于大纲决定要精读哪一段，避免直接整文件盲读造成 token 浪费与上下文污染。
- **基于大纲定向精读** - 拿到大纲后，仅对真正需要的符号/区间做进一步阅读；先用 `--match` / `--view` 展开目标符号的签名或成员，再决定是否需要读取完整实现。
- **检索代码时同样适用** - 查找“某个符号定义在哪”“某个模块导出了什么”“谁导入某个依赖”等结构化问题时，优先用 `ast-grep outline` 而非 `grep` 或整文件读取。

### 命令使用方式

```sh
# 查看单个文件的结构化大纲（函数、类、成员、源码区间）
ast-grep outline src/parser.ts

# 查看整个目录的结构化大纲（默认仅导出项）
ast-grep outline src

# 只查看某个文件的导入项
ast-grep outline src/parser.ts --items imports

# 展开匹配符号的成员/签名（不读完整实现）
ast-grep outline src/parser.ts --match Parser --type class --view expanded

# 在目录范围内查找匹配的导入
ast-grep outline src --items imports --match ast-grep-core --view signatures
```

### 常用参数

| 参数 | 作用 |
|------|------|
| `--items` | 控制提取内容，如 `imports`（默认为声明项） |
| `--match` | 按符号名过滤结果 |
| `--type` | 按符号类型收窄，如 `class` |
| `--view` | 控制详细程度，如 `expanded`（展开成员）、`signatures`（仅签名首行） |

### 适用场景判断

- ✅ **鼓励**：理解陌生文件结构、定位符号定义、梳理模块导出/导入关系、决定下一步精读范围。
- ✅ **鼓励**：在大型仓库中先用 outline 建立结构地图，再按需深入。
- ⚠️ **需说明**：当目标文件极小（如十几行的配置/模块）或已明确需要完整实现时，可直接读取，但应说明跳过 outline 的原因。
- ❌ **避免**：不先看大纲直接整文件读取大型源码文件；避免用 `grep` 替代 outline 做结构化定位。

### 参考资源

- 获取命令帮助：`ast-grep outline --help`
- 设计说明与背景：https://ast-grep.github.io/blog/ast-grep-outline.html#why-outline
