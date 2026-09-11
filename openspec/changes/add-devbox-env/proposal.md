## Why

目标用户是 Windows 业务开发/测试人员，技术能力弱、要求开箱即用，而环境安装正是这类用户弃用 AI agent 的第一死因。Cadence-skills 明确不做 Windows 原生兼容——容器就是兼容层（README 既有的「Windows 仅 WSL/Git Bash」口径的正统升级）。仓库现有夜测资产可直接复用三项：`eval/docker/container.py::_copy_auth` 的五端配置渲染实证（渲染目标的文件结构基线）、install.sh 的 skills 投影机制（`find cadence-init/skills/*/SKILL.md` 自动发现，新增 skill 零改动即被投影）、夜测探针 P1/P3/P5（skills 投影冒烟）。

## What Changes

新增 devbox 产物线（镜像发行与 skills 内容迭代解耦，代码集中于独立目录）：

- **镜像 4 层**：L1 os（ubuntu:24.04 + aliyun apt 源 + 基础工具 + 非 root 用户 dev）→ L2 runtime（JDK21 / Maven / Node 24 LTS / uv，国内源全 ARG pin）→ L3 agents（claude/codex/pi 经 npm -g，kimi/omp 独立安装器）→ L4 skills 空层（不进镜像，首启装卷）；压缩体积 ≤1GB，内置 `/opt/cadence/versions.txt` 版本清单。
- **compose 编排**：devbox + 中间件栈（mysql/redis 默认，rabbitmq/minio 按 profile），端口仅绑 127.0.0.1，状态/缓存分卷且 `external: true`，宿主代码父目录 bind 挂载 `/workspace`，docker.sock 运维通道（可覆盖关闭）。
- **install.ps1**：Windows ≤5 步首次体验——检测/引导 Docker Desktop、生成 `cadence-box.yaml` 模板与 compose 副本、写 daemon.json registry-mirrors、拉镜像并 `up -d`。
- **鉴权渲染器**（render-auth.py + entrypoint）：用户唯一维护 `cadence-box.yaml`（git 身份 + provider 端点/key/模型映射 + 各端绑定），只读挂载为 `/cadence/auth.yaml`，entrypoint 每次启动临时全量渲染 + 原子替换为五端真实配置与 `~/.gitconfig`；缺字段/格式错拒启（中文报错带行号、不回显 key）；无 OAuth、无其他鉴权路径。
- **devbox-stack skill**（`cadence-init/skills/devbox-stack/`）：容器内 agent 对中间件/app 运维的唯一入口——stack 命令集（第一期 status/ls/enable/disable/restart/logs/conn/add/rm）、catalog 预设目录（mysql/redis/rabbitmq/minio）、目录外自加必须落 CHANGES.md 留痕并引导反馈固化；环境检测不满足则声明不适用。

## Capabilities

### New Capabilities
- `devbox-env`: devbox 一体化开发环境容器的鉴权渲染、skills 装卷、中间件栈编排与 agent 运维入口行为，及其第一期完工口径。

### Modified Capabilities
- 无（镜像发行是独立产物线，不改动主线任何 skill 与脚本）。

## Impact

- 新增 `devbox/`：Dockerfile、versions.env、render-auth.py、entrypoint.sh、stack/（stack-lib.sh、stack.sh、catalog/）、compose.yaml、install.ps1、cadence-box.yaml.example、README.md
- 新增 `cadence-init/skills/devbox-stack/`：SKILL.md（install.sh 按既有 find 机制自动发现投影，`install.sh` 本身零改动）
- 新增 `tests/devbox/`：4 个测试文件共 37 项，命令统一 `uv run --with pytest --with pyyaml python -m pytest tests/devbox/ -v`
- 不动主线：不改 README.md 主文档、不改 install.sh、不改既有 skills；仓库仍以 markdown/yaml 文档为主
- 需求源：`cadence/designs/2026-09-11_方案设计_Cadence-skills一体化开发环境容器devbox_v1.0.md`（v1.6）；实施契约：`cadence/plans/2026-09-11_计划文档_实施_devbox第一期_v1.0.md`（Contract 1–7）
