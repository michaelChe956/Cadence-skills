## Why

现仓库唯一安装方式 `install-offline.sh`/`install-offline.bat` 是"本地复制到 Claude marketplace 目录 + 文本级追加 known_marketplaces.json"，仅服务 Claude Code 单客户端，且 sh 版对 JSON 的文本追加存在格式损坏风险；同时根 `README.md` 与 `readmes/` 7 份文档大量保留旧安装逻辑、失效的 `/cadence-init:*` 调用名与不完整的 skill 清单（列 7~8 个，实际 14 个），与仓库现状严重脱节。需对齐 cadence-aria monorepo 分支（feat-b-0808-add-monorepo）已验证的网络安装机制，并使全部用户文档恢复可信。

## What Changes

- **BREAKING** 新增 `install.sh`（bash）：网络安装——仅按序尝试 3 个镜像 clone（ghfast.top → gh-proxy.com → mirror.ghproxy.com，全部失败即报错，无直连 GitHub 兜底）；目标已存在则 `fetch --all` + `pull --ff-only` 更新（失败轮换镜像 remote 重试）；clone 后对 `cadence-init/skills/*` 建三层软链（`~/.agents/skills/<skill>` → 仓库源；`~/.claude/skills/<skill>`、`~/.codex/skills/skills/<skill>` → `~/.agents/skills/<skill>`）；目标目录存在但非 git 仓库时提醒用户删除后重新运行，不做离线降级
- **BREAKING** 删除 `install-offline.sh` 与 `install-offline.bat`；不再写 `known_marketplaces.json`、不再注册 marketplace；检测到旧 marketplace 安装残留（`~/.claude/plugins/marketplaces/cadence-skills-local`、`known_marketplaces.json` 残留键）时仅提示与给出手动清理命令，不自动删除
- 新增 `--uninstall`（仅删除精确匹配的托管软链）与 `--uninstall --delete-repo`（连同删除 `~/.agents/Cadence-skills`）
- 重写根 `README.md`：新安装方式为主线、移除 marketplace 安装与失效调用名、统一裸 skill 名调用、补齐 14 skill 清单、更新/卸载/FAQ
- 重写 `readmes/` 全部 7 份用户文档
- 新增开发者向项目知识文档 `cadence/readmes/2026-09-01_README_项目知识文档_v1.0.md`（目录地图、14 skills 职责、新旧安装机制对照、四 agent 消费路径、迁移与卸载）

## Capabilities

### New Capabilities

- `network-skill-install`：install.sh 的行为契约——镜像 clone 与失败语义、更新语义（ff-only、镜像轮换）、三层软链、冲突保护（非托管软链/普通文件不覆盖）、非 git 目录处理（提醒删除）、卸载语义、旧残留提示、发布验证（四 agent skill 可见性）

### Modified Capabilities

（无——现有 specs 的 requirement 均不变；`rule-config-scripted-execution` 中"marketplace checkout 不作为模板源"的约束与新安装位置天然兼容）

## Impact

- 受影响文件：仓库根（新增 `install.sh`，删除 `install-offline.sh`/`install-offline.bat`）、`README.md`、`readmes/` 全部 7 份、`cadence/readmes/`（新增知识文档）
- 用户影响：已用旧方式安装的用户需按迁移说明清理旧 marketplace 安装；安装目标从 `~/.claude/plugins/marketplaces/cadence-skills-local` 变为 `~/.agents/Cadence-skills` + 三层软链
- 不影响：`cadence-init` 插件内容本身、pre-check 运行时工具安装、各 skill 行为契约、openspec 既有 specs
