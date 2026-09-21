# Design: devbox 一体化 AI 开发环境容器（第一期）

## Context

本 change 的唯一需求源为 `cadence/designs/2026-09-11_方案设计_Cadence-skills一体化开发环境容器devbox_v1.0.md`（v1.6，已经 k3-reviewer 评审与三方裁定合入）；逐任务实施契约（接口签名/命令/文件清单/测试基线）为 `cadence/plans/2026-09-11_计划文档_实施_devbox第一期_v1.0.md`（Contract 1–7）。本文件只做决策索引与关键约束摘录，不复制设计全文；两处冲突时以设计文档为准。

## Goals / Non-Goals

**Goals**
- 第一期交付：镜像 4 层（国内源全 ARG pin、压缩 ≤1GB）、devbox+中间件 compose、install.ps1、鉴权渲染器、entrypoint（git 对齐→渲染→stack 模板同步→skills 软失败安装）、devbox-stack skill 核心命令集、图解 README。
- 本机（Arch Linux + podman 6.1.1）完成镜像构建、单容器冒烟与全部单测；Windows 真机验收项以逐条化清单移交。

**Non-Goals**
- 二期：CI 周更流水线、GHCR/ACR 双通道、cosign 签名、devcontainer.json 入口、stack update/report 完整版。
- 三期：测试工具链（JMeter/Playwright/渗透工具集）。
- 明确排除：Windows 原生兼容、云工作区、多语言版本矩阵、多 CPU 架构、容器内 git push PAT、一切 OAuth/WSL2 表述。

## Decisions（设计文档「二」5 项拍板，2026-09-11）

| # | 决策点 | 结论（细节见设计文档） |
|---|---|---|
| D1 | 发行形态 | 镜像主线（自维护 Dockerfile + compose）；devcontainer.json 引用同一镜像作 VS Code 图形入口（二期） |
| D2 | skills 层 | 不进镜像：首启 entrypoint 跑 install.sh 装到 `~/.agents` 卷，之后每次启动幂等 update |
| D3 | 发布节奏 | 周更 CI + GHCR/国内 ACR 双通道 + 三层标签（latest / YYYY.WW / semver），夜测探针冒烟通过才推；第一期维护者本地构建、手动打 tag |
| D4 | 第一期范围 | java+前端+python 全上，锁单版本（JDK21 / Node 24 LTS / uv），无版本矩阵无多架构 |
| D5 | 默认鉴权 | 用户维护单一配置文件（provider 端点/key/模型映射 + git 身份），只读挂载进容器，entrypoint 启动时渲染为各端真实配置；无其他鉴权路径 |

派生关键约束（实施 MUST 遵守，全文见计划文档「Global Constraints」）：

- 全 ARG pin 且与 `devbox/versions.env` 保持同步（唯一版本来源）；五端渲染目标以 `_copy_auth` 实证基线为准（含 pi 剔除 packages 防首启拉 275MB）。
- compose 单一项目（`name: cadence`）；状态/缓存卷 `external: true`；端口仅绑 127.0.0.1。
- entrypoint 顺序固定：git 对齐默认 → render-auth（失败即 exit 2）→ stack 模板同步（以 CHANGES.md 存在判定用户改动）→ skills 软失败安装 → `exec "$@"`。
- 新增文件只允许出现在 `devbox/`、`cadence-init/skills/devbox-stack/`、`tests/devbox/`；主线零改动。

## Risks / Trade-offs

前 3 项风险与缓解见设计文档「六」：GitHub 断链（kimi/omp 安装器）→ ghfast 类代理 + ARG pin + 维护机离线预取；宿主/容器共用工作树的换行符幻影 diff 与监听失效 → 容器 git 与 git-for-windows 对齐 + 默认轮询监听 + 验收 4 设门；Docker Hub 国内拉取失败 → install.ps1 写 daemon.json registry-mirrors + tag pin。docker.sock 挂载 = 宿主 root 等价：默认挂载 + 文档明示，企业敏感场景提供无 sock 覆盖文件一键关闭。

## Migration Plan

全新目录新增，无存量迁移；回滚 = 删除 `devbox/`、`cadence-init/skills/devbox-stack/`、`tests/devbox/` 三个目录即恢复原状（install.sh 未改动，无残留投影规则）。

## Open Questions

无（设计 v1.6 已闭合评审；版本精确号回填纪律已写入计划 Task 1）。
