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
