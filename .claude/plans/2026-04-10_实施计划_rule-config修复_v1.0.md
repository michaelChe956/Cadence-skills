# rule-config 命令修复 实施计划

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 修复 rule-config 命令的模板路径定位问题和 code-usage 规则的项目类型适配问题。

**Architecture:** 拆分 code-usage.md 为两套模板（coding/noncoding），通过 Glob 动态定位 skill 安装路径解决模板查找问题，增加项目类型检测逻辑区分编码与非编码项目。

**Tech Stack:** Markdown 文档编辑（无代码）

**Spec:** `.claude/plans/2026-04-10_计划文档_技能优化_rule-config修复_v1.0.md`

---

## File Structure

| 操作 | 文件路径 | 职责 |
|------|---------|------|
| **Create** | `cadence-init/references/rules/code-usage-coding.md` | 编码项目的代码使用规则模板 |
| **Create** | `cadence-init/references/rules/code-usage-noncoding.md` | 非编码项目的代码使用规则模板 |
| **Delete** | `cadence-init/references/rules/code-usage.md` | 已拆分为上面两个文件 |
| **Modify** | `cadence-init/references/rules/README.md` | 更新文件列表（code-usage 一条变两条） |
| **Modify** | `cadence-init/commands/rule-config.md` | 重写步骤 1、步骤 2、步骤 6 |

---

## Chunk 1: 模板文件变更

### Task 1: 创建 code-usage-coding.md 模板

**Files:**
- Create: `cadence-init/references/rules/code-usage-coding.md`

- [ ] **Step 1: 创建编码项目模板文件**

在 `cadence-init/references/rules/` 目录下创建 `code-usage-coding.md`，内容如下：

```markdown
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
```

- [ ] **Step 2: 验证文件创建成功**

确认 `cadence-init/references/rules/code-usage-coding.md` 存在且内容正确。

---

### Task 2: 创建 code-usage-noncoding.md 模板

**Files:**
- Create: `cadence-init/references/rules/code-usage-noncoding.md`

- [ ] **Step 1: 创建非编码项目模板文件**

在 `cadence-init/references/rules/` 目录下创建 `code-usage-noncoding.md`，内容与当前 `code-usage.md` 完全一致：

```markdown
## 代码使用规则

> **Skills 项目特殊规定**

- **非必要不编写代码** - 这是一个 Skills/Commands 配置项目，主要工作对象是 Markdown 文档、YAML 配置、JSON 数据等非代码文件。
- **必须说明理由** - 如果确实需要编写代码（如脚本、验证工具等），必须先向用户说明为什么必须使用代码，以及代码的作用和必要性。
- **优先替代方案** - 在决定编写代码前，必须先考虑是否可以通过纯文档方式、现有工具或配置文件完成相同目标。

**适用场景判断**：
- ✅ **允许**：文档编写、配置文件编辑、结构设计、方案规划、需求分析
- ⚠️ **需说明**：辅助脚本、验证工具、自动化处理（必须先说明必要性）
- ❌ **避免**：功能开发、业务逻辑实现、应用程序编写
```

- [ ] **Step 2: 验证文件创建成功**

确认 `cadence-init/references/rules/code-usage-noncoding.md` 存在且内容正确。

---

### Task 3: 删除旧 code-usage.md 并更新 README.md

**Files:**
- Delete: `cadence-init/references/rules/code-usage.md`
- Modify: `cadence-init/references/rules/README.md`

- [ ] **Step 1: 删除旧的 code-usage.md**

删除 `cadence-init/references/rules/code-usage.md`（内容已复制到 code-usage-noncoding.md）。

- [ ] **Step 2: 更新 README.md 文件列表**

将 `cadence-init/references/rules/README.md` 中第 12 行：

```markdown
| `code-usage.md` | 代码使用规则（非必要不编写代码） |
```

替换为两行：

```markdown
| `code-usage-coding.md` | 代码使用规则（编码项目适用） |
| `code-usage-noncoding.md` | 代码使用规则（非编码项目适用） |
```

- [ ] **Step 3: 验证变更**

确认：
- `code-usage.md` 已不存在
- `README.md` 文件列表包含 `code-usage-coding.md` 和 `code-usage-noncoding.md`

- [ ] **Step 4: 提交模板变更**

```bash
git add cadence-init/references/rules/code-usage-coding.md cadence-init/references/rules/code-usage-noncoding.md cadence-init/references/rules/README.md
git rm cadence-init/references/rules/code-usage.md
git commit -m "feat: split code-usage rule into coding/noncoding templates"
```

---

## Chunk 2: 命令文件重写

### Task 4: 重写 rule-config.md 步骤 1（模板路径定位 + 项目类型检测）

**Files:**
- Modify: `cadence-init/commands/rule-config.md`（第 16 行和第 27-47 行）

- [ ] **Step 1: 更新检查清单中的步骤 1 描述**

将第 16 行：

```markdown
1. **创建 rules 目录和规则文件** — 从 `references/rules/` 读取模板，创建到 `.claude/rules/`
```

替换为：

```markdown
1. **创建 rules 目录和规则文件** — 检测项目类型，定位模板目录，复制规则文件到 `.claude/rules/`
```

- [ ] **Step 2: 重写处理流程的步骤 1 整体内容**

将第 27-47 行（从 `### 1. 创建 rules 目录和规则文件` 到 `| \`references/rules/serena-usage.md\` | \`.claude/rules/serena-usage.md\` |`）整体替换为以下内容：

````markdown
### 1. 创建 rules 目录和规则文件

**步骤 1a：项目类型检测**

使用 Glob 工具搜索常见源代码文件，**排除框架内部目录**：

先使用 Glob 搜索：
```
**/*.{java,js,ts,py,go,php,rs,rb,swift,kt,c,cpp,cs}
```

从搜索结果中**排除**路径包含以下关键词的匹配：
- `cadence-init/`
- `Cadence-skills/`
- `.claude-plugin/`
- `node_modules/`

排除后：
- 如果仍有匹配结果 → **Coding 项目**
- 如果没有匹配结果或所有结果都被排除 → **非 Coding 项目**

检测结果需**展示给用户确认**：向用户说明检测结果和依据，允许用户手动修正。

**步骤 1b：定位模板目录**

使用 Glob 工具搜索标识文件：
```
**/cadence-init/references/rules/language.md
```
从返回结果中提取目录路径（去掉末尾 `language.md`），作为**模板根路径**。
如果匹配多个，验证每个路径下是否同时存在 `document-storage.md`，
从通过验证的结果中取修改时间最新的。

> **重要**：此模板根路径需在后续所有步骤中复用（包括步骤 6 的 playwright.md）。

**步骤 1c：创建目标目录**

```bash
mkdir -p .claude/rules
```

**步骤 1d：从模板根路径复制规则文件**

将以下文件从 [步骤 1b 定位的模板根路径] 读取内容，写入项目的 `.claude/rules/` 目录：

| 源文件名 | 目标文件 | 条件 |
|----------|---------|------|
| `README.md` | `.claude/rules/README.md` | 必选 |
| `language.md` | `.claude/rules/language.md` | 必选 |
| `document-storage.md` | `.claude/rules/document-storage.md` | 必选 |
| `markdown-format.md` | `.claude/rules/markdown-format.md` | 必选 |
| `serena-usage.md` | `.claude/rules/serena-usage.md` | 必选 |
| `mcp-servers.md` | `.claude/rules/mcp-servers.md` | 必选 |
| `code-usage-coding.md` | `.claude/rules/code-usage.md` | Coding 项目 |
| `code-usage-noncoding.md` | `.claude/rules/code-usage.md` | 非 Coding 项目 |
````

- [ ] **Step 3: 验证步骤 1 改写正确**

确认新的步骤 1 包含 1a（项目类型检测）、1b（定位模板目录）、1c（创建目录）、1d（复制文件）四个子步骤，且复制表格包含条件列。

---

### Task 5: 更新 rule-config.md 步骤 2（CLAUDE.md 规则引用区分项目类型）

**Files:**
- Modify: `cadence-init/commands/rule-config.md`（第 66-67 行，位于步骤 2 的 CLAUDE.md 模板输出块内部）

**背景**：步骤 2 中有一个用 4 反引号包裹的 CLAUDE.md 输出模板（第 52-90 行）。规则 2 的摘要行在这个模板块内部。需要将固定文本改为条件分支指令，让执行者根据步骤 1a 的检测结果选择对应摘要行。

- [ ] **Step 1: 更新检查清单中步骤 2 的描述**

将第 17 行：

```markdown
2. **添加 CLAUDE.md 规则引用** — 在 CLAUDE.md 中添加全部 8 条规则的摘要引用
```

替换为：

```markdown
2. **添加 CLAUDE.md 规则引用** — 在 CLAUDE.md 中添加全部 8 条规则的摘要引用（规则 2 根据步骤 1a 检测结果选择对应文本）
```

- [ ] **Step 2: 更新规则 2 的摘要文本**

在步骤 2 的 CLAUDE.md 模板输出块内部，将第 66-67 行：

```markdown
### 2. 代码使用规则
- **非必要不编写代码**（Skills 项目特殊规定） → 详见 `.claude/rules/code-usage.md`
```

替换为（注意：这是写入命令文件的条件分支指令，不是直接写入用户 CLAUDE.md 的内容）：

```markdown
### 2. 代码使用规则
- **Coding 项目**：`- **遵循 TDD 和代码规范** → 详见 .claude/rules/code-usage.md`
- **非 Coding 项目**：`- **非必要不编写代码** → 详见 .claude/rules/code-usage.md`
```

同时在模板块外、步骤 2 的**注意**部分（原第 92-95 行）追加一条说明：

```markdown
- 规则 2（代码使用规则）根据步骤 1a 的项目类型检测结果选择对应摘要行
```

- [ ] **Step 3: 验证步骤 2 改写正确**

确认：
- CLAUDE.md 模板输出块中规则 2 有两条条件分支选项
- 注意部分新增了规则 2 条件说明
- 模板块的 4 反引号包裹没有被破坏

---

### Task 6: 更新 rule-config.md 步骤 6（Playwright 路径统一）

**Files:**
- Modify: `cadence-init/commands/rule-config.md`（第 198 行）

- [ ] **Step 1: 更新步骤 6 的模板路径引用**

将第 198 行：

```markdown
**创建规则文件**：将 `references/rules/playwright.md` 复制到 `.claude/rules/playwright.md`
```

替换为：

```markdown
**创建规则文件**：将 [步骤 1b 定位的模板根路径] 中的 `playwright.md` 读取内容，写入 `.claude/rules/playwright.md`
```

- [ ] **Step 2: 验证步骤 6 改写正确**

确认步骤 6 不再使用 `references/rules/` 相对路径，而是引用步骤 1b 定位的模板根路径。

---

### Task 7: 最终验证并提交

- [ ] **Step 1: 完整阅读修改后的 rule-config.md**

通读整个文件，确认：
- 检查清单步骤 1 描述已更新
- 检查清单步骤 2 描述已更新（包含规则 2 条件说明）
- 处理流程步骤 1 包含 1a/1b/1c/1d 四个子步骤
- 步骤 2 CLAUDE.md 模板中规则 2 有条件分支
- 步骤 2 注意部分包含规则 2 条件说明
- 步骤 6 使用模板根路径引用
- 步骤 3-5 和核心原则部分未被修改
- 4 反引号包裹完整无破损

- [ ] **Step 2: 检查变更范围**

```bash
git diff --cached cadence-init/commands/rule-config.md
```

确认只有 `rule-config.md` 被暂存，且变更内容符合预期。

- [ ] **Step 3: 提交命令文件变更**

```bash
git add cadence-init/commands/rule-config.md
git commit -m "fix: rewrite rule-config command with dynamic template path and project type detection"
```
