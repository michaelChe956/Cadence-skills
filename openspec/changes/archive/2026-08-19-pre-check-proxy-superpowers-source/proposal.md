# Proposal: pre-check-proxy-superpowers-source

## Why

pre-check 的 Superpowers 在线安装源（cn 镜像 = Gitee）在受限网络下 git 协议被审计设备拦截（匿名 401），Gitee 归档下载亦被自身反爬拒绝，导致自动化初始化无法完成 Superpowers 安装/更新。实测 GitHub 加速代理通道（ghfast.top、gh-proxy.com、mirror.ghproxy.com）匿名 git clone 可用且与 GitHub 实时同步。

## What Changes

- cn 镜像的 `CADENCE_SUPERPOWERS_GIT` 由单一 Gitee 地址改为**三个 GitHub 加速代理候选**（空格分隔、顺序尝试）。
- 报告 `hints.superpowers_git` 改为候选数组 `hints.superpowers_git_candidates`（default 镜像为单元素数组），原字段移除。
- clone 逻辑：按序尝试候选，`--depth 1` 浅克隆；全部失败 → 步骤 `failed` 并按 no-interrupt 失败关闭规则终止，报告逐个候选的错误。
- 更新逻辑：本地 origin 非候选地址时自动切换为首个可用候选后更新。
- 移除离线复制兜底分支（用户裁决：不做兜底和保底，错误了就报错）；同步删除 SKILL.md 中离线安装方式与降级链描述。
- test.sh 镜像断言同步为候选数组。

## Capabilities

### Modified Capabilities

- `init-skill-sequencing`: pre-check Superpowers 在线安装来源从单一镜像地址改为代理候选列表，取消离线兜底，失败关闭语义收紧。

## Impact

- `cadence-init/skills/pre-check/scripts/mirrors/cn.sh`、`pre-check.sh`（hints 字段）、`SKILL.md`（步骤 6 重写）、`scripts/test.sh`（断言）。
- 行为兼容性：已有安装的 origin 指向 Gitee，更新时自动切换到代理；`hints.superpowers_git` 字段名变更（消费方仅 SKILL.md 自身）。
- 非目标：不保留 Gitee 兜底、不做离线目录校验、不改其他工具（npm/uv）镜像。
