## 1. 安装脚本 install.sh

- [ ] 1.1 实现 install.sh：镜像 clone（ghfast.top → gh-proxy.com → mirror.ghproxy.com，全失败报错、无直连兜底）、目标已存在时 fetch --all + ff-only 更新（remote 失败轮换镜像）、非 git 目录提醒删除后重装；验证：shellcheck 通过，隔离 HOME 下首装成功
- [ ] 1.2 实现三层软链同步与冲突保护（托管软链原子替换、非托管软链/普通文件警告跳过、孤儿托管软链清理）及四 agent 完成输出；验证：隔离 HOME 下三层软链齐全且指向正确
- [ ] 1.3 实现 --uninstall / --delete-repo 与旧 marketplace 残留检测提示；验证：卸载后托管条目清除且用户文件保留，残留场景输出清理命令

## 2. 测试与发布门禁

- [ ] 2.1 隔离 HOME 全流程测试：安装、重复安装（幂等）、非 git 目录场景、更新轮换、卸载；验证：全部场景符合 specs/network-skill-install
- [ ] 2.2 真实环境四 agent 可见性验证：Claude Code、pi、Codex、Kimi Code 均能发现 pre-check 等 cadence-init skills；验证：四端各自 skill 列举输出留档

## 3. 文档重写

- [ ] 3.1 重写根 README.md：项目定位、组件地图（14 skills）、新安装/更新/卸载/迁移（含旧 marketplace 清理）、四 agent 支持说明、FAQ；移除 marketplace 安装路径与 /cadence-init:* 失效调用；验证：文档内安装命令逐条可执行，无旧机制残留表述
- [ ] 3.2 重写 readmes/ 7 份（commands/README.md、commands/skill-create.md、skills/README.md 及 4 份指南）：统一裸 skill 名调用、补齐 14 skill 清单、对齐新安装方式；验证：scout 差异清单中的问题逐条闭合
- [ ] 3.3 新增开发者知识文档 cadence/readmes/2026-09-01_README_项目知识文档_v1.0.md：目录地图、14 skills 职责、新旧安装机制对照、四 agent 消费路径、迁移与卸载；验证：文档遵循 document-storage 命名与位置规则

## 4. 交付收尾

- [ ] 4.1 reviewer 审查脚本与文档是否符合本 change specs 与 design；验证：审查意见闭环或豁免记录
- [ ] 4.2 汇总交付物路径与验证证据，汇报（产物自动提交开关为关闭，不执行 git commit）；验证：用户收到路径清单

## 5. 安全包（F-2 修复、dry-run 与 CI）

- [ ] 5.1 TDD 修复所有权判定：先加两条红测（install 与 --uninstall 下第三方投影链必须存活），修正既有 managed-old 断言为完整 cadence 链形状，再以符号级所有权谓词替换前缀判定（install/uninstall 共用），孤儿清理改为先算共享层待清集合再清下游；验证：红转绿 + shellcheck 零告警 + 隔离全套件通过
- [ ] 5.2 实现 --dry-run（plan/execute 拆分，不联网不落盘）；验证：dry-run 后三层目录与软链零变化，计划与实装动作集合一致
- [ ] 5.3 新增 .github/workflows/ci.yml：shellcheck + 隔离 HOME 测试套件 + 含第三方形状回归 fixture 的 14×3 链接解析矩阵，不含真实四 CLI job；验证：CI 步骤本地模拟全绿
- [ ] 5.4 文档固化安全流程（README 安装章节与知识文档门禁节：dry-run → 确认 → 实装；真机四 agent 冒烟标注 SHOULD 一次性留档）；验证：文档 grep 断言通过
- [ ] 5.5 真机重验：三层链清单快照 → --dry-run 人工核对 → 实装 → 快照 diff 为空 → 四 agent 可见性留档或书面豁免；验证：门禁日志与快照 diff
