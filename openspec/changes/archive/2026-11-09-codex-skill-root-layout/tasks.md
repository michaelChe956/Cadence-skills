# Tasks

## 1. 安装器：Codex 根扁平化与旧层迁移

- [x] 1.1 将 install.sh 的 Codex 层目标从 `~/.codex/skills/skills` 改为 `~/.codex/skills`，并新增旧嵌套层的受管链接迁移与迁空删除（对应 `network-skill-install` 的「Codex 旧嵌套层迁移」）
- [x] 1.2 安装完成输出同步更新 Codex 用户层/系统层路径说明

## 2. 安装器：所有权与孤儿清理加固

- [x] 2.1 增加“共享层同名条目不存在时，下游层精确指向 `~/.agents/skills/<name>`”的遗留投影判定与清理；保持第三方投影链存活（对应「冲突保护与所有权证明」）

## 3. 安装器：投影入口可读性校验

- [x] 3.1 同步完成后校验各层受管条目的 `SKILL.md` 可读；可证明归属的重建链接，不可证明的告警并给手动命令（对应「投影入口可读性校验」）

## 4. 安装器：Codex 技能根完整性扫描

- [x] 4.1 只读扫描 `~/.codex/skills` 下全部入口（含嵌套命名空间目录），对不可读入口输出告警与手动清理命令，不删除非托管内容（对应「Codex 技能根完整性扫描」）

## 5. pre-check：Codex 层扁平化与可解析性校验

- [x] 5.1 `superpowers-links` 阶段改用 `~/.codex/skills`，支持从旧嵌套层迁移（对应 `pre-check-scripted-execution` 的「五阶段编排与结构化阶段报告」）
- [x] 5.2 `verify` 阶段复核四层软链最终可解析性，不把 `.system`/插件缓存计入受管集合（对应「只读 verify 与失败快返」）

## 6. 测试与门禁

- [x] 6.1 扩展 `tests/test-install.sh`：旧层迁移、共享层缺失后的下游清理、断链重建、不可读入口告警、Codex 根扫描告警、系统目录不误报
- [x] 6.2 更新 CI 链接矩阵 fixture 的 Codex 根
- [x] 6.3 更新 pre-check 集成测试与基线快照中的 Codex 层路径

## 7. 文档

- [x] 7.1 更新 `README.md`、`readmes/` 目录约定表与 Cadence 知识文档目录约定表：Codex 用户层/系统层路径、skill-creator 双版本口径、旧嵌套层迁移说明
