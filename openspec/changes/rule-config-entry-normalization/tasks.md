# Tasks: rule-config-entry-normalization

> 技术方案（v1.2）：`cadence/designs/2026-08-13_技术方案_rule-config入口规范化与产物覆盖及提交开关_v1.0.md`。实施遵循 TDD：先失败测试，后实现。

## 1. 权威清单与规范化算法（rule-config.py）

- [ ] 1.1 技术栈双入口不一致复现测试，定位根因并修复
- [ ] 1.2 定义 `CANONICAL_RULES`（含规则 6 内容 marker `cadence/project-rules/`）与 `RETIRED_RULE_FILES`（初始 `serena-usage.md`）
- [ ] 1.3 BASE 模板改由 `CANONICAL_RULES` 渲染；create 路径接入 `existing_rule_files`（Playwright 条件项）
- [ ] 1.4 `_normalize_mandatory_rules`：章节定位（首个匹配）/创建（L0 之后）、三分类（权威/失效/用户）、重建（重排编号、去重、用户块平移 + warning）
- [ ] 1.5 `_compose_entry` 移除全文规则 2 替换步骤
- [ ] 1.6 `_insert_l0_block` 无章节分支改插入 H1+首个简介段落之后
- [ ] 1.7 `TestNormalizeMandatoryRules` 17 用例（技术方案 §3.7）全绿

## 2. L0 v1→v2 接线与迁移不变量

- [ ] 2.1 `L0_BEGIN`/`L0_END` 升 v2；`l0_block` 旧版检测与 `_remove_l0_block_pair` versions 加入 v1
- [ ] 2.2 迁移不变量：升级后唯一区块；混合标记（旧版成对+当前单侧）先剥离再插入；重复当前区块归并 + `L0_DEDUP` warning
- [ ] 2.3 L0 测试改造：marker 常量版本参数化；新增 v1→v2 确定性 upgrade、v2 幂等、混合标记、重复归并、唯一性用例
- [ ] 2.4 `verify-managed-lifecycle.sh` 硬编码 v1 marker 同步为 v2

## 3. 产物路径覆盖表

- [ ] 3.1 脚本内定义映射表单一事实源常量
- [ ] 3.2 `agent-routing-kernel.md` 升 v2：路径映射覆盖表 + 优先级声明 + 自动提交开关条款
- [ ] 3.3 `document-storage.md` 同步映射表
- [ ] 3.4 三源（内核/document-storage/脚本常量）逐字一致性测试

## 4. 自动提交开关

- [ ] 4.1 `_ensure_commit_toggle`：确定性插入算法（首个 `## 项目配置`/缺失则文末创建/章节末尾落点/重复归并）、独立于 `tech_stack` 空值
- [ ] 4.2 取值语义：默认 `关闭`、保留用户值、非法值保留原文 + `INVALID_TOGGLE`
- [ ] 4.3 开关用例全绿（技术方案 §6 改动 3 清单）

## 5. warnings 报告契约

- [ ] 5.1 报告新增顶层 `warnings` 数组（schema：`code`/`file`/`message`/`detail`；6 错误码枚举）
- [ ] 5.2 三态一致（dry-run/apply/no-interrupt）且不影响 `overall`；测试覆盖

## 6. 语义与对账同步

- [ ] 6.1 `merge-semantics.md`：SM 表重写为 SM-01~05、L0 表"当前版本"表述更新、合计 62→64
- [ ] 6.2 `skill-clause-map.md` 条款对账与计数同步；`SKILL.md` 流程描述与计数同步
- [ ] 6.3 本仓库 `.claude/rules/` 副本与入口 L0 从规范源同步

## 7. 回归与验证

- [ ] 7.1 既有 160 个 unittest 全量回归通过
- [ ] 7.2 `verify-managed-lifecycle.sh` 通过
- [ ] 7.3 用 /tmp 两份问题入口文件 fixture 做端到端验证（Serena 清理、章节创建、双入口一致、开关落位）
