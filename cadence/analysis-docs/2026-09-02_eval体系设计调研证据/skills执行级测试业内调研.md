# Research: coding agent skills / 斜杠命令 / 规则文件的执行级测试(业内对照)

## Summary
业内执行级测试已从"触发识别"分化为三类落地形态:①规则遵循回归测试(claudemd-check/rulebench:probe 任务×多 run×确定性断言×基线 diff);②workspace 快照+文件系统断言的任务级 harness(iso-eval 思路、cae/swe-bench-essential);③录制回放/网络 mock(AgentHound、agenteval 的 fake MCP)。headless CLI 进 CI 的最大教训是 Backgrind 实测的"dontAsk 静默成功假绿",必须显式 gate `permission_denials`。anthropics/skills 主分支无 CI workflow,自身不跑执行级测试。

## Findings

### 一、skill/command 执行级测试实践
1. **anthropics/skills 主分支没有 .github/workflows**(本次克隆确认,根目录仅 .claude-plugin/ + skills/)——官方仓库自身不做 CI 执行级测试;质量门槛是 skill-creator 的 evals.json 生命周期:每 case 建临时环境、发 prompt、用 discriminating assertions 验证 outcome(执行级,但按 skill 内嵌、非 CI)。[anthropics/skills](https://github.com/anthropics/skills)、[DeepWiki: writing evals](https://deepwiki.com/dan323/easier-life-skills/6.1-writing-evals)
2. **skillgrade(mgechev)** 是目前最接近"skill 单测"的公开实现:eval.yaml 声明任务 + 双 grader(确定性脚本可查文件系统 + LLM rubric),支持 `--smoke` 免费冒烟;官方博客明确"golden-prompt 断言须行为级而非文本级"。[skillgrade](https://github.com/mgechev/skillgrade)、[博客](https://blog.mgechev.com/2026/03/14/skillgrade/)
3. **幂等性执行级测试先例**:jarvy 项目 `default_hook_idempotency.rs` 把安装 hook 跑两遍、隔离 `$HOME`、断言运行后状态 byte-identical——与我们阶段①"安装命令幂等"完全同构。[jarvy tests](https://github.com/Cliftonz/jarvy/blob/main/tests/default_hook_idempotency.rs)
4. **slash 命令测试现状**:公开实现集中在参数解析单测(如 atomic 仓库对 slash bridge 做 `invoke→assert.deepEqual(params)`),未见"跑完断言文件系统"的成熟开源框架——我们的空白有真实差异化价值。[atomic test](https://github.com/bastani-inc/atomic/blob/a0cd6b84/test/unit/subagents-slash-command-bridge.test.ts)

### 二、headless CLI 进 CI 的真实案例
5. **Backgrind 实测(2026-08,Claude Code 2.1.x)**:无 allowlist 的 `dontAsk` 模式下 agent 被拒后照样 exit 0 + `subtype:"success"`、工作树零改动、花 $0.383——CI 假绿;必须显式 gate `permission_denials` 与 `is_error`,且 `Edit`/`Write` 是两个工具需分别放行。[Backgrind](https://backgrind.com/blog/run-a-coding-agent-in-ci/)
6. 同文给出鉴权三选:`ANTHROPIC_API_KEY`(组织共享)/`CLAUDE_CODE_OAUTH_TOKEN`(绑定个人订阅,且与 `--bare` 不兼容——bare 模式不读 OAuth)/OIDC federation(无静态密钥);配套 `--max-turns`、`timeout-minutes`(默认 360 太长)、prompt 一律经 `env:` 注入防 shell 注入。[同上](https://backgrind.com/blog/run-a-coding-agent-in-ci/)
7. **官方指引**:headless 文档明确 `-p` + `--output-format stream-json/json`、permission-mode 体系;SDK 提供 SessionStore 把 transcript JSONL 镜像到 S3/Redis 以跨主机 resume(转录留存的官方机制);claude-code-sdk-python 的 CI 只单测 CLI 参数构造(`_build_command` 断言含 stream-json),不真跑。[headless docs](https://code.claude.com/docs/en/headless)、[session-storage](https://code.claude.com/docs/en/agent-sdk/session-storage)、[sdk tests](https://github.com/anthropics/claude-code-sdk-python/blob/cfdd28a2/tests/test_transport.py)
8. **Codex 侧**:官方 `codex exec` 非交互文档 + `openai/codex-action@v1`(装 CLI、起 Responses API proxy、权限收敛);cookbook autofix 示例强调"patch 生成与 PR 发布分离"的安全布局。[codex exec](https://www.codex-docs.com/en/docs/non-interactive-mode)、[GitHub Action](https://www.codex-docs.com/en/docs/github-action)、[cookbook](https://developers.openai.com/cookbook/examples/codex/autofix-github-actions)

### 三、规则遵循度量的实现先例
9. **claudemd-check(最接近我们设计)**:scenario=prompt+种子文件+确定性断言(`transcript_match/not_match`、`file_exists/absent`、`file_contains`、`command` 兜底),真 headless 会话跑 N 次×临时 workspace,输出 per-rule adherence 率并与已提交基线 diff,低于阈值 CI exit 1;transcript 断言刻意排除规则原文与工具结果防假阳。[claudemd-check](https://github.com/BenMalaga/claudemd-check)
10. **rulebench**:trap 测试在 fresh 隔离会话中对比多组规则配置(无规则/仅 CLAUDE.md/+skills),量化"规则是否真改变行为"的 delta;**agent-rules** 则做事后审计:从 CLAUDE.md/AGENTS.md/.cursorrules 抽祈使规则、扫 session transcript 找违规点。[rulebench](https://github.com/ralfyishere/rulebench)、[agent-rules](https://github.com/0xelitesystem/agent-rules)
11. **agents-md-evals** 基于 skill-creator 框架对 AGENTS.md 做 A/B(规则 vs 无规则),定位"哪些规则真的改变行为、哪些只耗 context"。[agents-md-evals](https://github.com/vltansky/agents-md-evals)

### 四、agent 测试的"Playwright 级"工具
12. **AgentHound**:pytest-native,录制真实 agent 会话后确定性回放、断言行为与正确性、零 API 调用(VCR 思路移植到 agent)。[AgentHound](https://github.com/martinwells/agenthound);同类:bit-exact 回放含模型 API/工具/网络/时钟 mock 的 [agentreplay](https://github.com/gadda00/agentreplay)
13. **agenteval(Minitour)**:场景 = prompt + fake MCP server(种子已知状态)+ 断言,Claude Code 为首个 provider——"断言用了指定 MCP"可通过假 MCP 实现而非真 MCP。[agenteval](https://github.com/Minitour/agenteval)
14. 未检索到 Arcade / Second.dev / DevQA 有公开的通用 agent 行为测试框架;该命名空间下公开可用的是上述 record-replay + fake-server 谱系(见 Gaps)。

### 五、多 harness × model 矩阵测试
15. **Harbor(Terminal-Bench 官方框架)**:统一 config 内置 claude-code/codex/openhands 等 adapter,每任务独立 Docker 环境、用后即删,可经 Daytona/Modal 等并行数千环境并导出 rollout。[harbor](https://github.com/harbor-framework/harbor)、[adapters](https://harborframework.com/docs/adapters)
16. **coding-agent-eval(cae)**:单文件实现 `AgentAdapter` 协议即可接入新端(含 mock adapter 免费冒烟);统一任务集(SWE-bench 导入)、git diff 捕 patch、重跑 test_cmd 判分、`--max-cost-usd` 累计成本熔断、结果 JSON 已存在即跳过(断点续跑)、订阅计费 cost_usd=None 特判。[cae](https://github.com/ttxs69/coding-agent-eval)
17. **Red Hat coding_agent_bench / swe-bench-essential**:Harbor 上跑多 harness(Claude Code/Codex/OpenClaw,含 vLLM 自托管模型),记录 traces/token/latency/cost;方法论上有 Scaffold Effect 论文与 HarnessBench 佐证:跨 harness 对比必须固定任务集与判分,否则 harness 效应与模型效应混淆。[redhat-et](https://github.com/redhat-et/coding_agent_bench/)、[swe-bench-essential](https://github.com/Prism-Shadow/swe-bench-essential)、[arXiv 2607.22585](https://arxiv.org/html/2607.22585)

## Sources
- Kept: Backgrind CI 实测博客(headless 假绿/鉴权/权限唯一一手实测)、claudemd-check(规则遵循回归测试范式)、cae 与 Harbor(多端 adapter + 成本/续跑工程细节)、anthropics/skills + skillgrade(官方生态现状)、agenteval/AgentHound(mock 与回放谱系)
- Dropped: AgentPatterns/iso(仓库 404)、Codex 知识库第三方站(danielvaughan,与官方 docs 重复)、ccaf-exam.guide(考试复习站,非一手)

## Gaps
1. 未找到任何公开项目专门测"slash command 执行后产物正确性"(最接近的是 CLAUDE.md probe 与 skill evals.json)——印证该空白真实存在。
2. Arcade/Second.dev/DevQA 无公开 agent 测试框架可引;若指闭源产品则无法对照。
3. Kimi CLI(`kimi -p`)headless 模式无公开 CI 实践文档;四端矩阵中该端只能靠自行验证。
4. claudemd-check/rulebench 等均单端(Claude Code),多端规则遵循矩阵无先例,我们的矩阵是增量。

## 对我们设计的增补建议
1. **判分必须 gate `permission_denials` 与 `is_error`**:dontAsk 被拒的 run 会 exit 0 假绿,只断言产物会把"没干活"误判为通过(Backgrind 实测)。
2. **阶段①加幂等双跑快照**:同一 fixture 上连跑两次安装命令、diff workspace byte-identical——jarvy 已验证该模式可抓"重复追加"类回归。
3. **transcript 全量留存 + SessionStore 式归档**:每 run 保存 stream-json 原始轨迹与结果 JSON 到 results/ 目录,支持断点续跑(已有结果即跳过)与失败事后回放(cae + 官方 SDK 双重先例)。
4. **mock/免费冒烟车道前置**: harness 自身先用 mock adapter 或 `--smoke` 跑通判分管线,再进付费矩阵——把"harness bug"与"agent 失败"分离(cae/skillgrade)。
5. **多层成本熔断**:`--max-turns` + `timeout-minutes` + 累计 `--max-cost-usd`,注意被阻塞的 run 照样烧钱(Backgrind:空跑 $0.383 > 修 bug $0.376)。
6. **transcript 断言排除规则原文**:断言"是否用了 pnpm"时须排除 agent 朗读规则文本与工具结果,防假阳(claudemd-check 的关键设计)。
7. **probe prompt 经 env 注入、不内联 shell**:防注入且避免引号转义污染探针语义(Backgrind)。
8. **规则遵循率对基线 diff 具名失败**:提交 adherence 基线文件,夜间跑出 `▼ rule7: 100%→60%` 式报告,低于阈值 CI 红——多 run 矩阵的判分报告形态(claudemd-check)。
9. **"必须用指定 MCP"探针改用 fake MCP server**:种子状态+断言调用记录,免真实 MCP 依赖与网络波动(agenteval)。
10. **模型与 CLI 版本双 pin**:`--model` 显式指定 + 各端 CLI 版本锁文件,防默认模型漂移静默改变成本与行为(Backgrind + cae)。
