# Proposal: rule-config-self-contained-templates

## Why

rule-config 的模板定位（`locate_templates`）与脚本/内核定位不对称：内核走 script-relative（skill 目录），模板却写死优先查 `~/.claude/plugins/marketplaces/` 下的 Claude 插件目录并短路返回。在非 Claude 客户端（pi）环境中，若该插件目录存在但过期（停留在旧提交），模板比对会以旧模板为准——最新 skill 安装的模板更新被静默跳过。naruto 实测：新脚本 + 旧 marketplace 模板的组合导致 `document-storage.md` 缺新章节却被判定"幂等跳过"，全程无报错无提示。

用户裁决的原则：**skill 包自包含**——脚本、模板、references 全部以"脚本自身所在 skill 目录"为唯一权威源；定位失败就失败关闭并报告安装不完整，绝不去别处找副本。

## What Changes

- **`locate_templates()` 重写为单源定位**：唯一候选 `SKILL_DIR/references/`（`SKILL_DIR = Path(__file__).resolve().parent.parent`，软链经 `resolve()` 解析到真实仓库）；成对校验（rules 三件套 + `document-storage.md` + `openspec/config.yaml`）缺失任一 → `TemplateError` 失败关闭、非零退出、目标项目零写入、报告缺失清单与"skill 安装不完整，请重新安装"。**BREAKING**（定位语义）
- **删除写死的客户端路径**：移除 `_ONLINE_RULES_SUBPATH`（cadence-skills-marketplace）、`_OFFLINE_RULES_SUBPATH`（cadence-skills-local）、`_FALLBACK_GLOB_PATTERN` 及全部三级定位逻辑。
- **统一 `SKILL_DIR` 常量**：`_load_reference` / `_load_kernel_source` / `locate_templates` 共用，消除三处重复的 `Path(__file__).resolve().parent.parent`。
- **SKILL.md 定位规则改写**：脚本即本 SKILL 所在目录的 `scripts/rule-config.py`；模板与脚本同包由脚本自动解析，Agent 不做模板定位；删除"plugin 缓存根/仓库安装根"候选表述。
- **文档对账**：`references/merge-semantics.md` §11.5 整节重写为"skill 自包含唯一定位"；`tests/skill-clause-map.md` 的 S1b-01~04 行同步。
- **测试语义反转**：shell `it-s2-templates-missing` 从"空 HOME 全缺 → 失败关闭"反转为"空 HOME 仍可运行（模板不依赖 HOME）"；pytest `TestLocateTemplates` 六用例全删重写为单源契约。

### 非目标

- 不改 pre-check 的 Superpowers 同步路径（`~/.agents/superpowers` 等外部依赖位置是功能本身）。
- 不改 skill-creator 的安装目标语义（另一功能）。
- 不改模板的成对校验文件清单与 TemplateError 的失败关闭性质（只改候选来源）。

## Capabilities

### New Capabilities

（无新 capability。）

### Modified Capabilities

- `rule-config-scripted-execution`：新增"模板与脚本必须同源（skill 自包含）"requirement——模板唯一定位到脚本所在 skill 目录，禁用环境相关路径候选与全局搜索回退，缺失即失败关闭。

## Impact

- **代码**：`cadence-init/skills/rule-config/scripts/rule-config.py`（`locate_templates` 重写、`SKILL_DIR` 常量、删除三级定位常量与逻辑）。
- **测试**：`tests/test_rule_config.py`（TestLocateTemplates 重写、新增 HOME 无依赖断言）；`tests/verify-managed-lifecycle.sh`（C16e 语义反转、删除 ONLINE_TEMPLATE_SKILL fixture）；`tests/skill-clause-map.md` 对账。
- **文档**：`SKILL.md`（第一步定位规则）、`references/merge-semantics.md` §11.5。
- **行为**：模板永远跟随当前调用的 skill 安装版本；过期 marketplace/缓存副本不再被误用；skill 安装不完整时立即显式失败而非静默使用别源模板。
- **回归场景**：naruto 式环境（pi + `~/.agents` 新仓库 + 过期 Claude marketplace 共存）重跑 rule-config，`document-storage.md` 将被归档并覆盖补齐新章节。
