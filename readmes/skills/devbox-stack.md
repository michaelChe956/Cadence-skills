# devbox-stack 使用指南

## 概述

`devbox-stack` 是 devbox 容器内 agent 对中间件（mysql/redis/rabbitmq/minio 及自加服务）与本地应用的**唯一运维入口**。它把设计文档中的「追加协议」（先查官方目录 → 目录外才自加 → 自加留痕 → 引导反馈固化）从文档约定落成工具强制：所有启停/配置/增删操作必须经 `stack` 命令完成，禁止裸写 docker 命令。

- Skill 源：[cadence-init/skills/devbox-stack/SKILL.md](../../cadence-init/skills/devbox-stack/SKILL.md)
- 镜像与编排实现：[Cadence-devbox 仓库](https://github.com/michaelChe956/Cadence-devbox)

## 环境检测（重要）

Skill 启动时执行环境检测：`test -d /cadence/stack && command -v stack`。

- **devbox 容器内**：检测通过，skill 生效，agent 使用 `stack` 命令
- **非 devbox 环境**（裸机 Linux/macOS、eval 容器等）：skill 声明「不适用」并静默退出，不干扰正常开发——安装 Cadence-skills 的所有用户都会装到本 skill，但只在 devbox 内激活

## 如何单独使用

本 skill 无需手动调用：devbox 容器内的 coding agent 遇到中间件/运维类请求时按 SKILL.md 规则自动走 `stack` 命令。用户也可以直接对 agent 说自然语言：

- 「帮我重启 mysql」→ agent 执行 `stack restart mysql`
- 「加个 kafka」→ agent 先查官方目录，没有则 `stack add kafka --tpl <模板>` 并自动留痕 `CHANGES.md`
- 「mysql 连接串是什么」→ agent 执行 `stack conn mysql` 输出标准 JDBC/配置片段

## 具体使用案例

### 案例 1：启用 MQ 与对象存储做联调

> 用户：「把 rabbitmq 和 minio 打开，我要联调消息和文件上传」

agent 执行：`stack enable mq,storage`（写 `COMPOSE_PROFILES` 并拉起），随后 `stack status` 确认 healthy，`stack conn rabbitmq` / `stack conn minio` 给出连接串供应用配置。

### 案例 2：目录外自加组件（留痕闭环）

> 用户：「项目要接 Elasticsearch，帮我加一个」

agent 流程：`stack ls` 查官方目录（无 es）→ `stack add es --tpl <相近模板>` 生成 service 片段（tag pin/卷/healthcheck）→ 自动追加 `CHANGES.md` 留痕行 → 提示用户「临时配置，建议反馈维护者固化进官方目录」。

### 案例 3：本地应用生命周期

> 用户：「把后端跑起来，看日志」

agent 执行：`app run backend -- mvn spring-boot:run`（后台启动+pid 管理）→ `app logs backend` 看输出 → `app port backend 8080` 探活确认就绪。

## 结果产物

| 产物 | 位置 | 说明 |
| --- | --- | --- |
| `CHANGES.md` | `/cadence/stack/CHANGES.md` | 所有 `stack add/rm/enable/disable` 的留痕（追加协议核心） |
| `stack report` 输出 | 终端 | 服务清单+版本+变更摘要，用于反馈维护者 |
| 环境报告 | 终端 | 排障时一页看清当前栈状态 |

## 最佳实践

1. **唯一入口**：中间件操作一律走 `stack` 命令——未经 skill 的裸 docker 操作不会被模板同步与 `stack report` 识别
2. **目录优先**：官方目录（mysql/redis/rabbitmq/minio，持续扩充）内的服务用 `stack enable`；`stack add` 是逃生通道，用后反馈固化
3. **高危确认**：`stack rm <名> --purge` 会连数据卷删除，必须二次确认
4. **反馈闭环**：定期把 `CHANGES.md` / `stack report` 发给维护者，高频自加项升级为官方目录项；也可直接提 [Issue](https://github.com/michaelChe956/Cadence-devbox/issues) 点菜或按 [贡献清单](https://github.com/michaelChe956/Cadence-devbox/blob/main/devbox/README.md#42-用户想增加中间件怎么办两条路推荐-a) 提 PR

## 常见问题

- **Q：为什么我在非 devbox 机器上装了 Cadence-skills，没看到这个 skill 生效？**
  A：设计如此——环境检测不通过即静默退出，对非 devbox 场景零干扰。
- **Q：agent 能不能绕过 stack 直接跑 docker 命令？**
  A：SKILL.md 规则禁止；且绕过后的变更不进 CHANGES.md，模板同步会按「用户改过」处理，得不偿失。
- **Q：`stack status` 显示某服务 Exited 怎么办？**
  A：先 `stack logs <服务>` 看原因，再 `stack restart <服务>`；仍失败看 FAQ（rabbitmq 在 rootless podman 下有已知卷权限问题，Docker Desktop/Podman Desktop 无此问题）。

## 相关 Skills

- [pre-check](./README.md#初始化与规则-skills-4-个)：环境前置检查（本 skill 的检测发生在更早的启动阶段）
- [rule-config](./README.md#初始化与规则-skills-4-个)：项目规则配置（可在项目规则中追加「中间件操作走 devbox-stack」强化约束）

## 技术细节

- 命令实现：`stack-lib.sh`（纯函数库，可单测）+ `stack.sh`（CLI 分发），随 devbox 镜像内置 `/usr/local/bin/stack`
- 双运行时适配：status/restart/logs 按 `com.docker.compose.project/service` 标签直连 docker 兼容 API，podman 与 Docker 语义均可用（46 项 pytest 覆盖，含 pipefail 回归）
- 探针：eval 体系 `D1`（devbox 环境检测）——非 devbox 容器内 agent 应声明「不适用」而非裸跑 docker 命令
