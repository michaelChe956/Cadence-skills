## ADDED Requirements

### Requirement: Superpowers 在线源使用代理候选列表
cn 镜像的 Superpowers 在线安装源 MUST 为 GitHub 加速代理候选列表（顺序：ghfast.top、gh-proxy.com、mirror.ghproxy.com，均指向 obra/superpowers 上游）；default 镜像 MUST 为单元素候选列表（GitHub 官方地址）。报告 MUST 以 `hints.superpowers_git_candidates` 数组暴露候选列表，MUST NOT 再输出单一地址字段。clone MUST 按序尝试候选并使用 `--depth 1` 浅克隆；全部候选失败时步骤 MUST 判定 `failed` 并报告逐个候选的错误原因，no-interrupt 模式 MUST 按失败关闭规则立即终止。

#### Scenario: 首个代理可用时浅克隆
- **WHEN** 执行 Superpowers 在线安装且第一个代理候选 clone 成功
- **THEN** 使用该候选以 `--depth 1` 完成克隆并继续软链同步

#### Scenario: 全部候选失败
- **WHEN** 三个代理候选 clone 全部失败
- **THEN** 步骤判定 `failed`，报告列出每个候选的错误
- **AND** no-interrupt 模式立即终止 `/pre-check`，不降级为警告

### Requirement: Superpowers 更新必须切换到候选源
本地 `~/.agents/superpowers` 的 origin 不在候选列表内（如历史 Gitee 地址）时，更新逻辑 MUST 先将 origin 切换为首个可拉取成功的候选再执行更新；候选内地址 MUST 直接更新。

#### Scenario: 历史安装源切换
- **WHEN** 已有安装的 origin 指向 Gitee 镜像且执行更新
- **THEN** 先切换 origin 为首个可用代理候选
- **AND** 切换后完成更新与软链同步

### Requirement: 不做离线兜底
Superpowers 安装/更新失败时系统 MUST NOT 提示或校验离线复制目录；失败即报告失败，MUST NOT 提供降级路径。

#### Scenario: 失败不降级
- **WHEN** Superpowers 在线安装失败
- **THEN** 报告失败原因与恢复建议（检查网络/代理可达性）
- **AND** MUST NOT 提示"离线复制到 ~/.agents/superpowers"或类似兜底路径
