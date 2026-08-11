## Why

`cadence/` 与 `openspec/` 积累了 2026 年 3 月至 7 月的全部历史产物：3 月 cadencing 时期的 16 份文档已被后续迭代完全取代；约 40 份已完成的计划、设计、分析报告散落在主目录；`cadence/analysis/` 与标准路径 `cadence/analysis-docs/` 职能重叠；OpenSpec change `improve-progressive-disclosure-routing` 的 7 个工作包已全部完成且验收通过，但仍占用活跃 changes 空间，`openspec/specs/` 与 `openspec/changes/archive/` 为空。主目录噪音大，活跃产物与历史产物混杂，不利于后续工作定位。

## What Changes

- 直接删除 `cadence/docs/` 下全部 15 份文档（14 份 2026 年 3 月旧文档及 2026 年 2 月的《AI 自动化开发环境配置系统设计方案》）和 `cadence/analysis/` 下 3 份 2026 年 3 月旧文档，并移除空的 `cadence/analysis/` 目录（用户已确认无保留价值，git 历史可追溯）。
- 新建 `cadence/archive/`，按原分类镜像归档全部历史产物共 45 份（plans 26、designs 13、analysis-docs 4、designs-reviews 1、prds 1），并生成 `INDEX.md` 记录原名、原路径、归档日期与关联工作。
- 计划文档归档判据为关联工作已交付（对应 OpenSpec change 已归档或 PR 已合并），文档内未勾选框仅为执行痕迹，不阻止归档。
- 将已完成的 change `improve-progressive-disclosure-routing` 移入 `openspec/changes/archive/2026-07-20-improve-progressive-disclosure-routing/`，其 3 份 capability spec 合并落地到 `openspec/specs/`。
- 全仓扫描被移动/删除文件的文件名引用，发现活引用则修复或回滚对应移动。
- 所有文件移动使用 `git mv` 保留历史。

## Capabilities

### New Capabilities

- `document-archive`: 定义 cadence 历史产物的归档目录结构、INDEX 索引要求、删除与归档的判定边界、归档前完成状态检查和引用扫描验证。

### Modified Capabilities

无。本 change 不修改已有 capability 行为；`improve-progressive-disclosure-routing` 的 specs 按 OpenSpec 标准归档流程落地到 `openspec/specs/`，内容不变。

## Impact

- 影响 `cadence/` 下 docs、analysis、analysis-docs、designs、designs-reviews、plans、prds 共 7 个目录 63 份文档（18 份删除、45 份归档）的位置或存续。
- 影响 `openspec/changes/` 与 `openspec/specs/` 的结构。
- 新增 `cadence/archive/` 目录及其 `INDEX.md`。
- 不改动 `readmes/`、`.claude/`、`cadence/project-rules/`、`cadence-init/` 及任何 Skill 正文；如引用扫描发现上述位置存在活引用，只修复引用本身。
