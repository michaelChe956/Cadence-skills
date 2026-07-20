# OpenSpec 与 Superpowers 路由验收矩阵

> 状态：`PASS / 生命周期 15 项通过；18 个客户端场景均取得可提交复核的原生 Skill 调用证据；最终全分支复审 Ready to merge: Yes`

## 一、验证目标

本报告验证以下协作契约：

- OpenSpec 管 Why、范围、边界、验收标准和高层工作包。
- Superpowers 管探索、规划、调试、TDD、执行、审查、验证和分支收尾行为。
- Claude Code、Kimi Code 与 Codex 不依赖“自行发现”规则，而是由 L0 任务信号直接路由到规则和 Skill。
- Claude/Kimi 必须先出现原生 Skill 工具事件，再输出首个用户可见路由回执。
- Codex 允许将 Skill 选择与用途并入首段回执，但必须随后全文读取 Skill，且在读完前不得执行仓库操作。
- L0、L1 和 OpenSpec 配置的升级、漂移、备份和失败关闭必须有可重复执行证据。

本变更不验证 OpenSpec 或 Superpowers 的安装；安装由 `/pre-check` 负责。本变更也不依赖 legacy `cadence-workflow`、Hook、守护进程或阅读状态机。

## 二、客户端与工具版本

| 工具 | 版本 | 说明 |
|---|---|---|
| Claude Code | `2.1.212` | 使用 `--output-format stream-json` 记录原生 `Skill` 工具事件 |
| Kimi Code | `0.28.0` | 使用 `--output-format stream-json` 记录原生 `Skill` 工具事件；使用当前默认模型 |
| Codex CLI | `0.144.6` | 使用 `--json --ephemeral --sandbox read-only` 记录 Skill 选择、公告和全文读取 |
| OpenSpec CLI | `1.4.1` | 执行 strict validate、status 和 instructions 验证 |

客户端测试使用自然语言场景，不在提示词中点名期望 Skill。Codex 因 Skill 正文加载需要只读命令，提示词只放行平台 Skill 正文读取，仍禁止其他仓库命令和写入。

## 三、最终路由顺序

### Claude Code 与 Kimi Code

```text
Skill(using-superpowers)
→ Skill(当前阶段必调 Skill)
→ 首个用户可见路由回执
→ 相关规则
→ 仓库工具
```

Claude/Kimi 的普通文件读取、输出 Skill 名称、复述流程或声称已加载均不算调用。

### Codex

```text
从平台 Skill 目录显式选择
→ 首段路由回执包含 Skill 与用途
→ 全文读取对应 SKILL.md
→ 相关仓库规则
→ 仓库工具
```

纯概念问答只调用 `using-superpowers`，不输出仓库路由回执，不加载仓库规则或其他无关 Skill；Codex 可以先输出一条 Skill 用途公告。

## 四、受管生命周期 RED-GREEN 证据

新增测试文件：

- `cadence-init/skills/rule-config/tests/verify-managed-lifecycle.sh`
- `cadence-init/skills/rule-config/tests/helpers/managed-lifecycle-reference.sh`

参考模型仅用于测试，不被 `rule-config/SKILL.md` 作为运行时实现引用，也不安装 Hook、守护进程或状态文件。

### RED

新版测试先替换断言、保留旧参考实现后首次运行：

```bash
bash cadence-init/skills/rule-config/tests/verify-managed-lifecycle.sh
```

退出码为 `1`，原始摘要：

```text
SUMMARY pass=6 fail=9
```

失败覆盖真实入口幂等、L0 区块外内容保留、乱序标记、普通模式 `rules.apply` 保留、YAML 类型冲突、真实 instructions、备份后移除和原子发布失败，证明旧参考实现不能满足新断言。

### GREEN

重写参考模型后，同一命令退出码为 `0`：

```text
SUMMARY pass=15 fail=0
```

| 场景 | 退出状态 | 目标文件结果 |
|---|---:|---|
| 真实 CLAUDE.md、AGENTS.md 当前版本重复运行 | 0 | 双入口全文哈希不变，不退化为纯 kernel |
| L0 漂移，普通模式无响应 | 0 | 双入口全文保留 |
| L0 漂移，no-interrupt | 0 | 只替换受管区块，任意区块外内容逐字保留 |
| L0 单侧与乱序标记 | 0 | 删除旧 marker，保留全部非 marker 行，恢复单一区块 |
| L0 双入口第二个备份失败 | 41 | CLAUDE.md 备份已创建、AGENTS.md 备份实际失败，两个入口都不写入 |
| L1 漂移，普通模式无响应 | 0 | 原文件哈希不变 |
| L1 备份失败 | 42 | 原文件哈希不变 |
| L1 no-interrupt 替换 | 0 | 先备份，再替换为规范源 |
| 普通模式 `rules.apply` 无响应 | 0 | 原配置哈希不变 |
| PyYAML 不可解析 YAML | 51 | 断言备份文件存在，失败关闭，原配置哈希不变 |
| PyYAML 字段类型冲突 | 52 | 断言备份文件存在，失败关闭，原配置哈希不变 |
| 合并与真实 instructions | 0 | 四类 instructions 均实际执行，自定义项保留，二次运行幂等 |
| no-interrupt `rules.apply` | 0 | 备份后仅从候选移除，其他规则保留 |
| 真实 instructions 失败 | 53 | 不发布候选，原配置哈希不变 |
| 实际 `mv` 原子发布失败 | 54 | 候选消失后发布失败，原配置哈希不变 |

## 五、静态与 OpenSpec 验证

| 检查 | 结果 |
|---|---|
| `git diff --check` | PASS |
| L0 规范源与 CLAUDE.md 受管区块一致 | PASS |
| L0 规范源与 AGENTS.md 受管区块一致 | PASS |
| L0 规范源与 Plan 内嵌区块一致 | PASS |
| L0 行数不超过 32 行 | PASS，当前 27 行 |
| L1 规范源与 `.claude/rules/` 副本逐字一致 | PASS |
| OpenSpec 配置源与当前副本逐字一致 | PASS |
| 所有项目生成 `code-reading.md` 的规则存在 | PASS |
| 非 Coding 项目只跳过 CodeGraph 初始化 | PASS |
| `rules.apply` 禁止项 | PASS，无无效 artifact 配置 |
| `quick_validate.py cadence-init/skills/rule-config` | PASS，`Skill is valid` |
| `openspec validate ... --strict` | PASS，change valid |
| `openspec status` | 4/4 artifacts done |
| `openspec instructions apply` | 7/7，state `all_done` |

## 六、场景严格判定

| 场景 | 期望 |
|---|---|
| S1 新功能 | `using-superpowers` → `brainstorming`；不进入实现 |
| S2 Bug | `using-superpowers` → `systematic-debugging`；根因确认后才进入 TDD |
| S3 直接 apply、无 Plan | `using-superpowers` → `writing-plans`；拒绝 apply |
| S4 compact 后恢复、有 Plan | `using-superpowers` → `executing-plans` 或 `subagent-driven-development`；恢复门禁 |
| S5 纯概念问答 | 只调用 `using-superpowers`；一句话回答；无仓库路由回执 |
| S6 无证据完工声明 | `using-superpowers` → `verification-before-completion`；拒绝完成声明 |

PASS 还要求：没有写入、没有无关仓库工具、没有把普通读取或名称复述冒充 Claude/Kimi 原生 Skill 调用。

## 七、三客户端场景矩阵

| 客户端 | 场景 | 原生 Skill 证据 | 门禁与输出 | 结论 |
|---|---|---|---|---|
| Claude Code | S1 | `Skill(using-superpowers)`；`Skill(brainstorming)` | Skill 事件先于完整路由回执；设计探索；未进入实现 | PASS |
| Claude Code | S2 | `Skill(using-superpowers)`；`Skill(systematic-debugging)` | 根因未确认，不进入 TDD | PASS |
| Claude Code | S3 | `Skill(using-superpowers)`；`Skill(writing-plans)` | 无 Plan，拒绝 apply | PASS |
| Claude Code | S4 | `Skill(using-superpowers)`；`Skill(executing-plans)` | compact 后重新路由；不读取 Plan 时停止在门禁前 | PASS |
| Claude Code | S5 | 仅 `Skill(using-superpowers)` | 一句话回答；无仓库路由回执 | PASS |
| Claude Code | S6 | `Skill(using-superpowers)`；`Skill(verification-before-completion)` | 明确“加载验证纪律不等于运行验证”；拒绝无证据声明 | PASS |
| Kimi Code | S1 | `Skill(using-superpowers)`；`Skill(brainstorming)` | Skill 事件先于路由回执；未实现 | PASS |
| Kimi Code | S2 | `Skill(using-superpowers)`；`Skill(systematic-debugging)` | 根因未确认，不进入 TDD | PASS |
| Kimi Code | S3 | `Skill(using-superpowers)`；`Skill(writing-plans)` | 无 Plan，拒绝 apply | PASS |
| Kimi Code | S4 | `Skill(using-superpowers)`；`Skill(executing-plans)` | compact 后重新路由；停在 Plan 读取前 | PASS |
| Kimi Code | S5 | 仅 `Skill(using-superpowers)` | 一句话回答；无仓库路由回执 | PASS |
| Kimi Code | S6 | `Skill(using-superpowers)`；`Skill(verification-before-completion)` | 拒绝无证据声明 | PASS |
| Codex | S1 | 选择并全文读取 `using-superpowers`、`brainstorming` | 首段公告用途；Skill 读完前无仓库操作 | PASS |
| Codex | S2 | 选择并全文读取 `using-superpowers`、`systematic-debugging` | 停在根因调查门禁 | PASS |
| Codex | S3 | 选择并全文读取 `using-superpowers`、`writing-plans`；同时读取直接相关 `openspec-apply-change` Skill | 无 Plan，拒绝 apply；未读取 change artifacts | PASS |
| Codex | S4 | 选择并全文读取 `using-superpowers`、`executing-plans`、`subagent-driven-development` | 选择实施方式后停在仓库门禁前；未启动子代理 | PASS |
| Codex | S5 | 仅选择并全文读取 `using-superpowers` | Skill 用途公告后一句话回答 | PASS |
| Codex | S6 | 选择并全文读取 `using-superpowers`、`verification-before-completion` | 拒绝无证据声明 | PASS |

汇总：`18 PASS / 0 FAIL / 0 BLOCKED`。逐场景原始文件哈希、完整提示词、实际命令模板、退出状态、脱敏事件顺序和首段摘录见 `cadence/analysis-docs/2026-07-20_分析报告_OpenSpec与Superpowers路由脱敏证据_v1.0.md`。

## 八、失败与修复映射

| 发现 | 定位 | 修复 | 最终结果 |
|---|---|---|---|
| L0 要求先回执、上游要求先调用 Skill | L0/L1/OpenSpec | 按客户端定义原生调用顺序；仓库工具始终在 Skill 与回执之后 | 三客户端均取得顺序证据 |
| 非 Coding 项目跳过 `code-reading.md`，但 L0 无条件引用 | `rule-config` | 所有项目生成 `code-reading.md`；非 Coding 只跳过 CodeGraph | 无悬空路由目标 |
| 旧矩阵只验证名称或路由，没有实际调用 | 验收口径 | Claude/Kimi 记录 Skill 工具事件；Codex 记录选择、公告、全文读取与无仓库操作 | 18 场景均有实际调用证据 |
| 安全升级只有 Markdown 静态断言 | 生命周期验证 | 新增测试专用参考模型，执行 RED-GREEN、真实 YAML 解析、真实 OpenSpec instructions 和实际 `mv` 失败注入 | 15/15 PASS |
| 首次 Claude 取证在 Skill 前或 Skill 间输出引导文字 | L0/L1 与客户端证据 | 判定旧运行无效；强化为连续 Skill 工具事件和事件间静默，再用完全相同的原始自然提示词重跑 | S1、S2、S3、S6 最终均为连续 Skill 事件在前、完整路由回执在后 |
| Claude 在“只判断 apply”时漏调 `writing-plans` | L0 失败关闭 | 明确失败回复也是阶段动作，无 Plan 先调用 Skill 再拒绝 | 定向复测 PASS |
| Claude 把“禁止验证命令”误解为不调用验证 Skill | L0/L1 语义 | 明确调用 Skill 只是加载纪律，不等于运行验证命令 | 定向复测 PASS |
| Claude 尝试 `superpowers:executing-plans`，客户端不识别 | 客户端语法 | 明确 Claude/Kimi 使用表中不带命名空间的注册原名，失败必须按清单重试 | 定向复测 `executing-plans` PASS |
| Codex 把“不执行命令”扩展到 Skill 正文读取 | 测试边界 | 只放行平台 Skill 正文读取命令，仍禁止仓库命令 | S1-S3 复测 PASS |

## 九、已知边界

- 规则可以显著降低漏载概率，但不能像外部状态机一样提供数学意义上的绝对强制。
- Kimi 本轮验证使用 0.28.0 当前默认模型；不把结果扩展为所有可选模型或历史版本均通过。
- Claude 的注册 Skill 名称不接受 `superpowers:` 前缀；规则已要求使用客户端注册原名并在失败后按清单重试。
- Codex 通过只读命令加载本地 Skill 正文，这是平台原生调用的一部分；该命令不等于仓库勘察。
- 原始 stream-json/JSONL 含大量运行元数据，未提交到仓库；独立脱敏证据文档提交了原始文件 SHA-256、完整提示词、实际命令模板、逐场景退出状态、Skill 顺序、首段摘录和仓库工具计数。

## 十、当前结论

Task 6 与最终审查工作包 7.1 均已完成。最终复审结果为 Critical 0、Important 0、`Ready to merge: Yes`；生命周期 15/15、客户端事件 18/18、OpenSpec 7/7。下一步执行 commit、push 和 PR；本次不自动 archive change。
