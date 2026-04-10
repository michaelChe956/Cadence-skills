# 计划文档：rule-config 命令修复

## 背景

`cadence-init:rule-config` 命令存在两个问题：
1. 步骤 1 的模板路径描述不明确，执行者无法找到模板文件
2. `code-usage.md` 规则模板写死了「非必要不编写代码」，不适用于编码项目

## 修改范围

仅涉及 `cadence-init` skill 内的文件：
- `cadence-init/commands/rule-config.md` — 修改步骤 1 和步骤 2 的逻辑
- `cadence-init/references/rules/code-usage-coding.md` — 新增（编码项目模板）
- `cadence-init/references/rules/code-usage-noncoding.md` — 新增（非编码项目模板）
- `cadence-init/references/rules/code-usage.md` — 删除（拆分为上面两个文件）

## 设计详情

### 修改 1：模板路径定位（步骤 1）

**问题**：当前写「从 `references/rules/` 读取模板」，但执行者不知道这个路径在哪里。

**方案**：在步骤 1 中增加前置子步骤「定位模板目录」。

具体改写：

1. 使用 Glob 工具搜索标识文件 `**/cadence-init/references/rules/language.md`
2. 从返回结果中提取目录路径（去掉末尾 `language.md`），作为模板根路径
3. 如果匹配多个结果，取排序最后一个（通常是最新版本）
4. 后续文件复制操作都基于该绝对路径执行

步骤 1 改写后的结构：

````markdown
### 1. 创建 rules 目录和规则文件

**步骤 1a：项目类型检测**

使用 Glob 工具搜索常见源代码文件：
```glob
**/*.{java,js,ts,py,go,php,rs,rb,swift,kt,c,cpp,cs}
```
- 如果匹配到任何结果 → Coding 项目
- 如果没有匹配结果 → 非 Coding 项目

**步骤 1b：定位模板目录**

使用 Glob 工具搜索标识文件：
```glob
**/cadence-init/references/rules/language.md
```
从返回结果中提取目录路径（去掉末尾 `language.md`），作为模板根路径。
如果匹配多个，取排序最后一个。

**步骤 1c：创建目标目录**

```bash
mkdir -p .claude/rules
```

**步骤 1d：从模板根路径复制规则文件**

将以下文件从 [模板根路径] 复制到 `.claude/rules/`：

| 源文件 | 目标文件 | 条件 |
|--------|---------|------|
| `README.md` | `.claude/rules/README.md` | 必选 |
| `language.md` | `.claude/rules/language.md` | 必选 |
| `document-storage.md` | `.claude/rules/document-storage.md` | 必选 |
| `markdown-format.md` | `.claude/rules/markdown-format.md` | 必选 |
| `serena-usage.md` | `.claude/rules/serena-usage.md` | 必选 |
| `code-usage-coding.md` | `.claude/rules/code-usage.md` | Coding 项目 |
| `code-usage-noncoding.md` | `.claude/rules/code-usage.md` | 非 Coding 项目 |
````

### 修改 2：code-usage 规则区分项目类型

**问题**：`code-usage.md` 写死了非编码项目规则，编码项目不适用。

**方案**：拆分为两套模板，根据项目类型选择。

#### 2a. 新增模板文件

**`code-usage-coding.md`**（编码项目适用）：

核心内容：
- 鼓励编码，遵循 TDD 流程
- 代码质量要求：规范、可读、可维护
- 测试覆盖要求
- 安全编码规范

**`code-usage-noncoding.md`**（非编码项目适用）：

核心内容：
- 与当前 `code-usage.md` 内容一致
- 非必要不编写代码
- 必须说明编写代码的理由
- 优先替代方案

#### 2b. CLAUDE.md 摘要引用区分

步骤 2 中 CLAUDE.md 的规则 2 摘要根据项目类型调整：

- **Coding 项目**：`- **遵循 TDD 和代码规范** → 详见 .claude/rules/code-usage.md`
- **非 Coding 项目**：`- **非必要不编写代码** → 详见 .claude/rules/code-usage.md`

#### 2c. 文件变更

- 删除：`references/rules/code-usage.md`
- 新增：`references/rules/code-usage-coding.md`
- 新增：`references/rules/code-usage-noncoding.md`
- 更新：`references/rules/README.md`（文件列表同步更新）

## 不变的部分

以下内容不做修改：
- 步骤 3（包管理器规则）
- 步骤 4（技术栈检测）
- 步骤 5（目录结构创建）
- 步骤 6（Playwright 配置）
- 其他模板文件（language.md、document-storage.md 等）
