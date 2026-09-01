# 真机实测门禁（Real-Machine Gating）

> **目的**：判断当前改动需要真机实测，还是 CI 通过即可。
> **背景**：本仓库的 `install.sh` 直接操作用户 HOME（软链安装/更新/卸载）。误操作代价是破坏用户正在使用的环境。历史教训 F-2（2026-09-01）：前缀判定误删 28 条 superpowers 投影链，隔离 fixture 未含第三方形状，只有真机能暴露。

## 🔴 快速判断表（先查这里）

| 改动内容 | 门禁 |
|---------|------|
| `install.sh` 的所有权判定 / 孤儿清理 / 卸载 / 任何删除-替换-清理逻辑 | 🔴 **必须真机**（先 `--dry-run`） |
| 软链层结构或目标路径变更（三层路径、新增层） | 🔴 **必须真机** |
| 新增 coding agent 消费层 | 🔴 **必须真机**（验新 agent 可见性） |
| clone / update 网络逻辑（镜像顺序、`--ff-only`、remote 轮换） | 🟡 **建议真机** 跑一次更新路径 |
| `cadence-init/skills/*` 内容（SKILL.md、references、scripts） | 🟢 CI 即可 |
| 文档（README、readmes、知识文档、specs、plans、规则） | 🟢 CI 即可 |
| 测试自身 / `ci.yml` 自身 | 🟢 CI 即可 |
| 不影响安装脚本的依赖/工具版本调整 | 🟢 CI 即可 |

**记忆口诀：动"删改用户HOME的路径"必须真机；动"仓库内容与文档"CI 就够。**

## 真机实测固定五步（4A.5，不得跳步、不得改序）

1. **快照**：三层链清单（路径 + readlink 文本 + 可解析性）存 `/tmp/cadence-three-layer-before.log`
2. **预览**：`install.sh --dry-run`，人工核对——**不得出现任何指向非 cadence 条目的 REMOVE/REPLACE**；第三方链只能出现 KEEP/SKIP/WARN-MANUAL
3. **实装**：真实安装后拍 after 快照，`diff` 结果——已存在条目必须为空（全新首装仅允许新增）
4. **四 agent 留档**：Claude Code / pi / Codex / Kimi Code 逐端可见性证据存 `/tmp/cadence-four-agent-visibility.log`
5. **异常即停**：快照可完整回滚；任何计划外变化停止并回隔离测试排查

## 真机前置条件（不满足不得上真机）

- [ ] 隔离 HOME 测试套件全绿（必须包含第三方形状链存活红测）
- [ ] `shellcheck --severity=warning` 零告警
- [ ] 改动 diff 已通过审查

## 豁免规则

- 跳过真机必须在 change / 发布记录中**书面豁免**（写明原因与日期）
- SHOULD 级验证（如四 agent 冒烟）跳过时不得写成已通过

## 判定有疑问时

- 默认从严：宁可多跑一次真机（有快照与 dry-run 保护，成本低）
- 拿不准就问用户，附上本表对应的行
