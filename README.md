# Cadence

## 项目简介

Cadence 是面向 Claude Code、pi、Codex 和 Kimi Code 的 Agent Skills 协作系统。它把需求澄清、设计、计划、实现、测试、评审和调试等工作组织为可复用的 Skills，并为 Java 与 Vue/React 存量项目提供 Schema 4.0 KnowledgeBase 能力。

当前仓库内的 `cadence-init` 插件版本为 `0.0.4`。Cadence 的安装、更新和卸载由仓库根目录的 `install.sh` 负责；Skills 以 Git 仓库为源，通过三层 skill 级软链供不同 Agent 消费，不依赖插件市场注册。

## 如何工作

Cadence Skills 会根据任务意图自动触发，也可以用裸 Skill 名手动调用。典型工作流如下：

1. 使用 `/pre-check` 检查基础工具和环境。
2. 使用 `/project-analysis` 了解项目结构与技术栈。
3. 使用 `/rule-config` 配置项目规则、`cadence/` 产物目录和 OpenSpec 协作入口。
4. 使用 `/mcp-configuration` 配置项目 MCP，按需使用 `/project-rules-examples` 补齐个性化规则模板。
5. 为存量项目填写 Schema 4.0 输入后，使用 `/knowledge-base-bootstrap` 初始化 KnowledgeBase。
6. 在需求、设计、计划、编码、测试、评审或调试前，使用 `/knowledge-base-context` 获取最小任务上下文。
7. 项目事实发生变化时，准备完整变更包并使用 `/knowledge-base-update` 增量更新知识库。

KnowledgeBase Skills 只在目标项目授权范围内读取证据；它们不会替代业务代码、数据库迁移、部署或发布流程。

## 安装前提

- 完整支持 Linux；macOS 需先安装 `bash>=4` 与 GNU coreutils（如执行 `brew install bash coreutils`），否则安装会失败；Windows 仅支持 WSL 或 Git Bash，不支持 Windows 原生环境。
- 需要 `bash`、`git`、`curl` 和可用的网络连接。
- 安装脚本只使用固定的三个 Git 镜像并按顺序轮换：`ghfast.top`、`gh-proxy.com`、`mirror.ghproxy.com`；全部失败时直接报错，不直连 GitHub，也没有离线分支。
- `~/.agents/Cadence-skills` 是 Cadence 的用户安装仓库。若该路径已有 Git 仓库，安装会更新它；若是非 Git 目录，脚本不会自动删除，须由用户先处理。
- 安装脚本只管理它创建并能精确识别的 Cadence skill 软链，不触碰用户普通文件或非受管软链。

## 安装 Cadence skills

### 快速安装

在网络可用的环境中，下载脚本后执行：

```bash
curl -fsSL 'https://ghfast.top/https://raw.githubusercontent.com/michaelChe956/Cadence-skills/main/install.sh' -o /tmp/cadence-install.sh
bash /tmp/cadence-install.sh
rm -f /tmp/cadence-install.sh
```

如果仓库已经位于目标路径，也可以直接运行：

```bash
bash ~/.agents/Cadence-skills/install.sh --help
bash ~/.agents/Cadence-skills/install.sh
```

安装过程会将仓库克隆或更新到 `~/.agents/Cadence-skills`，扫描 `cadence-init/skills/*/SKILL.md`，然后建立三层 skill 级软链：共享层 `~/.agents/skills/`，Claude Code 层 `~/.claude/skills/`，以及 Codex 兼容层 `~/.codex/skills/skills/`。重复运行会更新 Git 工作树并重新同步链接。

#### 安全安装流程（必须先预览）

安装前先生成动作计划：

首次安装也可以直接使用下载到 `/tmp` 的脚本预览：

```bash
bash /tmp/cadence-install.sh --dry-run
```

如果仓库已经安装，则使用仓库内脚本预览：

```bash
bash ~/.agents/Cadence-skills/install.sh --dry-run
```

`--dry-run` 只计算并打印将要 clone/update、创建、替换、清理、保留或告警跳过的动作，不联网、不落盘，也不会创建目录、写文件、替换或删除链接。请人工核对动作计划，重点确认三层路径均指向 Cadence 源、第三方链和普通目录/文件均为保留或告警跳过，确认无误后再执行真实安装：

```bash
bash ~/.agents/Cadence-skills/install.sh
```

人工核对不能替代真实安装；真实安装必须在核对通过后单独执行。更新、迁移和卸载同样沿用上述安全边界，`--dry-run` 不是旧 marketplace 预览。

### 验证安装

检查三个消费目录及一个实际 Skill：

```bash
ls ~/.claude/skills/
ls ~/.agents/skills/
ls ~/.codex/skills/skills/
test -f ~/.claude/skills/pre-check/SKILL.md
```

也可以查看脚本帮助，确认当前支持的接口：

```bash
bash ~/.agents/Cadence-skills/install.sh --help
```

四类 Agent 的消费路径如下。pi 和 Kimi Code 消费共享层，Claude Code 消费个人层，Codex 可见共享层并提供兼容投影。`~/.pi/agent/skills` 属于 Superpowers 或 pi 自身的目录，不是本安装脚本创建的 Cadence 层。

| Agent | 消费路径 | 验证命令 |
| --- | --- | --- |
| Claude Code | `~/.claude/skills/` | `ls ~/.claude/skills/` |
| pi | `~/.agents/skills/` | `ls ~/.agents/skills/` |
| Codex | `~/.agents/skills/`；兼容层 `~/.codex/skills/skills/` | `ls ~/.agents/skills/`、`ls ~/.codex/skills/skills/` |
| Kimi Code | `~/.agents/skills/` | `ls ~/.agents/skills/` |

### 更新

更新 Cadence skills 只需重新运行仓库中的安装脚本：

```bash
bash ~/.agents/Cadence-skills/install.sh
```

脚本会对已有 Git 仓库执行远端更新，使用跟踪分支、`fetch --all` 和快进更新，并在必要时轮换三个镜像；之后重新同步受管链接。若远端历史无法快进，脚本会报错并给出恢复建议，不会强制覆盖本地提交。

### 卸载

默认卸载仅移除安装脚本创建且仍指向 Cadence 源路径的受管 skill 软链，保留 `~/.agents/Cadence-skills` 仓库：

```bash
bash ~/.agents/Cadence-skills/install.sh --uninstall
```

如需同时删除安装仓库，必须显式使用：

```bash
bash ~/.agents/Cadence-skills/install.sh --uninstall --delete-repo
```

卸载不会删除用户普通文件、非受管软链或其他 Agent 的普通 Skills。仓库删除仅限用户明确指定的 `~/.agents/Cadence-skills` 目标目录。

### 从旧安装迁移

建议先完成一次新安装，再清理旧机制留下的残留。`install.sh` 只检测并提示，不自动改动以下位置：

- 旧目录：`~/.claude/plugins/marketplaces/cadence-skills-local`
- 旧登记文件：`~/.claude/plugins/known_marketplaces.json` 中的 `cadence-skills-local` 键

确认不再需要旧目录后，可手动删除：

```bash
rm -rf -- ~/.claude/plugins/marketplaces/cadence-skills-local
```

处理 JSON 文件前请先备份，并使用 `jq` 或其他 JSON 工具人工复核后删除 `cadence-skills-local` 键。不要把旧路径当作当前安装目录，也不要让迁移清理代替新脚本安装。

## 项目初始化（cadence-init）

`cadence-init` 是仓库中包含 14 个 Skills 的插件目录。安装后，在目标项目根目录按需执行以下流程；这些调用均使用实际 Skill 名，不使用插件命名空间。

### 初始化步骤

1. `/pre-check`：检查并补齐 npx、uvx、ast-grep、codegraph、OpenSpec 及相关工具。
2. `/project-analysis`：分析项目结构、技术栈和依赖。
3. `/rule-config`：配置 `.claude/rules/`、入口文件、`cadence/` 和 OpenSpec。
4. `/mcp-configuration`：生成或合并项目 `.mcp.json`，并交接其他客户端配置。
5. `/project-rules-examples`：按需创建 `cadence/project-rules/` 模板。
6. `/knowledge-base-bootstrap`：在已填写 Schema 4.0 输入后初始化存量项目知识库。

`/pre-check` 的运行时工具安装、Superpowers 目录及其同步边界，和 Cadence 的 Git 仓库与三层 skill 链接是两套独立机制，不要混称。

### 强制无交互模式（no-interrupt）

以下 Skills 支持 `no-interrupt` 或等价的 `--no-interrupt` 参数：

```text
/pre-check no-interrupt
/rule-config no-interrupt
/mcp-configuration no-interrupt
/project-rules-examples no-interrupt
```

需要 Playwright 时应明确提出启用要求。`/project-analysis` 不支持该参数，仍按其正常流程执行。

## 14 个 Skills

### KnowledgeBase skills

以下 7 个 Skills 面向 Schema 4.0 KnowledgeBase：

| Skill | 职责 |
| --- | --- |
| `knowledge-base-api` | 分析对外能力、工程内对内能力及 API/集成调用链 |
| `knowledge-base-base-info` | 建立工程、服务、数据模型、配置和开发方式基础信息 |
| `knowledge-base-bootstrap` | 校验输入并初始化 Schema 4.0 KnowledgeBase |
| `knowledge-base-context` | 按任务画像提供最小 KnowledgeBase 上下文 |
| `knowledge-base-overview` | 生成知识库入口、导航、术语和项目使用规则 |
| `knowledge-base-pages` | 分析 Vue/React 页面、路由、权限、状态和 API 关系 |
| `knowledge-base-update` | 依据完整变更包增量更新已有 KnowledgeBase |

常用调用：`/knowledge-base-bootstrap`、`/knowledge-base-context`、`/knowledge-base-update`。

### 项目初始化与规则 skills

| Skill | 职责 |
| --- | --- |
| `mcp-configuration` | 配置项目 `.mcp.json` 及客户端交接 |
| `pre-check` | 检查开发环境、工具和初始化前置条件 |
| `project-analysis` | 分析项目结构、技术栈、依赖和 Git 信息 |
| `project-rules-examples` | 创建项目个性化规则模板 |
| `rule-config` | 配置项目规则、目录和 OpenSpec 协作入口 |

常用调用：`/pre-check`、`/project-analysis`、`/rule-config`。

### Skill 创建与兼容 skills

| Skill | 职责 |
| --- | --- |
| `legacy-bootstrap` | 使用兼容流程为 legacy 项目建立 Cadence 项目认知 |
| `skill-creator` | 创建、校验、打包和优化 Skill |

常用调用：`/skill-creator`。`legacy-bootstrap` 默认不自动触发，需按实际需要使用。

插件元数据版本以 `cadence-init/.claude-plugin/plugin.json` 的 `0.0.4` 为准；Skill 数量以仓库中的 14 个 `SKILL.md` 为准。

## Commands 库

Cadence 当前不提供独立 Command 文件。所有能力均由 Skills 提供，直接使用裸名调用，例如 `/pre-check`、`/rule-config` 和 `/skill-creator`。

详细说明见 [Commands 使用指南](readmes/commands/README.md) 和 [Skills 使用指南](readmes/skills/README.md)。

## MCP 配置

仓库根目录 `.mcp.json` 的静态 `mcpServers` 清单包含以下 8 个 server：

1. `time`
2. `context7`
3. `sequential-thinking`
4. `zai-mcp-server`
5. `web-search-prime`
6. `web-reader`
7. `zread`
8. `MiniMax`

这是静态配置事实，不表示安装脚本会额外注册 server。`/mcp-configuration` 负责目标项目的 MCP 配置与客户端交接；真实 API Key 应由用户在本地按安全要求替换，不要提交密钥。

Cadence 产物使用 `cadence/designs/` 和 `cadence/plans/`。`docs/superpowers/specs/`、`docs/superpowers/plans/` 仅作为历史或对照路径，不是当前 Cadence 产物目录。

## 最佳实践

- 安装后先运行验证命令，再启动 Agent 客户端。
- 让 `/pre-check`、`/project-analysis`、`/rule-config` 按顺序完成项目基础配置。
- 先填写并校验 Schema 4.0 输入，再运行 `/knowledge-base-bootstrap`。
- 已完成知识库的任务优先使用 `/knowledge-base-context`；事实变化使用 `/knowledge-base-update`，不要用重新初始化替代增量更新。
- 更新 Cadence 时重新运行 `install.sh`，不要手工复制 Skill 目录。
- 卸载前核对链接目标；默认卸载保留仓库，删除仓库必须显式传递 `--delete-repo`。
- 不把密码、Token、AccessKey 或完整连接串写入项目文档、变更包或 MCP 配置提交。

## 技术亮点

- **三层 skill 级软链**：共享层以 Git 仓库为源，Claude Code 和 Codex 兼容层分别投影，重复安装可幂等重同步。
- **镜像轮换与快进更新**：固定镜像顺序、无直连兜底，更新拒绝强制覆盖本地历史。
- **用户文件保护**：仅识别精确的受管链接；冲突、非 Git 目录和旧残留均提示用户处理。
- **Schema 4.0 KnowledgeBase**：同时保留代码、数据模型、配置快照和变更包证据，按任务画像渐进检索。
- **四类 Agent 消费**：Claude Code、pi、Codex、Kimi Code 共享同一套仓库源和 Skill 名称。

## Skill Creator

仓库提供 `skill-creator` Skill，用于创建、校验、打包和优化可复用 Skill。直接调用：

```text
/skill-creator
```

使用时请说明 Skill 的名称、用途、触发场景、输入输出和目标目录。详细指南见 [skill-creator Skill 文档](readmes/skills/skill-creator.md)；定义文件见 `cadence-init/skills/skill-creator/SKILL.md`。

## 贡献

1. Fork 本仓库并创建功能分支。
2. 使用 `/skill-creator` 创建或维护 Skill，确保目录名、front matter 的 `name` 和 `SKILL.md` 一致。
3. 更新用户文档时同步检查 14 个 Skill 名称、四类 Agent 路径和安装脚本契约。
4. 运行 ShellCheck、安装/更新/卸载验证和文档定向断言后提交 Pull Request。

## 许可证

MIT License，详见 [LICENSE](LICENSE)。

## 支持

- 问题反馈：https://github.com/michaelChe956/Cadence-skills/issues
- 项目主页：https://github.com/michaelChe956/Cadence-skills
- 文档入口：[Skills 使用指南](readmes/skills/README.md)
