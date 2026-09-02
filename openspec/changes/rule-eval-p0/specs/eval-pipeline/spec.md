## Purpose

两阶段测试流水线：对 4 个 skill 的"安装效果"做确定性验证——装得对不对（阶段一产物断言）与装完后规则是否真被遵守（阶段二行为探针）。

## ADDED Requirements

### Requirement: 流水线必须在 fixture 变体上依序执行四 command 并断言安装产物

系统 MUST 提供 fixture 项目生成器（至少三变体：全新空项目、已初始化含 v3 L0、已配 .mcp.json+codegraph），在每变体上以 headless 方式依序直接调用 `/pre-check → /rule-config → /mcp-configuration → /project-rules-examples`，并对每步做确定性产物断言（pre-check 零文件改动；rule-config 的 `.claude/rules/` 清单、L0 v4 区块、settings.json permission-gate 区块、AGENTS.md codex-rules-inline 区块、`--verify` 退出码 0；mcp-configuration 的 `.mcp.json` 合法性与 `.codex/config.toml` 一致性、`.gitignore` 精确行；project-rules-examples 就位且不写 `.claude/rules/`）。

#### Scenario: 全新 coding fixture 首次安装全绿

- **WHEN** 全新空 fixture 依序跑完四 command 并执行安装断言
- **THEN** 全部断言通过且 `--verify` 退出码为 0

#### Scenario: v3 项目升级断言

- **WHEN** 已初始化（v3 L0）fixture 重跑 /rule-config
- **THEN** 断言 v3→v4 升级、备份进 `cadence/legacy/`、区块外内容逐字不变

### Requirement: 安装流水线必须通过幂等双跑检查

同一 fixture 上连续执行两遍安装流水线，第二遍结束后 workspace 与第一遍结束状态 MUST byte-identical；若存在"gate 从无到有"的一次性过渡写入，MUST 在第三遍达到稳态幂等并以显式测试锁定该过渡语义。

#### Scenario: 重复安装零追加

- **WHEN** 安装流水线在同一 fixture 连跑两遍（或过渡场景跑三遍）
- **THEN** 末遍相对前遍的 workspace diff 为空（byte-identical）

### Requirement: 行为探针集必须覆盖四类度量且判分确定性

系统 MUST 在装好的 fixture 上执行行为探针任务集（初始 8 个：检索优先级、文档 MCP、时序合规、中文输出、产物目录、时间 MCP、图片 MCP、安装幂等），每个探针的判分 MUST 为确定性（轨迹事件匹配 + 产物检查 + 时间序检查），MUST NOT 依赖 LLM 评审作为主判分。

#### Scenario: 检索探针断言工具优先级

- **WHEN** 探针 P1"梳理订单模块从入口到落库的调用链"在已安装 fixture 上执行
- **THEN** 断言轨迹含 codegraph/ast-grep 调用且无大范围裸 grep

#### Scenario: 时序探针在门禁上线前预期为红

- **WHEN** 探针 P3"给用户表加最后登录时间字段"在 p1 阶段执行
- **THEN** 其结果预期为不通过（无时序门禁），并在切片 2 交付后转为通过——该探针作为版本对比的常设标尺

### Requirement: fixture 与探针必须防泄漏与过拟合

fixture 三变体 MUST 轮换使用，探针题库 MUST 支持定期更换；fixture MUST 与 Cadence 仓库自身隔离（临时目录生成），防止模型凭仓库记忆通过测试。

#### Scenario: 隔离生成

- **WHEN** 流水线启动
- **THEN** fixture 在临时目录全新生成，不含 Cadence 仓库路径信息
