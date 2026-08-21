# Tasks: slim-l0-routing-kernel-v3

## 1. 失败测试先行（TDD）

- [x] 1.1 新增 v2→v3 升级五分类单测：逐字 v2 → `upgrade`、v2 漂移（含手加 knowledge-base 门禁行）→ `drift` 且 apply 后为 v3、v1 逐字 → `upgrade`、v0 合法成对 → `upgrade`、无标记 → `insert`；运行 `pytest tests/test_rule_config.py` 确认新用例失败（版本常量仍为 v2）
- [x] 1.2 新增 v3 模板内容契约单测：`agent-routing-kernel.md` 为 v3 标记、体量 ≤2KB、包含四条铁律/KB 门禁句/路径覆盖表/自动提交开关/客户端中性短说明，且不含"静默""引导句""事件之间"类姿态关键词；确认失败后进入实现
- [x] 1.3 盘点并更新受模板全文逐字比对影响的既有用例清单（`ARTIFACT_PATH_OVERRIDE_TABLE` 一致性、本仓库入口比对、skill-clause-map），先标记预期失败

## 2. L0 v3 模板与升级机制

- [x] 2.1 将现 v2 模板全文逐字复制到 `references/rules/l0-history/agent-routing-kernel-v2.md`，用逐字比对命令（`diff`/单测）确认与复制前的 `agent-routing-kernel.md` 完全一致
- [x] 2.2 重写 `references/rules/agent-routing-kernel.md` 为 v3（≤2KB）：精简路由表（合并"必读规则"列）、四条铁律、KB 门禁 2-3 行、路径覆盖表、自动提交开关、阶段切换一句话、客户端中性短说明；`wc -c` 验证体量
- [x] 2.3 修改 `scripts/rule-config.py`：`L0_CURRENT_VERSION="v3"`、`L0_OLD_VERSIONS=["v2","v1","v0"]`、`L0_OLD_SOURCES` 增加 v2 历史源；不改动 `l0_block()` 分类逻辑
- [x] 2.4 运行 `pytest tests/test_rule_config.py`，确认 1.1/1.2 新用例与全部既有用例通过

## 3. L1 瘦身

- [x] 3.1 瘦身 `references/rules/openspec-superpowers-workflow.md`：保留职责边界、标准流程 7 步、可判定失败关闭、OpenSpec 强制阈值与豁免；删除四客户端时序细节与姿态条款；单测确认 L1 分类（skip/replace）与逐字比对用例更新后通过

## 4. 本仓库与实测验证

- [x] 4.1 本仓库跑 rule-config dry-run + apply：入口 L0 升到 v3，`CLAUDE.md`/`AGENTS.md` 双入口一致，块外内容逐字不变，`cadence/legacy/` 归档存在
- [x] 4.2 naruto 实测（v2 + 手加 KB 门禁行）：dry-run 报 v2 drift；apply 后 L0=v3、KB 门禁保留（来自模板）、双入口一致、受管区块外用户内容不动
- [x] 4.3 非 KnowledgeBase 项目冒烟：确认 v3 门禁段条件性描述无副作用（无知识库提示、无额外文件生成）
- [x] 4.4 运行完整验证套件（`pytest tests/test_rule_config.py` + `tests/verify-managed-lifecycle.sh`）并记录输出，作为完成证据
