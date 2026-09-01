## Context

cadence-aria monorepo 分支（feat-b-0808-add-monorepo）已在其 Rust 初始化流程中验证了"Cadence-skills 机器级共享依赖"机制：clone 到 `~/.agents/Cadence-skills`，对 `cadence-init/skills/*` 建三层软链（`~/.agents/skills` → 源；`~/.claude/skills`、`~/.codex/skills/skills` → 共享层）。本仓库需将该机制固化为独立 bash 安装脚本，并重写全部用户文档。四个 agent 的 skill 目录约定已核实：pi 读 `~/.pi/agent/skills` 与 `~/.agents/skills`（源码跟随 symlink）；Codex 现行主根为 `~/.agents/skills`、`~/.codex/skills` 递归扫描且 PR #8801 支持 symlink；Kimi Code/kimi-cli 均读 `~/.agents/skills`（kimi-cli 品牌组回退链最终可达 `~/.claude/skills`）；Claude Code 个人级为 `~/.claude/skills`（官方文档明示 skill 级 symlink 支持与去重）。

## Goals / Non-Goals

**Goals:**

- install.sh 与 aria 机制保持行为一致（clone 位置、三层软链、冲突保护、ff-only 更新、镜像轮换）
- 全流程幂等：重复安装无副作用；卸载可完整还原托管条目
- 不触碰用户文件；所有破坏性操作仅限精确识别的托管软链与 `--delete-repo` 显式指定的仓库目录
- 文档与新机制一致：README.md、readmes/ 7 份、开发者知识文档

**Non-Goals:**

- 不支持 Windows 原生（无 .bat；Windows 用户经 WSL/Git Bash，文档说明即可）
- 不做离线安装模式、不保留直连 GitHub 兜底
- 不改动 cadence-init 插件内容、pre-check 运行时工具安装及任何既有 skill 行为
- 不自动清理旧 marketplace 残留（仅提示）

## Decisions

- **单文件 install.sh，set -euo pipefail**：与 aria 的内嵌 Rust 步骤不同，独立脚本需要自包含与可审计；备选（安装器二进制、Makefile）复杂度不成比例。
- **镜像顺序与 aria 完全一致，无直连兜底**：用户明确要求镜像优先且不直连（aria 行为：ghfast.top → gh-proxy.com → mirror.ghproxy.com，全失败报错）。
- **非 git 目录 → 提醒删除后重装**：偏离 aria 的 Offline 分支（用户裁定该场景应提示处理，不做离线降级）；脚本不自动删除，避免破坏性动作。
- **更新分支解析用 origin 自适应而非 aria 的 upstream**：`git clone` 默认 remote 是 origin，aria 依赖 `upstream` 在新装环境必然落空（潜在 bug）；行为语义（拉最新 + ff-only + 镜像轮换）与 aria 一致。
- **三层软链，Kimi 无专用层**：`~/.agents/skills` 共享层已覆盖 pi/Codex/Kimi Code/kimi-cli；`~/.claude/skills` 与 `~/.codex/skills/skills` 为 Claude Code 与旧版 Codex 兼容层。与 aria 完全一致。
- **托管软链判定（F-2 修订：符号级所有权证明）**：前缀匹配不能证明所有权——`~/.agents/skills` 是 cadence 与 superpowers 等第三方安装器的共用命名空间，真机事故已证明前缀判定会误删合法第三方投影链。改用 readlink 精确比对：共享层条目仅当直指 `仓库/cadence-init/skills/<name>` 才算托管；Claude/Codex 层仅当直指 `~/.agents/skills/<name>` 且该共享层条目本身通过所有权证明才算托管；孤儿清理先在共享层算待清集合再清下游两层；无法证明所有权的链（含 dangling 第三方链）只告警不删；`--uninstall` 复用同一谓词。替换用临时软链 + `mv -T` 原子操作。
- **--dry-run（plan/execute 拆分）**：同步/清理逻辑拆为"计算动作计划"与"执行计划"两阶段，dry-run 只输出计划不落盘，也不执行网络拉取；同时服务真机预览与 CI 断言面。
- **文档重写以 scout 差异清单为基线**：根 README 全新结构；readmes/ 7 份统一裸 skill 名调用并补齐 14 skill 清单；知识文档放 `cadence/readmes/`（遵循 document-storage 规则的开发者文档路径）。

## Risks / Trade-offs

- [Kimi 对 skills 目录内 symlink 条目的跟随行为无官方文档] → 发布门禁中加入 Kimi Code 真实扫描验证；本机 `~/.agents/skills` 已有同构软链长期可用作旁证。
- [Claude Code 对 `~/.claude/skills` 根目录级 symlink 曾有版本回归（#38051）] → 本方案只在 skill 子目录级建链，不链接根目录本身。
- [镜像源为第三方加速服务，存在供应链信任风险] → 与 aria 保持同一镜像集合（用户已确认接受）；脚本输出所用镜像地址供审计。
- [真机事故 F-2：前缀判定误删合法第三方投影链] → 所有权证明谓词（install 与 uninstall 共用）+ 第三方形状回归 fixture + --dry-run 预览；真机重验前先 dry-run 人工核对。
- [dry-run 与实装间存在 TOCTOU 窗口（用户期间手动改链）] → 可接受；实装输出与 dry-run 计划 diff 应为空的验收口径不变。
- [所有权证明使历史遗留、语义已漂移的旧链不可自动清理] → 接受：此类链只告警 + 手动命令，符合"正被使用的机器零意外"目标。
- [旧用户残留的 marketplace 安装与本安装并存可能造成重复 skill] → 残留检测提示 + 文档迁移章节给出清理命令。
- [ff-only 更新遇上游强推会失败] → 报错并提示删除仓库重新安装的恢复路径。

## Migration Plan

1. 合入后新用户直接 `curl/clone + install.sh` 安装。
2. 旧用户按 README 迁移章节：运行新 install.sh → 按提示手动清理 `~/.claude/plugins/marketplaces/cadence-skills-local` 与 `known_marketplaces.json` 残留键。
3. 回滚：`git revert` 后旧脚本自 git 历史恢复；已装软链可用 `--uninstall` 清除。

## Open Questions

（无）
