## 1. 期 1：九场景路由矩阵（规则文本重构）

- [ ] 1.1 重构 `cadence-init/skills/rule-config/references/rules/code-reading-coding.md`：顶部九场景路由矩阵（Markdown 表格，含判断信号与冲突优先级），正文保留 ast-grep/CodeGraph 使用细节；顶部元数据换 schema v2（schema_version/default_mode/recommended_profile，去除 fallback/when deny 用途）
- [ ] 1.2 `code-reading-noncoding.md` 同步 v2 元数据（该模板无 gate 元数据，仅对齐 schema）
- [ ] 1.3 `mcp-servers.md` 检索路由段与路由矩阵对齐：Context7（D 场景）/webSearchPrime/webReader/zread（R/U 场景）的触发场景表述与矩阵一致化，交叉引用矩阵；元数据换 v2
- [ ] 1.4 CLAUDE.md 模板（cadence-init 源）顶部加 ≤12 行场景决策卡；实现矩阵↔决策卡一致性快照校验（rule-config verify 项或独立测试）
- [ ] 1.5 rule-config `parse_tool_metadata` 升级：v2 schema 解析+v1 兼容读取（不产生 deny）+报告提示升级；快照测试
- [ ] 1.6 TDD 全套：矩阵存在性/决策卡一致性/元数据 v2 解析/v1 兼容/规则分发幂等（新规则文件分发到 .claude/rules/ 四端投影不变机制复用）

## 2. 期 2：gate 三模式

- [ ] 2.1 `collect_permission_gate_entries`/`merge_permission_gate` 按模式分流：text 零写入/safe 仅危险命令形态 deny（定义最小危险命令集合）/strict 现行全量；CLI 加 `--enable-permission-gate={safe|strict}`（默认 text）
- [ ] 2.2 ❌ 文案条目废除：`render_deny_reason` 停止写入 deny 区块（strict 模式亦然）；deny 理由职责回归规则正文
- [ ] 2.3 旧无标记 gate 区块迁移：apply 检测 v1 旧区块时提示显式选择模式（text 清除/safe 收窄/strict 保留），不静默沿用
- [ ] 2.4 危险命令形态集合定义与测试（递归删除类/敏感路径覆盖类；参数可识别；不含按工具名全局 deny）
- [ ] 2.5 TDD：三模式生成矩阵测试（text 空/safe 窄面/strict 全量）/用户 allow 不降级保留/`--remove-permission-gate` 三模式通用/v1 区块迁移路径/verify 与 apply 同源重算一致

## 3. 期 3：夜测演进（trust 修复+三组矩阵+场景化探针）

- [ ] 3.1 trust 修复：fixture 准备阶段写入 `hasTrustDialogAccepted` 到夜测隔离 HOME 的 claude 全局配置；启动后断言 stderr 无 `Ignoring ... permissions.allow`（失败即夜测失败）
- [ ] 3.2 探针 argv 白名单补 `mcp__codegraph`；确认全工具预授权口径（B/Grep/Glob/MCP 全集）
- [ ] 3.3 fixture 三组生成：control 裸（现 control）/installed-text（规则栈 v2，无 deny）/installed-gate-safe（规则栈+safe gate）；strict 低频 smoke 组
- [ ] 3.4 探针场景化重编：D/R/C/M/S/G/T/F/U 各≥3 例（正例断言首选工具、反例断言不误伤——M 场景 rg 必须可用且首选）
- [ ] 3.5 评分五指标：first_tool_accuracy（主）/task_completion/route_recovery/false_positive_block/denial_count；report.md 矩阵按三组×场景呈现；基线 diff 口径更新
- [ ] 3.6 mock 模式全套演练（night smoke）+单端真实夜测验证（claude 先行，trust 断言生效+三组跑通+M 反例通过）

## 4. 收尾

- [ ] 4.1 `openspec validate --strict` 通过；spec delta 与实现逐条对齐复核
- [ ] 4.2 全量回归三件套：pre-check test.sh / eval 全量 / openspec validate --all --strict；ledger 收尾
