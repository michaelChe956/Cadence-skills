# Proposal: script-rule-config-for-speed

## Why

`/rule-config --no-interrupt` 在 Claude Code 空项目上端到端耗时十几分钟，远超可接受范围。根因不是 shell 执行，而是全流程由 LLM 逐步读写文件：约 835 行规则模板经上下文"人肉搬运"、CLAUDE.md/AGENTS.md 被 4 个步骤反复读改写、OpenSpec 候选验证的 4 次 `openspec instructions --json` 大输出灌入上下文。仓库已有 pre-check 脚本化（#75）的成功先例，rule-config 需要同样的改造，把端到端耗时（不含整个 codegraph 步骤：install 与 init）压到 5 分钟以内。

## What Changes

- 新增 `cadence-init/skills/rule-config/scripts/rule-config.py`：python3 单脚本执行体，`dry-run`/`apply` 两阶段，JSON 报告驱动；所有文件操作（检测、规则文件、入口文件、目录、gitignore、OpenSpec 配置合并、codegraph）只在脚本内发生。CLI 提供用户意图参数（`--project-type`、`--ignore-cadence`、`--enable-playwright`、`--enable-codegraph`），承载现行"用户明确指定/要求"分支。
- 合并语义不丢：普通规则章节合并（no-interrupt）与不覆盖跳过（普通模式）、Markdown 不可解析回退、L0 受管区块、L1 版本化升级、OpenSpec 保守合并、历史目录两模式处理、技术栈与包管理器写入、备份屏障、原子发布全部在脚本内确定性实现；普通模式冲突由 Agent 在 dry-run 与 apply 之间逐条询问，no-interrupt 按权威合并规则自动决策。完整"模式×资产×冲突状态"矩阵移入 `references/merge-semantics.md`。
- **BREAKING（流程行为）**：删除 OpenSpec 候选验证的临时工作区与 4 次 `openspec instructions --json` 验证，由脚本内 YAML 解析 + 结构预检取代；CLI 健康门禁归属 pre-check。
- `SKILL.md` 从 758 行瘦身约 150 行编排骨架；被移除的合并语义正文迁移到 `references/` 作为权威定义按需加载。
- 生命周期测试从"shell 参考模型模拟 Skill 行为"改为直接测试脚本本体；新增"现行 SKILL 条款→fixture/test 映射表"并补齐既有 22 用例未覆盖的语义（历史目录、普通规则不覆盖、技术栈写入、gitignore、Playwright、Markdown 回退等）；`managed-lifecycle-reference.sh` 参考模型删除。
- codegraph install/init 仍在脚本内同步执行（不得异步）；install 失败时脚本仍按兜底配置自动补齐 `.mcp.json` 与 `.codex/config.toml`；整个 codegraph 步骤耗时单独计时、不计入 5 分钟预算。

## Capabilities

### New Capabilities

- `rule-config-scripted-execution`: rule-config 的脚本化两阶段执行——dry-run/apply 分离、冲突决策衔接、JSON 报告、失败关闭、幂等重跑与端到端耗时预算。

### Modified Capabilities

- `routing-conformance`: "路由目标和版本必须通过静态检查" requirement 中的可执行生命周期参考模型要求变化——测试对象从参考模型改为脚本本体，"候选 instructions 验证"改为"候选 YAML 解析与结构预检"，失败关闭场景相应更新。

## Impact

- **代码**：新增 `cadence-init/skills/rule-config/scripts/rule-config.py`、`cadence-init/skills/rule-config/tests/test_rule_config.py`；改造 `tests/verify-managed-lifecycle.sh`；删除 `tests/helpers/managed-lifecycle-reference.sh`。
- **文档**：重写 `cadence-init/skills/rule-config/SKILL.md`；新增 `references/merge-semantics.md`；`.claude/rules/` 与 `cadence/project-rules/` 不受影响。
- **依赖**：运行环境需要 python3 与 PyYAML；PyYAML 缺失时脚本以专属退出码退出，经 `uvx --with pyyaml` 兜底重跑（pre-check 已保证 uvx 可用），不新增强制安装步骤。
- **使用方**：Claude Code / Codex / pi 调用 `/rule-config` 的交互不变；普通模式冲突询问时机变为 dry-run 之后。
- **验收**：Claude Code 真实环境空项目端到端 ≤5 分钟（不含整个 codegraph 步骤：install 与 init），且不丢失任何现行合并、备份与失败关闭语义。
