# 测试规范示例

> **说明**：这是一个测试规范示例，展示如何定制您自己的测试标准。
> 
> **使用方法**：
> 1. 复制此文件到 `cadence/project-rules/` 目录
> 2. 根据您的项目需求修改内容
> 3. 在 `CLAUDE.md` 中添加规则引用此文件

---

# 测试规范

## 1. 测试原则

### 1.1 核心原则
- **FIRST 原则**：Fast（快速）、Independent（独立）、Repeatable（可重复）、Self-Validating（自我验证）、Timely（及时）
- **测试金字塔**：70% 单元测试 + 20% 集成测试 + 10% E2E 测试
- **测试驱动开发（TDD）**：先写测试，再写实现

### 1.2 测试目标
- **验证功能**：确保代码按预期工作
- **防止回归**：避免修改引入新问题
- **文档作用**：测试即文档
- **设计指导**：测试驱动更好的设计

## 2. 测试覆盖率要求

### 2.1 总体要求
- **最低覆盖率**：80%
- **推荐覆盖率**：90%
- **核心业务逻辑**：100%

### 2.2 分层要求

| 层级 | 最低覆盖率 | 推荐覆盖率 | 说明 |
|------|-----------|-----------|------|
| 工具函数 | 90% | 100% | 纯函数，易于测试 |
| 业务逻辑 | 80% | 90% | 核心功能，必须充分测试 |
| UI 组件 | 60% | 80% | 重点关注交互逻辑 |
| 配置文件 | 0% | 0% | 无需测试 |

### 2.3 覆盖率检查
```bash
# 运行测试并生成覆盖率报告
pnpm test --coverage

# 检查覆盖率是否达标
# 如果不达标，构建失败
```

## 3. 测试类型

### 3.1 单元测试（Unit Tests）

**适用场景**：
- 工具函数
- 纯函数组件
- 业务逻辑函数
- Hooks

**命名规范**：
```
文件名：[filename].test.ts
测试套件：describe('[模块名]', () => {})
测试用例：it('应该 [期望行为] 当 [条件]', () => {})
```

**示例**：
```typescript
// formatDate.test.ts
describe('formatDate', () => {
  it('应该返回格式化的日期 当传入有效日期时', () => {
    const date = new Date('2024-01-15');
    const result = formatDate(date, 'YYYY-MM-DD');
    expect(result).toBe('2024-01-15');
  });

  it('应该抛出错误 当传入无效日期时', () => {
    const invalidDate = 'invalid';
    expect(() => formatDate(invalidDate)).toThrow('Invalid date');
  });

  it('应该使用默认格式 当未指定格式时', () => {
    const date = new Date('2024-01-15');
    const result = formatDate(date);
    expect(result).toMatch(/^\d{4}-\d{2}-\d{2}$/);
  });
});
```

### 3.2 集成测试（Integration Tests）

**适用场景**：
- API 接口
- 数据库操作
- 服务间交互
- 组件集成

**示例**：
```typescript
// userAPI.test.ts
describe('User API', () => {
  beforeAll(async () => {
    // 设置测试数据库
    await setupTestDB();
  });

  afterAll(async () => {
    // 清理测试数据库
    await teardownTestDB();
  });

  it('应该返回用户列表 当请求 /api/users', async () => {
    const response = await request(app).get('/api/users');
    
    expect(response.status).toBe(200);
    expect(response.body.data).toBeInstanceOf(Array);
    expect(response.body.data.length).toBeGreaterThan(0);
  });

  it('应该创建用户 当 POST /api/users', async () => {
    const userData = {
      name: 'Test User',
      email: 'test@example.com'
    };

    const response = await request(app)
      .post('/api/users')
      .send(userData);

    expect(response.status).toBe(201);
    expect(response.body.data.name).toBe(userData.name);
  });
});
```

### 3.3 E2E 测试（End-to-End Tests）

**适用场景**：
- 关键业务流程
- 用户核心路径
- 跨系统交互

**示例**：
```typescript
// login.e2e.test.ts
describe('用户登录流程', () => {
  it('应该成功登录 当输入有效凭证', async () => {
    // 访问登录页
    await page.goto('http://localhost:3000/login');
    
    // 填写表单
    await page.fill('#email', 'user@example.com');
    await page.fill('#password', 'password123');
    
    // 点击登录
    await page.click('#login-button');
    
    // 验证跳转到首页
    await page.waitForURL('http://localhost:3000/dashboard');
    expect(page.url()).toContain('/dashboard');
  });
});
```

### 3.4 快照测试（Snapshot Tests）

**适用场景**：
- UI 组件渲染
- 配置文件
- 数据结构

**示例**：
```typescript
// Button.test.tsx
describe('Button 组件', () => {
  it('应该匹配快照', () => {
    const { container } = render(<Button>Click me</Button>);
    expect(container).toMatchSnapshot();
  });
});
```

## 4. 测试组织结构

### 4.1 目录结构
```
project/
├── src/
│   ├── utils/
│   │   ├── formatDate.ts
│   │   └── formatDate.test.ts     # 测试文件与源文件同级
│   └── services/
│       ├── UserService.ts
│       └── UserService.test.ts
└── tests/                          # 集成测试和 E2E 测试
    ├── integration/
    │   └── api.test.ts
    └── e2e/
        └── login.test.ts
```

### 4.2 测试文件命名
- **单元测试**：`[filename].test.ts` 或 `[filename].spec.ts`
- **集成测试**：`[feature].integration.test.ts`
- **E2E 测试**：`[scenario].e2e.test.ts`

## 5. Mock 和 Stub

### 5.1 何时使用 Mock
- 外部 API 调用
- 数据库操作
- 第三方服务
- 时间相关函数

### 5.2 Mock 示例
```typescript
// Mock 外部 API
jest.mock('@/services/api');

describe('UserService', () => {
  it('应该从 API 获取用户信息', async () => {
    // 设置 Mock 返回值
    const mockUser = { id: 1, name: 'Test User' };
    api.get.mockResolvedValue(mockUser);

    const result = await UserService.getUser(1);

    expect(result).toEqual(mockUser);
    expect(api.get).toHaveBeenCalledWith('/users/1');
  });
});
```

### 5.3 Mock 最佳实践
- ✅ 只 Mock 你不拥有的代码
- ✅ Mock 要尽量接近真实行为
- ❌ 不要过度 Mock
- ❌ 不要 Mock 被测试的代码

## 6. 测试数据

### 6.1 测试数据管理
```typescript
// testFixtures.ts
export const mockUsers = [
  { id: 1, name: 'User 1', email: 'user1@example.com' },
  { id: 2, name: 'User 2', email: 'user2@example.com' },
];

export const createMockUser = (overrides = {}) => ({
  id: 1,
  name: 'Default User',
  email: 'default@example.com',
  ...overrides,
});
```

### 6.2 数据清理
```typescript
describe('UserService', () => {
  beforeEach(async () => {
    // 每个测试前重置数据
    await resetDatabase();
  });

  afterEach(async () => {
    // 每个测试后清理数据
    await cleanupDatabase();
  });
});
```

## 7. 测试异步代码

### 7.1 Promise
```typescript
it('应该返回用户数据', async () => {
  const user = await UserService.getUser(1);
  expect(user).toBeDefined();
});
```

### 7.2 回调函数
```typescript
it('应该调用回调函数', (done) => {
  asyncFunction((result) => {
    expect(result).toBe('success');
    done();
  });
});
```

### 7.3 定时器
```typescript
it('应该在延迟后执行', () => {
  jest.useFakeTimers();
  
  const callback = jest.fn();
  setTimeout(callback, 1000);
  
  jest.advanceTimersByTime(1000);
  
  expect(callback).toHaveBeenCalled();
  
  jest.useRealTimers();
});
```

## 8. 测试 React 组件

### 8.1 渲染测试
```typescript
import { render, screen } from '@testing-library/react';

it('应该渲染按钮文本', () => {
  render(<Button>Click me</Button>);
  expect(screen.getByText('Click me')).toBeInTheDocument();
});
```

### 8.2 交互测试
```typescript
import { render, screen, fireEvent } from '@testing-library/react';

it('应该调用 onClick 当点击按钮时', () => {
  const handleClick = jest.fn();
  render(<Button onClick={handleClick}>Click me</Button>);
  
  fireEvent.click(screen.getByText('Click me'));
  
  expect(handleClick).toHaveBeenCalledTimes(1);
});
```

### 8.3 状态测试
```typescript
import { render, screen, fireEvent } from '@testing-library/react';

it('应该切换展开状态 当点击时', () => {
  render(<Accordion />);
  
  // 初始状态：内容隐藏
  expect(screen.queryByText('Content')).not.toBeInTheDocument();
  
  // 点击展开
  fireEvent.click(screen.getByText('Toggle'));
  
  // 展开状态：内容显示
  expect(screen.getByText('Content')).toBeInTheDocument();
});
```

## 9. 测试 Hooks

### 9.1 使用 renderHook
```typescript
import { renderHook, act } from '@testing-library/react-hooks';

it('应该更新计数 当调用 increment 时', () => {
  const { result } = renderHook(() => useCounter());

  expect(result.current.count).toBe(0);

  act(() => {
    result.current.increment();
  });

  expect(result.current.count).toBe(1);
});
```

## 10. 测试最佳实践

### 10.1 AAA 模式
```typescript
it('应该正确计算总价', () => {
  // Arrange：准备测试数据
  const items = [
    { price: 100, quantity: 2 },
    { price: 50, quantity: 1 },
  ];

  // Act：执行被测试的代码
  const total = calculateTotal(items);

  // Assert：验证结果
  expect(total).toBe(250);
});
```

### 10.2 一个测试一个断言
```typescript
// ✅ 正确：一个测试验证一个行为
it('应该返回正确的用户名', () => {
  const user = getUser(1);
  expect(user.name).toBe('John');
});

it('应该返回正确的用户邮箱', () => {
  const user = getUser(1);
  expect(user.email).toBe('john@example.com');
});

// ❌ 错误：一个测试验证多个行为
it('应该返回正确的用户信息', () => {
  const user = getUser(1);
  expect(user.name).toBe('John');
  expect(user.email).toBe('john@example.com');
  expect(user.age).toBe(25);
});
```

### 10.3 测试边界条件
```typescript
describe('divide', () => {
  it('应该返回正确结果 当除数不为零', () => {
    expect(divide(10, 2)).toBe(5);
  });

  it('应该抛出错误 当除数为零', () => {
    expect(() => divide(10, 0)).toThrow('Division by zero');
  });

  it('应该返回零 当被除数为零', () => {
    expect(divide(0, 10)).toBe(0);
  });
});
```

### 10.4 使用描述性的测试名称
```typescript
// ✅ 正确：描述性强
it('应该返回 null 当用户不存在时', () => {});

// ❌ 错误：描述性弱
it('test1', () => {});
it('works', () => {});
```

## 11. 测试反模式

### 11.1 不要测试实现细节
```typescript
// ❌ 错误：测试实现细节
it('应该设置 state.count 为 1', () => {
  wrapper.setState({ count: 1 });
  expect(wrapper.state('count')).toBe(1);
});

// ✅ 正确：测试公开行为
it('应该显示正确的计数', () => {
  render(<Counter />);
  fireEvent.click(screen.getByText('Increment'));
  expect(screen.getByText('Count: 1')).toBeInTheDocument();
});
```

### 11.2 不要测试私有方法
```typescript
// ❌ 错误：测试私有方法
it('应该调用私有方法', () => {
  const instance = new Service();
  instance['_privateMethod']();
  expect(instance['_called']).toBe(true);
});

// ✅ 正确：通过公开方法测试
it('应该正确执行操作', () => {
  const instance = new Service();
  instance.publicMethod();
  expect(instance.getResult()).toBe('expected');
});
```

### 11.3 不要在测试中包含逻辑
```typescript
// ❌ 错误：测试中包含逻辑
it('复杂测试', () => {
  if (condition) {
    expect(a).toBe(b);
  } else {
    expect(a).toBe(c);
  }
});

// ✅ 正确：简单直接的测试
it('应该返回正确结果 当条件 A', () => {
  const result = service.calculate(10, 20);
  expect(result).toBe(30);
});
```

## 12. CI/CD 集成

### 12.1 测试命令
```json
// package.json
{
  "scripts": {
    "test": "jest",
    "test:watch": "jest --watch",
    "test:coverage": "jest --coverage",
    "test:ci": "jest --ci --coverage --watchAll=false"
  }
}
```

### 12.2 CI 配置
```yaml
# .github/workflows/test.yml
name: Test
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-node@v2
      - run: pnpm install
      - run: pnpm test:ci
      - uses: codecov/codecov-action@v2
```

## 13. 测试清单

### 13.1 提交前检查
- [ ] 所有测试通过
- [ ] 覆盖率达标（≥80%）
- [ ] 无跳过的测试
- [ ] 无 console 输出
- [ ] 测试命名清晰
- [ ] 测试文档完整

### 13.2 Code Review 检查
- [ ] 测试覆盖核心逻辑
- [ ] 测试边界条件
- [ ] 测试错误处理
- [ ] Mock 使用合理
- [ ] 断言充分
- [ ] 测试执行快速

## 14. 测试工具推荐

### 14.1 测试框架
- **Jest**：JavaScript 测试框架
- **Vitest**：Vite 原生测试框架
- **Mocha**：灵活的测试框架

### 14.2 测试工具库
- **React Testing Library**：React 组件测试
- **Cypress**：E2E 测试
- **Playwright**：跨浏览器测试

### 14.3 辅助工具
- **MSW**：Mock Service Worker
- **Nock**：HTTP Mock
- **Faker**：生成测试数据

---

> **提示**：这是一个测试规范示例，您可以根据项目技术栈和团队习惯调整内容。
