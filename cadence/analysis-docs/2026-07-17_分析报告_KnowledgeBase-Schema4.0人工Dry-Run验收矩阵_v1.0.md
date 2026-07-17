# KnowledgeBase Schema 4.0 人工 Dry-Run 验收矩阵

## 文档元数据

- 文档类型：分析报告
- 日期：2026-07-17
- 版本：v1.0
- 验收方式：规则级人工 dry-run
- 适用范围：`cadence-init/skills/knowledge-base-*`

## 验收方法

本矩阵不执行数据库、配置中心、部署、迁移或业务脚本，也不创建真实配置快照。每个场景按以下顺序人工核对：

1. 固定 Manifest 4.0、用户输入或变更包前提。
2. 从对应 Skill 的前置门禁开始逐条走查。
3. 记录应继续、停止、降级或跳过的分支。
4. 核对模板、指南、Demo 和完成条件是否支持同一结论。
5. 只在所有文件语义一致时标记 `PASS`。

敏感场景只使用“敏感内容占位”描述，不写入任何真实配置值、凭证、内部地址或敏感哈希。

## Dry-Run 矩阵

| ID | 场景与输入 | 人工走查步骤 | 预期结果 | 规则证据 | 结果 |
|----|------------|--------------|----------|----------|------|
| DR-01 | 无 DDL，但存在 Entity、Mapper 和 SQL | Bootstrap 校验数据模型至少一种可定位证据 → BaseInfo 生成字段级文档 → 未确认数据库属性标记待确认 | 继续，不把 DDL 设为硬前置 | Bootstrap 输入契约；BaseInfo 数据模型规则 | PASS |
| DR-02 | DDL 与代码字段不一致 | BaseInfo 分别读取 DDL 与代码映射 → 不静默覆盖 → 写入来源冲突 | 双方证据保留 | BaseInfo Skill 与分析指南 | PASS |
| DR-03 | 使用锁定发布批次的测试配置包建立基线 | Bootstrap 校验目录、环境、批次、指纹、范围摘要 → 校验快照标识唯一映射 → 写入 Manifest baseline | 建立可审计配置基线 | Bootstrap Skill、配置范围模板、Manifest 模板 | PASS |
| DR-04 | 配置快照包含大量重复文件 | BaseInfo 在授权范围内临时比较内容 → 相同内容合并分析 → 不保存重复文件哈希 | 不重复生成配置知识 | BaseInfo Skill 与配置指南 | PASS |
| DR-05 | 快照包含敏感配置 | BaseInfo 识别敏感键 → 只保留键、用途、类型和绑定 → 值固定为 `<redacted>` | KnowledgeBase 无明文和敏感哈希 | BaseInfo Skill 与服务配置模板 | PASS |
| DR-06 | Update 未指定变更包 | Update 调用契约检查唯一 `CHANGE-*` 路径 → 路径缺失 | 立即停止并返回目标与模板路径 | Update Skill 调用契约 | PASS |
| DR-07 | Update 缺少任一主文档 | 校验五份固定文档 → 发现缺失 → 不读取 Git Diff 或快照 | 立即停止，不生成半成品 | Update Skill、增量指南、Demo 场景二 | PASS |
| DR-08 | 五份文档齐全，部分领域无变更且依据完整 | 先过全包敏感门禁 → 校验领域矩阵和对应文档 → 适用领域按证据验证 | 允许继续更新 | Update Skill 完整性门禁 | PASS |
| DR-09 | 配置范围适用，声明无配置变更但双快照有差异 | 校验双快照 → 比较指纹和内容 → 与无变更声明冲突 | 停止并保留来源冲突 | Update Skill、增量指南、Demo 场景三 | PASS |
| DR-10 | 代码字段变化但数据库文档声明无变更 | 校验提交范围 → 对照 Mapper/Entity 与数据库文档 → 依据不足 | 停止，不伪造数据库变更 | Update Skill、Demo 场景四 | PASS |
| DR-11 | Context 从 API 追踪到服务、表字段、配置键和快照 | 从任务种子定位 API → 扩展服务 → 读取表文档 → 校验配置范围摘要与指纹 → 读取相关配置 | 输出四类最小上下文 | Context Skill 与渐进检索指南 | PASS |
| DR-12 | Context 任务依赖配置但外部目录失效 | 确定直接配置关系 → 进入范围与指纹门禁 → 目录不可读 | 配置方向阻断，不连接远程源 | Context Skill 异常表 | PASS |
| DR-13 | Overview 生成适用领域导航 | 读取 Manifest → 对适用领域输出链接 → 保持入口只含摘要和导航 | 可导航到字段级模型和服务配置 | Overview Skill 与项目概览模板 | PASS |
| DR-14 | Mapper XML 出现在配置包 | BaseInfo 文件分类 → Mapper XML 转交数据模型 → 配置文档只保留关系 | 不作为普通配置键文件 | BaseInfo 分析指南 | PASS |
| DR-15 | 重复执行相同变更包 | 全包敏感门禁通过 → 计算相同幂等标识 → 命中 `processed_packages` | 不重复历史、实体或基线 | Update Skill、增量指南、Demo 场景五 | PASS |
| DR-16 | 目标目录已有 KnowledgeBase 固定产物 | Bootstrap 检查 Manifest 或任一固定输出：Manifest 缺失/损坏/非 4.0 时停止；4.0 但无显式重新初始化授权时停止；仅用户授权“重新初始化 Schema 4.0”的精确清理范围与风险后，才清理并全新重建。其他六个消费 Skill仍拒绝非 4.0 | 不把缺失 Manifest 但已有输出误判为首次初始化；不覆盖或迁移旧产物；不把普通初始化请求当作清理授权 | Bootstrap Skill、输入契约、输入清单与 Demo；其他六个 `SKILL.md` | PASS |
| DR-17 | `scope.configurations.status` 为 `不适用` 的纯代码或数据库更新 | `configuration-change.md` 存在并声明无变更 → 原因与 Manifest 一致 → 快照字段为带原因不适用 → 跳过快照比较 | 不因缺少快照阻断；不创建配置基线 | Update Skill、模板、指南、Demo 场景六、Overview 说明 | PASS |
| DR-18 | 配置范围适用但缺少 `scope_summary` 或文件/服务/规则摘要 | Bootstrap 或消费者读取可审计范围字段 → 发现缺失 | 扫描前停止，不自行推断范围 | Bootstrap、BaseInfo、Context、Update | PASS |
| DR-19 | 同一 `snapshot_id` 对应不同环境或目录 | Bootstrap/BaseInfo/Update/Context 核对唯一映射 → 发现冲突 | 停止并记录来源冲突，不覆盖映射 | 四个 Skill 与 Bootstrap Demo | PASS |
| DR-20 | 代码有变更但缺少独立代码变更说明 | Update 校验 `code-change.md` → 字段缺失或为空 | 停止；无代码变更时必须填带原因的不适用 | Update Skill、模板与指南 | PASS |
| DR-21 | 五份主文档之一包含敏感内容占位所代表的真实值 | Update 先执行全包敏感门禁 → 命中风险 | 在幂等哈希前停止，不读取后续证据 | Update Skill、五份模板、Demo 场景七 | PASS |
| DR-22 | 附件包含原始敏感配置或敏感值哈希 | 遍历附件门禁 → 命中禁止项 | 在幂等哈希前停止 | Update Skill、附件说明、增量指南 | PASS |
| DR-23 | 接口或页面领域为 `不适用` 且说明性 README 不存在 | Overview 读取 Manifest 状态 → 输出无链接 `不适用（原因）` 条目 | 不生成失效链接，仍保留稳定导航位置 | Overview Skill、两个模板、Demo | PASS |
| DR-24 | Context 未定位当前实现 | 证据矩阵状态选择固定枚举 | 统一使用设计枚举 `代码缺失`，不保留旧状态词 | Context Skill、模板、指南、用户说明 | PASS |
| DR-25 | Manifest 生命周期与待确认计数 | Bootstrap 写入知识库首次生成时间和初始四级计数 → BaseInfo/Update 保留 `generated_at` → 每次待确认项变化后按未解决条目重算四级计数并原子写入 | 时间字段不被后续写入者覆盖；blocking/high/medium/low 与待确认文档一致 | Manifest 模板、Bootstrap、BaseInfo、Update 与待确认模板 | PASS |

## 逐项核对结论

- 原设计 16 个验收场景：16/16 PASS。
- 新增配置不适用 Update 场景：PASS。
- 审查补充的范围摘要、快照标识冲突、代码说明、敏感门禁、条件导航、状态枚举和 Manifest 元数据场景：8/8 PASS。
- 总计：25/25 PASS。

## 实际核对证据

2026-07-17 在 Schema 4.0 worktree 中按矩阵顺序执行规则级断言，逐项输出 `DR-01 PASS` 至 `DR-25 PASS`。核对内容包括：

- DDL 可选、多源冲突、重复配置合并和敏感脱敏规则。
- Update 显式入口、五文档门禁、无变更依据、配置适用双快照、配置不适用分支、幂等和敏感门禁顺序。
- Context 四类证据路径、配置目录阻断、可审计范围摘要和固定状态枚举。
- Overview 适用链接与不适用无链接条目。
- Manifest `generated_at` 与四级 `open_questions` 默认计数。

DR-11 的四类证据路径分别按四条独立规则断言，避免把分行定义误当作单行文本。最终 25 项断言全部退出码 0。

## 边界说明

- 本矩阵验证规则与模板分支，不冒充真实业务仓库、真实配置快照或在线系统验证。
- 配置范围为 `全量` 或 `指定` 时，双快照、目录、指纹与范围摘要门禁保持不变。
- 只有 Manifest 明确声明配置领域 `不适用` 且原因一致时，Update 才允许跳过快照比较。
- Schema 4.0 是唯一支持版本；未增加任何旧版兼容、迁移或字段映射逻辑。
