## ADDED Requirements

### Requirement: L0 区块必须包含可见文本版本行

自 v4 起，L0 受管区块首行 MUST 包含可见文本版本标识（如 `Cadence L0 路由内核 v4`），与既有 HTML 注释标记并存：注释标记供脚本解析与受管识别，可见文本供 agent 在上下文中自报版本。既有确定性升级机制 MUST 将 v3 及更早版本升级为 v4；历史版本规范 MUST 归档进 `l0-history/`。

动机：Claude Code 注入上下文时剥离 HTML 注释（2026-09-02 实测），纯注释标记对 Claude Code 不可见，回执无法自报版本。

#### Scenario: v3 确定性升级为 v4

- **WHEN** 入口文件包含成对 v3 标记且完整区块内容与 v3 规范源一致，而框架当前版本为 v4
- **THEN** 系统 MUST 不经用户决策将区块升级为 v4 规范源，普通模式与 no-interrupt 模式同动作

#### Scenario: Claude Code 回执可自报版本

- **WHEN** Claude Code 会话被要求复述当前生效的 L0 版本
- **THEN** 其可从上下文中的可见文本版本行读出版本号 v4，不依赖 HTML 注释标记
