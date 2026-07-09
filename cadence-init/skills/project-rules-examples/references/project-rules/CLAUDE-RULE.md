## 项目个性化规则

> **🔴 强制规则**
>
> - 用户自定义规则**只能**存放在 `cadence/project-rules/` 目录
> - **禁止**在 `.claude/rules/` 目录中添加用户自定义规则
> - **禁止**直接修改 `.claude/rules/` 目录下的框架内置规则文件
> - 框架内置规则由维护者管理，详见 `.claude/rules/README.md`

- **规则目录**：`cadence/project-rules/`
- **使用方法**：
  1. 查看项目初始化时创建的示例文件（`examples/` 目录）
  2. 根据需要复制和修改示例文件到 `project-rules/` 目录
  3. 在本文件（CLAUDE.md）中添加规则引用，指导 Claude 使用您的定制文档

**示例规则**：

````markdown
## 项目个性化规则

> 以下是使用示例，默认不启用。
> 如果您创建了自定义规则，可以取消注释或添加类似规则：

<!--
### 需求文档格式
使用 `cadence/project-rules/requirement-template.md` 作为需求文档格式，
不要使用 requirement skill 中的通用格式。

### 设计文档格式
使用 `cadence/project-rules/design-template.md` 作为设计文档模板。

### 代码开发规范
所有代码开发必须遵循 `cadence/project-rules/coding-standards.md` 中的规范。
-->
````

**说明**：
- 个性化规则由用户主动启用
- Claude Code 会自动遵循 CLAUDE.md 中的规则
- 示例文件仅作参考，不强制使用
- 用户可以根据项目需求自由定制规则内容
