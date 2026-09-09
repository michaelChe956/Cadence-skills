# Proposal: rule-adherence-hardening-p1

## Why

业务项目使用 Cadence-skills 后持续出现三类违规：①跳过 workflow（不写 spec 就 plan、不 plan 直接改代码）；②不按规则优先使用 codegraph/ast-grep 检索；③该调 MCP 时不调。2026-09-02 的四端探针实验与调研（证据：`cadence/analysis-docs/2026-09-02_分析报告_L0规则加载四端探针实验_v1.0.md`、`cadence/analysis-docs/2026-09-02_规则遵循强化设计调研证据/`）确认了结构性根因：

1. 现有约束全部是提示词软约束，零 hook、零行为拦截——官方定调"CLAUDE.md 是上下文，不是强制配置"；
2. Claude Code 注入上下文时剥离 HTML 注释，`cadence-managed` 版本标记对其不可见；
3. Codex 不读 `.claude/rules/` 目录，②③类规则内容从未进入其上下文（列出的文件名恰好等于文本引用集）；
4. 规则要求"原生搜索不可用时用 MCP 兜底"在 pi 子代理上不可执行（子代理不继承 MCP），且 mcp-configuration 从未覆盖子代理可达性。

## What Changes

以"规则元数据为唯一事实源，按 harness 分级投影"为核心，新增五个工作包：

- **WP1**：`rule-config --verify` 只读自检子命令（L0 版本、规则哈希、投影漂移、软链解析；退出码可编程判定）；
- **WP2**：规则模板增加机器可读元数据（preferred/fallback/when），apply 时生成 `.claude/settings.json` 的 cadence-managed permissions 区块——fallback 工具进 **deny**，拒绝理由携带规则优先级链与兜底出口（模型自动改道、零人工），`CADENCE_BYPASS=1` 逃逸；
- **WP3**：L0 升级 v4，区块首行增加可见文本版本行（修复 Claude Code 剥离 HTML 注释导致的版本不可见）；
- **WP4**：Codex 规则自动内联投影——`.claude/rules/*` 为唯一源，apply 自动生成/维护 AGENTS.md 的 `cadence-managed:codex-rules-inline` 受管区块（≤60 行），加规则零手动维护；
- **WP5**：mcp-configuration 增补"子代理 MCP 可达性"（四端矩阵、Kimi glob 坑、验证探针步骤、pi 已知限制与规避），mcp-servers 规则模板增补"子代理兜底链"。

完整设计依据：`cadence/designs/2026-09-02_方案设计_规则遵循强化第一期_v1.0.md`（已获维护者批准）。

## Capabilities

### New Capabilities

- `permission-gate-projection`: 规则元数据驱动的 Claude Code 权限投影——deny 拦截、链式拒绝理由、逃逸阀与区块级受管合并
- `codex-rules-inline`: Codex 规则自动内联投影——AGENTS.md 受管区块的生成、预算约束与漂移检测
- `subagent-mcp-accessibility`: 四端子代理 MCP 可达性指引、验证探针与兜底链规则

### Modified Capabilities

- `rule-config-scripted-execution`: 新增 `--verify` 只读自检子命令的需求；新增 no-interrupt 下 deny 区块合并语义
- `managed-rule-lifecycle`: L0 版本化升级增加可见文本版本行要求（v4），修复 Claude Code HTML 注释剥离导致的版本不可见

## Impact

- **改动文件**：`rule-config.py`（新子命令+生成逻辑）、规则模板（元数据+v4+兜底链）、`mcp-configuration/SKILL.md`、`test_rule_config.py`（TDD）、`.github/workflows/ci.yml`（接入 pytest；不新增真实 CLI 车道）
- **不改动**：install.sh、软链层、`.mcp.json` 格式、Codex 配置同步逻辑——不触发真机实测门禁
- **业务项目应用**：全增量——更新 Cadence 源 → `rule-config dry-run/apply` → `--verify`，无 breaking change，新项目流程不变
- **已知代价**：pi/Kimi 因 AGENTS.md 内联区块多约 1.5KB 上下文（已获批准）；deny 在规则未覆盖边角场景可能致模型撞墙（以链式理由+逃逸阀缓解，观察期迭代文案）
- **非目标**（切片 2，设计要点已记录于设计文档 §12）：PreToolUse 时序门禁（攻①）、pi 扩展拦截器、eval 体系与 CI 夜间车道（目标 B 将并行立项）
