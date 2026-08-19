---
name: rule-config
description: "配置 Claude Code 与 Codex 规则：创建 rules 规则文件、配置目录结构和项目级提交开关"
disable-model-invocation: true
---

# Claude Code 与 Codex 规则配置

## 概述

配置 Claude Code 与 Codex 的规则：创建并维护 `.claude/rules/` 下 7 个框架受管规则文件，内容 drift 时执行框架权威全覆盖；`code-usage.md` 按最终项目类型从 `code-usage-coding.md` / `code-usage-noncoding.md` 单选来源并以固定名称落地。流程还会将 CLAUDE.md 与 AGENTS.md 的 L0 受管区块升级到当前 **v2**（受支持旧版 v0、v1），创建 `cadence/` 产物目录、迁移历史产物、保守合并 `openspec/config.yaml`，并按需配置 CodeGraph 与 Playwright；入口项目配置仅维护产物自动提交开关，不检测或写入技术栈。入口中的 `## 强制规则` 不再以“缺失摘要行追加”为语义，而是执行**强制规则章节规范化**：创建、清理退役引用、按权威顺序重排并替换旧文案，同时保留无法识别的用户内容。所有需备份分支先将原文件复制归档到 `cadence/legacy/<14位时间戳[-N]>/<相对项目根路径>`，原位文件不动，再以 `atomic_write` 原子发布。

脚本报告始终提供不影响 `overall` 的顶层 `warnings` 数组；其实际 code 为 `USER_LINES_KEPT`、`DUPLICATE_H2`、`ORPHAN_RULE6`、`INVALID_TOGGLE`、`L0_DEDUP`，详情见 `references/merge-semantics.md` §11.3。入口首个 `## 项目配置` 章节还会确保唯一的“产物自动提交（design/plan）”开关：缺失时写入 `关闭`，合法用户值保留，非法值保留原文并报告 warning；既有技术栈等项目配置内容逐字保留，不由脚本检测或写入。Agent 读取时以 CLAUDE.md 为准、AGENTS.md 兜底；两者不一致按关闭处理并提示 `ENTRY_TOGGLE_MISMATCH`（这是读取层告警，不是脚本 `warnings` code）。

全部探测、非框架资产合并与受管文件写入由关联脚本 `scripts/rule-config.py` 以 dry-run / apply 两阶段完成。框架受管规则文件绝不执行章节合并，也不生成“项目补充”或“原项目补充”。Agent 只负责定位脚本、按本文件编排调用、解读报告；当前系统无活跃冲突类型，两模式全程不经用户决策（决策文件机制休眠兜底，见 references/merge-semantics.md §11.6）；不得由 Agent 自行读写目标项目的受管文件。合并与冲突处理的权威定义见 `references/merge-semantics.md`，本文件不重复其十张表。

## 参数模式

支持以下调用方式：

```text
/rule-config
/rule-config no-interrupt
/rule-config --no-interrupt
```

- **等价规范化（强制）**：命令参数中的裸 token `no-interrupt` 与 `--no-interrupt` 完全等价，均进入 no-interrupt 模式；Agent 必须把裸 token `no-interrupt` 规范化为脚本的 `--no-interrupt` 标志后再调用脚本，不得把裸 token 原样透传给脚本。
- 未携带上述 token：进入普通模式。
- 两种模式互斥；no-interrupt 的权威合并与禁迁移规则不得应用于普通模式。

### 意图参数（两模式均可携带）

用户明确表达以下意图时，Agent 将其透传为脚本标志：

| 用户意图 | 脚本标志 | 语义 |
|----------|----------|------|
| 指定项目类型 | `--project-type coding\|non-coding` | 普通模式下仅能把检测为 non-coding 的项目提升为 coding；no-interrupt 模式完全忽略（以检测结果为准） |
| 忽略产物目录 | `--ignore-cadence` | 将 `cadence/` 追加到 `.gitignore`（默认不追加） |
| 启用 Playwright | `--enable-playwright` | 创建 `.claude/rules/playwright.md` 并补摘要（默认跳过） |
| 强制启用 CodeGraph | `--enable-codegraph` | 非 Coding 项目也执行 CodeGraph 安装与初始化（默认仅 Coding 项目） |

## 调用方式

**第一步——定位脚本（与 pre-check 同款约定）**：脚本是本 rule-config skill 的关联脚本。Agent 按以下候选根顺序定位并拼出完整绝对路径，记为 `<RULE_CONFIG_PY>`：

1. plugin 缓存：`<plugin 缓存根>/cadence-init/skills/rule-config/scripts/rule-config.py`。
2. 仓库安装根：`<skill 安装根>/cadence-init/skills/rule-config/scripts/rule-config.py`。

若候选根下 `scripts/` 缺失，说明命中了不含关联脚本的旧版本缓存；重新安装或刷新 plugin 后重试，不得从其他项目目录复制脚本。脚本只读，不要 `cd` 进 skill 目录，也不要把脚本复制到别处执行。

**第二步——确定报告与决策路径**：报告 `<REPORT>` 与决策文件 `<DECISIONS_JSON>` 是临时中间产物，必须位于项目根之外。用 `mktemp` 在 `/tmp` 生成原子唯一路径（如 `mktemp -t rule-config-report.XXXXXX.json`），记住字面值，后续每条命令直接写出。脚本拒绝项目根内的 `--report` / `--decisions` 路径（退出码 2）。

**第三步——调用脚本**：

```bash
# 阶段一：dry-run（零写入，只产出计划、冲突清单与备份需求）
python3 "<RULE_CONFIG_PY>" dry-run --project-root "<PROJECT_ROOT>" --report "<REPORT>" [--no-interrupt] [意图参数]

# 阶段二：apply（执行发布；普通模式有计划内冲突时必须携带 --decisions）
python3 "<RULE_CONFIG_PY>" apply --project-root "<PROJECT_ROOT>" --report "<REPORT>" [--decisions "<DECISIONS_JSON>"] [--no-interrupt] [意图参数]
```

**PyYAML 缺失（退出码 77）**：脚本依赖 PyYAML，缺失时以退出码 77 退出并照常写出报告。此时改用 `uvx --with pyyaml python "<RULE_CONFIG_PY>" ...` 以相同参数重跑（报告路径可复用或重新 `mktemp`）。

## 两阶段流程

### 普通模式

1. **dry-run**：脚本只读探测目标项目，报告给出计划动作（含 drift 资产的 `replace`/归档需求），对项目零写入。
2. **读 plan**：Agent 读取报告中的计划，向用户汇报将以模板权威覆盖/处理的资产清单与归档位置。
3. **apply**：执行阶段二命令。当前系统无活跃冲突类型，计划不要求决策文件；`--decisions`/`validate_decisions`/`default_keep` 机制保留休眠兜底（未来引入需用户决策的冲突类型时恢复"逐条提问、每次一问、附带推荐默认项"流程，语义见 references/merge-semantics.md §11.3/§11.6）。

### no-interrupt 模式

单次 apply：直接执行 `apply --no-interrupt` 一次完成（可选先跑 dry-run 摸底）。脚本不读取也不要求决策文件，全部冲突按 `references/merge-semantics.md` 的权威规则内部决策并记入报告。此模式禁止 Agent 调用 `AskUserQuestion`、`request_user_input` 或等价提问工具，禁止等待用户输入。

**汇报冲突实际动作（强制）**：两模式汇报 drift 处理结果时，Agent MUST 依据报告 `steps[].actions[]` 条目的 `action`/`branch`（如 `overwritten`/`authoritative-overwrite`/`l1-authoritative-replace`/`rules-apply-removed`/`template-replace`）描述**实际执行动作**。冲突清单已不再承载 drift 条目。

## 有界扫描说明

项目类型检测使用一次有界首命中扫描。以下命令**仅用于项目类型判定**，其剪枝目录清单与脚本 `PRUNE_DIRS` 常量逐项一致，不得增删：

```bash
find . \
  \( -type d \( -name .git -o -name .claude -o -name .claude-plugin -o -name .codex -o -name .pi -o -name .kimi-code -o -name .codegraph -o -name cadence-init -o -name Cadence-skills \
    -o -name node_modules -o -name vendor -o -name venv -o -name .venv -o -name env -o -name .env \
    -o -name dist -o -name build -o -name coverage -o -name .next -o -name target -o -name __pycache__ \) -prune \) \
  -o \( -type f \( -name '*.java' -o -name '*.js' -o -name '*.ts' -o -name '*.py' -o -name '*.go' \
    -o -name '*.php' -o -name '*.rs' -o -name '*.rb' -o -name '*.swift' -o -name '*.kt' -o -name '*.c' \
    -o -name '*.cpp' -o -name '*.cs' \) -print -quit \)
```

扫描有输出，或存在 `package.json`、`pyproject.toml`、`Cargo.toml`、`go.mod`、`pom.xml`、`build.gradle` 等主工程配置 → **Coding 项目**；两者全无 → **非 Coding 项目**。项目类型按两模式唯⼀规则确定最终 `project_type`：no-interrupt 模式以检测结果为准（`--project-type` 完全忽略）；普通模式下 `--project-type coding` 仅能把检测为 non-coding 的项目提升为 coding（检测为 coding 时无论 CLI 取何值均为 coding）。

## 报告解读

报告为 JSON。`overall` 取值：`ok`（全部成功）/ `degraded`（可降级项失败但已兜底，如 CodeGraph install/init/status 失败）/ `fail`（失败关闭）。提取示例：

```bash
# 总体结果与项目类型
python3 -c "import json;d=json.load(open('<REPORT>'));print(d['overall'], d['project_type'])"
# 冲突清单（决策文件机制的休眠兜底字段；当前系统无活跃冲突类型，两模式不依赖此清单）
python3 -c "import json;d=json.load(open('<REPORT>'));print(json.dumps(d.get('conflicts',[]),ensure_ascii=False,indent=2))"
# 各步骤状态
python3 -c "import json;d=json.load(open('<REPORT>'));print([(s['name'],s['status']) for s in d['steps']])"
# 各资产实际动作明细（两模式汇报 drift 实际动作的权威依据）
python3 -c "import json;d=json.load(open('<REPORT>'));print([(a.get('path'),a.get('action'),a.get('branch')) for s in d['steps'] for a in s.get('actions',[])])"
# 规范化诊断（始终存在；不改变 overall）
python3 -c "import json;d=json.load(open('<REPORT>'));print(d['warnings'])"
# 失败详情与恢复建议
python3 -c "import json;d=json.load(open('<REPORT>'));print(d.get('failure'))"
```

## 失败关闭

| 退出码 | 含义 | 恢复建议 |
|--------|------|----------|
| 0 | 成功（含 `degraded`，降级详情见报告） | 查看报告确认降级项，必要时按报告提示人工补齐 |
| 1 | 执行失败（决策缺失或不符、备份屏障失败、候选验证失败、发布失败等） | 读报告 `failure.file` / `failure.reason` / `failure.recovery`，修复后以相同参数重跑 |
| 2 | 用法错误（参数非法，或 `--report` / `--decisions` 路径位于项目根内） | 按本文件"调用方式"修正参数与路径后重跑 |
| 77 | 缺少 PyYAML 依赖 | 改用 `uvx --with pyyaml python "<RULE_CONFIG_PY>" ...` 重跑，或先安装 PyYAML |

任何失败分支脚本都先写报告再退出；失败时目标项目保持原样，已创建的恢复归档位于 `cadence/legacy/<14位时间戳[-N]>/<相对项目根路径>`，归档副本与原位文件均保留。不得跳过报告直接重试，也不得由 Agent 手工写入受管文件绕过失败关闭。

## 下一步

成功报告的 `hints.next` 固定为 `mcp-configuration`：rule-config 完成后，将配置结果交接给 `mcp-configuration` skill 进行 MCP 配置。

## 合并语义

合并与冲突处理的权威定义（NC/OS/L1/L0/RF/SM/OP/CS/CG/HM 十张表共 64 行，含 RF-05 框架权威全覆盖、SM-01~05 章节规范化与 L0 v2 迁移）见 `references/merge-semantics.md`；条款到测试的逐条对账见 `tests/skill-clause-map.md`。需要了解具体分支语义时按需加载上述文件，不要在本文件中重复维护。
