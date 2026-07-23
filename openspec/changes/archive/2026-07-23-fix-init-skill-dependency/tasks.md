# Tasks: fix-init-skill-dependency

## 1. pre-check 验收口径调整

- [x] 1.1 调整 pre-check 的 OpenSpec 完成门槛（no-interrupt 强制完成策略表、快速参考表、步骤 5 验证命令块），移除 `openspec/config.yaml` 断言（映射 Requirement: OpenSpec 检查完成门槛不含 config.yaml）
- [x] 1.2 新增 config.yaml 缺失的中文提示语义，两种参数模式均不因此失败（映射 Requirement: config.yaml 缺失提示语义）

## 2. pre-check 增量分支补齐

- [x] 2.1 将步骤 5 增量分支重写为按 claude/codex/pi 客户端产物存在性检测，缺失客户端精确 init 后执行 update（映射 Requirement: 按客户端检测的增量补齐）
- [x] 2.2 核验六个基础检查门槛地位与失败语义条款在改动后保持完整（映射 Requirement: 硬门槛与失败语义保留）

## 3. README 职责边界同步

- [x] 3.1 更新 README 的 `/pre-check`、`/rule-config` 说明行与 no-interrupt 行为表的 OpenSpec 口径（映射 Requirement: README 职责边界同步）
- [x] 3.2 更新 README 初始化顺序说明段，补充两个 Skill 的职责边界与顺序约束（映射 Requirement: README 职责边界同步）

## 4. 一致性核验

- [x] 4.1 逐条对照 specs 验收场景核验 pre-check 与 README 改后全文，确认无残留"config.yaml 为完成条件"的矛盾表述（映射全部 Requirement）
