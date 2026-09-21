# 配置变更

- 变更状态：无变更
- 判断依据：本次变更未触及任何 application.yml（git diff 仅 account-service Java 文件与 web-portal 前端文件，配置文件零改动）；基线与目标为同一快照，指纹一致

## 基线快照

| 项目 | 值 |
|------|-----|
| snapshot_id | baseline-config-v1 |
| 环境 | 开发（fixture 本地快照） |
| 发布批次 | fixture-batch-001 |
| 外部目录（只读） | {{SNAP_DIR}} |
| 获取时间 | runner prepare 生成 |
| 来源类型 | 工作区配置导出快照（锁定） |
| 最终快照指纹 | {{FINGERPRINT}} |

## 目标快照（无变更：与基线为同一快照）

| 项目 | 值 |
|------|-----|
| snapshot_id | baseline-config-v1（=基线） |
| 环境 | 开发（=基线） |
| 发布批次 | fixture-batch-001（=基线） |
| 外部目录（只读） | {{SNAP_DIR}}（=基线） |
| 来源类型 | 工作区配置导出快照（锁定） |
| 最终快照指纹 | {{FINGERPRINT}}（=基线，无差异） |

## 范围摘要（基线=目标）

- scope_summary：三服务 application.yml 全量纳入（3 文件）
- 纳入文件数：3
- 服务摘要：user-service、account-service、order-service
- 文件规则摘要：仅 src/main/resources/application.yml
- 涉及服务/配置组：无变更，不涉及
- 已知差异：无（基线与目标为同一快照，指纹一致）
