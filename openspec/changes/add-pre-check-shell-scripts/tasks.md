# Tasks: add-pre-check-shell-scripts

## 1. 镜像源配置文件

- [x] 1.1 新建 `cadence-init/skills/pre-check/scripts/mirrors/default.sh`，定义 `CADENCE_NPM_REGISTRY=https://registry.npmjs.org`、`CADENCE_PY_INDEX=https://pypi.org/simple`、`CADENCE_SUPERPOWERS_GIT=https://github.com/obra/superpowers`（映射 Requirement: default 与 cn 两个预置镜像、镜像配置经环境变量注入）
- [x] 1.2 新建 `cadence-init/skills/pre-check/scripts/mirrors/cn.sh`，定义 `CADENCE_NPM_REGISTRY=https://registry.npmmirror.com`、`CADENCE_PY_INDEX=https://pypi.tuna.tsinghua.edu.cn/simple`、`CADENCE_SUPERPOWERS_GIT=https://gitee.com/michaelChe-World/superpowers.git`（映射 Requirement: default 与 cn 两个预置镜像）

## 2. 主脚本核心框架

- [x] 2.1 新建 `cadence-init/skills/pre-check/scripts/pre-check.sh`，使用 `#!/usr/bin/env bash` 与 POSIX 兼容语法，实现参数解析（`run`/`check` 子命令、`--mirror <name>`、`--no-interrupt`、`--upgrade`）（映射 Requirement: run 与 check 子命令语义、mac 与 Linux 兼容）
- [x] 2.2 实现 mirror 加载逻辑：默认 `default.sh`，`--mirror <name>` 加载对应文件，未知 mirror 报错并非零退出（映射 Requirement: --mirror 切换与默认值）
- [x] 2.3 实现命令级源注入：npm 用 `--registry=$CADENCE_NPM_REGISTRY`，uv/uvx 用索引环境变量 `$CADENCE_PY_INDEX`，全程不写用户全局 npm/uv/git 配置（映射 Requirement: 镜像配置经环境变量注入）

## 3. 六工具探测、安装与复验

- [x] 3.1 实现六个工具（npx/uvx/ast-grep/codegraph/openspec/pi-mcp-adapter）的就绪探测函数，各用其版本命令探测；pi-mcp-adapter 按 `command -v pi` 条件触发，pi 不存在时标记 conditional-skip（映射 Requirement: 单一主脚本承接六工具检查与安装）
- [x] 3.2 实现缺失工具的安装逻辑（`run` 模式），`check` 模式仅探测不安装（映射 Requirement: run 与 check 子命令语义）
- [x] 3.3 实现已就绪工具秒跳过：探测成功即标记 ready，不查远端、不安装；安装后强制复验，复验失败标记 failed（映射 Requirement: 已就绪工具秒跳过）

## 4. 升级能力（opt-in）

- [x] 4.1 实现 `--upgrade` 逻辑：仅携带该参数时查询当前源 latest（`npm view <pkg> version --registry=...` / uv 索引），比对本地版本，落后则升级 npm 系工具与 uv 本体（映射 Requirement: 升级 opt-in 且以当前源为准、镜像即权威的版本口径）
- [x] 4.2 升级范围限定为 ast-grep/codegraph/openspec（npm 系）与 uv 本体；pi-mcp-adapter、uvx 临时包与 playwright-cli 不升级；升级记录 from/to/source 供报告使用（映射 Requirement: 升级 opt-in 且以当前源为准）

## 5. JSON 报告与人类摘要

- [x] 5.1 实现 stdout 输出单份 JSON：`overall`（success/partial/failed）、`steps[]`（name/status/action/version/error）、`next_actions`、`hints.superpowers_git`；status 用固定枚举 ready/installed/upgraded/skipped/failed（映射 Requirement: JSON 报告结构权威且走 stdout）
- [x] 5.2 将各安装/探测命令输出重定向，确保 stdout 仅含一份 JSON；stderr 输出彩色人类摘要（映射 Requirement: JSON 报告结构权威且走 stdout）
- [x] 5.3 实现 `next_actions` 固定列出 Superpowers 软链、OpenSpec 三客户端、Playwright（可选）、API Key 占位提醒（映射 Requirement: JSON 报告结构权威且走 stdout、脚本报告驱动 SKILL.md 后续动作）

## 6. 失败语义

- [x] 6.1 实现 `--no-interrupt` 失败关闭：任一基础工具失败即非零退出且 `overall=failed`；普通模式失败标记 partial/failed 并给出恢复建议（映射 Requirement: run 与 check 子命令语义、脚本报告驱动 SKILL.md 后续动作）

## 7. 脚本验证（mac 与 Linux）

- [x] 7.1 在 Linux 执行 `check`（全新/部分已装/全已装三种环境）验证探测与秒跳过（映射 Requirement: 已就绪工具秒跳过、mac 与 Linux 兼容）
- [x] 7.2 在 Linux 执行 `run`、`run --mirror cn`、`run --upgrade`、`run --mirror cn --upgrade`，验证安装、镜像源、升级与报告来源记录（映射 Requirement: 升级 opt-in 且以当前源为准、镜像即权威的版本口径）
- [x] 7.3 在 mac 执行关键路径验证平台一致性；验证 stdout JSON 可被 `python3 -m json.tool` 或 `jq` 解析（映射 Requirement: mac 与 Linux 兼容、JSON 报告结构权威且走 stdout）

## 8. SKILL.md 改写

- [x] 8.1 改写 `cadence-init/skills/pre-check/SKILL.md`：六工具的安装/验证正文替换为脚本调用约定（命令、参数、JSON 报告读取），保留 Superpowers 软链、OpenSpec 三客户端、Playwright、API Key 四项处理（映射 Requirement: 单一主脚本承接六工具检查与安装、六工具检查由脚本执行）
- [x] 8.2 Superpowers 步骤改为读取 `$CADENCE_SUPERPOWERS_GIT`，移除正文硬编码 GitHub 地址，说明 cn 模式直接用国内镜像、不配 git 代理（映射 Requirement: Superpowers Git 地址镜像化）
- [x] 8.3 更新快速参考表、no-interrupt 完成策略表与增量运行说明，与脚本行为一致（映射 Requirement: 六工具检查由脚本执行、脚本报告驱动 SKILL.md 后续动作）

## 9. 一致性核验

- [x] 9.1 逐条对照三个 spec 的验收场景，核验脚本、镜像文件与 SKILL.md 改后全文无矛盾表述（映射全部 Requirement）
- [x] 9.2 运行 `openspec validate add-pre-check-shell-scripts` 确认 change 有效（映射全部 Requirement）
