---
skill: legacy-bootstrap
---

# /legacy-bootstrap - Legacy 项目 Bootstrap

调用 `legacy-bootstrap` skill，使用 repomix 对当前本地 legacy 项目进行初始化认知分析。

## 使用场景

- 当前 Claude Code 或 Codex 已打开一个本地 clone 的 legacy 项目。
- 需要在需求、设计或修改代码前建立项目认知。
- 需要生成可版本化的 Cadence 项目认知文档。
- 需要让 `CLAUDE.md` 与 `AGENTS.md` 渐进式引用这些认知文档。

## 功能

执行以下流程：

1. 读取当前项目规则和入口文档。
2. 询问用户选择标准模式、深度模式或轻量降级模式。
3. 使用 `npx repomix@latest` 生成项目上下文。
4. 参考 repomix 实验性 `--skill-generate` 的结构思路，但不作为主流程，默认不执行。
5. 分析项目架构、模块、依赖、风险、数据模型、构建测试画像和未知项。
6. 将有证据支撑的认知产物写入 `cadence/` 下的对应目录。
7. 更新 `CLAUDE.md` 与 `AGENTS.md` 的渐进式项目认知加载区域，只链接实际生成的文档。
8. 输出 bootstrap 摘要和建议下一步。

## 输出

默认按实际证据生成或更新以下候选目录与文件：

- `cadence/analysis-docs/`
- `cadence/architecture/`
- `cadence/docs/`
- `cadence/models/`
- `cadence/plans/`
- `CLAUDE.md`
- `AGENTS.md`

## 约束

- 只处理当前打开的本地项目。
- 不 clone 远程仓库。
- 不生成 `.ai/`。
- 不直接重构业务代码。
- 不编造未知业务事实。
- repomix `--skill-generate` 仅作为参考，默认不执行。

## 相关命令

- `/pre-check` - 检查 npx 等基础工具
- `/cadence:init:project-analysis` - 基础项目结构分析
- `/cadence:init:rule-config` - 初始化项目规则
