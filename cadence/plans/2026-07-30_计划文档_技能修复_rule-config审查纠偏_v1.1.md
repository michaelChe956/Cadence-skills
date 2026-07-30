# rule-config 审查纠偏 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Change:** 无新增 Change。该计划只修复已确认的测试可移植性、测试断言与文档准确性；不改变 `rule-config` 的项目类型识别规则，保留 `env` 与 `.env` 的剪枝。

**Goal:** 让生命周期回归能在 macOS（BSD 工具链）和 Linux（GNU 工具链）完整执行，消除文件系统枚举顺序造成的假失败，并使计划与设计描述符合实际 22 个用例和验证模型；双平台验收必须覆盖优先使用 `sha256sum` 与仅有 `shasum -a 256` 时的回退路径。

**Architecture:** 以 Bash、POSIX awk 与同目录临时文件的 `mv` 替换首个标记文本，避免 BSD/GNU `sed -i` 及 `0,/…/` 的方言差异；源码扫描测试只断言“恰好一个、位于业务目录、扩展名受支持”的结果。文档仅同步已实现的事实，不调整运行时 Skill 的剪枝列表。

**Tech Stack:** Bash、awk、现有 OpenSpec CLI/PyYAML 生命周期测试、Markdown。

## Global Constraints

- 仅修改 `.worktrees/bugfix-b-0730` 下的 Cadence-skills；不得修改 ontology 或 `.claude/rules`。
- 保持 `.venv`、`venv`、`env`、`.env`、`node_modules`、`vendor`、`.claude-plugin`、`cadence-init`、`Cadence-skills` 等既有剪枝策略不变。
- 不新增依赖、业务代码、OpenSpec Change 或自动化工具。
- 生命周期验证不得依赖 macOS 专属或 GNU 专属的 `sed -i` 语法；修改后的 Bash/awk/mv 路径必须同时兼容 macOS 和 Linux。
- SHA-256 文件哈希优先使用 `sha256sum`，不可用时必须回退为 `shasum -a 256`；两者均缺失时必须向 stderr 明确失败，且哈希失败不得被后续管道掩盖。
- 真实扫描测试仍须从 `SKILL.md` 提取并运行 `find` 命令，静态合同检查不得删除。

---

### Task 1: 修复跨平台生命周期验证与审查文档

**Files:**
- Modify: `cadence-init/skills/rule-config/tests/verify-managed-lifecycle.sh`
- Modify: `cadence-init/skills/rule-config/tests/helpers/managed-lifecycle-reference.sh`
- Modify: `cadence/designs/2026-07-30_技术方案_rule-config初始化稳定性修复_v1.0.md`
- Modify: `cadence/plans/2026-07-30_计划文档_技能修复_rule-config初始化稳定性_v1.0.md`

**Interfaces:**
- Consumes: 现有 `record_result`、`SKILL` 与临时测试根目录。
- Produces: BSD/macOS 可执行的首个文本替换；与文件系统顺序无关的业务源码断言；显式 `return 0` 的候选验证成功路径。

- [x] **Step 1: 先写失败态覆盖**

在验证脚本中先添加一个测试辅助断言：当业务目录有 `first.py`、`second.ts` 时，任意一个单行 `./application/*.py` 或 `./application/*.ts` 都合格；多行、空值、剪枝目录路径和其他扩展名都不合格。运行该断言，确认旧的固定 `first.py` 比较无法满足新断言。

- [x] **Step 2: 以可移植替换函数取代五处 GNU sed 调用**

新增 `replace_first_visible_paragraph FILE REPLACEMENT`：用 POSIX awk 仅替换文件中第一次出现的 `首个用户可见段落`，写入同目录临时文件后 `mv` 回原路径。把 235、246、247、292、293 行的五处 GNU `sed -i '0,/…/s//'` 调用改为该函数；函数失败必须返回非零，且实现不得使用 BSD 或 GNU 专属选项。

- [x] **Step 3: 放宽业务源码结果的顺序假设**

新增 `is_single_application_source VALUE`：先以 `awk` 确认非空行数恰为 1，再只接受 `./application/*.py` 或 `./application/*.ts`。用它替换 `source-scan-prunes-excluded` 对 `./application/first.py` 的精确比较；保留“仅剪枝目录为空”和 `pyproject.toml` 回退断言。

- [x] **Step 4: 同步真实语义**

在 `validate_openspec_candidate` 的成功清理后显式 `return 0`。设计文档 4.2 改为“候选在目标配置目录构建、验证在独立临时根目录运行”；4.3 删除未被测试覆盖的“无 --change 基线失败”说法。原计划的三处 `SUMMARY pass=15 fail=0` 改为 `SUMMARY pass=18 fail=0`，并说明 macOS/BSD sed 可直接运行，不依赖临时 GNU sed。

- [x] **Step 5: 验证、审查并提交**

先记录 RED，再运行：

```bash
OPENSPEC_TELEMETRY=0 PYTHONPATH=/private/tmp/task1-python-deps \
  bash cadence-init/skills/rule-config/tests/verify-managed-lifecycle.sh
bash -n cadence-init/skills/rule-config/tests/verify-managed-lifecycle.sh
openspec validate --all --strict
git diff --check
```

Expected: 生命周期测试 `SUMMARY pass=22 fail=0`，在 macOS 与 Linux 的原生工具链下都不需要 GNU sed PATH；其余三个命令退出 0。提交信息：`fix(cadence-init): 稳定 rule-config 生命周期回归测试`。

双平台验收还必须在受控 PATH 下分别验证：保留 `sha256sum` 时的默认路径，以及移除 `sha256sum`、保留 `shasum` 时的完整生命周期；后者必须同样得到 `SUMMARY pass=22 fail=0`。测试还必须覆盖 `env/.env` 剪枝、四类完整 `openspec instructions ... --change ... --json` 命令以及哈希工具缺失/命令失败的透明传播。
