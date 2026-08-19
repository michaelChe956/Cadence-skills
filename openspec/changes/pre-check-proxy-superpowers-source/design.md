# Design: pre-check-proxy-superpowers-source

## Context
现状：cn.sh 单一 `CADENCE_SUPERPOWERS_GIT`（Gitee 镜像）；pre-check.sh 校验非空并输出 `hints.superpowers_git`（单串）；SKILL.md 步骤 6 指示 Agent 读该 hint 执行 clone/更新（`git -C` 自包含、不 cd）；test.sh 断言 hints 字段与两镜像地址。受限网络下 Gitee git 通道被审计设备 401 拦截，Gitee 归档下载被自身反爬拒绝；实测 GitHub 加速代理（ghfast.top / gh-proxy.com 匿名 clone 通过，mirror.ghproxy.com 保留为第三候选）可用且与上游实时同步。

## Decisions
1. **候选列表而非单地址**：`CADENCE_SUPERPOWERS_GIT` 保持变量名，值为空格分隔多 URL（默认镜像为单 URL），避免增加新变量与默认值语义分裂。
2. **报告字段改数组**：`hints.superpowers_git_candidates: [..]`（JSON 数组），删除旧字段；唯一消费方是 SKILL.md 自身命令模板，无外部兼容负担。
3. **浅克隆**：clone 统一 `--depth 1`（用户裁决）；更新用 fetch+pull 常规增量，不强制 shallow 维护。
4. **顺序尝试、全败即败**（用户裁决：不做 Gitee 兜底、不做离线保底）：失败关闭沿用既有 no-interrupt 规则；普通模式报告失败。
5. **更新自动切源**：origin 不在候选内 → set-url 为首个 fetch 成功的候选；已在候选内 → 直接更新。
6. **SKILL.md 步骤 6 重写**：clone/更新命令模板改为候选循环（单条自包含 shell，逐候选尝试），删除"离线安装方式"节与离线降级行为描述。

## Risks / Trade-offs
- [公益代理不稳定] → 三候选顺序尝试；全败报错（用户接受的残余风险）。
- [代理内容可被篡改] → 用户接受（不引入签名校验）；上游实时性换取可用性。
- [hints 字段名变更] → 仅 SKILL.md 消费，同步更新；test.sh 断言同步。

## Migration Plan
已有安装 origin 指向 Gitee：下次 pre-check 更新时自动切换（决策 5），无需人工干预。回滚：revert 本 change 即回到 Gitee 单源。

## Open Questions
无。
