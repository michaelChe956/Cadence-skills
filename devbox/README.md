# cadence devbox —— 一体化 AI 开发环境容器 使用手册

> 版本：第一期（2026-09-11）｜ 镜像压缩体积 872MB ｜ 内置：claude 2.1.247 / codex 0.153.4 / pi 0.85.0 / omp 18.1.17（bun 1.4.2）/ kimi（官方安装器）+ JDK21 + Maven 3.9.16 + Node 24.21.0 + uv 0.12.11 + mysql/redis/rabbitmq/minio 编排
> 完整设计见 `cadence/designs/2026-09-11_方案设计_Cadence-skills一体化开发环境容器devbox_v1.0.md`

## 1. 镜像获取（二选一）

**路线 A：国内镜像仓库（推荐，待推送）**

```powershell
docker pull registry.cn-hangzhou.aliyuncs.com/<命名空间>/cadence-devbox:latest
```

**路线 B：离线 tar（当前可用）**

从维护者处拿到 `devbox-image.tar.gz` 后：

```powershell
docker load -i devbox-image.tar.gz     # 导入为 localhost/cadence-devbox:dev
```

## 2. 初次使用

### 2.1 安装 Docker Desktop（一次性，30–60 分钟）

官网下载安装，默认 WSL2 后端，按提示重启；提示 BIOS 虚拟化未开时进 BIOS 打开。装完在 PowerShell 验证：`docker version`。

国内加速（推荐）：Docker Desktop → Settings → Docker Engine，加入后重启：

```json
{ "registry-mirrors": ["https://docker.m.daocloud.io"] }
```

### 2.2 建安装目录（一次性）

以下以 `C:\cadence` 为安装目录（Linux 同理放 `~/cadence`）：

```powershell
mkdir C:\cadence; cd C:\cadence
# 从仓库 devbox/ 目录拷入：compose.yaml、stack\（含 catalog、docker-compose.no-sock.yml）、cadence-box.yaml.example
Rename-Item cadence-box.yaml.example cadence-box.yaml
mkdir stack -Force
Move-Item compose.yaml stack\
# stack\ 目录应含：compose.yaml、catalog\、docker-compose.no-sock.yml
```

写 `stack\.env`（三行）：

```powershell
@"
CADENCE_WORKSPACE=D:\code
CADENCE_DEVBOX_IMAGE=localhost/cadence-devbox:dev
COMPOSE_PROFILES=
"@ | Set-Content -Encoding utf8 C:\cadence\stack\.env
```

- `CADENCE_WORKSPACE`：你的代码父目录（几十个 git 仓库的上一级），将整体挂载为容器内 `/workspace`
- `CADENCE_DEVBOX_IMAGE`：路线 A 填 registry 地址，路线 B 填 `localhost/cadence-devbox:dev`

创建数据卷（external 卷需预建）：

```powershell
"cadence-claude","cadence-codex","cadence-pi","cadence-kimi","cadence-agents","cadence-omp","cadence-m2","cadence-npm","cadence-npm-global","cadence-uv","cadence-pip","cadence-gradle","cadence-mysql-data","cadence-redis-data","cadence-rabbitmq-data","cadence-minio-data" | ForEach-Object { docker volume create $_ }
```

### 2.3 填鉴权文件（唯一要你编辑的文件）

用记事本打开 `C:\cadence\cadence-box.yaml`，填三处：`base_url`（中转/官方端点）、`api_key`、各端用哪个 `model`。git 姓名/邮箱也在这里。

```yaml
git:
  name: 张三
  email: zhangsan@corp.com
providers:
  relay1:
    base_url: http://你的端点/v1
    api_key: sk-你的key
    models:
      - { id: glm-5.3, ctx: 200k }
agents:
  claude: { provider: relay1, model: glm-5.3 }
  codex:  { provider: relay1, model: glm-5.3 }
  pi:     { provider: relay1 }
  kimi:   { provider: relay1 }
  omp:    { provider: relay1, model: glm-5.3 }
```

> ⚠️ 此文件=密钥，勿提交勿分享。换 key/换模型改这里，`docker compose restart devbox` 生效。

### 2.4 启动与首验

```powershell
cd C:\cadence\stack
docker compose up -d          # 首次拉起 devbox + mysql + redis
docker compose logs devbox    # 应看到「步骤 1-4」并出现「就绪」
docker compose exec devbox bash   # 进入容器
```

容器内首验：

```bash
claude --version && codex --version && pi --version && omp --version   # 五端 CLI
stack status                # mysql/redis 运行状态
stack conn mysql            # 标准 JDBC/连接串（可直接抄进 application.yml）
ls /workspace               # 你的全部仓库已可见
```

## 3. 日常使用

| 场景 | 操作 |
|---|---|
| 每天开工 | `cd C:\cadence\stack; docker compose up -d`（二次启动秒级） |
| 进入容器 | `docker compose exec devbox bash`，然后直接 `claude` / `codex` / `pi` / `kimi` / `omp` |
| 换 key/换模型 | 改 `..\cadence-box.yaml` → `docker compose restart devbox` |
| 中间件增删启停 | 容器内 `stack` 命令（见 §4），或直接对 agent 说「加个 kafka」「重启 mysql」 |
| 跑项目 | 容器内 `app run myapp -- mvn spring-boot:run`（后台+日志+端口探活），或让 agent 全权 |
| 宿主工具连库 | Navicat 连 `127.0.0.1:3306`（root/cadence123）；浏览器开 `localhost:3000/8080` |
| 下班 | `docker compose stop`——凭据/依赖缓存/中间件数据全在卷里，不丢 |

代码工作方式：宿主 IDE 照常编辑 `D:\code` 下的仓库，容器内 agent/构建实时看到同一工作树（bind 双向共享）；push 在宿主 git 客户端完成。

## 4. 中间件速查（容器内 `stack` 命令）

```text
stack ls                    官方目录 + 当前启用 profile + CHANGES.md 摘要
stack status                全部服务运行状态与端口
stack enable/disable <名>   启用/停用（如 enable mq 加 rabbitmq；enable storage 加 minio）
stack restart/logs <名>     重启 / 日志
stack conn <名>             标准连接串 + application.yaml 片段
stack add <名> [--tpl T]    目录外自加服务（自动留痕 CHANGES.md，建议反馈维护者固化）
stack rm <名> [--purge]     删除（--purge 连数据卷，需二次确认）
stack report                环境报告（服务+版本+变更摘要）
app run/stop/logs/port      本地应用生命周期
```

默认目录：mysql:8.4、redis:7.4（默认启用）；rabbitmq:3.13-management（profile `mq`）；minio（profile `storage`）。

## 5. 如何更新

**镜像更新（周更）**

```powershell
cd C:\cadence\stack
# 路线 A：改 .env 中 CADENCE_DEVBOX_IMAGE 为新周版 tag（如 :2026.38），然后
docker compose pull devbox && docker compose up -d
# 路线 B：拿到新 tar 后 docker load -i 新包，改 .env 指向新 tag，up -d
```

**skills 更新（自动）**：每次容器启动 entrypoint 自动执行 `install.sh update`（幂等；失败仅告警不阻断，下次启动重试）。

**数据与回滚**：16 个数据卷独立于镜像，更新镜像不动数据；回滚=把 `.env` 的镜像 tag 改回上一周版重启。缓存膨胀时可按 `docker system prune` 指引清理（不会碰 external 卷）。

## 6. FAQ

1. **企业敏感场景关闭 docker.sock**：`docker compose -f compose.yaml -f docker-compose.no-sock.yml up -d`（agent 仍能连中间件端口开发，但不能启停容器）
2. **新仓库避免换行符幻影 diff**：仓库根加 `.gitattributes`：`* text=auto eol=lf`
3. **宿主与容器同时跑 git 偶发 index.lock**：瞬时锁，重试即可；agent 提交时避免宿主同时操作
4. **dev server 收不到宿主侧文件改动**：镜像已默认 `CHOKIDAR_USEPOLLING=1`（vite）；spring-boot-devtools 需在配置中开启轮询：`spring.devtools.restart.poll-interval=1s` + `quiet-period=0.8s`

## 7. Windows 真机验收（待执行——第一期交付后由维护者在真机完成）

### 7.1 执行指引

**阶段 A（Arch 维护机）**：

```bash
cd /home/michaelche/workspace/github/Cadence-skills
podman save cadence-devbox:dev | gzip > /tmp/devbox-image.tar.gz
tar czf /tmp/devbox-files.tar.gz devbox/
```

两个文件传到 Windows 目标机。

**阶段 B（Windows 装机）**：按 §2.1–2.4 执行并全程录屏（= 验收 1 留证）。

**阶段 C（容器内验收操作）**：

1. 验收 3 计时：`time mvn -B archetype:generate -DgroupId=t -DartifactId=d -DarchetypeArtifactId=maven-archetype-quickstart`；`time npm create vite@latest dv -- --template vue`；`time uv init dp`（依赖预热后各 <3 分钟）
2. 验收 4：宿主 `git init` 仓库提交数文件 → 容器内 `git status` 应无「全文件被修改」；起 vite 后宿主改 `App.vue`，容器内 dev server 5 秒热更
3. 验收 6：容器内对 agent 说「创建最小 Spring Boot 3 应用：/api/items 增查走 MySQL、/api/hits 走 Redis 计数，表自动建并跑起来；再建 vue3+vite 前端代理 /api 到 8080，3000 端口起 dev server」→ Windows 浏览器开 `localhost:3000` 完成增删查 + 文件上传走 minio；Navicat 连 `127.0.0.1:3306` 核对数据

**阶段 D**：截图/录屏按 7.2 清单归档。

### 7.2 验收清单（设计文档「七、验证口径」）

- [ ] 1.【真机人工】装机到进终端（留证：机型、Docker/镜像版本、网络环境、命令、录屏）——**Linux 侧已预覆盖安装布局逻辑**
- [ ] 2. 改 `cadence-box.yaml` 换 key/模型 → 重启容器 → 五端按新配置工作；容器销毁重建配置仍生效——**已预覆盖**（渲染 6 文件 + exit 2 拒启，46 项测试；真机补真实 key 验证）
- [ ] 3.【真机实测，设门】容器内 mvn/npm create/uv init 各 <3 分钟——**参考计时已取**（mvn 15s/spring-boot 依赖 20s/vite 0.7s/uv 0.1s）
- [ ] 4.【真机人工】宿主改文件 5 秒热更 + 无幻影 diff（留证：改文件时间、热更与 git status/diff 截图）
- [ ] 5. skills 首启投影 + 体积 ≤1GB——**已达标**（872MB；devbox-stack skill 待仓库 push 后随 install.sh 投影）
- [ ] 6.【真机】中间件全链路（含 minio 上传）——**Linux 容器侧已预覆盖**（Spring+Vue+MySQL+Redis 全链路实测，2 个连接串模板 bug 已修复）

## 8. 镜像构建信息

- 构建上下文：`devbox/`；版本 pin 唯一来源 `devbox/versions.env`（升级只改它 + Dockerfile 默认值）
- 版本清单：容器内 `cat /opt/cadence/versions.txt`
- 源：apt/docker-ce/pypi=aliyun，maven=aliyun（原 USTC 因容器 TLS 指纹被 CF 误杀），node=npmmirror，npm=registry.npmmirror.com，omp/bun=npmmirror（官方安装器走 GitHub 不可达）
- omp 本地语音/视觉依赖（onnxruntime/sherpa-onnx，568MB）已按需裁剪；需要时容器内 `npm i -g` 补装
