# 追溯矩阵

| 来源稳定 ID | 关系类型 | 目标稳定 ID | 关系证据（文件:行号） | 证据状态 |
|------------|----------|------------|----------------------|----------|----------|
| API-user-basic | READS | TABLE-user | user-service/src/main/resources/mapper/UserMapper.xml:4 | 已确认 | interfaces/API-user-basic.md |
| SERVICE-order-service | PRODUCES | EVENT-order-paid | order-service/src/main/java/com/demo/order/mq/OrderEventProducer.java:24 | 已确认 | interfaces/EVENT-order-paid.md |
| SERVICE-order-service | CONSUMES | EVENT-order-paid | order-service/src/main/java/com/demo/order/mq/OrderEventListener.java:19 | 已确认 | interfaces/EVENT-order-paid.md |
| JOB-account-reconcile | INVOLVES | TABLE-user-account | account-service/src/main/java/com/demo/account/job/ReconcileJob.java:16 | 已确认 | interfaces/JOB-account-reconcile.md |
| CAP-USER-ALL-INFO | COMPOSES | API-user-basic | capabilities/CAP-USER-ALL-INFO.md#3 | 已确认 | capabilities/CAP-USER-ALL-INFO.md |
| CAP-USER-ALL-INFO | COMPOSES | API-account-query | capabilities/CAP-USER-ALL-INFO.md#3 | 已确认 | capabilities/CAP-USER-ALL-INFO.md |
| API-user-basic | JOIN_KEY | API-account-query | account-service/src/main/resources/mapper/AccountMapper.xml:8 | 待确认 | capabilities/CAP-USER-ALL-INFO.md#7 |
