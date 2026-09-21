# {{组合能力名称}}

## 1. 元数据

| 项目 | 内容 |
|------|------|
| 组合稳定 ID | CAP-{{业务名}} |
| 状态 | proposed / verified / retired |
| 来源 | 用户诉求（api-scope）/ 已有聚合端点 |
| 声明依据 | {{api-scope 诉求行 / 聚合端点 API ID}} |

> `proposed`=设计已确认未实现；`verified`=有实现证据（implementation_api_ids 非空）；`retired`=已退役。`verified` 不等于对外已暴露——对外属性唯一权威是用户 api-scope 清单。会话推导的组合候选不得生成本实体。

## 2. 目的与非目标

{{组合解决什么业务问题；明确不覆盖什么（"全部用户信息"必须收敛为明确字段清单，不默认涵盖敏感字段）}}

## 3. 输入能力清单

| step | api_id | required | request_mapping | contract_ref |
|------|--------|----------|-----------------|--------------|
| | | | | ../interfaces/…_参数与报文.md#… |

## 4. 编排与字段映射

- pattern：parallel_join / sequential（白名单，二选一）
- join_key：{{字段}}（两侧必须各自逐跳映射到同一 TABLE 字段，见第 7 节证据）
- output_mapping：命名空间合并（如 profile: / accounts:），禁覆盖同名字段
- failure_policy：fail_whole / partial

## 5. 输出契约

| 字段 | 来源 | 允许公开 |
|------|------|----------|

## 6. 约束与鉴权

| 约束 | 结论 | 证据 |
|------|------|------|
| identity_mapping | | |
| tenant_isolation | | |
| external_permission | | |

## 7. 连接键证据（JOIN_KEY 纪律）

| 输入 API | 连接键字段 | 映射链（API 模型→SERVICE/MODULE→Mapper/SQL→TABLE 字段） | 证据锚点 |
|----------|-----------|--------------------------------------------------------|----------|

> 字段同名不构成关联依据；任一跳缺失或待确认 → JOIN_KEY 标待确认，本组合不得 `verified`。

## 8. 实现关联

implementation_api_ids：{{实际聚合端点 API-*；为空=未实现，状态恒 proposed}}

## 9. 证据与待确认
