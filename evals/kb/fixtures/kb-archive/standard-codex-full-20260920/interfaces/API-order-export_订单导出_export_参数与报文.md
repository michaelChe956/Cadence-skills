# API-order-export 订单导出 - 参数与报文

> **主文件**：`API-order-export_订单导出_export.md`
> **能力 ID**：`API-order-export`
> **分类**：对外
> **HTTP 方法与路径**：`POST /api/order/export`
> **数据来源**：用户对外能力清单、`ExportController`、`ExportService`、`db/init.sql`

## 一、输入参数

未提供。

补充证据：`ExportController#export()` 无方法参数、无 `@RequestBody`/`@RequestParam`/`@RequestHeader`，未发现查询条件、导出范围、分页或时间窗口参数（`order-service/src/main/java/com/demo/order/controller/ExportController.java:10-13`）。用户清单亦未提供参数规范（`user-input/api-scope.md:13`）。

## 二、输出参数

| 节点或字段 | 父节点 | 必填 | 类型 | 长度或格式 | 说明 | 来源 |
|------------|--------|------|------|------------|------|------|
| 响应体 | 根 | 是 | String | 固定字面量 `taskId` | 方法返回字面量，非真实任务 ID；无唯一性、无状态查询方式 | `order-service/src/main/java/com/demo/order/controller/ExportController.java:11-12` |
| `Content-Type` | 响应头 | 条件 | String | 未声明 `produces` | 由 Spring 内容协商决定，未发现显式配置 | `ExportController.java:10-13` |

未发现导出文件链接、文件 ID、任务状态、进度、分页或导出记录等业务响应字段。

## 三、请求报文示例

```http
POST /api/order/export HTTP/1.1
Host: localhost:8083
Content-Length: 0
```

无请求体（未发现请求体解析）；未发现必填请求头或鉴权头。前端调用形态：`request.post('/order/export')`（`web-portal/src/api/index.js:4`）。

## 四、响应报文示例

```text
taskId
```

> 该值为源码字面量（`ExportController.java:12`）；不随请求变化，未发现任务登记或文件生成。

## 五、错误或异常载荷

未提供。

| 错误码或类型 | 触发条件 | 含义 | 来源 |
|--------------|----------|------|------|
| 未提供（未发现统一错误码定义） | - | 未发现 `@ControllerAdvice`、错误码枚举或统一响应包装 | `order-service/src/main/java/com/demo/order/**` |
| 405（框架默认） | 使用非 POST 方法访问该路径 | 方法不允许 | `ExportController.java:10` |
| 500（框架默认，待确认） | 类加载或容器异常 | 服务端错误 | 待确认（无自定义处理证据） |
