# 实施计划：Legacy-Bootstrap Skill v2.0 重构

> 基于设计文档：`cadence/designs/2026-05-27_方案设计_legacy-bootstrap-skill重构_v2.0.md`
> 目标文件：`cadence-init/skills/legacy-bootstrap/SKILL.md`

## 概述

重写 `SKILL.md`，将现有松散的"分析后批量输出"流程改为**类型驱动的产物管线**。同时更新 command 入口文件以反映新能力。

## 任务分解

### Task 1: 重写 SKILL.md — Phase 1 & 2（环境检测 + 类型识别）

**文件**: `cadence-init/skills/legacy-bootstrap/SKILL.md`

**改动内容**:
- 保留 frontmatter 和概述/核心原则/何时使用/不使用场景（微调措辞）
- 重写"处理流程"部分的 Step 1-4，新增 Phase 2"项目类型识别"
- 新增"项目类型识别规则"章节，包含 6 种类型的检测信号表
- 新增"组合规则"和"用户确认"子节

**验收标准**:
- 6 种项目类型及其检测信号完整列出
- 组合类型取并集规则明确
- 用户确认步骤存在

---

### Task 2: 重写 SKILL.md — 产物清单章节

**文件**: `cadence-init/skills/legacy-bootstrap/SKILL.md`

**改动内容**:
- 替换现有"标准模式候选产物"和"深度模式额外候选产物"表格
- 新增 5.1-5.6 六个子节：核心产物(8) + 前端(4) + 后端单体(3) + 微服务(2) + CLI(2) + DevOps(2)
- 每个产物包含：编号、名称、路径模板、内容要求
- 明确"核心产物所有类型必选"的规则

**验收标准**:
- 21 个产物全部列出，路径和内容要求完整
- 产物与类型的映射关系清晰

---

### Task 3: 重写 SKILL.md — 执行保障机制

**文件**: `cadence-init/skills/legacy-bootstrap/SKILL.md`

**改动内容**:
- 新增"逐产物生成协议"章节（提取→写入→确认三步）
- 新增状态报告格式示例
- 新增"收尾验证"章节（磁盘检查 + 非空验证 + 重试 + 汇总表）
- 新增"禁止行为"清单（4 条红线）

**验收标准**:
- 三步协议明确
- 状态报告格式有示例
- 禁止行为 4 条完整

---

### Task 4: 重写 SKILL.md — 深度模式 + 入口文档更新

**文件**: `cadence-init/skills/legacy-bootstrap/SKILL.md`

**改动内容**:
- 重写"执行模式"章节，明确标准/深度的区别（系统级 vs 模块级）
- 深度模式触发建议：repomix > 200k tokens 或文件数 > 100
- 重写"更新入口文档"章节，按"首选入口→修改前必读→类型专属"分层
- 更新完成标准和 bootstrap 摘要输出格式（含汇总表）

**验收标准**:
- 标准/深度模式对比表存在
- 模式选择逻辑明确
- 入口文档模板按新分层结构

---

### Task 5: 更新 command 入口文件

**文件**: `cadence-init/commands/legacy-bootstrap.md`

**改动内容**:
- 功能描述中新增"项目类型识别"步骤
- 输出部分新增类型专属产物说明
- 约束部分新增"逐产物生成，禁止合并"

**验收标准**:
- command 文件与 SKILL.md 新流程一致
- 用户能从 command 文件了解新增的类型驱动能力

---

### Task 6: 最终验证

**动作**:
- 通读完整 SKILL.md，确认无内部矛盾
- 确认所有产物路径符合 `cadence/` 文档存储规则
- 确认 Markdown 格式正确（嵌套代码块用 4/3 反引号）
- 提交所有改动

**验收标准**:
- SKILL.md 无 TBD/TODO 占位符
- 路径命名符合 `YYYY-MM-DD_类型_名称_v版本.md` 格式
- Git commit 成功

## 执行顺序

```
Task 1 → Task 2 → Task 3 → Task 4 → Task 5 → Task 6
```

所有 Task 串行执行，因为后续 Task 依赖前序 Task 写入的内容。

## 风险

| 风险 | 缓解 |
|------|------|
| SKILL.md 过长导致 AI 执行时截断 | 使用清晰的层级结构和表格，避免冗余描述 |
| 新旧 SOP 混淆 | 完全替换，不保留旧流程片段 |
