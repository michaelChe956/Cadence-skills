## Purpose

定义 devbox 一体化开发环境容器（第一期）的行为契约：鉴权仅经配置文件渲染（无 OAuth）、skills 不进镜像首启装卷、追加软件分层制、stack 命令为 agent 运维唯一入口，以及以设计文档「七、验证口径」6 条验收为基础的完工口径（Linux 冒烟 + pytest 绿 + Windows 真机清单移交）。需求源：`cadence/designs/2026-09-11_方案设计_Cadence-skills一体化开发环境容器devbox_v1.0.md`（v1.6）。

## ADDED Requirements

### Requirement: 鉴权仅经配置文件渲染

用户 MUST 仅维护单一配置文件 `cadence-box.yaml`（git 身份 + providers 端点/key/模型映射 + 各端 agent 绑定），经 compose 只读挂载为 `/cadence/auth.yaml`；entrypoint 每次启动 MUST 将其渲染为五端（claude/codex/pi/kimi/omp）真实配置与 `~/.gitconfig`，采用临时目录全量渲染 + 原子替换。系统 MUST NOT 提供任何 OAuth 或其他凭据获取路径；任何凭据 MUST NOT 写入镜像层；`cadence-box.yaml` MUST 列入 .gitignore 模板并明示「该文件 = 密钥」。配置缺字段或格式错时 MUST 拒绝启动（exit 2），中文报错指明缺失键与 YAML 行号且不回显 key 值。容器内 git 默认做到 commit 为止，push 由宿主 git 客户端完成。

#### Scenario: 合法配置首启渲染五端

- **WHEN** 容器以合法 `cadence-box.yaml` 首次启动
- **THEN** `~/.claude/settings.json` 与 `.credentials.json`、`~/.codex/config.toml`+`auth.json`+`models.json`、`~/.pi/agent/` 下 `models.json`+`auth.json`+`settings.json`（剔除 packages）、`~/.kimi-code/` 下 5 文件、`~/.omp/agent/models.yml`+`config.yml`、`~/.gitconfig` 全部生成且内容与配置一致

#### Scenario: 缺字段拒启且不回显密钥

- **WHEN** `cadence-box.yaml` 缺 api_key 或 agent 引用不存在的 provider 时启动容器
- **THEN** 容器以 exit 2 退出，stderr 为中文报错、指明缺失键与 YAML 行号，且不含 key 值原文

#### Scenario: 换 key/换模型重启生效

- **WHEN** 用户修改 `cadence-box.yaml` 的 key 或模型后重启 devbox 容器
- **THEN** 五端均按新配置工作

#### Scenario: 容器销毁重建配置保持

- **WHEN** devbox 容器销毁后重建（配置文件在宿主）
- **THEN** 渲染产物重新生成，鉴权配置仍生效

#### Scenario: 无 OAuth 路径

- **WHEN** 检视 devbox 产物线的鉴权实现与文档
- **THEN** 不存在 OAuth/WSL2 相关路径或表述，环境前置仅表述为「安装 Docker Desktop」

### Requirement: skills 不进镜像、首启装卷

镜像 MUST NOT 包含 Cadence-skills 内容（L4 为空层）。entrypoint 首启 MUST 执行 install.sh 将 skills 装入 `~/.agents` named 卷，此后每次启动幂等 update。skills 安装失败 MUST 降级告警不阻断（容器与 agent 仍可用），日志落盘，下次启动幂等重试。镜像压缩体积 MUST ≤1GB。

#### Scenario: 首启自动投影 skills

- **WHEN** 容器首次启动完成
- **THEN** skills 经既有 install.sh 投影机制落入 `~/.agents`（以夜测探针 P1/P3/P5 冒烟验证），镜像压缩体积 ≤1GB

#### Scenario: 安装软失败不阻断

- **WHEN** skills 安装在启动时失败（如网络问题）
- **THEN** 容器正常进入就绪、日志留有中文告警，下次启动自动重试

### Requirement: 国内网络工具链就绪门

镜像 MUST 预装 JDK21/Maven/Node 24 LTS/uv 工具链（全 ARG pin、国内镜像源），依赖缓存落 named 卷；依赖缓存预热后，容器内 `mvn archetype:generate`（spring-boot）、`npm create vite`、`uv init` 三条命令在国内网络下 MUST 各在 3 分钟内完成（Windows 真机实测设通过门）。

#### Scenario: 三条脚手架命令通过时间门

- **WHEN** 在 Windows 真机容器内依次执行三条脚手架命令（依赖缓存预热后）
- **THEN** 每条命令在国内网络下 <3 分钟完成

### Requirement: 宿主/容器工作树共存

宿主代码父目录 MUST 以 bind mount 挂载到 `/workspace`（共享非拷贝，双向即时可见）。entrypoint MUST 默认将容器 git 配置与 git-for-windows 对齐（core.autocrlf/core.filemode）并注入轮询监听环境（CHOKIDAR_USEPOLLING 等）。宿主 IDE 改文件后，容器内 vite dev server MUST 5 秒内热更；容器 git status/diff 对宿主已检出仓库 MUST 无幻影改动（真机人工留证）。

#### Scenario: 热更与无幻影 diff

- **WHEN** 宿主 IDE 修改文件并保存
- **THEN** 容器内 vite dev server 5 秒内热更（轮询生效），且容器 git status/diff 不产生全文件幻影改动（留证：改文件时间、热更与 git status/diff 截图）

### Requirement: Windows 首次体验五步完成

install.ps1 MUST 覆盖五要素：检测/引导安装 Docker Desktop（含 BIOS 虚拟化提示）、生成 `cadence-box.yaml` 模板与 compose 副本（引导选择宿主代码父目录）、写 Docker Desktop daemon.json registry-mirrors、拉取镜像并 `up -d`、提示后续步骤。全新 Windows 11 机器 MUST 能按文档 ≤5 步完成装机并进入容器终端（真机人工留证）。话术承诺「零配置」而非「零安装」。

#### Scenario: 全新机器五步装机

- **WHEN** Windows 11 全新机器按 README 快速开始操作
- **THEN** ≤5 步完成装机进入容器终端，`/workspace` 下可见全部现有仓库，跑通第一条命令（如 `claude`）确认鉴权生效（留证：机型、Docker/镜像版本、网络环境、命令、录屏）

### Requirement: 中间件栈编排与全链路

compose MUST 以单一项目（`name: cadence`）编排 devbox + 中间件：mysql/redis 默认启用，rabbitmq/minio 经 profile 按需启用（弱用户改一行 `.env`）；端口仅绑 127.0.0.1；中间件数据卷 `external: true`。应用连接串 MUST 使用 compose 服务名（宿主工具直连 127.0.0.1）。启用 mq、storage profile 后，Spring Boot 样例工程 MUST 连 mysql/redis/rabbitmq/minio 全部启动成功，宿主浏览器经 3000 端口访问前端页面完成一次增删改查（含文件上传走 minio）（真机人工留证）。

#### Scenario: 全栈联调增删改查

- **WHEN** `stack enable mq,storage` 后启动 Spring Boot 样例工程与前端
- **THEN** 四中间件连接全部成功，宿主浏览器完成一次增删改查与 minio 文件上传

### Requirement: 追加软件分层制

追加中间件 MUST 以维护者固化的官方目录（catalog：tag pin + healthcheck + 国内源 + 验收后入目录）为主路径，用户启用 = 改一行 profile。目录外组件允许 agent 经 `stack add` 逃生通道自加，MUST 自动留痕于 `/cadence/stack/CHANGES.md` 并告知用户「临时配置，建议反馈维护者固化」；被多个用户采用的自加项升级为官方目录项。轻量 CLI 可在容器内安装并落 named 卷（跨容器重建保留）；重型运行时（Go/新 JDK 等）MUST 反馈维护者进镜像 L2 随周更发版。stack 模板同步 MUST 以 CHANGES.md 存在判定用户改动：未改自动同步镜像内置新版，已改保留用户版并日志提示可合并。

#### Scenario: 目录内启用走 profile

- **WHEN** 用户需要 mysql/redis/rabbitmq/minio 目录内服务
- **THEN** 仅改 `.env` 的 `COMPOSE_PROFILES` 一行即启用，不安装多余组件

#### Scenario: 目录外自加留痕

- **WHEN** agent 经 `stack add` 添加目录外中间件
- **THEN** 生成含 tag pin/卷/healthcheck 的 service 骨架，CHANGES.md 自动追加留痕行，用户被提示反馈维护者固化

#### Scenario: 模板同步尊重用户改动

- **WHEN** 镜像周更后容器启动且 `/cadence/stack` 已存在 CHANGES.md
- **THEN** 保留用户版不覆盖，日志提示可合并；若无 CHANGES.md 则自动同步官方新版

### Requirement: stack 命令唯一入口

容器内 agent 对中间件与本地应用的所有操作 MUST 经 devbox-stack skill 的 `stack` 命令执行（SKILL.md 规则约束），MUST NOT 裸写 docker compose 命令。第一期命令集 MUST 覆盖 status/ls/enable/disable/restart/logs/conn/add/rm（update/report 属二期）。`add`/`rm` MUST 是 CHANGES.md 留痕的唯一写入口——未走 skill 的裸操作不被模板同步与识别，agent 无动机绕过。skill MUST 做环境检测：`/cadence/stack` 存在且 `stack` 命令可用才激活，否则声明不适用并静默退出（非 devbox 裸机环境不受影响）。

#### Scenario: 运维操作走 stack 命令

- **WHEN** 容器内 agent 需要启停/查询/取连接串/追加中间件
- **THEN** 全程经 stack 命令完成（验收 6 的操作口径），`stack add` 自加项正确落 CHANGES.md

#### Scenario: 非 devbox 环境不适用

- **WHEN** devbox-stack skill 在无 `/cadence/stack` 的裸机 Linux/macOS 环境被触发
- **THEN** skill 声明不适用并静默退出，不执行任何操作

### Requirement: 第一期完工口径

第一期完工判定 MUST 为双段：本机 Linux（podman）段——镜像构建（L1–L4 国内源全通）、鉴权失败路径（exit 2）、entrypoint 全链路（渲染 + 模板同步 + skills 软失败或成功）、stack 命令、`/opt/cadence/versions.txt`、压缩体积 ≤1GB 冒烟全过，且 `tests/devbox/` 全部 pytest 通过；Windows 真机段——验收项（五步装机、换 key 重启、三条命令时间门、热更与无幻影 diff、skills 投影真机腿、全栈联调增删改查）MUST 以逐条化清单移交用户人工执行并留证，多容器联调为环境项按计划 Task 9 Step 7 处理。

#### Scenario: Linux 冒烟与单测全绿

- **WHEN** 第一期实现完成判定
- **THEN** podman 冒烟矩阵全过（五端渲染断言 / 失败路径 exit 2 / stack 命令 / 体积 ≤1GB）且 `uv run --with pytest --with pyyaml python -m pytest tests/devbox/ -v` 37 项全部通过

#### Scenario: 真机清单移交

- **WHEN** Linux 侧完工
- **THEN** `devbox/README.md` 提供设计文档「七」6 条逐条化的 Windows 真机验收清单，移交状态在收尾汇报中明示
