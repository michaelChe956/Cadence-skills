# Design: rule-config-self-contained-templates

## Context

现状与动机见 proposal.md。设计相关的当前状态：

- `rule-config.py` 中 `_load_reference`/`_load_kernel_source` 已用 `Path(__file__).resolve().parent.parent`（script-relative），但 `locate_templates()` 保持旧三级定位（在线 marketplace → 离线 local → glob 回退，在线命中即短路）。
- pytest `TestLocateTemplates` 六用例通过伪造 HOME 测三级行为；shell `it-s2-templates-missing`（C16e）用空 HOME 触发全缺失败；`ONLINE_TEMPLATE_SKILL` fixture（106-108 行）往 fake HOME 铺 marketplace 布局。
- naruto 事故现场：pi 调用 `~/.agents/Cadence-skills` 新脚本，模板却被短路过期的 `~/.claude` marketplace checkout。

## Goals / Non-Goals

**Goals:**

- 模板与脚本同源：模板唯一定位 `SKILL_DIR/references/`，与客户端无关。
- 删除全部写死的客户端路径候选与全局搜索回退。
- skill 包不完整时显式失败关闭并给出可操作的恢复建议。
- 空 HOME 环境照常工作（回归断言）。

**Non-Goals:**

- 不改模板成对校验的文件清单与 TemplateError 的失败关闭性质。
- 不动 pre-check 的 Superpowers 外部依赖路径、skill-creator 安装目标。
- 不引入"多候选择优"逻辑（mtime 等）——单源即契约，无需择优。

## Decisions

### D1：单源唯一定位，删除全部回退档位

模板只从 `SKILL_DIR/references/` 取。原则：skill 包自包含，任何"去别处找"的行为都会引入跨安装污染（naruto 事故的根因）。替代方案"保留旧档位作兜底"被否决——兜底即漏洞：兜底命中过期副本时静默错误，比显式失败更糟；且脚本与 references 同船分发，正常安装下单源必然命中。

### D2：模块级 `SKILL_DIR` 常量统一三处引用

`SKILL_DIR = Path(__file__).resolve().parent.parent`。`resolve()` 使软链安装（如 `~/.agents/skills/<name>` → 真实仓库）正确落位；`_load_reference`/`_load_kernel_source` 改为引用常量，消除重复表达式。测试经 `mock.patch.object(rc, "SKILL_DIR", ...)` 注入 fixture 路径即可隔离。

### D3：不完整即失败关闭，而非顺延

必备文件清单（四件套 + `openspec/config.yaml`）缺失任一 → `TemplateError`，列出缺失清单与重装建议。不修不补不猜测——部分复制的 skill 包是安装缺陷，必须用显式失败暴露，而不是用别源内容掩盖。

### D4：测试语义反转而非删除

- pytest：六用例全删重写为单源契约（完整命中 / 缺件失败 / 空 HOME 无依赖）。
- shell C16e（`it-s2-templates-missing`）反转为正断言：空 HOME 下流程仍正常完成（模板来自 skill 目录）——把旧失败场景变成新契约的回归断言。`ONLINE_TEMPLATE_SKILL` fixture 删除。
- E2E 回归：fake marketplace 旧模板 + skill 目录新模板共存，断言项目文件按 skill 目录模板收敛。

## Risks / Trade-offs

- **Claude Code 极端环境**：若某客户端把 skill 拆包安装（scripts 与 references 分离），单源会失败——但该布局本就违反"skill 包自包含"前提，SKILL.md 已声明"不得复制脚本单独执行"。失败信息会指引重装。 → 接受。
- **既有 shell fixture 语义变化**：`ONLINE_TEMPLATE_SKILL` 删除后 C16e 改为正断言 → 审查时重点核对。
- **调试场景失去 glob 便利**（在任意目录放个模板就能跑）→ 该便利正是污染源，放弃。

## Migration Plan

1. 本 change 为仓库内代码/测试/文档变更，TDD 实施。
2. 框架用户无需迁移：正常安装的 skill 包天然自包含，行为只会更正（模板与版本同步）。
3. 回滚：git 回滚实现提交即可，目标项目无持久状态。

## Open Questions

无。
