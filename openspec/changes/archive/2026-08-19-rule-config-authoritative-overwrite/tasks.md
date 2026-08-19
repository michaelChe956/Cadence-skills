# Tasks: rule-config-authoritative-overwrite

## 1. 测试先行（TDD 红）

- [x] 1.1 改写规则文件 drift 的普通模式用例：断言两模式统一"归档+权威覆盖、无冲突条目、不要求决策文件"（映射 `rule-config-scripted-execution`「合并与保护语义脚本内确定性实现」）
- [x] 1.2 改写 L1 drift/unmarked 用例：断言两模式统一"归档+当前框架版本替换、不经用户决策"（映射 `managed-rule-lifecycle`「L1 框架规则升级必须保护无法识别的本地内容」）
- [x] 1.3 改写 L0 drift 与单侧/顺序错误标记用例：断言两模式统一"屏障归档+规范源替换/安全归并"（映射 `managed-rule-lifecycle`「L0 入口内容必须版本化且可安全升级」）
- [x] 1.4 改写 `rules.apply` 普通模式用例与 OS-03/05 用例：断言"归档+移除键+保守合并"与"归档+模板整体替换"（映射 `rule-config-scripted-execution`「OpenSpec 配置验证以结构预检取代 instructions 验证」）
- [x] 1.5 更新 `verify-managed-lifecycle.sh` 生命周期测试：不可解析 YAML/类型冲突改为归档+替换断言，漂移保护改为权威覆盖断言（映射 `routing-conformance`「路由目标和版本必须通过静态检查」）

## 2. 脚本实现（TDD 绿）

- [x] 2.1 `compute_plan` 移除六类状态的冲突条目生成（S3 规则文件 drift、L1 replace 类、L0 drift/异常标记、S7 rules.apply 与结构/解析冲突），保留计划动作与备份需求（映射「当前无活跃冲突类型」scenario）
- [x] 2.2 S3 apply 合流普通模式到权威覆盖分支，退役 `rules-keep`/`rules-replace`/`l1-keep`/`l1-replace` 决策分支名（映射「普通模式框架规则文件权威覆盖」scenario）
- [x] 2.3 S4 apply 合流 L0-03/L0-06 普通模式到备份+替换/安全归并路径（映射「当前版本受管区块存在内容漂移」「单侧或顺序错误标记确定性归并」scenario）
- [x] 2.4 S7 apply 合流 `rules.apply` 普通模式到"归档+移除+保守合并"；OS-03/05 两模式改为"归档+模板整体替换"，移除 no-interrupt 终止分支（映射「无法无损规范化的既有配置归档后模板替换」scenario）
- [x] 2.5 清理 `no_interrupt_action` 字段与相关报告代码；确认决策机制（`--decisions`/`validate_decisions`/`default_keep`）休眠兜底语义不变

## 3. 文档与对账同步

- [x] 3.1 更新 `SKILL.md`：普通模式流程移除逐条提问/无响应处理步骤，冲突汇报规则改为依据 `steps[].actions[]`
- [x] 3.2 更新 `references/merge-semantics.md`：RF-05/L1-04~06/L0-03/L0-06/OS-03~05 表行两模式列、§11.6 A 类清单清空并标注机制休眠、决策 schema 说明
- [x] 3.3 更新 `references/rules/README.md` 的 keep 默认描述
- [x] 3.4 更新 `tests/skill-clause-map.md` 条款对账（测试 ID、关键断言、语义变更标注）

## 4. 全量验证

- [x] 4.1 pytest 全量通过，无跳过之外的失效用例
- [x] 4.2 shell 集成/生命周期测试通过
- [x] 4.3 真实临时项目两模式端到端验证：drift 项目普通模式与 no-interrupt 产物逐字一致、归档齐全、无提问交互
