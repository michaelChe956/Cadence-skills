---
name: devbox-stack
description: "Use when 容器内 agent 需要启停/配置/排障中间件（mysql、redis、rabbitmq、minio 等）、查询标准连接串、或目录外追加服务。前置门禁：`test -d /cadence/stack && command -v stack` 不满足时本 skill 不适用——声明不适用并按普通流程继续，不模拟其行为。"
---

# devbox 中间件与应用栈运维（唯一入口）

## 适用性检测（先于一切操作）

```bash
test -d /cadence/stack && command -v stack >/dev/null 2>&1 \
  || { echo "devbox-stack 不适用：当前环境非 devbox 容器（无 /cadence/stack 或无 stack 命令）"; exit 0; }
```

非 devbox 环境（裸机 Linux/macOS 用户）不得伪造 stack 行为或直接操作不存在的工作目录，声明不适用即可静默退出。

## 硬性规则

1. 中间件的启停/重启/日志/配置变更/版本更换/追加/删除，**必须**通过 `stack` 命令完成（`/usr/local/bin/stack`，镜像内置），禁止裸写 `docker compose`/`docker` 命令操作 `/cadence/stack` 下的服务；
2. `stack add` 与 `stack rm` 是 `/cadence/stack/CHANGES.md` 留痕的唯一写入口——未留痕的改动不会被启动时模板同步与维护者评估识别，也不要手工编辑 CHANGES.md；
3. 目录外自加服务必须走「追加协议」三步（设计 4.7）：先 `stack ls` 查官方目录 → 目录内没有才 `stack add <name> --tpl <最接近的官方模板>` → 完成后告知用户「这是临时配置，建议反馈维护者固化入官方目录」；
4. 连接串一律使用 compose 服务名（`mysql`/`redis`/`rabbitmq`/`minio`），禁止在应用配置里写宿主 localhost——用 `stack conn <name>` 获取标准连接串与 application.yaml 片段后原样粘贴；
5. `stack rm --purge` 会删除数据且不可恢复：必须先向用户复述后果（服务名+数据位置）并获得明确确认后才执行；
6. enable/disable 修改的是 `/cadence/stack/.env` 的 `COMPOSE_PROFILES`——容器内与宿主侧是同一 compose 项目（`name: cadence`），任一侧生效即全局生效。

## 命令速查（引用镜像内已装命令，本 skill 不复制任何脚本）

| 场景 | 命令 | 说明 |
|---|---|---|
| 服务运行状态 | `stack status` | compose ps |
| 目录与启用清单 | `stack ls` | 官方目录 + 当前 COMPOSE_PROFILES + CHANGES.md 摘要 |
| 启用 | `stack enable rabbitmq`（或 `stack enable mq`） | 写 COMPOSE_PROFILES 并尝试拉起 |
| 停用 | `stack disable mq` | 移出 COMPOSE_PROFILES；默认服务（mysql/redis）仅 stop 保留数据 |
| 重启 | `stack restart mysql` | 配置改动后生效手段（改 `/cadence/stack/catalog/<svc>/conf` 后重启） |
| 日志 | `stack logs mysql` | --tail 100 跟随 |
| 连接串 | `stack conn mysql` | 标准连接串 + Spring 片段 |
| 目录外自加 | `stack add kafka --tpl rabbitmq` | 参数化生成 service 骨架+自动留痕 |
| 删除 | `stack rm kafka`（`--purge` 连数据） | 二次确认 |
| 本地应用 | `stack app run demo mvn spring-boot:run`（同组：`app stop/logs/port <name>`） | run=后台起（pid/log 落 stack/../run/app/）、port=端口探活带超时；spring-boot/vite 起停不经 docker |

## 排障与边界

- 应用侧连通性排障用镜像内已装客户端：`mysql`（mysql-client）、`redis-cli`（redis-tools）；rabbitmq/minio 用端口探活（`nc`/`curl`）；
- docker.sock ≈ 宿主 root 等价（设计 4.7 安全口径）：仅用于本项目中间件运维，不得操作用户其他容器；
- 建库建表走项目自身 Flyway/JPA；无此能力的项目在容器内执行 SQL 前先 `stack conn mysql` 核对连接信息。
