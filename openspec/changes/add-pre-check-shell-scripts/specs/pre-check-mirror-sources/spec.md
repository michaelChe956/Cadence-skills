# pre-check-mirror-sources Specification

## ADDED Requirements

### Requirement: 镜像配置经环境变量注入

pre-check MUST 在 `scripts/mirrors/` 目录下以 `<name>.sh` 文件形式维护镜像源配置，每个文件 MUST 通过环境变量定义源地址，至少包含 `CADENCE_NPM_REGISTRY`（npm 源）、`CADENCE_PY_INDEX`（Python 包索引）、`CADENCE_SUPERPOWERS_GIT`（Superpowers Git 地址）。脚本 MUST 在命令级注入这些变量（如 `npm --registry=`、uv 索引环境变量），MUST NOT 写入用户全局 npm/uv/git 配置文件。

#### Scenario: 镜像文件定义三类源

- **WHEN** 查看任一 `scripts/mirrors/<name>.sh`
- **THEN** 文件定义 `CADENCE_NPM_REGISTRY`、`CADENCE_PY_INDEX`、`CADENCE_SUPERPOWERS_GIT` 三个环境变量

#### Scenario: 不污染用户全局配置

- **WHEN** 以任一 mirror 执行 `pre-check.sh run`
- **THEN** 脚本不修改 `~/.npmrc`、`~/.config/uv/uv.toml` 或 `git config --global`，源仅在脚本进程内生效

### Requirement: default 与 cn 两个预置镜像

`mirrors/` MUST 预置 `default.sh` 与 `cn.sh`。`default.sh` MUST 使用官方源：npm registry 为 `https://registry.npmjs.org`，Python 索引为 `https://pypi.org/simple`，Superpowers Git 为 `https://github.com/obra/superpowers`。`cn.sh` MUST 使用大陆镜像：npm registry 为 `https://registry.npmmirror.com`，Python 索引为 `https://pypi.tuna.tsinghua.edu.cn/simple`，Superpowers Git 为国内镜像地址。

#### Scenario: default 使用官方源

- **WHEN** 查看 `mirrors/default.sh`
- **THEN** 三个变量分别指向 registry.npmjs.org、pypi.org/simple、github.com/obra/superpowers

#### Scenario: cn 使用大陆镜像

- **WHEN** 查看 `mirrors/cn.sh`
- **THEN** npm 指向 registry.npmmirror.com，Python 索引指向 pypi.tuna.tsinghua.edu.cn，Superpowers Git 指向国内镜像地址

### Requirement: --mirror 切换与默认值

脚本 MUST 支持 `--mirror <name>` 参数加载 `scripts/mirrors/<name>.sh`；未携带 `--mirror` 时 MUST 默认加载 `default.sh`；指定的 mirror 文件不存在时 MUST 报错并以非零退出码终止，MUST NOT 静默回退到其他源。

#### Scenario: 默认加载 default

- **WHEN** 执行 `pre-check.sh run`（不带 `--mirror`）
- **THEN** 脚本加载 `default.sh`，使用官方源

#### Scenario: 指定 cn 加载大陆镜像

- **WHEN** 执行 `pre-check.sh run --mirror cn`
- **THEN** 脚本加载 `cn.sh`，npm 与 uv 命令使用大陆镜像源

#### Scenario: 未知 mirror 报错

- **WHEN** 执行 `pre-check.sh run --mirror nonexistent`
- **THEN** 脚本报错并以非零退出码终止，不使用任何源继续执行

### Requirement: Superpowers Git 地址镜像化

SKILL.md 的 Superpowers 步骤 MUST 从镜像配置注入的 `$CADENCE_SUPERPOWERS_GIT` 读取 clone/pull 地址，MUST NOT 在正文中硬编码 GitHub 地址；使用国内镜像时 MUST 直接使用该地址，MUST NOT 额外配置 git 代理或修改 git 全局配置。

#### Scenario: SKILL.md 读取镜像地址

- **WHEN** SKILL.md 执行 Superpowers clone/pull
- **THEN** 使用 `$CADENCE_SUPERPOWERS_GIT` 的值作为远端地址，正文不出现硬编码 github.com 地址

#### Scenario: cn 模式下无代理

- **WHEN** 以 `--mirror cn` 执行后 SKILL.md 同步 Superpowers
- **THEN** 直接使用 `cn.sh` 定义的国内 Git 地址 clone/pull，不设置 http.proxy 等 git 代理

### Requirement: 镜像即权威的版本口径

脚本在 `--upgrade` 或下载工具时 MUST 以当前生效镜像源的 latest 为权威版本；`--mirror cn` 时 MUST 以 npmmirror/清华镜像的 latest 为准，通用源时 MUST 以 npmjs/pypi 的 latest 为准；MUST NOT 跨源比对版本或对镜像落后于主仓库发出告警（镜像同步由镜像维护方负责）。

#### Scenario: cn 升级不比对主仓库

- **WHEN** 执行 `pre-check.sh run --mirror cn --upgrade`
- **THEN** 脚本以 npmmirror/清华 latest 判定是否升级，不查询 npmjs/pypi，不对源间版本差异告警

#### Scenario: 报告记录升级来源

- **WHEN** `--upgrade` 触发某工具升级
- **THEN** JSON 报告在该工具项记录升级前后版本与所用源（如 npmmirror 或 npmjs）
