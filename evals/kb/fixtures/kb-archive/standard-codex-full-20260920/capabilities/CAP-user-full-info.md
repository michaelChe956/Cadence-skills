# 全部用户信息

## 1. 元数据

| 项目 | 内容 |
|------|------|
| 组合稳定 ID | CAP-user-full-info |
| 状态 | proposed |
| 来源 | 用户诉求（`user-input/api-scope.md`） |
| 声明依据 | `user-input/api-scope.md:19-21`“全部用户信息”诉求行（期望输出：用户基本信息 + 账户信息；连接键 `userId`；依据：业务需求：对外统一提供用户全景） |

> `proposed`=设计已确认未实现；`verified`=有实现证据（`implementation_api_ids` 非空）；`retired`=已退役。`verified` 不等于对外已暴露——对外属性唯一权威是用户 api-scope 清单。

## 2. 目的与非目标

- 目的：为调用方一次获取“用户基本信息 + 账户信息”，避免分别调用两个能力。
- 非目标：不默认涵盖敏感字段以外的任何信息（手机号、邮箱、余额等是否允许公开须由用户确认，Q-M13）；不覆盖用户创建、修改、账户余额调整等写操作；不代表已对外暴露。

## 3. 输入能力清单

| step | api_id | required | request_mapping | contract_ref |
|------|--------|----------|-----------------|--------------|
| 1 | `API-user-basic` | 是 | `userId` → path 参数 `{userId}` | [`API-user-basic 参数与报文`](../interfaces/API-user-basic_查询用户基本信息_queryBasic_参数与报文.md) |
| 2 | `API-account-query` | 是 | 同一 `userId` → path 参数 `{userId}` | [`API-account-query 参数与报文`](../interfaces/API-account-query_账户信息查询_queryAccount_参数与报文.md) |

来源能力存在性与契约锚点已由 api 阶段核实（`interfaces/README.md#能力组合诉求核实`）；对内能力 `API-account-query` 在用户诉求中以“预期登记为对内能力”表述。

## 4. 编排与字段映射

- pattern：`parallel_join`
- join_key：`userId`（待确认，见第 7 节）
- output_mapping：命名空间合并（`profile:` 承载用户基本信息字段，`accounts:` 承载账户字段），禁覆盖同名字段
- failure_policy：`partial`（单侧失败时返回已成功部分并标注缺失来源；该策略为用户诉求未定义项，登记 Q-M13）

## 5. 输出契约

| 字段 | 来源 | 允许公开 |
|------|------|----------|
| `profile.userId` | `API-user-basic`（`t_user.user_id`） | 待确认 |
| `profile.userName` | `API-user-basic`（`t_user.user_name`） | 待确认 |
| `profile.mobile` | `API-user-basic`（`t_user.mobile`） | 待确认（敏感字段，Q-M8） |
| `profile.email` | `API-user-basic`（`t_user.email`） | 待确认（敏感字段，Q-M8） |
| `accounts.accountNo` | `API-account-query`（`t_user_account.account_no`） | 待确认 |
| `accounts.balance` | `API-account-query`（`t_user_account.balance`） | 待确认（敏感字段） |
| `accounts.status` | `API-account-query`（`t_user_account.status`） | 待确认 |

字段清单来自两个来源接口的参数与报文文档，仅表示可组合范围；任何字段的对外公开性都必须由用户确认。

## 6. 约束与鉴权

| 约束 | 结论 | 证据 |
|------|------|------|
| identity_mapping | 未定义：两来源接口均以 `userId` 为唯一入参，本组合未定义调用方身份到 `userId` 的映射与越权校验 | `interfaces/API-user-basic_查询用户基本信息_queryBasic.md`、`interfaces/API-account-query_账户信息查询_queryAccount.md` |
| tenant_isolation | 未发现多租户或数据范围隔离机制 | 三后端未发现安全依赖与数据范围过滤（Q-M8） |
| external_permission | 未确认：两来源均未发现鉴权实现，`API-account-query` 未登记为对外能力 | `user-service/pom.xml:13-17`、`account-service/pom.xml:13-17`（无安全依赖）；`user-input/api-scope.md:12-13`、Q-M7、Q-M8 |

## 7. 连接键证据（JOIN_KEY 纪律）

| 输入 API | 连接键字段 | 映射链（API 模型→SERVICE/MODULE→Mapper/SQL→TABLE 字段） | 证据锚点 |
|----------|-----------|--------------------------------------------------------|----------|
| `API-user-basic` | `userId` | `UserEntity.userId` → `MODULE-user-basic`/`UserBasicService#queryBasic` → `UserMapper.xml#selectById` → `t_user.user_id` | `user-service/src/main/resources/mapper/UserMapper.xml:4-7`（`user_id AS userId`、`WHERE user_id = #{userId}`）；`UserBasicController.java:26-30`；已确认 |
| `API-account-query` | `userId` | `AccountEntity.userId` → `MODULE-account-core`/`AccountService#queryAccount` → `AccountMapper.xml#selectByUserId` → `t_user_account.user_id` | `account-service/src/main/resources/mapper/AccountMapper.xml:5-7`（`WHERE user_id = #{userId}`，请求条件已确认；响应字段依赖隐式驼峰映射，**待确认**，Q-M3） |

- 连接键类型与值域一致：两侧均为 `BIGINT`/`Long`，DDL 注释声明同源（`db/init.sql:5,17`）。
- 跨库关联无外键约束，仅为注释级同源声明，不能作为约束事实（`db/init.sql` 无 `FOREIGN KEY`，Q-M5）。
- 结论：任一跳存在待确认 → 本组合的 `JOIN_KEY` 边与组合整体按`待确认`处理，状态不得为 `verified`（Q-M9）。

## 8. 实现关联

`implementation_api_ids`：空。全量接口扫描未发现聚合上述两个能力的端点，故本组合未实现，状态恒为 `proposed`。

## 9. 证据与待确认

- 用户诉求：`user-input/api-scope.md:19-21`。
- 来源能力与契约锚点核实：`interfaces/README.md#能力组合诉求核实`、`interfaces/README.md` 对外与对内能力清单。
- 待确认：Q-M3（账户响应隐式映射）、Q-M5（跨库无外键）、Q-M7（`API-account-query` 分类冲突）、Q-M8（鉴权缺失）、Q-M9（JOIN_KEY 未闭合）、Q-M13（组合字段范围、敏感字段公开性与失败策略未定义）。
