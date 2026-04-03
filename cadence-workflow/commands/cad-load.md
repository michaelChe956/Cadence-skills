# /cad-load - Cadence 项目上下文加载

快速加载 Cadence 项目上下文，激活工作区，准备开发工作。

## 使用方法

```bash
/cad-load [--quick|--full] [--checkpoint <name>]
```

## 参数说明

| 参数 | 说明 | 示例 |
|------|------|------|
| `--quick` | 快速加载（只加载 P0 记忆，5-10秒） | `/cad-load --quick` |
| `--full` | 完整加载（加载所有相关记忆，30-60秒） | `/cad-load --full` |
| `--checkpoint <name>` | 加载特定检查点 | `/cad-load --checkpoint checkpoint-2026-03-02-scheme6-complete` |
| 无参数 | 标准加载（加载 4-6 个关键记忆，15-30秒） | `/cad-load` |

## 功能说明

### 核心功能

1. **激活 Serena MCP 项目** - 建立项目连接
2. **加载关键记忆** - 恢复项目上下文
3. **检查 Git 状态** - 确认当前分支和提交
4. **建立会话上下文** - 保存会话记录

### 加载的记忆

#### P0 优先级（必须加载）
- `project_overview` - 项目概述、技术栈、关键规则
- `progress/cadence-skills-v2.4-mvp` - 当前进度、已完成方案

#### P1 优先级（标准加载）
- 最新 `checkpoint-*` - 最新检查点
- 最新 `sessions/*` - 最新会话记录

#### P2 优先级（完整加载）
- `patterns/*` - 项目模式和最佳实践
- `style_conventions` - 代码风格约定
- 其他项目记忆

## 使用示例

### 示例1：标准加载（推荐）

```bash
/cad-load
```

**输出**:
```
✅ Cadence 项目上下文已加载

📦 项目信息：
- 项目名称：Cadence-skills
- 当前版本：v2.4 MVP
- 完成状态：100% (7/7 schemes)
- Git 分支：main
- 最新提交：95e29d5 - 增加claude规则

🎯 已完成内容：
- ✅ 8 个核心节点 Skills
- ✅ 3 个流程 Skills
- ✅ 9 个 Commands

💾 已加载记忆：
- project_overview（项目概述）
- progress/cadence-skills-v2.4-mvp（进度追踪）
- checkpoint-2026-03-02-scheme6-implementation-complete
- sessions/2026-03-02_scheme7_completion

🚀 会话已就绪，可以开始工作！
```

### 示例2：快速加载

```bash
/cad-load --quick
```

**输出**:
```
✅ 快速加载完成（耗时：8秒）

📦 项目信息：
- 项目名称：Cadence-skills
- 当前版本：v2.4 MVP
- Git 分支：main

💾 已加载记忆：
- project_overview ✓
- progress/cadence-skills-v2.4-mvp ✓

🚀 会话已就绪！
```

### 示例3：完整加载

```bash
/cad-load --full
```

**输出**:
```
✅ 完整加载完成（耗时：45秒）

📦 项目信息：
- 项目名称：Cadence-skills
- 当前版本：v2.4 MVP
- 完成状态：100% (7/7 schemes)
- Git 分支：main
- 最新提交：95e29d5

🎯 已完成内容：
- ✅ 8 个核心节点 Skills
- ✅ 3 个流程 Skills
- ✅ 9 个 Commands
- ✅ 3 个 Subagent Prompts

💾 已加载记忆（12个）：
- project_overview ✓
- progress/cadence-skills-v2.4-mvp ✓
- checkpoint-2026-03-02-scheme6-complete ✓
- checkpoint-2026-03-02-scheme5-complete ✓
- sessions/2026-03-02_scheme7_completion ✓
- sessions/2026-03-02_scheme6_completion ✓
- patterns/claude-code-skills-specification ✓
- patterns/global-verification-technique ✓
- style_conventions ✓
- subagent-calling-pattern ✓
- tech-stack-detection-simplified ✓
- error-recovery-mechanism ✓

🚀 会话已就绪，具备完整上下文！
```

### 示例4：加载特定检查点

```bash
/cad-load --checkpoint checkpoint-2026-03-01-scheme4-complete
```

**输出**:
```
✅ 已加载检查点：方案4实施完成

📅 检查点信息：
- 创建时间：2026-03-01
- Git 提交：50da68d
- 状态：方案4已完成，方案5待开始

📊 当前进度：
- 设计进度：4/7 (57%)
- 实施进度：4/7 (57%)

✅ 已完成：
- 方案1: 基础架构 + 配置 + Hooks
- 方案2: 元Skill + Init Skill
- 方案3: 质量保证Skills
- 方案4: 节点Skill第1组（探索阶段）

⏳ 待完成：
- 方案5: 节点Skill第2组（设计阶段）
- 方案6: 节点Skill第3组（开发阶段）
- 方案7: 流程Skill + 进度追踪

💡 下一步：开始方案5设计

🚀 已恢复到方案4完成时的状态！
```

## 使用场景

### 场景1：新会话开始

```bash
# 会话开始时立即加载
/cad-load

# 然后开始工作
/full-flow  # 开始完整开发流程
```

### 场景2：快速查看项目状态

```bash
# 快速加载查看状态
/cad-load --quick

# 查看详细进度
/status
```

### 场景3：恢复之前的工作

```bash
# 加载最新状态
/cad-load

# 恢复之前的工作
/resume
```

### 场景4：回到特定时间点

```bash
# 加载特定检查点
/cad-load --checkpoint checkpoint-2026-03-01-scheme4-complete

# 从这个点继续工作
```

## 注意事项

### ✅ 推荐做法

- **会话开始时立即使用** - 建立完整的上下文
- **根据需求选择模式** - 简单任务用 `--quick`，复杂任务用 `--full`
- **定期检查项目状态** - 使用 `/status` 查看详细进度
- **结合进度追踪使用** - `/cad-load` → `/status` → `/resume`

### ❌ 避免的做法

- **跳过加载直接工作** - 可能缺少重要上下文
- **忽略错误信息** - 可能导致后续工作失败
- **不检查 Git 状态** - 可能在错误的分支上工作

## 相关命令

| 命令 | 说明 | 关系 |
|------|------|------|
| `/status` | 查看详细进度 | 依赖 `cad-load` 加载的记忆 |
| `/resume` | 恢复之前的工作 | 依赖 `cad-load` 激活的项目 |
| `/checkpoint` | 创建检查点 | 依赖 `cad-load` 的 Serena 连接 |
| `/report` | 生成报告 | 依赖 `cad-load` 的项目上下文 |

## 性能优化

| 加载模式 | 加载记忆数 | 时间范围 | 适用场景 |
|---------|-----------|---------|---------|
| `--quick` | 2个 | 5-10秒 | 简单查看、快速问答 |
| 标准 | 4-6个 | 15-30秒 | 日常开发、正常工作 |
| `--full` | 10+个 | 30-60秒 | 复杂任务、完整上下文 |

## 错误处理

### 常见错误

#### 错误1：Serena MCP 不可用

```
❌ 错误：Serena MCP 不可用

解决方案：
1. 检查 Serena MCP 是否已安装
2. 检查 Claude Code 配置
3. 重启 Claude Code
```

#### 错误2：项目未初始化

```
❌ 错误：项目未初始化（缺少 .serena 目录）

解决方案：
1. 确认当前目录是否是项目根目录
2. 运行项目初始化流程
```

#### 错误3：记忆不存在

```
⚠️ 警告：某些记忆不存在

影响：不影响当前会话，使用现有记忆即可
```

## 与其他流程的集成

### 与 full-flow 集成

```bash
# 1. 加载项目上下文
/cad-load

# 2. 开始完整开发流程
/full-flow

# cad-load 已加载的记忆会被 full-flow 使用
```

### 与进度追踪集成

```bash
# 1. 加载项目上下文
/cad-load

# 2. 查看详细进度
/status

# 3. 恢复之前的工作
/resume

# 4. 创建检查点
/checkpoint

# 5. 生成报告
/report
```

## 最佳实践

### 1. 会话开始立即加载

```bash
✅ 推荐：
会话开始 → /cad-load → 开始工作

❌ 不推荐：
会话开始 → 直接工作 → 遇到问题 → 才想起加载
```

### 2. 根据任务复杂度选择模式

```bash
简单问答 → /cad-load --quick
正常开发 → /cad-load
复杂任务 → /cad-load --full
```

### 3. 定期检查项目状态

```bash
/cad-load → /status → 开始工作
```

## 技术细节

### 实现原理

1. **激活 Serena 项目** - 调用 `activate_project`
2. **列出可用记忆** - 调用 `list_memories`
3. **读取关键记忆** - 调用 `read_memory`（并行读取）
4. **检查 Git 状态** - 执行 `git status` 和 `git log`
5. **保存会话记录** - 调用 `write_memory`

### 性能优化

- **并行读取记忆** - 同时读取多个记忆，提升速度
- **优先级加载** - 先加载 P0，再加载 P1/P2
- **缓存机制** - Serena MCP 内置记忆缓存

## 更新日志

### v1.0 (2026-03-02)
- ✅ 初始版本
- ✅ 支持三种加载模式（quick/standard/full）
- ✅ 支持加载特定检查点
- ✅ 集成 Git 状态检查
- ✅ 集成进度追踪系统
