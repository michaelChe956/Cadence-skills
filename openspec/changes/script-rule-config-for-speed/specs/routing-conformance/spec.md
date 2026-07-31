## MODIFIED Requirements

### Requirement: 路由目标和版本必须通过静态检查
系统 MUST 提供可重复的静态检查，确认 L0 引用的规则文件与 Skill 名称存在、`CLAUDE.md` 和 `AGENTS.md` 的路由版本一致、L1 规范源与生成副本一致，并且 OpenSpec 配置只使用有效 artifact 规则键。系统还 MUST 提供直接驱动 rule-config 脚本执行体的可执行生命周期测试，证明同版本幂等、内容漂移保护、双入口备份屏障、候选 YAML 解析与结构预检和原子发布失败关闭；该测试 SHALL 通过脚本 CLI 断言真实文件系统结果与 JSON 报告字段，不得再以独立参考模型模拟 Skill 行为。

#### Scenario: 入口引用不存在的 Skill
- **WHEN** L0 引用当前项目应已安装但实际不存在的 Superpowers Skill
- **THEN** 静态检查失败并报告入口文件、任务信号和缺失名称

#### Scenario: OpenSpec 包含 rules.apply
- **WHEN** `openspec/config.yaml` 将 `apply` 配置为 artifact 规则键
- **THEN** 静态检查失败并指出 `apply` 是特殊命令而非有效 artifact

#### Scenario: 受管生命周期失败关闭
- **WHEN** 测试夹具模拟 L0/L1 备份失败、不可解析 YAML、目标字段类型冲突、候选结构预检失败或原子发布失败
- **THEN** 脚本执行体 MUST 返回非零状态并保持目标文件运行前后哈希一致
- **AND** 测试报告 MUST 记录场景、退出状态和运行前后 SHA-256
