# 增量更新案例

## 场景一：完整变更包通过

用户必须显式指定：

```text
cadence/knowledge-base/user-input/updates/CHANGE-order-v2/
```

该目录包含五份强制文档。代码文档登记 Merge Request `!128`、源分支 `feature/order-v2`、目标分支 `main`、本地可解析的 `abc1234..def5678`、修改工程及文件与符号、独立代码变更说明。数据库文档登记 `t_order.remark` 删除的迁移、上线状态、兼容性和回滚。Manifest 的配置状态为 `指定`，配置文档登记同一测试环境的基线与目标快照、两个外部目录、两个指纹，以及匹配的范围摘要、纳入文件数量、服务摘要和文件规则摘要。验证文档记录测试、数据兼容、配置生效和回滚验证。

校验通过后按以下链路更新：

```text
CHANGE-order-v2 → !128 / abc1234..def5678 → OrderController#create、OrderEntity#remark → API-order-create、TABLE-order → 数据模型/API/页面 → 受影响文档
```

成功后把目标配置快照写为新基线，并把变更包幂等标识写入 `update.last_change_package` 和 `update.processed_packages`。保留原 `generated_at`；若本次新增、解决或调整待确认项，则从 `open-questions.md` 未解决条目重算四级计数，并与受影响文档、历史和 Manifest 原子写入。

## 场景二：缺少数据库文档而停止

用户提供了 Git Diff、MR 元数据、配置快照和验证记录，但目标目录缺少 `database-change.md`。

流程立即停止，不读取 Git Diff 来推断数据库状态，也不生成半成品。返回：

- 目标补齐目录：`cadence/knowledge-base/user-input/updates/CHANGE-order-v2/`
- 插件模板目录：`cadence-init/skills/knowledge-base-update/user-input/change-package/`
- 缺失文档：`database-change.md`
- 影响：无法确认数据模型、兼容性、上线状态和回滚范围

## 场景三：声明无配置变化但快照有差异

`configuration-change.md` 声明 `无变更`，且填写了基线和目标快照；快照比较却发现目标指纹不同，并定位到纳入范围内的 `order-service/application.yaml`。

流程停止，保留“无变更”声明与快照差异两份来源。快照比较只能验证输入，不能擅自把状态改成 `有变更`。返回冲突字段、差异影响及需要修正的配置文档。

## 场景四：代码字段变化但数据库声明无变化

本地提交范围显示 `OrderEntity#remark` 和 Mapper 映射被删除，但 `database-change.md` 声明 `无变更`，且依据只有“本次没有 DDL”。

流程停止。代码扫描与 Mapper 只能验证冲突，不能替代数据库文档。用户必须补充数据库迁移资料，或提供可定位证据证明该字段不属于持久化结构并更新无变更判断依据。

## 场景五：重复包不重复更新

再次显式指定 `CHANGE-order-v2` 时，计算出的变更标识和幂等标识已存在于 `update.processed_packages`。

流程报告该包已处理，不再次更新实体、不追加第二条变更历史、不生成第二组稳定 ID，也不重复写入配置基线。如果相同目录内容已改变导致幂等标识不同，则按已处理包被修改停止并登记来源冲突。

## 场景六：配置领域不适用的纯代码更新

Manifest 的 `scope.configurations.status` 为 `不适用`，`not_applicable_reason` 为“该项目不使用运行时配置且没有授权快照”。变更包仍包含 `configuration-change.md`，其中配置状态为 `无变更`，原因与 Manifest 一致；环境、双快照、目录、指纹、范围摘要、文件数量和服务规则摘要均填写 `不适用（Manifest 配置领域不适用）`。

流程跳过配置目录、指纹和快照差异比较，继续验证代码与数据库资料。成功时不创建配置基线，`last_change_package` 的目标配置指纹记录为 `不适用（Manifest 配置领域不适用）`。如果配置文档声明 `有变更` 或原因与 Manifest 不一致，则停止。

## 场景七：敏感内容在幂等计算前停止

五份主文档或附件中出现真实配置值、明文凭证、完整连接串、未脱敏内部地址、原始配置文件或敏感值哈希。

流程在计算幂等标识前停止，报告文件和字段位置；不对该包生成内容哈希，不读取 Git Diff、快照或其他未授权资料。用户必须把配置差异改为只记录配置键、变更类型、用途和 `<redacted>` 后重新提交完整包。

## 附件安全

附件可以包含脱敏 DDL 差异、迁移说明、不含真实配置值的配置差异摘要和 MR 导出说明，但不得包含明文凭证、完整生产配置、完整连接串、未脱敏内部地址或敏感值哈希。附件不能替代五份强制文档；五份主文档和全部附件都必须在计算幂等标识前通过敏感门禁。
