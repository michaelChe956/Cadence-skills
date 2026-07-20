---
name: design-to-implementation
description: Use when implementing design documents for pure documentation projects, especially when designs contain code examples that need to be converted to skill documentation
---

# Design to Implementation - 纯文档项目的设计方案实施指南

## 概述

**核心原则**：识别设计方案的文档部分和代码部分，根据项目类型（纯文档项目 vs 代码项目）调整实施策略，将代码实现转化为Skill执行步骤。

**关键洞察**：设计方案通常包含伪代码、函数示例、脚本实现，但Skills项目是纯文档项目（CLAUDE.md规定："非必要不编写代码"），需要将"代码实现"转化为"执行步骤描述"。

## 何时使用

**使用场景**：
- 设计文档包含Python/JavaScript代码示例
- 方案描述了验证函数、清理脚本、迁移工具
- 不确定是否需要编写代码实现
- 需要将"设计意图"转化为"可执行步骤"

**不使用场景**：
- 设计文档已经是纯文档形式
- 方案只需要创建Markdown文档
- 明确知道不需要代码实现

## 识别项目类型

### 纯文档项目特征

✅ **是纯文档项目**，如果：
- 主要内容是Markdown文档（SKILL.md、README.md）
- 工作方式是描述执行流程
- Agent按照步骤执行，不需要实际代码
- 数据存储在Serena memory（YAML/JSON格式）
- 工具是其他Skills（通过调用完成功能）

❌ **不是纯文档项目**，如果：
- 需要编写可执行脚本（.py、.js、.sh）
- 需要实现业务逻辑函数
- 需要创建工具类或库
- 需要部署可运行的应用程序

### Cadence-skills 项目性质

**项目类型**：✅ **纯文档项目**

**证据**：
- 主要内容：16个Skills（SKILL.md）
- 工作方式：描述流程步骤，Claude Code Agent执行
- 数据存储：Serena memory（YAML格式）
- 工具实现：通过调用其他Skills完成功能
- **CLAUDE.md明确指出**："非必要不编写代码"

## 转化流程

### Step 1: 分析设计方案结构

**读取设计文档**：
```markdown
1. 读取设计方案文档（.claude/docs/*.md）
2. 识别文档结构：
   - 问题描述
   - 解决方案
   - 数据模型
   - 实现逻辑（代码示例）
   - 验证标准
```

**识别内容类型**：
```markdown
方案内容分类：
- ✅ 文档部分：流程描述、数据模型、验证规则、使用场景
- ⚠️ 代码部分：验证函数、清理脚本、迁移工具、辅助函数
```

### Step 2: 分离文档和代码部分

**创建分类表**：

| 设计内容 | 类型 | 实施方式 |
|---------|------|---------|
| **数据模型**（YAML结构） | 文档 | ✅ 直接使用 |
| **验证规则**（JSON Schema） | 文档 | ✅ 直接使用 |
| **执行流程**（步骤描述） | 文档 | ✅ 直接使用 |
| **验证函数**（Python代码） | 代码 | ⚠️ 需要转化 |
| **清理脚本**（Bash命令） | 代码 | ⚠️ 需要转化 |
| **迁移工具**（函数实现） | 代码 | ⚠️ 需要转化 |

### Step 3: 确定转化策略

#### 策略A：纯文档实施（推荐）

**适用**：纯文档项目（如Cadence-skills）

**转化方式**：
```markdown
## 代码 → 工具Skill

将"验证函数"转化为"验证工具Skill"：
- ❌ 不是：def validate_data(data): ...
- ✅ 而是：创建 skills/data-validation/SKILL.md
  - 描述验证步骤（Step 1-7）
  - 定义验证规则（表格形式）
  - 提供验证检查清单

## 脚本 → 流程描述

将"清理脚本"转化为"清理流程"：
- ❌ 不是：cleanup.sh 脚本
- ✅ 而是：skills/data-cleanup/SKILL.md
  - Step 1: 扫描数据
  - Step 2: 识别过期数据
  - Step 3: 执行清理
  - Step 4: 更新索引

## 函数 → 调用指令

将"迁移函数"转化为"迁移Skill"：
- ❌ 不是：migrate_progress_1_0_to_1_1() 函数
- ✅ 而是：skills/version-migration/SKILL.md
  - 检测版本
  - 确定迁移路径
  - 执行迁移步骤
  - 验证结果
```

#### 策略B：混合实施（不推荐）

**适用**：需要辅助脚本的项目

**转化方式**：
```markdown
## 必须编写代码时

1. 向用户说明理由：
   - 为什么必须用代码
   - 代码的作用和必要性
   - 无法用纯文档替代的原因

2. 考虑替代方案：
   - 是否可以通过现有工具完成？
   - 是否可以通过配置文件完成？
   - 是否可以通过命令行完成？

3. 最小化代码量：
   - 只编写必要的脚本
   - 优先使用现有工具
   - 代码作为辅助工具，不是主要工作
```

### Step 4: 创建工具Skills（纯文档方式）

**模板**：
```markdown
---
name: {tool-name}
description: Use when {triggering conditions}
---

# {Tool Name} - {Purpose}

## 概述
核心原则（1-2句话）

## 何时使用
- 使用场景
- 不使用场景

## 执行流程

### Step 1: {第一步}
描述做什么，如何做

### Step 2: {第二步}
描述做什么，如何做

...

### Step N: {最后一步}
描述做什么，如何做

## 快速参考
| 操作 | 说明 |
|------|------|
| ... | ... |

## 常见错误
- 错误1：... → 如何避免
- 错误2：... → 如何避免
```

### Step 5: 集成到现有Skills

**添加调用指令**：
```markdown
## 在现有Skill中引用工具Skill

### 示例：checkpoint skill

**原流程**：
Step 1-3: 收集数据
Step 4: 保存数据

**修改后**：
Step 1-3: 收集数据
Step 3.5: 🔴 验证数据（调用data-validation skill）
Step 4: 保存数据

**关键**：
- 使用明确的触发指令
- 添加🔴 CRITICAL标记
- 说明为什么必须调用
- 确保不会被遗忘
```

## 实施案例：方案4（数据管理层）

### 原设计方案分析

**来源**：`cadence/docs/2026-03-05_设计文档_数据管理系统_v1.0.md`（该文档已于 2026-07-20 清理中删除，可经 git 历史查阅）

**内容结构**：
```yaml
设计方案:
  数据验证机制:
    - JSON Schema定义（✅ 文档）
    - 验证流程描述（✅ 文档）
    - validate_progress_data() 函数（⚠️ 代码）
    - validate_checkpoint_data() 函数（⚠️ 代码）

  数据清理策略:
    - 生命周期管理（✅ 文档）
    - 清理流程描述（✅ 文档）
    - cleanup_checkpoint() 脚本（⚠️ 代码）

  版本管理机制:
    - 版本标识规范（✅ 文档）
    - 迁移流程描述（✅ 文档）
    - migrate_progress() 函数（⚠️ 代码）
```

### 转化决策

**项目类型判断**：
- ✅ Cadence-skills 是纯文档项目
- ✅ 主要工作是创建SKILL.md
- ✅ 不需要Python/JavaScript实现

**转化策略**：
- 选择 **策略A：纯文档实施**
- 将代码部分转化为工具Skills
- 保留文档部分作为Skill内容

### 实施步骤

#### 步骤1：创建数据验证工具Skill

**转化方式**：
```markdown
## 原设计（代码）
```python
def validate_progress_data(progress_data):
    errors = []
    # 检查必填字段
    required_fields = [...]
    for field_path in required_fields:
        if not has_field(progress_data, field_path):
            errors.append(f"缺少必填字段: {field_path}")
    # ...
    return {"valid": len(errors) == 0, "errors": errors}
```

## 转化后（文档）
skills/data-validation/SKILL.md:
- Step 1: 识别数据类型（Progress/Checkpoint）
- Step 2: 验证必填字段（表格列出所有字段）
- Step 3: 验证字段类型（表格列出类型规则）
- Step 4: 验证值范围（表格列出有效范围）
- Step 5: 验证枚举值（列出所有有效值）
- Step 6: 验证UUID格式（Checkpoint专用）
- Step 7: 所有验证通过
```

#### 步骤2：创建数据清理工具Skill

**转化方式**：
```markdown
## 原设计（代码）
```bash
#!/bin/bash
# cleanup.sh
find checkpoints -mtime +30 -exec rm {} \;
```

## 转化后（文档）
skills/data-cleanup/SKILL.md:
- Step 1: 扫描数据清单（list_memories）
- Step 2: 识别归档数据（7-30天）
- Step 3: 识别删除数据（>30天）
- Step 4: 执行归档（重命名为archive-*）
- Step 5: 执行删除（delete_memory）
- Step 6: 更新索引（清理过期条目）
- Step 7: 生成清理报告
```

#### 步骤3：创建版本迁移工具Skill

**转化方式**：
```markdown
## 原设计（代码）
```python
def migrate_progress_1_0_to_1_1(progress_data):
    progress_data["time_stats"] = {"total_time": 0, "estimated_remaining": 0}
    progress_data["metadata"]["version"] = "1.1"
    return progress_data
```

## 转化后（文档）
skills/version-migration/SKILL.md:
- Step 1: 读取数据版本（metadata.version）
- Step 2: 创建备份（backup-{name}-{timestamp}）
- Step 3: 确定迁移路径（1.0 → 1.1）
- Step 4: 执行迁移（添加字段、更新版本）
- Step 5: 验证迁移数据（调用data-validation）
- Step 6: 保存迁移数据（write_memory）
- Step 7: 失败时回滚（从备份恢复）
```

#### 步骤4：集成到现有Skills

**修改checkpoint skill**：
```markdown
## 添加验证步骤

原流程：
Step 1-3: 收集数据
Step 4: 保存数据

新流程：
Step 1-3: 收集数据
Step 3.5: 🔴 验证数据（REQUIRED）
  → 调用 data-validation skill
  → 验证失败则停止
Step 4: 保存数据
```

**修改status skill**：
```markdown
## 添加迁移和验证步骤

原流程：
Step 1: 收集项目信息
Step 2: 读取Progress数据

新流程：
Step 1: 收集项目信息
Step 2: 读取Progress数据
Step 2.5: 🔴 自动迁移和验证（REQUIRED）
  → 调用 version-migration skill（自动升级）
  → 调用 data-validation skill（验证格式）
Step 3: 计算进度
```

**修改resume skill**：
```markdown
## 添加Checkpoint迁移步骤

原流程：
Step 4: 读取最新Checkpoint

新流程：
Step 4: 读取最新Checkpoint
Step 4.5: 🔴 自动迁移Checkpoint（REQUIRED）
  → 调用 version-migration skill
  → 调用 data-validation skill
Step 5: 重建上下文
```

### 实施成果

**创建的文件**：
```
skills/
├── data-validation/SKILL.md       ✅ 工具Skill（纯文档）
├── data-cleanup/SKILL.md          ✅ 工具Skill（纯文档）
└── version-migration/SKILL.md     ✅ 工具Skill（纯文档）

commands/
├── data-validation.md             ✅ Command（简化格式）
├── data-cleanup.md                ✅ Command（支持--dry-run）
└── version-migration.md           ✅ Command（支持--dry-run）

readmes/skills/
├── data-validation.md             ✅ 详细使用指南
├── data-cleanup.md                ✅ 详细使用指南
└── version-migration.md           ✅ 详细使用指南
```

**修改的文件**：
```
skills/
├── checkpoint/SKILL.md            ✅ 添加Step 3.5验证
├── status/SKILL.md                ✅ 添加Step 2.5迁移和验证
└── resume/SKILL.md                ✅ 添加Step 4.5迁移和验证

README.md                           ✅ 添加"数据管理阶段"
```

**总工作量**：
- 创建13个文件（3个工具Skills + 3个Commands + 3个READMEs + 更新主README + 修改3个现有Skills）
- 全部为Markdown文档，**无代码实现**
- 工作量：1天（实际）

## 验证检查清单

### 方案可行性检查

**纯文档实施可行性**：
- [ ] 确认项目是纯文档项目（无代码实现需求）
- [ ] 确认工具功能可以通过Skill调用完成
- [ ] 确认数据操作可以通过Serena MCP完成
- [ ] 确认不需要可执行脚本

### 转化完整性检查

**文档部分保留**：
- [ ] 数据模型定义完整
- [ ] 验证规则清晰
- [ ] 执行流程描述详细
- [ ] 使用场景明确

**代码部分转化**：
- [ ] 函数转化为执行步骤
- [ ] 脚本转化为流程描述
- [ ] 工具转化为Skill调用
- [ ] 配置转化为表格/清单

### 集成完整性检查

**现有Skills修改**：
- [ ] 添加明确的调用指令
- [ ] 使用🔴 CRITICAL标记
- [ ] 说明为什么必须调用
- [ ] 确保不会被遗忘

**新Skills创建**：
- [ ] 符合SKILL.md结构
- [ ] 包含完整的执行流程
- [ ] 提供快速参考
- [ ] 包含常见错误

## 常见错误

### ❌ 错误1：直接实现代码

**问题**：看到设计方案中的函数就编写Python代码

```python
# ❌ 错误做法
def validate_progress_data(progress_data):
    # ... 实际代码实现
```

**正确做法**：转化为Skill文档
```markdown
# ✅ 正确做法
skills/data-validation/SKILL.md:
- Step 1: 识别数据类型
- Step 2: 验证必填字段
- ...
```

### ❌ 错误2：保留伪代码

**问题**：在Skill中保留设计方案的伪代码

```markdown
# ❌ 错误做法
## 验证逻辑
```python
def validate(data):
    errors = []
    # 检查字段...
```

**正确做法**：转化为执行步骤
```markdown
# ✅ 正确做法
## Step 2: 验证必填字段

**检查所有必填字段**：
1. 读取数据
2. 遍历必填字段列表
3. 检查每个字段是否存在
4. 记录缺失字段
```

### ❌ 错误3：隐式调用

**问题**：假设工具Skills会自动被调用

```markdown
# ❌ 错误做法
Step 4: 保存数据
（假设验证会自动发生）
```

**正确做法**：显式添加调用指令
```markdown
# ✅ 正确做法
Step 3.5: 🔴 验证数据（REQUIRED）

**必须调用**：data-validation skill

IF 验证失败:
  → 停止操作
  → 返回错误

IF 验证通过:
  → 继续Step 4
```

### ❌ 错误4：混合实施

**问题**：部分用文档，部分用代码

```markdown
# ❌ 错误做法
- 数据验证：创建Skill文档 ✅
- 数据清理：编写cleanup.sh脚本 ❌
- 版本迁移：编写migrate.py脚本 ❌
```

**正确做法**：统一使用纯文档方式
```markdown
# ✅ 正确做法
- 数据验证：创建Skill文档 ✅
- 数据清理：创建Skill文档 ✅
- 版本迁移：创建Skill文档 ✅
```

## 快速参考

| 设计内容 | 代码形式 | 文档形式（推荐） |
|---------|---------|-----------------|
| **验证函数** | `def validate(data)` | Skill: Step 1-N验证步骤 |
| **清理脚本** | `cleanup.sh` | Skill: Step 1-N清理流程 |
| **迁移工具** | `migrate.py` | Skill: Step 1-N迁移流程 |
| **辅助函数** | `helper.py` | Skill: 执行步骤描述 |
| **配置文件** | `config.yaml` | Skill: 表格/清单 |
| **数据模型** | `class Data` | Skill: YAML结构示例 |

## 实施建议

### 优先级判断

**高优先级**（P0）：
- 核心功能的工具Skills
- 被多个Skills调用的通用工具
- 数据质量保障工具

**中优先级**（P1）：
- 性能优化工具
- 辅助管理工具

**低优先级**（P2）：
- 可选的增强功能
- 未来可能需要的工具

### 工作量估算

**单个工具Skill**：
- 创建SKILL.md：1-2小时
- 创建Command：15分钟
- 创建README：30分钟
- 修改现有Skills：30分钟
- **总计**：2-3小时

**完整方案实施**（3个工具Skills）：
- 3个工具Skills：6-9小时
- 集成到现有Skills：1-2小时
- 测试验证：1-2小时
- **总计**：8-13小时（约1-2天）

## 总结

**核心洞察**：
1. **识别项目类型**：纯文档项目 vs 代码项目
2. **分离方案内容**：文档部分 + 代码部分
3. **转化代码为文档**：函数 → 步骤，脚本 → 流程
4. **显式集成调用**：确保工具Skills被使用
5. **全部Markdown**：无代码实现，纯文档工作

**成功标志**：
- ✅ 所有设计内容都有对应的Skill
- ✅ 无需编写Python/JavaScript代码
- ✅ 现有Skills显式调用工具Skills
- ✅ 功能完整可用
- ✅ 文档清晰易懂
