# Tasks: rule-adherence-hardening-p1

> 高层工作包；精确文件、命令、测试与提交步骤由 Plan（cadence/plans/）展开。每包映射 delta specs 的 requirement。

## 1. WP3：L0 v4 可见版本行（managed-rule-lifecycle）

- [x] 1.1 模板升级 v4：`agent-routing-kernel.md` 首行加可见文本版本行，v3 归档进 `l0-history/`，`L0_CURRENT_VERSION=v4`（TDD：v3→v4 确定性升级用例）
- [ ] 1.2 Claude Code 可见性验收：探针确认四端均能从上下文读出版本号

## 2. WP2：规则元数据 + 权限投影（permission-gate-projection）

- [x] 2.1 规则模板增加工具元数据（code-reading-coding、mcp-servers 起步：preferred/fallback/when）
- [x] 2.2 rule-config.py 实现元数据解析与 deny 区块生成（区块级受管、dry-run 预览、no-interrupt 保守合并）
- [x] 2.3 链式拒绝理由渲染（从元数据生成，含兜底出口与 CADENCE_BYPASS 提示）与 `--remove-permission-gate` 撤销
- [x] 2.4 TDD：生成/合并/撤销/allow 不降级/when 不成立不生成 五类用例

## 3. WP4：Codex 自动内联投影（codex-rules-inline）

- [x] 3.1 实现压缩渲染器（源=rules+元数据，60 行预算，截断标注）
- [x] 3.2 AGENTS.md `codex-rules-inline` 受管区块生成与增量更新
- [x] 3.3 TDD：加规则自动更新、区块外不变、预算截断、未生成 vs 漂移

## 4. WP1：--verify 只读自检（rule-config-scripted-execution）

- [x] 4.1 实现五项检查（L0 版本/规则哈希/权限投影漂移/内联漂移/软链解析）与结构化输出（JSON 可选）、退出码语义
- [x] 4.2 TDD：全绿 0、漂移 1、未生成不误报、JSON 可消费

## 5. WP5：子代理 MCP 可达性（subagent-mcp-accessibility）

- [x] 5.1 mcp-configuration SKILL.md 增补四端矩阵、各端坑位、验证探针步骤（仅告警不阻断）
- [x] 5.2 mcp-servers 规则模板增补子代理兜底链条款
- [ ] 5.3 探针验收：业务项目四端子代理可见性实测（Claude Code/Codex/Kimi 继承、pi 报已知限制）

## 6. 收尾

- [x] 6.1 CI 接入 rule-config pytest（现有车道内，不新增真实 CLI 车道）
- [x] 6.2 业务项目增量应用演练：update → dry-run → apply → verify 全绿（naruto 或等价 fixture 项目）
