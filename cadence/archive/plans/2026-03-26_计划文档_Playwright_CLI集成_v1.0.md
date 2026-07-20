# Playwright CLI with SKILLS 集成实施计划

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 Cadence-skills 项目中集成 Playwright CLI with SKILLS，使其成为 pre-check 检查项，并提供完善的使用规则。

**Architecture:**
1. 在 pre-check 中增加 playwright-cli 的检查和自动安装
2. 在 rule-config 中增加 playwright skills 的使用规则配置
3. Playwright CLI 以全局 npm 包形式安装，skills 以 `playwright-cli install --skills` 安装到全局

**Tech Stack:** Node.js, npm, Playwright CLI

---

## Chunk 1: Pre-check 集成

### Task 1: 更新 pre-check.md 增加 Playwright CLI 检查

**Files:**
- Modify: `commands/pre-check.md`

**目标：** 在现有检查流程（npx、uvx、serena）后增加 playwright-cli 的检查和安装步骤。

- [ ] **Step 1: 分析现有 pre-check.md 结构**

当前结构：
- npx 检查（步骤1）
- uvx 检查（步骤2）
- serena 检查（步骤3）

需要在 serena 检查后增加 playwright-cli 检查（步骤4）。

- [ ] **Step 2: 添加 playwright-cli 检查功能描述**

在 `## 功能` 部分增加：

```markdown
4. **playwright-cli** - Playwright CLI with SKILLS
   - 检查是否全局安装 @playwright/cli
   - 自动安装缺失的 playwright-cli
   - 自动安装 Playwright skills
```

- [ ] **Step 3: 更新检查流程图**

将现有流程图：
```markdown
## 检查流程

```dot
检查 npx → 检查 uvx → 检查 serena → 用户选择 → 验证配置 → 完成
```
```

修改为：
```markdown
## 检查流程

```dot
检查 npx → 检查 uvx → 检查 serena → 用户选择 → 验证配置 → 检查 playwright-cli → 完成
```
```

- [ ] **Step 4: 更新重要规则说明**

将：
```markdown
**重要**：所有三个步骤都必须完成，不允许跳过任何步骤。
```

修改为：
```markdown
**重要**：所有四个步骤都必须完成，不允许跳过任何步骤。
```

- [ ] **Step 5: 添加 playwright-cli 检查详细说明**

在 `## serena github地址` 后增加：

```markdown
## playwright-cli 安装

### 检查命令

```bash
# 检查 playwright-cli 是否已安装
which playwright-cli || npm list -g @playwright/cli
```

### 安装命令

```bash
# 全局安装 Playwright CLI
npm install -g @playwright/cli@latest

# 安装 Playwright Skills（供 Claude Code 等 coding agents 使用）
playwright-cli install --skills
```

### 验证安装

```bash
# 验证 playwright-cli 安装成功
playwright-cli --help

# 验证 skills 安装成功（检查全局 skills 目录）
ls ~/.claude/skills/playwright-cli 2>/dev/null || echo "Skills not found"
```

### 说明

- **用途**：浏览器自动化测试、表单填写、截图、数据提取
- **特点**：Token-efficient，不会强制将页面数据加载到 LLM
- **Skills**：安装后 Claude Code 可自动识别并使用 Playwright skills
```

- [ ] **Step 6: 更新强制规则**

将现有强制规则：
```markdown
## 强制规则

- 所有与用户的交互必须使用中文
- 必须完成所有三个步骤（npx、uvx、serena）
- serena 配置必须询问用户选择，提供三个选项
- 验证失败必须重新选择，不能跳过
- 必须验证配置成功后才能继续
```

修改为：
```markdown
## 强制规则

- 所有与用户的交互必须使用中文
- 必须完成所有四个步骤（npx、uvx、serena、playwright-cli）
- serena 配置必须询问用户选择，提供三个选项
- 验证失败必须重新选择，不能跳过
- 必须验证配置成功后才能继续
- playwright-cli 安装失败必须提供手动安装命令
```

---

## Chunk 2: Rule-config 集成

### Task 2: 更新 rule-config.md 增加 Playwright Skills 使用规则

**Files:**
- Modify: `commands/init/rule-config.md`

**目标：** 在规则配置中增加 Playwright Skills 的使用规则，使其成为项目初始化时的可选配置项。

- [ ] **Step 1: 分析现有 rule-config.md 结构**

当前结构：
1. 语言规则配置
2. 文档存储规则配置
3. 文档命名规则配置
4. 包管理器规则
5. 技术栈检测
6. 目录结构创建

需要增加：
7. Playwright Skills 使用规则配置（可选）

- [ ] **Step 2: 添加新检查清单项**

在 `## 检查清单` 中增加：

```markdown
7. **Playwright Skills 规则配置** — 配置 Playwright CLI 的使用规则（可选）
```

- [ ] **Step 3: 添加 Playwright Skills 规则配置章节**

在 `### 6. 目录结构创建` 后增加：

```markdown
### 7. Playwright Skills 规则配置

**检测条件**：
- 用户需要浏览器自动化功能
- 项目涉及 Web 测试、表单填写、截图、数据提取

**添加以下规则到 CLAUDE.md**：

```markdown
## Playwright CLI 使用规则

> **浏览器自动化工具规范**

### 用途

Playwright CLI 是一个 Token-efficient 的浏览器自动化工具，适合：
- Web 应用测试
- 表单自动填写
- 网页截图
- 数据提取
- 网站导航和交互

### 触发场景

- 用户需要测试 Web 应用
- 用户需要自动填写网页表单
- 用户需要截取网页截图
- 用户需要从网页提取数据
- 用户需要与网页进行交互

### 常用命令

#### 基础操作

```bash
# 打开浏览器
playwright-cli open
playwright-cli open https://example.com --headed

# 页面导航
playwright-cli goto https://playwright.dev
playwright-cli go-back
playwright-cli go-forward
playwright-cli reload

# 获取页面快照（用于获取元素 ref）
playwright-cli snapshot

# 元素交互（使用 snapshot 返回的 ref）
playwright-cli click e15
playwright-cli type "搜索内容"
playwright-cli fill e5 "user@example.com"
playwright-cli hover e4
playwright-cli check e12
playwright-cli uncheck e12
playwright-cli select e9 "option-value"

# 键盘操作
playwright-cli press Enter
playwright-cli press ArrowDown
playwright-cli keydown Shift
playwright-cli keyup Shift

# 截图
playwright-cli screenshot
playwright-cli screenshot --filename=page.png

# 关闭浏览器
playwright-cli close
```

#### 会话管理

```bash
# 列出所有会话
playwright-cli list

# 关闭所有浏览器
playwright-cli close-all

# 强制终止所有浏览器进程
playwright-cli kill-all
```

#### 存储操作

```bash
# 保存存储状态（cookies、localStorage 等）
playwright-cli state-save auth.json

# 加载存储状态
playwright-cli state-load auth.json

# Cookie 操作
playwright-cli cookie-list
playwright-cli cookie-set session_id abc123
playwright-cli cookie-delete session_id
```

### 使用规则

1. **必须使用 snapshot** - 在进行任何元素交互前，必须先执行 `playwright-cli snapshot` 获取元素 ref
2. **使用 ref 定位元素** - 不要使用选择器，使用 snapshot 返回的元素 ref（如 e15、e21）
3. **Headless 优先** - 默认使用 headless 模式，需要可视化调试时使用 `--headed`
4. **会话隔离** - 不同项目使用不同的会话（`-s=` 参数）
5. **状态管理** - 需要保持登录状态时，使用 `state-save` 和 `state-load`

### 典型工作流

```bash
# 1. 打开浏览器并导航
playwright-cli open https://example.com/login

# 2. 获取页面快照
playwright-cli snapshot

# 3. 填写表单（使用 snapshot 返回的 ref）
playwright-cli fill e5 "username"
playwright-cli fill e8 "password"

# 4. 点击登录
playwright-cli click e10

# 5. 验证结果
playwright-cli screenshot --filename=after-login.png

# 6. 保存登录状态（可选）
playwright-cli state-save auth.json

# 7. 关闭浏览器
playwright-cli close
```

### 重要规则

- 交互前必须先执行 snapshot 获取元素 ref
- 使用 `--headed` 参数可以看到浏览器界面
- 使用 `-s=session-name` 可以创建独立会话
- 截图保存到当前工作目录
```

**用户确认**：
- 添加规则前询问用户是否需要 Playwright 自动化功能
- 如果不需要，跳过此步骤
- 如果需要，写入 CLAUDE.md 前展示完整规则供确认
```

---

## Chunk 3: 验证与文档

### Task 3: 验证集成效果

**Files:**
- None（验证任务）

- [ ] **Step 1: 验证 pre-check.md 修改**

检查 pre-check.md 是否包含：
- [ ] playwright-cli 功能描述
- [ ] 更新的检查流程图
- [ ] playwright-cli 安装说明
- [ ] 更新的强制规则

- [ ] **Step 2: 验证 rule-config.md 修改**

检查 rule-config.md 是否包含：
- [ ] 新增的检查清单项
- [ ] Playwright Skills 规则配置章节
- [ ] 完整的命令参考
- [ ] 用户确认流程

- [ ] **Step 3: 测试 playwright-cli 安装命令**

```bash
# 测试安装命令（仅验证语法，不实际执行）
npm install -g @playwright/cli@latest --dry-run 2>/dev/null || echo "Command syntax OK"

# 验证帮助命令输出格式
playwright-cli --help | head -20
```

---

## 文件变更摘要

| 文件 | 操作 | 变更说明 |
|------|------|---------|
| `commands/pre-check.md` | Modify | 增加 playwright-cli 检查和安装步骤 |
| `commands/init/rule-config.md` | Modify | 增加 Playwright Skills 使用规则配置 |

---

## 执行顺序

1. **Task 1** → 更新 pre-check.md
2. **Task 2** → 更新 rule-config.md
3. **Task 3** → 验证集成效果

---

## 注意事项

1. **Node.js 版本要求**：Playwright CLI 需要 Node.js 18 或更高版本
2. **全局安装**：`@playwright/cli` 需要全局安装，确保用户有 npm 全局安装权限
3. **Skills 安装位置**：`playwright-cli install --skills` 会将 skills 安装到 `~/.claude/skills/playwright-cli/`
4. **可选配置**：Playwright Skills 规则是可选的，根据用户需求决定是否配置

---

## 完成标准

- [ ] pre-check.md 包含完整的 playwright-cli 检查流程
- [ ] rule-config.md 包含完整的 Playwright Skills 使用规则
- [ ] 所有修改符合项目文档规范
- [ ] 文档格式正确，Markdown 语法无误
