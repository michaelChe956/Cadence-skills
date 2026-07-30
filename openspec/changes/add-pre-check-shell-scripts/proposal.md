# Proposal: add-pre-check-shell-scripts

## Why

`pre-check` 当前把 npx/uvx/ast-grep/codegraph/openspec/pi-mcp-adapter 六个工具的安装与验证逻辑全部以正文形式写在 SKILL.md 中，由模型逐条读懂、逐条执行 bash、逐条判断成败。这带来三个实际问题：

1. **模型思考压力大**：每次执行 `/pre-check` 都要重新推理约 20 条安装/验证命令与大量增量/冲突分支，token 消耗高且易出错。
2. **大陆环境无开箱方案**：npm/pypi/GitHub 默认源在大陆访问不稳定，现有逻辑不含镜像切换能力，用户需手动配代理或改源。
3. **重复执行慢**：老项目重跑 `/pre-check` 时，模型仍需逐个判断"是否已装"，缺乏毫秒级的本地版本探测与秒跳过机制。

本 change 来自已经用户确认的 brainstorming 结论（方案 B2：一键脚本 + 模型只读 JSON 报告；镜像源可切换；升级 opt-in）。

## What Changes

- 在 `pre-check` skill 下新增 `scripts/` 目录，包含一个主脚本 `pre-check.sh`（mac/Linux 通用 bash）与镜像配置目录 `mirrors/`（`default.sh` 通用源、`cn.sh` 大陆镜像源）。六个工具的检查/安装/验证逻辑移交脚本实现。
- 脚本提供 `run` 与 `check` 两个子命令，支持 `--mirror <name>` 与 `--no-interrupt` 参数；`run` 端到端完成六个工具的就绪探测、缺失安装与安装后复验；`check` 仅探测不安装。脚本对 stdout 输出结构化 JSON 报告，对 stderr 输出人类可读彩色摘要。
- 脚本默认对"已就绪"工具执行毫秒级版本探测后秒跳过，不查远端、不重装；新增 `--upgrade` 开关，仅在显式携带时查询 latest 并升级需要升级的工具。升级版本以当前源为准：`--mirror cn` 以 npmmirror/清华镜像 latest 为准，通用源以 npmjs/pypi latest 为准（镜像即权威，不与另一源比对）。
- 升级范围限定为 npm 系工具（ast-grep/codegraph/openspec）与 uv 本体；pi-mcp-adapter、uvx 临时包与 playwright-cli 不纳入升级。Playwright 为可选按需项，其安装与升级由 SKILL.md 在用户明确要求时处理，不进入脚本。
- 镜像配置以 `mirrors/<name>.sh` 环境变量形式注入：`CADENCE_NPM_REGISTRY`、`CADENCE_PY_INDEX`、`CADENCE_SUPERPOWERS_GIT`。`cn.sh` 预置淘宝 npm 镜像、清华 pypi 镜像与国内 Superpowers Git 镜像地址；`default.sh` 预置官方源。
- 改写 `pre-check/SKILL.md`：六个工具的安装/验证正文移交脚本，SKILL.md 改为"调用脚本 → 读 JSON 报告 → 处理脚本不管的四项（Superpowers 软链、OpenSpec 三客户端产物、Playwright、API Key 占位提醒）"；Superpowers clone/pull 地址经 JSON 报告 `<REPORT>` 的 `hints.superpowers_git` 传递（镜像配置写入报告，SKILL.md 从报告读取，而非直接读脚本内部变量 `$CADENCE_SUPERPOWERS_GIT`）。
- 非目标：
  - 不修改 `rule-config` 与 `mcp-configuration`（后续单独 change）。
  - 脚本不处理 Superpowers 软链同步、OpenSpec 三客户端产物补齐、Playwright 安装、API Key 收集（这四项仍由 SKILL.md 驱动）。
  - 不自动修改用户 git 全局配置；Superpowers 国内镜像通过环境变量注入，零副作用。
  - 不编写 Windows 脚本（本 change 仅支持 mac/Linux bash）。

## Capabilities

### New Capabilities

- `pre-check-shell-execution`: pre-check 六个基础工具的脚本化执行机制——脚本职责边界、`run`/`check` 子命令与参数语义、增量秒跳过行为、`--upgrade` opt-in 升级语义与升级范围、JSON 报告结构与 SKILL.md 的调用约定。
- `pre-check-mirror-sources`: pre-check 镜像源配置能力——`mirrors/` 目录与环境变量注入机制、`default.sh` 与 `cn.sh` 的源地址定义、`--mirror` 切换语义、Superpowers Git 地址的镜像化与"镜像即权威"版本口径。

### Modified Capabilities

- `init-skill-sequencing`: pre-check 的六个基础工具检查从"SKILL.md 正文逐步执行"调整为"脚本执行 + SKILL.md 读报告处理剩余项"，OpenSpec 三客户端产物补齐与失败门槛语义保留，但执行主体与验收口径需补充脚本化后的表述。

## Impact

- 受影响文件（新增）：`cadence-init/skills/pre-check/scripts/pre-check.sh`、`cadence-init/skills/pre-check/scripts/mirrors/default.sh`、`cadence-init/skills/pre-check/scripts/mirrors/cn.sh`。
- 受影响文件（修改）：`cadence-init/skills/pre-check/SKILL.md`（六个工具的安装/验证正文移交脚本，改为调用约定与剩余四项处理）。
- 受影响行为：`/pre-check` 的执行方式（模型从逐条 bash 编排变为单条脚本调用 + 读 JSON）；大陆环境的可用性（镜像源开箱）；重复执行的耗时（秒跳过）；升级能力（新增 `--upgrade`）。
- 依赖变化：新增对 `mirrors/cn.sh` 中国内 Git 镜像地址的依赖（`https://gitee.com/michaelChe-World/superpowers.git`，由用户自行同步维护）。
- 不受影响：rule-config、mcp-configuration、OpenSpec CLI 本身、六个工具的门槛地位、no-interrupt 失败关闭语义。
