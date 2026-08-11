## ADDED Requirements

### Requirement: 无价值旧文档必须直接删除

系统 MUST 删除 `cadence/docs/` 下全部 15 份文档（14 份 2026 年 3 月文档及 2026 年 2 月的《AI 自动化开发环境配置系统设计方案》）和 `cadence/analysis/` 下全部 3 份 2026 年 3 月文档，删除 MUST 使用 `git rm`；删除后 MUST 移除空的 `cadence/analysis/` 目录。被删除文档 MUST NOT 复制到 `cadence/archive/`。

#### Scenario: 删除旧文档

- **WHEN** 执行清理工作包
- **THEN** `cadence/docs/` 15 份与 `cadence/analysis/` 3 份共 18 份文档通过 `git rm` 移除
- **AND** `cadence/analysis/` 目录不复存在
- **AND** `cadence/archive/` 中不存在这 18 份文档的任何副本

### Requirement: 历史产物必须按镜像结构归档并建立索引

系统 MUST 新建 `cadence/archive/`，将被归档文档按原分类移入 `archive/plans/`、`archive/designs/`、`archive/analysis-docs/`、`archive/designs-reviews/`、`archive/prds/`，移动 MUST 使用 `git mv` 且文件名保持不变。系统 MUST 生成 `cadence/archive/INDEX.md`，逐条记录每份归档文档的文件名、原路径、归档日期和关联工作（OpenSpec change 或 PR 号，无法确认时标注"未知"）。

#### Scenario: 归档已完成历史产物

- **WHEN** 执行归档工作包
- **THEN** 归档文档出现在与原分类对应的 `cadence/archive/` 子目录中
- **AND** 原位置不再存在这些文件
- **AND** `INDEX.md` 条目数与实际归档文件数一致

### Requirement: 全部计划文档必须随关联交付工作一并归档

计划文档的勾选框是执行痕迹，不作为完成判据。系统 MUST 以关联工作已交付（对应 OpenSpec change 已归档或对应 PR 已合并）作为归档判据，将 `cadence/plans/` 下全部 26 份计划文档归档；MUST NOT 仅因文档内存在未勾选框（`- [ ]`）而保留任何计划文档。

#### Scenario: 计划文档存在未勾选步骤但工作已交付

- **WHEN** 某计划文档含未勾选框，但其关联的 OpenSpec change 已归档或对应 PR 已合并
- **THEN** 该文档照常归档到 `cadence/archive/plans/`
- **AND** 交付报告记录该判据依据

### Requirement: 已完成的 OpenSpec change 必须完成标准归档

系统 MUST 将 `openspec/changes/improve-progressive-disclosure-routing/` 移入 `openspec/changes/archive/2026-07-20-improve-progressive-disclosure-routing/`，并 MUST 将其 3 份 capability spec 的 requirements 落地到 `openspec/specs/managed-rule-lifecycle/`、`openspec/specs/progressive-context-routing/`、`openspec/specs/routing-conformance/`。CLI 可用时 SHALL 优先使用 `openspec archive` 完成；CLI 不可用时 MUST 手动执行等价操作。

#### Scenario: 归档已完成的 change

- **WHEN** 执行 OpenSpec 归档工作包
- **THEN** 活跃 changes 下不再存在 `improve-progressive-disclosure-routing/`
- **AND** archive 下存在带日期前缀的完整 change 目录
- **AND** `openspec/specs/` 下 3 个 capability 目录各包含对应 spec.md

### Requirement: 迁移前后必须完成引用扫描

系统 MUST 在迁移前扫描全仓（排除 `.git/`、`.worktrees/` 与被迁移文件自身）中所有被移动/删除文件的文件名引用并形成基线；迁移后 MUST 复扫，残留活引用 MUST 修复为新路径或移除失效引用。引用位于 `.claude/rules/` 框架规则文件时 MUST NOT 直接修改，MUST 报告用户裁决。

#### Scenario: 迁移后发现残留活引用

- **WHEN** 迁移后复扫发现非框架规则文件仍引用旧路径
- **THEN** 引用被更新为 `cadence/archive/` 下的新路径或被移除
- **AND** 最终扫描结果中不存在指向已删除文档的引用

### Requirement: 交付必须附核对清单

系统 MUST 在完工前输出核对清单，逐项列出：删除文件数（预期 18）、归档文件数（预期 45：plans 26、designs 13、analysis-docs 4、designs-reviews 1、prds 1）与 INDEX 条目数、specs 落地数（预期 3）、引用扫描结果；任何一项与预期不符时 MUST NOT 声称完成。

#### Scenario: 核对清单与预期不符

- **WHEN** 删除数、归档数或 specs 落地数与预期不一致
- **THEN** 停止完工声明
- **AND** 报告差异项并修复后重新核对
