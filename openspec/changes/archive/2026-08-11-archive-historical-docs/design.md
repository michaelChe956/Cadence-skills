## Context

仓库是文档型 Skills 项目，`cadence/` 是全部过程产物的存放地，`openspec/` 是契约层。两者均未建立历史产物的退出机制：已完成的计划、设计、报告与活跃内容混放，`openspec/specs/` 从未接收过已归档 change 的 spec。本设计记录用户在 brainstorming 中已确认的清理与归档决策。

## Goals / Non-Goals

- Goals：主目录只保留活跃内容；历史产物可追溯（archive + INDEX + git 历史）；OpenSpec 完成标准归档闭环。
- Non-Goals：不评判或改写任何文档内容；不调整 `.claude/rules/` 框架规则与 Skill 正文；不建立持续性的归档自动化（本次为一次性整理，归档约定可日后再规则化）。

## Decisions

### 1. 删除与归档的判定边界

- 删除：`cadence/docs/` 全部 15 份（14 份 2026 年 3 月文档及 2026 年 2 月的《AI 自动化开发环境配置系统设计方案》）与 `cadence/analysis/` 3 份 2026 年 3 月文档，共 18 份。用户明确判定无保留价值；git 历史提供兜底追溯。
- 归档：其余全部历史产物共 45 份。用户选择"归档不删除"，保留仓库内直接可读的历史。
- 备选方案（已否决）：全部归档含 3 月文档——用户明确选择删除；只删不整——主目录仍然混杂，达不到目标。

### 2. 归档结构：`cadence/archive/<原分类>/`

镜像原目录分类（`plans/`、`designs/`、`analysis-docs/`、`designs-reviews/`、`prds/`），文件名保持不变。备选方案（已否决）：扁平单层 archive——40 份文档混放后无法区分类型；按月份分层——切割了同一工作的 plan/design/report 关联。

### 3. `INDEX.md` 作为可追溯入口

`cadence/archive/INDEX.md` 逐行记录：文件名、原路径、归档日期（2026-07-20）、关联工作（OpenSpec change 或 PR 号，未知则标注）。没有索引的 archive 等于第二个杂物堆。

### 4. 计划文档归档判据：关联工作已交付

初版契约以计划文档勾选状态为完成判据，勘察证据已将其证伪：16 份计划含未勾选步骤（如 2026-07-20 路由实施计划 50 个未勾选步骤），但对应 OpenSpec change tasks 全部完成、PR #69 已合并。勾选框是执行痕迹而非完成判据。经用户确认，判据改为关联工作已交付（对应 OpenSpec change 已归档或对应 PR 已合并），26 份计划全部归档。

### 5. OpenSpec 归档采用标准流程

优先使用 `openspec archive improve-progressive-disclosure-routing --yes`（CLI 可用时），自动完成移动与 specs 合并；CLI 不可用时手动执行等价操作：移动目录到 `openspec/changes/archive/2026-07-20-improve-progressive-disclosure-routing/`，并将 3 份 spec 的 requirements 按 `## ADDED Requirements` 语义写入 `openspec/specs/<capability>/spec.md`。

### 6. 引用扫描先行

迁移前对全仓（排除 `.git/`、`.worktrees/`、被迁移文件自身）扫描被移动/删除文件的文件名引用，形成引用基线；迁移后复扫，残留的活引用修复为 archive 新路径或删除失效引用。涉及 `.claude/rules/` 框架规则文件的引用不直接修改，报告给用户裁决。

### 7. `git mv` 保留历史

全部移动操作使用 `git mv`；删除使用 `git rm`。不使用普通 `mv`/`rm`，保证 `git log --follow` 可追溯。

## Risks / Trade-offs

- 误删仍有隐性价值的 3 月文档 → 用户已显式确认删除，且 git 历史可恢复。
- 归档后外部（其他仓库、笔记）引用失效 → 本仓引用扫描覆盖仓内；仓外引用不在可控范围，INDEX.md 提供查找入口。
- `openspec` CLI 不存在或版本不符 → 降级为手动等价操作，并在验证阶段用 `openspec validate --strict`（可用时）兜底。
