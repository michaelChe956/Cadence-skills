# 计划文档：rule-config 命令修复

## 背景

`cadence-init:rule-config` 命令存在两个问题：
1. 步骤 1 的模板路径描述不明确，执行者无法找到模板文件
2. `code-usage.md` 规则模板写死了「非必要不编写代码」，不适用于编码项目

## 修改范围

仅涉及 `cadence-init` skill 内的文件：
- `cadence-init/commands/rule-config.md` — 修改步骤 1、步骤 2 和步骤 6 的逻辑
- `cadence-init/references/rules/code-usage-coding.md` — 新增（编码项目模板）
- `cadence-init/references/rules/code-usage-noncoding.md` — 新增（非编码项目模板）
- `cadence-init/references/rules/code-usage.md` — 删除（拆分为上面两个文件）
- `cadence-init/references/rules/README.md` — 更新文件列表

## 设计详情

### 修改 1：模板路径定位（步骤 1）

**问题**：当前写「从 `references/rules/` 读取模板」，但执行者不知道这个路径在哪里。

**方案**：在步骤 1 中增加前置子步骤「定位模板目录」，定位后的路径供所有步骤共用（包括步骤 6 的 playwright.md）。

具体改写：

1. 使用 Glob 工具搜索标识文件 `**/cadence-init/references/rules/language.md`
2. 从返回结果中提取目录路径（去掉末尾 `language.md`），作为模板根路径
3. 如果匹配多个结果，验证每个路径下是否包含 `document-storage.md`（确认是完整模板目录），从通过验证的结果中取修改时间最新的
4. 后续所有步骤的文件复制操作都基于该绝对路径执行

步骤 1 改写后的结构：

````markdown
### 1. 创建 rules 目录和规则文件

**步骤 1a：项目类型检测**

使用 Glob 工具搜索常见源代码文件，**排除框架内部目录**：

先使用 Glob 搜索：
```glob
**/*.{java,js,ts,py,go,php,rs,rb,swift,kt,c,cpp,cs}
```

从搜索结果中**排除**路径包含以下关键词的匹配：
- `cadence-init/`
- `Cadence-skills/`
- `.claude-plugin/`
- `node_modules/`

排除后：
- 如果仍有匹配结果 → Coding 项目
- 如果没有匹配结果或所有结果都被排除 → 非 Coding 项目

检测结果需**展示给用户确认**：向用户说明检测结果和依据，允许用户手动修正。

**步骤 1b：定位模板目录**

使用 Glob 工具搜索标识文件：
```glob
**/cadence-init/references/rules/language.md
```
从返回结果中提取目录路径（去掉末尾 `language.md`），作为模板根路径。
如果匹配多个，验证每个路径下是否同时存在 `document-storage.md`，
从通过验证的结果中取修改时间最新的。

**步骤 1c：创建目标目录**

```bash
mkdir -p .claude/rules
```

**步骤 1d：从模板根路径复制规则文件**

将以下文件从 [步骤 1b 定位的模板根路径] 复制到 `.claude/rules/`：

| 源文件 | 目标文件 | 条件 |
|--------|---------|------|
| `README.md` | `.claude/rules/README.md` | 必选 |
| `language.md` | `.claude/rules/language.md` | 必选 |
| `document-storage.md` | `.claude/rules/document-storage.md` | 必选 |
| `markdown-format.md` | `.claude/rules/markdown-format.md` | 必选 |
| `serena-usage.md` | `.claude/rules/serena-usage.md` | 必选 |
| `mcp-servers.md` | `.claude/rules/mcp-servers.md` | 必选 |
| `code-usage-coding.md` | `.claude/rules/code-usage.md` | Coding 项目 |
| `code-usage-noncoding.md` | `.claude/rules/code-usage.md` | 非 Coding 项目 |

> **注意**：步骤 1b 定位的模板根路径应被后续所有步骤引用。
> 步骤 6 的 `references/rules/playwright.md` 也应使用该路径。
````

### 修改 2：code-usage 规则区分项目类型

**问题**：`code-usage.md` 写死了非编码项目规则，编码项目不适用。

**方案**：拆分为两套模板，根据项目类型选择。

#### 2a. 新增模板文件

**`code-usage-coding.md`**（编码项目适用）：

完整模板内容：

````markdown
## 代码使用规则

> **编码项目规范**

- **遵循 TDD 流程** - 先写测试，再写实现。新功能必须有对应测试，Bug 修复必须有回归测试。
- **代码质量要求** - 编写可读、可维护、可测试的代码。遵循项目既有的代码风格和命名规范。
- **安全编码** - 遵循 OWASP 安全最佳实践，避免引入 XSS、SQL 注入、命令注入等安全漏洞。
- **增量交付** - 小步提交，每次提交保持原子性。避免一次性大范围重构。

**适用场景判断**：
- ✅ **鼓励**：功能开发、Bug 修复、性能优化、重构改进
- ⚠️ **需说明**：引入新依赖、修改公共 API、跨模块变更（需说明影响范围）
- ❌ **避免**：过度工程、过早优化、无测试覆盖的代码提交
````

**`code-usage-noncoding.md`**（非编码项目适用）：

与当前 `code-usage.md` 内容完全一致：

````markdown
## 代码使用规则

> **Skills 项目特殊规定**

- **非必要不编写代码** - 这是一个 Skills/Commands 配置项目，主要工作对象是 Markdown 文档、YAML 配置、JSON 数据等非代码文件。
- **必须说明理由** - 如果确实需要编写代码（如脚本、验证工具等），必须先向用户说明为什么必须使用代码，以及代码的作用和必要性。
- **优先替代方案** - 在决定编写代码前，必须先考虑是否可以通过纯文档方式、现有工具或配置文件完成相同目标。

**适用场景判断**：
- ✅ **允许**：文档编写、配置文件编辑、结构设计、方案规划、需求分析
- ⚠️ **需说明**：辅助脚本、验证工具、自动化处理（必须先说明必要性）
- ❌ **避免**：功能开发、业务逻辑实现、应用程序编写
````

#### 2b. CLAUDE.md 摘要引用区分

步骤 2 中 CLAUDE.md 的规则 2 摘要根据项目类型调整：

- **Coding 项目**：`- **遵循 TDD 和代码规范** → 详见 .claude/rules/code-usage.md`
- **非 Coding 项目**：`- **非必要不编写代码** → 详见 .claude/rules/code-usage.md`

#### 2c. 文件变更

- 删除：`references/rules/code-usage.md`
- 新增：`references/rules/code-usage-coding.md`
- 新增：`references/rules/code-usage-noncoding.md`
- 更新：`references/rules/README.md`（文件列表更新为两条）

README.md 文件列表更新后的表格：

```markdown
| 文件 | 内容概述 |
|------|---------|
| `language.md` | 语言规则（中文回答要求） |
| `code-usage-coding.md` | 代码使用规则（编码项目适用） |
| `code-usage-noncoding.md` | 代码使用规则（非编码项目适用） |
| `document-storage.md` | 文档存储规则（目录、命名、路径映射） |
| `markdown-format.md` | Markdown 格式规则（代码块嵌套） |
| `serena-usage.md` | Serena MCP 使用规则 |
| `mcp-servers.md` | MCP Server 使用规则（所有 MCP 工具） |
| `playwright.md` | Playwright CLI 使用规则 |
```

### 修改 3：步骤 6 路径统一

**问题**：步骤 6 中 playwright.md 的复制也使用了相对路径 `references/rules/playwright.md`，与步骤 1 要解决的路径问题相同。

**方案**：在步骤 6 中明确使用步骤 1b 定位的模板根路径，将：
> 将 `references/rules/playwright.md` 复制到 `.claude/rules/playwright.md`

改为：
> 将 `[模板根路径]/playwright.md` 复制到 `.claude/rules/playwright.md`

## 不变的部分

以下内容不做修改：
- 步骤 3（包管理器规则）
- 步骤 4（技术栈检测）
- 步骤 5（目录结构创建）
- 其他模板文件（language.md、document-storage.md、serena-usage.md、markdown-format.md、mcp-servers.md、playwright.md）
