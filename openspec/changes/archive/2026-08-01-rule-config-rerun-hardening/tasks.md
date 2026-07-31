# Tasks: rule-config-rerun-hardening

## 1. P0：merge_markdown 幂等修复（对应 Requirement: 合并与保护语义脚本内确定性实现）

- [x] 1.1 新增失败回归测试 `ut-merge_markdown-rerun-idempotent`：断言 merge(t, merge(t, x)) == merge(t, x)，覆盖多同名章节含项目补充场景
- [x] 1.2 新增失败测试 `ut-merge_markdown-polluted-self-heal`：已含重复标记的文件合并后仅保留一个标记行且项目内容不丢
- [x] 1.3 实现：标记字符串提升为模块级常量；项目独有行过滤排除保留字标记行；确认 1.1/1.2 转绿

## 2. unchanged 跳过写盘（对应 Scenario: 合并结果一致跳过写盘）

- [x] 2.1 新增失败测试：no-interrupt 下合并结果与现有文件一致时不写盘、报告动作 `unchanged`
- [x] 2.2 实现：step_s3 普通规则 no-interrupt 分支增加逐字比较与 unchanged 动作；确认测试转绿

## 3. dry-run 冲突报告模式感知（对应 Requirement: dry-run 冲突报告标注 no-interrupt 真实动作）

- [x] 3.1 新增失败测试：no-interrupt dry-run drift 冲突条目含 `no_interrupt_action: "markdown-merge"`；普通模式不含该字段
- [x] 3.2 实现：compute_plan 普通规则 drift 冲突条目按模式增量字段；确认测试转绿

## 4. RF-04 去特判（对应 Scenario: 缺 CodeGraph 段落统一合并）

- [x] 4.1 删改现有 report-only 断言为失败测试：no-interrupt 下缺 CodeGraph 段落的 code-reading.md 被自动合并（模板段落并入、项目内容保留、有备份）；普通模式走统一冲突询问
- [x] 4.2 实现：删除 compute_plan 与 step_s3 的 codegraph-section-missing 特判分支；确认测试转绿

## 5. 文档同步

- [x] 5.1 更新 merge-semantics.md：NC-03 行补充保留字与幂等语义、RF-04 行改写为统一合并、补充 unchanged 动作说明
- [x] 5.2 更新 SKILL.md 脚本定位段落：补 plugin 安装场景候选根与缓存缺 scripts/ 重装指引
- [x] 5.3 更新 tests/skill-clause-map.md 条款映射

## 6. 验证

- [x] 6.1 全量运行 rule-config 测试套件并确认通过
- [x] 6.2 openspec validate 通过
