## ADDED Requirements

### Requirement: verify 子命令必须提供只读加载自检

`rule-config --verify` MUST 以只读方式检查业务项目五项：①AGENTS.md/CLAUDE.md 的 L0 区块版本（v1/v2/v3/v4 及是否最新）；②受管规则文件与模板哈希比对；③权限投影区块与元数据重算结果比对；④codex-rules-inline 区块与源重算结果比对；⑤三层软链解析是否指向 Cadence 源。输出 MUST 结构化且可选 JSON；全部健康时退出码 MUST 为 0，存在漂移或过时项时 MUST 为 1。第 ③④ 项对从未生成过投影区块的项目 MUST 报"未生成"（提示运行 apply）而不报漂移。`--verify` MUST NOT 修改任何文件。

#### Scenario: 过时版本被报告

- **WHEN** 业务项目 L0 为 v3 且框架当前版本为 v4，运行 `--verify`
- **THEN** 报告"L0 版本过时（当前 v3，最新 v4）"且退出码为 1

#### Scenario: 全绿可编程判定

- **WHEN** 各项检查全部通过
- **THEN** 退出码为 0，JSON 输出可被 CI 直接消费为断言

#### Scenario: 投影漂移被定位

- **WHEN** apply 后修改任一规则源文件再运行 `--verify`
- **THEN** 对应投影项报告漂移且退出码为 1
