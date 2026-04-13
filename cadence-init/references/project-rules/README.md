# 项目个性化规则文档

## 强制约束

> **🔴 以下规则必须遵守**

### 规则目录划分

| 目录 | 用途 | 管理者 |
|------|------|--------|
| `.claude/rules/` | 框架内置规则文件 | 框架维护者 |
| `.claude/project-rules/` | 用户自定义规则文件 | 用户 |

### 禁止行为

- ❌ **禁止**在 `.claude/rules/` 目录中添加用户自定义规则
- ❌ **禁止**直接修改 `.claude/rules/` 目录下的框架内置规则文件
- ❌ **禁止**在项目根目录创建规则文件

### 正确做法

- ✅ 用户自定义规则放在 `.claude/project-rules/` 目录
- ✅ 从 `examples/` 目录复制模板并修改
- ✅ 在 `CLAUDE.md` 中添加规则引用以启用

## 📖 目录说明

本目录用于存放项目个性化的规则文档，包括模板、规范、约定等。

## 🎯 使用方法

### 步骤 1：浏览示例

查看 `examples/` 目录中的示例文件，了解可以定制的内容。

### 步骤 2：创建您的规则

1. 复制 `examples/` 中的模板到本目录
2. 根据您的项目需求修改内容
3. 重命名为合适的文件名（不含 `examples/` 前缀）

### 步骤 3：在 CLAUDE.md 中启用

在项目根目录的 `CLAUDE.md` 中添加规则，指导 Claude 使用您的定制文档。

**示例：**

```markdown
## 项目个性化规则

### 需求文档格式
使用 `.claude/project-rules/requirement-template.md` 作为需求文档格式，
不要使用 requirement skill 中的通用格式。

### 设计文档格式
使用 `.claude/project-rules/design-template.md` 作为设计文档模板。

### 代码开发规范
所有代码开发必须遵循 `.claude/project-rules/coding-standards.md` 中的规范。
```

## 📁 文件说明

### requirement-template.md
需求文档模板，定义需求文档的格式和内容结构。

### design-template.md
设计文档模板，定义设计文档的格式和内容结构。

### coding-standards.md
代码开发规范，包括命名规范、代码风格、注释规范等。

### test-standards.md
测试规范，包括测试覆盖率要求、测试类型要求、测试命名规范等。

## 💡 提示

- 只创建您需要的规则文档，不必全部创建
- 规则文档可以根据项目需求随时调整
- 在 CLAUDE.md 中明确说明何时使用哪个规则文档

## 📝 示例文件

所有示例文件都在 `examples/` 目录中，包含详细的注释和说明。
