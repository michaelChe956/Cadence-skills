# OpenSpec 与 Superpowers 路由验收矩阵

## 一、验证范围

- OpenSpec change：`improve-progressive-disclosure-routing`
- OpenSpec 工作包：`5.1`
- 验证对象：Claude Code、Kimi Code、Codex
- 验证内容：静态一致性检查，以及三个客户端的六类关键路由场景
- 验证根目录：由 `git rev-parse --show-toplevel` 在执行时解析，不在报告中持久化临时 worktree 绝对路径
- 数据最小化：静态检查与 Codex 使用真实工作树只读验证；Claude Code 与 Kimi Code 另使用不含 Git、业务源码、用户配置和 `cadence/plans/` 的临时脱敏夹具
- 判定值：`PASS`、`FAIL`、`BLOCKED`

### 脱敏夹具审计

- 创建方式：`mktemp -d`、`mkdir`、`cp`/`cp -a` 机械复制，不生成脚本。
- 文件范围：共 19 个文件，仅包含 `CLAUDE.md`、`AGENTS.md`、`.claude/rules/`、`openspec/config.yaml` 与目标 change。
- 一致性：三个单文件 `cmp`、两个目录 `diff -qr` 均退出 0；`.git` 与 `cadence` 不存在。
- Kimi 隔离：宿主根只读，完整 `/home/michaelche/workspace` 由 tmpfs 隐藏，夹具只读挂载到 tmpfs 内的验证目录，Kimi 运行态位于 tmpfs。

| 相对路径 | SHA-256 |
|---|---|
| `.claude/rules/README.md` | `eecc92f0e18d7dc07a1b74aaa3e8d42c81276806e58487bd43f818d4dae54828` |
| `.claude/rules/code-reading.md` | `03b7471a78fb34a6f97e35241a1d59c724f5114bd4fee3879836a294f97100f8` |
| `.claude/rules/code-usage.md` | `fac1e300d7d4de0242e5fce5d281caa0ccfb97cb4745597abe94b1e8ee897088` |
| `.claude/rules/document-storage.md` | `10672fda93c99283c732e60dd900b7bb65e3c3733e240a775004cc592c0ae422` |
| `.claude/rules/language.md` | `161a43fbb6ce96f9fc832335fb771bcabea495ef7fafe619c490eb8f14af2588` |
| `.claude/rules/markdown-format.md` | `0be1029d074f3a032ac7031cabe302f5b829a9ab8f83e6c5916b60fbfd2ee74f` |
| `.claude/rules/mcp-servers.md` | `3eccd8fdb11edaa8a0fe4f629667c1e2224352dd259aaf58ea3f33b166773884` |
| `.claude/rules/openspec-superpowers-workflow.md` | `758f4b51ee4c0808db3cc02862df3af949e88906d16dd6824838b0265156b5b2` |
| `.claude/rules/playwright.md` | `0248c02caae5841e29e4d13ea9118001cd6bdcad8b0a1ef2a854dc87162982a1` |
| `AGENTS.md` | `03a4a562eec64b1698a983e23d8f5792809e05b412faec8b6c690ebeddc2d93b` |
| `CLAUDE.md` | `fd4e3cc49626c9125a025be891f53d0fe7dbb67841973683521e49ae79c4641c` |
| `openspec/config.yaml` | `650390ed1019338e61520ed3d95c4a8ab50fe401be73a7a785c30af6c1bb0464` |
| `openspec/changes/improve-progressive-disclosure-routing/.openspec.yaml` | `de76da64ea78cfbcca727518866c848b20ea41b11d77cbb92ef64e61f479cf96` |
| `openspec/changes/improve-progressive-disclosure-routing/design.md` | `d21322d5b00d01b08997cd4f75b49146a8f090f523f586fd3139bebc262ec497` |
| `openspec/changes/improve-progressive-disclosure-routing/proposal.md` | `fcd3d253583b44065cf21a353562d834cdb1d51933b3d880eeb658f906c211b0` |
| `openspec/changes/improve-progressive-disclosure-routing/specs/managed-rule-lifecycle/spec.md` | `e6dfaa8a95c8b58daee0d89a5eb76b625f25caeaaf07934058cccadff6515e45` |
| `openspec/changes/improve-progressive-disclosure-routing/specs/progressive-context-routing/spec.md` | `b724ada8bec557f8294d413d8ec3961d302d16b61e05d508a17943c2b1e0cdd9` |
| `openspec/changes/improve-progressive-disclosure-routing/specs/routing-conformance/spec.md` | `a73e5150b5e4e35eaa43e567d339ee80fbf3e52d57d8ab25b2826fb5eb24dcde` |
| `openspec/changes/improve-progressive-disclosure-routing/tasks.md` | `0669a96d5d08b408dee45bbe1ecc9a5389608d9ba2200972efb5c6b69713b3de` |

## 二、客户端与工具版本

| 工具 | 实际版本 | 命令退出码 | 备注 |
|---|---|---:|---|
| Claude Code | `2.1.212 (Claude Code)` | 0 | 版本命令正常 |
| Kimi Code | `0.27.0` | 0 | 版本命令正常 |
| Codex | `codex-cli 0.144.6` | 0 | 同时警告无法在只读文件系统创建 PATH alias；不影响版本命令 |
| OpenSpec | `1.4.1` | 0 | 版本命令正常 |

## 三、静态检查

| 编号 | 检查 | 命令 | 退出码 | 原始摘要 | 结论 |
|---|---|---|---:|---|---|
| C1 | L1 规范源与生成副本一致 | `cmp cadence-init/skills/rule-config/references/rules/openspec-superpowers-workflow.md .claude/rules/openspec-superpowers-workflow.md` | 0 | 无输出，文件逐字节一致 | PASS |
| C2 | OpenSpec 配置源与当前副本一致 | `cmp cadence-init/skills/rule-config/references/openspec/config.yaml openspec/config.yaml` | 0 | 无输出，文件逐字节一致 | PASS |
| C3 | L0 start 标记总数为 2 | `test "$(rg --no-filename -o "cadence-managed:openspec-superpowers-routing:v1:start" CLAUDE.md AGENTS.md \| wc -l)" -eq 2` | 0 | 无输出，断言成立 | PASS |
| C4 | L0 end 标记总数为 2 | `test "$(rg --no-filename -o "cadence-managed:openspec-superpowers-routing:v1:end" CLAUDE.md AGENTS.md \| wc -l)" -eq 2` | 0 | 无输出，断言成立 | PASS |
| C5 | OpenSpec 不含无效 `rules.apply` | `if rg -n "^  apply:" openspec/config.yaml; then exit 1; fi` | 0 | 无匹配输出 | PASS |
| C6 | L0 引用的 Superpowers Skill 均存在 | `for skill in ...; do test -f "/home/michaelche/.agents/superpowers/skills/$skill/SKILL.md" \|\| exit 1; done` | 0 | 无输出，十个 Skill 文件均存在 | PASS |
| C7 | OpenSpec strict 校验 | `openspec validate improve-progressive-disclosure-routing --type change --strict --no-interactive` | 0 | `Change 'improve-progressive-disclosure-routing' is valid` | PASS |
| C8 | L0 规范源与两个入口受管区块一致 | 对 `CLAUDE.md`、`AGENTS.md` 提取受管区块后分别与 `agent-routing-kernel.md` 执行 `cmp` | 0 / 0 | L0 修复后两次 `cmp` 均无输出 | PASS |

首次静态检查和 Claude S1 的 L0 修复后全量静态复测均退出 0。

## 四、场景定义

| 场景 | 输入类型 | 严格判定标准 |
|---|---|---|
| S1 | 新功能 | 识别探索阶段、`using-superpowers` 与 `brainstorming`，不进入实现 |
| S2 | Bug | 先路由 `systematic-debugging`，根因确认后才进入 `test-driven-development` |
| S3 | 直接 apply | 无已确认 Plan 时拒绝实施，并路由 `writing-plans` |
| S4 | compact/resume | 重新识别阶段、Change、Plan 和必调 Skill，并重做门禁 |
| S5 | 纯概念问答 | 一句话轻量回答，不读取仓库、不调用工具、不加载无关正文 |
| S6 | 完工声明 | 拒绝无证据完成声明，并路由 `verification-before-completion` |

## 五、三客户端场景矩阵

| 客户端 | 场景 | 期望阶段与 Skill | 实际路由与加载 | 门禁结果 | 无关正文误加载 | 结论 |
|---|---|---|---|---|---|---|
| Claude Code | S1 | 探索；`using-superpowers`、`brainstorming` | 全工作树调用先因 socket/审批阻断；脱敏夹具首次退出 0，但先勘察 change、未先给完整四字段回执，遗漏 `using-superpowers`，严格 `FAIL`。最小强化 L0 后只重跑 S1，180 秒超时退出 124、无正文 | 首次未实施但违反前置回执；修复后运行时门禁不可验证 | 首次在回执前误加载 change 状态；修复后无正文可审计 | BLOCKED |
| Claude Code | S2 | 调试；`systematic-debugging` 后 TDD | 脱敏夹具命令退出 0；原始回执“阶段=调试/根因分析；Change=待定；Plan=无；必调 Skill=using-superpowers → systematic-debugging”，并说明根因后才进入 TDD | 明确根因未确认不得写修复；根因确认后调用 `test-driven-development` 并先写失败测试 | 仅额外提及完成验证/审查门禁，未加载无关正文 | PASS |
| Claude Code | S3 | 规划；拒绝 apply，`writing-plans` | 脱敏夹具命令退出 0；识别目标 change 与 `cadence/plans/` 不存在，原文“不允许继续，必须停止”，要求先 `writing-plans` | 无已确认 Plan 时停止，禁止执行 tasks 或修改文件 | 仅读取 change 状态与直接相关协作规则 | PASS |
| Claude Code | S4 | 恢复；重识别四字段与门禁 | 脱敏夹具命令退出 0；列出阶段、Change、Plan、首调 `using-superpowers` 后按阶段补调 Skill | 明确缺 Skill、缺 Plan、契约变化或缺新鲜证据时失败关闭 | 仅说明恢复路由与相关门禁 | PASS |
| Claude Code | S5 | 轻量问答；无 Skill 正文 | 脱敏夹具命令退出 0；原始响应仅一句渐进式披露定义 | 直接回答，无仓库路由或工具调用 | 无实现、OpenSpec、Plan 或完成验证正文 | PASS |
| Claude Code | S6 | 验证；`verification-before-completion` | 脱敏夹具命令退出 0；先回执“阶段=完工声明；Change=improve-progressive-disclosure-routing；Plan=未核验；必调 Skill=verification-before-completion” | 明确拒绝无验证命令、无新鲜证据的完成声明 | 仅说明完工验证直接相关流程 | PASS |
| Kimi Code | S1 | 探索；`using-superpowers`、`brainstorming` | 原 Plan 命令退出 1：`Cannot combine --prompt with --plan.`。改为 Bubblewrap 只读 `-p` 后，全工作树与脱敏夹具两次沙箱复测均在 OAuth DNS `EAI_AGAIN` 阻断；两次最小权限重试均被审批拒绝。脱敏复测前还保留一次 `/validation` 位于只读根的挂载失败，改到 `/tmp/validation` 后版本冒烟退出 0 | 模型未启动，实际路由与门禁不可验证；夹具和只读隔离已独立验证 | 无模型正文可观察 | BLOCKED |
| Kimi Code | S2 | 调试；`systematic-debugging` 后 TDD | 原命令参数互斥；脱敏夹具的唯一外部发送审批仍明确拒绝并禁止绕过，命令未再启动 | 模型未启动，`systematic-debugging` 与后续 TDD 门禁不可验证 | 无模型正文可观察 | BLOCKED |
| Kimi Code | S3 | 规划；拒绝 apply，`writing-plans` | 原命令参数互斥；脱敏夹具不含 Plan，但外部发送审批仍拒绝，命令未再启动 | 模型未启动，无 Plan 拒绝与 `writing-plans` 路由不可验证 | 无模型正文可观察 | BLOCKED |
| Kimi Code | S4 | 恢复；重识别四字段与门禁 | 原命令参数互斥；脱敏夹具外部发送审批仍拒绝，命令未再启动 | 模型未启动，阶段、Change、Plan、Skill 重识别不可验证 | 无模型正文可观察 | BLOCKED |
| Kimi Code | S5 | 轻量问答；无 Skill 正文 | 原命令参数互斥；脱敏夹具外部发送审批仍拒绝，命令未再启动 | 模型未启动，未生成概念回答，无法判定轻量行为 | 无模型正文可观察，不能据此判定通过 | BLOCKED |
| Kimi Code | S6 | 验证；`verification-before-completion` | 原命令参数互斥；脱敏夹具外部发送审批仍拒绝，命令未再启动 | 模型未启动，拒绝声明与完成验证门禁不可验证 | 无模型正文可观察 | BLOCKED |
| Codex | S1 | 探索；`using-superpowers`、`brainstorming` | 首次沙箱内调用退出 1：`failed to initialize in-process app-server client: Read-only file system`；最小权限重试退出 0。原始响应先给出“阶段=新功能需求澄清与方案讨论；Change=尚未创建/确认；Plan=尚不存在；必调 Skill=using-superpowers、brainstorming”，随后实际读取两个 Skill、L1/L0，并只读识别现有候选 Change/Plan | 明确“未获确认前不会进入 OpenSpec 或实施”，最终只提出 Change 归属澄清问题；未修改文件 | 读取了与潜在文档产物相关的文档/Markdown 规则，属 S1 路由表要求；未加载实现或完成验证正文 | PASS |
| Codex | S2 | 调试；`systematic-debugging` 后 TDD | 命令退出 0。原始响应：“阶段=测试失败诊断；Change=未确认；Plan=无；必调 Skill=`using-superpowers` → `systematic-debugging`”，并说明根因确认后才调用 `test-driven-development` | 遵守“不读取”约束而未加载 Skill 正文，按失败关闭停止；禁止猜测或修改代码，根因确认后重新路由进入 TDD | 无工具调用，无无关正文加载 | PASS |
| Codex | S3 | 规划；拒绝 apply，`writing-plans` | 命令退出 0。先回执“阶段=apply 前门禁检查；Change=improve-progressive-disclosure-routing；Plan=不存在”，只读加载 L0/L1、`using-superpowers`、`openspec-apply-change` 与 `executing-plans` 门禁；最终原文：“不允许继续 apply……应先调用 `writing-plans` 生成并确认 Plan” | 无已确认 Plan 时停止，没有读取 change 产物、没有执行工作包、没有修改文件 | 加载内容均与直接 apply 及其 Plan 门禁相关；无实现、审查或完成验证正文误加载 | PASS |
| Codex | S4 | 恢复；重识别四字段与门禁 | 命令退出 0。先回执“阶段=compact/resume 后恢复已有 OpenSpec change；Change=待重新确认；Plan=待重新确认；必调 Skill=using-superpowers”，实际重新读取 `using-superpowers`、L0 和 L1；最终列出阶段、Change、Plan、必调 Skill 四字段 | 明确 Skill 未加载、Change 未确认、无已确认 Plan、契约变化四类停止门禁，并要求 apply/实施前重新路由 | 仅加载恢复路由直接相关正文 | PASS |
| Codex | S5 | 轻量问答；无 Skill 正文 | 命令退出 0；原始响应仅一句：“渐进式披露是先展示最必要的信息，再根据用户需求逐步呈现更多细节，以降低认知负担。” | 直接回答，无仓库读取或工具调用 | 无任何正文加载 | PASS |
| Codex | S6 | 验证；`verification-before-completion` | 命令退出 0。先回执“阶段=完工声明前；Change=improve-progressive-disclosure-routing；Plan=未知；必调 Skill=using-superpowers、verification-before-completion”，实际读取 L0/L1 与两个 Skill | 拒绝声明，原文：“尚未在本次会话中验证，完成状态与测试结果未确认。”未运行验证命令 | 仅加载完成声明门禁直接相关正文 | PASS |

## 六、失败与修复映射

| 首次失败或阻塞 | 定位层 | 原始证据 | 最小修复 | 复测结果 |
|---|---|---|---|---|
| Kimi S1–S6 首次均为 `Cannot combine --prompt with --plan.` | Plan 执行命令 | Kimi 0.27.0 参数校验明确禁止 `--prompt` 与 `--plan` 组合；其 `-p` 又固定自动批准工具 | 将 Plan 六个 Kimi 命令改为 Bubblewrap 宿主只读、完整 workspace 隐藏、脱敏夹具只读挂载、Kimi Home tmpfs 的原生 `-p`，未修改 L0/L1/L2 | 兼容性与隔离冒烟通过；全工作树及脱敏夹具均因 DNS/审批拒绝，S1–S6 最终仍为 `BLOCKED` |
| Kimi 脱敏包装首次使用 `/validation` | Plan 执行命令 | `--ro-bind / /` 后只读根无法创建新的顶层挂载目标 | 将挂载目标移到 tmpfs 内的 `/tmp/validation` | `kimi --version` 在相同包装下退出 0；随后到达 OAuth 网络阶段 |
| Codex S1 首次 app-server 初始化失败 | 执行环境 | 沙箱只读文件系统阻止 Codex 创建运行态 | 保持 Codex 自身 `--sandbox read-only`，申请最小外层权限重试；未修改规则 | 重试退出 0，S1 `PASS`；S2–S6 同方式均退出 0 |
| Claude 全工作树 S1–S6 无路由正文 | 执行环境/外部审批 | 沙箱内 API socket 不可达或超时；最小权限外部调用因私有工作区外传风险被拒绝 | 不更换模型、不绕过审批；构造仅含路由规则与目标 change 的脱敏夹具，并申请一次 materially safer 外部调用 | 脱敏复测 S2–S6 `PASS`；S1 暴露 L0 缺口后修复，但定向复测超时为 `BLOCKED` |
| Claude 脱敏 S1 首次遗漏前置路由 | L0 | 首次响应先勘察 change，未先输出阶段/Change/Plan/Skill，遗漏 `using-superpowers`；只提条件式 `brainstorming` | 强化 `agent-routing-kernel.md`：第一段必须先完整回执，回执前禁止任何只读勘察，澄清问题不得替代回执；同步 `CLAUDE.md` 与 `AGENTS.md` | 只重跑 S1 时 180 秒超时，无正文，最终 `BLOCKED`；首次 `FAIL` 证据保留，不能声称修复已通过运行时验收 |

## 七、未验证风险

- Kimi Code 的脱敏夹具外部调用仍被审批系统拒绝，六个场景均无模型响应；Kimi 的实际路由行为完全未验证。
- Claude Code S1 首次运行暴露 L0 前置回执缺口；规范源和两个入口已同步，静态检查通过，但修复后的定向运行复测超时，尚无运行时通过证据。
- Claude Code 与 Kimi Code 的可执行验证采用最小脱敏夹具。夹具覆盖 L0、L1、OpenSpec 配置与目标 change，且故意不含 Plan 以验证 S3；它不等同于完整工作树运行环境。
- 完整三客户端矩阵未全部通过，不能据此宣称跨客户端验收完成。

## 八、结论

结论为 `DONE_WITH_CONCERNS`。静态检查 8 组（其中 L0 同步含两个 `cmp`）全部通过；18 个最终场景中 11 个 `PASS`、7 个 `BLOCKED`、0 个当前 `FAIL`。Codex 6/6 `PASS`；Claude Code S2–S6 `PASS`，S1 首次 `FAIL` 后完成 L0 修复但复测 `BLOCKED`；Kimi Code 6/6 因外部调用审批拒绝而 `BLOCKED`。首次失败、修复和复测证据均已保留，不以预期结果替代实际响应。
