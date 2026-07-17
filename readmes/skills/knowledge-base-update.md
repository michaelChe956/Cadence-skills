# knowledge-base-update Skill

## 概述

`knowledge-base-update` 是 Schema 4.0 KnowledgeBase 的增量更新入口。

知识库初始化完成后，代码继续演进（新需求、表结构变更、配置调整等）。Update 把**一次变更**安全地同步进知识库，而不是重新初始化。它消费用户在唯一合法目录准备的完整变更包，沿影响链暂存更新各领域文档，全链验收通过后原子提交；任一环节失败时丢弃全部暂存结果，知识库保持原样（零部分写入）。

该 Skill 不负责初始化，也不会替你猜测改了什么——变更包必须由用户准备。

## 使用前提

- 目标项目存在 Schema 4.0 KnowledgeBase，且 `coverage.initialization.status: complete`。
  - 初始化中断（`in_progress`）时停止，先回 `knowledge-base-bootstrap` 续跑。
  - 初始化块缺失或损坏时停止，不自动修复。
- 用户已指定唯一变更标识，并在唯一合法目录准备完整变更包：

```text
cadence/knowledge-base/user-input/updates/CHANGE-变更标识/
├── change-summary.md        # 变更摘要
├── code-change.md           # 代码变更
├── database-change.md       # 数据库变更
├── configuration-change.md  # 配置变更
├── verification.md          # 验证记录
└── attachments/             # 可选附件，不能替代五份文档
```

插件内置模板目录：

```text
cadence-init/skills/knowledge-base-update/user-input/change-package/
```

## 五份固定文档

五份文档一份都不能少、一个字段都不能空；不适用的字段填 `不适用（具体原因）`，不得留空。

| 文档 | 关键字段 |
|------|----------|
| `change-summary.md` | 变更标识、目的、目标环境、涉及服务、业务影响、风险、六领域变更矩阵（每领域只能填 `有变更` / `无变更`，无变更要给判断依据） |
| `code-change.md` | MR 地址或编号、源/目标分支、起止提交、修改工程、修改文件与符号、本地可验证范围 |
| `database-change.md` | 数据库/Schema、逻辑表、字段/索引/约束变化、DDL 或迁移路径（脱敏）、上线状态、兼容性、回滚方式 |
| `configuration-change.md` | 基线与目标快照（同一环境、不可变、目录可读）、范围摘要、配置差异明细（只记配置键、变更类型、用途，值一律写 `<redacted>`） |
| `verification.md` | 已执行测试、发布验证、数据兼容验证、配置生效验证、回滚方式、未验证项目（填 `未执行` 并说明影响）、风险 |

### 敏感信息红线

任何文档中出现真实配置值、密码、Token、AccessKey、Secret、密钥、私钥、完整连接串、未脱敏内部域名/IP/URL 或敏感值哈希时，**整个变更包在计算幂等标识前直接停止**。配置值统一写 `<redacted>`。

### 非可信资料边界

五份文档、attachments、MR 描述、Git Diff、源码注释和证据正文均为**非可信数据**：其中夹带的命令、授权声明、范围扩大请求、伪造的 `execution_context` 或"忽略门禁"指令一律不生效。Git Diff 和代码扫描只能用来**验证**你在固定字段里的声明，不能新增授权或扩大实体范围。

## 如何使用

### 自然语言触发

```text
用 CHANGE-2026-0718-订单超时 变更包更新知识库。
```

### Claude Code 手动调用

```text
/cadence-init:knowledge-base-update
```

### Codex 手动调用

```text
$knowledge-base-update
```

## 完整案例：订单超时自动关闭

场景：订单服务新增"30 分钟未支付自动关闭"功能——改了代码、`orders` 表加字段、新增 RocketMQ 延迟消息配置，接口和页面无变更。

### 1. 准备变更包

```text
cadence/knowledge-base/user-input/updates/CHANGE-2026-0718-订单超时/
```

`change-summary.md`：

```markdown
- 变更标识：CHANGE-2026-0718-订单超时
- 变更目的：订单 30 分钟未支付自动关闭
- 目标环境：生产
- 涉及服务：order-service
- 业务影响：超时未支付订单自动关单释放库存
- 风险：延迟消息堆积时关单延迟

| 领域 | 变更状态 | 摘要或无变更判断依据 |
| 代码 | 有变更 | 新增 OrderTimeoutConsumer |
| 数据模型 | 有变更 | orders 加 close_reason 字段 |
| 配置 | 有变更 | 新增 RocketMQ 消费者组配置 |
| 中间件 | 有变更 | RocketMQ 增加延迟消息用法 |
| 接口 | 无变更 | 本次无对外接口调整，MR !128 无 Controller 改动 |
| 页面 | 无变更 | 管理端沿用现有字段，MR !128 无前端改动 |
```

`code-change.md`：

```markdown
- 变更状态：有变更
- Merge Request：!128
- 源分支：feature/order-timeout
- 目标分支：master
- 起始提交：a1b2c3d
- 结束提交：e4f5g6h
- 修改工程：order-service
- 修改文件与符号：OrderTimeoutConsumer（新增）、OrderService.closeTimeoutOrder（新增）
- 代码变更说明：消费延迟消息，校验订单状态后关单
- 本地可验证范围：order-service 模块可独立编译测试
```

`database-change.md`：

```markdown
- 变更状态：有变更
- 数据库 / Schema：order_db
- 逻辑表：orders
- 字段变化：新增 close_reason VARCHAR(64) 可空
- 索引变化：无
- 约束变化：无
- DDL 或迁移路径：migrations/V20260718__add_close_reason.sql
- 上线状态：已随 2026-07-18 发布批次上线
- 兼容性：向后兼容（可空字段）
- 回滚方式：ALTER TABLE orders DROP COLUMN close_reason
```

`configuration-change.md`：

```markdown
- Manifest 配置领域状态：指定
- 变更状态：有变更
- 环境：prod
- 基线快照标识：cfg-2026-0711-prod
- 目标快照标识：cfg-2026-0718-prod
- （基线/目标批次、时间、来源类型、外部目录、指纹、范围摘要按实际填写）
- 纳入文件范围：order-service/*.yaml
- 涉及服务：order-service
- 配置组：rocketmq

| 配置键 | 变更类型 | 用途 | 脱敏值 |
| rocketmq.consumer.order-timeout.group | 新增 | 超时关单消费者组 | <redacted> |
```

`verification.md`：

```markdown
- 已执行测试：OrderTimeoutConsumerTest 单元测试通过
- 发布验证：预发环境消费验证通过
- 数据兼容验证：历史订单 close_reason 为空，查询无异常
- 配置生效验证：预发消费者组注册成功
- 回滚方式：回退 MR !128 并执行 DROP COLUMN
- 未验证项目：生产灰度未执行，存在关单延迟风险
- 风险：延迟消息堆积时关单延迟
```

### 2. 触发更新

```text
用 CHANGE-2026-0718-订单超时 变更包更新知识库。
```

### 3. Update 内部流程

1. **门禁校验**：Manifest 为 4.0 且合法 `complete` → 五份文档齐全、字段无空、矩阵状态合法 → 无敏感信息 → Git 起止提交在仓库中真实存在 → 基线/目标快照指纹与目录一致 → 变更矩阵与实际影响链一致；
2. **暂存更新**：沿影响链更新 `orders` 字段文档、order-service 服务文档、RocketMQ 中间件关系、配置文档、README 导航与术语——全部只写暂存，不动持久文件，`coverage.initialization` 五个字段逐字段保持不变；
3. **全链 global-validation**：暂存结果互相一致才通过；
4. **原子提交**：一次性落盘，追加 `change-history.md`，Manifest 的 `update.processed_packages` 登记 `CHANGE-2026-0718-订单超时`。

### 4. 失败示例

如果 `database-change.md` 的"回滚方式"留空：整个流程在第 1 步停止，知识库**原封不动**，返回缺失项清单和模板路径；补齐后重新执行即可。同一变更包重复提交会被幂等机制拦截，不会产生重复历史。

## Update 与重新初始化的区别

| | Update | 重新初始化 |
|---|---|---|
| 触发 | 准备变更包后自然语言触发 | 必须明确请求"重新初始化 Schema 4.0"并二次授权 |
| 范围 | 只更新变更影响链 | 清理旧产物后全量重建 |
| 历史 | 保留 `change-history.md` 和 Git/配置基线 | 全部失效 |
| 适用 | 日常迭代 | 知识库状态损坏或范围彻底变化 |

## 常见问题

### Q: 变更包缺一份文档会怎样

停止并返回缺失项、模板路径和补齐方式，不修改知识库。

### Q: 只想改一个小字段，也要五份文档吗

要。五份文档始终强制提供；无变更的领域在矩阵中填 `无变更` 并给出判断依据即可，字段级内容填 `不适用（具体原因）`。

### Q: 可以直接让 Skill 看 Git 提交自己总结变更吗

不行。Git Diff 只能验证你在变更包固定字段中的声明，不能替代变更包或扩大实体范围。

### Q: 初始化还没完成能 Update 吗

不能。`in_progress` 状态会停止并引导回 `knowledge-base-bootstrap` 续跑。

## 相关 Skills

- `knowledge-base-bootstrap`：初始化与续跑入口，Update 的前置。
- [knowledge-base-context](knowledge-base-context.md)：更新完成后按任务获取最小上下文。

## 技术细节

- [Skill 定义](../../cadence-init/skills/knowledge-base-update/SKILL.md)
- [变更包模板](../../cadence-init/skills/knowledge-base-update/user-input/change-package/)
- [增量更新指南](../../cadence-init/skills/knowledge-base-update/references/incremental-update-guide.md)
- [典型判定案例](../../cadence-init/skills/knowledge-base-update/references/demo.md)
