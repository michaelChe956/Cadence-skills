# Kimi Code CLI 0.41.0 规则与 context 发现机制

> 调研人:researcher 子代理(KimiResearch),2026-09-09。来源:官方文档(www.kimi.com/code/docs)+ binary strings + 本机 `-p` 无头探针。

**版本与身份校正**:本机 `kimi --version` → 0.41.0(2026-09-04 发布,与官方 changelog 对应)。Kimi Code 是 **Moonshot AI(月之暗面)** 产品(开源仓库 MoonshotAI/kimi-code),非智谱系;本机 config.toml 里的 GLM 模型只是经第三方 openai 兼容代理接入的推理后端。仓库内含 `packages/pi-tui` 等与 pi 同源的包,上下文机制与 pi 一脉相承(AGENTS.md 优先、cwd 树状列表)。

## 1. context 文件发现

### 启动时注入 system prompt 的文件【实测 + binary strings 双重确认】

发现逻辑(摘自二进制内嵌源码):

```js
for (const dir of dirsRootToLeaf(rootWorkDir, projectRoot))
  projectCandidates.push(join(dir, ".kimi-code", "AGENTS.md"), join(dir, "AGENTS.md"), join(dir, "agents.md"));
// 全局层:
await collect(join(brandHome ?? join(realHome, ".kimi-code"), "AGENTS.md"));
const genericFiles = [join(realHome, ".agents")].flatMap(dir => ["AGENTS.md","agents.md"].map(name => join(dir, name)));
```

- **项目层**(项目根=向上最近的含 `.git` 目录,无 `.git` 则用 cwd):从项目根到 cwd 逐目录收集 `.kimi-code/AGENTS.md` + `AGENTS.md`/`agents.md`(同目录内 AGENTS.md 优先于 agents.md,首个命中即止;`.kimi-code/AGENTS.md` 与根 `AGENTS.md` **同时**加载)。
- **全局层**:`~/.kimi-code/AGENTS.md` + `~/.agents/AGENTS.md`(仅用户主目录层,**项目内 `.agents/AGENTS.md` 不加载**——实测确认)。
- **合并而非遮蔽**:所有命中的文件全部拼接进 system prompt 的 `# Project Information` 段,每块用 `<!-- From: <绝对路径> -->` 标注来源;冲突时「更深/更具体(按来源路径标记)者胜」。
- **不加载**(实测):`CLAUDE.md`、`KIMI.md`、`.kimi/rules/`、`.claude/rules/`、项目 `.agents/AGENTS.md`。
- **体积预算**:合并总量 >32768 字节产生 warning(`AGENTS_MD_RECOMMENDED_MAX_BYTES`)。
- **热重载**:binary 有 `agentsMdWatchRoots`、变更提醒文案——会话中文件变更被监视并提醒重注入【源码级证据】。
- **其他注入**:cwd 两层树状目录列表(隐藏目录折叠)、`${skills}` 技能索引、`${plugin_sections}` 插件指令段。

### MCP 配置三层(binary 佐证)

`~/.kimi-code/mcp.json` → 项目根 `.mcp.json` → `<cwd>/.kimi-code/mcp.json`,后者覆盖前者。

## 2. 规则系统

**没有独立 rules 目录/规则格式**(无 frontmatter 分桶;strings 无任何 rules 目录路径)。规则性内容走两条通道:

### a) AGENTS.md 指令文件(常驻通道)

启动即全文注入。渐进能力:

- **按需指针提醒**:工具调用触达的路径所在目录有未注入的 AGENTS.md 时,追加 system-reminder(实测原文):「The following AGENTS.md file(s) apply to paths accessed by your recent tool call, but were not included in your system prompt: … — Read them before making changes in those directories.」——**只给路径不给内容**,模型自行 Read。

### b) Agent Skills(按需通道)

- 位置与优先级 **Project > User > Extra > Built-in**:项目 `.kimi-code/skills/`、`.agents/skills/`;用户 `~/.kimi-code/skills/`、`~/.agents/skills/`;`extra_skill_dirs` 追加;内置最低。
- 格式:`<name>/SKILL.md`(目录式,推荐)或平铺 `<name>.md`;frontmatter:`name`、`description`、`type`、`whenToUse`(兼容 when-to-use/when_to_use)、`disableModelInvocation`、`arguments`。**无触发条件字段——`whenToUse` 只是模型自由裁量的提示,不是确定性 trigger**。
- **渐进加载实测确认**:system prompt 只注入 `name: description` 索引,正文不进上下文;模型按 description/whenToUse 经 Skill 工具自动调用,或 `/skill:<name>` 手动;最多 3 层嵌套。
- `--skills-dir`(可重复):**整体替换**自动发现的项目+用户技能目录(实测)。
- 实测 `.claude/skills/` 不被发现(只有 `.kimi-code/skills`、`.agents/skills`)。

## 3. agent/角色限定能力

- **Agent 文件即角色**:`.kimi-code/agents/`、`.agents/agents/`(项目)、`~/.kimi-code/agents/`、`~/.agents/agents/`(用户)、`extra_agent_dirs`;优先级 Explicit(`--agent-file`) > Project > Extra > User > Plugin > Built-in;内置 `coder`/`explore`/`plan`。frontmatter:`name/description/whenToUse/override/tools/disallowedTools/subagents`;**body 就是该 agent 的 system prompt**,支持 `${base_prompt}/${agents_md}/${skills}/${plugin_sections}` 模板变量 → 可通过是否引用 `${agents_md}` 粗粒度控制该角色是否带规则。`~/.kimi-code/SYSTEM.md` 整体替换默认主 agent system prompt。
- **规则按 agent 过滤:不支持**。实测(explore 子代理):**子代理继承完整合并版 AGENTS.md 块 + cwd 列表,但拿不到 skills 索引**——想给子代理不同规则只能写不同 agent 文件 body。

## 4. 符号链接兼容性【实测 0.41.0】

- **根 AGENTS.md 为 symlink → 正常加载**(marker 全文进 system prompt)。
- **嵌套 symlink AGENTS.md → 被发现**(按需提醒列出的是 symlink 路径,即发现层 stat 跟随软链)。
- 技能目录 SKILL.md 为软链:未实测;binary 中技能发现用 `isFile`(stat 语义,跟随 symlink)【[INFERENCE]】。
- 结论:**发现层对 AGENTS.md 全链路跟随 symlink**。

## 5. 版本注记

- 本机 0.41.0 与官方 changelog 顶条一致,无版本漂移。
- **与 2026-09-02 四端探针的差异**:探针当日版本为 0.40.x;本次 0.41.0 探针中 `.claude/rules/*` 文件名**未**出现在启动上下文——cwd 列表两层树且隐藏目录折叠。09-02 的「.claude/rules 文件名进上下文」在 0.41.0 无法以纯启动上下文复现,按 0.41.0 现状修正认知(Kimi 端 .claude/rules 目录级加载迹象不成立)。

## 6. 本机 config.toml 相关开关

仅模型/provider/thinking/services 配置,无规则相关开关。可用开关(默认):`merge_all_available_skills=true`、`extra_skill_dirs`、`extra_agent_dirs`、`builtin_product_skills=true`、`[tools]`、`[identity]`。**不存在 AGENTS.md 加载的关闭开关**。

## 7. 对五端统一规则架构的启示

1. **常驻通道唯一且是合并语义**:Kimi 只认 AGENTS.md 家族,全部拼接、`<!-- From: path -->` 标源、深者胜。统一规则应发布到**项目根 AGENTS.md**(五端最大公约数);`.kimi-code/AGENTS.md` 为 Kimi 专属增强层但与根**叠加**,内容需去重分工。32KB 软预算要求 L0 精简。
2. **按需通道 = 技能索引**:SKILL.md 是「description → 正文按需展开」的原生形态;但没有确定性触发器,条件触发桶在 Kimi 端只能降级为模型裁量;**子代理看不到技能索引**,依赖技能的规则必须写进 AGENTS.md 或 agent 文件 body。
3. **symlink 全兼容 + CLI 可控注入**:AGENTS.md 软链实测可用;`--skills-dir` 可做无痕 A/B。

## 证据清单

- 官方文档:www.kimi.com/code/docs/en/kimi-code-cli/(configuration/config-files、customization/skills、customization/agents、release-notes/changelog)、仓库 MoonshotAI/kimi-code
- 本地实测:`~/.kimi-code/bin/kimi --version`、`kimi --help`、`strings ~/.kimi-code/bin/kimi`(加载器源码片段)、`/tmp/kimi-fixture` 探针(启动上下文盘点/嵌套按需提醒/symlink/子代理上下文/`--skills-dir` 替换语义)

## Gaps

- AGENTS.md 热重载仅源码级证据,未做 TUI 实测。
- 全局层两文件同时存在时的合并顺序未实测(本机两者皆不存在)。
- SKILL.md 目录为软链、`local.toml [workspace] additional_dir` 对发现的影响未测。
