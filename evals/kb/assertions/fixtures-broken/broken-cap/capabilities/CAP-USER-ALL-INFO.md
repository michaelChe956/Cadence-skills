# 全部用户信息

## 1. 元数据

| 项目 | 内容 |
|------|------|
| 组合稳定 ID | CAP-USER-ALL-INFO |
| 状态 | verified |
| 来源 | 用户诉求（api-scope） |

## 3. 输入能力清单

| step | api_id | required |
|------|--------|----------|
| basic | API-user-basic | true |
| account | API-account-query | true |

## 7. 连接键证据（JOIN_KEY 纪律）

| 输入 API | 连接键字段 | 映射链 | 结论 |
|----------|-----------|--------|------|
| API-account-query | userId | SELECT * 隐式映射（断链） | 待确认 |

## 8. 实现关联

implementation_api_ids：无
