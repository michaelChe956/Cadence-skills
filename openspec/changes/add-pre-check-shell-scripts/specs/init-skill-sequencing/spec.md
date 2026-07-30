# init-skill-sequencing Delta Specification

## ADDED Requirements

### Requirement: 六工具检查由脚本执行

pre-check 对 npx、uvx、ast-grep、codegraph、openspec、pi-mcp-adapter 六个基础工具的就绪探测、缺失安装与安装后复验 MUST 由 `scripts/pre-check.sh` 执行；SKILL.md MUST 调用脚本并读取其 JSON 报告，MUST NOT 在正文中逐条罗列六工具的安装与验证命令。OpenSpec 三客户端指令产物的检测与补齐 MUST 仍由 SKILL.md 依据本 spec 既有 Requirements 执行，脚本 MUST NOT 接管。

#### Scenario: SKILL.md 调用脚本处理六工具

- **WHEN** 执行 `/pre-check`
- **THEN** SKILL.md 调用 `scripts/pre-check.sh run` 完成六工具检查与安装，读取 JSON 报告判定六工具状态，正文不含六工具的逐条安装命令

#### Scenario: OpenSpec 三客户端仍由 SKILL.md 处理

- **WHEN** 脚本执行完成后 SKILL.md 处理 OpenSpec 检查
- **THEN** SKILL.md 按 claude/codex/pi 客户端产物存在性检测并补齐，脚本不执行 `openspec init`/`openspec update` 的客户端产物判断

### Requirement: 脚本报告驱动 SKILL.md 后续动作

脚本 JSON 报告的 `overall` 与 `steps[].status` MUST 作为 SKILL.md 判定六工具门槛的权威依据；`next_actions` MUST 提示 SKILL.md 继续处理 Superpowers 软链、OpenSpec 三客户端产物、Playwright（可选）与 API Key 占位提醒。脚本以非零退出码终止或 `overall` 为 failed 时，no-interrupt 模式 MUST 立即终止 `/pre-check`，普通模式 MUST 报告失败，均 MUST NOT 降级为警告。

#### Scenario: 依据报告判定门槛

- **WHEN** 脚本返回 `overall` 为 success 或 partial
- **THEN** SKILL.md 依据各 `steps[].status` 判定六工具门槛是否通过，并据 `next_actions` 继续处理剩余项

#### Scenario: 脚本失败触发失败关闭

- **WHEN** 脚本以非零退出码终止或报告 `overall` 为 failed
- **THEN** no-interrupt 模式立即终止 `/pre-check` 并报告失败，普通模式报告失败，不宣称初始化成功
