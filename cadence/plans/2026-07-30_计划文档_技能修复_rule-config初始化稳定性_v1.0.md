# rule-config 初始化稳定性修复 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (- [ ]) syntax for tracking.

**Change:** 无新增 Change。本 Plan 恢复既有契约：openspec/changes/archive/2026-07-20-improve-progressive-disclosure-routing/ 工作包 5.1、7.1，以及 openspec/specs/routing-conformance/spec.md 的候选 instructions 验证和原子发布失败关闭要求；同时遵守 openspec/specs/init-skill-sequencing/spec.md 中 config.yaml 由 rule-config 创建的职责边界。

**Goal:** 使 /rule-config --no-interrupt 能在全新项目完成候选 OpenSpec 配置验证并原子发布，同时让项目类型检测不再把虚拟环境或依赖目录中的文件当作业务源码。

**Architecture:** rule-config 是 Markdown Skill，行为由指令文本定义；既有 Bash 生命周期参考模型只用于回归验证，不接入业务运行路径。修复保持候选先验证、目标后发布的原子语义：在临时验证根目录自建固定名称的临时 Change，并让四类 openspec instructions 显式绑定到它；项目类型检测改为一次、命中首个有效源码即停止的目录剪枝扫描。

**Tech Stack:** Markdown Skill、既有 Bash 生命周期参考模型、OpenSpec CLI、Python/PyYAML（现有验证依赖）。

## Global Constraints

- 只在 .worktrees/bugfix-b-0730 修改 Cadence-skills；/Users/michaelche/Desktop/ontology 仅作只读复现参考，绝不写入。
- 不新建 OpenSpec Change：这是已有规格覆盖的小型 Bug 修复，Plan 不扩大范围或改变验收标准。
- 候选通过 YAML、结构和四类 instructions 验证前，目标 openspec/config.yaml MUST 保持未创建或原样不变；验证失败 MUST 不发布候选。
- 临时验证 Change MUST 仅存在于临时验证根目录，固定名为 cadence-rule-config-validation，且不得依赖目标项目或仓库中某个活动 Change。
- 项目类型检测 MUST 在首个未被剪枝目录下的常见源码文件出现后停止；MUST 剪枝 .venv、venv、node_modules、vendor、cadence-init、Cadence-skills 与框架/构建目录。
- 生命周期测试 MUST 可独立执行，MUST 不引用已归档后消失的活动 Change 路径。
- 不修改 .claude/rules/；不新增业务代码、依赖或自动化工具。
- Markdown 嵌套代码块使用外层 4 个反引号、内层 3 个反引号。

## 文件结构

| 文件 | 责任 | 改动任务 |
|---|---|---|
| cadence-init/skills/rule-config/SKILL.md | 定义项目类型检测与 OpenSpec 候选验证的运行时指令 | Task 1、Task 2 |
| cadence-init/skills/rule-config/tests/helpers/managed-lifecycle-reference.sh | 独立的候选配置生命周期参考模型 | Task 1 |
| cadence-init/skills/rule-config/tests/verify-managed-lifecycle.sh | 对 Skill 合同和参考模型的可重复回归验证 | Task 1、Task 2 |

---

### Task 1: 让候选 OpenSpec 验证在全新临时根目录可运行

映射：已归档 Change improve-progressive-disclosure-routing 工作包 5.1、7.1；Requirement: routing-conformance 的路由目标和版本必须通过静态检查、受管生命周期失败关闭；Requirement: init-skill-sequencing 的 config.yaml 缺失提示语义。

**Files:**

- Modify: cadence-init/skills/rule-config/tests/verify-managed-lifecycle.sh:4-20,196-263
- Modify: cadence-init/skills/rule-config/SKILL.md:634-663
- Modify: cadence-init/skills/rule-config/tests/helpers/managed-lifecycle-reference.sh:240-338

**Interfaces:**

- Consumes: 候选 YAML 文件路径与 CADENCE_OPENSPEC_BIN（缺省为 openspec）。
- Produces: 一个只存在于 mktemp -d 目录的 Change cadence-rule-config-validation，以及四次均带 --change cadence-rule-config-validation --json 的 instructions 调用。
- Invariant: 目标 openspec/config.yaml 不参与临时 Change 创建；参考模型验证失败时保留 apply_openspec 的 53 失败关闭语义。

- [x] **Step 1: 先写会失败的 Skill 合同断言**

在 verify-managed-lifecycle.sh 声明 SKILL="$TEST_DIR/../SKILL.md"，并在既有依赖检查之前加入以下函数和调用，使当前旧 Skill 因缺少临时 Change 约定而失败。

~~~bash
assert_fresh_change_contract() {
  local missing=0
  for needle in \
    'openspec new change cadence-rule-config-validation' \
    '--change cadence-rule-config-validation --json'; do
    if ! rg -Fq -- "$needle" "$SKILL"; then
      printf '缺少 rule-config 候选验证约定: %s\n' "$needle" >&2
      missing=1
    fi
  done
  return "$missing"
}

assert_fresh_change_contract
~~~

- [x] **Step 2: 运行失败态验证**

~~~bash
OPENSPEC_TELEMETRY=0 PYTHONPATH=/private/tmp/task1-python-deps \
  bash cadence-init/skills/rule-config/tests/verify-managed-lifecycle.sh
~~~

Expected: 非零退出，输出“缺少 rule-config 候选验证约定: openspec new change cadence-rule-config-validation”。这证明测试先于实现捕获了截图中的无活动 Change 缺陷。

- [x] **Step 3: 修改 Skill 的候选验证指令**

在 SKILL.md 的 OpenSpec 配置处理第 10 条中，将未限定 Change 的四条 instructions 验证替换为以下要求：

~~~text
必须在临时验证工作区创建固定名称为 cadence-rule-config-validation 的临时 Change，例如执行：
openspec new change cadence-rule-config-validation --description "Temporary candidate validation"

该 Change 只用于验证，不得写入目标项目或复用目标项目的 Change。随后依次运行：
openspec instructions proposal --change cadence-rule-config-validation --json
openspec instructions design --change cadence-rule-config-validation --json
openspec instructions specs --change cadence-rule-config-validation --json
openspec instructions tasks --change cadence-rule-config-validation --json
~~~

同步调整第 12 条和完成报告文字，使失败报告中的命令包含带 --change 的实际命令；不得改变候选、备份或原子发布的既有约束。

- [x] **Step 4: 让参考模型自行创建临时 Change**

在 managed-lifecycle-reference.sh 中删除 change_source 参数及复制逻辑。validate_openspec_candidate 使用固定局部变量，并在复制候选配置后创建 Change：

~~~bash
local change_name=cadence-rule-config-validation

mkdir -p "$validation_root/openspec"
cp "$candidate" "$validation_root/openspec/config.yaml"
if ! (cd "$validation_root" && "$openspec_bin" new change "$change_name" --description "Temporary candidate validation" >/dev/null); then
  rm -rf "$validation_root"
  return 1
fi
~~~

保留现有四类循环，并继续执行：

~~~bash
"$openspec_bin" instructions "$artifact" --change "$change_name" --json > "$output_file"
~~~

同步把 apply_openspec 的参数从六个缩为五个，并把调用改为：

~~~bash
validate_openspec_candidate "$candidate"
~~~

- [x] **Step 5: 移除已归档 Change 的测试耦合并记录真实命令**

删除 CHANGE_SOURCE 变量、依赖检查项和 run_openspec 的第六个参数。成功案例的断言除已有四类 artifact instructions 外，增加：

~~~bash
rg -Fq 'new change cadence-rule-config-validation' "$case_root/instructions.log"
rg -Fq -- '--change cadence-rule-config-validation --json' "$case_root/instructions.log"
~~~

这使仪器化 OpenSpec 包装器证明参考模型确实从空临时根目录创建 Change 后再验证候选，而不是只检查文字。

- [x] **Step 6: 运行通过态回归**

~~~bash
OPENSPEC_TELEMETRY=0 PYTHONPATH=/private/tmp/task1-python-deps \
  bash cadence-init/skills/rule-config/tests/verify-managed-lifecycle.sh
~~~

Expected: 退出 0，末行是 SUMMARY pass=18 fail=0，且不再出现缺少测试依赖: .../openspec/changes/improve-progressive-disclosure-routing。若 OpenSpec CLI 的遥测仅写 stderr 但退出码为 0，以退出码和 summary 为准，不把遥测网络噪声当作候选验证失败。

- [x] **Step 7: Commit**

~~~bash
git add cadence-init/skills/rule-config/SKILL.md \
  cadence-init/skills/rule-config/tests/helpers/managed-lifecycle-reference.sh \
  cadence-init/skills/rule-config/tests/verify-managed-lifecycle.sh
git commit -m "fix(cadence-init): 为 rule-config 候选验证创建临时 change"
~~~

---

### Task 2: 让项目类型检测跳过依赖和虚拟环境

映射：已归档 Change improve-progressive-disclosure-routing 工作包 7.1；Requirement: managed-rule-lifecycle 的初始化后的业务项目生成协作规则；截图复现中 backend/.venv/lib/python3.11/site-packages/anyio/* 被误收集的根因。

**Files:**

- Modify: cadence-init/skills/rule-config/tests/verify-managed-lifecycle.sh:4-40
- Modify: cadence-init/skills/rule-config/SKILL.md:117-139

**Interfaces:**

- Consumes: 目标项目工作目录。
- Produces: 至多一个符合扩展名且不位于剪枝目录的源码路径；无结果时仍可由既有主工程配置文件决定 Coding 项目。
- Invariant: 扫描不得枚举 node_modules、.venv、venv、vendor 或框架/构建目录的全部内容；扫描命中首个有效源码后立即结束。

- [x] **Step 1: 扩展现有合同检查为失败态的源码扫描断言**

在 Task 1 的 assert_fresh_change_contract 后加入 assert_bounded_source_scan_contract，并在依赖检查前调用：

~~~bash
assert_bounded_source_scan_contract() {
  local missing=0
  for needle in 'find .' '-name .venv' '-name venv' '-name node_modules' '-name vendor' '-name cadence-init' '-name Cadence-skills' '-print -quit'; do
    if ! rg -Fq -- "$needle" "$SKILL"; then
      printf '缺少 rule-config 有界源码扫描约定: %s\n' "$needle" >&2
      missing=1
    fi
  done
  if rg -Fq '**/*.{java,js,ts,py,go,php,rs,rb,swift,kt,c,cpp,cs}' "$SKILL"; then
    printf '仍存在无界源码 Glob 约定\n' >&2
    missing=1
  fi
  return "$missing"
}

assert_bounded_source_scan_contract
~~~

- [x] **Step 2: 运行失败态验证**

~~~bash
OPENSPEC_TELEMETRY=0 PYTHONPATH=/private/tmp/task1-python-deps \
  bash cadence-init/skills/rule-config/tests/verify-managed-lifecycle.sh
~~~

Expected: 非零退出，输出“缺少 rule-config 有界源码扫描约定: find .”或“仍存在无界源码 Glob 约定”。这是编辑 Skill 前对虚拟环境误扫描的回归保护。

- [x] **Step 3: 替换步骤 1a 的全仓 Glob 指令**

在 SKILL.md 的步骤 1a：项目类型检测中删除先 Glob 后过滤的做法，改为要求一次有界的首命中扫描。写入以下命令，并说明它只用于项目类型判定：

~~~bash
find . \
  \( -type d \( -name .git -o -name .claude -o -name .codex -o -name .pi -o -name .codegraph -o -name cadence-init -o -name Cadence-skills \
    -o -name node_modules -o -name vendor -o -name venv -o -name .venv -o -name env -o -name .env \
    -o -name dist -o -name build -o -name coverage -o -name .next -o -name target -o -name __pycache__ \) -prune \) \
  -o \( -type f \( -name '*.java' -o -name '*.js' -o -name '*.ts' -o -name '*.py' -o -name '*.go' \
    -o -name '*.php' -o -name '*.rs' -o -name '*.rb' -o -name '*.swift' -o -name '*.kt' -o -name '*.c' \
    -o -name '*.cpp' -o -name '*.cs' \) -print -quit \)
~~~

紧随命令规定：命令有输出即判定检测到业务源码；无输出时才继续检查已有的 package.json、pyproject.toml、Cargo.toml、go.mod、pom.xml、build.gradle 等主工程配置。删除旧的 cadence-init/、Cadence-skills/ 字符串后过滤列表，因为框架目录已经在遍历前被剪枝。

- [x] **Step 4: 运行通过态回归与格式检查**

~~~bash
OPENSPEC_TELEMETRY=0 PYTHONPATH=/private/tmp/task1-python-deps \
  bash cadence-init/skills/rule-config/tests/verify-managed-lifecycle.sh
git diff --check
~~~

Expected: 生命周期测试退出 0 且输出 SUMMARY pass=18 fail=0；git diff --check 无输出。静态锚点同时证明 .venv、venv、node_modules、vendor 被剪枝并使用 -print -quit，不再允许截图所示的数万条依赖文件输出。该命令可在 macOS/BSD sed 环境直接运行，不依赖临时 GNU sed PATH。

- [x] **Step 5: Commit**

~~~bash
git add cadence-init/skills/rule-config/SKILL.md \
  cadence-init/skills/rule-config/tests/verify-managed-lifecycle.sh
git commit -m "fix(cadence-init): 限制 rule-config 源码扫描范围"
~~~

---

### Task 3: 完整验证与交付前审查

映射：已归档 Change improve-progressive-disclosure-routing 工作包 6.1；Requirement: routing-conformance 的受管生命周期失败关闭和验证结果必须可审计。

**Files:**

- Verify only: cadence-init/skills/rule-config/SKILL.md
- Verify only: cadence-init/skills/rule-config/tests/helpers/managed-lifecycle-reference.sh
- Verify only: cadence-init/skills/rule-config/tests/verify-managed-lifecycle.sh

**Interfaces:**

- Consumes: Task 1、Task 2 的已提交修复。
- Produces: 新鲜的生命周期测试、OpenSpec 全量严格校验、空白格式检查和待审查 diff 证据。

- [x] **Step 1: 运行完整回归与 OpenSpec 严格校验**

~~~bash
OPENSPEC_TELEMETRY=0 PYTHONPATH=/private/tmp/task1-python-deps \
  bash cadence-init/skills/rule-config/tests/verify-managed-lifecycle.sh
openspec validate --all --strict
~~~

Expected: 第一条退出 0 且输出 SUMMARY pass=18 fail=0；第二条对所有 specs 与 archived changes 无 invalid 结果。若严格校验报告报告历史 Purpose 字段中的占位文本，记录为基线问题，不修改无关 archive 内容。

- [x] **Step 2: 审查范围与格式**

~~~bash
git diff f370564..HEAD -- cadence-init/skills/rule-config/SKILL.md \
  cadence-init/skills/rule-config/tests/helpers/managed-lifecycle-reference.sh \
  cadence-init/skills/rule-config/tests/verify-managed-lifecycle.sh
git diff --check f370564..HEAD
git status --short
~~~

Expected: diff 只涉及本 Plan 的三个实现文件及已提交的 cadence/ 方案/计划文档；格式检查无输出；没有对 /Users/michaelche/Desktop/ontology 的工作树操作或待提交改动。

- [x] **Step 3: Push 已提交分支并发起审查**

~~~bash
git push origin bugfix-b-0730
~~~

Expected: origin/bugfix-b-0730 包含方案、实施计划和两个修复提交；随后按仓库流程调用代码审查 Skill，依据上述新鲜证据决定是否进入归档或分支收尾。
