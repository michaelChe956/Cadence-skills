# 配置范围

- 状态：全量

## 基线快照

| 项目 | 值 |
|------|-----|
| snapshot_id | baseline-config-v1 |
| 环境 | 开发（fixture 本地快照） |
| 发布批次 | fixture-batch-001 |
| 外部目录（只读） | {{SNAPSHOT_DIR}} |
| 获取时间 | 由 runner 生成 |
| 来源类型 | 工作区配置导出快照（锁定） |
| 最终快照指纹 | {{FINGERPRINT}} |

## 范围摘要

- scope_summary：三服务 application.yml 全量纳入（3 文件）
- 纳入文件数：3
- 服务摘要：user-service、account-service、order-service
- 文件规则摘要：仅 src/main/resources/application.yml
