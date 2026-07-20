# no-interrupt 模式与冲突合并技术方案

**版本**：v1.0

**日期**：2026-07-15

**适用范围**：`pre-check`、`rule-config`、`mcp-configuration`、`project-rules-examples`

## 1. 目标

为四个初始化 Skill 增加显式的强制无交互模式，并统一冲突处理方式：

```text
/<skill-name> no-interrupt
/<skill-name> --no-interrupt
```

启用该参数后，Skill 不得调用用户提问工具，不得等待用户确认，也不得通过保守跳过掩盖强制步骤失败。能够自动解决的冲突按确定性策略处理，无法满足强制结果时立即报错终止。

## 2. 统一执行契约

### 2.1 参数识别

- 参数列表包含 `no-interrupt` 或 `--no-interrupt` 时，进入强制无交互模式。
- 参数匹配采用完整 token，不使用模糊包含匹配。
- 未携带参数时完整保留四个 Skill 当前的执行逻辑、交互策略、冲突处理和迁移行为。
- 强制安装、立即失败、结构化合并、禁止迁移等新规则只在 `no-interrupt` 模式中生效。

### 2.2 强制无交互规则

- 禁止调用 `AskUserQuestion`、`request_user_input` 或等价用户提问工具。
- 禁止等待输入、超时后选择默认值或暂停流程等待人工处理。
- 不收集 API Key、Token、密码等私密信息。
- 不绕过操作系统权限、网络授权和执行平台安全限制；缺少必要权限时直接失败。
- 自动变更已有文件前必须保留内容：优先结构化合并，无法可靠合并时先创建备份。
- 失败报告必须包含失败步骤、原因、已完成步骤和恢复建议，不得宣称初始化成功。

### 2.3 向后兼容

- `/pre-check`、`/rule-config`、`/mcp-configuration`、`/project-rules-examples` 不带参数时，行为必须与修改前一致。
- 普通模式继续使用原有的条件询问、超时默认值、保守跳过、文件不覆盖和历史产物迁移策略。
- `no-interrupt` 分支必须独立描述，不得把严格策略写成所有模式共享的默认行为。
- 后续新增严格策略时，除非用户明确要求改变默认行为，否则只能加入 `no-interrupt` 分支。

## 3. pre-check

### 3.1 no-interrupt 模式下的强制项

除 Playwright 外，下列六项必须全部完成安装和验证：

1. npx
2. uvx
3. ast-grep
4. codegraph
5. OpenSpec
6. Superpowers

在 `no-interrupt` 模式下，任一强制项安装、同步或验证失败时，立即终止 `/pre-check`，不执行剩余步骤，也不得把失败降级为警告后继续。普通模式继续使用原有失败处理方式。

### 3.2 Playwright

- Playwright 继续保持可选。
- 仅用户明确要求浏览器自动化能力时安装。
- 用户未要求时跳过 Playwright 不属于失败。

### 3.3 no-interrupt 模式下的 Superpowers 在线与离线安装

- 优先识别现有的 `~/.agents/superpowers/skills`。
- 现有目录无效时尝试在线安装或更新。
- 在线安装失败后，仅检查固定离线目录 `~/.agents/superpowers/skills`。
- 固定离线目录不存在或校验失败时立即报错，不询问其他来源路径，不继续后续流程。

### 3.4 no-interrupt 模式下的同名冲突

Superpowers 来源目录或软链目标存在同名非软链内容时：

1. 将冲突内容重命名为带时间戳的备份。
2. 创建 Skill 要求的目录或软链。
3. 验证新目录或软链正确可用。
4. 任一步失败立即终止，禁止删除原内容或跳过冲突项。

## 4. rule-config

### 4.1 no-interrupt 模式下的权威来源

`rule-config` 提供的框架规则、必需章节、规则路径和强制约束是权威内容。当前项目已有内容作为补充，不得删除项目独有的技术栈、命令、业务规则和说明。

### 4.2 no-interrupt 模式下的 Markdown 合并

- 文件不存在：创建标准文件。
- 文件存在：按 Markdown 标题结构合并。
- 同名章节以 `rule-config` 内容为主体，项目独有条目去重后追加到对应章节的“项目补充”。
- 模板没有的项目章节完整保留。
- `CLAUDE.md` 和 `AGENTS.md` 中的强制规则摘要及引用路径以 `rule-config` 为准，其他项目内容继续保留。
- 无法可靠解析时，先备份原文件，再写入标准结构，并将原内容放入“原项目补充”章节。

### 4.3 no-interrupt 模式下禁止历史产物迁移

- 不移动 `.claude/prds`、`.claude/docs`、`.claude/plans` 等历史产物目录。
- 不把历史目录内容合并到 `cadence/`。
- 不删除历史目录。
- 只检测并在执行报告中列出仍存在的历史目录。
- 普通模式继续执行 `rule-config` 当前定义的历史产物迁移逻辑。

## 5. mcp-configuration

### 5.1 no-interrupt 模式下的权威来源

`mcp-configuration` 定义的必需 MCP Server、传输方式、命令、URL 和必要参数是权威配置。当前项目中的额外 Server 和扩展字段作为补充保留。

### 5.2 no-interrupt 模式下的 JSON 与 TOML 合并

- `.mcp.json` 按 `mcpServers` 的 Server 名称进行集合合并。
- `.codex/config.toml` 按 `[mcp_servers.<name>]` 配置块进行集合合并。
- 当前项目额外的 MCP Server 全部保留。
- 同名 Server 的 `type`、`command`、`url` 和必要参数以 Skill 为准。
- 项目独有的环境变量、Header 和扩展字段继续保留。
- 参数数组以 Skill 必需参数为前缀，再追加不重复且不改变必需语义的项目参数。
- Codex 仅同步支持的 stdio MCP，不同步 HTTP MCP。

### 5.3 no-interrupt 模式下的密钥占位符

- `your_zhipu_api_key`、`your_minimax_api_key` 等占位符不是权威真实值。
- 当前项目已有非占位值时予以保留，不用占位符覆盖。
- 执行报告不得输出真实密钥内容。

### 5.4 no-interrupt 模式下的无法解析与 gitignore

- JSON 或 TOML 无法解析时先备份原文件，再生成标准配置。
- 能安全识别的项目配置作为补充恢复；无法保证内容安全时立即报错。
- `.gitignore` 采用集合合并，Skill 要求的忽略项必须生效，重复项去重。

## 6. project-rules-examples

### 6.1 no-interrupt 模式下的权威来源

`project-rules-examples` 提供的模板结构、必需章节、章节顺序、AI 执行规则和强制约束是权威内容。当前项目已有真实事实和个性化规范作为补充保留。

### 6.2 no-interrupt 模式下的模板合并

- 不再因为目标模板存在而直接跳过。
- 同名章节以标准模板为主体，当前项目独有条目去重后追加。
- 项目中已经填写的技术栈、调用链、契约、异常体系、日志规范和测试要求必须保留。
- 当前项目真实内容可替换相应模板占位符。
- 模板没有的项目章节完整保留在“项目补充”区域。
- 无法解析时先备份原文件，生成标准模板，再将原内容附加到“原项目补充”章节。
- `CLAUDE.md` 和 `AGENTS.md` 中的项目规则引用路径以 Skill 定义为准，其他内容保留。

## 7. 验证标准

- 四个 Skill 均说明 `no-interrupt` 和 `--no-interrupt` 的调用方式。
- 四个 Skill 均明确说明不带参数时保持修改前行为。
- 强制无交互分支不存在询问、等待、超时选择或保守跳过。
- `pre-check no-interrupt` 的六个强制项任一失败都会立即终止，普通模式失败处理不变。
- `rule-config no-interrupt` 不执行历史产物迁移，普通模式迁移逻辑保持不变。
- 三个配置类 Skill 均定义权威内容、项目补充、去重、备份和失败策略。
- API Key 占位符不会覆盖已有非占位值。
- 所有 Markdown 修改符合仓库格式规范。

## 8. 非目标

- 不为 Skill 开发独立命令行参数解析程序。
- 不绕过宿主平台权限审批或网络限制。
- 不安装用户未要求的 Playwright。
- 不迁移、删除或清理项目历史文档目录。

## 9. README 使用说明同步

为避免项目入口文档与 Skill 实际能力不一致，同步更新以下三个 README：

- 根目录 `README.md`
- `readmes/commands/README.md`
- `readmes/skills/README.md`

文档必须统一说明：

- `no-interrupt` 和 `--no-interrupt` 是等价的完整 token 参数。
- 不携带参数时保持四个 Skill 原有逻辑。
- 携带参数时禁止用户交互，按各 Skill 的严格策略执行。
- 无法自动完成严格结果时直接报错终止，不等待用户确认。
- 新项目初始化示例同时展示普通模式和可选的强制无交互模式。

根 README 提供完整行为对照表；命令指南和 Skills 指南提供简化调用示例并链接回根 README 的初始化章节，避免重复维护全部规则细节。
