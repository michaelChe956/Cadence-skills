## 1. 备份机制重构

- [x] 1.1 重构 `backup_file` 为复制原文件到 `cadence/legacy/<时间戳[-N]>/<相对路径>`（`shutil.copy2`，原位不动），保留同秒 `-N` 目录后缀唯一性
- [x] 1.2 在 `cadence/legacy/` 首次创建及每次运行前验证/修复 `.gitignore`（内容 `*` 换行 `!.gitignore`）
- [x] 1.3 适配 L0 双入口屏障（§11.2）：两入口先全部复制归档、全部成功后才依次 `atomic_write` 覆盖；任一归档失败不写入任一入口；`atomic_write` 失败原文件不变
- [x] 1.4 适配 OS config.yaml、L1 备份分支为复制归档 + 原子覆盖，保留"归档失败即终止不写入"语义

## 2. 框架规则文件权威全覆盖

- [x] 2.1 S3 规则文件步骤新增全覆盖分支：内容==模板则跳过，否则复制归档+`atomic_write` 模板，不调用 `merge_markdown`
- [x] 2.2 收窄 `merge_markdown` 适用范围，使其不再用于框架受管规则文件（保留入口/OS 各自语义）
- [x] 2.3 遗留 `code-usage-coding.md`/`code-usage-noncoding.md` 归档到 `cadence/legacy/` 后从 `.claude/rules/` 移除（归档失败则不移除）

## 3. code-usage 按类型单选

- [x] 3.1 `ORDINARY_RULE_FILES` 移除两个 `code-usage-*.md` 与 `agent-routing-kernel.md`，新增按 `project_type` 单选来源映射、落地名恒为 `code-usage.md`
- [x] 3.2 项目类型变化时归档原文件 + 以当前类型模板原子覆盖（不合并互斥内容）
- [x] 3.3 验证 L0 规范源与 `RULE2_TEXT_*` 对 `code-usage.md` 的引用不再悬空

## 4. 连带 bug 修复

- [x] 4.1 `_ensure_summary_lines` 缺失判据改为"章节内是否已存在指向该规则文件名的引用"（无论措辞，指向同一文件名即视为已存在）；规则 6 多行块按首行存在性判断
- [x] 4.2 `_ensure_techstack_block` 改为逐项判断：占位集合固定 `{"待确认","未检测到"}`，空值视为占位；占位替换为检测值，非占位真实值保留，区块缺失则追加

## 5. 语义层与文档同步

- [x] 5.1 `merge-semantics.md`：NC-02/NC-03 适用范围收窄、RF 表新增框架权威全覆盖行、SM 表摘要判据改写、§11.1/§11.2 备份命名与屏障改写为 `cadence/legacy/` 复制归档 + 原子覆盖
- [x] 5.2 `SKILL.md` 概述与合并语义引用同步更新
- [x] 5.3 模板 `references/rules/README.md` 修正 `agent-routing-kernel.md` 描述与受管清单一致性

## 6. 测试与对账

- [x] 6.1 `test_rule_config.py` 新增/改写：全覆盖幂等、code-usage 单选与类型切换、摘要不重复追加、技术栈占位替换与用户值保留、`cadence/legacy/` 归档与 `.gitignore`、归档失败终止
- [x] 6.2 跨资产失败关闭测试拆解：L0 双入口部分归档失败（第二个归档失败时第一个入口不动）、L0 `atomic_write` 失败原文件不变、OS 发布失败恢复、L1 归档+写入失败恢复、归档同秒 `-N` 冲突、`.gitignore` 损坏修复、code-usage 历史文件归档成功但移除失败时原文件保持原样
- [x] 6.3 幂等回归矩阵：连续两次 apply 全部受管产物逐字一致且 `cadence/legacy/` 无新归档；drift->覆盖->重跑不归档；type switch->重跑稳定；摘要不同措辞同引用不重复追加
- [x] 6.4 dry-run JSON 计划测试：no-interrupt 框架规则文件 drift 冲突条目含 `no_interrupt_action: "authoritative-overwrite"`；普通模式冲突条目不含该字段
- [x] 6.4 `skill-clause-map.md` 逐行对账新增/改写条款的测试 ID
- [x] 6.5 `openspec validate --strict` 通过，人工核对 naruto 场景下新设计不再产生 Serena 复活与摘要重复
</content>
