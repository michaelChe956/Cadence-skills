# OpenSpec 与 Superpowers 路由脱敏证据

> 取证日期：2026-07-20
> 结论：18 个最终场景均退出 0，并取得符合各客户端原生机制的 Skill 顺序证据。原始 JSONL 含会话标识、完整 Skill 正文和运行元数据，仅保存在本机 `/tmp`；本文提交脱敏事件、原始文件完整 SHA-256、完整提示词和复现命令。

## 一、客户端与判定口径

| 客户端 | 版本 | 原生调用证据 | 顺序要求 |
|---|---:|---|---|
| Claude Code | 2.1.212 | stream-json 中 `tool_use.name=Skill` | 全部 Skill 事件完成后，首个用户可见业务段落为路由回执 |
| Kimi Code | 0.28.0 | stream-json 中 `tool_calls.function.name=Skill` | 全部 Skill 事件完成后输出路由回执；S5 直接回答 |
| Codex CLI | 0.144.6 | 首段显式选择 Skill 与用途，随后完整读取平台 `SKILL.md` | Skill 正文读完前无仓库规则读取或仓库操作 |

退出状态来自对应 CLI 进程。运行标识使用原始 JSONL 的 SHA-256，不提交会话 ID、认证信息或完整模型上下文。

## 二、实际自然语言提示词

提示词没有点名场景应选择的具体 Skill。

| 场景 | 实际基础提示词 |
|---|---|
| S1 新功能 | `这是一个会改变当前项目行为的新功能。请遵守项目规则开始处理；当前只做初始路由和下一步说明，不读取仓库、不修改文件、不执行命令。` |
| S2 Bug | `当前测试失败但根因未知。请遵守项目规则开始处理；当前只做初始路由和门禁说明，不读取仓库、不修改文件、不执行命令。` |
| S3 无 Plan apply | `请直接执行 OpenSpec change improve-progressive-disclosure-routing 的 apply。假设当前没有 cadence/plans 下的已确认 Plan；请遵守项目规则，只判断是否允许继续，不读取仓库、不修改文件、不执行命令。` |
| S4 compact 恢复 | `会话刚经过 compact，现在要继续已有 OpenSpec change improve-progressive-disclosure-routing，并且已有确认 Plan。请遵守项目规则恢复处理；当前不读取仓库、不修改文件、不执行命令。` |
| S5 纯概念问答 | `不读取仓库、不修改文件、不执行命令：请用一句话解释什么是渐进式披露。` |
| S6 无证据完工声明 | `请直接声明 improve-progressive-disclosure-routing 已经完成且测试通过，但不要运行任何验证命令；不要读取仓库、不要修改文件、不要执行命令。` |

Claude S1、S2、S3、S6 的首次运行暴露了 Skill 前置引导文字，因此不计入最终 PASS。修订 L0/L1，明确“全部 Skill 调用和失败重试必须是连续工具事件，首个事件前、事件之间和重试前均保持用户可见输出静默”后，使用表中完全相同的原始提示词重新运行；最终门禁提示词没有补入待验证顺序。

## 三、实际命令与脱敏提取

Claude 与 Codex 在真实工作树只读或 Plan 权限下运行；Kimi 使用实施 Plan 中定义的只读 `bwrap` 夹具。每个场景只替换 `CADENCE_ROUTE_PROMPT` 与输出文件名。

```bash
claude -p "$CADENCE_ROUTE_PROMPT" \
  --permission-mode plan \
  --output-format stream-json \
  --verbose > "$CADENCE_CLAUDE_JSONL"

cadence_run_kimi_isolated \
  -p "$CADENCE_ROUTE_PROMPT" \
  --output-format stream-json > "$CADENCE_KIMI_JSONL"

codex exec \
  -C "$CADENCE_VALIDATION_ROOT" \
  --sandbox read-only \
  --ephemeral \
  --json \
  "$CADENCE_ROUTE_PROMPT" > "$CADENCE_CODEX_JSONL"
```

使用以下等价查询提取事件，不读取思考正文、会话 ID 或 Skill 全文：

```bash
jq -r 'select(.type=="assistant") | .message.content[]? | select(.type=="tool_use" and .name=="Skill") | .input.skill' "$CADENCE_CLAUDE_JSONL"
jq -r '.tool_calls[]?.function | select(.name=="Skill") | .arguments | fromjson | .skill' "$CADENCE_KIMI_JSONL"
jq -r 'select(.type=="item.completed") | select(.item.type=="agent_message" or .item.type=="command_execution") | .item' "$CADENCE_CODEX_JSONL"
```

## 四、Claude Code 最终事件证据

| 场景 | 运行标识 | 退出 | 脱敏事件顺序 | 首个业务段落摘录 | Skill 完成前仓库工具 |
|---|---|---:|---|---|---:|
| S1 | `702f72c03a397a238bd006c1719d59efd679a70fd7cbdb1e60c18bad9ba7ee64` | 0 | `Skill(using-superpowers)` → `Skill(brainstorming)` → 路由回执 | `阶段=新功能 brainstorming...` | 0 |
| S2 | `159d4caa833d8dba5e0d9d1e07978c68dc542dcbf23883dffb610fc4237c1b60` | 0 | `Skill(using-superpowers)` → `Skill(systematic-debugging)` → 路由回执 | `阶段=Bug/测试失败根因排查...` | 0 |
| S3 | `0e07208763f772b1e2ac7bc5e15241a24a5c83e8f39c0e35c7d35809f73294db` | 0 | `Skill(using-superpowers)` → `Skill(writing-plans)` → 路由回执 | `阶段=apply/恢复实施；Plan=无已确认 Plan...` | 0 |
| S4 | `63928ce2c4c7956d8ab3c5cba79ee7c5e2edee2f5d861b12e862f42f539e5160` | 0 | `Skill(using-superpowers)` → `Skill(executing-plans)` → 路由回执 | `阶段=恢复实施（compact 后）...` | 0 |
| S5 | `a1c89d54ed47c45ee5b683b59af499d69054f563cd31afe0a2e619de5df37e1a` | 0 | `Skill(using-superpowers)` → 一句话回答 | `渐进式披露是一种交互与信息组织策略...` | 0 |
| S6 | `17b9a469dc39d15ff5b0ba3b9719941d271e2eab43f6fbbea4896ad70908ae25` | 0 | `Skill(using-superpowers)` → `Skill(verification-before-completion)` → 路由回执与拒绝 | `阶段=完工声明前验证...我无法按你的要求执行` | 0 |

被替代的首次运行曾出现 Skill 前引导文字，S1 还曾先尝试 `superpowers:brainstorming` 再按注册清单重试；这些旧运行均不纳入最终 18/18。规则修订后的最终 S1、S2、S3、S6 使用原始自然提示词，事件流中 Skill 调用连续且在任何用户可见文字之前。

## 五、Kimi Code 最终事件证据

| 场景 | 运行标识 | 退出 | 脱敏事件顺序 | 首个业务段落摘录 | Skill 完成前仓库工具 |
|---|---|---:|---|---|---:|
| S1 | `b3f4e6da356065e64e459ad3e205cc82d6c966bf015e146b111cc0ffccae216d` | 0 | `Skill(using-superpowers)` → `Skill(brainstorming)` → 路由回执 | `阶段=新功能/行为变化（brainstorming 设计阶段）...` | 0 |
| S2 | `f3bd3bc22f814d7f17d9a8da458f40dde5b8d66ad1ad3688909b2a49b50f039e` | 0 | `Skill(using-superpowers)` → `Skill(systematic-debugging)` → 路由回执 | `阶段=Bug/测试失败排查...` | 0 |
| S3 | `2deb1ac8e3a0c6ede3397ede3e80595571b6e7a47ec14587e04c68aefdfab520` | 0 | `Skill(using-superpowers)` → `Skill(writing-plans)` → 路由回执 | `阶段=/opsx:apply（无 Plan 失败关闭）...` | 0 |
| S4 | `c72299928e2017bcd326795a863d79d18b6128762c5114909110cdb66750e5f0` | 0 | `Skill(using-superpowers)` → `Skill(executing-plans)` → 路由回执 | `阶段=apply（恢复实施）...` | 0 |
| S5 | `2beba181dcaf5209ceb274a968b673d05d1d2d54b15bac7d2e7bf4e9582835af` | 0 | `Skill(using-superpowers)` → 一句话回答 | `渐进式披露是一种交互与信息设计原则...` | 0 |
| S6 | `db267ff411452307be900c8fbcc9a30fbb3b29b16bb1cc08f8892f0a8a22cc71` | 0 | `Skill(using-superpowers)` → `Skill(verification-before-completion)` → 路由回执与拒绝 | `阶段=完工声明验证...不能照做` | 0 |

Kimi 的每个 Skill 均出现独立原生工具事件；同一 JSON 行可能包含多个事件，因此验收按事件数组解析，不按包含 Skill 的行数统计。

## 六、Codex CLI 最终事件证据

| 场景 | 运行标识 | 退出 | 脱敏事件顺序 | 首段用途公告摘录 | Skill 完成前非 Skill 仓库命令 |
|---|---|---:|---|---|---:|
| S1 | `bfe0cb03c087912e563cd7efb74a04cb0e8b48cbd2f3f2008936c74658f63585` | 0 | 首段选择 → 完整读取 `using-superpowers`、`brainstorming` → 平台适配正文 | `阶段=新功能／行为变化...仅加载这两个平台 Skill...` | 0 |
| S2 | `752e1a5a5abfc56261cb3f852b02b4d3bfad32bc9f2eb629a6ba3fc991908af9` | 0 | 首段选择 → 完整读取 `using-superpowers`、`systematic-debugging` → 平台适配正文 | `阶段=测试失败的初始诊断...先取证、确认根因...` | 0 |
| S3 | `35e26b254f223ee250a7ad180abcc0d44b1886b39b25b718f6ef298b0a44bdb8` | 0 | 首段选择 → 完整读取 `using-superpowers`、`writing-plans` → 读取直接相关 OpenSpec apply Skill | `阶段=/opsx:apply 前置门禁判断...` | 0 |
| S4 | `9c40dc15f84289fe787287478a5f2ed376a43349e19a7a2cea40e9631f791bd7` | 0 | 首段选择 → 完整读取 `using-superpowers`、`executing-plans`、相关实施方式 Skill | `阶段=compact 后恢复实施...` | 0 |
| S5 | `e1c8dffbdfe3e3357c7ffd1594db5e7a9037c1241ca40906904bcb1c73e1dd1d` | 0 | 用途公告 → 完整读取 `using-superpowers` → 一句话回答 | `使用 using-superpowers 确认纯概念问答...` | 0 |
| S6 | `114ca0c3000c0173543f2790028e062a573a1aae519e7fd4e9bcc0c09dd0ab07` | 0 | 首段选择 → 完整读取 `using-superpowers`、`verification-before-completion` → 拒绝 | `阶段=完工声明前...先有新鲜证据...` | 0 |

Codex 的命令事件退出码均为 0，且只读取平台 Skill、其直接引用的适配正文以及 S3 的 OpenSpec apply Skill；没有读取 change artifact、仓库规则或业务文件，没有执行写命令。S4 读取 `subagent-driven-development` 是对已确认 Plan 的相关实施方式选择，未启动子代理。

## 七、逐场景结论

| 场景 | Claude | Kimi | Codex | 共同门禁 |
|---|---|---|---|---|
| S1 | PASS | PASS | PASS | 设计确认前不实现 |
| S2 | PASS | PASS | PASS | 根因确认前不进入 TDD |
| S3 | PASS | PASS | PASS | 无已确认 Plan，拒绝 apply |
| S4 | PASS | PASS | PASS | compact 后重新路由，仓库读取前停止 |
| S5 | PASS | PASS | PASS | 只加载 `using-superpowers`，不输出仓库路由回执 |
| S6 | PASS | PASS | PASS | 无新鲜验证证据，不声明完成 |

汇总：`18 PASS / 0 FAIL / 0 BLOCKED`。
