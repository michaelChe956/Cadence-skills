# API-account-query 账户信息查询接口 - 参数与报文

> **主文件**：`API-account-query_账户信息查询_queryAccount.md`
> **能力 ID**：`API-account-query`
> **分类**：对内
> **HTTP 方法与路径**：`GET /api/account/{userId}`
> **数据来源**：`AccountController`、`AccountEntity`、`AccountMapper.xml`、`db/init.sql`

## 一、输入参数

| 节点或字段 | 父节点 | 必填 | 类型 | 长度或格式 | 说明 | 来源 |
|------------|--------|------|------|------------|------|------|
| `userId` | 路径 | 是 | Long | BIGINT，十进制整数 | 用户唯一标识；与 `t_user.user_id` 同源（注释声明，无外键，Q-M5） | `AccountController.java:20`、`AccountMapper.xml:6`、`db/init.sql:17` |
| （请求头/请求体） | - | - | - | - | 未发现鉴权头、租户头或请求体解析；无请求体（GET） | `AccountController.java:19-22`；未发现安全依赖 |

未发现其他查询条件（无账户号、状态、分页参数）。

## 二、输出参数

| 节点或字段 | 父节点 | 必填 | 类型 | 长度或格式 | 说明 | 来源 |
|------------|--------|------|------|------------|------|------|
| `userId` | 响应根 | 条件 | Long | BIGINT，NOT NULL | 用户唯一标识；映射依赖隐式驼峰（Q-M3） | `AccountMapper.xml:5-6`、`AccountEntity.java:6` |
| `accountNo` | 响应根 | 条件 | String | VARCHAR(32)，NOT NULL | 账户号；DDL 有唯一键 `uk_account_no` | `db/init.sql:18,21`、`AccountEntity.java:8` |
| `balance` | 响应根 | 条件 | BigDecimal | DECIMAL(18,2)，NOT NULL，默认 0 | 账户余额；表级硬约束“不可为负” | `db/init.sql:19`、`AccountEntity.java:10` |
| `status` | 响应根 | 条件 | String | VARCHAR(16)，NOT NULL，默认 `NORMAL` | 账户状态：`NORMAL`/`FROZEN`/`CLOSED` | `db/init.sql:20`、`AccountEntity.java:12` |
| `id` | - | - | - | BIGINT | 表主键列由 `SELECT *` 返回，但 Entity 无对应属性；未发现映射配置，是否输出取决于框架未知列处理（Q-M3） | `db/init.sql:16`、`AccountMapper.xml:6`、`AccountEntity.java:4-13` |

> “条件”表示字段是否出现取决于隐式映射结果（Q-M3），不得据此断言接口已稳定输出这些字段。

## 三、请求报文示例

无请求体（GET），未发现必填请求头。

```http
GET /api/account/1 HTTP/1.1
Host: localhost:8082
Accept: application/json
```

前端调用形态：`request.get('/account/${userId}')`（`web-portal/src/api/index.js:3`）。

## 四、响应报文示例

```json
{
  "userId": 1,
  "accountNo": "ACC00000001",
  "balance": 100.00,
  "status": "NORMAL"
}
```

> 样例为结构展示；`accountNo`/`balance` 为示例值。查无结果时实现为返回 `null`（HTTP 200 空体）。

## 五、错误或异常载荷

| 错误码或类型 | 触发条件 | 含义 | 来源 |
|--------------|----------|------|------|
| 未提供（未发现统一错误码定义） | - | 未发现 `@ControllerAdvice`、错误码枚举或统一响应包装 | `account-service/src/main/java/com/demo/account/**` |
| 500 或框架默认异常（待确认） | 同一 `user_id` 命中多行导致 `TooManyResultsException` | 服务端异常；DDL 未对 `user_id` 建唯一约束 | `AccountMapper.xml:5-7`、`db/init.sql:14-22`；待确认 |
| 400（框架默认，待确认） | `userId` 非数字 | 参数格式错误 | 待确认（无自定义处理证据） |
