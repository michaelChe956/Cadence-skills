## ADDED Requirements

### Requirement: 模板与脚本必须同源（skill 自包含）

rule-config 的规则模板与 OpenSpec 配置模板 MUST 从脚本自身所在 skill 目录解析——以 `SKILL_DIR`（`Path(__file__).resolve().parent.parent`，软链经 `resolve()` 解析到真实安装位置）下的 `references/` 为唯一模板源，MUST NOT 使用任何与调用环境相关的固定路径候选（如 `~/.claude/plugins/` 下的 marketplace 目录）或全局文件系统搜索回退。skill 包（`SKILL.md` + `scripts/` + `references/`）MUST 视为自包含整体。

必备模板文件清单固定为：`references/rules/` 下 `agent-routing-kernel.md`、`language.md`、`openspec-superpowers-workflow.md`、`document-storage.md`，以及 `references/openspec/config.yaml`。缺失任一时脚本 MUST 以 `TemplateError` 失败关闭：非零退出、目标项目零写入、报告列出每个缺失文件名与"skill 安装不完整，请重新安装"恢复建议。

模板定位 MUST NOT 依赖 `HOME` 环境变量或客户端安装目录布局；脚本被任何客户端以任意安装根调用时，模板内容 MUST 始终与该调用来源的 skill 包版本一致。

#### Scenario: 模板始终取自调用来源的 skill 目录

- **WHEN** 脚本运行且其 skill 目录的 references 完整
- **THEN** 模板源 MUST 为该 skill 目录的 `references/`
- **AND** 即使其他安装位置（如过期的 marketplace checkout）存在内容不同的模板副本，MUST NOT 被选用

#### Scenario: skill 目录模板不完整即失败关闭

- **WHEN** skill 目录的必备模板文件缺失任一
- **THEN** 脚本 MUST 以 `TemplateError` 非零退出且目标项目零写入
- **AND** 报告 MUST 列出每个缺失文件名与"skill 安装不完整，请重新安装"恢复建议

#### Scenario: 模板定位不依赖 HOME

- **WHEN** `HOME` 环境变量指向空目录（无任何插件或缓存布局）
- **THEN** 脚本 MUST 仍能以 skill 目录模板正常完成全部流程
- **AND** 不得因固定路径候选缺失而失败
