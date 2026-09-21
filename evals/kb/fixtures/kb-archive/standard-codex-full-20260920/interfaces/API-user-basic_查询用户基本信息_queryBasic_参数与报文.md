# API-user-basic 查询用户基本信息 - 参数与报文

> **主文件**：`API-user-basic_查询用户基本信息_queryBasic.md`
> **能力 ID**：`API-user-basic`
> **分类**：对外
> **HTTP 方法与路径**：`GET /api/user/basic/{userId}`
> **数据来源**：用户对外能力清单、`UserBasicController`、`UserEntity`、`UserMapper.xml`、`db/init.sql`

## 一、输入参数

| 节点或字段 | 父节点 | 必填 | 类型 | 长度或格式 | 说明 | 来源 |
|------------|--------|------|------|------------|------|------|
| `userId` | 路径 | 是 | Long | BIGINT，十进制整数 | 用户唯一标识；服务端未做格式/范围校验 | `UserBasicController.java:20`、`UserMapper.xml:6`、`db/init.sql:5` |
| （请求头/请求体） | - | - | - | - | 未发现鉴权头、租户头或请求体解析；无请求体（GET） | `UserBasicController.java:19-21`；未发现安全依赖 |

未发现其他输入参数、查询条件或分页参数。

## 二、输出参数

| 节点或字段 | 父节点 | 必填 | 类型 | 长度或格式 | 说明 | 来源 |
|------------|--------|------|------|------------|------|------|
| `userId` | 响应根 | 是 | Long | BIGINT | 用户唯一标识，来自 `user_id AS userId` | `UserMapper.xml:5`、`UserEntity.java:6` |
| `userName` | 响应根 | 条件 | String | VARCHAR(64) | 用户姓名，来自 `user_name AS userName` | `UserMapper.xml:5`、`db/init.sql:6` |
| `mobile` | 响应根 | 条件 | String | VARCHAR(20) | 手机号；DDL 可空，SQL 未做脱敏，响应可能包含明文手机号（提示，不记录真实值） | `UserMapper.xml:5`、`db/init.sql:7` |
| `email` | 响应根 | 条件 | String | VARCHAR(128) | 邮箱；DDL 可空 | `UserMapper.xml:5`、`db/init.sql:8` |
| `createdAt` | 响应根 | - | - | - | 未返回：`created_at` 存在于 DDL，但 SELECT 列表与 Entity 均不含该字段 | `db/init.sql:9`、`UserMapper.xml:5`、`UserEntity.java:4-9` |

条件字段说明：`userName`、`mobile`、`email` 在 DDL 中未声明 `NOT NULL`（`user_name` 声明 `NOT NULL`），返回值取决于库内数据；未发现响应脱敏或字段过滤逻辑。

## 三、请求报文示例

无请求体（GET），未发现必填请求头。

```http
GET /api/user/basic/1 HTTP/1.1
Host: localhost:8081
Accept: application/json
```

前端调用形态：`request.get('/user/basic/${userId}')`，经 `baseURL: /api` 合并为 `/api/user/basic/{userId}`（`web-portal/src/api/index.js:2`、`web-portal/src/api/request.js:3`）。

## 四、响应报文示例

```json
{
  "userId": 1,
  "userName": "示例用户",
  "mobile": "138****0000",
  "email": "user@example.invalid"
}
```

> 字段样例仅为展示结构；`mobile`/`email` 为脱敏与示例值，不代表真实数据。查无结果时实现为返回 `null`（HTTP 200 空体），未发现 404 语义。

## 五、错误或异常载荷

| 错误码或类型 | 触发条件 | 含义 | 来源 |
|--------------|----------|------|------|
| 未提供（未发现统一错误码定义） | - | 未发现 `@ControllerAdvice`、错误码枚举或统一响应包装 | `user-service/src/main/java/com/demo/user/**` |
| 400（框架默认，待确认） | `userId` 非数字，路径变量类型转换失败 | 参数格式错误；响应体为 Spring 默认错误结构 | 待确认（无自定义处理证据） |
| 500（框架默认，待确认） | `UserMapper.xml` 未命中 `resultType` 或数据源不可用 | 服务端异常，响应体按 Spring 默认错误输出 | 待确认（无自定义处理证据） |
