## Why

规则文档的场景化引导意图（"大范围检索优先 CodeGraph""小配置可直接读取"）在两处失真：①permission gate 把 fallback 工具物化为全局无条件 deny（Grep/Glob/Bash(grep/rg/find:*)/WebSearch/WebFetch 一律拦），规则正文明确允许的场景（配置查询/小文件直读/实时调研）被物理误伤；②场景指引散落 335 行长文且覆盖不全（Markdown 检索场景缺失），模型自主路由缺乏清晰依据。夜测实证（2026-09-06）进一步证明：deny 引导文案模型不可见、workspace trust 使 settings allow 失效、headless 无授权出口——"规则遵循率"主指标从未被真实度量。

## What Changes

- 新增九类场景工具路由矩阵（库文档/开放调研/代码结构/Markdown 配置文本/Shell 日志/Git 历史/测试定位/路径发现/已知 URL 精读），作为规则文件的规范源：矩阵置顶 + CLAUDE.md 极简决策卡（≤12 行）
- **BREAKING** permission gate 默认行为反转：默认安装不再生成任何 deny（text 模式）；物理拦截改为显式 opt-in，且收窄为参数可识别的危险命令形态（safe 模式）；现行全量 deny 降级为 strict 实验模式（仅供 opt-in/夜测 smoke 回归）
- 规则元数据 schema v2：`cadence-tools` 块不再含 fallback deny 列表，仅保留稳定字段（schema_version/default_mode/recommended_profile）
- 废除 deny 区 ❌ 中文文案条目（实证模型不可见），引导职责完全回归规则文本
- 夜测矩阵演进：control 裸 / installed-text（主指标=首次工具选择正确率）/ installed-gate-safe 三组对照；探针按场景重编（D/R/C/M/S/G/T/F/U，每场景≥3 正反例）；夜测 fixture 写入 workspace 信任标记并断言 stderr 无 `Ignoring ... permissions.allow`
- 预留（本期不实施）PreToolUse hook 审计层

## Capabilities

### New Capabilities
- `scenario-tool-routing`: 九类场景的工具路由规范——场景枚举、每场景首选链/次选/判断信号/冲突优先级（任务目标 > 对象类型 > 范围 > 时效性）、规则文件与 CLAUDE.md 决策卡的投影关系、单源一致性约束

### Modified Capabilities
- `permission-gate-projection`: 默认行为反转（默认不生成 deny）+ 三模式（text/safe/strict）定义与启用方式 + 元数据 schema v2 + 旧无标记 gate 区块的迁移提示 + ❌ 文案条目废除
- `pre-check-scripted-execution`: 无直接变更（pre-check 流程不涉及）；夜测侧矩阵定义不在产品 spec 范围，落 eval 配置与探针实现
