# Claude Code 2.1.247 `.claude/rules/` 规则系统语义与符号链接兼容性

> 调研人:researcher 子代理(ClaudeRulesResearch),2026-09-09。方法:InstructionsLoaded hook 审计 + transcript `nested_memory` 原文 + 唯一 marker 探针(模型自报被证实不可靠,未采信);fixture `/tmp/claude-rules-fx`。

## 关键结论(对任务书假设的修正)

1. **任务书假设的 description/always-apply/globs 三字段三模式属 Cursor 模型;Claude Code 2.1.247 仅认 `paths` frontmatter**,只有**常驻/paths-按需**两档,无 description 索引模式(`always-apply: false` 与 `globs:` 键实测均被无视→强载;binary 中 `always-apply` 0 命中)。
2. **frontmatter 注入前被剥离**:`nested_memory` attachment 实证 content=仅正文/rawContent=原文/differsFromDisk:true ⇒ `description` 永不进上下文。
3. **`@import` 在 CLAUDE.md 与规则文件内均可用**,相对路径按包含文件解析,递归恰 4 跳(L5 丢弃),反引号转义有效。
4. **symlink:目标在项目根内→跟随并按解析路径装载(文件+目录均 ✓);目标在项目外(绝对/相对、文件/目录)→无头模式静默不装载**,与官方文档宣称相悖;循环 symlink 优雅处理。
5. **子代理无法按角色过滤规则**:非 Explore/Plan 子代理全部拿同一套 CLAUDE.md+常驻规则(实测 18/18 吻合),差异化只能靠 `.claude/agents/<name>.md` 自身 prompt。
6. **`.mdc` 不发现;`.md` 递归;无 frontmatter=全文强载、优先级同 `.claude/CLAUDE.md`;无数量上限**(4MiB/文件、1000 patterns/规则)。

## 证据

- 文档:https://code.claude.com/docs/en/memory 、/sub-agents#what-loads-at-startup 、/hooks(InstructionsLoaded,经 GH issue #30573 佐证)
- 本地:claude 2.1.247;fixture `/tmp/claude-rules-fx`(hook_log + transcripts + marker 探针);主会话补充实测(2026-09-09,fixture `/tmp/cc-paths-fx`):**`paths: []` 与 description-only 均 session_start 强载**(InstructionsLoaded 审计)——「永不自动载入」桶必须用永不匹配 glob 表达。

## Gaps

- 交互模式下项目外 symlink 规则是否批准后装载(无 TTY 未测)。
- `./CLAUDE.md` 与 `./.claude/CLAUDE.md` 并存时优先级未测未文档化。
- 外部 `@import` 无头行为、`~/.claude/rules/` 用户级(仅文档)未实测。

## 对五端统一规则架构的启示

- **description 桶在 Claude 端退化为常驻全文**且不能当路由元数据;跨端惰性唯一锚点是 `paths` glob;omp `alwaysApply` 与 CC 语义相反,统一层必须显式翻译。
- 五端共享不可靠仓库外 symlink(CC 2.1.247 无头实测不装载);改用**仓库内共享目录+symlink(实测可用)**或构建期物化为 `.md`(`.mdc` 不发现)。
- agents 桶在 Claude 端只能映射进 `.claude/agents/<name>.md` 的 prompt;import 4 跳上限与 4MiB 单文件上限要求深嵌套组织 flatten。
