# 方案设计：Cadence-skills 一体化 AI 开发环境容器（devbox）v1.0

> 生成时间：2026-09-11
> 状态：v1.1——k3-reviewer 评审（4 阻断+5 建议）+ 三方裁定已合入，可进 writing-plans
> 讨论参与：主会话（glm-5.3）+ ds-task（镜像工程）+ oracle（决策守护）+ ter-task（鉴权/挂载/UX）+ k3-reviewer（设计评审）

## 一、背景与目标

- **用户群**：Windows 业务开发/测试人员，技术能力弱，要求开箱即用。
- **动机**：
  1. 不为 Windows 做 Cadence-skills 原生兼容——容器就是兼容层；
  2. 环境安装是目标用户弃用 AI agent 的第一死因；
  3. README 已承诺「Windows 仅 WSL/Git Bash」，容器是正统升级。
- **目标**：一个 Docker 镜像 + 启动脚本，预装 claude/codex/pi/kimi/omp 五端 CLI 与 Java/前端/Python 工具链，Cadence-skills 首启自动安装；用户维护一份鉴权配置文件、宿主代码目录直接挂载，改完即用。
- **定位约束（oracle）**：镜像发行是**独立产物线**，与 skills 内容迭代解耦；仓库仍以 markdown/yaml 文档为主，本产物线代码集中在独立目录。

## 二、已拍板决策（5 项，2026-09-11）

| # | 决策点 | 结论 |
|---|---|---|
| 1 | 发行形态 | 镜像主线（自维护 Dockerfile+compose）+ devcontainer.json 引用同一镜像作 VS Code 图形入口 |
| 2 | skills 层 | **不进镜像**：首启 entrypoint 跑 install.sh 装到 `~/.agents` 卷，之后每次启动幂等 update |
| 3 | 发布节奏 | 周更 CI + GHCR/国内 ACR 双通道 + 三层标签（latest / YYYY.WW / semver 里程碑），夜测探针冒烟通过才推 |
| 4 | 第一期范围 | java+前端+python 全上，锁单版本（JDK21 / Node 24 LTS / uv），无版本矩阵无多架构 |
| 5 | 默认鉴权 | **用户维护单一配置文件**（含 provider 端点/key/模型映射 + git 身份），只读挂载进容器，entrypoint 启动时渲染为各端真实配置；无其他鉴权路径 |

明确排除：云工作区（Codespaces 类，大陆网络与公司代码出网合规风险）。

## 三、竞品参考

| 竞品 | 借鉴点 |
|---|---|
| dirien/devcontainer-coding-agents | 多 agent+技能打包；named volume 持久化配置目录 |
| Claude Code 官方 devcontainer 指南 | 官方认可容器内运行 |
| OpenHands / E2B | 沙箱流派（一次性容器），本方案为常驻开发环境，不冲突 |

## 四、架构

### 4.1 镜像分层（ds-task 方案，压缩后共约 0.5–0.6GB）

| 层 | 内容 | 更新频率 | 策略 |
|---|---|---|---|
| L1 os | ubuntu:24.04 + aliyun apt 源 + 基础工具（git/curl/ripgrep/vim/tmux/sudo/mysql-client/redis-cli/docker-ce-cli+compose 插件 等）+ 非 root 用户 dev | 季/年 | 手动重建跟安全更新 |
| L2 runtime | JDK21（Temurin adoptium deb@USTC）+ Maven 3.9.x tarball@USTC + Node 24 LTS tarball@npmmirror + uv@USTC github-release | 季 | ARG pin 版本，独立 tag |
| L3 agents | npm -g：@anthropic-ai/claude-code / @openai/codex / @earendil-works/pi-coding-agent；kimi 独立安装器→~/.kimi-code；omp 独立安装器→~/.local | 周 | 顶层重建 + 容器内自更新 |
| L4 skills | （无）首启装卷 | — | 见决策 2 |

- SpringBoot/Cloud、Vue/React 框架**不预装**：`settings.xml`/`.npmrc` 镜像配好后 `mvn archetype`/`npm create` 秒拉。
- pyenv 不装（需编译、报错难懂）；poetry 可选 pip 一行装（存量项目用户）；默认 uv。
- 可复现性：全 ARG pin + 镜像内置 `/opt/cadence/versions.txt` 版本清单。

### 4.2 国内镜像源（ds-task 已实测连通）

| 用途 | 源 | 配置位置 |
|---|---|---|
| apt | mirrors.aliyun.com/ubuntu | /etc/apt/sources.list.d/ubuntu.sources |
| Adoptium | mirrors.ustc.edu.cn/adoptium/deb | trusted.gpg.d + sources.list.d |
| maven | maven.aliyun.com/repository/public | ~/.m2/settings.xml |
| gradle | mirrors.cloud.tencent.com/gradle | ~/.gradle/init.gradle |
| npm | registry.npmmirror.com | ~/.npmrc |
| node dist | npmmirror.com/mirrors/node | 构建期 |
| pypi | mirrors.aliyun.com/pypi/simple | pip.conf + uv.toml |

### 4.3 卷设计（ter-task 方案）

**状态卷与缓存卷必须分卷**——清缓存不丢运行态与渲染产物：

| 卷 | 挂载点 | 用途 |
|---|---|---|
| cadence-claude / cadence-codex / cadence-pi / cadence-kimi | ~/.claude、~/.codex、~/.pi/agent、~/.kimi-code | 各端运行态与渲染产物 |
| cadence-agents | ~/.agents | Cadence-skills 仓库 + 投影 |
| cadence-omp | ~/.omp | omp 运行态与渲染产物（models.yml/config.yml；~/.local 二进制在镜像层，**不挂卷**以免遮蔽周更） |
| m2 / npm / uv / pip / gradle | ~/.m2、~/.npm(+.npm-global)、~/.cache/uv、~/.cache/pip、~/.gradle | 依赖缓存 |
| auth.yaml（bind, 只读） | /cadence/auth.yaml | 用户维护的鉴权配置文件（4.4） |
| work（bind） | /workspace | **宿主代码父目录**（如 `D:\code`），几十个仓库一次挂载，双向共享 |

卷治理：①状态/缓存卷标 `external: true`，防 `down -v` 误删；②多项目并存用 compose 项目名前缀隔离；③文档提供 `docker system prune` 清理指引；④回滚=改用上一周版 tag 重启，无额外工具。

端口：3000/8080（dev server）。

### 4.4 鉴权：配置文件驱动（决策 5 细化）

用户唯一维护的文件 `cadence-box.yaml`（放宿主，随 compose 只读挂载到 `/cadence/auth.yaml`）：

```yaml
git:
  name: 张三
  email: zhangsan@corp.com
providers:            # 中转/官方端点均可，可多个
  relay1:
    base_url: http://xxx/v1
    api_key: sk-xxx
    models:           # 可选：模型元数据（pi/omp 的 models 文件需要）
      - { id: glm-5.3, ctx: 200k }
agents:               # 各端用哪个 provider、哪个模型
  claude: { provider: relay1, model: glm-5.3 }
  codex:  { provider: relay1, model: glm-5.3 }
  pi:     { provider: relay1 }
  kimi:   { provider: relay1 }
  omp:    { provider: relay1, model: glm-5.3 }
  # 任一端可加 raw: 块，原样并入该端配置文件（逃生口）
```

- **渲染目标（以夜测 `_copy_auth` 代码实证为准）**：claude→`~/.claude/settings.json`+.credentials.json；codex→`~/.codex/config.toml`+`auth.json`+`models.json`；pi→`~/.pi/agent/` 下 `models.json`（真实端点/key 所在）+`auth.json`（空对象）+`settings.json`（渲染时剔除 packages 清单，防首次启动拉 275MB）；kimi→`~/.kimi-code/` 下 `credentials`+`config.toml`+`device_id`+`region`+`oauth`（5 文件，最低集为前 4）；omp→`~/.omp/agent/models.yml`+`config.yml`；git 身份→`~/.gitconfig`。渲染采用「临时全量渲染+原子替换」。
- **失败语义**：auth.yaml 缺字段/格式错→拒启，中文报错指明缺失键与行号，不回显密钥；install.sh/skills 装失败→降级告警不阻断（容器与 agent 可用），日志落盘，下次启动幂等重试。
- **git push 边界**：容器内 git 默认做到 commit 为止，**push 由宿主 git 客户端完成**（宿主 Credential Manager 天然持有凭据）；容器内 PAT push 为后续增强（最小 scope PAT，经 credential.store 写 tmpfs，不进镜像/卷/remote URL），不在第一期。
- **换 key/换模型**：改这一个文件 → 重启容器生效。
- **禁止**：任何凭据写入镜像层；`cadence-box.yaml` 进 .gitignore 模板；文档明示「该文件=密钥，勿提交勿分享」。

### 4.5 代码挂载：宿主工作树与容器共享（bind mount）

背景：用户宿主机已维护几十个 git 仓库，且要保持宿主侧 git 工作流（IDE/图形客户端）不变，容器内做编译/开发/测试/git 操作。

- **挂父目录**：`-v D:\code:/workspace` 一次挂载全部仓库；bind mount 是**共享挂载非拷贝**——宿主改文件容器即时可见，容器内 agent 改代码/产物宿主即时可见，两边操作同一工作树。
- **宿主/容器 git 共存规则**（entrypoint 默认配置，用户无感）：
  1. 换行符/幻影 diff：容器 git 的 `core.autocrlf`/`core.filemode` 与宿主 git-for-windows 对齐，避免容器首碰仓库即「全文件被修改」；新仓库推荐 `.gitattributes` 固定 LF；
  2. 文件监听：跨挂载 inotify 不传播，容器内 dev server 默认开轮询（`CHOKIDAR_USEPOLLING=1` / vite `usePolling` / spring-devtools 轮询）；
  3. 并发 git：两侧同时写 index 偶发 `index.lock`——瞬时锁重试即过，文档提示「agent 提交时避免同时在宿主跑 git」。
- **性能**：依赖缓存走 named volume（4.3）；Windows 宿主盘 bind 走 9p/drvfs，小文件密集 I/O 显著慢于原生（`node_modules`/`target` 写入 Windows 盘是最重场景）——依赖与产物尽量落卷，文档如实预告；若真机实测验收 3 不达标，既定后备方案=活动仓库的 `node_modules`/`target` 以 per-project 命名卷覆盖挂载（install.ps1 扫描生成，宿主同名目录被遮蔽需重装）。

### 4.6 Windows 首次体验（≤5 步）

1. install.ps1 检测/引导安装 Docker Desktop（含 BIOS 虚拟化提示）；
2. 生成 `cadence-box.yaml` 模板 + compose 文件（引导用户填 provider/key/模型，选择宿主代码父目录）；
3. 拉取镜像并 `up -d`（entrypoint 自动：渲染鉴权 → 装/更新 skills → 就绪）；
4. 打开终端/VS Code 进容器，即见 `/workspace` 下全部现有仓库；
5. 跑通第一条命令（如 `claude`）确认鉴权生效。

话术承诺「**零配置**」而非「零安装」：一次性 30–60 分钟装 Docker Desktop（可能含一次重启），配图解向导（README 图文分册）。用户文件全程留在 Windows 盘。

### 4.7 中间件栈：compose 多服务编排（支撑 javaweb+前端全链路）

目标：用户一条 `docker compose up -d` 同时拉起 devbox + 项目所需中间件，Java Web + 前端项目在容器内即可编译、起服务、联调。

| 服务 | 镜像（tag pin） | 启用方式 | 宿主访问（仅绑 127.0.0.1） |
|---|---|---|---|
| mysql | mysql:8.4（utf8mb4、数据卷、healthcheck） | 默认 | 3306（Navicat 等直连） |
| redis | redis:7-x | 默认 | 6379 |
| rabbitmq | rabbitmq:3-management | profile `mq` | 5672 + 管理台 15672 |
| minio（文件存储，S3 协议） | minio/minio | profile `storage` | 9000 + 控制台 9001 |

- **按需启用**：默认只起 mysql+redis；`.env` 一行 `COMPOSE_PROFILES=mq,storage` 加开其余——弱用户改一行，不装多余东西。RocketMQ/Kafka 等其他 MQ 今后按用户需求加 profile，不动默认。
- **连接规则**：应用一律跑在 devbox 容器内，连接串用 compose 服务名（`jdbc:mysql://mysql:3306/…`、`redis://redis:6379`、`amqp://rabbitmq:5672`、minio endpoint `http://minio:9000`）；README 提供标准 `application-dev.yaml` 片段（环境变量占位），杜绝「宿主 localhost/容器服务名」混用的经典坑。
- **初始化**：建库建表走项目自身 Flyway/JPA；无此能力的项目由 agent 在容器内用 `mysql-client` 执行 SQL（L1 已含 mysql-client/redis-cli，供 agent 排障）。
- **数据持久**：各中间件数据 named volume，`external: true` 同卷治理；容器销毁重建数据不丢。
- **镜像拉取（国内）**：install.ps1 写 Docker Desktop `daemon.json` registry-mirrors（1ms.run/daocloud 类），否则弱用户 `compose pull` 直接失败。
- **资源口径**：全开约 +1.5–2GB 内存；文档标注「16GB 舒适，8GB 仅开必需 profile」。
- **前端联调**：vite dev server（3000 已发布宿主）proxy 指向容器内后端服务名，浏览器在 Windows 上直接访问。
- **agent 运维通道（关键设计）**：中间件启停/配置/换版本由容器内 coding agent 经 docker.sock 完成——devbox 挂载 `/var/run/docker.sock`，compose 项目目录（含各中间件 conf.d/redis.conf 挂载源）bind 到容器内 `/cadence/stack`；agent 执行 `docker compose -f /cadence/stack/compose.yaml restart|logs|up -d --profile xxx`，改 `/cadence/stack` 下配置后 restart 即生效（宿主同见）。**不采用**把中间件装进 devbox 单容器（supervisord）方案：镜像 2–3GB、换版本=重建镜像、进程管理复杂、资源不可按需。安全口径：docker.sock ≈ 宿主 root 等价，本威胁模型（用户自机+agent 全权）可接受；默认挂载+文档明示，企业敏感场景用无 sock 覆盖文件关闭（此时 agent 仅能连中间件端口，不能启停）。
- **追加软件：维护者固化为主，agent 自加为逃生通道**（防环境分叉）：
  1. **主路径·菜单制**：官方 stack 模板维护「已验证中间件目录」（mysql/redis/rabbitmq/minio，后续按反馈扩 kafka/es/nacos…），用户启用=改一行 profile；维护者负责 tag pin+healthcheck+国内源+验收后入目录——质量闸门在维护者；
  2. **逃生通道**：目录外的（临时试验/内部特殊组件）允许 agent 当场在 `/cadence/stack/compose.yaml` 加 service；
  3. **反馈闭环（Cadence 规则约束）**：以 skill 规则给 agent 装「中间件追加协议」——先查目录→没有才自加→自加必须留痕（diff 追加到 `/cadence/stack/CHANGES.md`）→告知用户「临时配置，建议反馈维护者固化」；维护者拿 CHANGES.md 零成本评估入目录。被多个用户采用的自加项升级为官方目录项；
  4. **其他软件**：轻量 CLI——agent 容器内 `apt`/`uv tool install`/`npm -g`（prefix 落 named volume，跨容器重建保留）；重型运行时（Go/新 JDK…）——反馈维护者进镜像 L2，随周更发版，用户 `docker compose pull` 升级。
- **stack 模板版本同步**：镜像内置 `/opt/cadence/stack/`（随周更更新，含版本号）；entrypoint 启动时对比宿主 `/cadence/stack`——未被用户/agent 改动则自动同步新版，已改（存在 CHANGES.md 留痕）则保留用户版并日志提示可合并。

### 4.8 devbox-stack skill：agent 的唯一中间件/app 运维入口

定位：Cadence-skills 新增 skill `devbox-stack`——容器内 agent 对中间件与本地应用的所有操作必须经它执行（SKILL.md 规则约束），不裸写 docker compose 命令；统一操作协议、强制留痕、内置预设。

**命令集（scripts/stack.sh）**：

| 命令 | 作用 |
|---|---|
| `stack status` / `stack ls` | 服务运行状态 / 目录+已启用清单 |
| `stack enable/disable <name>` | 启用/停用目录内服务（profile 一行） |
| `stack restart/logs <name>` | 重启、日志 |
| `stack conn <name>` | 打印标准连接串 + application.yaml 片段 |
| `stack add <name> --tpl <kafka>` | 目录外自加：参数化生成 service 骨架（tag pin/卷/healthcheck）+ 自动追加 CHANGES.md |
| `stack rm <name> --purge` | 删除服务（--purge 连数据卷，二次确认） |
| `stack update` | 同步官方模板（复用 entrypoint 判定逻辑） |
| `stack report` | 环境报告（服务+版本+CHANGES 摘要）供反馈维护者 |
| `app run/stop/logs/port` | 本地应用生命周期（后台起 spring-boot/vite、日志、端口探活） |

**预设目录（catalog/）**：每个中间件一项 = compose 片段 + 默认端口 + 连接串模板 + 配置骨架（my.cnf/redis.conf 等）+ 健康检查命令；首期预置 mysql/redis/rabbitmq/minio，按 CHANGES.md 反馈扩展。

**关键设计**：
1. **唯一入口双保险**：SKILL.md 规定中间件操作必须走 stack 命令；`add/rm` 是 CHANGES.md 留痕的唯一写入口——未走 skill 的裸操作不被模板同步与 `stack report` 识别，agent 无动机绕过；
2. **环境检测**：skill 检测 `/cadence/stack` 存在才激活；非 devbox 环境（裸机 Linux/macOS 用户）声明不适用并静默退出。skill 本体位于 `cadence-init/skills/devbox-stack/`，随 install.sh 投影五端，脚本仅依赖 bash+docker CLI；
3. **追加协议执行者**：4.7「先查目录→自加留痕→引导反馈」三步全部由 skill 命令实现，协议从文档约定变为工具强制。

分期：核心命令（status/ls/enable/disable/restart/logs/conn/add/rm/app）进第一期；update/report 第二期。

## 五、分期计划

| 期 | 内容 |
|---|---|
| 第一期 | 镜像 4 层 + compose（devbox+中间件栈 4.7）+ install.ps1（含 daemon.json 镜像源）+ 鉴权配置渲染器（entrypoint）+ skills 首启装卷 + devbox-stack skill 核心命令集（4.8）+ 图解文档（java/前端/python）；镜像由维护者本地构建、手动打 tag 发布，CI 第二期接入 |
| 第二期 | CI 周更流水线 + GHCR/ACR 双通道 + cosign 签名 + devcontainer.json 入口 + devbox-stack skill 完整版（stack update/report） |
| 第三期 | 测试工具链：JMeter（WSLg GUI，需显式接 Wayland/X11 socket，另行验证）、Playwright、渗透工具集 |
| 后续 | agent-update 容器内自助升级、容器内 git push PAT 增强、多语言版本矩阵（仅在用户强需求时） |

## 六、风险与缓解（前 3）

| 风险 | 缓解 |
|---|---|
| GitHub 断链：kimi/omp 安装器只发 GitHub，USTC github-release 无 kimi/pi/codex | ghfast.top 类代理 + ARG pin + 维护机离线预取 |
| 宿主/容器共用工作树的换行符幻影 diff 与 dev server 监听失效 | 容器 git 配置与 git-for-windows 对齐 + 默认轮询监听；首期验收含这两项（见七） |
| Docker Hub 拉取中间件镜像在国内失败 | install.ps1 写 daemon.json registry-mirrors + tag pin + 文档兜底手动导入 |
| docker.sock 挂载=宿主 root 等价，agent 可操作宿主全部容器 | 默认挂+文档明示含义；提供无 sock 覆盖文件一键关闭（企业敏感场景） |
| 9p/drvfs 小文件 I/O 慢：容器内 `npm install`/构建写 Windows 盘 | 依赖/产物落卷；验收 3 真机实测设门；后备=per-project 命名卷覆盖挂载（见 4.5） |

其他已记录：danger-full-access 与公司代码出网——默认不启用 bypass，compose 显式声明，公司代码按需只读挂载。

## 七、验证口径（第一期验收）

1. 【Windows 真机人工】Windows 11 全新机器按文档 5 步完成装机并进入终端（留证：机型、Docker/镜像版本、网络环境、命令、录屏）；
2. 用户改 `cadence-box.yaml` 换 key/模型 → 重启容器 → 五端均按新配置工作；容器销毁重建后配置仍生效（文件在宿主）；
3. 【Windows 真机实测，设通过门】容器内 `mvn archetype:generate`(spring-boot) / `npm create vite` / `uv init` 三条命令在国内网络下各 <3 分钟完成（依赖缓存预热后）；
4. 【Windows 真机人工】宿主 IDE 改文件 → 容器内 vite dev server 5 秒内热更（轮询生效）；容器 git `status/diff` 对宿主已检出的仓库**无幻影改动**（留证：改文件时间、热更与 git status/diff 截图）；
5. install.sh 在容器首启自动完成 skills 投影（复用夜测探针 P1/P3/P5 冒烟）；镜像压缩体积 ≤1GB；
6. 【Windows 真机】`stack enable mq,storage` 后，Spring Boot 样例工程连 mysql/redis/rabbitmq/minio 全部启动成功，宿主浏览器经 3000 端口访问前端页面完成一次增删改查（含文件上传走 minio）；全程启停/查询经 devbox-stack skill 命令完成，`stack add` 自加项正确落 CHANGES.md。

## 八、工作量预估

- 设计文档：本篇（已完成）；
- 第一期实现：4–6 个工作日（人+agent 协作；含五端渲染器联调、devbox-stack skill 与真机验收）；
- 之后每周维护：1–2 小时（CI 自动构建为主）。

## 九、本设计不做的事

- 不做 Windows 原生 Cadence-skills 兼容；
- 不做多语言版本矩阵、多 CPU 架构（第一阶段）；
- 不做云工作区；
- 不做宿主↔容器文件同步工具（bind mount 本身即双向共享）。

## 修订记录

- 2026-09-11 v1.6：新增 4.8 devbox-stack skill——agent 对中间件/app 的唯一运维入口（9 组命令+catalog 预设+CHANGES.md 唯一写入口+环境检测）；核心命令进第一期，预估改 4–6 天。
- 2026-09-11 v1.5：追加软件改为分层机制——维护者固化（菜单制/已验证目录）为主路径，agent 自加为逃生通道；Cadence 规则装「中间件追加协议」（先查目录→自加留痕 CHANGES.md→引导反馈）；模板同步以 CHANGES.md 判断用户改动。
- 2026-09-11 v1.4：4.7 补「追加软件三条路径」（中间件=agent 当场改 stack；轻工具=容器内装落卷；重型运行时=进镜像发版）与「stack 模板版本同步」机制（/opt/cadence/stack ↔ 宿主 /cadence/stack，未改自动同步/已改提示合并）。
- 2026-09-11 v1.3：明确「compose 多容器 + docker.sock 运维通道」优于「中间件单容器」——devbox 挂 docker.sock、compose 项目目录 bind 至 /cadence/stack、容器内装 docker-ce-cli+compose 插件，agent 可启停/改配/换版本；安全口径与关闭路径入风险表。
- 2026-09-11 v1.2：新增 4.7 中间件栈（compose 编排 mysql/redis/rabbitmq/minio + profiles 按需启用 + 服务名连接规则 + daemon.json 国内镜像源 + 资源口径）；L1 补 mysql-client/redis-cli；风险表与验收 6 同步。
- 2026-09-11 v1.1：k3-reviewer 评审 9 条经 ds-task/oracle/ter-task 三方裁定合入——B1 渲染清单按 _copy_auth 实证改写；B2 omp 卷改挂 ~/.omp；B3 勘误（Windows 无 VirtioFS，走 9p/drvfs）；B4 降为风险行+验收门+后备方案（per-project 卷不进第一期）；S1 失败语义；S2 容器内不 push（PAT 记后续）；S3 卷治理四条；S4 预估改 3–5 天；S5 验收标注真机人工项。
- 2026-09-11 按用户要求彻底移除 OAuth 与 WSL2 相关表述：鉴权仅保留配置文件路径；环境前置仅表述为「安装 Docker Desktop」。
- 2026-09-11 v1.0 初稿（三方讨论综合）。
