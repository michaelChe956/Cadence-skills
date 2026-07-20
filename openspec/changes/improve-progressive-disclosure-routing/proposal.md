## Why

已执行 Cadence 初始化的业务项目虽然已经具备 OpenSpec 与 Superpowers，但 `CLAUDE.md`、`AGENTS.md` 仍只要求“按需查看”规则，没有告诉 Claude Code、Kimi Code 等 Agent 在哪个阶段必须读取哪份规则、调用哪个 Skill。结果是工具已经安装，Agent 仍可能跳过 brainstorming、writing-plans、TDD 或完成前验证，OpenSpec 与 Superpowers 也容易被当成两套互相替代的流程。

## What Changes

- 明确 OpenSpec 是契约层，负责 Why、范围、非目标、架构边界、验收标准和高层工作包；Superpowers 是行为层，负责探索、规划、调试、TDD、执行、审查、验证和分支收尾。
- 由 `rule-config` 在 `CLAUDE.md` 与 `AGENTS.md` 中生成短小的常驻路由内核，使 Agent 在新任务、阶段切换、上下文恢复和完工声明前重新判断应读取的规则与应调用的 Skill。
- 新增完整的 OpenSpec 与 Superpowers 协作规则，规定阶段门禁、失败关闭、冲突裁决、轻量豁免，以及 OpenSpec 高层工作包与 Superpowers 实施 Plan 的映射关系。
- 在 `openspec/config.yaml` 的公共上下文和 artifact 规则中冗余关键职责与产物边界，使 OpenSpec 产物本身也携带协作契约。
- 使用版本化受管内容让已初始化项目重新运行 `rule-config` 后获得新版路由，同时保留项目自定义内容。
- 通过静态检查和 Claude Code、Kimi Code、Codex 场景验证，确认关键阶段不会静默漏读规则、漏调 Skill 或越过门禁。

## Capabilities

### New Capabilities

- `progressive-context-routing`: 定义常驻路由内核、任务与阶段触发映射、路由回执、失败关闭和轻量豁免。
- `managed-rule-lifecycle`: 定义完整协作规则的规范来源、`rule-config` 生成方式、版本化升级和用户内容保护。
- `routing-conformance`: 定义 OpenSpec 配置冗余、契约与 Plan 的可追溯关系，以及跨客户端路由验证。

### Modified Capabilities

无。当前仓库没有已有的 OpenSpec capability。

## Impact

- 影响 `cadence-init/skills/rule-config/` 的规则模板、入口生成和增量升级说明。
- 影响业务项目根目录的 `CLAUDE.md`、`AGENTS.md`、`.claude/rules/openspec-superpowers-workflow.md` 与 `openspec/config.yaml`。
- 影响当前仓库中上述生成内容的同步副本，以及相关使用说明和验证记录。
- 不负责安装 OpenSpec 或 Superpowers；`/pre-check` 已承担该职责。
- 不依赖或修改 legacy 的 `cadence-workflow`，不新增 Hook、运行时插件或阅读状态服务。
