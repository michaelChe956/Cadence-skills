# Tasks: 支持 Kimi Code 第四客户端

## 1. pre-check：OpenSpec 四客户端产物

- [x] 1.1 将 `cadence-init/skills/pre-check/SKILL.md` 步骤 5 的三客户端初始化命令更新为四客户端：新项目 `openspec init --tools claude,codex,pi,kimi`；按缺失客户端补齐的命令示例补充 `--tools kimi` 分支
- [x] 1.2 在步骤 5 的客户端就绪判定表新增 kimi 行：`.kimi-code/skills/` 下存在 5 个 `openspec-*` 目录即就绪
- [x] 1.3 更新步骤 5 的验证命令，新增 kimi 产物检查（`test -f .kimi-code/skills/openspec-propose/SKILL.md` 与 5 个目录计数）
- [x] 1.4 更新步骤 5 的产物结构说明：kimi 为 `.kimi-code/skills/openspec-*`，无 commands/adapter（与 OpenSpec CLI 实测一致）
- [x] 1.5 全篇"三客户端"表述改为"四客户端"（no-interrupt 强制完成策略表、检查流程图、快速参考表、判定规则、增量示例）
- [x] 1.6 查证 OpenSpec `--tools kimi` 的最低版本并在 SKILL.md 标注（与 pi ">= 1.4.1" 同款注记）；确认 `--tools pi` 注记一并保留
- [x] 1.7 更新 `scripts/pre-check.sh` 头部职责边界注释（OpenSpec 三客户端产物 → 四客户端），无逻辑改动

## 2. pre-check：Superpowers 覆盖说明

- [x] 2.1 在步骤 6 Superpowers 的目录约定与说明中注明：`~/.agents/skills` 通用层已被 Kimi Code 扫描（用户级通用 skills），Kimi 无需额外同步层；不新增 `~/.kimi-code/skills` 软链目标

## 3. mcp-configuration：Kimi 复用根目录 `.mcp.json`

- [x] 3.1 在 `cadence-init/skills/mcp-configuration/SKILL.md` 新增 Kimi 消费方式说明：Kimi Code 原生读取项目根 `.mcp.json`（源码与测试证实三层加载：`~/.kimi-code/mcp.json`、`<项目根>/.mcp.json`、`<cwd>/.kimi-code/mcp.json`），复用本 Skill 已生成的文件，无需第二份配置
- [x] 3.2 更新检查清单与处理流程：明确不为 Kimi 生成 `.kimi-code/mcp.json` 副本、不新增 `.gitignore` 条目；`directTools` 等未知字段被 Kimi 非严格 schema 静默剥离，无需专门处理
- [x] 3.3 更新客户端格式差异表，新增 Kimi 列（复用根目录 `.mcp.json`、JSON、stdio/HTTP/SSE 均支持）
- [x] 3.4 补充 Kimi 侧验证方式（`/mcp` 查看连接状态、`/mcp-config` 交互管理）与 API Key 安全提醒覆盖 Kimi

## 4. rule-config：项目类型扫描剪枝

- [x] 4.1 在 `scripts/rule-config.py` 的 `PRUNE_DIRS` 常量增加 `.kimi-code`
- [x] 4.2 在 `cadence-init/skills/rule-config/SKILL.md` 的有界扫描 find 剪枝目录清单同步增加 `.kimi-code`
- [x] 4.3 运行 harness 断言 `assert_bounded_source_scan_contract` 确认两处清单逐项一致

## 5. README 与文档

- [x] 5.1 `README.md` 全篇"三客户端"表述更新为四客户端（claude/codex/pi/kimi）
- [x] 5.2 更新 `README.md` skills 表格：`/pre-check` 行加入 kimi 客户端产物说明；`/mcp-configuration` 行加入 Kimi 原生读取根目录 `.mcp.json` 的说明
- [x] 5.3 在 `README.md` 增加 Kimi Code 支持说明（`.kimi-code/` 目录、MCP 原生复用 `.mcp.json`、Superpowers 经 `~/.agents/skills` 消费）

## 6. 验证

- [x] 6.1 在临时项目执行 `openspec init --tools claude,codex,pi,kimi`，验证四客户端产物齐全（含 `.kimi-code/skills/` 5 个 openspec-*）
- [x] 6.2 运行 rule-config 测试套件（`tests/test_rule_config.py` 与生命周期脚本）确认 PRUNE_DIRS 变更无回归
- [x] 6.3 端到端冒烟：对临时项目按 pre-check → rule-config → mcp-configuration 顺序验证 kimi 产物、根目录 `.mcp.json` 被 Kimi 消费（无需第二份配置）
