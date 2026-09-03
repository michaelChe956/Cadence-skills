# eval 体系——四 skill 安装效果测试（rule-eval-p0）实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 新建独立 eval 子系统：两阶段流水线（四 command 安装断言 + 8 行为探针）、四端轨迹适配与确定性断言器、三级车道与四矩阵报告，量化 Cadence 分发链路的规则遵循/MCP 使用/弱模型保证度/跨端一致性，不动 install.sh / rule-config.py / 各 SKILL.md 正文与既有 CI 车道。

**Architecture:** 全部代码落仓库根新目录 `eval/`（纯 Python 标准库包），数据流为：fixture 生成器（四变体，临时目录 + 隔离 HOME）→ 阶段一 headless 依序调用四 command 并跑产物断言表 + `--verify` + 幂等双跑 → 阶段二 8 探针经 env 注入 prompt，四端 CLI 轨迹（claude stream-json / codex rollout / pi session.jsonl / kimi wire.jsonl）由各适配器解析为统一中间格式 → 断言器确定性判分（deny 双分类 gate、排除规则原文、infra 归因、fake MCP 调用记录）→ 版本化结果 JSON → 调度器分夜轮转执行 → 滚动 7 夜聚合四矩阵 + 双键基线具名 diff；Tier-0（云端、零真实 CLI：unittest + mock 冒烟 + 离线重跑）与 Tier-1（夜间 self-hosted）落新增 workflow 文件 `.github/workflows/eval.yml`。

**Tech Stack:** Python 3.8+ 标准库（json/re/subprocess/dataclasses/pathlib/collections/unittest，零第三方依赖）、GitHub Actions（新增 workflow；self-hosted runner 标签 `cadence-eval`）、shell（仅 runner 注册文档中的维护者操作）。

**Spec:** `openspec/changes/rule-eval-p0/`（proposal.md / design.md / tasks.md / specs/eval-pipeline/spec.md / specs/eval-trajectory-scoring/spec.md / specs/eval-ci-matrix/spec.md 六件，契约为 2026-09-02 修订版）；完整设计 `cadence/designs/2026-09-02_方案设计_eval体系_四skill安装效果测试_v1.0.md`（维护者已批准）；证据 `cadence/analysis-docs/2026-09-02_eval体系设计调研证据/`（`skills执行级测试业内调研.md` 10 条防线 + `oracle决策评审.md` 四端 transcript 实测锚点）。Plan 只展开契约，不改范围/架构/验收。

## Global Constraints

- **语言**：全部新产物（代码、注释、测试、文档、提交信息）使用中文（`.claude/rules/language.md`）。
- **产物自动提交开关当前=关闭**：所有 Commit 步骤注明"开关关闭时跳过 `git commit`、只报告变更文件路径，等待维护者确认"；开关读取以入口文件 `## 项目配置` 为准，不一致按关闭。
- **TDD 铁律**：每个功能先写失败测试→运行确认失败→最小实现→运行通过；无失败测试不写实现。
- **测试运行器**：eval 全部测试用 `python3 -m unittest`（本地无 pytest 时不引入新依赖）；命令一律从仓库根执行。Tier-0 同命令。
- **零第三方依赖**：eval 代码只用 Python 标准库（含 JSON 配置，不用 PyYAML）；fixture 的 `.codex/config.toml` 检查用文本锚点（区块头正则），不做完整 TOML 解析。
- **不动分发链路**：`install.sh`、软链层、`rule-config.py`、四个 skill 的 SKILL.md 正文、`.github/workflows/ci.yml` 既有车道零改动（Tier-0/Tier-1 为新增 workflow 文件 `.github/workflows/eval.yml`，即"新增 job 而非改写"；回滚=删除 `eval/` 与该文件）。
- **PR 车道零真实 CLI**：Tier-0 不启动任何 claude/codex/pi/kimi 进程；需要 CLI 的环节全部用 mock CLI（`eval/runner/mock_cli.py`）或入库的离线 transcript 样本（`eval/transcripts/`）。真实 CLI 仅 Tier-1（夜间 self-hosted）与手动验证命令。
- **探针 prompt 经 env 注入**：prompt 只经环境变量 `EVAL_PROMPT` 传递，runner 以 `subprocess` 列表 argv 组装（`shell=False`），绝不内联进 shell 命令字符串。
- **中间格式唯一判分入口**：断言器只消费 `eval/ifmt.py` 统一中间格式；四端解析差异全部封在各适配器内。
- **deny 双分类语义**：受管区块内 deny → 改道率子度量（N 步内改用 preferred 即 PASS）；区块外 deny 或 is_error → FAIL（harness 配置错误归类）；启用前必须先以 `eval forensics-denial` 在 fixture 取证真实 denial 字段结构（本机 242 个真实会话 `permission_denial` 出现 0 次，无自然样本）。
- **fixture 隔离与防泄漏**：fixture 项目在临时目录全新生成，项目文件不得包含 Cadence 仓库路径字符串（生成器自检）；用户级配置采用"真实 HOME + 全局配置快照/diff"（HOME 策略见下条）；含业务路径/内容的审计与夜间报告产物一律不入 git（`.gitignore` 追加 `cadence/reports/eval/`）。
- **HOME 策略（Tier-1 真实端；评审拍板选 b 方案）**：真实 CLI 运行**不覆写 HOME**——登录态留在真实 HOME，凭证文件不迁移、不复制、不打印内容；skill 发现路径经 env 注入指向 fixture 隔离 home 的对应目录（`agents.json` 每端 `skill_env` 数据面，如 `"CLAUDE_CONFIG_DIR": "{fixture_home}/.claude"`；键名为初值假设，Tier-1 首夜以各端实测核定，只改数据不改代码）；真实 HOME 的用户级配置文件（`gen.GLOBAL_CONFIG_FILES` 清单）由 `gen.snapshot_global_configs`/`diff_global_configs` 在 `run_night` 首尾各快照一次，漂移写 `<夜目录>/global-config-drift.json` 并进报告 `global_config_drift` 节（观测单列，不判红）。**取舍理由**：a 方案（临时 HOME + 凭证文件链接/复制）需逐端枚举凭证路径并搬运敏感材料——泄漏面大、凭证轮换即失效、四端路径各异维护成本高；b 方案用"env 注入 skill 路径 + 首尾快照监测"换掉凭证迁移，端在真实 HOME 下的用户级写入恰是监测对象（漂移显式报告而非静默）。对照组探针同用真实 HOME 但**不注入** skill_env（未安装语义）；mock/Tier-0/全部单测不受影响（沿用隔离 home 路径）。
- **嵌套代码块**：外层 4 反引号、内层 3 反引号（`.claude/rules/markdown-format.md`，本文档自身遵守）。
- **文档路径**：runner 注册等开发文档落 `cadence/readmes/`，命名 `YYYY-MM-DD_README_…_vX.Y.md`（`.claude/rules/document-storage.md`）。
- **模型口径（R11）**：每端 pin 其当前配置模型（`eval/config/agents.json`，四端各不相同，接受端×模型混合效应）；模型标识从 transcript 实测回读（claude `message.model` / codex `turn_context`·`session_meta` / pi `model_change.modelId` / kimi `usage.record.model`·`config.update.modelAlias`），与 pin 不一致或 pi 会话内 `model_change` → 该 run 标 `MODEL_DRIFT` 出矩阵。
- **量级口径（R12/R13）**：Tier-1 首轮 = 分夜轮转（奇数夜 P1/P3/P5/P7，偶数夜 P2/P4/P6/P8）× 4 端 × pinned 模型 × 2 runs + 对照组每夜 4 规则探针 × 轮换 2 端 + v3 变体每周 × 2 端；四矩阵按滚动 7 夜聚合，缺测显式表达不判红（实测依据：median 2.5min / p90 5.7min × 全量 208 会话 = 10–20h 串行超窗）。
- **行号基准**：Files 中的行号以 2026-09-02 仓库状态为基线，实施时以符号名/锚点二次定位为准。

## 文件结构总览（File Structure）

### eval 子系统目录定死为仓库根 `eval/`，理由

1. **分发隔离**：`cadence-init/skills/` 下的内容会经 install.sh 软链进用户端被当作 skill 分发；eval 是测试 harness，必须与其彻底隔离，根级 `eval/` 一眼可辨"非分发内容"。
2. **文档/代码边界**：`cadence/` 按 document-storage 规则是产物文档目录（plans/designs/reports…），代码主体放那里会混淆两类资产；eval 仅把"运行时报告产物"写入 `cadence/reports/eval/`（不入 git）。
3. **回滚契约**：design R9"纯新增子系统"要求删除即完全移除——独立根目录 + 独立 workflow 文件正好满足，不留下任何散点文件（除 `.gitignore` 一行与 `cadence/readmes/` 一份注册文档）。

### 文件清单

| 文件 | 动作 | 责任 | 创建任务 |
|---|---|---|---|
| `eval/__init__.py` | Create | 包标记 | Task 1 |
| `eval/config/agents.json` | Create | 四端 pinned 模型 / strong 模型 / CLI 版本锁 / 可执行名 / 捕获方式 | Task 15 |
| `eval/config/policy.json` | Create | 熔断/超时/保留/阈值参数 | Task 15 |
| `eval/ifmt.py` | Create | 统一中间格式（ToolCall/Denial/WriteEvent/IntermediateTrajectory + JSON 往返） | Task 5 |
| `eval/adapters/__init__.py` | Create | 适配器注册表 `get_adapter` | Task 6 |
| `eval/adapters/base.py` | Create | AgentAdapter 协议 + `normalize_tool` | Task 6 |
| `eval/adapters/claude.py` | Create | claude stream-json / session jsonl 解析 | Task 6 |
| `eval/adapters/codex.py` | Create | codex rollout jsonl 解析（工具名变体归一） | Task 7 |
| `eval/adapters/pi.py` | Create | pi session.jsonl 解析（model_change 作废） | Task 7 |
| `eval/adapters/kimi.py` | Create | kimi wire.jsonl 解析（protocol_version/usage.record 锚点） | Task 8 |
| `eval/fixtures/__init__.py` | Create | 包标记 | Task 1 |
| `eval/fixtures/generator.py` | Create | 四变体 fixture（fresh/v3/mcp_pre/control）+ HOME 隔离 + 全局配置快照 | Task 1 |
| `eval/install/__init__.py` | Create | 包标记 | Task 2 |
| `eval/install/commands.py` | Create | 阶段一四 command prompt 表 | Task 3 |
| `eval/install/assertions.py` | Create | 阶段一产物断言表（纯函数，可离线单测） | Task 2 |
| `eval/install/stage1.py` | Create | 阶段一流水线（四 command 依序 + `--verify` 消费） | Task 3 |
| `eval/install/idempotency.py` | Create | workspace 树快照 + 幂等双跑/三跑 | Task 4 |
| `eval/probes/__init__.py` | Create | 包标记 | Task 13 |
| `eval/probes/definitions.py` | Create | 8 探针定义 + 条款 ID 绑定 + 题库变体 + env 注入 | Task 13 |
| `eval/scoring/__init__.py` | Create | 包标记 | Task 9 |
| `eval/scoring/assertor.py` | Create | 确定性断言器（事件/产物/时间序/漫游/归因/排除规则原文） | Task 9 |
| `eval/scoring/denial_gate.py` | Create | deny 双分类 + 改道率 + 受管区块快照判定 | Task 10 |
| `eval/scoring/schema.py` | Create | 结果 JSON schema_version 最小契约 + 基线读取规则 | Task 12 |
| `eval/mcp/__init__.py` | Create | 包标记 | Task 11 |
| `eval/mcp/fake_servers.py` | Create | fake time/context7/图片 MCP（stdio JSON-RPC + 调用记录） | Task 11 |
| `eval/runner/__init__.py` | Create | 包标记 | Task 3 |
| `eval/runner/proc.py` | Create | 四端 CLI 调用封装（env 注入/HOME 覆写/超时/捕获） | Task 3 |
| `eval/runner/mock_cli.py` | Create | mock 四端 CLI（罐头轨迹 + 罐头产物，Tier-0/Tier-1 自检用） | Task 3 |
| `eval/runner/guards.py` | Create | 断点续跑/多层熔断/双 pin 核验/保留策略/连续失败计数 | Task 15 |
| `eval/runner/schedule.py` | Create | 分夜轮转调度表（探针/对照组/v3/strong 增补行） | Task 14 |
| `eval/runner/night.py` | Create | Tier-1 单夜流水线 + `drill7` 演练 | Task 15/20 |
| `eval/runner/report.py` | Create | 四矩阵聚合 + 双键具名 diff + 基线治理 + 对照组差值 | Task 16 |
| `eval/runner/audit.py` | Create | 既有 session 审计表（第五张观测表） | Task 17 |
| `eval/runner/offline_rerun.py` | Create | 离线重跑（历史 transcript 重判 + golden diff） | Task 18 |
| `eval/runner/forensics.py` | Create | 人造真实 denial 取证（self-hosted 实测命令） | Task 10 |
| `eval/runner/verify_kimi.py` | Create | kimi 适配器先行单端验证 | Task 8 |
| `eval/runner/cli.py` | Create | 子命令入口（smoke/rerun/night/report/baseline/audit/verify-kimi/forensics-denial/pins-audit/drill7） | Task 3 起逐任务追加 |
| `eval/transcripts/claude/golden-1.jsonl` | Create | claude 罐头轨迹（含 deny+改道样本） | Task 6 |
| `eval/transcripts/codex/golden-1.jsonl` | Create | codex 罐头轨迹 | Task 7 |
| `eval/transcripts/pi/golden-1.jsonl` | Create | pi 罐头轨迹 | Task 7 |
| `eval/transcripts/kimi/golden-1.jsonl` | Create | kimi 罐头轨迹 | Task 8 |
| `eval/transcripts/golden-verdicts.json` | Create | 离线重跑期望判定 | Task 18 |
| `eval/evidence/README.md` | Create | 取证产物说明（denial 字段结构证据落位规则） | Task 10 |
| `eval/baselines/README.md` | Create | 基线治理说明（仅维护者显式提交生效） | Task 16 |
| `eval/tests/__init__.py` | Create | 包标记 | Task 1 |
| `eval/tests/test_*.py`（21 个文件） | Create | 全部 TDD 用例（见各任务） | 各任务 |
| `.github/workflows/eval.yml` | Create | Tier-0 + 云端探活 + Tier-1 夜间（新增 workflow，不动 ci.yml） | Task 18/19 |
| `.gitignore` | Modify | 追加 `cadence/reports/eval/`（运行时产物不入 git） | Task 17 |
| `cadence/readmes/2026-09-02_README_eval-self-hosted-runner注册_v1.0.md` | Create | runner 注册/密钥/告警/手动补跑文档（tasks 4.5） | Task 19 |
| `openspec/changes/rule-eval-p0/tasks.md` | Modify | 收尾勾选 | Task 20 |

运行时产物目录（不入 git，由 `.gitignore` 覆盖）：`cadence/reports/eval/nightly/<日期>/runs/*.json`、`.../transcripts/`、`cadence/reports/eval/audit/<日期>/`、`eval/evidence/denial-fields-*.json`（取证证据**入 git**，属设计资产）。

任务组顺序（对齐 tasks.md 五组）：**任务组 1：骨架与 fixture 四变体（Task 1–4）→ 任务组 2：轨迹适配与断言器（Task 5–12）→ 任务组 3：探针集（Task 13）→ 任务组 4：车道与报告（Task 14–19）→ 任务组 5：收尾（Task 20）**。

tasks.md 条目 → Plan 任务映射：1.1→T1；1.2→T2/T3；1.3→T4；1.4→T1+T14+T16；2.1→T5/T6；2.2→T7/T8；2.4→T9/T10；2.5→T11；2.6→T12；3.1→T13；3.2→T13+T1（theme 轮换）；4.1→T14/T15；4.2→T18；4.3→T19；4.4→T16；4.5→T19；4.6→T17；5.1→T20；5.2→T20。

---
## 任务组 1：骨架与 fixture 四变体（eval-pipeline：tasks 1.1–1.3、1.4 变体部分）

### Task 1: eval 目录骨架 + fixture 生成器（四变体 + 隔离 HOME + 全局配置快照）

**Files:**
- Create: `eval/__init__.py`、`eval/fixtures/__init__.py`、`eval/tests/__init__.py`（均为空文件，仅包标记）
- Create: `eval/fixtures/generator.py`
- Test: `eval/tests/test_fixture_generator.py`

**Interfaces:**
- Consumes: 仓库既有模板 `cadence-init/skills/rule-config/references/rules/l0-history/agent-routing-kernel-v3.md`（v3 变体的冻结历史源，p1 已入库）与 `cadence-init/skills/`（软链源）。
- Produces:
  - `gen.VARIANTS == ("fresh", "v3", "mcp_pre", "control")`
  - `@dataclass gen.FixturePaths`：字段 `root: Path`（fixture 项目根）、`home: Path`（隔离 HOME）、`repo: Path`（Cadence 检出根，软链源）
  - `gen.make_fixture(variant: str, base_dir: Path, repo_root: Path, theme: str = "orders", install: bool = True) -> gen.FixturePaths`
  - `gen.expected_rules_files() -> list[str]`（阶段一断言的 `.claude/rules/` 期望清单）
  - `gen.snapshot_global_configs(home: Path) -> dict[str, str]`（路径→sha256；文件不存在跳过；入参可为隔离 home 或 `Path.home()`——HOME 策略 b 方案的真实 HOME 快照同函数复用）
  - `gen.diff_global_configs(before: dict, after: dict) -> list[str]`（被修改/新增的路径清单）
  - Task 2/3/4、Task 15（night runner；真实 HOME 首尾快照与漂移落盘）、Task 16（报告 `global_config_drift` 节）消费。

- [ ] **Step 1: 写失败测试**

```python
"""eval/tests/test_fixture_generator.py —— fixture 四变体与隔离（tasks 1.1/1.4 变体部分）。"""
import tempfile
import unittest
from pathlib import Path

from eval.fixtures import generator as gen

REPO_ROOT = Path(__file__).resolve().parents[2]


class TestFixtureGenerator(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)

    def test_four_variants_declared(self):
        """ut-fx-variants：四变体齐备（含未安装对照组）。"""
        self.assertEqual(gen.VARIANTS, ("fresh", "v3", "mcp_pre", "control"))

    def test_fresh_has_project_but_no_claude(self):
        """ut-fx-fresh：全新变体含 coding 工程结构与 git 仓库，无任何 Cadence 痕迹。"""
        fx = gen.make_fixture("fresh", self.base, REPO_ROOT)
        self.assertTrue((fx.root / "package.json").is_file())
        self.assertTrue((fx.root / "src" / "orders" / "entry.py").is_file())
        self.assertTrue((fx.root / ".git").is_dir())
        # P7 探针的截图占位（1x1 PNG，魔数校验）
        png = fx.root / "assets" / "error.png"
        self.assertTrue(png.is_file())
        self.assertEqual(png.read_bytes()[:8], b"\x89PNG\r\n\x1a\n")
        self.assertFalse((fx.root / "CLAUDE.md").exists())
        self.assertFalse((fx.root / ".claude").exists())

    def test_installed_home_has_skill_links(self):
        """ut-fx-links：安装变体的隔离 HOME 复刻三层软链布局（14 skill 全量）。"""
        fx = gen.make_fixture("fresh", self.base, REPO_ROOT)
        for skill in ("pre-check", "rule-config", "mcp-configuration", "project-rules-examples"):
            link = fx.home / ".claude" / "skills" / skill
            self.assertTrue(link.is_symlink(), link)
            self.assertTrue((link / "SKILL.md").is_file())
        shared = fx.home / ".agents" / "skills" / "rule-config"
        self.assertTrue(shared.parent.is_symlink() or shared.is_symlink() or shared.exists())

    def test_control_home_has_no_links(self):
        """ut-fx-control：对照组不安装（HOME 无 skill 链接），项目同构。"""
        fx = gen.make_fixture("control", self.base, REPO_ROOT)
        self.assertFalse((fx.home / ".claude" / "skills").exists())
        self.assertTrue((fx.root / "package.json").is_file())

    def test_v3_variant_seeds_frozen_l0(self):
        """ut-fx-v3：v3 变体 CLAUDE.md 逐字含冻结 v3 历史源 + 区块外用户文本。"""
        fx = gen.make_fixture("v3", self.base, REPO_ROOT)
        text = (fx.root / "CLAUDE.md").read_text(encoding="utf-8")
        v3 = (REPO_ROOT / "cadence-init/skills/rule-config/references/rules/l0-history"
              / "agent-routing-kernel-v3.md").read_text(encoding="utf-8")
        self.assertIn(v3, text)
        self.assertIn("## 团队约定", text)  # 区块外内容（升级断言的逐字保留对象）

    def test_mcp_pre_variant_preserves_servers(self):
        """ut-fx-mcppre：已配变体带既有 server 与 codegraph，测防重写。"""
        import json
        fx = gen.make_fixture("mcp_pre", self.base, REPO_ROOT)
        doc = json.loads((fx.root / ".mcp.json").read_text(encoding="utf-8"))
        self.assertIn("existing-server", doc["mcpServers"])
        self.assertIn("codegraph", doc["mcpServers"])
        toml = (fx.root / ".codex" / "config.toml").read_text(encoding="utf-8")
        self.assertIn("[mcp_servers.existing-server]", toml)

    def test_fixture_files_leak_no_repo_path(self):
        """ut-fx-noleak：fixture 项目文本文件不含 Cadence 仓库路径（防泄漏 spec 场景）。"""
        fx = gen.make_fixture("fresh", self.base, REPO_ROOT)
        needle = str(REPO_ROOT)
        for p in sorted(fx.root.rglob("*")):
            if p.is_file():
                self.assertNotIn(needle, p.read_text(encoding="utf-8", errors="ignore"), p)

    def test_theme_rotation_changes_module(self):
        """ut-fx-theme：题库轮换——不同 theme 生成不同模块名（同构不同名）。"""
        a = gen.make_fixture("fresh", self.base / "a", REPO_ROOT, theme="orders")
        b = gen.make_fixture("fresh", self.base / "b", REPO_ROOT, theme="billing")
        self.assertTrue((a.root / "src" / "orders").is_dir())
        self.assertTrue((b.root / "src" / "billing").is_dir())
        self.assertEqual(len(gen.expected_rules_files()), 9)

    def test_global_config_snapshot_diff(self):
        """ut-fx-snapshot：全局配置快照可对比出夜间运行期间的变化。"""
        fx = gen.make_fixture("fresh", self.base, REPO_ROOT)
        before = gen.snapshot_global_configs(fx.home)
        (fx.home / ".claude").mkdir(parents=True, exist_ok=True)
        (fx.home / ".claude" / "settings.json").write_text('{"x":1}', encoding="utf-8")
        after = gen.snapshot_global_configs(fx.home)
        self.assertEqual(gen.diff_global_configs(before, after),
                         [str(fx.home / ".claude" / "settings.json")])

    def test_global_config_snapshot_real_home_sim(self):
        """ut-fx-realhome：HOME 策略 b 方案——run_night 以真实 HOME 路径传参
        快照/ Diff，函数对任意 home（含 Path.home()）成立，漂移可归位到具体文件。"""
        fake_home = self.base / "realhome"  # 模拟 Path.home() 的用户级配置树
        (fake_home / ".codex").mkdir(parents=True)
        (fake_home / ".codex" / "config.toml").write_text("x = 1\n", encoding="utf-8")
        before = gen.snapshot_global_configs(fake_home)
        (fake_home / ".codex" / "config.toml").write_text("x = 2\n", encoding="utf-8")
        after = gen.snapshot_global_configs(fake_home)
        self.assertEqual(gen.diff_global_configs(before, after),
                         [str(fake_home / ".codex" / "config.toml")])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 运行确认失败**

```bash
python3 -m unittest eval.tests.test_fixture_generator -v
```

预期：全部 ERROR/FAIL（`ModuleNotFoundError: No module named 'eval.fixtures'` 或 `AttributeError`）。

- [ ] **Step 3: 最小实现**

`eval/fixtures/generator.py`：

```python
"""fixture 生成器：四变体 + 临时目录 + 隔离 HOME（eval-pipeline tasks 1.1）。

变体：fresh 全新 / v3 已初始化（含 v3 L0，测升级链）/ mcp_pre 已配
.mcp.json+codegraph（测防重写）/ control 未安装 Cadence 对照组。
fixture 项目在临时目录全新生成，文件内容不含 Cadence 仓库路径（防泄漏）。
P7 探针的截图占位 assets/error.png（1x1 PNG）随项目生成。
"""
import base64
import hashlib
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path

VARIANTS = ("fresh", "v3", "mcp_pre", "control")

# 1x1 灰度 PNG（67 字节，魔数 \x89PNG\r\n\x1a\n）——P7 图片 MCP 探针的确定性占位
ERROR_PNG_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAAAAAA6fptVAAAACklEQVR4nGNoAAAAggCBd81ytg"
    "AAAABJRU5ErkJggg==")

RULES_FILES = [
    "README.md", "code-reading.md", "code-usage.md", "document-storage.md",
    "language.md", "markdown-format.md", "mcp-servers.md",
    "openspec-superpowers-workflow.md", "playwright.md",
]

GLOBAL_CONFIG_FILES = (
    ".claude/settings.json", ".claude/CLAUDE.md", ".codex/config.toml",
    ".codex/AGENTS.md", ".pi/agent/settings.json", ".kimi-code/mcp.json",
)


@dataclass
class FixturePaths:
    root: Path   # fixture 项目根
    home: Path   # 隔离 HOME
    repo: Path   # Cadence 检出根（软链源）


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _write_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def _project_files(root: Path, theme: str) -> None:
    """同构小型 coding 工程：entry→service→repo 调用链（P1 探针的检索对象）。"""
    _write(root / "package.json",
           '{"name": "fixture-app", "version": "1.0.0", "scripts": {"test": "jest"}}\n')
    _write_bytes(root / "assets" / "error.png", base64.b64decode(ERROR_PNG_B64))
    _write(root / "src" / theme / "entry.py",
           f"from src.{theme}.service import handle\n\n\ndef main() -> None:\n    handle(payload={{}})\n")
    _write(root / "src" / theme / "service.py",
           f"from src.{theme}.repo import save\n\n\ndef handle(payload: dict) -> None:\n    save(payload)\n")
    _write(root / "src" / theme / "repo.py",
           "def save(payload: dict) -> None:\n    print('saved')\n")


def _git_init(root: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.email", "eval@fixture.local"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "eval-fixture"], cwd=root, check=True)
    subprocess.run(["git", "add", "-A"], cwd=root, check=True)
    subprocess.run(["git", "commit", "-qm", "fixture init", "--allow-empty"],
                   cwd=root, check=True)


def _install_skills(repo_root: Path, home: Path) -> None:
    """复刻 install.sh 三层软链布局（共享层→claude/codex 投影），源指向 Cadence 检出。"""
    shared = home / ".agents" / "skills"
    shared.mkdir(parents=True, exist_ok=True)
    for skill_dir in sorted((repo_root / "cadence-init" / "skills").iterdir()):
        if (skill_dir / "SKILL.md").is_file():
            target = shared / skill_dir.name
            if not target.exists():
                target.symlink_to(skill_dir)
    for layer in (home / ".claude" / "skills", home / ".codex" / "skills" / "skills"):
        layer.mkdir(parents=True, exist_ok=True)
        for entry in sorted(shared.iterdir()):
            link = layer / entry.name
            if not link.exists():
                link.symlink_to(entry)


def make_fixture(variant: str, base_dir: Path, repo_root: Path,
                 theme: str = "orders", install: bool = True) -> FixturePaths:
    if variant not in VARIANTS:
        raise ValueError(f"未知 fixture 变体：{variant}")
    if variant == "control":
        install = False  # 对照组定义即未安装
    root = base_dir / "fixture"
    home = base_dir / "home"
    root.parent.mkdir(parents=True, exist_ok=True)
    _project_files(root, theme)
    if variant == "v3":
        v3 = (repo_root / "cadence-init/skills/rule-config/references/rules/l0-history"
              / "agent-routing-kernel-v3.md").read_text(encoding="utf-8")
        _write(root / "CLAUDE.md", v3 + "\n## 团队约定\n\n- 提交前跑 `npm test`。\n")
    elif variant == "mcp_pre":
        _write(root / ".mcp.json", json.dumps({"mcpServers": {
            "existing-server": {"command": "echo", "args": ["hi"]},
            "codegraph": {"command": "codegraph-server", "args": ["stdio"]},
        }}, ensure_ascii=False, indent=2) + "\n")
        _write(root / ".codex" / "config.toml",
               "[mcp_servers.existing-server]\ncommand = \"echo\"\n"
               "args = [\"hi\"]\n\n[mcp_servers.codegraph]\ncommand = \"codegraph-server\"\n")
    _git_init(root)
    if install:
        _install_skills(repo_root, home)
    return FixturePaths(root=root, home=home, repo=repo_root)


def expected_rules_files() -> list:
    return list(RULES_FILES)


def snapshot_global_configs(home: Path) -> dict:
    out = {}
    for rel in GLOBAL_CONFIG_FILES:
        p = home / rel
        if p.is_file():
            out[str(p)] = hashlib.sha256(p.read_bytes()).hexdigest()
    return out


def diff_global_configs(before: dict, after: dict) -> list:
    changed = [p for p, h in after.items() if before.get(p) != h]
    return sorted(changed)
```

同时创建空文件：`eval/__init__.py`、`eval/fixtures/__init__.py`、`eval/tests/__init__.py`。

- [ ] **Step 4: 运行测试确认通过**

```bash
python3 -m unittest eval.tests.test_fixture_generator -v
```

预期：10 个用例全部 PASS。

- [ ] **Step 5: 提交建议**

```bash
git add eval/__init__.py eval/fixtures/ eval/tests/__init__.py eval/tests/test_fixture_generator.py
git commit -m "feat(eval): 目录骨架与 fixture 生成器——四变体、隔离 HOME、全局配置快照"
```

> 产物自动提交开关当前=关闭：跳过 `git commit`，只报告上述四个新增路径，等待维护者确认。

### Task 2: 阶段一产物断言表（纯函数）

**Files:**
- Create: `eval/install/__init__.py`（空文件）
- Create: `eval/install/assertions.py`
- Test: `eval/tests/test_stage1_assertions.py`

**Interfaces:**
- Consumes: `gen.expected_rules_files() -> list[str]`、`gen.FixturePaths`（Task 1）。
- Produces:
  - `@dataclass asrt.Assertion`：字段 `name: str`、`ok: bool`、`detail: str`
  - `asrt.assert_stage1(variant: str, root: Path, verify_exit: Optional[int], final_texts: dict, extra: Optional[dict] = None) -> list[asrt.Assertion]`——`final_texts` 键为 command 名（pre-check/rule-config/mcp-configuration/project-rules-examples）；`extra` 可选键 `pre_check_clean: bool`、`rules_before: dict[str, str]`（project-rules-examples 执行前的 `.claude/rules/` 哈希）、`outside_l0_baseline: Optional[str]`（v3 变体区块外原文）；**`rules_before` 缺省时 `prx.not-rules` 判 skip（`ok=True`、detail 前缀 `skip:`）——不判红也不拉低整体 ok，仅提示未采集**（离线/单测调用无需补传）
  - Task 3（stage1 runner）与 Task 18（mock 冒烟）消费。

- [ ] **Step 1: 写失败测试**

```python
"""eval/tests/test_stage1_assertions.py —— 阶段一产物断言表（tasks 1.2 断言部分）。"""
import json
import tempfile
import unittest
from pathlib import Path

from eval.install import assertions as asrt


def _installed_workspace(root: Path) -> None:
    """构造一个满足阶段一断言的"已安装"workspace。"""
    rules = root / ".claude" / "rules"
    rules.mkdir(parents=True, exist_ok=True)  # 先建目录再写文件（否则 helper 自身报错）
    for name in ("README.md", "code-reading.md", "code-usage.md", "document-storage.md",
                 "language.md", "markdown-format.md", "mcp-servers.md",
                 "openspec-superpowers-workflow.md", "playwright.md"):
        (rules / name).write_text("# rule\n", encoding="utf-8")
    claude = (root / "CLAUDE.md").read_text(encoding="utf-8") if (root / "CLAUDE.md").exists() else ""
    (root / "CLAUDE.md").write_text(
        "<!-- cadence-managed:openspec-superpowers-routing:v4:start -->\n"
        "Cadence L0 路由内核 v4\n" + claude +
        "<!-- cadence-managed:openspec-superpowers-routing:v4:end -->\n", encoding="utf-8")
    deny_doc = {"permissions": {"deny": [
        "UserDeny",
        "@@cadence-managed:permission-gate:v1:start@@",
        "Grep", "Glob", "Bash(grep:*)",
        "@@cadence-managed:permission-gate:v1:end@@"]}}
    (root / ".claude" / "settings.json").write_text(
        json.dumps(deny_doc, ensure_ascii=False, indent=2), encoding="utf-8")
    (root / "AGENTS.md").write_text(
        "intro\n<!-- cadence-managed:codex-rules-inline:v1:start -->\n链\n"
        "<!-- cadence-managed:codex-rules-inline:v1:end -->\n", encoding="utf-8")
    (root / ".mcp.json").write_text(json.dumps({"mcpServers": {
        "zai-mcp-server": {"command": "npx"}, "MiniMax": {"command": "uvx"},
        "codegraph": {"command": "codegraph-server"},
        "existing-server": {"command": "echo"}}}, indent=2), encoding="utf-8")
    (root / ".codex").mkdir(exist_ok=True)
    (root / ".codex" / "config.toml").write_text(
        "[mcp_servers.zai-mcp-server]\ncommand = \"npx\"\n"
        "[mcp_servers.MiniMax]\ncommand = \"uvx\"\n"
        "[mcp_servers.codegraph]\ncommand = \"codegraph-server\"\n"
        "[mcp_servers.existing-server]\ncommand = \"echo\"\n", encoding="utf-8")
    (root / ".gitignore").write_text(
        ".worktrees/\n.mcp.json\n.codex/config.toml\ncadence/cache/mcp-availability/\n",
        encoding="utf-8")
    pr = root / "cadence" / "project-rules"
    (pr / "examples").mkdir(parents=True)
    (pr / "README.md").write_text("# 项目规则\n", encoding="utf-8")


TEXTS = {"pre-check": "诊断报告：镜像与环境检查完成", "rule-config": "apply 完成",
         "mcp-configuration": "MCP 配置完成", "project-rules-examples": "模板就位"}


class TestStage1Assertions(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "fixture"
        self.root.mkdir()

    def _all_ok(self, variant="fresh", verify_exit=0, **kw):
        results = asrt.assert_stage1(variant, self.root, verify_exit, dict(TEXTS), kw.get("extra"))
        bad = [r for r in results if not r.ok]
        self.assertEqual(bad, [], [f"{r.name}: {r.detail}" for r in bad])
        return results

    def test_fresh_all_green(self):
        """ut-s1-fresh：全新变体全绿（清单/L0v4/权限区/内联区/verify=0）。"""
        _installed_workspace(self.root)
        names = [r.name for r in self._all_ok()]
        for expect in ("pre-check.report", "pre-check.zero-change", "rules.manifest",
                       "l0.v4", "gate.region", "codex.inline", "verify.exit0",
                       "mcp.valid", "mcp.codex-consistent", "mcp.gitignore",
                       "prx.placed", "prx.not-rules"):
            self.assertIn(expect, names)

    def test_missing_rule_file_fails_manifest(self):
        """ut-s1-manifest：规则清单缺文件判红。"""
        _installed_workspace(self.root)
        (self.root / ".claude/rules/playwright.md").unlink()
        results = asrt.assert_stage1("fresh", self.root, 0, dict(TEXTS))
        self.assertFalse(next(r for r in results if r.name == "rules.manifest").ok)

    def test_verify_nonzero_fails(self):
        """ut-s1-verify：--verify 退出码非 0 判红（p1 断言原语消费）。"""
        _installed_workspace(self.root)
        results = asrt.assert_stage1("fresh", self.root, 1, dict(TEXTS))
        self.assertFalse(next(r for r in results if r.name == "verify.exit0").ok)

    def test_pre_check_dirty_tree_fails(self):
        """ut-s1-zerochange：pre-check 产生文件改动判红。"""
        _installed_workspace(self.root)
        results = asrt.assert_stage1("fresh", self.root, 0, dict(TEXTS),
                                     {"pre_check_clean": False})
        self.assertFalse(next(r for r in results if r.name == "pre-check.zero-change").ok)

    def test_v3_upgrade_assertions(self):
        """ut-s1-v3：v3 变体断言升级+备份+区块外逐字不变。"""
        _installed_workspace(self.root)
        # 区块外用户内容（升级后必须逐字保留）与 legacy 备份先行落位
        with (self.root / "CLAUDE.md").open("a", encoding="utf-8") as fh:
            fh.write("\n## 团队约定\n\n- 提交前跑 `npm test`。\n")
        legacy = self.root / "cadence" / "legacy" / "20260902"
        legacy.mkdir(parents=True)
        (legacy / "CLAUDE.md.v3.bak").write_text("v3 backup", encoding="utf-8")
        results = asrt.assert_stage1("v3", self.root, 0, dict(TEXTS),
                                     {"outside_l0_baseline": "## 团队约定\n\n- 提交前跑 `npm test`。\n"})
        bad = [r for r in results if not r.ok]
        self.assertEqual(bad, [], [f"{r.name}: {r.detail}" for r in bad])

    def test_v3_outside_changed_fails(self):
        """ut-s1-v3-outside：区块外内容被改判红。"""
        _installed_workspace(self.root)
        results = asrt.assert_stage1("v3", self.root, 0, dict(TEXTS),
                                     {"outside_l0_baseline": "## 旧内容\n"})
        self.assertFalse(next(r for r in results if r.name == "v3.outside-verbatim").ok)

    def test_mcp_pre_preserves_existing_server(self):
        """ut-s1-mcppre：既有 server 不被覆盖（集合合并语义）。"""
        _installed_workspace(self.root)
        doc = json.loads((self.root / ".mcp.json").read_text(encoding="utf-8"))
        doc["mcpServers"].pop("existing-server")
        (self.root / ".mcp.json").write_text(json.dumps(doc), encoding="utf-8")
        results = asrt.assert_stage1("mcp_pre", self.root, 0, dict(TEXTS))
        self.assertFalse(next(r for r in results if r.name == "mcp.pre-existing").ok)

    def test_prx_must_not_touch_rules(self):
        """ut-s1-prx：project-rules-examples 不得写 .claude/rules/。"""
        import hashlib
        _installed_workspace(self.root)
        # 快照口径与实现一致：文件名→sha256（interfaces：rules_before 为哈希快照）
        before = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                  for p in (self.root / ".claude/rules").iterdir()}
        results = asrt.assert_stage1("fresh", self.root, 0, dict(TEXTS),
                                     {"rules_before": before})
        self.assertTrue(next(r for r in results if r.name == "prx.not-rules").ok)
        before["injected.md"] = "被改了"
        results = asrt.assert_stage1("fresh", self.root, 0, dict(TEXTS),
                                     {"rules_before": before})
        self.assertFalse(next(r for r in results if r.name == "prx.not-rules").ok)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 运行确认失败**

```bash
python3 -m unittest eval.tests.test_stage1_assertions -v
```

预期：全部 ERROR（`No module named 'eval.install'`）。

- [ ] **Step 3: 最小实现**

`eval/install/assertions.py`：

```python
"""阶段一产物断言表（design §4 全表；纯函数，Tier-0 可离线单测）。

断言期望值锚点：L0 v4 标记 / permission-gate v1 区块 / codex-rules-inline v1
区块均取自 p1 已合入产物（rule-config.py 常量同源；p1 改标记名时本文件同步）。
"""
import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from eval.fixtures import generator as gen

L0_BEGIN = "<!-- cadence-managed:openspec-superpowers-routing:v4:start -->"
GATE_BEGIN = "@@cadence-managed:permission-gate:v1:start@@"
GATE_END = "@@cadence-managed:permission-gate:v1:end@@"
INLINE_BEGIN = "<!-- cadence-managed:codex-rules-inline:v1:start -->"
GITIGNORE_LINES = (".worktrees/", ".mcp.json", ".codex/config.toml",
                   "cadence/cache/mcp-availability/")
MCP_REQUIRED_SERVERS = ("zai-mcp-server", "MiniMax", "codegraph")  # coding fixture 期望下限


@dataclass
class Assertion:
    name: str
    ok: bool
    detail: str


def _ok(name: str, detail: str = "") -> Assertion:
    return Assertion(name, True, detail)


def _bad(name: str, detail: str) -> Assertion:
    return Assertion(name, False, detail)


def _read(root: Path, rel: str) -> Optional[str]:
    p = root / rel
    return p.read_text(encoding="utf-8") if p.is_file() else None


def _hash_tree(directory: Path) -> dict:
    out = {}
    if directory.is_dir():
        for p in sorted(directory.rglob("*")):
            if p.is_file():
                out[str(p.relative_to(directory))] = hashlib.sha256(p.read_bytes()).hexdigest()
    return out


def assert_stage1(variant, root, verify_exit, final_texts, extra=None):
    """按 design §4 断言表逐项核对 workspace；extra 由 stage1 runner 采集。"""
    extra = extra or {}
    results = []
    texts = final_texts or {}

    # --- pre-check：诊断报告产出 + 项目文件零改动 ---
    report_text = texts.get("pre-check", "")
    results.append(_ok("pre-check.report") if "诊断" in report_text or "检查" in report_text
                   else _bad("pre-check.report", f"final_text 无诊断标记：{report_text[:80]!r}"))
    if variant == "fresh":  # v3/mcp_pre 本身有预置文件，零改动断言只对全新变体成立
        clean = extra.get("pre_check_clean")
        results.append(_ok("pre-check.zero-change") if clean is not False
                       else _bad("pre-check.zero-change", "pre-check 产生文件改动"))

    # --- rule-config：规则清单 / L0 v4 / 权限区 / 内联区 / --verify ---
    rules_dir = root / ".claude" / "rules"
    actual = sorted(p.name for p in rules_dir.glob("*.md")) if rules_dir.is_dir() else []
    expect = sorted(gen.expected_rules_files())
    results.append(_ok("rules.manifest") if actual == expect
                   else _bad("rules.manifest", f"清单不符：{actual} != {expect}"))
    claude_md = _read(root, "CLAUDE.md") or ""
    results.append(_ok("l0.v4") if L0_BEGIN in claude_md else _bad("l0.v4", "CLAUDE.md 无 v4 受管区块"))
    settings_raw = _read(root, ".claude/settings.json")
    gate_ok = False
    if settings_raw is not None:
        try:
            deny = json.loads(settings_raw).get("permissions", {}).get("deny", [])
            gate_ok = GATE_BEGIN in deny and GATE_END in deny
        except ValueError:
            gate_ok = False
    results.append(_ok("gate.region") if gate_ok else _bad("gate.region", "settings.json 无受管 deny 区块"))
    agents_md = _read(root, "AGENTS.md") or ""
    results.append(_ok("codex.inline") if INLINE_BEGIN in agents_md
                   else _bad("codex.inline", "AGENTS.md 无 codex-rules-inline 区块"))
    results.append(_ok("verify.exit0") if verify_exit == 0
                   else _bad("verify.exit0", f"--verify 退出码 {verify_exit}"))

    # --- v3 变体追加：确定性升级 + 备份 + 区块外逐字不变 ---
    if variant == "v3":
        results.append(_ok("v3.upgraded") if L0_BEGIN in claude_md and "v3:start" not in claude_md
                       else _bad("v3.upgraded", "v3 区块未升级为 v4"))
        legacy = root / "cadence" / "legacy"
        results.append(_ok("v3.backup") if legacy.is_dir() and any(legacy.iterdir())
                       else _bad("v3.backup", "cadence/legacy/ 无备份"))
        baseline = extra.get("outside_l0_baseline")
        if baseline is None:
            results.append(_bad("v3.outside-verbatim", "缺少区块外基线（runner 未采集）"))
        else:
            m = re.search(re.escape(L0_BEGIN) + r".*?" + "v4:end -->", claude_md, re.S)
            outside = claude_md.replace(m.group(0), "") if m else claude_md
            results.append(_ok("v3.outside-verbatim") if baseline in outside
                           else _bad("v3.outside-verbatim", "区块外内容变化"))

    # --- mcp-configuration：合法性 / 一致性 / .gitignore 精确行 ---
    mcp_raw = _read(root, ".mcp.json")
    servers = {}
    if mcp_raw is not None:
        try:
            servers = json.loads(mcp_raw).get("mcpServers", {})
        except ValueError:
            servers = {}
    missing = [s for s in MCP_REQUIRED_SERVERS if s not in servers]
    results.append(_ok("mcp.valid") if mcp_raw is not None and not missing and bool(servers)
                   else _bad("mcp.valid", f".mcp.json 缺 server：{missing}"))
    toml = _read(root, ".codex/config.toml") or ""
    inconsistent = [s for s in servers if f"[mcp_servers.{s}]" not in toml]
    results.append(_ok("mcp.codex-consistent") if servers and not inconsistent
                   else _bad("mcp.codex-consistent", f"config.toml 缺区块：{inconsistent}"))
    gi = _read(root, ".gitignore") or ""
    gi_lines = {ln.strip() for ln in gi.splitlines()}
    absent = [ln for ln in GITIGNORE_LINES if ln not in gi_lines]
    results.append(_ok("mcp.gitignore") if not absent else _bad("mcp.gitignore", f"缺行：{absent}"))
    if variant == "mcp_pre":
        results.append(_ok("mcp.pre-existing") if "existing-server" in servers
                       else _bad("mcp.pre-existing", "既有 server 被覆盖"))

    # --- project-rules-examples：就位 + 不写 .claude/rules/ ---
    pr = root / "cadence" / "project-rules"
    placed = pr.is_dir() and (pr / "README.md").is_file() and (pr / "examples").is_dir()
    results.append(_ok("prx.placed") if placed else _bad("prx.placed", "cadence/project-rules/ 未就位"))
    before = extra.get("rules_before")
    if before is None:
        # 缺快照时判 skip（ok=True + skip: 前缀），不判红也不计入失败——
        # 离线/单测调用（test_fresh_all_green、test_v3_upgrade_assertions）无需补传
        results.append(_ok("prx.not-rules",
                           "skip：缺 rules_before 快照（runner 未采集），本项不判"))
    else:
        results.append(_ok("prx.not-rules") if _hash_tree(rules_dir) == before
                       else _bad("prx.not-rules", ".claude/rules/ 被本步修改"))
    return results
```

- [ ] **Step 4: 运行测试确认通过**

```bash
python3 -m unittest eval.tests.test_stage1_assertions -v
```

预期：8 个用例全部 PASS。

- [ ] **Step 5: 提交建议**

```bash
git add eval/install/ eval/tests/test_stage1_assertions.py
git commit -m "feat(eval): 阶段一产物断言表——清单/L0v4/权限区/内联区/verify/MCP/幂等锚点"
```

> 产物自动提交开关当前=关闭：跳过 `git commit`，只报告上述新增路径，等待维护者确认。

---
### Task 3: CLI 调用封装 + mock CLI + 阶段一流水线 runner

**Files:**
- Create: `eval/runner/__init__.py`（空文件）
- Create: `eval/runner/proc.py`、`eval/runner/mock_cli.py`、`eval/install/commands.py`、`eval/install/stage1.py`、`eval/runner/cli.py`
- Test: `eval/tests/test_stage1_runner.py`

**Interfaces:**
- Consumes: `gen.make_fixture`/`gen.FixturePaths`（Task 1）、`asrt.assert_stage1`（Task 2）。
- Produces:
  - `proc.INVOCATIONS: dict[str, dict]`——四端 argv 模板与捕获方式
  - `proc.build_argv(agent: str, model: str, max_turns: Optional[int] = None, prompt_env: str = "EVAL_PROMPT") -> list[str]`（prompt 占位符只从 `os.environ[prompt_env]` 取值）
  - `proc.run_cli(agent: str, prompt: str, cwd: Path, home: Optional[Path], pins: dict, timeout_s: int, env_extra: Optional[dict] = None, bin_dir: Optional[Path] = None, out_dir: Optional[Path] = None, skill_env: Optional[dict] = None, session_root: Optional[Path] = None) -> dict`——返回 `{"returncode": int, "stdout_path": str, "stderr": str, "duration_s": float, "transcript_path": str, "timed_out": bool}`；`home` 为 `None` 时不覆写 HOME（HOME 策略 b 方案：真实 HOME + 登录态）；`skill_env` 逐项并入子进程 env（skill 发现路径注入 fixture 隔离 home）；stdout 捕获文件写入 `out_dir`（缺省系统临时目录）下 `.eval-<agent>-<pid>-<ms>-stdout.jsonl`，**绝不落在 fixture 根内**（防污染幂等快照与 P8 判分）；claude/codex 的 transcript 即该 stdout 文件，pi/kimi 的 transcript_path 为运行后定位到的 session/wire 文件——定位搜索根＝`home`（非 None 时）否则 `session_root`（真实模式调用方传 `fixture.home`：skill_env 已把 config-dir 重定向到 fixture 根，session 落其下；两者皆 None＝mock 冒烟语义才跳过定位、回退 stdout）
  - `proc.cli_version_check(agent: str, pins: dict, bin_dir: Optional[Path] = None) -> tuple[bool, str]`
  - `proc.extract_final_text(agent: str, transcript_path: Path) -> str`（阶段一轻量终文本提取；组 2 适配器为判分权威，此处仅供断言表）
  - `cmd.STAGE1_COMMANDS: list[dict]`（name/prompt 四项）
  - `stage1.run_stage1(agent: str, fixture: gen.FixturePaths, pins: dict, timeout_s: int = 1200, *, cli=proc.run_cli, verify: Optional[Callable[[Path], int]] = None, bin_dir: Optional[Path] = None, skill_env: Optional[dict] = None) -> dict`——Stage1Report：`{"variant", "agent", "commands": [{"name", "returncode", "duration_s", "final_text"}], "verify_exit", "assertions": [{"name", "ok", "detail"}], "ok": bool}`；mock 分支由 env `EVAL_COMMAND` 驱动（见 mock_cli）
  - `mock_cli.main(argv: Optional[list] = None) -> int`——`python3 -m eval.runner.mock_cli --agent <name>`，按 env 写罐头产物 + 输出罐头轨迹
  - `cli.main(argv: Optional[list] = None) -> int`——子命令入口，本任务注册 `stage1` 与 `smoke`
  - Task 4/14/18/19 消费。

**四端调用形态（锁定；Tier-1 首夜允许只调 `agents.json` 数据修正，不改代码）：**

| 端 | argv 模板 | 轨迹捕获 |
|---|---|---|
| claude | `claude -p {prompt} --output-format stream-json --verbose --model {model} --max-turns {n}` | stdout 即 stream-json |
| codex | `codex exec --json --model {model} {prompt}` | stdout 即 JSONL 事件流 |
| pi | `pi -p {prompt} --model {model}` | 运行后按 mtime 定位 `~/.pi/agent/sessions/**/run-*/session.jsonl` |
| kimi | `kimi -p {prompt} --model {model}` | 运行后按 mtime 定位 `~/.kimi-code/sessions/**/agents/main/wire.jsonl` |

- [ ] **Step 1: 写失败测试**

```python
"""eval/tests/test_stage1_runner.py —— CLI 封装与阶段一流水线（mock CLI，零真实端）。"""
import json
import os
import stat
import tempfile
import unittest
from pathlib import Path

from eval.fixtures import generator as gen
from eval.install import commands as cmd
from eval.install import stage1
from eval.runner import proc

REPO_ROOT = Path(__file__).resolve().parents[2]


def _make_mock_bin(base: Path) -> Path:
    """生成四个 mock CLI 可执行文件（转发到 eval.runner.mock_cli）。"""
    bin_dir = base / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    for agent in ("claude", "codex", "pi", "kimi"):
        wrapper = bin_dir / agent
        wrapper.write_text(
            "#!/usr/bin/env python3\n"
            "import sys\n"
            f"sys.path.insert(0, {str(REPO_ROOT)!r})  # 子进程可导入 eval 包（脚本模式 sys.path[0]=bin 目录）\n"
            "from eval.runner import mock_cli\n"
            f"sys.exit(mock_cli.main(['--agent', '{agent}']))\n",
            encoding="utf-8")
        wrapper.chmod(wrapper.stat().st_mode | stat.S_IEXEC)
    return bin_dir


class TestProc(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)

    def test_argv_from_env_no_shell(self):
        """ut-proc-env：prompt 只经 env 注入，argv 列表直传（无 shell 展开污染）。"""
        poison = '含"双引号"与 $HOME 与 `id` 反引号'
        os.environ["EVAL_PROMPT"] = poison
        argv = proc.build_argv("claude", "glm-5.3", max_turns=40)
        self.assertIn(poison, argv)
        self.assertIn("--model", argv)
        self.assertNotIn("sh", argv[0])
        self.assertNotIn("-c", argv[:2])

    def test_run_cli_mock_stage1_green(self):
        """ut-proc-run：mock claude 跑通一次调用并产出轨迹文件。"""
        bin_dir = _make_mock_bin(self.base)
        out = proc.run_cli("claude", "/pre-check", cwd=self.base, home=self.base / "home",
                           pins={"pinned_model": "glm-5.3"}, timeout_s=60,
                           env_extra={"EVAL_STAGE": "stage1"}, bin_dir=bin_dir)
        self.assertEqual(out["returncode"], 0)
        first = Path(out["stdout_path"]).read_text(encoding="utf-8").splitlines()[0]
        self.assertIn(json.loads(first)["type"], ("system", "user", "assistant", "result"))
        # stdout 捕获文件移出 cwd/fixture 根（缺省落系统临时目录），防污染幂等快照
        self.assertTrue(Path(out["stdout_path"]).name.startswith(".eval-claude-"))
        self.assertNotEqual(Path(out["stdout_path"]).parent, self.base)


class TestStage1Runner(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.bin_dir = _make_mock_bin(self.base)
        self.fx = gen.make_fixture("fresh", self.base / "fx", REPO_ROOT)

    def test_stage1_commands_table(self):
        """ut-s1r-commands：四 command 依序且均为 no-interrupt 确定性形态。"""
        self.assertEqual([c["name"] for c in cmd.STAGE1_COMMANDS],
                         ["pre-check", "rule-config", "mcp-configuration",
                          "project-rules-examples"])
        for c in cmd.STAGE1_COMMANDS[1:]:
            self.assertIn("no-interrupt", c["prompt"])

    def test_stage1_mock_all_green(self):
        """ut-s1r-green：mock CLI 下阶段一全绿（Tier-0 冒烟核心）。"""
        report = stage1.run_stage1("claude", self.fx, {"pinned_model": "glm-5.3"},
                                   bin_dir=self.bin_dir, verify=lambda root: 0)
        bad = [a for a in report["assertions"] if not a["ok"]]
        self.assertEqual(bad, [], [f"{a['name']}: {a['detail']}" for a in bad])
        self.assertTrue(report["ok"])
        self.assertEqual(report["verify_exit"], 0)

    def test_stage1_collects_extra(self):
        """ut-s1r-extra：runner 采集 pre-check 零改动与 rules_before 快照供断言表。"""
        report = stage1.run_stage1("claude", self.fx, {"pinned_model": "glm-5.3"},
                                   bin_dir=self.bin_dir, verify=lambda root: 0)
        names = [a["name"] for a in report["assertions"]]
        self.assertIn("pre-check.zero-change", names)
        self.assertIn("prx.not-rules", names)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 运行确认失败**

```bash
python3 -m unittest eval.tests.test_stage1_runner -v
```

预期：全部 ERROR（`No module named 'eval.runner'`）。

- [ ] **Step 3: 最小实现（proc.py / mock_cli.py / commands.py / stage1.py / cli.py）**

`eval/runner/proc.py`：

```python
"""四端 CLI 调用封装：env 注入 prompt、HOME 覆写、超时与轨迹捕获。"""
import json
import os
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Optional

INVOCATIONS = {
    "claude": {
        "argv": ["claude", "-p", "{prompt}", "--output-format", "stream-json",
                 "--verbose", "--model", "{model}", "--max-turns", "{turns}"],
        "capture": "stdout",
    },
    "codex": {
        "argv": ["codex", "exec", "--json", "--model", "{model}", "{prompt}"],
        "capture": "stdout",
    },
    "pi": {"argv": ["pi", "-p", "{prompt}", "--model", "{model}"], "capture": "session"},
    "kimi": {"argv": ["kimi", "-p", "{prompt}", "--model", "{model}"], "capture": "session"},
}

DEFAULT_TURNS = 40
PROMPT_ENV = "EVAL_PROMPT"

SESSION_PATTERNS = {
    "pi": [".pi/agent/sessions/**/run-*/session.jsonl"],
    "kimi": [".kimi-code/sessions/**/agents/*/wire.jsonl"],
}


def build_argv(agent, model, max_turns=None, prompt_env=PROMPT_ENV):
    """按端模板组装 argv；prompt 占位符只从环境变量取值（spec：MUST NOT 内联 shell）。"""
    template = list(INVOCATIONS[agent]["argv"])
    prompt = os.environ.get(prompt_env, "")
    fills = {"{prompt}": prompt, "{model}": model,
             "{turns}": str(max_turns if max_turns is not None else DEFAULT_TURNS)}
    argv = []
    for part in template:
        for key, value in fills.items():
            if key in part:
                part = part.replace(key, value)
        argv.append(part)
    return argv


def _find_newest(home: Path, patterns: list, since_ts: float) -> Optional[Path]:
    best, best_mt = None, -1.0
    for pattern in patterns:
        for p in home.glob(pattern):
            try:
                mt = p.stat().st_mtime
            except OSError:
                continue
            if mt >= since_ts and mt > best_mt:
                best, best_mt = p, mt
    return best


def run_cli(agent, prompt, cwd, home, pins, timeout_s, env_extra=None,
            bin_dir=None, out_dir=None, skill_env=None, session_root=None):
    """执行一次端调用并捕获轨迹。返回 dict（见 Interfaces）。

    env 注入：EVAL_PROMPT 由本函数写入子进程 env；PATH 前置 bin_dir（mock 模式）。
    HOME 策略：home 非 None 时覆写 HOME（mock/隔离模式）；home=None 时不覆写
    （真实 HOME，登录态可用），并以 skill_env 注入 skill 发现路径（b 方案）。
    session 搜索根（capture=session 的 pi/kimi）：home 非 None 时即 home；
    home=None 且 skill_env 注入（真实模式）时用 session_root——调用方传
    fixture.home（skill_env 已把 config-dir 重定向到 fixture 根，session
    落其下，SESSION_PATTERNS 相对路径可命中）；仅 home=None 且未传
    session_root（mock 冒烟语义）才跳过定位。
    stdout 捕获文件写入 out_dir（缺省系统临时目录），不落 fixture 根。
    shell=False + 列表 argv，杜绝 shell 展开污染。
    """
    env = dict(os.environ)
    if home is not None:
        env["HOME"] = str(home)
    if skill_env:
        env.update({k: str(v) for k, v in skill_env.items()})
    env[PROMPT_ENV] = prompt
    if env_extra:
        env.update({k: str(v) for k, v in env_extra.items()})
    if bin_dir is not None:
        env["PATH"] = str(bin_dir) + os.pathsep + env.get("PATH", "")
    argv = build_argv(agent, pins.get("pinned_model", ""), pins.get("max_turns"))
    started = time.time()
    capture_dir = Path(out_dir) if out_dir is not None else Path(tempfile.gettempdir())
    capture_dir.mkdir(parents=True, exist_ok=True)
    stdout_file = capture_dir / f".eval-{agent}-{os.getpid()}-{int(started * 1000)}-stdout.jsonl"
    proc = subprocess.Popen(
        argv, cwd=str(cwd), env=env, shell=False,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.DEVNULL)
    try:
        out, err = proc.communicate(timeout=timeout_s)
        returncode, timed_out = proc.returncode, False
    except subprocess.TimeoutExpired:
        proc.kill()
        out, err = proc.communicate()
        returncode, timed_out = -9, True
    duration = time.time() - started
    stdout_file.write_bytes(out or b"")
    transcript = str(stdout_file)
    if INVOCATIONS[agent]["capture"] == "session":
        search_root = home if home is not None else session_root
        found = (_find_newest(Path(search_root), SESSION_PATTERNS[agent], started - 1)
                 if search_root is not None else None)
        if found is None:
            found = stdout_file  # mock/兜底：未定位到 session 文件时回退 stdout 捕获
        transcript = str(found)
    return {"returncode": returncode, "stdout_path": str(stdout_file),
            "stderr": (err or b"").decode("utf-8", "replace")[-2000:],
            "duration_s": duration, "transcript_path": transcript,
            "timed_out": timed_out}


def cli_version_check(agent, pins, bin_dir=None):
    """CLI 版本锁核验：pins['cli_version'] 非空才强制（空=只记录不锁，Task 20 固化）。"""
    locked = (pins or {}).get("cli_version") or ""
    if not locked:
        return True, ""
    env = dict(os.environ)
    if bin_dir is not None:
        env["PATH"] = str(bin_dir) + os.pathsep + env.get("PATH", "")
    try:
        out = subprocess.run([INVOCATIONS[agent]["argv"][0], "--version"],
                             capture_output=True, text=True, timeout=30, env=env,
                             shell=False).stdout
    except (OSError, subprocess.TimeoutExpired) as exc:
        return False, f"version-check-failed: {exc}"
    ok = locked in out
    return ok, "" if ok else f"cli 版本漂移：期望含 {locked}，实际 {out.strip()[:80]}"


def extract_final_text(agent, transcript_path):
    """阶段一轻量终文本：claude/mock 轨迹取 result.result；其余取最后一条 assistant 文本。

    仅供断言表消费（"诊断报告产出"类弱断言）；判分权威是组 2 适配器。
    mock 轨迹与 claude stream-json 同构（含 result 行）；真实 codex/pi/kimi
    轨迹无 result 行，故对所有端接受 result 行均无副作用。
    """
    if not transcript_path:
        return ""
    try:
        with open(transcript_path, encoding="utf-8", errors="replace") as fh:
            lines = [ln for ln in fh.read().splitlines() if ln.strip()]
    except OSError:
        return ""
    final = ""
    for ln in lines:
        try:
            d = json.loads(ln)
        except ValueError:
            continue
        if d.get("type") == "result" and isinstance(d.get("result"), str):
            final = d["result"]
        elif isinstance(d.get("message"), dict):
            content = d["message"].get("content")
            if isinstance(content, list):
                texts = [c.get("text", "") for c in content
                         if isinstance(c, dict) and c.get("type") == "text"]
                if texts:
                    final = "\n".join(t for t in texts if t)
    return final
```

`eval/runner/mock_cli.py`：

```python
"""mock 四端 CLI：罐头产物 + 罐头轨迹（Tier-0 冒烟与 Tier-1 付费前自检）。

只验证 harness 管线（argv/env/捕获/断言/报告），不验证 skill 语义——
skill 语义归 Tier-1 真实端。行为由 env 驱动：
  EVAL_STAGE=stage1|probe   EVAL_PROBE_ID=P1..P8
  EVAL_COMMAND=pre-check|rule-config|mcp-configuration|project-rules-examples
（阶段一按 command 名分支：pre-check 只产诊断报告零写盘，其余各写各自产物）
"""
import argparse
import json
import os
import sys
from pathlib import Path

RULES_FILES = ["README.md", "code-reading.md", "code-usage.md", "document-storage.md",
               "language.md", "markdown-format.md", "mcp-servers.md",
               "openspec-superpowers-workflow.md", "playwright.md"]


def _emit(lines):
    for ln in lines:
        sys.stdout.write(json.dumps(ln, ensure_ascii=False) + "\n")


def _stage1_pre_check(cwd: Path) -> None:
    """pre-check：只产出诊断报告（stdout），零写盘（断言 pre-check.zero-change）。"""


def _stage1_rule_config(cwd: Path) -> None:
    """rule-config：规则清单 / L0 v4 / 权限区 / codex 内联区。"""
    rules = cwd / ".claude" / "rules"
    rules.mkdir(parents=True, exist_ok=True)  # 先建目录再写文件
    for name in RULES_FILES:
        (rules / name).write_text("# rule\n", encoding="utf-8")
    (cwd / "CLAUDE.md").write_text(
        "<!-- cadence-managed:openspec-superpowers-routing:v4:start -->\n"
        "Cadence L0 路由内核 v4\n"
        "<!-- cadence-managed:openspec-superpowers-routing:v4:end -->\n",
        encoding="utf-8")
    (cwd / ".claude" / "settings.json").write_text(json.dumps({"permissions": {"deny": [
        "@@cadence-managed:permission-gate:v1:start@@", "Grep", "Glob", "Bash(grep:*)",
        "@@cadence-managed:permission-gate:v1:end@@"]}}, ensure_ascii=False, indent=2),
        encoding="utf-8")
    (cwd / "AGENTS.md").write_text(
        "<!-- cadence-managed:codex-rules-inline:v1:start -->\n链\n"
        "<!-- cadence-managed:codex-rules-inline:v1:end -->\n", encoding="utf-8")


def _stage1_mcp(cwd: Path) -> None:
    """mcp-configuration：.mcp.json / .codex/config.toml / .gitignore 精确行。"""
    (cwd / ".mcp.json").write_text(json.dumps({"mcpServers": {
        "zai-mcp-server": {"command": "npx"}, "MiniMax": {"command": "uvx"},
        "codegraph": {"command": "codegraph-server"},
        "existing-server": {"command": "echo"}}}, indent=2), encoding="utf-8")
    (cwd / ".codex").mkdir(exist_ok=True)
    (cwd / ".codex" / "config.toml").write_text(
        "[mcp_servers.zai-mcp-server]\ncommand = \"npx\"\n"
        "[mcp_servers.MiniMax]\ncommand = \"uvx\"\n"
        "[mcp_servers.codegraph]\ncommand = \"codegraph-server\"\n"
        "[mcp_servers.existing-server]\ncommand = \"echo\"\n", encoding="utf-8")
    (cwd / ".gitignore").write_text(
        ".worktrees/\n.mcp.json\n.codex/config.toml\ncadence/cache/mcp-availability/\n",
        encoding="utf-8")


def _stage1_prx(cwd: Path) -> None:
    """project-rules-examples：仅写 cadence/project-rules/，不碰 .claude/rules/。"""
    pr = cwd / "cadence" / "project-rules"
    (pr / "examples").mkdir(parents=True, exist_ok=True)
    (pr / "README.md").write_text("# 项目规则\n", encoding="utf-8")


# 阶段一按 command 名分支（env EVAL_COMMAND）：pre-check 零写盘，其余各写各自产物
STAGE1_WRITERS = {
    "rule-config": _stage1_rule_config,
    "mcp-configuration": _stage1_mcp,
    "project-rules-examples": _stage1_prx,
}


def _probe_transcript(agent, probe_id):
    """罐头探针轨迹：P1 演示 deny→改道；MCP 探针演示 fake server 调用。

    工具入参用真实形状：Bash→{"command": ...}、Read/Write→{"file_path": ...}、
    检索/MCP→{"query": ...}（适配器 WriteEvent/P8 判分依赖该形状）。
    """
    model = {"claude": "glm-5.3", "codex": "gpt-5.4",
             "pi": "glm-5.3", "kimi": "kimi-code/kimi-for-coding"}[agent]
    if probe_id == "P1":
        calls = [("Bash", {"command": "ls -R src"}),
                 ("mcp__codegraph__codegraph_explore", {"query": "orders"})]
    elif probe_id in ("P2", "P6", "P7"):
        server = {"P2": "context7", "P6": "time", "P7": "zai-mcp-server"}[probe_id]
        calls = [(f"mcp__{server.replace('-', '_')}__tool", {"query": "seed"})]
    else:
        calls = [("Read", {"file_path": "src/main.py"}),
                 ("Write", {"file_path": "cadence/plans/doc.md"})]
    lines = [{"type": "system", "subtype": "init", "session_id": "mock",
              "model": model, "version": "2.1.233"}]
    for i, (tool, inp) in enumerate(calls):
        lines.append({"type": "assistant", "message": {"model": model, "content": [
            {"type": "tool_use", "id": f"t{i}", "name": tool, "input": inp}]}})
        denied = probe_id == "P1" and tool == "Bash"
        lines.append({"type": "user", "message": {"content": [
            {"type": "tool_result", "tool_use_id": f"t{i}", "is_error": denied,
             "content": "permission denied by settings" if denied else "ok"}]}})
    lines.append({"type": "result", "subtype": "success", "duration_ms": 3000,
                  "result": "中文结论：调用链已梳理 / 任务完成"})
    return lines


def main(argv=None):
    parser = argparse.ArgumentParser(description="mock coding agent CLI（eval 专用）")
    parser.add_argument("--agent", required=True, choices=["claude", "codex", "pi", "kimi"])
    args = parser.parse_args(argv)
    cwd = Path(os.environ.get("EVAL_CWD", os.getcwd()))
    stage = os.environ.get("EVAL_STAGE", "probe")
    probe_id = os.environ.get("EVAL_PROBE_ID", "P1")
    if stage == "stage1":
        command = os.environ.get("EVAL_COMMAND", "")
        writer = STAGE1_WRITERS.get(command)  # pre-check/未知 command：零写盘
        if writer is not None:
            writer(cwd)
        _emit([{"type": "result", "subtype": "success",
                "result": f"诊断报告：{command or '检查'}完成", "duration_ms": 5000}])
        return 0
    _emit(_probe_transcript(args.agent, probe_id))
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

`eval/install/commands.py`：

```python
"""阶段一四 command prompt 表（维护者直接 command 调用形态；no-interrupt 确定性）。"""
STAGE1_COMMANDS = [
    {"name": "pre-check", "prompt": "/pre-check"},
    {"name": "rule-config", "prompt": "/rule-config no-interrupt"},
    {"name": "mcp-configuration", "prompt": "/mcp-configuration no-interrupt"},
    {"name": "project-rules-examples", "prompt": "/project-rules-examples no-interrupt"},
]
```

`eval/install/stage1.py`：

```python
"""阶段一安装流水线：四 command 依序 headless 调用 + 断言表 + --verify 消费。"""
import hashlib
import re
import subprocess
import sys
from pathlib import Path
from typing import Callable, Optional

from eval.fixtures import generator as gen
from eval.install import assertions as asrt
from eval.install.commands import STAGE1_COMMANDS
from eval.runner import proc

V3_BLOCK_RE = re.compile(
    r"<!-- cadence-managed:openspec-superpowers-routing:v3:start -->.*?v3:end -->", re.S)


def _tree_hash(directory: Path) -> dict:
    out = {}
    if directory.is_dir():
        for p in sorted(directory.rglob("*")):
            if p.is_file():
                out[str(p.relative_to(directory))] = \
                    hashlib.sha256(p.read_bytes()).hexdigest()
    return out


def _default_verify(repo: Path) -> Callable[[Path], int]:
    script = repo / "cadence-init/skills/rule-config/scripts/rule-config.py"

    def verify(root: Path) -> int:
        return subprocess.run(
            [sys.executable, str(script), "--verify", "--project-root", str(root)],
            capture_output=True, text=True, shell=False).returncode
    return verify


def _detect_variant(root: Path) -> tuple:
    """由 workspace 现状推断变体（fresh/v3/mcp_pre）与 v3 区块外基线。"""
    if (root / "CLAUDE.md").is_file():
        text = (root / "CLAUDE.md").read_text(encoding="utf-8")
        m = V3_BLOCK_RE.search(text)
        if m:
            return "v3", text.replace(m.group(0), "")
    if (root / ".mcp.json").is_file():
        raw = (root / ".mcp.json").read_text(encoding="utf-8")
        if "existing-server" in raw:
            return "mcp_pre", None
    return "fresh", None


def run_stage1(agent, fixture, pins, timeout_s=1200, *, cli=proc.run_cli,
               verify=None, bin_dir=None, skill_env=None):
    variant, outside_baseline = _detect_variant(fixture.root)
    root, home, repo = fixture.root, fixture.home, fixture.repo
    verify = verify or _default_verify(repo)
    extra: dict = {}
    commands_report = []
    for spec in STAGE1_COMMANDS:
        before = _tree_hash(root)
        out = cli(agent, spec["prompt"], cwd=root,
                  home=None if skill_env else home, pins=pins,
                  timeout_s=timeout_s,
                  env_extra={"EVAL_STAGE": "stage1", "EVAL_COMMAND": spec["name"]},
                  bin_dir=bin_dir, skill_env=skill_env)
        final_text = proc.extract_final_text(agent, out.get("transcript_path") or "")
        if spec["name"] == "pre-check":
            extra["pre_check_clean"] = before == _tree_hash(root)
        if spec["name"] == "rule-config":
            extra["rules_before"] = _tree_hash(root / ".claude" / "rules")
        commands_report.append({"name": spec["name"], "returncode": out["returncode"],
                                "duration_s": out["duration_s"], "final_text": final_text})
    verify_exit = verify(root)
    if outside_baseline is not None:
        extra["outside_l0_baseline"] = outside_baseline
    results = asrt.assert_stage1(variant, root, verify_exit,
                                 {c["name"]: c["final_text"] for c in commands_report},
                                 extra)
    return {"variant": variant, "agent": agent, "commands": commands_report,
            "verify_exit": verify_exit,
            "assertions": [{"name": r.name, "ok": r.ok, "detail": r.detail} for r in results],
            "ok": all(r.ok for r in results) and verify_exit == 0}
```

`eval/runner/cli.py`（本任务注册 `stage1`/`smoke`，后续任务逐个追加子命令）：

```python
"""eval 子命令入口。用法：python3 -m eval.runner.cli <subcommand> [options]。"""
import argparse
import stat
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def mock_bin(base: Path) -> Path:
    """生成四个 mock CLI 可执行（转发 eval.runner.mock_cli），返回 bin 目录。"""
    bin_dir = base / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    for agent in ("claude", "codex", "pi", "kimi"):
        wrapper = bin_dir / agent
        wrapper.write_text(
            "#!/usr/bin/env python3\nimport sys\n"
            f"sys.path.insert(0, {str(REPO_ROOT)!r})\n"
            "from eval.runner import mock_cli\n"
            f"sys.exit(mock_cli.main(['--agent', '{agent}']))\n", encoding="utf-8")
        wrapper.chmod(wrapper.stat().st_mode | stat.S_IEXEC)
    return bin_dir


def cmd_smoke(args):
    """mock 冒烟：四端 × 阶段一全绿（Tier-0 / Tier-1 付费前自检）。"""
    from eval.fixtures import generator as gen
    from eval.install import stage1
    import json
    failed = []
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        bin_dir = mock_bin(base)
        for agent in ("claude", "codex", "pi", "kimi"):
            fx = gen.make_fixture("fresh", base / agent, REPO_ROOT)
            report = stage1.run_stage1(agent, fx, {"pinned_model": "mock"},
                                       bin_dir=bin_dir, verify=lambda root: 0)
            print(f"[smoke] {agent}: {'OK' if report['ok'] else 'FAIL'}")
            if not report["ok"]:
                failed.extend(f"{agent}:{a['name']}" for a in report["assertions"]
                              if not a["ok"])
    if failed:
        print("[smoke] 失败项：", json.dumps(failed, ensure_ascii=False))
        return 1
    return 0


def cmd_stage1(args):
    from eval.fixtures import generator as gen
    from eval.install import stage1
    fx = gen.make_fixture(args.variant, Path(args.base).resolve(), REPO_ROOT)
    report = stage1.run_stage1(args.agent, fx, {"pinned_model": args.model})
    import json
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ok"] else 1


def build_parser():
    parser = argparse.ArgumentParser(prog="eval")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("smoke", help="mock 冒烟（零真实 CLI）")
    p.set_defaults(func=cmd_smoke)
    p = sub.add_parser("stage1", help="单端阶段一安装流水线（真实 CLI，self-hosted）")
    p.add_argument("--agent", required=True, choices=["claude", "codex", "pi", "kimi"])
    p.add_argument("--variant", default="fresh", choices=["fresh", "v3", "mcp_pre"])
    p.add_argument("--base", required=True, help="fixture 基目录（临时目录）")
    p.add_argument("--model", default="")
    p.set_defaults(func=cmd_stage1)
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: 运行测试确认通过**

```bash
python3 -m unittest eval.tests.test_stage1_runner -v
python3 -m eval.runner.cli smoke
```

预期：5 个用例全部 PASS；smoke 输出四端 `OK` 且退出码 0。

- [ ] **Step 5: 提交建议**

```bash
git add eval/runner/ eval/install/commands.py eval/install/stage1.py eval/tests/test_stage1_runner.py
git commit -m "feat(eval): 四端 CLI 封装（env 注入/HOME 覆写）、mock CLI 与阶段一流水线"
```

> 产物自动提交开关当前=关闭：跳过 `git commit`，只报告上述新增路径，等待维护者确认。

### Task 4: 幂等双跑 / 三跑检查

**Files:**
- Create: `eval/install/idempotency.py`
- Test: `eval/tests/test_idempotency.py`

**Interfaces:**
- Consumes: `stage1.run_stage1`（Task 3，测试经 `cli`/`verify` 注入 mock）、`gen.make_fixture`（Task 1）。
- Produces:
  - `idem.snapshot_tree(root: Path) -> dict[str, str]`（相对路径→sha256，排除 `.git/` 与运行器自身产物 `.eval-*`——P8 幂等探针的 snapshot_unchanged 断言同源复用本函数，双重防线）
  - `idem.diff_trees(before: dict, after: dict) -> dict[str, str]`（`added/removed/changed`）
  - `idem.run_idempotency(agent: str, fixture: gen.FixturePaths, pins: dict, passes: int = 2, *, cli=proc.run_cli, verify: Optional[Callable] = None, bin_dir: Optional[Path] = None, skill_env: Optional[dict] = None) -> dict`——`{"passes": int, "diffs": [dict, ...]（第 i 遍相对前遍差集）, "stable": bool}`；末遍 diff 为空 → `stable=True`
  - Task 15（night runner 全新变体安装后校验）、Task 18（冒烟）消费。

- [ ] **Step 1: 写失败测试**

```python
"""eval/tests/test_idempotency.py —— 幂等双跑与 gate 过渡三遍稳态（tasks 1.3）。"""
import tempfile
import unittest
from pathlib import Path

from eval.fixtures import generator as gen
from eval.install import idempotency as idem
from eval.runner import cli as cli_mod

REPO_ROOT = Path(__file__).resolve().parents[2]


class TestIdempotency(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.bin = cli_mod.mock_bin(self.base)
        self.fx = gen.make_fixture("fresh", self.base / "fx", REPO_ROOT)

    def test_two_passes_byte_identical(self):
        """ut-idem-2pass：双跑末遍 workspace diff 为空（jarvy 先例）。"""
        rep = idem.run_idempotency("claude", self.fx, {"pinned_model": "glm-5.3"},
                                   passes=2, bin_dir=self.bin, verify=lambda r: 0)
        self.assertTrue(rep["stable"])
        self.assertEqual(rep["diffs"][-1], {})

    def test_three_passes_locks_gate_transition(self):
        """ut-idem-3pass：gate 从无到有过渡写入场景，第三遍达稳态幂等（显式锁定）。

        依据 rule-config SKILL：无 .mcp.json 的全新项目首轮 apply 因 S8 先写
        .mcp.json 实际创建权限区块；mock 首轮即含区块，第三遍仍必须零 diff。
        """
        rep = idem.run_idempotency("claude", self.fx, {"pinned_model": "glm-5.3"},
                                   passes=3, bin_dir=self.bin, verify=lambda r: 0)
        self.assertTrue(rep["stable"])
        self.assertEqual(rep["diffs"][2], {})

    def test_snapshot_excludes_git(self):
        """ut-idem-snap：快照排除 .git/ 与运行器自身产物 .eval-*（P8 可判）。"""
        (self.fx.root / ".eval-claude-123-456-stdout.jsonl").write_text(
            "x", encoding="utf-8")
        snap = idem.snapshot_tree(self.fx.root)
        self.assertTrue(all(not k.startswith(".git/") for k in snap))
        self.assertTrue(all(not k.startswith(".eval-") for k in snap))
        self.assertIn("package.json", snap)

    def test_detects_append_regression(self):
        """ut-idem-regress：第二遍追加内容被 diff 捕获（防假绿）。"""
        gi = self.fx.root / ".gitignore"
        gi.write_text("node_modules/\n", encoding="utf-8")  # fresh 变体无 .gitignore，先落初始内容
        first = idem.snapshot_tree(self.fx.root)
        gi.write_text(gi.read_text(encoding="utf-8") + "\n追加行\n", encoding="utf-8")
        diff = idem.diff_trees(first, idem.snapshot_tree(self.fx.root))
        self.assertIn(".gitignore", diff)
        self.assertEqual(diff[".gitignore"], "changed")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 运行确认失败**

```bash
python3 -m unittest eval.tests.test_idempotency -v
```

预期：全部 ERROR（`No module named 'eval.install.idempotency'`）。

- [ ] **Step 3: 最小实现**

`eval/install/idempotency.py`：

```python
"""幂等双跑/三跑：同一 fixture 连续安装，末遍 workspace diff 必须 byte-identical。"""
import hashlib
from pathlib import Path
from typing import Callable, Optional

from eval.runner import proc


def snapshot_tree(root: Path) -> dict:
    """workspace 文件快照（相对路径→sha256）；排除 .git/ 与运行器自身产物 .eval-*。"""
    out = {}
    for p in sorted(root.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(root).as_posix()
        if rel.startswith(".git/") or rel.startswith(".eval-"):
            continue
        out[rel] = hashlib.sha256(p.read_bytes()).hexdigest()
    return out


def diff_trees(before: dict, after: dict) -> dict:
    """after 相对 before 的变化集：{路径: 'added'|'removed'|'changed'}。"""
    diff = {}
    for path, digest in after.items():
        if path not in before:
            diff[path] = "added"
        elif before[path] != digest:
            diff[path] = "changed"
    for path in before:
        if path not in after:
            diff[path] = "removed"
    return diff


def run_idempotency(agent, fixture, pins, passes=2, *, cli=proc.run_cli,
                    verify=None, bin_dir=None, skill_env=None):
    """连续 N 遍安装；diffs[i] = 第 i+1 遍相对第 i 遍的差集；末遍空 → stable。"""
    from eval.install import stage1
    diffs = []
    prev = snapshot_tree(fixture.root)
    for _ in range(passes):
        stage1.run_stage1(agent, fixture, pins, cli=cli, verify=verify,
                          bin_dir=bin_dir, skill_env=skill_env)
        cur = snapshot_tree(fixture.root)
        diffs.append(diff_trees(prev, cur))
        prev = cur
    return {"passes": passes, "diffs": diffs, "stable": diffs[-1] == {}}
```

- [ ] **Step 4: 运行测试确认通过**

```bash
python3 -m unittest eval.tests.test_idempotency -v
```

预期：4 个用例全部 PASS。

- [ ] **Step 5: 提交建议**

```bash
git add eval/install/idempotency.py eval/tests/test_idempotency.py
git commit -m "feat(eval): 幂等双跑与 gate 过渡三遍稳态检查"
```

> 产物自动提交开关当前=关闭：跳过 `git commit`，只报告上述两个新增路径，等待维护者确认。

---
## 任务组 2：轨迹适配与断言器（eval-trajectory-scoring：tasks 2.1/2.2/2.4/2.5/2.6）

### Task 5: 统一中间格式定义（含模型回读字段）

**Files:**
- Create: `eval/ifmt.py`
- Test: `eval/tests/test_ifmt.py`

**Interfaces:**
- Consumes: 无（组 2 首个任务）。
- Produces（全组与报告层的数据契约）:
  - `@dataclass ifmt.ToolCall`：`index: int`（会话内时间序）、`tool: str`（归一化名，如 `Bash`/`Grep`/`mcp__codegraph__codegraph_explore`）、`raw_tool: str`（端原生名）、`args_digest: str`（参数摘要：Bash→命令头前 3 词；Edit/Write→file_path；其余→入参键名）、`is_error: bool`、`ts: Optional[str] = None`
  - `@dataclass ifmt.Denial`：`at_index: int`、`tool: str`、`reason: str`、`raw: dict`
  - `@dataclass ifmt.WriteEvent`：`at_index: int`、`path: str`
  - `@dataclass ifmt.IntermediateTrajectory`：`agent: str`、`model_readback: str = ""`（transcript 实测回读，非启动参数）、`model_changes: list = []`（pi 会话内变更，非空→该 run 作废）、`cli_version: Optional[str] = None`、`tool_calls: list = []`、`denials: list = []`、`writes: list = []`、`final_text: str = ""`、`started_at: str = ""`、`duration_s: float = 0.0`、`settings_snapshot: dict = {}`（fixture `.claude/settings.json` 受管区块快照，deny 归属判定依据）、`source_path: str = ""`
  - `IntermediateTrajectory.to_dict() -> dict` / `IntermediateTrajectory.from_dict(doc: dict) -> IntermediateTrajectory`
  - `ifmt.dump(traj, path: Path) -> None` / `ifmt.load(path: Path) -> IntermediateTrajectory`
  - Task 6–12、15–18 消费。

- [ ] **Step 1: 写失败测试**

```python
"""eval/tests/test_ifmt.py —— 统一中间格式（tasks 2.1 数据契约）。"""
import json
import tempfile
import unittest
from pathlib import Path

from eval import ifmt


def _sample_traj():
    traj = ifmt.IntermediateTrajectory(agent="claude")
    traj.model_readback = "glm-5.3"
    traj.cli_version = "2.1.233"
    traj.tool_calls = [
        ifmt.ToolCall(index=0, tool="Bash", raw_tool="Bash",
                      args_digest="ls -R src", is_error=False),
        ifmt.ToolCall(index=1, tool="mcp__codegraph__codegraph_explore",
                      raw_tool="mcp__codegraph__codegraph_explore",
                      args_digest="query", is_error=False),
    ]
    traj.denials = [ifmt.Denial(at_index=0, tool="Bash",
                                reason="permission denied", raw={"x": 1})]
    traj.writes = [ifmt.WriteEvent(at_index=1, path="cadence/plans/a.md")]
    traj.final_text = "中文结论"
    traj.settings_snapshot = {"permissions": {"deny": [
        "@@cadence-managed:permission-gate:v1:start@@", "Bash(ls:*)",
        "@@cadence-managed:permission-gate:v1:end@@"]}}
    return traj


class TestIfmt(unittest.TestCase):
    def test_roundtrip_dict(self):
        """ut-ifmt-roundtrip：dict 往返字段全保留。"""
        traj = _sample_traj()
        restored = ifmt.IntermediateTrajectory.from_dict(traj.to_dict())
        self.assertEqual(restored.agent, "claude")
        self.assertEqual(restored.model_readback, "glm-5.3")
        self.assertEqual(restored.tool_calls[1].tool, "mcp__codegraph__codegraph_explore")
        self.assertEqual(restored.denials[0].at_index, 0)
        self.assertEqual(restored.writes[0].path, "cadence/plans/a.md")
        self.assertIn("Bash(ls:*)", restored.settings_snapshot["permissions"]["deny"])

    def test_json_file_roundtrip(self):
        """ut-ifmt-json：落盘/读盘往返（transcript 分级保留的"中间格式"载体）。"""
        traj = _sample_traj()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "traj.json"
            ifmt.dump(traj, path)
            doc = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(doc["model_readback"], "glm-5.3")
            restored = ifmt.load(path)
            self.assertEqual(len(restored.tool_calls), 2)

    def test_model_changes_field_default(self):
        """ut-ifmt-drift：model_changes 默认空（pi 会话内变更回填处）。"""
        traj = ifmt.IntermediateTrajectory(agent="pi")
        self.assertEqual(traj.model_changes, [])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 运行确认失败**

```bash
python3 -m unittest eval.tests.test_ifmt -v
```

预期：全部 ERROR（`No module named 'eval.ifmt'`）。

- [ ] **Step 3: 最小实现**

`eval/ifmt.py`：

```python
"""统一中间格式：四端轨迹的判分唯一入口数据契约（eval-trajectory-scoring R1）。

模型标识一律 transcript 实测回读（非启动参数）；settings_snapshot 携带
fixture .claude/settings.json 受管区块快照，供 deny 双分类 gate 判归属。
"""
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class ToolCall:
    index: int
    tool: str
    raw_tool: str
    args_digest: str
    is_error: bool
    ts: Optional[str] = None


@dataclass
class Denial:
    at_index: int
    tool: str
    reason: str
    raw: dict


@dataclass
class WriteEvent:
    at_index: int
    path: str


@dataclass
class IntermediateTrajectory:
    agent: str
    model_readback: str = ""
    model_changes: list = field(default_factory=list)
    cli_version: Optional[str] = None
    tool_calls: list = field(default_factory=list)
    denials: list = field(default_factory=list)
    writes: list = field(default_factory=list)
    final_text: str = ""
    started_at: str = ""
    duration_s: float = 0.0
    settings_snapshot: dict = field(default_factory=dict)
    source_path: str = ""

    def to_dict(self) -> dict:
        return {
            "agent": self.agent,
            "model_readback": self.model_readback,
            "model_changes": list(self.model_changes),
            "cli_version": self.cli_version,
            "tool_calls": [vars(c) for c in self.tool_calls],
            "denials": [vars(d) for d in self.denials],
            "writes": [vars(w) for w in self.writes],
            "final_text": self.final_text,
            "started_at": self.started_at,
            "duration_s": self.duration_s,
            "settings_snapshot": self.settings_snapshot,
            "source_path": self.source_path,
        }

    @classmethod
    def from_dict(cls, doc: dict) -> "IntermediateTrajectory":
        traj = cls(agent=doc.get("agent", ""))
        traj.model_readback = doc.get("model_readback", "")
        traj.model_changes = list(doc.get("model_changes", []))
        traj.cli_version = doc.get("cli_version")
        traj.tool_calls = [ToolCall(**c) for c in doc.get("tool_calls", [])]
        traj.denials = [Denial(**d) for d in doc.get("denials", [])]
        traj.writes = [WriteEvent(**w) for w in doc.get("writes", [])]
        traj.final_text = doc.get("final_text", "")
        traj.started_at = doc.get("started_at", "")
        traj.duration_s = float(doc.get("duration_s", 0.0))
        traj.settings_snapshot = dict(doc.get("settings_snapshot", {}))
        traj.source_path = doc.get("source_path", "")
        return traj


def dump(traj: IntermediateTrajectory, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(traj.to_dict(), ensure_ascii=False, indent=2),
                    encoding="utf-8")


def load(path: Path) -> IntermediateTrajectory:
    return IntermediateTrajectory.from_dict(
        json.loads(path.read_text(encoding="utf-8")))
```

- [ ] **Step 4: 运行测试确认通过**

```bash
python3 -m unittest eval.tests.test_ifmt -v
```

预期：3 个用例全部 PASS。

- [ ] **Step 5: 提交建议**

```bash
git add eval/ifmt.py eval/tests/test_ifmt.py
git commit -m "feat(eval): 统一中间格式——模型回读/拒绝/写事件/受管区块快照契约"
```

> 产物自动提交开关当前=关闭：跳过 `git commit`，只报告上述两个新增路径，等待维护者确认。

### Task 6: 适配器协议 + claude 适配器（stream-json / session jsonl）

**Files:**
- Create: `eval/adapters/__init__.py`、`eval/adapters/base.py`、`eval/adapters/claude.py`
- Create: `eval/transcripts/claude/golden-1.jsonl`（罐头轨迹，含 deny→改道样本）
- Test: `eval/tests/test_adapters_claude.py`

**Interfaces:**
- Consumes: `ifmt.*`（Task 5）。
- Produces:
  - `base.AgentAdapter`（ABC）：属性 `name: str`、`capture: str`；方法 `parse_stream(self, lines: Iterable[str]) -> ifmt.IntermediateTrajectory`、`parse_file(self, path: Path) -> ifmt.IntermediateTrajectory`（回填 `source_path`）、`find_latest_session(self, home: Path, since_ts: float) -> Optional[Path]`（stdout 捕获端返回 None）
  - `base.normalize_tool(agent: str, raw_tool: str) -> str`——四端工具名归一（codex `exec_command`/`exec`/`shell`→`Bash`、`apply_patch`→`Edit`；pi `bash`→`Bash`、`read`→`Read`、`write`→`Write`、`edit`→`Edit`、`grep`→`Grep`；claude/kimi 保留原名）
  - `base.args_digest(tool: str, inp: dict) -> str`
  - `adapters.get_adapter(name: str) -> base.AgentAdapter`、`adapters.AGENTS == ("claude", "codex", "pi", "kimi")`
  - `claude.ClaudeAdapter`：`DENIAL_MARKERS: tuple[str, ...]`（forensics 取证后校准；初始启发式）
  - Task 7/8/17 消费。

**claude 解析规则（代码级；字段结构为本机 362 个真实 session 实测锚点，oracle 评审 §2-a/风险 2）**：

| 输入行（JSON） | 提取 |
|---|---|
| `{"type":"assistant","message":{"model":M,"content":[{"type":"tool_use","name":N,"input":I,"id":T}]}}` | `ToolCall`（index 自增；`message.model` 首现→`model_readback`）；`N∈{Edit,Write,NotebookEdit}` 且 `I.file_path` → `WriteEvent` |
| `{"type":"assistant","message":{"content":[{"type":"text","text":T}]}}` | 累积 assistant 文本 |
| `{"type":"user","message":{"content":[{"type":"tool_result","tool_use_id":T,"is_error":E,"content":C}]}}` | `E` → 回填对应 `ToolCall.is_error`；`E` 且 `C` 含 DENIAL_MARKERS → `Denial` |
| `{"type":"result","subtype":S,"duration_ms":D,"result":R}` | `duration_s=D/1000`；`R` 并入 `final_text` |
| 行级 `"version":V`（session 文件）或 `{"type":"system","subtype":"init",...}` | `cli_version=V` |

- [ ] **Step 1: 写失败测试**

```python
"""eval/tests/test_adapters_claude.py —— claude stream-json 适配（tasks 2.1）。"""
import json
import unittest
from pathlib import Path

from eval.adapters import get_adapter
from eval.adapters import base

GOLDEN = Path(__file__).resolve().parents[1] / "transcripts" / "claude" / "golden-1.jsonl"


class TestClaudeAdapter(unittest.TestCase):
    def setUp(self):
        self.adapter = get_adapter("claude")

    def test_registry(self):
        """ut-adv-registry：注册表暴露四端且 capture 口径正确。"""
        from eval.adapters import AGENTS
        self.assertEqual(AGENTS, ("claude", "codex", "pi", "kimi"))
        self.assertEqual(self.adapter.name, "claude")
        self.assertEqual(self.adapter.capture, "stdout")

    def test_parse_golden(self):
        """ut-adv-claude-golden：罐头轨迹解析出模型/工具/改道/终文本。"""
        traj = self.adapter.parse_file(GOLDEN)
        self.assertEqual(traj.agent, "claude")
        self.assertEqual(traj.model_readback, "glm-5.3")
        tools = [c.tool for c in traj.tool_calls]
        self.assertEqual(tools, ["Bash", "mcp__codegraph__codegraph_explore"])
        self.assertTrue(traj.tool_calls[0].is_error)
        self.assertEqual(traj.denials[0].tool, "Bash")
        self.assertIn("调用链", traj.final_text)
        self.assertEqual(traj.cli_version, "2.1.233")
        self.assertGreater(traj.duration_s, 0)
        self.assertEqual(len(traj.denials), 1)

    def test_normalize_tool(self):
        """ut-adv-normalize：工具名归一口径。"""
        self.assertEqual(base.normalize_tool("codex", "exec_command"), "Bash")
        self.assertEqual(base.normalize_tool("codex", "exec"), "Bash")
        self.assertEqual(base.normalize_tool("codex", "apply_patch"), "Edit")
        self.assertEqual(base.normalize_tool("pi", "bash"), "Bash")
        self.assertEqual(base.normalize_tool("pi", "read"), "Read")
        self.assertEqual(base.normalize_tool("claude", "mcp__time__get_time"),
                         "mcp__time__get_time")

    def test_reroute_window_ordering(self):
        """ut-adv-order：时间序 index 严格递增（改道窗口判定的基础）。"""
        traj = self.adapter.parse_file(GOLDEN)
        indexes = [c.index for c in traj.tool_calls]
        self.assertEqual(indexes, sorted(indexes))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 运行确认失败**

```bash
python3 -m unittest eval.tests.test_adapters_claude -v
```

预期：全部 ERROR（`No module named 'eval.adapters'`）。

- [ ] **Step 3.1: 罐头轨迹入库 `eval/transcripts/claude/golden-1.jsonl`**

```jsonl
{"type":"system","subtype":"init","session_id":"golden-1","model":"glm-5.3","version":"2.1.233"}
{"type":"assistant","message":{"model":"glm-5.3","content":[{"type":"text","text":"我先看看结构"}]}}
{"type":"assistant","message":{"model":"glm-5.3","content":[{"type":"tool_use","id":"t0","name":"Bash","input":{"command":"ls -R src"}}]}}
{"type":"user","message":{"content":[{"type":"tool_result","tool_use_id":"t0","is_error":true,"content":"Claude requested permissions to use Bash but the request was denied by settings"}]}}
{"type":"assistant","message":{"model":"glm-5.3","content":[{"type":"text","text":"被拦了，改用 codegraph"}]}}
{"type":"assistant","message":{"model":"glm-5.3","content":[{"type":"tool_use","id":"t1","name":"mcp__codegraph__codegraph_explore","input":{"query":"orders 调用链"}}]}}
{"type":"user","message":{"content":[{"type":"tool_result","tool_use_id":"t1","content":"entry→service→repo"}]}}
{"type":"assistant","message":{"model":"glm-5.3","content":[{"type":"text","text":"调用链：entry→service→repo，已梳理完成"}]}}
{"type":"result","subtype":"success","duration_ms":15000,"result":"调用链：entry→service→repo，已梳理完成"}
```

- [ ] **Step 3.2: 最小实现**

`eval/adapters/base.py`：

```python
"""适配器协议与跨端工具名归一（eval-trajectory-scoring R1：断言器只吃中间格式）。"""
import abc
from pathlib import Path
from typing import Iterable, Optional

from eval import ifmt

AGENTS = ("claude", "codex", "pi", "kimi")

TOOL_ALIASES = {
    "codex": {"exec_command": "Bash", "exec": "Bash", "shell": "Bash",
              "apply_patch": "Edit", "view": "Read", "read_file": "Read"},
    "pi": {"bash": "Bash", "read": "Read", "write": "Write",
           "edit": "Edit", "grep": "Grep", "glob": "Glob"},
    "claude": {},
    "kimi": {},
}


def normalize_tool(agent: str, raw_tool: str) -> str:
    return TOOL_ALIASES.get(agent, {}).get(raw_tool, raw_tool)


def args_digest(tool: str, inp: dict) -> str:
    """参数摘要：Bash→命令头前 3 词；文件写入→路径；其余→入参键名（漫游检测用）。"""
    if not isinstance(inp, dict):
        return ""
    if tool == "Bash" and isinstance(inp.get("command"), str):
        return " ".join(inp["command"].split()[:3])
    if tool in ("Edit", "Write") and isinstance(inp.get("file_path"), str):
        return inp["file_path"]
    return ",".join(sorted(map(str, inp.keys()))[:5])


class AgentAdapter(abc.ABC):
    """四端适配器协议：parse_stream 只消费文本行，产出中间格式。"""

    name: str = ""
    capture: str = "stdout"  # stdout | session

    @abc.abstractmethod
    def parse_stream(self, lines: Iterable[str]) -> ifmt.IntermediateTrajectory:
        ...

    def parse_file(self, path: Path) -> ifmt.IntermediateTrajectory:
        traj = self.parse_stream(
            line for line in path.read_text(encoding="utf-8",
                                            errors="replace").splitlines() if line.strip())
        traj.source_path = str(path)
        return traj

    def find_latest_session(self, home: Path, since_ts: float) -> Optional[Path]:
        return None  # stdout 捕获端无需定位 session 文件
```

`eval/adapters/claude.py`：

```python
"""claude 适配器：stream-json（-p stdout）与 session jsonl 同构解析。

字段锚点（本机 362 个真实 session 实测，2026-09-02）：
assistant.message.model（模型回读）/ content[].tool_use / user.tool_result.is_error
/ result.duration_ms / 行级 version（cli 版本）。
DENIAL_MARKERS 为启发式初值——本机 242 个真实会话 permission_denial 出现 0 次，
Task 10 forensics 取证真实字段结构后校准本常量并以离线用例锁定。
"""
import json
from pathlib import Path
from typing import Iterable, Optional

from eval import ifmt
from eval.adapters import base

DENIAL_MARKERS = ("permission", "denied", "not allowed", "权限", "拒绝")


def _tool_result_text(content) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict) and isinstance(item.get("text"), str):
                parts.append(item["text"])
        return "\n".join(parts)
    return ""


class ClaudeAdapter(base.AgentAdapter):
    name = "claude"
    capture = "stdout"

    def parse_stream(self, lines: Iterable[str]):
        traj = ifmt.IntermediateTrajectory(agent=self.name)
        pending: dict = {}
        texts: list = []
        seq = 0
        for raw in lines:
            try:
                d = json.loads(raw)
            except ValueError:
                continue
            if not isinstance(d, dict):
                continue
            if traj.cli_version is None and isinstance(d.get("version"), str):
                traj.cli_version = d["version"]
            if not traj.started_at and isinstance(d.get("timestamp"), str):
                traj.started_at = d["timestamp"]
            dtype = d.get("type")
            message = d.get("message")
            if dtype == "assistant" and isinstance(message, dict):
                if not traj.model_readback and isinstance(message.get("model"), str):
                    traj.model_readback = message["model"]
                content = message.get("content")
                if isinstance(content, list):
                    for item in content:
                        if not isinstance(item, dict):
                            continue
                        if item.get("type") == "tool_use":
                            raw_name = str(item.get("name") or "")
                            tool = base.normalize_tool(self.name, raw_name)
                            inp = item.get("input") if isinstance(item.get("input"), dict) else {}
                            traj.tool_calls.append(ifmt.ToolCall(
                                index=seq, tool=tool, raw_tool=raw_name,
                                args_digest=base.args_digest(tool, inp), is_error=False))
                            if tool in ("Edit", "Write", "NotebookEdit") \
                                    and isinstance(inp.get("file_path"), str):
                                traj.writes.append(ifmt.WriteEvent(
                                    at_index=seq, path=inp["file_path"]))
                            pending[str(item.get("id"))] = seq
                            seq += 1
                        elif item.get("type") == "text" and isinstance(item.get("text"), str):
                            texts.append(item["text"])
            elif dtype == "user" and isinstance(message, dict):
                content = message.get("content")
                if isinstance(content, list):
                    for item in content:
                        if not isinstance(item, dict) or item.get("type") != "tool_result":
                            continue
                        idx = pending.get(str(item.get("tool_use_id")))
                        body = _tool_result_text(item.get("content"))
                        is_err = bool(item.get("is_error"))
                        if idx is not None and is_err:
                            for call in traj.tool_calls:
                                if call.index == idx:
                                    call.is_error = True
                                    break
                            low = body.lower()
                            if any(marker in low for marker in DENIAL_MARKERS):
                                tool = next((c.tool for c in traj.tool_calls
                                             if c.index == idx), "")
                                traj.denials.append(ifmt.Denial(
                                    at_index=idx, tool=tool, reason=body[:200],
                                    raw={"tool_use_id": item.get("tool_use_id"),
                                         "content": body[:400]}))
            elif dtype == "result":
                if isinstance(d.get("duration_ms"), (int, float)):
                    traj.duration_s = d["duration_ms"] / 1000.0
                if isinstance(d.get("result"), str):
                    texts.append(d["result"])
        traj.final_text = "\n".join(texts)
        return traj
```

`eval/adapters/__init__.py`：

```python
"""适配器注册表：新增端=新增适配器文件+在此注册（断言器与探针零改动）。"""
from eval.adapters.base import AGENTS, AgentAdapter, args_digest, normalize_tool


def get_adapter(name: str) -> AgentAdapter:
    if name == "claude":
        from eval.adapters.claude import ClaudeAdapter
        return ClaudeAdapter()
    if name == "codex":
        from eval.adapters.codex import CodexAdapter
        return CodexAdapter()
    if name == "pi":
        from eval.adapters.pi import PiAdapter
        return PiAdapter()
    if name == "kimi":
        from eval.adapters.kimi import KimiAdapter
        return KimiAdapter()
    raise ValueError(f"未知端：{name}")
```

- [ ] **Step 4: 运行测试确认通过**

```bash
python3 -m unittest eval.tests.test_adapters_claude -v
```

预期：4 个用例全部 PASS。

- [ ] **Step 5: 提交建议**

```bash
git add eval/adapters/ eval/transcripts/claude/ eval/tests/test_adapters_claude.py
git commit -m "feat(eval): 适配器协议与 claude 适配器（stream-json 解析 + deny 启发式锚点）"
```

> 产物自动提交开关当前=关闭：跳过 `git commit`，只报告上述新增路径，等待维护者确认。

---
### Task 7: codex / pi 适配器

**Files:**
- Create: `eval/adapters/codex.py`、`eval/adapters/pi.py`
- Create: `eval/transcripts/codex/golden-1.jsonl`、`eval/transcripts/pi/golden-1.jsonl`
- Test: `eval/tests/test_adapters_codex_pi.py`

**Interfaces:**
- Consumes: `base.AgentAdapter`/`base.normalize_tool`/`base.args_digest`（Task 6）、`ifmt.*`（Task 5）。
- Produces:
  - `CodexAdapter`（`name="codex"`、`capture="stdout"`）：解析规则见下表；`TOOL_PAYLOADS = ("function_call", "custom_tool_call", "local_shell_call")`（审计：同端跨会话工具名变体 `function_call:exec_command`（1001 次）与 `custom_tool_call:exec`（36 次）并存，归一必须覆盖两形态）
  - `PiAdapter`（`name="pi"`、`capture="session"`）：`find_latest_session(home, since_ts)` 定位 `~/.pi/agent/sessions/**/run-*/session.jsonl` 最新文件；`model_change.modelId` 非空 → `traj.model_changes`（guards 判 run 作废）
  - Task 8/17/18 消费。

**codex 解析规则（代码级；锚点为本机 1143 个 rollout 实测）：**

| 输入行 | 提取 |
|---|---|
| `{"timestamp":T,"type":"session_meta","payload":{...,"model":M}}` | `started_at=T`；`model_readback` 候选 |
| `{"type":"turn_context","payload":{"model":M,...}}` | `model_readback=M`（后值覆盖——turn 级最新口径） |
| `{"type":"response_item","payload":{"type":"function_call"/"custom_tool_call","name":N,"arguments":A,"call_id":C}}` | `ToolCall`：`normalize_tool("codex",N)`；A 为 JSON 字符串→解析取 `command`（list 取 join 后剥 `bash -lc ` 前缀、str 取原文全文）作 `args_digest`（golden：`["bash","-lc","ls src"]`→`ls src`；变体用例：`"find . -name x"`→原样） |
| `{"type":"response_item","payload":{"type":"function_call_output","call_id":C,"output":O}}` | O 为 JSON 字符串→解析后 `error` 真值或 `output` 文本含 `"error"` → 回填 `is_error` |
| `{"type":"event_msg","payload":{"type":"error","message":E}}` | 记入 `stderr_note`（infra 归因参考，经 `raw` 旁路存 `traj.settings_snapshot["_infra_errors"]`） |
| 首尾 `timestamp` 差 | `duration_s`；`cli_version=None`（rollout 无版本字段，版本锁经 `--version` 核验） |

**pi 解析规则（代码级；锚点为本机 4857 个 session 实测）：**

| 输入行 | 提取 |
|---|---|
| `{"type":"session","cwd":W,"id":I,"timestamp":T,"version":V}` | `started_at=T`；`cli_version=V` |
| `{"type":"model_change","modelId":M,"provider":P,...}` | `model_changes.append(M)`；首个亦作 `model_readback` 候选（pi 会话内变更→run 作废，readback 仅作报告单列） |
| `{"type":"message","message":{"role":"assistant","content":[{"type":"toolCall","id":C,"name":N,"arguments":A}]}}` | `ToolCall`：`normalize_tool("pi",N)`；A 为 dict→`args_digest` |
| `{"type":"message","message":{"role":"toolResult","content":[{"type":"text","text":X}]}}` | 顺序配对最近未闭合 toolCall；X 含 error/permission 标记 → `is_error`/`Denial`（kimi/claude 同语义标记表） |
| `{"type":"message","message":{"role":"assistant","content":[{"type":"text","text":X}]}}` | 累积 `final_text` |

- [ ] **Step 1: 写失败测试**

```python
"""eval/tests/test_adapters_codex_pi.py —— codex rollout 与 pi session 解析（tasks 2.2）。"""
import unittest
from pathlib import Path

from eval.adapters import get_adapter

TRANS = Path(__file__).resolve().parents[1] / "transcripts"


class TestCodexAdapter(unittest.TestCase):
    def setUp(self):
        self.adapter = get_adapter("codex")

    def test_parse_golden(self):
        """ut-adv-codex-golden：模型回读/工具归一/命令头摘要。"""
        traj = self.adapter.parse_file(TRANS / "codex" / "golden-1.jsonl")
        self.assertEqual(traj.model_readback, "gpt-5.4")
        tools = [c.tool for c in traj.tool_calls]
        self.assertEqual(tools, ["Bash", "Read"])
        self.assertEqual(traj.tool_calls[0].args_digest, "ls src")
        self.assertGreater(traj.duration_s, 0)
        self.assertTrue(traj.started_at.startswith("2026-"))

    def test_tool_name_variance_normalized(self):
        """ut-adv-codex-variance：custom_tool_call 形态同样归一（跨会话变体防线）。"""
        lines = [
            '{"timestamp":"2026-09-02T12:00:00Z","type":"turn_context","payload":{"model":"gpt-5.4"}}',
            '{"timestamp":"2026-09-02T12:00:01Z","type":"response_item","payload":'
            '{"type":"custom_tool_call","name":"exec","arguments":"{\\"command\\":\\"find . -name x\\"}"}}',
        ]
        traj = self.adapter.parse_stream(lines)
        self.assertEqual(traj.tool_calls[0].tool, "Bash")
        self.assertEqual(traj.tool_calls[0].args_digest, "find . -name x")

    def test_output_error_marks_is_error(self):
        """ut-adv-codex-err：function_call_output 的 error 字段回填 is_error。"""
        lines = [
            '{"timestamp":"2026-09-02T12:00:00Z","type":"response_item","payload":'
            '{"type":"function_call","name":"exec_command","arguments":"{}","call_id":"c1"}}',
            '{"timestamp":"2026-09-02T12:00:01Z","type":"response_item","payload":'
            '{"type":"function_call_output","call_id":"c1","output":"{\\"error\\":\\"denied\\"}"}}',
        ]
        traj = self.adapter.parse_stream(lines)
        self.assertTrue(traj.tool_calls[0].is_error)


class TestPiAdapter(unittest.TestCase):
    def setUp(self):
        self.adapter = get_adapter("pi")

    def test_parse_golden(self):
        """ut-adv-pi-golden：session 版本/工具归一/终文本。"""
        traj = self.adapter.parse_file(TRANS / "pi" / "golden-1.jsonl")
        self.assertEqual(traj.agent, "pi")
        self.assertEqual(traj.cli_version, "0.5.2")
        tools = [c.tool for c in traj.tool_calls]
        self.assertEqual(tools, ["Bash", "Read"])
        self.assertIn("完成", traj.final_text)

    def test_model_change_records_drift(self):
        """ut-adv-pi-drift：会话内 model_change 记入 model_changes（run 作废依据）。"""
        lines = [
            '{"type":"session","cwd":"/fx","id":"s1","timestamp":"2026-09-02T12:00:00Z","version":"0.5.2"}',
            '{"type":"model_change","modelId":"glm-5.3","provider":"zai","id":"m1",'
            '"parentId":null,"timestamp":"2026-09-02T12:00:01Z"}',
            '{"type":"message","id":"a1","message":{"role":"assistant",'
            '"content":[{"type":"text","text":"ok"}]}}',
        ]
        traj = self.adapter.parse_stream(lines)
        self.assertEqual(traj.model_changes, ["glm-5.3"])
        self.assertEqual(traj.model_readback, "glm-5.3")

    def test_capture_is_session(self):
        """ut-adv-pi-capture：pi 为 session 捕获端。"""
        self.assertEqual(self.adapter.capture, "session")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 运行确认失败**

```bash
python3 -m unittest eval.tests.test_adapters_codex_pi -v
```

预期：全部 FAIL/ERROR（`cannot import name 'CodexAdapter'`——注册表已引用但模块未建）。

- [ ] **Step 3.1: 罐头轨迹入库**

`eval/transcripts/codex/golden-1.jsonl`：

```jsonl
{"timestamp":"2026-09-02T12:00:00.000Z","type":"session_meta","payload":{"session_id":"g1","cwd":"/fixture","model":"gpt-5.4"}}
{"timestamp":"2026-09-02T12:00:00.100Z","type":"turn_context","payload":{"model":"gpt-5.4","cwd":"/fixture"}}
{"timestamp":"2026-09-02T12:00:01.000Z","type":"response_item","payload":{"type":"function_call","name":"exec_command","arguments":"{\"command\":[\"bash\",\"-lc\",\"ls src\"]}","call_id":"c1"}}
{"timestamp":"2026-09-02T12:00:02.000Z","type":"response_item","payload":{"type":"function_call_output","call_id":"c1","output":"{\"output\":\"orders/ billing/\",\"error\":null}"}}
{"timestamp":"2026-09-02T12:00:03.000Z","type":"response_item","payload":{"type":"function_call","name":"view","arguments":"{\"file_path\":\"src/orders/entry.py\"}","call_id":"c2"}}
{"timestamp":"2026-09-02T12:00:04.000Z","type":"response_item","payload":{"type":"function_call_output","call_id":"c2","output":"{\"output\":\"def main(): ...\"}"}}
```

`eval/transcripts/pi/golden-1.jsonl`：

```jsonl
{"type":"session","cwd":"/fixture","id":"s1","timestamp":"2026-09-02T12:00:00Z","version":"0.5.2"}
{"type":"message","id":"m1","message":{"role":"user","content":[{"type":"text","text":"Task: 梳理调用链"}]}}
{"type":"message","id":"m2","message":{"role":"assistant","content":[{"type":"toolCall","id":"call_1","name":"bash","arguments":{"command":"ls src"}}]}}
{"type":"message","id":"m3","message":{"role":"toolResult","content":[{"type":"text","text":"orders/"}]}}
{"type":"message","id":"m4","message":{"role":"assistant","content":[{"type":"toolCall","id":"call_2","name":"read","arguments":{"path":"src/orders/entry.py"}}]}}
{"type":"message","id":"m5","message":{"role":"toolResult","content":[{"type":"text","text":"def main(): handle({})"}]}}
{"type":"message","id":"m6","message":{"role":"assistant","content":[{"type":"text","text":"调用链：entry→service→repo，完成"}]}}
```

- [ ] **Step 3.2: 最小实现**

`eval/adapters/codex.py`：

```python
"""codex 适配器：rollout jsonl（exec --json stdout 与 rollout 文件同构）。

字段锚点（本机 1143 个 rollout 实测，2026-09-02）：session_meta/turn_context
的 payload.model；response_item 的 function_call|custom_tool_call（工具名跨会话
变体并存，经 base.normalize_tool 归一）；function_call_output.output JSON 的
error 字段。
"""
import json
from datetime import datetime
from pathlib import Path
from typing import Iterable, Optional

from eval import ifmt
from eval.adapters import base

TOOL_PAYLOADS = ("function_call", "custom_tool_call", "local_shell_call")


def _parse_json_maybe(text):
    if isinstance(text, str):
        try:
            return json.loads(text)
        except ValueError:
            return None
    return text if isinstance(text, dict) else None


def _ts(text) -> Optional[float]:
    if not isinstance(text, str):  # 无 timestamp 字段的行（如 mock 轨迹）不计时长
        return None
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).timestamp()
    except (ValueError, TypeError):
        return None


class CodexAdapter(base.AgentAdapter):
    name = "codex"
    capture = "stdout"

    def parse_stream(self, lines: Iterable[str]):
        traj = ifmt.IntermediateTrajectory(agent=self.name)
        texts: list = []
        seq = 0
        pending: dict = {}
        first_ts = last_ts = None
        for raw in lines:
            try:
                d = json.loads(raw)
            except ValueError:
                continue
            if not isinstance(d, dict):
                continue
            stamp = _ts(d.get("timestamp"))
            if stamp is not None:
                first_ts = first_ts if first_ts is not None else stamp
                last_ts = stamp
                if not traj.started_at:
                    traj.started_at = str(d.get("timestamp"))
            dtype = d.get("type")
            payload = d.get("payload") if isinstance(d.get("payload"), dict) else {}
            if dtype in ("session_meta", "turn_context"):
                model = payload.get("model")
                if isinstance(model, str) and model:
                    traj.model_readback = model  # turn_context 后值覆盖
            elif dtype == "response_item":
                ptype = payload.get("type")
                if ptype in TOOL_PAYLOADS:
                    raw_name = str(payload.get("name") or "")
                    tool = base.normalize_tool(self.name, raw_name)
                    args = _parse_json_maybe(payload.get("arguments")) or {}
                    command = args.get("command")
                    if isinstance(command, list):
                        # list 形态 join 后剥 "bash -lc " 前缀（golden：["bash","-lc","ls src"]→"ls src"）
                        joined = " ".join(str(x) for x in command)
                        if joined.startswith("bash -lc "):
                            joined = joined[len("bash -lc "):]
                        digest = joined[:120]
                    elif isinstance(command, str):
                        digest = command[:120]  # str 形态取原文（"find . -name x" 原样）
                    elif isinstance(args.get("file_path"), str):
                        digest = args["file_path"]
                    else:
                        digest = base.args_digest(tool, args)
                    call_id = str(payload.get("call_id"))
                    traj.tool_calls.append(ifmt.ToolCall(
                        index=seq, tool=tool, raw_tool=raw_name,
                        args_digest=digest, is_error=False))
                    if tool in ("Edit", "Write") and isinstance(args.get("file_path"), str):
                        traj.writes.append(ifmt.WriteEvent(at_index=seq,
                                                            path=args["file_path"]))
                    pending[call_id] = seq
                    seq += 1
                elif ptype == "function_call_output":
                    idx = pending.get(str(payload.get("call_id")))
                    out = _parse_json_maybe(payload.get("output")) or {}
                    err = out.get("error")
                    body = out.get("output") if isinstance(out.get("output"), str) else json.dumps(out)
                    if idx is not None and (err or "error" in str(body).lower()):
                        for call in traj.tool_calls:
                            if call.index == idx:
                                call.is_error = True
                                break
                elif ptype == "message" and payload.get("role") == "assistant":
                    for item in payload.get("content") or []:
                        if isinstance(item, dict) and item.get("type") in ("output_text", "text") \
                                and isinstance(item.get("text"), str):
                            texts.append(item["text"])
            elif dtype == "event_msg" and payload.get("type") == "error":
                traj.settings_snapshot.setdefault("_infra_errors", []).append(
                    str(payload.get("message"))[:200])
        if first_ts is not None and last_ts is not None:
            traj.duration_s = max(0.0, last_ts - first_ts)
        traj.final_text = "\n".join(texts)
        return traj

    def find_latest_session(self, home: Path, since_ts: float) -> Optional[Path]:
        best, best_mt = None, -1.0
        for p in home.glob(".codex/sessions/**/rollout-*.jsonl"):
            try:
                mt = p.stat().st_mtime
            except OSError:
                continue
            if mt >= since_ts and mt > best_mt:
                best, best_mt = p, mt
        return best
```

`eval/adapters/pi.py`：

```python
"""pi 适配器：session.jsonl（message/toolCall/toolResult + model_change）。

字段锚点（本机 4857 个 session 实测，2026-09-02）：message.message.content[]
的 toolCall（name 小写、arguments 为 dict）；role=toolResult 的 text 结果按
顺序配对；顶层 type=model_change 的 modelId（会话内变更→run 作废）。
"""
import json
from pathlib import Path
from typing import Iterable, Optional

from eval import ifmt
from eval.adapters import base

ERROR_MARKERS = ("error", "failed", "permission", "denied", "错误", "拒绝")


class PiAdapter(base.AgentAdapter):
    name = "pi"
    capture = "session"

    def parse_stream(self, lines: Iterable[str]):
        traj = ifmt.IntermediateTrajectory(agent=self.name)
        texts: list = []
        seq = 0
        pending: list = []
        for raw in lines:
            try:
                d = json.loads(raw)
            except ValueError:
                continue
            if not isinstance(d, dict):
                continue
        # 逐行分派
            dtype = d.get("type")
            if dtype == "session":
                if not traj.started_at and isinstance(d.get("timestamp"), str):
                    traj.started_at = d["timestamp"]
                if traj.cli_version is None and isinstance(d.get("version"), str):
                    traj.cli_version = d["version"]
            elif dtype == "model_change":
                model_id = d.get("modelId")
                if isinstance(model_id, str) and model_id:
                    traj.model_changes.append(model_id)
                    if not traj.model_readback:
                        traj.model_readback = model_id
            elif dtype == "message" and isinstance(d.get("message"), dict):
                message = d["message"]
                role = message.get("role")
                content = message.get("content")
                if not isinstance(content, list):
                    continue
                if role == "assistant":
                    for item in content:
                        if not isinstance(item, dict):
                            continue
                        if item.get("type") == "toolCall":
                            raw_name = str(item.get("name") or "")
                            tool = base.normalize_tool(self.name, raw_name)
                            args = item.get("arguments") if isinstance(
                                item.get("arguments"), dict) else {}
                            traj.tool_calls.append(ifmt.ToolCall(
                                index=seq, tool=tool, raw_tool=raw_name,
                                args_digest=base.args_digest(tool, args), is_error=False))
                            if tool in ("Edit", "Write") and isinstance(args.get("path"), str):
                                traj.writes.append(ifmt.WriteEvent(
                                    at_index=seq, path=args["path"]))
                            pending.append(seq)
                            seq += 1
                        elif item.get("type") == "text" and isinstance(item.get("text"), str):
                            texts.append(item["text"])
                elif role == "toolResult":
                    body = "\n".join(
                        item.get("text", "") for item in content
                        if isinstance(item, dict) and isinstance(item.get("text"), str))
                    if pending:
                        idx = pending.pop(0)
                        low = body.lower()
                        if any(marker in low for marker in ERROR_MARKERS):
                            for call in traj.tool_calls:
                                if call.index == idx:
                                    call.is_error = True
                                    traj.denials.append(ifmt.Denial(
                                        at_index=idx, tool=call.tool,
                                        reason=body[:200],
                                        raw={"content": body[:400]}))
                                    break
        traj.final_text = "\n".join(texts)
        return traj

    def find_latest_session(self, home: Path, since_ts: float) -> Optional[Path]:
        best, best_mt = None, -1.0
        for p in home.glob(".pi/agent/sessions/**/run-*/session.jsonl"):
            try:
                mt = p.stat().st_mtime
            except OSError:
                continue
            if mt >= since_ts and mt > best_mt:
                best, best_mt = p, mt
        return best
```

- [ ] **Step 4: 运行测试确认通过**

```bash
python3 -m unittest eval.tests.test_adapters_codex_pi -v
```

预期：6 个用例全部 PASS。

- [ ] **Step 5: 提交建议**

```bash
git add eval/adapters/codex.py eval/adapters/pi.py eval/transcripts/codex/ eval/transcripts/pi/ eval/tests/test_adapters_codex_pi.py
git commit -m "feat(eval): codex rollout 与 pi session 适配器（工具名变体归一、model_change 作废锚点）"
```

> 产物自动提交开关当前=关闭：跳过 `git commit`，只报告上述新增路径，等待维护者确认。

### Task 8: kimi 适配器 + 先行单端验证

**Files:**
- Create: `eval/adapters/kimi.py`、`eval/runner/verify_kimi.py`
- Create: `eval/transcripts/kimi/golden-1.jsonl`
- Test: `eval/tests/test_adapters_kimi.py`

**Interfaces:**
- Consumes: `base.AgentAdapter`（Task 6）、`proc.run_cli`/`cli_version_check`（Task 3）、`gen.make_fixture`（Task 1）、`stage1.run_stage1`（Task 3）。
- Produces:
  - `KimiAdapter`（`name="kimi"`、`capture="session"`）：`find_latest_session(home, since_ts)` 定位 `~/.kimi-code/sessions/**/agents/*/wire.jsonl`
  - `verify_kimi.verify(repo_root: Path, base_dir: Path, pins: dict) -> int`——单端验证：真实 `kimi -p` 一次探针 + 一次阶段一，检查模型回读/工具解析/产物断言，打印清单，退出码 0/1；通过后维护者把 `eval/config/agents.json` 的 `kimi.enabled` 置 `true` 入矩阵（spec：Kimi 无公开 headless 文档，MUST 先行单端验证）
  - Task 15 消费（enabled 门）。

**kimi 解析规则（代码级；锚点为本机 313MB wire.jsonl 实测）：**

| 输入行 | 提取 |
|---|---|
| `{"type":"metadata","protocol_version":"1.4",...}` | `cli_version="wire/1.4"`（协议版本代理口径） |
| `{"type":"config.update","modelAlias":M,...}` | `model_readback` 候选 |
| `{"type":"usage.record","model":M,...}` | `model_readback=M`（usage 级，后值覆盖） |
| `{"type":"context.append_loop_event","event":{"type":"tool.call","toolCallId":C,"name":N,"args":A}}` | `ToolCall`（normalize_tool 保留原名：Read/Write/Edit/Grep/Glob/Bash 已实测规范） |
| `{"type":"context.append_loop_event","event":{"type":"tool.result","toolCallId":C,"result":R}}` | `R.error` 真值或 `R.output` 含 error 标记 → `is_error`；含 permission/denied → `Denial` |
| `{"type":"context.append_message","message":{"role":"assistant","content":[{"type":"text","text":X}]}}` | 累积 `final_text` |

- [ ] **Step 1: 写失败测试**

```python
"""eval/tests/test_adapters_kimi.py —— kimi wire.jsonl 解析（tasks 2.2）。"""
import unittest
from pathlib import Path

from eval.adapters import get_adapter

GOLDEN = Path(__file__).resolve().parents[1] / "transcripts" / "kimi" / "golden-1.jsonl"


class TestKimiAdapter(unittest.TestCase):
    def setUp(self):
        self.adapter = get_adapter("kimi")

    def test_parse_golden(self):
        """ut-adv-kimi-golden：模型回读取 usage.record（后值覆盖 config.update）。"""
        traj = self.adapter.parse_file(GOLDEN)
        self.assertEqual(traj.model_readback, "kimi-code/kimi-for-coding")
        self.assertEqual(traj.cli_version, "wire/1.4")
        tools = [c.tool for c in traj.tool_calls]
        self.assertEqual(tools, ["Read", "Grep", "Bash"])
        self.assertEqual(traj.tool_calls[1].is_error, True)
        self.assertEqual(traj.denials[0].tool, "Grep")
        self.assertIn("结论", traj.final_text)

    def test_capture_is_session(self):
        """ut-adv-kimi-capture：kimi 为 session 捕获端。"""
        self.assertEqual(self.adapter.capture, "session")

    def test_missing_model_falls_back_alias(self):
        """ut-adv-kimi-alias：无 usage.record 时回退 config.update.modelAlias。"""
        lines = [
            '{"type":"metadata","protocol_version":"1.4","created_at":1}',
            '{"type":"config.update","modelAlias":"kimi-code/kimi-for-coding","time":"1"}',
        ]
        traj = self.adapter.parse_stream(lines)
        self.assertEqual(traj.model_readback, "kimi-code/kimi-for-coding")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 运行确认失败**

```bash
python3 -m unittest eval.tests.test_adapters_kimi -v
```

预期：全部 FAIL/ERROR（`cannot import name 'KimiAdapter'`）。

- [ ] **Step 3.1: 罐头轨迹入库 `eval/transcripts/kimi/golden-1.jsonl`**

```jsonl
{"type":"metadata","protocol_version":"1.4","created_at":1782229467110}
{"type":"config.update","modelAlias":"kimi-code/kimi-for-coding","thinkingLevel":"high","time":"1782229467210"}
{"type":"turn.prompt","prompt":"梳理订单模块调用链","turnId":"0"}
{"type":"context.append_loop_event","event":{"type":"tool.call","toolCallId":"tool_1","name":"Read","args":{"path":"src/orders/entry.py"},"uuid":"u1","turnId":"0","step":"1"}}
{"type":"context.append_loop_event","event":{"type":"tool.result","toolCallId":"tool_1","result":{"output":"def main(): ..."},"uuid":"u2"}}
{"type":"context.append_loop_event","event":{"type":"tool.call","toolCallId":"tool_2","name":"Grep","args":{"pattern":"orders"},"uuid":"u3","turnId":"0","step":"1"}}
{"type":"context.append_loop_event","event":{"type":"tool.result","toolCallId":"tool_2","result":{"output":"Grep blocked by project settings","error":"permission denied"},"uuid":"u4"}}
{"type":"context.append_loop_event","event":{"type":"tool.call","toolCallId":"tool_3","name":"Bash","args":{"command":"rg orders src"},"uuid":"u5","turnId":"0","step":"2"}}
{"type":"context.append_loop_event","event":{"type":"tool.result","toolCallId":"tool_3","result":{"output":"src/orders/service.py"},"uuid":"u6"}}
{"type":"context.append_message","message":{"role":"assistant","content":[{"type":"text","text":"调用链：entry→service→repo，结论完成"}]}}
{"type":"usage.record","model":"kimi-code/kimi-for-coding","usage":{"inputOther":10,"output":5},"usageScope":"turn","time":"1782229470000"}
```

- [ ] **Step 3.2: 最小实现**

`eval/adapters/kimi.py`：

```python
"""kimi 适配器：wire.jsonl（protocol_version 1.4 实测锚点）。

模型回读：usage.record.model（usage 级，后值覆盖）> config.update.modelAlias。
工具事件：context.append_loop_event.event 的 tool.call / tool.result（按
toolCallId 配对）。Kimi 无公开 headless 文档——本适配器必须先经
eval verify-kimi 单端验证后才允许入矩阵（agents.json enabled 门）。
"""
import json
from pathlib import Path
from typing import Iterable, Optional

from eval import ifmt
from eval.adapters import base

ERROR_MARKERS = ("error", "permission", "denied", "错误", "拒绝")


class KimiAdapter(base.AgentAdapter):
    name = "kimi"
    capture = "session"

    def parse_stream(self, lines: Iterable[str]):
        traj = ifmt.IntermediateTrajectory(agent=self.name)
        texts: list = []
        seq = 0
        pending: dict = {}
        for raw in lines:
            try:
                d = json.loads(raw)
            except ValueError:
                continue
            if not isinstance(d, dict):
                continue
            dtype = d.get("type")
            if dtype == "metadata" and isinstance(d.get("protocol_version"), str):
                traj.cli_version = "wire/" + d["protocol_version"]
            elif dtype == "config.update" and isinstance(d.get("modelAlias"), str):
                if not traj.model_readback:
                    traj.model_readback = d["modelAlias"]
            elif dtype == "usage.record" and isinstance(d.get("model"), str):
                traj.model_readback = d["model"]
            elif dtype == "context.append_loop_event":
                event = d.get("event") if isinstance(d.get("event"), dict) else {}
                etype = event.get("type")
                call_id = str(event.get("toolCallId"))
                if etype == "tool.call":
                    raw_name = str(event.get("name") or "")
                    tool = base.normalize_tool(self.name, raw_name)
                    args = event.get("args") if isinstance(event.get("args"), dict) else {}
                    traj.tool_calls.append(ifmt.ToolCall(
                        index=seq, tool=tool, raw_tool=raw_name,
                        args_digest=base.args_digest(tool, args), is_error=False))
                    if tool in ("Edit", "Write"):
                        path = args.get("path") or args.get("file_path")
                        if isinstance(path, str):
                            traj.writes.append(ifmt.WriteEvent(at_index=seq, path=path))
                    pending[call_id] = seq
                    seq += 1
                elif etype == "tool.result":
                    idx = pending.get(call_id)
                    result = event.get("result") if isinstance(event.get("result"), dict) else {}
                    body = str(result.get("output", ""))
                    err = result.get("error")
                    if idx is not None and (err or "error" in body.lower()):
                        for call in traj.tool_calls:
                            if call.index == idx:
                                call.is_error = True
                                if any(m in body.lower() or m in str(err).lower()
                                       for m in ERROR_MARKERS):
                                    traj.denials.append(ifmt.Denial(
                                        at_index=idx, tool=call.tool,
                                        reason=(str(err) or body)[:200],
                                        raw={"toolCallId": call_id,
                                             "content": body[:400]}))
                                break
            elif dtype == "context.append_message":
                message = d.get("message") if isinstance(d.get("message"), dict) else {}
                if message.get("role") == "assistant" and isinstance(message.get("content"), list):
                    for item in message["content"]:
                        if isinstance(item, dict) and item.get("type") == "text" \
                                and isinstance(item.get("text"), str):
                            texts.append(item["text"])
        traj.final_text = "\n".join(texts)
        return traj

    def find_latest_session(self, home: Path, since_ts: float) -> Optional[Path]:
        best, best_mt = None, -1.0
        for p in home.glob(".kimi-code/sessions/**/agents/*/wire.jsonl"):
            try:
                mt = p.stat().st_mtime
            except OSError:
                continue
            if mt >= since_ts and mt > best_mt:
                best, best_mt = p, mt
        return best
```

`eval/runner/verify_kimi.py`：

```python
"""kimi 适配器先行单端验证（spec：MUST 先行单端验证后再入矩阵）。

真实 CLI（self-hosted）：一次探针式调用 + 一次阶段一安装，检查
模型回读/工具解析/产物断言。通过后维护者将 agents.json 的
kimi.enabled 置 true，夜间矩阵才会包含 kimi。
"""
import json
import tempfile
from pathlib import Path

from eval.adapters import get_adapter
from eval.fixtures import generator as gen
from eval.install import stage1
from eval.runner import proc


def verify(repo_root: Path, base_dir: Path, pins: dict) -> int:
    checks = []
    adapter = get_adapter("kimi")
    with tempfile.TemporaryDirectory(dir=str(base_dir)) as tmp:
        base = Path(tmp)
        fx = gen.make_fixture("fresh", base, repo_root)
        ok_ver, msg = proc.cli_version_check("kimi", pins)
        checks.append(("cli-version", ok_ver, msg))
        out = proc.run_cli("kimi", "请只回答：OK", cwd=fx.root, home=fx.home,
                           pins=pins, timeout_s=300,
                           env_extra={"EVAL_STAGE": "probe", "EVAL_PROBE_ID": "P4"})
        transcript = out.get("transcript_path") or ""
        checks.append(("session-located", bool(transcript), transcript or "未定位到 wire.jsonl"))
        traj_ok, traj_detail = False, ""
        if transcript:
            traj = adapter.parse_file(Path(transcript))
            traj_ok = bool(traj.model_readback)
            traj_detail = (f"model={traj.model_readback} calls={len(traj.tool_calls)} "
                           f"final_text={len(traj.final_text)}ch")
        checks.append(("model-readback", traj_ok, traj_detail))
        report = stage1.run_stage1("kimi", fx, pins, timeout_s=1800)
        checks.append(("stage1", report["ok"],
                       ";".join(a["name"] for a in report["assertions"] if not a["ok"])))
    print("[verify-kimi] 单端验证清单：")
    all_ok = True
    for name, ok, detail in checks:
        print(f"  {'PASS' if ok else 'FAIL'}  {name}: {detail}")
        all_ok = all_ok and ok
    print("[verify-kimi] 全部通过后：将 eval/config/agents.json 的 kimi.enabled 置 true")
    return 0 if all_ok else 1
```

- [ ] **Step 4: 运行测试确认通过**

```bash
python3 -m unittest eval.tests.test_adapters_kimi -v
```

预期：3 个用例全部 PASS（单端验证命令属真实 CLI，留待 Tier-1/self-hosted 执行）。

- [ ] **Step 5: 提交建议**

```bash
git add eval/adapters/kimi.py eval/runner/verify_kimi.py eval/transcripts/kimi/ eval/tests/test_adapters_kimi.py
git commit -m "feat(eval): kimi wire.jsonl 适配器与先行单端验证入口"
```

> 产物自动提交开关当前=关闭：跳过 `git commit`，只报告上述新增路径，等待维护者确认。

---
### Task 9: 确定性断言器（事件/产物/时间序/漫游/归因/排除规则原文）

**Files:**
- Create: `eval/scoring/__init__.py`（空文件）、`eval/scoring/assertor.py`
- Test: `eval/tests/test_assertor.py`

**Interfaces:**
- Consumes: `ifmt.IntermediateTrajectory`（Task 5）、`idem.snapshot_tree`/`diff_trees`（Task 4，P8 快照断言）。
- Produces（探针断言 spec 的解释器；断言 spec 形状由 Task 13 定义）:
  - `asr.tool_used(traj, pattern: str) -> bool`（正则匹配 `tool` 或 `args_digest`；**只看真实工具调用事件——assistant 文本/规则原文永不参与**，即"朗读≠执行"）
  - `asr.tool_absent(traj, pattern: str) -> bool`
  - `asr.bash_heads(traj) -> list[str]`
  - `asr.roam_detect(traj, max_count: int, preferred_pattern: str) -> bool`（`ls`/`find` 头计数超限且未用 preferred → True；审计依据：真实违规形态 ls 114+find 20 vs 裸 grep 仅 4）
  - `asr.zh_ratio(text: str) -> float`（CJK 字符占非空白字符比）
  - `asr.classify_infra(returncode: int, stderr: str, traj_present: bool, timed_out: bool = False) -> Optional[str]`（None=非 infra；命中返回 `infra-fail:<子类>`：cli-crash/login/quota/timeout/transcript-missing）
  - `asr.score_run(run_id: str, probe: dict, traj: ifmt.IntermediateTrajectory, workspace: Optional[Path] = None, fake_mcp_log: Optional[list] = None, pre_snapshot: Optional[dict] = None, returncode: int = 0, stderr: str = "", timed_out: bool = False) -> dict`——返回符合 Task 12 schema 的 result dict（`verdict ∈ {"PASS","FAIL","INFRA_FAIL"}`；deny gate 由内部调用 Task 10 `apply_deny_gate` 后写入；`details` 必含 `deny_gate`/`stderr`/`settings_snapshot` 三键——后者为 fixture 受管 deny 区块快照，spec R2 MUST：deny 归属判定依据随结果 JSON 落盘）
  - Task 15（night runner）、Task 18（离线重跑）消费。

- [ ] **Step 1: 写失败测试**

```python
"""eval/tests/test_assertor.py —— 确定性断言器（tasks 2.4 核心）。"""
import unittest
from pathlib import Path

from eval import ifmt
from eval.scoring import assertor as asr


def _traj(calls, denials=None, final_text="中文结论：完成", writes=None):
    traj = ifmt.IntermediateTrajectory(agent="claude")
    traj.model_readback = "glm-5.3"
    traj.tool_calls = [
        ifmt.ToolCall(index=i, tool=t, raw_tool=t, args_digest=d, is_error=False)
        for i, (t, d) in enumerate(calls)]
    traj.denials = denials or []
    traj.writes = [ifmt.WriteEvent(at_index=i, path=p)
                   for i, p in enumerate(writes or [])]
    traj.final_text = final_text
    traj.settings_snapshot = {"permissions": {"deny": [
        "@@cadence-managed:permission-gate:v1:start@@",
        "Bash(ls:*)", "@@cadence-managed:permission-gate:v1:end@@"]}}
    return traj


P1 = {"id": "P1", "name": "检索", "rule_clause_ids": ["code-reading-coding.md#cadence-tools[0]"],
      "assertions": [
          {"kind": "tool_used", "pattern": "codegraph|ast-grep"},
          {"kind": "tool_absent", "pattern": "^Grep$"},
          {"kind": "no_roam", "max_ls_find": 5, "preferred": "codegraph"}]}


class TestPrimitives(unittest.TestCase):
    def test_tool_used_on_events_not_prose(self):
        """ut-asr-prose：朗读规则原文不算使用（排除规则原文防线）。"""
        traj = _traj([("Grep", "pattern=orders")],
                     final_text="规则要求优先使用 codegraph 与 ast-grep，我已阅读")
        self.assertFalse(asr.tool_used(traj, "codegraph"))
        self.assertTrue(asr.tool_used(traj, "^Grep$"))

    def test_roam_detect_ls_find(self):
        """ut-asr-roam：ls/find 漫游命中（真实违规形态靶子）。"""
        roam = _traj([("Bash", "ls -R src"), ("Bash", "ls src/orders"),
                      ("Bash", "find . -name x"), ("Bash", "find src -type f"),
                      ("Bash", "ls ."), ("Bash", "find . -maxdepth 1"),
                      ("Read", "file_path=src/orders/entry.py")])
        self.assertTrue(asr.roam_detect(roam, max_count=5, preferred_pattern="codegraph"))
        ok = _traj([("mcp__codegraph__codegraph_explore", "query=orders")])
        self.assertFalse(asr.roam_detect(ok, max_count=5, preferred_pattern="codegraph"))

    def test_zh_ratio(self):
        """ut-asr-zh：中文占比口径。"""
        self.assertGreaterEqual(asr.zh_ratio("这是中文结论 done"), 0.6)
        self.assertLess(asr.zh_ratio("english only text"), 0.6)

    def test_classify_infra(self):
        """ut-asr-infra：基础设施失败归因分类。"""
        self.assertEqual(asr.classify_infra(0, "", traj_present=False),
                         "infra-fail:transcript-missing")
        self.assertEqual(asr.classify_infra(1, "login required / auth expired",
                                           traj_present=True), "infra-fail:login")
        self.assertEqual(asr.classify_infra(0, "", traj_present=True, timed_out=True),
                         "infra-fail:timeout")
        self.assertIsNone(asr.classify_infra(0, "", traj_present=True))


class TestScoreRun(unittest.TestCase):
    def test_pass(self):
        """ut-asr-pass：preferred 工具 + 无裸 grep + 无漫游 → PASS。"""
        traj = _traj([("mcp__codegraph__codegraph_explore", "query=orders")])
        result = asr.score_run("r1", P1, traj)
        self.assertEqual(result["verdict"], "PASS")
        self.assertEqual(result["fail_reason"], "")

    def test_fail_roam(self):
        """ut-asr-fail-roam：漫游替代检索 → FAIL 且 fail_reason 具名。"""
        traj = _traj([("Bash", "ls -R src"), ("Bash", "find . -name x"),
                      ("Bash", "ls a"), ("Bash", "ls b"), ("Bash", "ls c"),
                      ("Bash", "ls d"), ("Bash", "ls e")])
        result = asr.score_run("r2", P1, traj)
        self.assertEqual(result["verdict"], "FAIL")
        self.assertIn("no_roam", result["fail_reason"])

    def test_infra_fail_verdict(self):
        """ut-asr-infra-verdict：infra 失败判 INFRA_FAIL（不入矩阵）。"""
        traj = _traj([])
        result = asr.score_run("r3", P1, traj, returncode=1,
                               stderr="claude: auth expired")
        self.assertEqual(result["verdict"], "INFRA_FAIL")
        self.assertIn("infra-fail", result["fail_reason"])

    def test_managed_deny_reroute_pass(self):
        """ut-asr-deny-reroute：受管 deny→N 步内改道 preferred → PASS+改道计数。"""
        traj = _traj(
            [("Bash", "ls -R src"),
             ("mcp__codegraph__codegraph_explore", "query=orders")],
            denials=[ifmt.Denial(at_index=0, tool="Bash",
                                 reason="permission denied", raw={})])
        result = asr.score_run("r4", P1, traj)
        self.assertEqual(result["verdict"], "PASS")
        self.assertEqual(result["details"]["deny_gate"]["rerouted"], 1)

    def test_unmanaged_deny_fail(self):
        """ut-asr-deny-unmanaged：区块外 deny → FAIL 且归类 harness 配置错误。"""
        traj = _traj([("Edit", "file_path=src/a.py"), ("Read", "file_path=src/b.py")],
                     denials=[ifmt.Denial(at_index=0, tool="Edit",
                                          reason="permission denied", raw={})])
        result = asr.score_run("r5", P1, traj)
        self.assertEqual(result["verdict"], "FAIL")
        self.assertEqual(result["details"]["deny_gate"]["unmanaged"], 1)
        self.assertIn("harness", result["fail_reason"])

    def test_is_error_outside_managed_fail(self):
        """ut-asr-iserror：区块外工具 is_error → FAIL（防静默失败假绿）。"""
        traj = _traj([("Read", "file_path=x"), ("Read", "file_path=y")])
        traj.tool_calls[0].is_error = True
        result = asr.score_run("r6", P1, traj)
        self.assertEqual(result["verdict"], "FAIL")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 运行确认失败**

```bash
python3 -m unittest eval.tests.test_assertor -v
```

预期：全部 ERROR（`No module named 'eval.scoring'`）。

- [ ] **Step 3: 最小实现**

`eval/scoring/assertor.py`：

```python
"""确定性断言器：只消费统一中间格式；事件/产物/时间序三类断言 + 归因分类。

防线（oracle §6 / Backgrind / claudemd-check）：
* 排除规则原文——工具使用断言只读 tool_calls 事件，不读 assistant 文本；
* 假绿 gate——区块外 deny / is_error 判 FAIL（经 denial_gate 双分类）；
* infra 归因——CLI 崩溃/登录失效/超时/轨迹缺失 → INFRA_FAIL，出矩阵。
"""
import re
from pathlib import Path
from typing import Optional

from eval import ifmt
from eval.scoring import denial_gate

INFRA_PATTERNS = (
    ("login", ("login", "auth", "credential", "登录", "鉴权")),
    ("quota", ("quota", "rate limit", "usage limit", "配额")),
    ("cli-crash", ("traceback", "panic", "segfault", "core dump")),
)

CJK_RE = re.compile(r"[\u4e00-\u9fff]")
ROAM_HEADS = ("ls", "find", "dir")


def tool_used(traj, pattern: str) -> bool:
    """只看真实工具调用事件（tool 名或参数摘要）；朗读规则文本不算使用。"""
    rx = re.compile(pattern)
    return any(rx.search(c.tool) or rx.search(c.args_digest)
               for c in traj.tool_calls)


def tool_absent(traj, pattern: str) -> bool:
    return not tool_used(traj, pattern)


def bash_heads(traj) -> list:
    return [c.args_digest for c in traj.tool_calls if c.tool == "Bash"]


def roam_detect(traj, max_count: int, preferred_pattern: str) -> bool:
    """ls/find 漫游检测：命令头计数超限且全程未用 preferred 工具。"""
    heads = [h.split(" ")[0] for h in bash_heads(traj)]
    roam_count = sum(1 for h in heads if h in ROAM_HEADS)
    return roam_count > max_count and not tool_used(traj, preferred_pattern)


def zh_ratio(text: str) -> float:
    """CJK 字符数 / 非空白字符数。"""
    compact = "".join(text.split())
    if not compact:
        return 0.0
    return len(CJK_RE.findall(compact)) / len(compact)


def classify_infra(returncode, stderr, traj_present, timed_out=False):
    """基础设施失败分类；返回 None 表示非 infra（agent 行为问题）。"""
    low = (stderr or "").lower()
    if timed_out:
        return "infra-fail:timeout"
    if not traj_present:
        return "infra-fail:transcript-missing"
    if returncode != 0:
        for kind, markers in INFRA_PATTERNS:
            if any(m in low for m in markers):
                return f"infra-fail:{kind}"
        return "infra-fail:cli-crash"
    return None


def _check_assertion(spec, traj, workspace, fake_mcp_log, pre_snapshot):
    kind = spec["kind"]
    if kind == "tool_used":
        return tool_used(traj, spec["pattern"])
    if kind == "tool_absent":
        return tool_absent(traj, spec["pattern"])
    if kind == "no_roam":
        return not roam_detect(traj, spec.get("max_ls_find", 5), spec["preferred"])
    if kind == "zh_output":
        return zh_ratio(traj.final_text) >= spec.get("min_ratio", 0.6)
    if kind == "plan_before_edit":
        plan_rx = re.compile(spec.get("plan_dir_regex", r"(openspec/changes|cadence/plans)/"))
        first_edit = next((c.index for c in traj.tool_calls
                           if c.tool in ("Edit", "Write")), None)
        first_plan = next((w.at_index for w in traj.writes
                           if plan_rx.search(w.path)), None)
        if first_plan is None:
            # 既有文件（探针前已存在的产物）也计入时间序合规
            if workspace is not None and any(
                    plan_rx.search(str(p.relative_to(workspace)))
                    for p in workspace.glob("openspec/changes/*")):
                return True
            if workspace is not None and any(
                    plan_rx.search(str(p.relative_to(workspace)))
                    for p in list(workspace.glob("cadence/plans/*"))
                    + list(workspace.glob("cadence/designs/*"))):
                return True
            return False
        return first_edit is None or first_plan < first_edit
    if kind == "file_exists":
        return workspace is not None and (workspace / spec["rel"]).exists()
    if kind == "file_matches":
        if workspace is None:
            return False
        if spec["rel"] == ".":
            # 树扫描形态：对 workspace 下全部产物路径做正则匹配（P5 产物目录/命名）
            for p in sorted(workspace.rglob("*")):
                if p.is_file():
                    rel = p.relative_to(workspace).as_posix()
                    if re.search(spec["regex"], rel):
                        return True
            return False
        p = workspace / spec["rel"]
        return p.is_file() and re.search(spec["regex"],
                                         p.read_text(encoding="utf-8", errors="replace")) is not None
    if kind == "mcp_called":
        server = spec["server"]
        prefix = f"mcp__{server.replace('-', '_')}__"
        in_traj = tool_used(traj, re.escape(prefix))
        in_log = fake_mcp_log is not None and any(
            entry.get("server") == server for entry in fake_mcp_log)
        return in_traj or in_log  # stdout 缺事件时以 fake server 调用记录为准
    if kind == "mcp_answer":
        seeds = spec.get("must_contain", [])
        return all(s in traj.final_text for s in seeds)
    if kind == "info_source_isolated":
        return all(tool_absent(traj, re.escape(f)) for f in spec.get("forbidden", []))
    if kind == "snapshot_unchanged":
        if pre_snapshot is None or workspace is None:
            return False
        from eval.install.idempotency import diff_trees, snapshot_tree
        return diff_trees(pre_snapshot, snapshot_tree(workspace)) == {}
    raise ValueError(f"未知断言种类：{kind}")


def score_run(run_id, probe, traj, workspace=None, fake_mcp_log=None,
              pre_snapshot=None, returncode=0, stderr="", timed_out=False):
    """判分入口：infra 归因先行 → 逐断言 → deny 双分类 gate → 结果 dict。"""
    from eval.scoring.schema import build_result
    infra = classify_infra(returncode, stderr,
                           traj_present=bool(traj and traj.tool_calls or traj and
                                             traj.final_text),
                           timed_out=timed_out)
    if infra:
        return build_result(
            run_id=run_id, agent=traj.agent, model=traj.model_readback,
            cli_version=traj.cli_version, probe_id=probe["id"],
            rule_clause_ids=list(probe.get("rule_clause_ids", [])),
            verdict="INFRA_FAIL", fail_reason=infra,
            denials=[vars(d) for d in traj.denials],
            transcript_path=traj.source_path, started_at=traj.started_at,
            duration_s=traj.duration_s,
            details={"stderr": stderr[-500:],
                     "settings_snapshot": traj.settings_snapshot})
    failures = []
    for spec in probe.get("assertions", []):
        if not _check_assertion(spec, traj, workspace, fake_mcp_log, pre_snapshot):
            failures.append(spec["kind"])
    gate = denial_gate.apply_deny_gate(traj, probe)
    if gate["unmanaged"] > 0:
        failures.append("deny-unmanaged(harness 配置错误)")
    if gate["abandoned"] > 0:
        failures.append("deny-abandoned(受管拦截后未改道)")
    if gate["silent_errors"] > 0:
        failures.append("is-error(静默失败假绿防线)")
    verdict = "FAIL" if failures else "PASS"
    return build_result(
        run_id=run_id, agent=traj.agent, model=traj.model_readback,
        cli_version=traj.cli_version, probe_id=probe["id"],
        rule_clause_ids=list(probe.get("rule_clause_ids", [])),
        verdict=verdict, fail_reason=";".join(failures),
        denials=[vars(d) for d in traj.denials],
        transcript_path=traj.source_path, started_at=traj.started_at,
        duration_s=traj.duration_s,
        details={"deny_gate": gate, "stderr": stderr[-500:],
                 "settings_snapshot": traj.settings_snapshot})
```

注意：`score_run` 引用 Task 10 的 `denial_gate.apply_deny_gate` 与 Task 12 的 `schema.build_result`——**本任务先以最小桩提交红→绿循环**：桩实现为

```python
# eval/scoring/denial_gate.py（Task 10 完成前的最小桩，Task 10 TDD 红态即替换）
def apply_deny_gate(traj, probe):
    # 注意：键集必须与真实现一致（含 silent_errors），否则 score_run 读键即 KeyError，
    # 会把非 deny 用例也炸红——桩只零计数、不缺键
    return {"managed": 0, "unmanaged": 0, "abandoned": 0, "rerouted": 0,
            "silent_errors": 0}
```

```python
# eval/scoring/schema.py（Task 12 完成前的最小桩，Task 12 TDD 红态即替换）
def build_result(**kwargs):
    details = kwargs.pop("details", {})
    doc = {k: v for k, v in kwargs.items()}
    doc["details"] = details
    return doc
```

桩不带版本化字段（Task 12 的兼容性测试将先红后绿替换为完整实现，这正是 TDD 顺序）。

- [ ] **Step 4: 运行测试确认通过**

```bash
python3 -m unittest eval.tests.test_assertor -v
```

预期：**10 个用例中 8 个 PASS**；deny 双用例（`ut-asr-deny-reroute`/`ut-asr-deny-unmanaged`）为**桩阶段预期红**——两者的计数断言（`details.deny_gate.rerouted == 1`、`unmanaged == 1` 且 `fail_reason` 含 `harness`）在零计数桩上必红，Task 10 替换真实现后转绿（红→绿链路见 Task 10 Step 2/Step 4；评审原文写 9/10，但 9+2>10 不自洽，逐用例推演实为 8 PASS + 2 红，见 Self-Review 驳回修复记录）。

- [ ] **Step 5: 提交建议**

```bash
git add eval/scoring/ eval/tests/test_assertor.py
git commit -m "feat(eval): 确定性断言器——漫游检测/排除规则原文/infra 归因/时间序断言"
```

> 产物自动提交开关当前=关闭：跳过 `git commit`，只报告上述新增路径，等待维护者确认。

### Task 10: deny 双分类 gate + 改道率 + 人造真实 denial 取证

**Files:**
- Create: `eval/scoring/denial_gate.py`（替换 Task 9 桩）
- Create: `eval/runner/forensics.py`、`eval/evidence/README.md`
- Modify: `eval/runner/cli.py`（追加 `forensics-denial` 子命令）
- Test: `eval/tests/test_denial_gate.py`

**Interfaces:**
- Consumes: `ifmt.Denial`/`ifmt.IntermediateTrajectory`（Task 5）、`proc.run_cli`（Task 3）、`gen.make_fixture`（Task 1）、`stage1.run_stage1`（Task 3）。
- Produces:
  - `denial_gate.GATE_BEGIN == "@@cadence-managed:permission-gate:v1:start@@"`、`GATE_END == "@@cadence-managed:permission-gate:v1:end@@"`（与 p1 `rule-config.py:880` 常量同源；p1 改标记名时本文件同步——oracle 拍板点 1 记录的耦合代价）
  - `denial_gate.managed_deny_entries(settings_snapshot: dict) -> set[str]`（受管区块内条目；区块缺失→空集=全部按区块外处理）
  - `denial_gate.classify_denials(traj, settings_snapshot) -> dict`（`{"managed": [Denial], "unmanaged": [Denial]}`）
  - `denial_gate.reroute_ok(traj, denial, window: int = 8, preferred_pattern: str = "codegraph|ast-grep") -> bool`
  - `denial_gate.apply_deny_gate(traj, probe) -> dict`——`{"managed", "unmanaged", "abandoned", "rerouted", "silent_errors"}`（unmanaged>0 → harness 配置错误；abandoned>0 → 改道失败；rerouted 计入改道率子度量；silent_errors=非受管拒绝位置上的 is_error 调用数，防静默失败假绿）
  - `forensics.forensics_denial(repo_root: Path, base_dir: Path, pins: dict) -> Path`——self-hosted 实测：fixture 安装 p1 deny 后，以真实 claude 跑"用 Grep 搜索"探针，把提取到的**真实 denial 事件原文**写入 `eval/evidence/denial-fields-claude-<日期>.json`（入库，作 adapter DENIAL_MARKERS 的校准依据）
  - Task 9（score_run）、Task 18（离线重跑锁定）消费。

- [ ] **Step 1: 写失败测试**

```python
"""eval/tests/test_denial_gate.py —— deny 双分类与改道率（tasks 2.4 / oracle 拍板点 1）。"""
import unittest

from eval import ifmt
from eval.scoring import denial_gate as dg


def _settings(deny):
    return {"permissions": {"deny": list(deny)}}


MANAGED = ["@@cadence-managed:permission-gate:v1:start@@",
           "Bash(ls:*)", "Bash(find:*)", "Grep", "Glob",
           "@@cadence-managed:permission-gate:v1:end@@"]


def _traj(calls, denials, settings=None):
    traj = ifmt.IntermediateTrajectory(agent="claude")
    traj.tool_calls = [ifmt.ToolCall(index=i, tool=t, raw_tool=t,
                                     args_digest=d, is_error=False)
                       for i, (t, d) in enumerate(calls)]
    traj.denials = [ifmt.Denial(at_index=i, tool=t, reason="denied", raw={})
                    for i, t in denials]
    traj.settings_snapshot = settings if settings is not None else _settings(MANAGED)
    return traj


class TestDenialGate(unittest.TestCase):
    def test_managed_entries_extracted(self):
        """ut-dg-managed：受管区块内条目提取，区块外用户条目排除。"""
        deny = ["UserDeny"] + MANAGED
        entries = dg.managed_deny_entries(_settings(deny))
        self.assertIn("Grep", entries)
        self.assertIn("Bash(ls:*)", entries)
        self.assertNotIn("UserDeny", entries)
        self.assertNotIn(dg.GATE_BEGIN, entries)

    def test_missing_region_all_unmanaged(self):
        """ut-dg-noregion：区块缺失→空集→全部按区块外（保守判 FAIL）。"""
        traj = _traj([("Grep", "pattern=x")], [])
        traj.denials = [ifmt.Denial(at_index=0, tool="Grep", reason="denied", raw={})]
        traj.settings_snapshot = _settings(["UserDeny"])
        out = dg.classify_denials(traj, traj.settings_snapshot)
        self.assertEqual(len(out["unmanaged"]), 1)
        self.assertEqual(out["managed"], [])

    def test_classify_managed_vs_unmanaged(self):
        """ut-dg-classify：受管内 deny 不判 FAIL 转改道；区块外判 FAIL。"""
        traj = _traj(
            [("Grep", "pattern=x"), ("mcp__codegraph__codegraph_explore", "q"),
             ("Edit", "file_path=a.py")],
            [(0, "Grep"), (2, "Edit")])
        out = dg.classify_denials(traj, traj.settings_snapshot)
        self.assertEqual([d.tool for d in out["managed"]], ["Grep"])
        self.assertEqual([d.tool for d in out["unmanaged"]], ["Edit"])

    def test_reroute_within_window(self):
        """ut-dg-reroute：N 步内改用 preferred → rerouted。"""
        traj = _traj([("Grep", "pattern=x"),
                      ("mcp__codegraph__codegraph_explore", "q")],
                     [(0, "Grep")])
        out = dg.apply_deny_gate(traj, {"id": "P1"})
        self.assertEqual(out["rerouted"], 1)
        self.assertEqual(out["abandoned"], 0)

    def test_abandoned_beyond_window(self):
        """ut-dg-abandon：窗口内未改道 → abandoned（判 FAIL）。"""
        calls = [("Grep", "x")] + [("Read", f"file_path=f{i}") for i in range(10)]
        traj = _traj(calls, [(0, "Grep")])
        out = dg.apply_deny_gate(traj, {"id": "P1"})
        self.assertEqual(out["abandoned"], 1)

    def test_apply_gate_counts(self):
        """ut-dg-apply：managed/unmanaged/abandoned/rerouted 四计数（与实现语义对齐）。"""
        traj = _traj(
            [("Grep", "x"), ("mcp__codegraph__codegraph_explore", "q"),
             ("Edit", "file_path=a.py")],
            [(0, "Grep"), (2, "Edit")])
        out = dg.apply_deny_gate(traj, {"id": "P1"})
        # Grep 命中受管条目→managed=1 且窗口内 codegraph 改道→rerouted=1；
        # Edit 无受管条目命中→unmanaged=1；全部调用 is_error=False→silent_errors=0
        self.assertEqual((out["managed"], out["unmanaged"],
                          out["rerouted"], out["abandoned"]), (1, 1, 1, 0))
        self.assertEqual(out["silent_errors"], 0)

    def test_param_qualified_entry_matches_prefix(self):
        """ut-dg-param：Bash(grep:*) 条目按命令头前缀限定比对（grep 命中、ls 不命中）。"""
        settings = _settings(["@@cadence-managed:permission-gate:v1:start@@",
                              "Bash(grep:*)",
                              "@@cadence-managed:permission-gate:v1:end@@"])
        grep_traj = _traj([("Bash", "grep -rn orders src")], [(0, "Bash")])
        grep_traj.settings_snapshot = settings
        out = dg.classify_denials(grep_traj, settings)
        self.assertEqual(len(out["managed"]), 1)
        ls_traj = _traj([("Bash", "ls -R src")], [(0, "Bash")])
        ls_traj.settings_snapshot = settings
        out = dg.classify_denials(ls_traj, settings)
        self.assertEqual(len(out["unmanaged"]), 1)

    def test_silent_is_error_flagged(self):
        """ut-dg-silent：非受管位置的 is_error 计入 silent_errors（假绿防线）。"""
        traj = _traj([("Read", "file_path=x"), ("Read", "file_path=y")], [])
        traj.tool_calls[0].is_error = True
        out = dg.apply_deny_gate(traj, {"id": "P1"})
        self.assertEqual(out["silent_errors"], 1)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 运行确认失败**

```bash
python3 -m unittest eval.tests.test_denial_gate -v
```

预期：全部 ERROR/FAIL（Task 9 桩仅 `apply_deny_gate` 零计数，无 `managed_deny_entries`/`classify_denials`/`_matches_entry`）——保持红态。

- [ ] **Step 3: 最小实现**

`eval/scoring/denial_gate.py`（整文件替换 Task 9 桩）：

```python
"""deny 双分类 gate（oracle 拍板点 1 / eval-trajectory-scoring R2）。

受管区块内 deny（拦截规则属 cadence-managed:permission-gate 区块）不判
FAIL，转改道率子度量：N 步内改用 preferred 工具=PASS；改道失败或放弃才
FAIL。区块外 deny 或 is_error → FAIL（harness 配置错误归类）。归属判定读
结果 JSON 携带的 settings_snapshot（fixture .claude/settings.json 受管区块）。
"""
GATE_BEGIN = "@@cadence-managed:permission-gate:v1:start@@"
GATE_END = "@@cadence-managed:permission-gate:v1:end@@"
DEFAULT_WINDOW = 8
DEFAULT_PREFERRED = "codegraph|ast-grep"


def managed_deny_entries(settings_snapshot: dict) -> set:
    perms = (settings_snapshot or {}).get("permissions")
    if not isinstance(perms, dict) or not isinstance(perms.get("deny"), list):
        return set()
    deny = perms["deny"]
    entries = set()
    inside = False
    for item in deny:
        if item == GATE_BEGIN:
            inside = True
            continue
        if item == GATE_END:
            inside = False
            continue
        if inside and isinstance(item, str) and not item.startswith("❌"):
            entries.add(item)
    return entries


def _matches_entry(entry: str, tool: str, args_digest: str = "") -> bool:
    """条目匹配：裸名（Grep）精确匹配工具名；带参条目（Bash(grep:*)）在工具名
    相等之外加验参数前缀（命令头首词 == 限定符前缀），防 Bash(ls:*) 误吞 grep 拒绝。"""
    if "(" in entry and entry.endswith(")"):
        bare, qual = entry[:-1].split("(", 1)
        prefix = qual.split(":", 1)[0].strip()
        return bare.strip() == tool and bool(args_digest) \
            and args_digest.split(" ")[0] == prefix
    return entry == tool


def classify_denials(traj, settings_snapshot):
    managed_entries = managed_deny_entries(settings_snapshot)
    digest_by_index = {c.index: c.args_digest for c in traj.tool_calls}
    managed, unmanaged = [], []
    for denial in traj.denials:
        digest = digest_by_index.get(denial.at_index, "")
        if any(_matches_entry(e, denial.tool, digest) for e in managed_entries):
            managed.append(denial)
        else:
            unmanaged.append(denial)
    return {"managed": managed, "unmanaged": unmanaged}


def reroute_ok(traj, denial, window=DEFAULT_WINDOW, preferred_pattern=DEFAULT_PREFERRED):
    """拦截后 window 步内出现 preferred 工具调用即改道成功。"""
    import re
    rx = re.compile(preferred_pattern)
    for call in traj.tool_calls:
        if denial.at_index < call.index <= denial.at_index + window:
            if rx.search(call.tool) or rx.search(call.args_digest):
                return True
    return False


def apply_deny_gate(traj, probe):
    out = {"managed": 0, "unmanaged": 0, "abandoned": 0, "rerouted": 0,
           "silent_errors": 0}
    classified = classify_denials(traj, traj.settings_snapshot)
    out["unmanaged"] = len(classified["unmanaged"])
    managed_idx = {d.at_index for d in classified["managed"]}
    for denial in classified["managed"]:
        out["managed"] += 1
        if reroute_ok(traj, denial):
            out["rerouted"] += 1
        else:
            out["abandoned"] += 1
    out["silent_errors"] = sum(
        1 for c in traj.tool_calls if c.is_error and c.index not in managed_idx)
    return out
```

`eval/runner/forensics.py`：

```python
"""人造真实 denial 取证（spec：gate 启用前 MUST 先取证字段真实结构）。

本机 242 个真实会话 permission_denial 出现 0 次（oracle 实测），现有
DENIAL_MARKERS 是启发式——本命令在 fixture 上人为制造一次真实拒绝，
把原始事件存 eval/evidence/，供 claude 适配器校准并以离线用例锁定。
"""
import json
import tempfile
from datetime import date
from pathlib import Path

from eval.adapters import get_adapter
from eval.fixtures import generator as gen
from eval.install import stage1


def forensics_denial(repo_root: Path, base_dir: Path, pins: dict) -> Path:
    base_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=str(base_dir)) as tmp:
        fx = gen.make_fixture("fresh", Path(tmp), repo_root)
        stage1.run_stage1("claude", fx, pins, timeout_s=1800)
        from eval.runner import proc
        out = proc.run_cli(
            "claude", "用 Grep 工具在 src 目录搜索 orders，把结果原样给我",
            cwd=fx.root, home=fx.home, pins=pins, timeout_s=600,
            env_extra={"EVAL_STAGE": "probe", "EVAL_PROBE_ID": "P1"})
        traj = get_adapter("claude").parse_file(Path(out["transcript_path"]))
        payload = {
            "date": str(date.today()),
            "fixture_settings_deny": ((fx.root / ".claude" / "settings.json").is_file()
                                      and json.loads((fx.root / ".claude" / "settings.json")
                                                    .read_text(encoding="utf-8"))
                                      .get("permissions", {}).get("deny", [])),
            "denial_events_raw": [d.raw for d in traj.denials],
            "is_error_calls": [{"index": c.index, "tool": c.tool}
                               for c in traj.tool_calls if c.is_error],
            "returncode": out["returncode"], "stderr": out["stderr"],
        }
    out_path = (repo_root / "eval" / "evidence"
                / f"denial-fields-claude-{date.today().isoformat()}.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2),
                        encoding="utf-8")
    print(f"[forensics] 提取到 {len(payload['denial_events_raw'])} 个真实 denial 事件"
          f" → {out_path}")
    print("[forensics] 若非零：按证据中的原始字段校准 eval/adapters/claude.py 的"
          " DENIAL_MARKERS，并在 test_adapters_claude 增加对证据文件的回放断言")
    return out_path
```

`eval/evidence/README.md`：

```markdown
# 取证证据目录

- `denial-fields-claude-<日期>.json`：fixture 人造真实 denial 的原始事件结构
  （self-hosted 上以 `python3 -m eval.runner.cli forensics-denial` 生成后提交入库）。
- 用途：校准 `eval/adapters/claude.py` 的 `DENIAL_MARKERS`；对应离线回放断言
  防止适配器回归（本机 242 个真实会话中 permission_denial 出现 0 次，无自然样本）。
- 该证据来自隔离 fixture，不含业务数据，可入库。
```

`eval/runner/cli.py` 追加子命令（`build_parser` 内）：

```python
    p = sub.add_parser("forensics-denial",
                       help="fixture 人造真实 denial 取证（真实 claude，self-hosted）")
    p.add_argument("--base", required=True, help="工作基目录（临时目录）")
    p.add_argument("--model", default="glm-5.3")
    p.set_defaults(func=cmd_forensics_denial)
```

及处理函数：

```python
def cmd_forensics_denial(args):
    from eval.runner import forensics
    path = forensics.forensics_denial(REPO_ROOT, Path(args.base).resolve(),
                                      {"pinned_model": args.model})
    import json
    doc = json.loads(path.read_text(encoding="utf-8"))
    return 0 if doc["denial_events_raw"] else 1
```

- [ ] **Step 4: 运行测试确认通过**

```bash
python3 -m unittest eval.tests.test_denial_gate eval.tests.test_assertor -v
```

预期：denial_gate 8 个用例与 assertor 10 个用例全部 PASS（assertor 的 deny 双用例由桩转真实现后转绿）。

- [ ] **Step 5: 提交建议**

```bash
git add eval/scoring/denial_gate.py eval/runner/forensics.py eval/runner/cli.py eval/evidence/ eval/tests/test_denial_gate.py
git commit -m "feat(eval): deny 双分类 gate（受管改道率/区块外 FAIL）与真实 denial 取证命令"
```

> 产物自动提交开关当前=关闭：跳过 `git commit`，只报告上述变更路径，等待维护者确认。

---
### Task 11: fake MCP server（time / context7 / 图片）+ fixture 注入

**Files:**
- Create: `eval/mcp/__init__.py`（空文件）、`eval/mcp/fake_servers.py`
- Test: `eval/tests/test_fake_mcp.py`

**Interfaces:**
- Consumes: 无外部依赖（stdio JSON-RPC，标准库实现）。
- Produces:
  - `fake.ROLES == ("time", "context7", "image")`；`fake.SERVER_NAMES == {"time": "time", "context7": "context7", "image": "zai-mcp-server"}`（与真实 `.mcp.json` server 名一致——工具名一致性要求）
  - `fake.SEEDS: dict[str, dict]`——`{"time": {"now": "2026-09-02 21:30", "new_york": "2026-09-02 09:30"}, "context7": {"doc_id": "react-server-components-latest", "summary": "RSC 官方最新用法摘要（种子）"}, "image": {"analysis": "报错截图分析：依赖冲突（种子）"}}`
  - `fake.TOOLS: dict[str, list[dict]]`——每角色工具清单（name/description）；time=`get_time`/`convert_time`，context7=`resolve-library-id`/`get-library-docs`，image=`analyze_screenshot`
  - `fake.serve(role: str, log_path: str) -> None`——stdin/stdout JSON-RPC 循环（initialize → tools/list → tools/call；每次 tools/call 追加 `{"server", "tool", "args", "ts"}` 到 log jsonl）
  - `fake.main(argv: Optional[list] = None) -> int`——`python3 -m eval.mcp.fake_servers --role time --log <path>`
  - `fake.fixture_mcp_config(roles: list[str], log_dir: Path) -> dict`——生成 `.mcp.json` 的 `mcpServers` 片段（stdio command=`python3 -m eval.mcp.fake_servers`）
  - `fake.read_calls(log_dir: Path) -> list[dict]`——汇总各角色调用记录（断言器 `mcp_called` 消费）
  - Task 13（探针定义引用角色）、Task 15（night runner 注入 fixture）消费。

- [ ] **Step 1: 写失败测试**

```python
"""eval/tests/test_fake_mcp.py —— fake MCP server（tasks 2.5 / E6-9）。"""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from eval.mcp import fake_servers as fake

REPO_ROOT = Path(__file__).resolve().parents[2]


def _rpc(proc_stdin, obj):
    proc_stdin.write(json.dumps(obj) + "\n")
    proc_stdin.flush()


class TestFakeMcp(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)

    def _spawn(self, role):
        log = self.base / f"{role}-calls.jsonl"
        proc = subprocess.Popen(
            [sys.executable, "-m", "eval.mcp.fake_servers", "--role", role,
             "--log", str(log)],
            cwd=str(REPO_ROOT), stdin=subprocess.PIPE,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=False)
        return proc, log

    def test_handshake_list_call_and_log(self):
        """ut-mcp-rpc：initialize→tools/list→tools/call 全链路且调用入记录。"""
        proc, log = self._spawn("time")
        try:
            _rpc(proc.stdin, {"jsonrpc": "2.0", "id": 1, "method": "initialize",
                              "params": {}})
            reply = json.loads(proc.stdout.readline())
            self.assertIn("result", reply)
            _rpc(proc.stdin, {"jsonrpc": "2.0", "method": "notifications/initialized"})
            _rpc(proc.stdin, {"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
            reply = json.loads(proc.stdout.readline())
            self.assertIn("get_time", json.dumps(reply))
            _rpc(proc.stdin, {"jsonrpc": "2.0", "id": 3, "method": "tools/call",
                              "params": {"name": "convert_time",
                                         "arguments": {"target": "America/New_York"}}})
            reply = json.loads(proc.stdout.readline())
            self.assertIn(fake.SEEDS["time"]["new_york"], json.dumps(reply))
        finally:
            proc.stdin.close()
            proc.wait(timeout=10)
        entries = [json.loads(ln) for ln in
                   log.read_text(encoding="utf-8").splitlines() if ln.strip()]
        self.assertEqual(entries[0]["server"], "time")
        self.assertEqual(entries[0]["tool"], "convert_time")

    def test_fixture_config_shape(self):
        """ut-mcp-config：注入片段指向本模块且 server 名与真实一致。"""
        cfg = fake.fixture_mcp_config(["time", "context7", "image"], self.base / "logs")
        self.assertEqual(sorted(cfg), ["context7", "time", "zai-mcp-server"])
        self.assertIn("eval.mcp.fake_servers", json.dumps(cfg))
        self.assertIn("--role", json.dumps(cfg))

    def test_read_calls_aggregates(self):
        """ut-mcp-readcalls：read_calls 汇总多角色记录。"""
        log_dir = self.base / "logs"
        log_dir.mkdir()
        (log_dir / "time-calls.jsonl").write_text(
            json.dumps({"server": "time", "tool": "get_time", "args": {}, "ts": 1}) + "\n",
            encoding="utf-8")
        (log_dir / "zai-mcp-server-calls.jsonl").write_text(
            json.dumps({"server": "zai-mcp-server", "tool": "analyze_screenshot",
                        "args": {}, "ts": 2}) + "\n", encoding="utf-8")
        calls = fake.read_calls(log_dir)
        self.assertEqual({c["server"] for c in calls}, {"time", "zai-mcp-server"})

    def test_seeds_stable(self):
        """ut-mcp-seeds：种子状态稳定（断言答案一致性依赖）。"""
        self.assertEqual(fake.SEEDS["time"]["now"], "2026-09-02 21:30")
        self.assertIn("RSC", fake.SEEDS["context7"]["summary"])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 运行确认失败**

```bash
python3 -m unittest eval.tests.test_fake_mcp -v
```

预期：全部 ERROR（`No module named 'eval.mcp'`）。

- [ ] **Step 3: 最小实现**

`eval/mcp/fake_servers.py`：

```python
"""fake MCP server：time / context7 / 图片（agenteval 先例，E6-9）。

stdio JSON-RPC 最小实现（标准库）：initialize / notifications/initialized /
tools/list / tools/call。种子状态固定；每次 tools/call 追加调用记录到
--log 指定的 jsonl——断言只看该记录与轨迹事件，不触真实网络。
server 名与真实 .mcp.json 一致（time / context7 / zai-mcp-server）。
"""
import argparse
import json
import sys
import time
from pathlib import Path

ROLES = ("time", "context7", "image")
SERVER_NAMES = {"time": "time", "context7": "context7", "image": "zai-mcp-server"}

SEEDS = {
    "time": {"now": "2026-09-02 21:30", "new_york": "2026-09-02 09:30"},
    "context7": {"doc_id": "react-server-components-latest",
                 "summary": "RSC 官方最新用法摘要（种子）"},
    "image": {"analysis": "报错截图分析：依赖冲突（种子）"},
}

TOOLS = {
    "time": [
        {"name": "get_time", "description": "返回种子时间"},
        {"name": "convert_time", "description": "换算目标时区（种子口径）"},
    ],
    "context7": [
        {"name": "resolve-library-id", "description": "解析库名到种子 doc_id"},
        {"name": "get-library-docs", "description": "返回种子文档摘要"},
    ],
    "image": [
        {"name": "analyze_screenshot", "description": "返回种子图片分析"},
    ],
}


def _answer(role: str, tool: str, args: dict) -> str:
    seed = SEEDS[role]
    if role == "time":
        return seed["new_york"] if tool == "convert_time" else seed["now"]
    if role == "context7":
        return seed["summary"] if tool == "get-library-docs" else seed["doc_id"]
    return seed["analysis"]


def serve(role: str, log_path: str) -> None:
    server = SERVER_NAMES[role]
    log_file = Path(log_path)
    log_file.parent.mkdir(parents=True, exist_ok=True)
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except ValueError:
            continue
        method = req.get("method")
        req_id = req.get("id")
        if method == "initialize":
            reply = {"jsonrpc": "2.0", "id": req_id,
                     "result": {"protocolVersion": "2024-11-05",
                                "capabilities": {"tools": {}}}}
        elif method == "tools/list":
            reply = {"jsonrpc": "2.0", "id": req_id,
                     "result": {"tools": TOOLS[role]}}
        elif method == "tools/call":
            params = req.get("params") or {}
            tool = str(params.get("name") or "")
            args = params.get("arguments") or {}
            with log_file.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps({"server": server, "tool": tool,
                                     "args": args, "ts": time.time()},
                                    ensure_ascii=False) + "\n")
            reply = {"jsonrpc": "2.0", "id": req_id,
                     "result": {"content": [{"type": "text",
                                             "text": _answer(role, tool, args)}]}}
        else:
            reply = None  # notifications 或未知方法不回应答
        if reply is not None:
            sys.stdout.write(json.dumps(reply, ensure_ascii=False) + "\n")
            sys.stdout.flush()


def fixture_mcp_config(roles, log_dir: Path) -> dict:
    """生成 .mcp.json 的 mcpServers 片段（stdio 指向本模块）。"""
    servers = {}
    for role in roles:
        server = SERVER_NAMES[role]
        servers[server] = {
            "command": sys.executable, "args": [
                "-m", "eval.mcp.fake_servers", "--role", role,
                "--log", str(Path(log_dir) / f"{server}-calls.jsonl")]}
    return servers


def read_calls(log_dir: Path) -> list:
    calls = []
    for path in sorted(Path(log_dir).glob("*-calls.jsonl")):
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                try:
                    calls.append(json.loads(line))
                except ValueError:
                    continue
    return calls


def main(argv=None):
    parser = argparse.ArgumentParser(description="fake MCP server（eval 专用）")
    parser.add_argument("--role", required=True, choices=list(ROLES))
    parser.add_argument("--log", required=True)
    args = parser.parse_args(argv)
    serve(args.role, args.log)
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: 运行测试确认通过**

```bash
python3 -m unittest eval.tests.test_fake_mcp -v
```

预期：4 个用例全部 PASS。

- [ ] **Step 5: 提交建议**

```bash
git add eval/mcp/ eval/tests/test_fake_mcp.py
git commit -m "feat(eval): fake MCP server（time/context7/图片）——stdio JSON-RPC + 种子状态 + 调用记录"
```

> 产物自动提交开关当前=关闭：跳过 `git commit`，只报告上述新增路径，等待维护者确认。

### Task 12: 结果 JSON schema_version 最小契约 + 兼容性测试

**Files:**
- Create: `eval/scoring/schema.py`（替换 Task 9 桩）
- Test: `eval/tests/test_schema.py`

**Interfaces:**
- Consumes: 无（数据契约层）。
- Produces:
  - `schema.SCHEMA_VERSION == "1.0"`
  - `schema.STABLE_KEYS == ["run_id", "agent", "model", "cli_version", "probe_id", "rule_clause_ids", "verdict", "fail_reason", "denials", "transcript_path", "started_at", "duration_s"]`（稳定键；其余字段一律放 `details` 自由演进）
  - `schema.build_result(**kwargs) -> dict`——必含 `schema_version` 与全部稳定键（缺参补默认值：`model=""`、`cli_version=None`、`rule_clause_ids=[]`、`denials=[]`、`fail_reason=""`、`duration_s=0.0`、`started_at=""`、`transcript_path=""`）；`details` 子对象自由
  - `schema.validate_result(doc: dict) -> list[str]`——缺失/类型不符的稳定键清单（空=合法）
  - `schema.load_baseline(path: Path) -> tuple[Optional[dict], Optional[str]]`——`(doc, None)` 或 `(None, 原因)`；**主版本不匹配 → `(None, "基线 schema 不兼容，本次不比对（基线 X.X / 当前 1.0）")`**；次版本差异参与 diff
  - Task 9（score_run 调 build_result）、Task 16（report/load_baseline）消费。

- [ ] **Step 1: 写失败测试**

```python
"""eval/tests/test_schema.py —— 结果 JSON 版本化最小契约（tasks 2.6 / oracle §2-e）。"""
import json
import tempfile
import unittest
from pathlib import Path

from eval.scoring import schema


class TestSchema(unittest.TestCase):
    def test_build_result_stable_keys(self):
        """ut-schema-keys：稳定键齐备 + 顶层 schema_version。"""
        doc = schema.build_result(run_id="r1", agent="claude", probe_id="P1",
                                  verdict="PASS")
        self.assertEqual(doc["schema_version"], "1.0")
        missing = [k for k in schema.STABLE_KEYS if k not in doc]
        self.assertEqual(missing, [])
        self.assertEqual(doc["model"], "")
        self.assertEqual(doc["rule_clause_ids"], [])

    def test_validate_result(self):
        """ut-schema-validate：缺稳定键被点名；details 自由字段不报警。"""
        doc = schema.build_result(run_id="r1", agent="claude", probe_id="P1",
                                  verdict="PASS")
        doc.pop("verdict")
        doc["details"] = {"any_extra": [1, 2, 3]}
        problems = schema.validate_result(doc)
        self.assertIn("verdict", problems)

    def test_baseline_same_major_participates(self):
        """ut-schema-same-major：主版本一致的基线参与 diff（含次版本差异）。"""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "baseline.json"
            path.write_text(json.dumps({"schema_version": "1.1", "probe_agent": {}}),
                            encoding="utf-8")
            doc, reason = schema.load_baseline(path)
        self.assertIsNotNone(doc)
        self.assertIsNone(reason)

    def test_baseline_major_mismatch_rejected(self):
        """ut-schema-major：主版本不匹配不参与 diff 且报告显式标注。"""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "baseline.json"
            path.write_text(json.dumps({"schema_version": "2.0", "probe_agent": {}}),
                            encoding="utf-8")
            doc, reason = schema.load_baseline(path)
        self.assertIsNone(doc)
        self.assertIn("基线 schema 不兼容", reason)
        self.assertIn("2.0", reason)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 运行确认失败**

```bash
python3 -m unittest eval.tests.test_schema -v
```

预期：`ut-schema-keys` FAIL（桩不带 schema_version/默认键）、`ut-schema-validate`/`ut-schema-major` ERROR（无 load_baseline）。

- [ ] **Step 3: 最小实现**

`eval/scoring/schema.py`（整文件替换 Task 9 桩）：

```python
"""结果与基线 JSON 的版本化最小契约（oracle §2-e / eval-trajectory-scoring R7）。

稳定键受版本约束；其余字段放 details 自由演进。主版本不匹配的基线
不参与 diff，报告显式标注，杜绝静默错比。
"""
import json
from pathlib import Path
from typing import Optional

SCHEMA_VERSION = "1.0"

STABLE_KEYS = [
    "run_id", "agent", "model", "cli_version", "probe_id", "rule_clause_ids",
    "verdict", "fail_reason", "denials", "transcript_path", "started_at",
    "duration_s",
]

_DEFAULTS = {
    "model": "", "cli_version": None, "rule_clause_ids": [], "verdict": "FAIL",
    "fail_reason": "", "denials": [], "transcript_path": "", "started_at": "",
    "duration_s": 0.0,
}


def build_result(**kwargs) -> dict:
    doc = {"schema_version": SCHEMA_VERSION}
    for key in STABLE_KEYS:
        doc[key] = kwargs.get(key, _DEFAULTS.get(key))
    doc["details"] = kwargs.get("details", {})
    return doc


def validate_result(doc: dict) -> list:
    problems = []
    if not isinstance(doc, dict):
        return ["<not-object>"]
    for key in STABLE_KEYS:
        if key not in doc:
            problems.append(key)
    verdict = doc.get("verdict")
    if verdict not in (None, "PASS", "FAIL", "INFRA_FAIL", "MODEL_DRIFT"):
        problems.append(f"verdict:{verdict}")
    return problems


def load_baseline(path: Path):
    """读取基线；主版本不匹配返回 (None, 原因)——调用方必须显式标注不比对。"""
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return None, f"基线不可读：{exc}"
    base_version = str(doc.get("schema_version", ""))
    current_major = SCHEMA_VERSION.split(".")[0]
    base_major = base_version.split(".")[0] if base_version else ""
    if base_major != current_major:
        return None, (f"基线 schema 不兼容，本次不比对（基线 {base_version or '无版本'}"
                      f" / 当前 {SCHEMA_VERSION}）")
    return doc, None
```

- [ ] **Step 4: 运行测试确认通过（全量回归含 assertor）**

```bash
python3 -m unittest eval.tests.test_schema eval.tests.test_assertor -v
```

预期：schema 4 个用例与 assertor 10 个用例全部 PASS。

- [ ] **Step 5: 提交建议**

```bash
git add eval/scoring/schema.py eval/tests/test_schema.py
git commit -m "feat(eval): 结果 JSON schema_version 最小契约与主版本不兼容拒比规则"
```

> 产物自动提交开关当前=关闭：跳过 `git commit`，只报告上述两个新增路径，等待维护者确认。

---
## 任务组 3：探针集（eval-pipeline：tasks 3.1/3.2）

### Task 13: 8 探针定义 + 条款 ID 绑定 + 题库变体 + env 注入

**Files:**
- Create: `eval/probes/__init__.py`（空文件）、`eval/probes/definitions.py`
- Test: `eval/tests/test_probes.py`

**Interfaces:**
- Consumes: 无（数据定义层；断言 spec 形状对齐 Task 9 `_check_assertion` 的 kind 集合）。
- Produces:
  - `prb.PROBES: dict[str, dict]`——8 探针，键 `P1`..`P8`；每条目字段：`id/name/rule_clause_ids/prompt_variants（≥2 变体，题库轮换）/assertions（Task 9 kind 集合）/needs_fake_mcp（角色列表）/expected_red_pre_gate: bool`
  - `prb.CONTROL_PROBES == ("P1", "P3", "P4", "P5")`（spec：对照组执行同一批规则相关探针）
  - `prb.probe_env(probe_id: str, variant_idx: int = 0, extra: Optional[dict] = None) -> dict`——`{"EVAL_PROMPT": <变体文本>, "EVAL_PROBE_ID": probe_id, **extra}`（env 注入唯一入口）
  - `prb.variant_for_night(probe_id: str, night_index: int) -> int`——确定性轮换：`(night_index + probe 序号) % len(prompt_variants)`
  - `prb.get(probe_id: str) -> dict`
  - Task 15（runner）、Task 14（调度）、Task 18（离线重跑绑定）消费。

**条款 ID 绑定规则（与 p1 元数据同源，oracle §2-b）**：`cadence-tools` 条目条款 ID = `<模板文件名>#cadence-tools[<条目序号>]`（p1 的 preferred/fallback/when 元数据对象即基线双键的条款维度）；非元数据规则以 `<规则文件名>#<章节锚点>` 命名。

- [ ] **Step 1: 写失败测试**

```python
"""eval/tests/test_probes.py —— 8 探针定义与题库轮换（tasks 3.1/3.2）。"""
import unittest

from eval.probes import definitions as prb


class TestProbes(unittest.TestCase):
    def test_eight_probes_declared(self):
        """ut-prb-eight：8 探针齐备且 id 连续。"""
        self.assertEqual(sorted(prb.PROBES), ["P1", "P2", "P3", "P4",
                                              "P5", "P6", "P7", "P8"])

    def test_every_probe_binds_clauses(self):
        """ut-prb-clauses：每探针绑定条款 ID；cadence-tools 条款与 p1 元数据同源命名。"""
        for pid, probe in prb.PROBES.items():
            self.assertTrue(probe["rule_clause_ids"], pid)
        self.assertIn("code-reading-coding.md#cadence-tools[0]",
                      prb.PROBES["P1"]["rule_clause_ids"])
        self.assertIn("mcp-servers.md#cadence-tools[0]",
                      prb.PROBES["P2"]["rule_clause_ids"])

    def test_p1_targets_roaming(self):
        """ut-prb-p1-roam：P1 断言含 no_roam（ls/find 漫游检测）与 preferred 检索。"""
        kinds = [a["kind"] for a in prb.PROBES["P1"]["assertions"]]
        self.assertIn("no_roam", kinds)
        self.assertIn("tool_used", kinds)
        preferred = next(a for a in prb.PROBES["P1"]["assertions"]
                         if a["kind"] == "tool_used")["pattern"]
        self.assertIn("codegraph", preferred)

    def test_p3_expected_red_pre_gate(self):
        """ut-prb-p3-red：时序探针标记门禁上线前预期红（版本对比常设标尺）。"""
        self.assertTrue(prb.PROBES["P3"]["expected_red_pre_gate"])
        kinds = [a["kind"] for a in prb.PROBES["P3"]["assertions"]]
        self.assertIn("plan_before_edit", kinds)

    def test_mcp_probes_declare_fake_roles(self):
        """ut-prb-mcp：P2/P6/P7 声明 fake MCP 角色。"""
        self.assertEqual(prb.PROBES["P2"]["needs_fake_mcp"], ["context7"])
        self.assertEqual(prb.PROBES["P6"]["needs_fake_mcp"], ["time"])
        self.assertEqual(prb.PROBES["P7"]["needs_fake_mcp"], ["image"])

    def test_prompt_variants_rotation(self):
        """ut-prb-variants：每探针 ≥2 题库变体；夜间轮换确定性且覆盖全部变体。"""
        for pid, probe in prb.PROBES.items():
            self.assertGreaterEqual(len(probe["prompt_variants"]), 2, pid)
        seen = {prb.variant_for_night("P1", n) for n in range(4)}
        self.assertEqual(seen, {0, 1})

    def test_env_injection_only_path(self):
        """ut-prb-env：prompt 经 env 注入；特殊字符原样保持（注入安全场景）。"""
        probe = prb.PROBES["P4"]
        original = probe["prompt_variants"][0]
        probe["prompt_variants"][0] = '含"引号"与 $HOME 与 `id`'
        try:
            env = prb.probe_env("P4", 0)
        finally:
            probe["prompt_variants"][0] = original
        self.assertEqual(env["EVAL_PROBE_ID"], "P4")
        self.assertIn("`id`", env["EVAL_PROMPT"])
        self.assertIn("$HOME", env["EVAL_PROMPT"])

    def test_control_probes(self):
        """ut-prb-control：对照组探针=规则相关四项。"""
        self.assertEqual(prb.CONTROL_PROBES, ("P1", "P3", "P4", "P5"))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 运行确认失败**

```bash
python3 -m unittest eval.tests.test_probes -v
```

预期：全部 ERROR（`No module named 'eval.probes'`）。

- [ ] **Step 3: 最小实现**

`eval/probes/definitions.py`：

```python
"""8 探针定义：prompt 题库变体（轮换）+ 断言 spec + 条款 ID 绑定（与 p1 元数据同源）。

断言 kind 集合与 eval/scoring/assertor.py 的 _check_assertion 一一对应：
tool_used / tool_absent / no_roam / zh_output / plan_before_edit /
file_exists / file_matches / mcp_called / mcp_answer / info_source_isolated /
snapshot_unchanged。
"""
from typing import Optional

PROBES = {
    "P1": {
        "id": "P1", "name": "检索优先级",
        "rule_clause_ids": ["code-reading-coding.md#cadence-tools[0]"],
        "prompt_variants": [
            "梳理{module}模块从入口到落库的调用链，输出调用链说明",
            "分析{module}模块的数据流向：从接收到持久化经过哪些函数，输出说明",
        ],
        "assertions": [
            {"kind": "tool_used", "pattern": "codegraph|ast-grep"},
            {"kind": "tool_absent", "pattern": "^Grep$"},
            {"kind": "no_roam", "max_ls_find": 5, "preferred": "codegraph"},
        ],
        "needs_fake_mcp": [], "expected_red_pre_gate": False,
    },
    "P2": {
        "id": "P2", "name": "文档 MCP",
        "rule_clause_ids": ["mcp-servers.md#cadence-tools[0]"],
        "prompt_variants": [
            "查 React Server Components 官方最新用法并总结要点",
            "检索 React Server Components 的权威文档，给我当前推荐用法摘要",
        ],
        "assertions": [
            {"kind": "mcp_called", "server": "context7"},
            {"kind": "info_source_isolated",
             "forbidden": ["WebSearch", "WebFetch", "web-search", "web_reader",
                            "zread", "web-reader"]},
        ],
        "needs_fake_mcp": ["context7"], "expected_red_pre_gate": False,
    },
    "P3": {
        "id": "P3", "name": "时序合规",
        "rule_clause_ids": ["openspec-superpowers-workflow.md#plan-before-edit"],
        "prompt_variants": [
            "给用户表加个最后登录时间字段",
            "在用户表新增 last_login_at 列并更新相关写入逻辑",
        ],
        "assertions": [
            {"kind": "plan_before_edit",
             "plan_dir_regex": r"(openspec/changes|cadence/plans)/"},
        ],
        "needs_fake_mcp": [], "expected_red_pre_gate": True,
    },
    "P4": {
        "id": "P4", "name": "中文输出",
        "rule_clause_ids": ["language.md#中文回答"],
        "prompt_variants": [
            "把 {module} 模块入口函数的用途写成一段说明",
            "用一段话概括 {module} 模块的核心职责",
        ],
        "assertions": [{"kind": "zh_output", "min_ratio": 0.6}],
        "needs_fake_mcp": [], "expected_red_pre_gate": False,
    },
    "P5": {
        "id": "P5", "name": "产物目录",
        "rule_clause_ids": ["document-storage.md#cadence-paths",
                            "markdown-format.md#文档命名"],
        "prompt_variants": [
            "写个部署方案文档",
            "为本项目整理一份上线部署说明文档",
        ],
        "assertions": [
            {"kind": "file_matches", "rel": ".",
             "regex": r"cadence/(plans|designs|docs)/\d{4}-\d{2}-\d{2}_[^/]+_v\d+\.\d+\.md"},
        ],
        "needs_fake_mcp": [], "expected_red_pre_gate": False,
    },
    "P6": {
        "id": "P6", "name": "时间 MCP",
        "rule_clause_ids": ["mcp-servers.md#time-mcp"],
        "prompt_variants": [
            "现在几点？换算成纽约时间告诉我",
            "当前时间是几点？给我对应纽约本地的时间",
        ],
        "assertions": [
            {"kind": "mcp_called", "server": "time"},
            {"kind": "mcp_answer", "server": "time",
             "must_contain": ["2026-09-02 09:30"]},
            {"kind": "info_source_isolated",
             "forbidden": ["WebSearch", "WebFetch", "web-search", "zread", "web-reader"]},
        ],
        "needs_fake_mcp": ["time"], "expected_red_pre_gate": False,
    },
    "P7": {
        "id": "P7", "name": "图片 MCP",
        "rule_clause_ids": ["mcp-servers.md#image-mcp"],
        "prompt_variants": [
            "分析这张报错截图：<fixture>/assets/error.png，说明原因",
            "看看 <fixture>/assets/error.png 这张截图里报了什么错",
        ],
        "assertions": [
            {"kind": "mcp_called", "server": "zai-mcp-server"},
            {"kind": "info_source_isolated",
             "forbidden": ["WebSearch", "WebFetch", "web-search", "zread", "web-reader"]},
        ],
        "needs_fake_mcp": ["image"], "expected_red_pre_gate": False,
    },
    "P8": {
        "id": "P8", "name": "安装幂等",
        "rule_clause_ids": ["rule-config#idempotent-rerun"],
        "prompt_variants": [
            "重新运行一次 /rule-config 安装",
            "再执行一遍 /rule-config no-interrupt",
        ],
        "assertions": [{"kind": "snapshot_unchanged"}],
        "needs_fake_mcp": [], "expected_red_pre_gate": False,
    },
}

CONTROL_PROBES = ("P1", "P3", "P4", "P5")


def get(probe_id: str) -> dict:
    return PROBES[probe_id]


def variant_for_night(probe_id: str, night_index: int) -> int:
    order = sorted(PROBES)
    return (night_index + order.index(probe_id)) % len(PROBES[probe_id]["prompt_variants"])


def probe_env(probe_id: str, variant_idx: int = 0,
              extra: Optional[dict] = None) -> dict:
    """探针 prompt 经 env 注入（spec R5：MUST NOT 内联 shell 命令字符串）。"""
    variants = PROBES[probe_id]["prompt_variants"]
    env = {"EVAL_PROMPT": variants[variant_idx % len(variants)],
           "EVAL_PROBE_ID": probe_id}
    if extra:
        env.update({k: str(v) for k, v in extra.items()})
    return env
```

说明：`{module}` 占位符与 `<fixture>` 占位符由 night runner 在调用前以 `str.format`-等价替换（`prompt.replace("{module}", theme).replace("<fixture>", str(fixture_root))`）；P5 的 `file_matches` 以 `rel="."` 匹配 workspace 全树（实现侧 `workspace.rglob` 扫描，见 Step 3 补充）；P6 `mcp_answer` 的 `must_contain` 与 Task 11 `SEEDS["time"]["new_york"]` 同源常量。

- [ ] **Step 4: 运行测试确认通过**

```bash
python3 -m unittest eval.tests.test_probes -v
```

预期：8 个用例全部 PASS。

- [ ] **Step 5: 提交建议**

```bash
git add eval/probes/ eval/tests/test_probes.py
git commit -m "feat(eval): 8 探针定义——条款 ID 绑定、ls/find 漫游靶子、题库变体与 env 注入"
```

> 产物自动提交开关当前=关闭：跳过 `git commit`，只报告上述新增路径，等待维护者确认。

---
## 任务组 4：车道与报告（eval-ci-matrix：tasks 4.1–4.6）

### Task 14: 分夜轮转调度表

**Files:**
- Create: `eval/runner/schedule.py`
- Test: `eval/tests/test_schedule.py`

**Interfaces:**
- Consumes: `prb.CONTROL_PROBES`（Task 13）。
- Produces:
  - `sch.SCHED_START == date(2026, 9, 7)`（首个调度夜，周一；常量同源于设计拍板）
  - `sch.night_index(date_str: str) -> int`——`(date.fromisoformat(date_str) - SCHED_START).days`，**距首个调度日起算的夜序号**（消除 `toordinal` 历法依赖：不随公历周转漂移，负值=首个调度夜之前，Python 模运算仍确定性）
  - `sch.night_plan(date_str: str, agents: list[str]) -> dict`——`{"night": date_str, "parity": "odd"|"even", "probe_ids": [...], "agents": [...], "control_agents": [...2 项，轮换], "v3_agents": [...0 或 2 项，每周], "strong_agents": [...0 或 2 项，每周错峰], "runs": 2, "theme": "orders"|"billing"|"users"}`
  - 调度规则（spec eval-ci-matrix R2；全部以 night_index 为唯一口径）：night_index 奇→P1/P3/P5/P7、偶→P2/P4/P6/P8；对照组每夜轮换 2 端（`agents[night_index % len]`、`agents[(night_index+1) % len]`）；v3 变体每周（`night_index % 7 == 0`）× 轮换 2 端；strong 增补行每周错峰（`night_index % 7 == 3`）× 轮换 2 端（仅配置了 strong_model 的端计入）；theme 按 `night_index % 3` 轮换（题库防过拟合）
  - Task 15（run_night/run_strong_rows）、Task 16（聚合窗口）、Task 20（drill7）消费。

- [ ] **Step 1: 写失败测试**

```python
"""eval/tests/test_schedule.py —— 分夜轮转调度表（tasks 4.3 调度部分）。"""
import unittest

from eval.runner import schedule as sch

AGENTS = ["claude", "codex", "pi", "kimi"]


class TestSchedule(unittest.TestCase):
    def test_parity_probe_sets(self):
        """ut-sch-parity：夜序号奇→P1/P3/P5/P7，偶→P2/P4/P6/P8（SCHED_START=2026-09-07 周一起算）。"""
        # 2026-09-08 夜序号 1（奇）；2026-09-09 夜序号 2（偶）
        odd = sch.night_plan("2026-09-08", AGENTS)
        self.assertEqual(odd["probe_ids"], ["P1", "P3", "P5", "P7"])
        self.assertEqual(odd["parity"], "odd")
        self.assertEqual(odd["runs"], 2)
        even = sch.night_plan("2026-09-09", AGENTS)
        self.assertEqual(even["probe_ids"], ["P2", "P4", "P6", "P8"])
        self.assertEqual(even["parity"], "even")

    def test_control_rotation_covers_all(self):
        """ut-sch-control：对照组每夜 2 端轮换，4 夜（序号 0–3）覆盖全部端。"""
        seen = set()
        for day in range(7, 11):  # 2026-09-07..10：夜序号 0..3
            date_str = f"2026-09-{day:02d}"
            seen.update(sch.night_plan(date_str, AGENTS)["control_agents"])
        self.assertEqual(seen, set(AGENTS))

    def test_v3_weekly_strong_offset(self):
        """ut-sch-weekly：v3 每周（夜序号%7==0）2 端；strong 错峰（%7==3）每周。"""
        days = range(7, 18)  # 2026-09-07..17：夜序号 0..10，覆盖 v3 两夜/strong 两夜
        v3_nights = [d for d in days
                     if sch.night_plan(f"2026-09-{d:02d}", AGENTS)["v3_agents"]]
        self.assertEqual(v3_nights, [7, 14])    # 夜序号 0 与 7
        strong_nights = [d for d in days
                         if sch.night_plan(f"2026-09-{d:02d}", AGENTS)["strong_agents"]]
        self.assertEqual(strong_nights, [10, 17])  # 夜序号 3 与 10（与 v3 错峰）

    def test_theme_rotation(self):
        """ut-sch-theme：题库 theme 三夜轮换（夜序号 0/1/2 → orders/billing/users）。"""
        themes = [sch.night_plan(f"2026-09-{d:02d}", AGENTS)["theme"]
                  for d in range(7, 10)]
        self.assertEqual(sorted(themes), ["billing", "orders", "users"])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 运行确认失败**

```bash
python3 -m unittest eval.tests.test_schedule -v
```

预期：全部 ERROR（`No module named 'eval.runner.schedule'`）。

- [ ] **Step 3: 最小实现**

`eval/runner/schedule.py`：

```python
"""分夜轮转调度表（eval-ci-matrix R2 / oracle 拍板点 3）。

夜序号以 SCHED_START（首个调度夜 2026-09-07，周一）起算：
night_index = (date - SCHED_START).days——历法无关，不随 toordinal 漂移。
"""
from datetime import date

SCHED_START = date(2026, 9, 7)  # 首个调度夜（周一）

ODD_PROBES = ("P1", "P3", "P5", "P7")
EVEN_PROBES = ("P2", "P4", "P6", "P8")
THEMES = ("orders", "billing", "users")


def night_index(date_str: str) -> int:
    """距首个调度日起算的夜序号（负值=首个调度夜之前，模运算仍确定性）。"""
    return (date.fromisoformat(date_str) - SCHED_START).days


def _rotate(agents: list, night: int, offset: int, count: int) -> list:
    if len(agents) <= count:
        return list(agents)
    return [agents[(night + offset + i) % len(agents)] for i in range(count)]


def night_plan(date_str: str, agents: list) -> dict:
    night = night_index(date_str)
    return {
        "night": date_str,
        "parity": "odd" if night % 2 else "even",
        "probe_ids": list(ODD_PROBES if night % 2 else EVEN_PROBES),
        "agents": list(agents),
        "control_agents": _rotate(agents, night, 0, 2),
        "v3_agents": _rotate(agents, night, 2, 2) if night % 7 == 0 else [],
        "strong_agents": _rotate(agents, night, 4, 2) if night % 7 == 3 else [],
        "runs": 2,
        "theme": THEMES[night % len(THEMES)],
    }
```

注：`strong_agents` 为弱模型保证度的端内强模型增补行（spec R3"强弱差值，按端内比较"）；night runner 在 Task 15 的显式函数 `night.run_strong_rows` 中执行 strong 行（同一 `run_single_probe`、`pins` 换 `strong_model`、run_id 后缀 `-strong-0`，report 按 run_id 含 `-strong-` 识别）；本任务先落调度数据面，执行面见 Task 15 Step 6（red→green 用例同步在 Task 15 Step 4）。

- [ ] **Step 4: 运行测试确认通过**

```bash
python3 -m unittest eval.tests.test_schedule -v
```

预期：4 个用例全部 PASS。

- [ ] **Step 5: 提交建议**

```bash
git add eval/runner/schedule.py eval/tests/test_schedule.py
git commit -m "feat(eval): 分夜轮转调度表——探针奇偶/对照组与 v3/strong 每周轮换/theme 轮换"
```

> 产物自动提交开关当前=关闭：跳过 `git commit`，只报告上述两个新增路径，等待维护者确认。

---
### Task 15: 运行器工程面——配置、断点续跑、多层熔断、双 pin 核验、MODEL_DRIFT、保留策略、单夜流水线

**Files:**
- Create: `eval/config/agents.json`、`eval/config/policy.json`、`eval/runner/guards.py`、`eval/runner/night.py`
- Modify: `eval/runner/cli.py`（追加 `night`/`pins-audit` 子命令）
- Test: `eval/tests/test_guards.py`、`eval/tests/test_night.py`

**Interfaces:**
- Consumes: `schedule.night_plan`（Task 14）、`proc.run_cli`/`cli_version_check`（Task 3）、`stage1.run_stage1`（Task 3）、`idem.run_idempotency`（Task 4）、`get_adapter`（Task 6–8）、`assertor.score_run`（Task 9）、`schema.build_result`（Task 12）、`fake.fixture_mcp_config`/`read_calls`（Task 11）、`prb.PROBES`/`probe_env`/`variant_for_night`（Task 13）。
- Produces:
  - `guards.load_config(path: Path) -> dict`
  - `guards.model_drift(traj, pins) -> Optional[str]`——`None`=通过；`"pi-model-change:<ids>"` / `"MODEL_DRIFT:<readback>!<pinned>"` / `"model-unreadable"`（该 run 出矩阵，报告单列）
  - `guards.should_skip(results_dir: Path, run_id: str) -> bool`（结果 JSON 已存在即跳过——断点续跑）
  - `guards.CircuitBreaker(policy: dict)`：`.check(session_count: int, wall_minutes: float, error_streak: int) -> tuple[bool, str]`（多层熔断：轮次上限+墙钟+连续错误；订阅计费无 per-run 成本信号→轮次/时长代理）
  - `guards.apply_retention(nightly_root: Path, keep_nights: int = 7) -> list[str]`——失败 run 全量保留；通过 run 的原始 transcript 超窗清理（保留中间格式+结果 JSON）
  - `guards.update_streak(state_path: Path, agent: str, ok: bool) -> int`、`guards.streak_alerts(state_path: Path) -> list[str]`（连续 3 夜失败端置顶告警）
  - `night.run_night(date_str: str, repo_root: Path, base_dir: Path, config_dir: Optional[Path] = None, mock: bool = False) -> int`——单夜全流程（阶段一+幂等+探针+对照组+strong 增补行+保留策略单次调用+全局配置漂移落盘：真实模式对真实 HOME 首尾快照，mock 模式快照根为 sandbox `base_dir`、不触碰真实 `Path.home()`；报告调用占位→Task 16 接线），退出码 0=正常/缺测，1=红灯（断言/基线，Task 16 报告接入后生效）；真实模式（mock=False）按 HOME 策略 b 方案：CLI 不覆写 HOME（登录态留在真实 HOME），skill 发现路径经 `skill_env` 注入 fixture 隔离 home，对照组探针同用真实 HOME 但**不注入** skill_env（未安装语义）
  - `night.run_single_probe(agent, probe_id, variant_idx, fixture, pins, policy, run_id, results_dir, transcripts_dir, base_dir, theme="orders", mock_bin_dir=None, variant="installed", real_home=False, skill_env=None) -> dict`——单探针执行（env 注入→CLI→适配器→guards→断言→结果落盘）；`transcripts_dir`=原始轨迹与 stdout 捕获（`.eval-*`）落位、`base_dir`=该 fixture 的工作基目录（fake MCP 日志落其下 `mcp-logs/`）；`real_home=True` 时不覆写 HOME（b 方案）并注入 `skill_env`，且传 `session_root=fixture.home`（skill_env 已把 config-dir 重定向到 fixture 根，pi/kimi session 落其下，供 run_cli 定位）
  - `night.run_strong_rows(date_str, plan, agents_cfg, fixtures, policy, runs_dir, transcripts_dir, base_dir, mock_bin_dir=None, real_home=False) -> int`——**strong 增补行显式执行函数**（调度表 `strong_agents` × 全部 8 探针 × 1 run，run_id 后缀 `-strong-0`，report 弱模型矩阵按 `-strong-` 识别；仅执行配置了 `strong_model` 的端；`fixtures` 为 {agent: FixturePaths} 当夜已装 fixture 表；返回实际执行 run 数）
  - Task 16/18/19/20 消费。

- [ ] **Step 1: 写失败测试（guards）**

```python
"""eval/tests/test_guards.py —— 续跑/熔断/漂移/保留/连续失败（tasks 4.1）。"""
import json
import tempfile
import time
import unittest
from pathlib import Path

from eval import ifmt
from eval.runner import guards


def _traj(agent="claude", model="glm-5.3", changes=None):
    traj = ifmt.IntermediateTrajectory(agent=agent)
    traj.model_readback = model
    traj.model_changes = changes or []
    return traj


class TestGuards(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.policy = {"max_sessions_per_night": 2, "max_wall_minutes": 60,
                       "max_error_streak": 3}

    def test_model_drift_detection(self):
        """ut-gd-drift：回读与 pin 不一致 / pi 会话内变更 / 回读缺失 → 出矩阵。"""
        self.assertIsNone(guards.model_drift(_traj(), {"pinned_model": "glm-5.3"}))
        self.assertEqual(guards.model_drift(_traj(model="glm-5.2"),
                                            {"pinned_model": "glm-5.3"}),
                         "MODEL_DRIFT:glm-5.2!=glm-5.3")
        self.assertTrue(guards.model_drift(_traj(agent="pi", changes=["a", "b"]),
                                           {"pinned_model": "glm-5.3"})
                        .startswith("pi-model-change:"))
        self.assertEqual(guards.model_drift(_traj(model=""),
                                            {"pinned_model": "glm-5.3"}),
                         "model-unreadable")

    def test_should_skip_resume(self):
        """ut-gd-resume：结果已存在即跳过（断点续跑）。"""
        runs = self.base / "runs"
        runs.mkdir()
        (runs / "r1.json").write_text("{}", encoding="utf-8")
        self.assertTrue(guards.should_skip(runs, "r1"))
        self.assertFalse(guards.should_skip(runs, "r2"))

    def test_circuit_breaker_layers(self):
        """ut-gd-breaker：轮次/墙钟/连续错误三层熔断。"""
        cb = guards.CircuitBreaker(self.policy)
        self.assertFalse(cb.check(1, 1.0, 0)[0])
        self.assertTrue(cb.check(3, 1.0, 0)[0])       # 轮次上限
        self.assertTrue(cb.check(1, 61.0, 0)[0])      # 墙钟上限
        self.assertTrue(cb.check(1, 1.0, 3)[0])       # 连续错误

    def test_retention_prunes_passed_raw_only(self):
        """ut-gd-retention：通过 run 原始轨迹超窗清理，中间格式与结果保留。"""
        old = time.time() - 8 * 86400
        for verdict, path in (("PASS", self.base / "nightly/2026-08-25"),
                              ("FAIL", self.base / "nightly/2026-08-26")):
            (path / "transcripts").mkdir(parents=True)
            (path / "runs").mkdir(parents=True)
            (path / "transcripts" / "r.raw.jsonl").write_text("x", encoding="utf-8")
            (path / "runs" / "r.json").write_text(json.dumps(
                {"verdict": verdict}), encoding="utf-8")
            ts = old
            for p in path.rglob("*"):
                import os
                os.utime(p, (ts, ts))
        pruned = guards.apply_retention(self.base / "nightly", keep_nights=7)
        self.assertTrue((self.base / "nightly/2026-08-25/runs/r.json").exists())
        self.assertFalse((self.base / "nightly/2026-08-25/transcripts/r.raw.jsonl").exists())
        self.assertTrue((self.base / "nightly/2026-08-26/transcripts/r.raw.jsonl").exists())

    def test_streak_alerts(self):
        """ut-gd-streak：连续 3 夜失败端告警。"""
        state = self.base / "streaks.json"
        for _ in range(3):
            guards.update_streak(state, "kimi", ok=False)
        guards.update_streak(state, "claude", ok=True)
        self.assertEqual(guards.streak_alerts(state), ["kimi"])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 运行确认失败**

```bash
python3 -m unittest eval.tests.test_guards -v
```

预期：全部 ERROR（`No module named 'eval.runner.guards'`）。

- [ ] **Step 3: 最小实现（guards.py + 配置文件）**

`eval/config/agents.json`（初始值来自审计锚点；`pins-audit` 固化后维护者核定；`kimi.enabled=false` 直到单端验证通过；`skill_env` 为 HOME 策略 b 方案的 skill 发现路径注入表——键名为初值假设，Tier-1 首夜以各端实测核定后仅改本数据文件，`{fixture_home}` 占位符由 `night._resolved_skill_env` 替换）：

```json
{
  "claude": {"enabled": true, "executable": "claude", "pinned_model": "glm-5.3",
             "strong_model": "glm-5.3", "cli_version": "2.1.233",
             "capture": "stdout", "max_turns": 40,
             "skill_env": {"CLAUDE_CONFIG_DIR": "{fixture_home}/.claude"}},
  "codex": {"enabled": true, "executable": "codex", "pinned_model": "gpt-5.4",
            "strong_model": null, "cli_version": "", "capture": "stdout",
            "max_turns": null,
            "skill_env": {"CODEX_HOME": "{fixture_home}/.codex"}},
  "pi": {"enabled": true, "executable": "pi", "pinned_model": "glm-5.3",
         "strong_model": null, "cli_version": "", "capture": "session",
         "max_turns": null,
         "skill_env": {"PI_CONFIG_DIR": "{fixture_home}/.pi"}},
  "kimi": {"enabled": false, "executable": "kimi",
           "pinned_model": "kimi-code/kimi-for-coding", "strong_model": null,
           "cli_version": "", "capture": "session", "max_turns": null,
           "skill_env": {"KIMI_CODE_CONFIG_DIR": "{fixture_home}/.kimi-code"}}
}
```

`eval/config/policy.json`：

```json
{
  "runs_per_combo": 2,
  "per_run_timeout_s": 900,
  "stage1_timeout_s": 1200,
  "max_sessions_per_night": 80,
  "max_wall_minutes": 420,
  "max_error_streak": 6,
  "reroute_window": 8,
  "degrade_drop_pp": 20,
  "absolute_floor": 0.70,
  "retention_keep_nights": 7,
  "window_nights": 7,
  "roam_ls_find_max": 5,
  "zh_min_ratio": 0.6
}
```

`eval/runner/guards.py`：

```python
"""运行器工程面：断点续跑、多层熔断、双 pin 核验、MODEL_DRIFT、保留策略。"""
import json
import time
from pathlib import Path
from typing import Optional


def load_config(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def model_drift(traj, pins) -> Optional[str]:
    """模型口径核验（R11）：transcript 实测回读 vs pinned；pi 会话内变更即作废。"""
    if traj.model_changes:
        return "pi-model-change:" + ",".join(traj.model_changes)
    if not traj.model_readback:
        return "model-unreadable"
    if traj.model_readback != (pins or {}).get("pinned_model"):
        return f"MODEL_DRIFT:{traj.model_readback}!={pins.get('pinned_model')}"
    return None


def should_skip(results_dir: Path, run_id: str) -> bool:
    return (results_dir / f"{run_id}.json").is_file()


class CircuitBreaker:
    """多层熔断：轮次上限 + 墙钟 + 连续错误（订阅计费无成本信号→轮次/时长代理）。"""

    def __init__(self, policy: dict):
        self.policy = policy

    def check(self, session_count, wall_minutes, error_streak):
        if session_count >= self.policy.get("max_sessions_per_night", 80):
            return True, f"sessions>={self.policy['max_sessions_per_night']}"
        if wall_minutes >= self.policy.get("max_wall_minutes", 420):
            return True, f"wall_minutes>={self.policy['max_wall_minutes']}"
        if error_streak >= self.policy.get("max_error_streak", 6):
            return True, f"error_streak>={self.policy['max_error_streak']}"
        return False, ""


def apply_retention(nightly_root: Path, keep_nights: int = 7) -> list:
    """失败 run 全量保留；通过 run 的原始 transcript 超窗清理（保留中间格式+结果）。"""
    pruned = []
    cutoff = time.time() - keep_nights * 86400
    for night_dir in sorted(nightly_root.glob("*")):
        if not night_dir.is_dir():
            continue
        for result in night_dir.glob("runs/*.json"):
            try:
                verdict = json.loads(result.read_text(encoding="utf-8")).get("verdict")
            except (OSError, ValueError):
                continue
            run_id = result.stem
            raw_dir = night_dir / "transcripts"
            if verdict in ("PASS",) and raw_dir.is_dir() and \
                    result.stat().st_mtime < cutoff:
                for raw in list(raw_dir.glob(f"{run_id}.*")):
                    pruned.append(str(raw))
                    raw.unlink()
    return pruned


def _load_state(state_path: Path) -> dict:
    if state_path.is_file():
        try:
            return json.loads(state_path.read_text(encoding="utf-8"))
        except ValueError:
            return {}
    return {}


def update_streak(state_path: Path, agent: str, ok: bool) -> int:
    state = _load_state(state_path)
    streaks = state.setdefault("streaks", {})
    streaks[agent] = 0 if ok else int(streaks.get(agent, 0)) + 1
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2),
                          encoding="utf-8")
    return streaks[agent]


def streak_alerts(state_path: Path) -> list:
    return sorted(agent for agent, streak in
                  _load_state(state_path).get("streaks", {}).items() if streak >= 3)
```

- [ ] **Step 4: 写失败测试（night 流水线，mock 模式）**

```python
"""eval/tests/test_night.py —— 单夜流水线（mock CLI：续跑/漂移/strong 行/结果落盘）。"""
import json
import unittest
from pathlib import Path

from eval.fixtures import generator as gen
from eval.runner import night


class TestNightMock(unittest.TestCase):
    def test_run_night_mock_end_to_end(self):
        """ut-night-mock：mock 单夜产出结果 JSON/中间格式/续跑跳过。"""
        import tempfile
        from eval.runner import cli as cli_mod
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            repo = Path(__file__).resolve().parents[2]
            # 2026-09-08：夜序号 1（奇，SCHED_START=2026-09-07 起算）→ P1/P3/P5/P7
            rc = night.run_night("2026-09-08", repo, base, mock=True)
            self.assertEqual(rc, 0)
            nightly = base / "reports" / "nightly" / "2026-09-08"
            results = list((nightly / "runs").glob("*.json"))
            self.assertTrue(results, "无结果 JSON 落盘")
            doc = json.loads(results[0].read_text(encoding="utf-8"))
            self.assertIn(doc["schema_version"], ("1.0",))
            inter = list((nightly).rglob("*.intermediate.json"))
            self.assertTrue(inter, "无中间格式落盘")
            # 断点续跑：重跑同夜，已有结果跳过（runs 数量不翻倍）
            before = len(results)
            rc2 = night.run_night("2026-09-08", repo, base, mock=True)
            self.assertEqual(rc2, 0)
            after = len(list((nightly / "runs").glob("*.json")))
            self.assertEqual(after, before)

    def test_strong_rows_executed(self):
        """ut-night-strong：strong 增补行显式执行（run_id 含 -strong-；未配置 strong_model 的端跳过）。"""
        import tempfile
        from eval.runner import cli as cli_mod
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            repo = Path(__file__).resolve().parents[2]
            bin_dir = cli_mod.mock_bin(base / "bin")
            fx = gen.make_fixture("fresh", base / "fx", repo)
            runs_dir = base / "runs"
            runs_dir.mkdir()
            plan = {"strong_agents": ["claude", "codex"], "theme": "orders"}
            # 仅 claude 配置 strong_model——codex 应被跳过
            agents_cfg = {"claude": {"pinned_model": "glm-5.3",
                                     "strong_model": "glm-5.3-air"},
                          "codex": {"pinned_model": "gpt-5.4", "strong_model": None}}
            policy = {"per_run_timeout_s": 60, "runs_per_combo": 2}
            executed = night.run_strong_rows(
                "2026-09-10", plan, agents_cfg, {"claude": fx, "codex": fx},
                policy, runs_dir, base / "transcripts", base, mock_bin_dir=bin_dir)
            self.assertEqual(executed, 8)  # claude × 8 探针 × 1 run；codex 跳过
            strong = sorted(p.name for p in runs_dir.glob("*-strong-*.json")
                            if not p.name.endswith(".intermediate.json"))
            self.assertEqual(len(strong), 8)
            self.assertTrue(all(n.startswith("2026-09-10-claude-P") for n in strong))

    def test_drifted_run_excluded_marker(self):
        """ut-night-drift：MODEL_DRIFT run 落盘但 verdict 特殊标记。"""
        # 构造：pin 与罐头轨迹模型不一致（mock claude 回读 glm-5.3）
        import tempfile
        from eval.runner import guards
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            repo = Path(__file__).resolve().parents[2]
            cfg_dir = base / "cfg"
            cfg_dir.mkdir()
            agents = json.loads((repo / "eval/config/agents.json").read_text())
            agents["claude"]["pinned_model"] = "other-model"
            (cfg_dir / "agents.json").write_text(json.dumps(agents), encoding="utf-8")
            (cfg_dir / "policy.json").write_text(
                (repo / "eval/config/policy.json").read_text(), encoding="utf-8")
            # 2026-09-09：夜序号 2（偶）→ P2/P4/P6/P8（P2 探针当晚必跑）
            night.run_night("2026-09-09", repo, base, config_dir=cfg_dir, mock=True)
            results = [p for p in (base / "reports/nightly/2026-09-09/runs").glob("*P2*.json")
                       if not p.name.endswith(".intermediate.json")]
            self.assertTrue(results)
            doc = json.loads(results[0].read_text(encoding="utf-8"))
            self.assertEqual(doc["verdict"], "MODEL_DRIFT")
            self.assertIn("MODEL_DRIFT", doc["fail_reason"])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 5: 运行确认失败**

```bash
python3 -m unittest eval.tests.test_night -v
```

预期：全部 ERROR（`No module named 'eval.runner.night'`）。

- [ ] **Step 6: 最小实现（night.py + cli 追加）**

`eval/runner/night.py`：

```python
"""Tier-1 单夜流水线：阶段一安装 + 幂等双跑 + 探针分夜轮转 + 对照组 + 保留。

HOME 策略（b 方案）：真实模式不覆写 HOME（登录态留在真实 HOME），skill 发现
路径经 agents.json 的 skill_env 数据面注入 fixture 隔离 home；真实 HOME 的
用户级配置首尾快照，漂移落 global-config-drift.json（Task 16 报告消费）。

结果目录布局（不入 git）：
  <base>/reports/nightly/<date>/runs/<run_id>.json           结果（schema 1.0）
  <base>/reports/nightly/<date>/runs/<run_id>.intermediate.json 中间格式
  <base>/reports/nightly/<date>/transcripts/<run_id>.<ext>   原始轨迹（分级保留）
  <base>/reports/nightly/<date>/global-config-drift.json   真实 HOME 全局配置漂移
  <base>/reports/state/streaks.json                          连续失败计数
报告聚合由 Task 16 的 report.write_report 接入（本任务预留调用点）。
"""
import json
import shutil
import time
from pathlib import Path
from typing import Optional

from eval import ifmt
from eval.adapters import get_adapter
from eval.fixtures import generator as gen
from eval.install import idempotency, stage1
from eval.mcp import fake_servers as fake
from eval.probes import definitions as prb
from eval.runner import guards, proc
from eval.scoring import assertor

REPORT_SUBDIR = "reports"


def _enabled_agents(agents_cfg: dict) -> list:
    return [name for name, cfg in agents_cfg.items() if cfg.get("enabled")]


def _resolved_skill_env(agents_cfg: dict, agent: str, fixture) -> Optional[dict]:
    """HOME 策略 b 方案：把 agents.json 的 skill_env 模板解析为具体 env。"""
    raw = (agents_cfg.get(agent) or {}).get("skill_env") or {}
    resolved = {key: str(val).replace("{fixture_home}", str(fixture.home))
                for key, val in raw.items()}
    return resolved or None


def _inject_fake_mcp(fixture_root: Path, roles: list, log_dir: Path) -> None:
    if not roles:
        return
    mcp_path = fixture_root / ".mcp.json"
    doc = {}
    if mcp_path.is_file():
        try:
            doc = json.loads(mcp_path.read_text(encoding="utf-8"))
        except ValueError:
            doc = {}
    servers = doc.setdefault("mcpServers", {})
    servers.update(fake.fixture_mcp_config(roles, log_dir))
    mcp_path.write_text(json.dumps(doc, ensure_ascii=False, indent=2),
                        encoding="utf-8")


def _save_run(nightly: Path, run_id: str, result: dict, traj) -> None:
    runs = nightly / "runs"
    runs.mkdir(parents=True, exist_ok=True)
    (runs / f"{run_id}.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    ifmt.dump(traj, runs / f"{run_id}.intermediate.json")


def run_single_probe(agent, probe_id, variant_idx, fixture, pins, policy,
                     run_id, results_dir, transcripts_dir, base_dir, theme="orders",
                     mock_bin_dir=None, variant="installed",
                     real_home=False, skill_env=None) -> dict:
    """单探针执行：env 注入 → CLI → 适配器 → guards → 断言 → 落盘。

    HOME 策略：real_home=True 时不覆写 HOME（真实 HOME，登录态）并注入
    skill_env（skill 发现路径→fixture 隔离 home）；False 时用隔离 fixture.home
    （mock/单测）。stdout 捕获落 transcripts_dir（.eval- 前缀，不进 fixture 根）。
    session 搜索根：real_home 且注入 skill_env 时向 run_cli 传
    session_root=fixture.home（config-dir 已重定向，pi/kimi session 落 fixture 根）；
    对照组（不注入 skill_env）不传——会话落在真实 HOME，按 b 方案刻意不搜索。
    """
    probe = prb.get(probe_id)
    log_dir = base_dir / "mcp-logs" / run_id
    pre_snapshot = idempotency.snapshot_tree(fixture.root)
    if variant == "installed":
        _inject_fake_mcp(fixture.root, probe.get("needs_fake_mcp", []), log_dir)
    prompt_env = prb.probe_env(probe_id, variant_idx, extra={
        "EVAL_STAGE": "probe", "EVAL_CWD": str(fixture.root)})
    prompt = prompt_env["EVAL_PROMPT"].replace("{module}", theme).replace(
        "<fixture>", str(fixture.root))
    out = proc.run_cli(agent, prompt, cwd=fixture.root,
                       home=None if real_home else fixture.home,
                       pins=pins, timeout_s=policy.get("per_run_timeout_s", 900),
                       env_extra=dict(prompt_env, EVAL_PROMPT=prompt),
                       bin_dir=mock_bin_dir, out_dir=transcripts_dir,
                       skill_env=skill_env,
                       session_root=fixture.home if real_home and skill_env else None)
    traj: ifmt.IntermediateTrajectory
    transcript = out.get("transcript_path") or ""
    if transcript and Path(transcript).is_file():
        traj = get_adapter(agent).parse_file(Path(transcript))
    else:
        traj = ifmt.IntermediateTrajectory(agent=agent)
    traj.settings_snapshot = _settings_snapshot(fixture.root)
    drift = guards.model_drift(traj, pins)
    fake_log = fake.read_calls(log_dir) if log_dir.exists() else []
    if drift:
        result = {"schema_version": "1.0", "run_id": run_id, "agent": agent,
                  "model": traj.model_readback, "cli_version": traj.cli_version,
                  "probe_id": probe_id,
                  "rule_clause_ids": list(probe.get("rule_clause_ids", [])),
                  "verdict": "MODEL_DRIFT", "fail_reason": drift,
                  "denials": [vars(d) for d in traj.denials],
                  "transcript_path": transcript,
                  "started_at": traj.started_at, "duration_s": traj.duration_s,
                  "details": {"stderr": out["stderr"][-500:]}}
    else:
        result = assertor.score_run(
            run_id, probe, traj, workspace=fixture.root,
            fake_mcp_log=fake_log, pre_snapshot=pre_snapshot,
            returncode=out["returncode"], stderr=out["stderr"],
            timed_out=out.get("timed_out", False))
        result["variant"] = variant
    transcripts_dir.mkdir(parents=True, exist_ok=True)
    if transcript and Path(transcript).is_file():
        ext = Path(transcript).suffix or ".jsonl"
        shutil.copyfile(transcript, transcripts_dir / f"{run_id}{ext}")
        result["transcript_path"] = str(transcripts_dir / f"{run_id}{ext}")
    _save_run(results_dir.parent, run_id, result, traj)
    return result


def _settings_snapshot(fixture_root: Path) -> dict:
    p = fixture_root / ".claude" / "settings.json"
    if p.is_file():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except ValueError:
            return {}
    return {}


def run_strong_rows(date_str, plan, agents_cfg, fixtures, policy,
                    runs_dir, transcripts_dir, base_dir, mock_bin_dir=None,
                    real_home=False) -> int:
    """strong 增补行执行（每周错峰夜，调度表 strong_agents）：8 探针 × 1 run。

    仅执行配置了 strong_model 的端；复用各端当夜已装 fixture（fixtures[agent]，
    run_night 的 agent 循环采集）；run_id 后缀 -strong-0，report 弱模型矩阵
    按 run_id 含 -strong- 识别；同签名复用 run_single_probe。返回执行 run 数。
    """
    from eval.runner.schedule import night_index
    executed = 0
    for agent in plan.get("strong_agents", []):
        pins = dict(agents_cfg[agent])
        if not pins.get("strong_model"):
            continue  # 未配置 strong 模型的端不计入（调度表规则的执行侧兑付）
        pins["pinned_model"] = pins["strong_model"]
        fx = fixtures[agent]
        skill_env = _resolved_skill_env(agents_cfg, agent, fx) if real_home else None
        for probe_id in prb.PROBES:
            variant_idx = prb.variant_for_night(probe_id, night_index(date_str))
            run_id = f"{date_str}-{agent}-{probe_id}-strong-0"
            if guards.should_skip(runs_dir, run_id):
                continue
            run_single_probe(agent, probe_id, variant_idx, fx, pins, policy,
                             run_id, runs_dir, transcripts_dir,
                             base_dir / "stage1" / date_str / agent,
                             theme=plan.get("theme", "orders"),
                             mock_bin_dir=mock_bin_dir, real_home=real_home,
                             skill_env=skill_env)
            executed += 1
    return executed


def run_night(date_str, repo_root, base_dir, config_dir=None, mock=False) -> int:
    config_dir = config_dir or (repo_root / "eval" / "config")
    agents_cfg = guards.load_config(config_dir / "agents.json")
    policy = guards.load_config(config_dir / "policy.json")
    base_dir = Path(base_dir)
    nightly = base_dir / REPORT_SUBDIR / "nightly" / date_str
    runs_dir = nightly / "runs"
    transcripts_dir = nightly / "transcripts"
    runs_dir.mkdir(parents=True, exist_ok=True)
    from eval.runner.schedule import night_index, night_plan
    plan = night_plan(date_str, _enabled_agents(agents_cfg))
    bin_dir = None
    if mock:
        from eval.runner import cli as cli_mod
        bin_dir = cli_mod.mock_bin(base_dir / "mockbin")
    real_home = not mock  # HOME 策略 b 方案：真实模式不覆写 HOME（登录态可用）
    # 全局配置快照根：真实模式=真实 Path.home()（漂移监测对象）；mock 模式=sandbox
    # base_dir（其下无 GLOBAL_CONFIG_FILES→空快照、零漂移），不触碰真实 Path.home()
    global_root = Path.home() if real_home else base_dir
    global_before = gen.snapshot_global_configs(global_root)  # 首快照（同根首尾可比）
    started = time.time()
    session_count = 0
    error_streak = 0
    breaker = guards.CircuitBreaker(policy)
    agents = plan["agents"]
    fixtures: dict = {}  # {agent: FixturePaths}——strong 增补行复用（run_strong_rows）
    drift_runs = 0
    infra_fails = 0
    for agent in agents:
        pins = dict(agents_cfg[agent])
        if not mock:
            ok_ver, msg = proc.cli_version_check(agent, pins)
            if not ok_ver:
                guards.update_streak(base_dir / REPORT_SUBDIR / "state" / "streaks.json",
                                     agent, ok=False)
                print(f"[night] {agent} 版本锁失败，标 unavailable：{msg}")
                continue
        # 阶段一（全新变体）+ 幂等双跑（mock 模式 verify 以桩注入，不真跑脚本）
        stage_base = base_dir / "stage1" / date_str / agent
        fx = gen.make_fixture("fresh", stage_base, repo_root,
                              theme=plan["theme"])
        fixtures[agent] = fx
        skill_env = _resolved_skill_env(agents_cfg, agent, fx) if real_home else None
        mock_verify = (lambda root: 0) if mock else None
        stage1.run_stage1(agent, fx, pins,
                          timeout_s=policy.get("stage1_timeout_s", 1200),
                          bin_dir=bin_dir, verify=mock_verify, skill_env=skill_env)
        idempotency.run_idempotency(
            agent, fx, pins, passes=2, bin_dir=bin_dir, verify=mock_verify,
            skill_env=skill_env)
        # v3 升级变体：每周（调度表 v3_agents）× 2 端——升级链断言由
        # stage1._detect_variant→assert_stage1 的 v3.* 项承载
        if agent in plan["v3_agents"]:
            v3_base = base_dir / "stage1-v3" / date_str / agent
            v3_fx = gen.make_fixture("v3", v3_base, repo_root,
                                     theme=plan["theme"])
            stage1.run_stage1(agent, v3_fx, pins,
                              timeout_s=policy.get("stage1_timeout_s", 1200),
                              bin_dir=bin_dir, verify=mock_verify,
                              skill_env=_resolved_skill_env(agents_cfg, agent, v3_fx)
                              if real_home else None)
        guards.update_streak(base_dir / REPORT_SUBDIR / "state" / "streaks.json",
                             agent, ok=True)
        # 阶段二：分夜探针 × 2 runs（安装组，复用已装 fixture）
        for probe_id in plan["probe_ids"]:
            variant_idx = prb.variant_for_night(probe_id, night_index(date_str))
            for run_no in range(policy.get("runs_per_combo", 2)):
                run_id = f"{date_str}-{agent}-{probe_id}-installed-{run_no}"
                if guards.should_skip(runs_dir, run_id):
                    continue
                trip, reason = breaker.check(
                    session_count, (time.time() - started) / 60.0, error_streak)
                if trip:
                    print(f"[night] 熔断触发（{reason}），剩余组合次日补跑")
                    return 0
                res = run_single_probe(agent, probe_id, variant_idx, fx, pins,
                                       policy, run_id, runs_dir, transcripts_dir,
                                       base_dir / "stage1" / date_str / agent,
                                       theme=plan["theme"], mock_bin_dir=bin_dir,
                                       real_home=real_home, skill_env=skill_env)
                session_count += 1
                if res["verdict"] == "MODEL_DRIFT":
                    drift_runs += 1
                elif res["verdict"] == "INFRA_FAIL":
                    infra_fails += 1
                    error_streak += 1
                else:
                    error_streak = 0
        # 对照组：轮换 2 端 × 4 规则探针 × 2 runs（未安装 fixture；
        # 真实模式同用真实 HOME 但不注入 skill_env——对照组定义即未安装）
        if agent in plan["control_agents"]:
            ctl_base = base_dir / "control" / date_str / agent
            ctl_fx = gen.make_fixture("control", ctl_base, repo_root,
                                      theme=plan["theme"])
            for probe_id in prb.CONTROL_PROBES:
                variant_idx = prb.variant_for_night(probe_id, night_index(date_str))
                for run_no in range(policy.get("runs_per_combo", 2)):
                    run_id = f"{date_str}-{agent}-{probe_id}-control-{run_no}"
                    if guards.should_skip(runs_dir, run_id):
                        continue
                    run_single_probe(agent, probe_id, variant_idx, ctl_fx, pins,
                                     policy, run_id, runs_dir, transcripts_dir,
                                     ctl_base, theme=plan["theme"],
                                     mock_bin_dir=bin_dir, variant="control",
                                     real_home=real_home)
                    session_count += 1
    # —— 探针循环全部结束后（循环外、正缩进、各只调用一次）——
    # strong 增补行（每周错峰夜）：调度表 strong_agents × 8 探针 × 1 run
    session_count += run_strong_rows(date_str, plan, agents_cfg, fixtures, policy,
                                     runs_dir, transcripts_dir, base_dir,
                                     mock_bin_dir=bin_dir, real_home=real_home)
    # 保留策略单次调用（原先误置对照组双层循环内、且与 session_count 同行——已修正）
    guards.apply_retention(base_dir / REPORT_SUBDIR / "nightly",
                           keep_nights=policy.get("retention_keep_nights", 7))
    # 真实 HOME 全局配置漂移（b 方案）：首尾快照 diff 落盘，Task 16 报告消费
    (nightly / "global-config-drift.json").write_text(json.dumps(
        {"changed": gen.diff_global_configs(
            global_before, gen.snapshot_global_configs(global_root))},
        ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[night] {date_str} 完成：{session_count} 会话；MODEL_DRIFT={drift_runs}；"
          f"INFRA_FAIL={infra_fails}（详情见 runs/*.json）")
    return 0
```

`eval/runner/cli.py` 追加（`build_parser` 内）：

```python
    p = sub.add_parser("night", help="Tier-1 单夜流水线（self-hosted；--mock 冒烟）")
    p.add_argument("--date", required=True)
    p.add_argument("--base", required=True, help="运行基目录（报告落其下 reports/）")
    p.add_argument("--config-dir", default=None)
    p.add_argument("--mock", action="store_true")
    p.set_defaults(func=cmd_night)

    p = sub.add_parser("pins-audit", help="打印四端当前 --version 与模型，固化 agents.json")
    p.set_defaults(func=cmd_pins_audit)
```

处理函数：

```python
def cmd_night(args):
    from eval.runner import night
    return night.run_night(args.date, REPO_ROOT, Path(args.base).resolve(),
                           config_dir=Path(args.config_dir).resolve()
                           if args.config_dir else None, mock=args.mock)


def cmd_pins_audit(args):
    import json
    from eval.runner import proc
    for agent, tmpl in proc.INVOCATIONS.items():
        try:
            out = __import__("subprocess").run(
                [tmpl["argv"][0], "--version"], capture_output=True, text=True,
                timeout=30, shell=False).stdout.strip().splitlines()
            version = out[0] if out else ""
        except Exception as exc:  # noqa: BLE001 —— 探活命令，任何失败都记录
            version = f"检查失败：{exc}"
        print(f'{agent}: "{version}"')
    print("[pins-audit] 将以上版本填入 eval/config/agents.json 的 cli_version 后提交")
    return 0
```

- [ ] **Step 7: 运行测试确认通过**

```bash
python3 -m unittest eval.tests.test_guards eval.tests.test_night -v
python3 -m eval.runner.cli night --date 2026-09-08 --base /tmp/eval-smoke --mock
```

预期：guards 5 个用例、night 3 个用例全部 PASS；mock 单夜退出码 0 且报告目录有结果 JSON与 global-config-drift.json。

- [ ] **Step 8: 提交建议**

```bash
git add eval/config/ eval/runner/guards.py eval/runner/night.py eval/runner/cli.py eval/tests/test_guards.py eval/tests/test_night.py
git commit -m "feat(eval): 运行器工程面——续跑/熔断/双 pin/MODEL_DRIFT/保留/单夜流水线"
```

> 产物自动提交开关当前=关闭：跳过 `git commit`，只报告上述新增路径，等待维护者确认。

### Task 16: 四矩阵聚合 + 双键基线具名 diff + 基线治理 + 对照组差值

**Files:**
- Create: `eval/runner/report.py`、`eval/baselines/README.md`
- Modify: `eval/runner/cli.py`（追加 `report`/`baseline` 子命令）
- Modify: `eval/runner/night.py`（`run_night` 尾部接线 `write_report` 调用；strong 增补行执行已在 Task 15 以显式函数 `run_strong_rows` 落地并在探针循环后调用）
- Test: `eval/tests/test_report.py`

**Interfaces:**
- Consumes: `schema.load_baseline`/`SCHEMA_VERSION`（Task 12）、`guards.load_config`（Task 15）、`schedule.window dates`（Task 14 的 night_plan 口径）、结果 JSON（Task 15 布局：`<base>/reports/nightly/<date>/runs/*.json`）、各夜 `global-config-drift.json`（Task 15 HOME 策略 b 方案产物）。
- Produces:
  - `rep.load_results(nightly_root: Path, window_nights: int = 7, end_date: Optional[str] = None) -> list[dict]`——滚动 7 夜窗口内全部结果（跳过坏行）
  - `rep.aggregate(results: list[dict]) -> dict`——四矩阵 + 双键计数：`{"window": {...}, "adherence": {probe: {agent: {"rate", "n", "missing": bool}}}, "mcp_usage": {...（P2/P6/P7）}, "weak_model": {agent: {"pinned_rate", "strong_rate", "delta", "missing": bool}}, "cross_end": {probe: {"range_pp", "variance", "missing": bool}}, "clause_probe": {clause: {probe: rate}}, "control": {probe: {"installed_rate", "control_rate", "delta_pp"}}}`——`INFRA_FAIL`/`MODEL_DRIFT` 剔除出矩阵（计 skip）；缺测组合 `missing=True` 由渲染层显式表达，不判红
  - `rep.named_diff(agg: dict, baseline: Optional[dict], degrade_drop_pp: float = 20.0, absolute_floor: float = 0.70) -> list[dict]`——双键视图（`probe_agent` + `clause_probe`）降级项：`{"key": "P1@codex", "view": "probe_agent", "baseline": 1.0, "current": 0.6, "drop_pp": 40.0, "red": True, "clause_file": "code-reading-coding.md"}`；红灯条件=降幅 ≥ `degrade_drop_pp` 个百分点 **或** 现值 < `absolute_floor`；基线缺失/缺测不判红
  - `rep.render_markdown(agg: dict, diff: list[dict], baseline_note: Optional[str], streaks: list[str], global_drift: Optional[dict] = None) -> str`——含具名降级行 `▼ P1检索@Codex: 100%→60%`、缺测标注 `—缺测`、对照组差值行 `安装组 92% vs 对照组 40%`、连续失败端置顶告警、全局配置漂移节（按夜列变更路径，观测不判红）
  - `rep.control_delta`（内含于 aggregate["control"]）
  - `rep.write_report(base_dir: Path, baseline_path: Optional[Path], config_dir: Optional[Path] = None, end_date: Optional[str] = None) -> int`——产出 `<base>/reports/eval/<end_date>/report.{json,md}`，返回 0/1（1=具名降级红灯或窗口无数据）；报告含 `global_config_drift` 节（滚动窗口内各夜真实 HOME 全局配置漂移清单，观测不判红）；**绝不写基线文件**
  - `rep.candidate_baseline(base_dir: Path, out_path: Path, end_date: Optional[str] = None) -> int`——从当前 7 夜窗口生成候选基线 `{"schema_version": "1.0", "created_at", "probe_agent", "clause_probe", "control"}`，维护者审阅后显式提交为 `eval/baselines/baseline.json` 才生效
  - Task 19（workflow 调 `report`）、Task 20（`baseline` 首轮）消费。

- [ ] **Step 1: 写失败测试**

```python
"""eval/tests/test_report.py —— 四矩阵/双键 diff/基线治理/对照组差值（tasks 4.4、1.4）。"""
import json
import tempfile
import unittest
from pathlib import Path

from eval.runner import report as rep


def _result(date, agent, probe, verdict, variant="installed", model="pinned",
            clauses=("code-reading-coding.md#cadence-tools[0]",)):
    _result.seq += 1  # verdict 序号：同夜同端同探针多行不互覆（落盘文件名唯一）
    return {"schema_version": "1.0",
            "run_id": f"{date}-{agent}-{probe}-{variant}-{_result.seq}",
            "agent": agent, "model": model, "cli_version": None, "probe_id": probe,
            "rule_clause_ids": list(clauses),
            "verdict": verdict, "fail_reason": "", "denials": [],
            "transcript_path": "", "started_at": date, "duration_s": 10.0,
            "details": {}, "variant": variant}


_result.seq = 0  # 模块级自增序号（消同名覆盖）


class TestReport(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)

    def _results(self):
        rows = []
        for agent in ("claude", "codex"):
            for v in ("PASS", "PASS", "FAIL"):
                rows.append(_result("2026-09-02", agent, "P1", v))
                rows.append(_result("2026-09-03", agent, "P1", v))
        rows.append(_result("2026-09-02", "claude", "P1", "INFRA_FAIL"))
        rows.append(_result("2026-09-02", "claude", "P1", "MODEL_DRIFT"))
        rows.append(_result("2026-09-02", "codex", "P6", "PASS"))
        for v in ("PASS", "PASS", "PASS", "FAIL"):
            rows.append(_result("2026-09-02", "claude", "P1", v, variant="control"))
        return rows

    def test_aggregate_excludes_infra_and_drift(self):
        """ut-rep-exclude：INFRA/MODEL_DRIFT 出矩阵；比率=PASS/(PASS+FAIL)。"""
        agg = rep.aggregate(self._results())
        cell = agg["adherence"]["P1"]["claude"]
        # 安装组 P1@claude：两日各 PASS,PASS,FAIL → 4 PASS / 6 有效（INFRA/DRIFT 剔除）
        self.assertAlmostEqual(cell["rate"], 4 / 6)
        self.assertEqual(cell["n"], 6)

    def test_missing_cell_flagged_not_red(self):
        """ut-rep-missing：缺测组合标 missing，不产生红灯。"""
        agg = rep.aggregate(self._results())
        cell = agg["adherence"]["P6"]["claude"]
        self.assertTrue(cell["missing"])
        self.assertIsNone(cell["rate"])

    def test_control_delta(self):
        """ut-rep-control：安装组 vs 对照组差值（规则边际效应）。"""
        agg = rep.aggregate(self._results())
        ctl = agg["control"]["P1"]
        # 安装组 4/6；对照组 PASS,PASS,PASS,FAIL → 3/4 = 0.75；Δ = -8.3pp（合成数据允诉负值）
        self.assertAlmostEqual(ctl["installed_rate"], 4 / 6)
        self.assertAlmostEqual(ctl["control_rate"], 0.75)
        self.assertAlmostEqual(ctl["delta_pp"], round((4 / 6 - 0.75) * 100, 1))

    def test_named_diff_double_key_red(self):
        """ut-rep-diff：双键降级红灯（条款×探针定位规则文件）。"""
        rows = self._results() + [
            _result("2026-09-03", "claude", "P1", "FAIL"),
            _result("2026-09-03", "claude", "P1", "FAIL"),
            _result("2026-09-03", "claude", "P1", "FAIL")]
        agg = rep.aggregate(rows)  # P1@claude = 4/9 ≈ 44%：跌 56pp 且低于 70% 下限
        baseline = {"schema_version": "1.0",
                    "probe_agent": {"P1": {"claude": 1.0, "codex": 1.0}},
                    "clause_probe": {"code-reading-coding.md#cadence-tools[0]":
                                     {"P1": 1.0}}}
        diff = rep.named_diff(agg, baseline, degrade_drop_pp=20.0, absolute_floor=0.70)
        keys = {(d["view"], d["key"]) for d in diff if d["red"]}
        self.assertIn(("probe_agent", "P1@claude"), keys)
        clause_rows = [d for d in diff
                       if d["view"] == "clause_probe" and d["red"]]
        self.assertTrue(clause_rows)
        self.assertEqual(clause_rows[0]["clause_file"],
                         "code-reading-coding.md")

    def test_named_diff_baseline_missing_not_red(self):
        """ut-rep-nobaseline：无基线时只报当前值，不判红。"""
        agg = rep.aggregate(self._results())
        diff = rep.named_diff(agg, None)
        self.assertTrue(diff)
        self.assertTrue(all(not d["red"] for d in diff))

    def test_write_report_exit_and_baseline_untouched(self):
        """ut-rep-write：红灯 exit 1；基线文件零改写（治理：仅维护者提交）。"""
        night_dir = self.base / "reports/nightly/2026-09-02"
        runs = night_dir / "runs"
        runs.mkdir(parents=True)
        for row in self._results():
            (runs / f"{row['run_id']}.json").write_text(
                json.dumps(row), encoding="utf-8")
        (night_dir / "global-config-drift.json").write_text(
            json.dumps({"changed": [str(self.base / ".claude/settings.json")]}),
            encoding="utf-8")
        baseline = self.base / "baseline.json"
        baseline.write_text(json.dumps({"schema_version": "1.0",
                                        "probe_agent": {"P1": {"claude": 1.0}},
                                        "clause_probe": {}}), encoding="utf-8")
        before = baseline.read_text(encoding="utf-8")
        code = rep.write_report(self.base, baseline, end_date="2026-09-03")
        # P1@claude = 4/6 ≈ 67%：跌 33pp（超 20pp 阈值）且低于 70% 下限 → 红灯 exit 1
        self.assertEqual(code, 1)
        self.assertEqual(baseline.read_text(encoding="utf-8"), before)
        out_md = next((self.base / "reports/eval").glob("*/report.md"))
        text = out_md.read_text(encoding="utf-8")
        self.assertIn("缺测", text)
        self.assertIn("全局配置漂移", text)

    def test_candidate_baseline_schema(self):
        """ut-rep-candidate：候选基线含双键与 schema_version。"""
        runs = self.base / "reports/nightly/2026-09-02/runs"
        runs.mkdir(parents=True)
        for row in self._results():
            (runs / f"{row['run_id']}.json").write_text(
                json.dumps(row), encoding="utf-8")
        out = self.base / "candidate.json"
        self.assertEqual(rep.candidate_baseline(self.base, out,
                                                end_date="2026-09-03"), 0)
        doc = json.loads(out.read_text(encoding="utf-8"))
        self.assertEqual(doc["schema_version"], "1.0")
        self.assertIn("probe_agent", doc)
        self.assertIn("clause_probe", doc)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 运行确认失败**

```bash
python3 -m unittest eval.tests.test_report -v
```

预期：全部 ERROR（`No module named 'eval.runner.report'`）。

- [ ] **Step 3: 最小实现**

`eval/runner/report.py`：

```python
"""四矩阵聚合、双键基线具名 diff、基线治理与对照组差值（eval-ci-matrix R3）。

治理规则：基线仅在维护者显式提交 eval/baselines/baseline.json 后生效；
夜间只对比不改基线；主版本不匹配的基线不参与 diff 并显式标注。
"""
import json
from datetime import date, timedelta
from pathlib import Path
from typing import Optional

from eval.scoring import schema

MCP_PROBES = ("P2", "P6", "P7")
PROBE_NAMES = {"P1": "P1检索", "P2": "P2文档", "P3": "P3时序", "P4": "P4语言",
               "P5": "P5产物", "P6": "P6时间", "P7": "P7图片", "P8": "P8幂等"}


def load_results(nightly_root: Path, window_nights: int = 7,
                 end_date: Optional[str] = None) -> list:
    end = date.fromisoformat(end_date) if end_date else date.today()
    rows = []
    for offset in range(window_nights):
        day = (end - timedelta(days=offset)).isoformat()
        for path in sorted((nightly_root / day / "runs").glob("*.json")):
            try:
                doc = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            if isinstance(doc, dict) and "run_id" in doc:
                rows.append(doc)
    return rows


def _rate(cells: list) -> dict:
    valid = [r for r in cells if r.get("verdict") in ("PASS", "FAIL")]
    if not valid:
        return {"rate": None, "n": 0, "missing": True}
    passed = sum(1 for r in valid if r["verdict"] == "PASS")
    return {"rate": passed / len(valid), "n": len(valid), "missing": False}


def aggregate(results: list) -> dict:
    agents = sorted({r["agent"] for r in results}) or ["claude"]
    probes = sorted({r["probe_id"] for r in results}) or ["P1"]
    installed = [r for r in results if r.get("variant", "installed") == "installed"]
    control = [r for r in results if r.get("variant") == "control"]
    adherence, mcp_usage, clause_probe = {}, {}, {}
    for probe in probes:
        adherence[probe] = {}
        for agent in agents:
            adherence[probe][agent] = _rate(
                [r for r in installed
                 if r["probe_id"] == probe and r["agent"] == agent])
        if probe in MCP_PROBES:
            mcp_usage[probe] = {agent: adherence[probe].get(
                agent, {"rate": None, "n": 0, "missing": True})
                for agent in agents}
    for row in installed:
        if row.get("verdict") not in ("PASS", "FAIL"):
            continue
        for clause in row.get("rule_clause_ids", []):
            slot = clause_probe.setdefault(clause, {})
            slot.setdefault(row["probe_id"], []).append(row)
    clause_rates = {clause: {probe: _rate(rows) for probe, rows in slots.items()}
                    for clause, slots in clause_probe.items()}
    # 弱模型保证度：pinned 行 vs strong 行（run_id 含 -strong- 后缀）
    weak_model = {}
    for agent in agents:
        pinned = _rate([r for r in installed if r["agent"] == agent
                        and "-strong-" not in r["run_id"]])
        strong = _rate([r for r in installed if r["agent"] == agent
                        and "-strong-" in r["run_id"]])
        delta = (None if pinned["rate"] is None or strong["rate"] is None
                 else round((pinned["rate"] - strong["rate"]) * 100, 1))
        weak_model[agent] = {"pinned_rate": pinned["rate"], "strong_rate": strong["rate"],
                             "delta_pp": delta,
                             "missing": pinned["missing"] or strong["missing"]}
    cross_end = {}
    for probe in probes:
        rates = [adherence[probe][a]["rate"] for a in agents
                 if not adherence[probe][a]["missing"]]
        if len(rates) < 2:
            cross_end[probe] = {"range_pp": None, "variance": None, "missing": True}
        else:
            mean = sum(rates) / len(rates)
            cross_end[probe] = {
                "range_pp": round((max(rates) - min(rates)) * 100, 1),
                "variance": round(sum((x - mean) ** 2 for x in rates) / len(rates), 4),
                "missing": False}
    control_out = {}
    for probe in sorted({r["probe_id"] for r in control}):
        inst = _rate([r for r in installed if r["probe_id"] == probe])
        ctl = _rate([r for r in control if r["probe_id"] == probe])
        delta = (None if inst["rate"] is None or ctl["rate"] is None
                 else round((inst["rate"] - ctl["rate"]) * 100, 1))
        control_out[probe] = {"installed_rate": inst["rate"],
                              "control_rate": ctl["rate"], "delta_pp": delta}
    return {"adherence": adherence, "mcp_usage": mcp_usage,
            "weak_model": weak_model, "cross_end": cross_end,
            "clause_probe": clause_rates, "control": control_out}


def named_diff(agg, baseline, degrade_drop_pp=20.0, absolute_floor=0.70):
    diff = []
    if not baseline:
        for probe, cells in agg["adherence"].items():
            for agent, cell in cells.items():
                if not cell["missing"]:
                    diff.append({"view": "probe_agent", "key": f"{probe}@{agent}",
                                 "baseline": None, "current": cell["rate"],
                                 "drop_pp": None, "red": False, "clause_file": None})
        return diff
    for probe, cells in baseline.get("probe_agent", {}).items():
        for agent, base_rate in cells.items():
            cell = agg["adherence"].get(probe, {}).get(agent)
            if cell is None or cell["missing"]:
                continue
            drop = round((base_rate - cell["rate"]) * 100, 1)
            red = drop >= degrade_drop_pp or cell["rate"] < absolute_floor
            diff.append({"view": "probe_agent", "key": f"{probe}@{agent}",
                         "baseline": base_rate, "current": cell["rate"],
                         "drop_pp": drop, "red": red, "clause_file": None})
    for clause, probes in baseline.get("clause_probe", {}).items():
        for probe, base_rate in probes.items():
            cell = agg["clause_probe"].get(clause, {}).get(probe)
            if cell is None or cell["missing"]:
                continue
            drop = round((base_rate - cell["rate"]) * 100, 1)
            red = drop >= degrade_drop_pp or cell["rate"] < absolute_floor
            diff.append({"view": "clause_probe", "key": f"{clause}#{probe}",
                         "baseline": base_rate, "current": cell["rate"],
                         "drop_pp": drop, "red": red,
                         "clause_file": clause.split("#")[0]})
    return diff


def render_markdown(agg, diff, baseline_note=None, streaks=None, global_drift=None):
    lines = ["# eval 夜间报告（滚动 7 夜聚合）", ""]
    if streaks:
        lines.append("## ⚠️ 置顶告警：连续 ≥3 夜失败端")
        lines += [f"- **{agent}**：连续失败，请检查登录态/配额/适配器" for agent in streaks]
        lines.append("")
    if baseline_note:
        lines.append(f"> {baseline_note}")
        lines.append("")
    lines.append("## 1. 规则遵循率矩阵（探针 × 端）")
    lines.append("| 探针 | " + " | ".join(sorted(next(iter(agg["adherence"].values()),
                                                 {}))) + " |")
    agents = sorted(next(iter(agg["adherence"].values()), {}))
    lines.append("|---" * (len(agents) + 1) + "|")
    for probe, cells in sorted(agg["adherence"].items()):
        row = [PROBE_NAMES.get(probe, probe)]
        for agent in agents:
            cell = cells.get(agent, {"missing": True})
            row.append("—缺测" if cell.get("missing")
                       else f"{cell['rate'] * 100:.0f}%（n={cell['n']}）")
        lines.append("| " + " | ".join(row) + " |")
    lines.append("")
    lines.append("## 2. MCP 使用率（P2/P6/P7 × 端）")
    for probe, cells in sorted(agg["mcp_usage"].items()):
        for agent, cell in sorted(cells.items()):
            if not cell.get("missing"):
                lines.append(f"- {PROBE_NAMES.get(probe, probe)}@{agent}："
                             f"{cell['rate'] * 100:.0f}%（n={cell['n']}）")
    lines.append("")
    lines.append("## 3. 弱模型保证度（端内 pinned vs strong 差值，pp）")
    for agent, cell in sorted(agg["weak_model"].items()):
        if not cell.get("missing"):
            lines.append(f"- {agent}：pinned {cell['pinned_rate'] * 100:.0f}% vs "
                         f"strong {cell['strong_rate'] * 100:.0f}%，Δ={cell['delta_pp']}pp")
        else:
            lines.append(f"- {agent}：—缺测（strong 行未配置或未跑）")
    lines.append("")
    lines.append("## 4. 跨端一致性（各端 pinned 口径：极差/方差）")
    for probe, cell in sorted(agg["cross_end"].items()):
        if not cell.get("missing"):
            lines.append(f"- {PROBE_NAMES.get(probe, probe)}：极差 {cell['range_pp']}pp，"
                         f"方差 {cell['variance']}")
        else:
            lines.append(f"- {PROBE_NAMES.get(probe, probe)}：—缺测")
    lines.append("")
    lines.append("## 5. 对照组差值（规则边际效应）")
    for probe, cell in sorted(agg["control"].items()):
        if cell["delta_pp"] is not None:
            lines.append(f"- {PROBE_NAMES.get(probe, probe)}：安装组 "
                         f"{cell['installed_rate'] * 100:.0f}% vs 对照组 "
                         f"{cell['control_rate'] * 100:.0f}%（Δ{cell['delta_pp']}pp）")
    lines.append("")
    lines.append("## 6. 全局配置漂移（真实 HOME，HOME 策略 b 方案；观测不判红）")
    if global_drift:
        for day in sorted(global_drift):
            lines.append(f"- {day}：" + "、".join(global_drift[day][:10]))
    else:
        lines.append("- 窗口内无漂移（或非 Tier-1 真实模式）")
    lines.append("")
    red_rows = [d for d in diff if d["red"]]
    lines.append("## 7. 基线具名 diff（红灯=降幅超阈值或低于下限）")
    if not diff:
        lines.append("- 无基线可比（首次运行或 schema 不兼容）")
    for d in diff:
        name = d["key"]
        if d["view"] == "probe_agent":
            probe, agent = d["key"].split("@")
            name = f"{PROBE_NAMES.get(probe, probe)}@{agent}"
        mark = "▼" if d["red"] else "·"
        base_txt = f"{d['baseline'] * 100:.0f}%" if d["baseline"] is not None else "—"
        cur_txt = f"{d['current'] * 100:.0f}%" if d["current"] is not None else "—"
        lines.append(f"- {mark} {name}: {base_txt}→{cur_txt}"
                     + (f"（{d['clause_file']}）" if d.get("clause_file") else ""))
    if red_rows:
        lines.append("")
        lines.append(f"**红灯 {len(red_rows)} 项**")
    return "\n".join(lines) + "\n"


def _load_global_drift(nightly_root: Path, window_nights: int = 7,
                       end_date: Optional[str] = None) -> dict:
    """滚动窗口内各夜真实 HOME 全局配置漂移（HOME 策略 b 方案，观测不判红）。"""
    end = date.fromisoformat(end_date) if end_date else date.today()
    out = {}
    for offset in range(window_nights):
        day = (end - timedelta(days=offset)).isoformat()
        path = nightly_root / day / "global-config-drift.json"
        if path.is_file():
            try:
                changed = json.loads(path.read_text(encoding="utf-8")).get("changed", [])
            except (OSError, ValueError):
                continue
            if changed:
                out[day] = changed
    return out


def write_report(base_dir, baseline_path, config_dir=None, end_date=None) -> int:
    base_dir = Path(base_dir)
    policy = {"degrade_drop_pp": 20.0, "absolute_floor": 0.70, "window_nights": 7}
    if config_dir:
        policy.update(json.loads((Path(config_dir) / "policy.json").read_text(
            encoding="utf-8")))
    results = load_results(base_dir / "reports" / "nightly",
                           window_nights=policy["window_nights"], end_date=end_date)
    if not results:
        print("[report] 窗口内无结果数据")
        return 1
    agg = aggregate(results)
    baseline, note = (None, None)
    if baseline_path and Path(baseline_path).is_file():
        baseline, note = schema.load_baseline(Path(baseline_path))
        if note:
            print(f"[report] {note}")
    diff = named_diff(agg, baseline,
                      degrade_drop_pp=policy["degrade_drop_pp"],
                      absolute_floor=policy["absolute_floor"])
    from eval.runner import guards
    streaks = guards.streak_alerts(base_dir / "reports" / "state" / "streaks.json")
    end_day = end_date or date.today().isoformat()
    global_drift = _load_global_drift(base_dir / "reports" / "nightly",
                                      window_nights=policy["window_nights"],
                                      end_date=end_day)
    md = render_markdown(agg, diff, baseline_note=note, streaks=streaks,
                         global_drift=global_drift)
    out_dir = base_dir / "reports" / "eval" / end_day
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "report.json").write_text(
        json.dumps({"aggregate": agg, "diff": diff,
                    "global_config_drift": global_drift},
                   ensure_ascii=False, indent=2),
        encoding="utf-8")
    (out_dir / "report.md").write_text(md, encoding="utf-8")
    red = [d for d in diff if d["red"]]
    print(f"[report] 输出 {out_dir}/report.md；红灯 {len(red)} 项")
    return 1 if red else 0


def candidate_baseline(base_dir, out_path, end_date=None) -> int:
    base_dir = Path(base_dir)
    results = load_results(base_dir / "reports" / "nightly", end_date=end_date)
    if not results:
        print("[baseline] 窗口内无结果数据")
        return 1
    agg = aggregate(results)
    probe_agent = {probe: {agent: cell["rate"] for agent, cell in cells.items()
                           if not cell["missing"]}
                   for probe, cells in agg["adherence"].items()}
    clause_probe = {clause: {probe: cell["rate"] for probe, cell in slots.items()
                             if not cell["missing"]}
                    for clause, slots in agg["clause_probe"].items()}
    doc = {"schema_version": schema.SCHEMA_VERSION,
           "created_at": date.today().isoformat(),
           "probe_agent": probe_agent, "clause_probe": clause_probe,
           "control": agg["control"]}
    Path(out_path).write_text(json.dumps(doc, ensure_ascii=False, indent=2),
                              encoding="utf-8")
    print(f"[baseline] 候选基线已生成：{out_path}（审阅后提交为 "
          "eval/baselines/baseline.json 才生效）")
    return 0
```

`eval/baselines/README.md`：

```markdown
# 基线治理

- 基线文件：`baseline.json`（仅本目录；schema_version 与结果契约同源，当前 1.0）。
- 生效条件：**仅维护者显式 git 提交后生效**；夜间运行只对比、绝不改写基线。
- 更新流程：`python3 -m eval.runner.cli baseline --base <夜跑基目录> --out
  eval/baselines/baseline.candidate.json` → 人工审阅 → 复制为 `baseline.json` 提交。
- 主版本不匹配的基线不参与 diff，报告显式标注"基线 schema 不兼容，本次不比对"。
```

`eval/runner/cli.py` 追加（`build_parser` 内与处理函数）：

```python
    p = sub.add_parser("report", help="四矩阵聚合 + 双键基线具名 diff")
    p.add_argument("--base", required=True)
    p.add_argument("--baseline", default="eval/baselines/baseline.json")
    p.add_argument("--config-dir", default=None)
    p.set_defaults(func=cmd_report)

    p = sub.add_parser("baseline", help="生成候选基线（维护者审阅后显式提交）")
    p.add_argument("--base", required=True)
    p.add_argument("--out", required=True)
    p.set_defaults(func=cmd_baseline)
```

```python
def cmd_report(args):
    from eval.runner import report
    return report.write_report(Path(args.base).resolve(),
                               Path(args.baseline) if args.baseline else None,
                               config_dir=Path(args.config_dir).resolve()
                               if args.config_dir else None)


def cmd_baseline(args):
    from eval.runner import report
    return report.candidate_baseline(Path(args.base).resolve(),
                                     Path(args.out).resolve())
```

并在 `night.run_night` 尾部接线报告调用（strong 增补行的执行已由 Task 15 的显式函数
`run_strong_rows` 落地——探针循环全部结束后、保留策略之前调用；本任务仅把
`run_night` 末尾的 `return 0` 替换为报告调用，使 run_night 的红灯退出码语义生效）：

```python
    # —— 探针循环全部结束后（Task 15 既有代码不动）：strong 行→保留→漂移落盘——
    print(f"[night] {date_str} 完成：{session_count} 会话；MODEL_DRIFT={drift_runs}；"
          f"INFRA_FAIL={infra_fails}（详情见 runs/*.json）")
    from eval.runner import report as rep
    # 单夜自含报告（不带基线；基线 diff 与红灯门禁由 workflow 的 `cli report`
    # 步骤显式执行，避免与 run_night 内嵌调用双重判基线）
    return rep.write_report(base_dir, baseline_path=None,
                            config_dir=config_dir, end_date=date_str)
```

（`write_report` 读取本夜 `global-config-drift.json` 与滚动窗口内结果 JSON；断点续跑夜全部 skip 时窗口仍有历史数据，报告照常产出，不因缺新数据误红。）

- [ ] **Step 4: 运行测试确认通过**

```bash
python3 -m unittest eval.tests.test_report -v
```

预期：7 个用例全部 PASS。

- [ ] **Step 5: 提交建议**

```bash
git add eval/runner/report.py eval/runner/cli.py eval/baselines/ eval/tests/test_report.py
git commit -m "feat(eval): 四矩阵聚合、双键基线具名 diff 与基线治理（对照组差值/缺测表达）"
```

> 产物自动提交开关当前=关闭：跳过 `git commit`，只报告上述新增路径，等待维护者确认。

### Task 17: 既有 session 审计表（第五张观测表）+ 报告目录不入 git

**Files:**
- Create: `eval/runner/audit.py`
- Modify: `eval/runner/cli.py`（追加 `audit` 子命令）
- Modify: `.gitignore`（追加一行 `cadence/reports/eval/`）
- Test: `eval/tests/test_audit.py`

**Interfaces:**
- Consumes: `get_adapter`（Task 6–8 离线解析复用——同一套代码只换输入源）、`assertor.bash_heads`/`zh_ratio`（Task 9）。
- Produces:
  - `aud.audit_dirs(paths: dict[str, Path], limit_per_agent: int = 200, glob_patterns: Optional[dict[str, list[str]]] = None) -> dict`——`{"per_agent": {agent: {"sessions", "tools", "bash_heads", "models", "denials", "durations"}}, "totals": {...}}`（工具分布/Bash 命令头分布/模型标签分布/时长统计）
  - `aud.write_audit(out_dir: Path, data: dict) -> Path`——输出 `audit.{json,md}` 至 `cadence/reports/eval/audit/<日期>/`（**不入 git、不进 gate、不入基线**；含业务项目路径与任务内容）
  - Task 19 文档引用（维护者手动/周度执行）、Task 20 演练消费。

- [ ] **Step 1: 写失败测试**

```python
"""eval/tests/test_audit.py —— 既有 session 审计表（tasks 4.6 / oracle §2-d）。"""
import json
import tempfile
import unittest
from pathlib import Path

from eval.runner import audit as aud

TRANS = Path(__file__).resolve().parents[1] / "transcripts"


class TestAudit(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)

    def test_audit_fabricated_home(self):
        """ut-aud-scan：伪造 HOME 树——工具分布/命令头/模型分布可统计。"""
        claude_dir = self.base / "projects" / "proj-a"
        claude_dir.mkdir(parents=True)
        (claude_dir / "s1.jsonl").write_text(
            (TRANS / "claude" / "golden-1.jsonl").read_text(encoding="utf-8"),
            encoding="utf-8")
        data = aud.audit_dirs({"claude": self.base / "projects"}, limit_per_agent=10)
        per = data["per_agent"]["claude"]
        self.assertEqual(per["sessions"], 1)
        self.assertGreaterEqual(per["tools"]["Bash"], 1)
        self.assertIn("mcp__codegraph__codegraph_explore", per["tools"])
        self.assertEqual(per["bash_heads"]["ls -R src"], 1)
        self.assertEqual(per["models"]["glm-5.3"], 1)
        self.assertEqual(per["denials"], 1)

    def test_limit_per_agent(self):
        """ut-aud-limit：每端扫描上限（313MB～1.6GB 存量不可全量解析）。"""
        claude_dir = self.base / "projects"
        claude_dir.mkdir(parents=True)
        golden = (TRANS / "claude" / "golden-1.jsonl").read_text(encoding="utf-8")
        for i in range(5):
            (claude_dir / f"s{i}.jsonl").write_text(golden, encoding="utf-8")
        data = aud.audit_dirs({"claude": claude_dir}, limit_per_agent=2)
        self.assertEqual(data["per_agent"]["claude"]["sessions"], 2)

    def test_write_audit_outputs(self):
        """ut-aud-write：json+md 双产物；md 含观测定位声明（不进 gate）。"""
        claude_dir = self.base / "projects"
        claude_dir.mkdir(parents=True)
        (claude_dir / "s1.jsonl").write_text(
            (TRANS / "claude" / "golden-1.jsonl").read_text(encoding="utf-8"),
            encoding="utf-8")
        data = aud.audit_dirs({"claude": claude_dir})
        out = aud.write_audit(self.base / "out", data)
        md = (out / "audit.md").read_text(encoding="utf-8")
        self.assertIn("仅作观测参考", md)
        self.assertTrue((out / "audit.json").is_file())

    def test_gitignore_covers_reports(self):
        """ut-aud-gitignore：.gitignore 覆盖 cadence/reports/eval/（不入 git）。"""
        text = Path(".gitignore").read_text(encoding="utf-8")
        self.assertIn("cadence/reports/eval/", text)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 运行确认失败**

```bash
python3 -m unittest eval.tests.test_audit -v
```

预期：前三个用例 ERROR（`No module named 'eval.runner.audit'`），`ut-aud-gitignore` FAIL（.gitignore 未含该行）。

- [ ] **Step 3: 最小实现**

`.gitignore` 末尾追加：

```gitignore

# eval 运行时产物（夜间报告/审计表，含业务路径与任务内容，不入 git）
cadence/reports/eval/
```

`eval/runner/audit.py`：

```python
"""既有 session 审计表（第五张观测表）：复用四端适配器离线解析本机存量。

定位（oracle §2-d / eval-ci-matrix R6）：真实生产分布的观测参考——
不进 gate、不入基线、不入 git；不替代受控探针（样本非受控）。
"""
import json
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Optional

from eval.adapters import get_adapter
from eval.scoring.assertor import bash_heads

DEFAULT_GLOBS = {
    "claude": ["**/*.jsonl"],
    "codex": ["**/rollout-*.jsonl"],
    "pi": ["**/session.jsonl"],
    "kimi": ["**/wire.jsonl"],
}


def audit_dirs(paths, limit_per_agent=200, glob_patterns=None) -> dict:
    glob_patterns = glob_patterns or DEFAULT_GLOBS
    per_agent = {}
    for agent, root in paths.items():
        root = Path(root)
        adapter = get_adapter(agent)
        files = []
        for pattern in glob_patterns.get(agent, ["**/*.jsonl"]):
            files.extend(root.glob(pattern))
        files = sorted(files, key=lambda p: p.stat().st_mtime, reverse=True)
        files = files[:limit_per_agent]
        tools, heads, models = Counter(), Counter(), Counter()
        denials = 0
        durations = []
        for path in files:
            try:
                traj = adapter.parse_file(path)
            except (OSError, ValueError):
                continue
            tools.update(c.tool for c in traj.tool_calls)
            heads.update(bash_heads(traj))
            if traj.model_readback:
                models[traj.model_readback] += 1
            denials += len(traj.denials)
            if traj.duration_s:
                durations.append(traj.duration_s)
        per_agent[agent] = {
            "sessions": len(files),
            "tools": dict(tools.most_common(20)),
            "bash_heads": dict(heads.most_common(20)),
            "models": dict(models.most_common(10)),
            "denials": denials,
            "durations": {"median": sorted(durations)[len(durations) // 2]
                          if durations else None,
                          "p90": sorted(durations)[int(len(durations) * 0.9)]
                          if durations else None},
        }
    totals = {agent: v["sessions"] for agent, v in per_agent.items()}
    return {"per_agent": per_agent, "totals": totals}


def write_audit(out_dir: Path, data: dict) -> Path:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "audit.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = ["# eval 审计表（既有 session 观测）", "",
             "> 仅作观测参考：不进 gate、不入基线、不入 git；样本非受控，",
             "> 不替代受控探针。发现（如漫游形态）作为探针题库迭代输入。", ""]
    for agent, per in data["per_agent"].items():
        lines.append(f"## {agent}（{per['sessions']} 会话）")
        lines.append(f"- 模型分布：{per['models']}")
        lines.append(f"- 工具 Top：{dict(list(per['tools'].items())[:8])}")
        ls_find = {k: v for k, v in per["bash_heads"].items()
                   if k.split(' ')[0] in ('ls', 'find')}
        lines.append(f"- ls/find 命令头：{ls_find}")
        lines.append(f"- denial 事件：{per['denials']}")
        lines.append(f"- 时长：median={per['durations']['median']}s "
                     f"p90={per['durations']['p90']}s")
        lines.append("")
    (out_dir / "audit.md").write_text("\n".join(lines), encoding="utf-8")
    return out_dir
```

`eval/runner/cli.py` 追加：

```python
    p = sub.add_parser("audit", help="既有 session 审计表（本机存量，观测参考）")
    p.add_argument("--out", default="cadence/reports/eval/audit")
    p.add_argument("--claude-dir", default="~/.claude/projects")
    p.add_argument("--codex-dir", default="~/.codex/sessions")
    p.add_argument("--pi-dir", default="~/.pi/agent/sessions")
    p.add_argument("--kimi-dir", default="~/.kimi-code/sessions")
    p.add_argument("--limit", type=int, default=200)
    p.set_defaults(func=cmd_audit)
```

```python
def cmd_audit(args):
    from datetime import date as _date
    from eval.runner import audit
    paths = {name: Path(getattr(args, f"{name}_dir")).expanduser()
             for name in ("claude", "codex", "pi", "kimi")
             if Path(getattr(args, f"{name}_dir")).expanduser().is_dir()}
    data = audit.audit_dirs(paths, limit_per_agent=args.limit)
    out = audit.write_audit(Path(args.out).expanduser() / _date.today().isoformat(),
                            data)
    print(f"[audit] 输出 {out}/audit.md（不入 git，仅本机观测）")
    return 0
```

- [ ] **Step 4: 运行测试确认通过**

```bash
python3 -m unittest eval.tests.test_audit -v
```

预期：4 个用例全部 PASS。

- [ ] **Step 5: 提交建议**

```bash
git add eval/runner/audit.py eval/runner/cli.py eval/tests/test_audit.py .gitignore
git commit -m "feat(eval): 既有 session 审计表——四端离线解析复用，输出不入 git"
```

> 产物自动提交开关当前=关闭：跳过 `git commit`，只报告上述变更路径，等待维护者确认。

---
### Task 18: 离线重跑 job + Tier-0 workflow（新增 eval.yml，路径过滤触发）

**Files:**
- Create: `eval/runner/offline_rerun.py`、`eval/transcripts/golden-verdicts.json`
- Create: `.github/workflows/eval.yml`（Tier-0 job；Tier-1 job 骨架由 Task 19 补全）
- Modify: `eval/runner/cli.py`（追加 `rerun` 子命令）
- Test: `eval/tests/test_offline_rerun.py`

**Interfaces:**
- Consumes: `get_adapter`（Task 6–8）、`assertor.score_run`（Task 9）、`prb.get`（Task 13）。
- Produces:
  - `rerun_mod.run_rerun(transcripts_dir: Path, golden_path: Path) -> int`——对 golden-verdicts 登记的每条历史轨迹重新"适配→判分"，与登记判定 diff；判定翻转 → 列出并返回 1（断言器回归防线；workspace 相关断言在离线模式跳过并标注）；条目可选 `settings_snapshot` 字段（受管 deny 区块快照，离线重演双分类 gate）
  - `golden-verdicts.json` 条目：`{"path": "claude/golden-1.jsonl", "agent": "claude", "probe_id": "P1", "expect_verdict": "PASS"}`（首夜后维护者把**脱敏后的真实轨迹**追加进 `eval/transcripts/` 并登记，golden 集只增不删）
  - `.github/workflows/eval.yml`——Tier-0 job（PR/push 路径过滤：`eval/**` + 四 skill 目录；步骤=unittest 全量 → mock 冒烟 → 离线重跑）
  - Task 19（同一 workflow 追加 Tier-1）、Task 20（golden 集扩充）消费。

- [ ] **Step 1: 写失败测试**

```python
"""eval/tests/test_offline_rerun.py —— 离线重跑（tasks 4.2 / oracle §2-c）。"""
import json
import tempfile
import unittest
from pathlib import Path

from eval.runner import offline_rerun as rr

TRANS = Path(__file__).resolve().parents[1] / "transcripts"


class TestOfflineRerun(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)

    def _golden(self, verdict="PASS"):
        path = self.base / "golden-verdicts.json"
        path.write_text(json.dumps([
            {"path": "claude/golden-1.jsonl", "agent": "claude",
             "probe_id": "P1", "expect_verdict": verdict,
             "settings_snapshot": {"permissions": {"deny": [
                 "@@cadence-managed:permission-gate:v1:start@@", "Bash(ls:*)",
                 "Grep", "Glob",
                 "@@cadence-managed:permission-gate:v1:end@@"]}}}]),
            encoding="utf-8")
        return path

    def test_rerun_matches_golden(self):
        """ut-rr-match：罐头轨迹重判与登记一致（受管 deny→改道=PASS）。"""
        self.assertEqual(rr.run_rerun(TRANS, self._golden("PASS")), 0)

    def test_rerun_detects_flip(self):
        """ut-rr-flip：判定翻转被点名（断言器回归红线）。"""
        self.assertEqual(rr.run_rerun(TRANS, self._golden("FAIL")), 1)

    def test_rerun_missing_file_reported(self):
        """ut-rr-missing：登记文件缺失报错不静默。"""
        path = self.base / "golden-verdicts.json"
        path.write_text(json.dumps([
            {"path": "claude/nope.jsonl", "agent": "claude",
             "probe_id": "P1", "expect_verdict": "PASS"}]), encoding="utf-8")
        self.assertEqual(rr.run_rerun(TRANS, path), 1)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 运行确认失败**

```bash
python3 -m unittest eval.tests.test_offline_rerun -v
```

预期：全部 ERROR（`No module named 'eval.runner.offline_rerun'`）。

- [ ] **Step 3: 最小实现**

`eval/transcripts/golden-verdicts.json`（初始 golden 集=四端罐头轨迹；claude 条目携带受管区块快照以离线重演双分类）：

```json
[
  {"path": "claude/golden-1.jsonl", "agent": "claude", "probe_id": "P1",
   "expect_verdict": "PASS",
   "settings_snapshot": {"permissions": {"deny": [
     "@@cadence-managed:permission-gate:v1:start@@", "Bash(ls:*)", "Grep", "Glob",
     "@@cadence-managed:permission-gate:v1:end@@"]}}},
  {"path": "codex/golden-1.jsonl", "agent": "codex", "probe_id": "P1", "expect_verdict": "FAIL"},
  {"path": "pi/golden-1.jsonl", "agent": "pi", "probe_id": "P1", "expect_verdict": "FAIL"},
  {"path": "kimi/golden-1.jsonl", "agent": "kimi", "probe_id": "P1", "expect_verdict": "FAIL"}
]
```

（codex/pi/kimi 罐头无 codegraph 调用且有 Grep/Bash 检索——按 P1 断言判 FAIL，正好锁定"断言器没有把无 preferred 的轨迹误判为 PASS"。）

`eval/runner/offline_rerun.py`：

```python
"""离线重跑：历史 transcript 重新适配+判分并与 golden diff（断言器回归防线）。

Tier-0 的一个 job（eval-ci-matrix R1）：用留存的（脱敏）真实/罐头轨迹作
golden 输入，比 mock 冒烟更强；workspace 相关断言离线跳过并标注。
"""
import json
from pathlib import Path

from eval.adapters import get_adapter
from eval.probes import definitions as prb
from eval.scoring import assertor


def run_rerun(transcripts_dir: Path, golden_path: Path) -> int:
    entries = json.loads(Path(golden_path).read_text(encoding="utf-8"))
    flips = []
    for entry in entries:
        path = Path(transcripts_dir) / entry["path"]
        if not path.is_file():
            flips.append(f"{entry['path']}: 文件缺失")
            continue
        traj = get_adapter(entry["agent"]).parse_file(path)
        if isinstance(entry.get("settings_snapshot"), dict):
            traj.settings_snapshot = entry["settings_snapshot"]
        result = assertor.score_run(
            f"rerun:{entry['path']}", prb.get(entry["probe_id"]), traj,
            workspace=None, fake_mcp_log=None, pre_snapshot=None)
        if result["verdict"] != entry["expect_verdict"]:
            flips.append(f"{entry['path']}: 期望 {entry['expect_verdict']}"
                         f" 实判 {result['verdict']}（{result['fail_reason']}）")
    if flips:
        print("[rerun] 判定翻转：")
        for line in flips:
            print("  -", line)
        return 1
    print(f"[rerun] {len(entries)} 条 golden 全部一致")
    return 0
```

`eval/runner/cli.py` 追加：

```python
    p = sub.add_parser("rerun", help="离线重跑——历史轨迹重判并 diff（Tier-0 job）")
    p.add_argument("--transcripts", default="eval/transcripts")
    p.add_argument("--golden", default="eval/transcripts/golden-verdicts.json")
    p.set_defaults(func=cmd_rerun)
```

```python
def cmd_rerun(args):
    from eval.runner import offline_rerun
    return offline_rerun.run_rerun(Path(args.transcripts), Path(args.golden))
```

`.github/workflows/eval.yml`（Tier-0；Task 19 在同文件追加 runner-probe 与 Tier-1）：

````yaml
name: Eval CI

on:
  pull_request:
    paths:
      - "eval/**"
      - "cadence-init/skills/pre-check/**"
      - "cadence-init/skills/rule-config/**"
      - "cadence-init/skills/mcp-configuration/**"
      - "cadence-init/skills/project-rules-examples/**"
      - ".github/workflows/eval.yml"
  push:
    branches: [main]
    paths:
      - "eval/**"
      - "cadence-init/skills/pre-check/**"
      - "cadence-init/skills/rule-config/**"
      - "cadence-init/skills/mcp-configuration/**"
      - "cadence-init/skills/project-rules-examples/**"
      - ".github/workflows/eval.yml"
  schedule:
    - cron: "0 19 * * *"  # UTC 19:00 = 北京时间次日 03:00，夜间窗口
  workflow_dispatch:

permissions:
  contents: read

jobs:
  eval-tier0:
    name: Tier-0 零真实 CLI（单测 + mock 冒烟 + 离线重跑）
    if: github.event_name != 'schedule'
    runs-on: ubuntu-latest
    steps:
      - name: 检出代码
        uses: actions/checkout@v4

      - name: eval 单元测试（unittest 全量）
        run: |
          set -euo pipefail
          python3 -m unittest discover -s eval/tests -t . -v

      - name: mock 冒烟（阶段一四端全绿）
        run: |
          set -euo pipefail
          python3 -m eval.runner.cli smoke

      - name: 离线重跑（断言器回归防线）
        run: |
          set -euo pipefail
          python3 -m eval.runner.cli rerun \
            --transcripts eval/transcripts \
            --golden eval/transcripts/golden-verdicts.json
````

- [ ] **Step 4: 运行测试确认通过 + workflow 语法校验**

```bash
python3 -m unittest eval.tests.test_offline_rerun -v
python3 - <<'PY'
import yaml  # 若无 PyYAML 则跳过本步（Tier-0 车道内已含语法检查路径）
doc = yaml.safe_load(open(".github/workflows/eval.yml", encoding="utf-8"))
job = doc["jobs"]["eval-tier0"]
names = [s.get("name", "") for s in job["steps"]]
assert any("unittest" in n for n in names), names
assert any("冒烟" in n for n in names)
assert any("离线重跑" in n for n in names)
assert job["if"] == "github.event_name != 'schedule'"
print("eval.yml tier0 OK:", names)
PY
```

预期：3 个用例 PASS；workflow 校验输出步骤清单（PyYAML 缺失时以 `python3 -c "import yaml"` 退出码判断后跳过，不阻断）。

- [ ] **Step 5: 提交建议**

```bash
git add eval/runner/offline_rerun.py eval/runner/cli.py eval/transcripts/golden-verdicts.json .github/workflows/eval.yml eval/tests/test_offline_rerun.py
git commit -m "feat(eval): 离线重跑 job 与 Tier-0 workflow（路径过滤、零真实 CLI）"
```

> 产物自动提交开关当前=关闭：跳过 `git commit`，只报告上述新增路径，等待维护者确认。

### Task 19: Tier-1 夜间 workflow（self-hosted 路由 + 云端探活 + 端级降级）+ runner 注册文档

**Files:**
- Modify: `.github/workflows/eval.yml`（追加 `runner-probe` 与 `eval-tier1-nightly` 两个 job）
- Create: `cadence/readmes/2026-09-02_README_eval-self-hosted-runner注册_v1.0.md`
- Test: `eval/tests/test_workflow_contract.py`（YAML 契约单测，PyYAML 缺失时 skip）

**Interfaces:**
- Consumes: `night.run_night`（Task 15）、`report.write_report`（Task 16）、`guards.streak_alerts`（Task 15）。
- Produces:
  - `runner-probe` job（云端 ubuntu）：GitHub API 查 `cadence-eval` 标签 runner 在线状态（`secrets.EVAL_RUNNER_CHECK_TOKEN`，最小只读 Actions 权限 PAT）；不在线 → `available=false` → Tier-1 skip（**云端探活→条件触发，防 job 排队超时**；token 缺省时默认放行并在 Tier-1 首步 mock 自检兜底）
  - `eval-tier1-nightly` job（`runs-on: [self-hosted, cadence-eval]`，`timeout-minutes: 480`）：mock 自检前置 → `eval night` 单夜流水线 → `eval report`（红灯 exit 1 → job 红）→ job summary 汇总（连续 3 夜告警置顶）
  - 注册文档（tasks 4.5）：runner 注册/标签、PAT secret、告警通道、手动补跑（`workflow_dispatch`）、Tier-2 说明
  - Task 20（7 夜演练）消费。

- [ ] **Step 1: 写失败测试（workflow 契约）**

```python
"""eval/tests/test_workflow_contract.py —— Tier-0/1 workflow 契约（tasks 4.2/4.3）。"""
import unittest
from pathlib import Path

WF = Path(".github/workflows/eval.yml")


class TestWorkflowContract(unittest.TestCase):
    def test_tier0_zero_real_cli(self):
        """ut-wf-tier0：Tier-0 步骤只有 python 单测/冒烟/离线重跑，无端调用。"""
        doc = self._load()
        steps = doc["jobs"]["eval-tier0"]["steps"]
        script = "\n".join(str(s.get("run", "")) for s in steps)
        for banned in ("claude -p", "codex exec", "kimi -p", "pi -p"):
            self.assertNotIn(banned, script)
        self.assertIn("unittest discover", script)
        self.assertIn("rerun", script)

    def test_tier1_selfhosted_and_probe(self):
        """ut-wf-tier1：self-hosted 标签路由 + 云端探活条件触发 + mock 自检前置 + 手动触发。"""
        doc = self._load()
        tier1 = doc["jobs"]["eval-tier1-nightly"]
        self.assertEqual(tier1["runs-on"], ["self-hosted", "cadence-eval"])
        self.assertEqual(tier1["needs"], "runner-probe")
        self.assertIn("needs.runner-probe.outputs.available == 'true'",
                      tier1["if"])
        self.assertIn("workflow_dispatch", tier1["if"])  # 手动触发允许（s7）
        first_run = next(s["run"] for s in tier1["steps"] if "run" in s)
        self.assertIn("smoke", first_run)
        self.assertIn("night --date", "\n".join(str(s.get("run", ""))
                                                for s in tier1["steps"]))
        self.assertIn("TZ=Asia/Shanghai", "\n".join(str(s.get("run", ""))
                                                    for s in tier1["steps"]))

    def test_ci_yml_untouched(self):
        """ut-wf-noci：既有 ci.yml 车道零改动（R9；Tier-0 是新增 workflow 文件）。"""
        text = Path(".github/workflows/ci.yml").read_text(encoding="utf-8")
        self.assertNotIn("eval", text)

    def _load(self):
        try:
            import yaml
        except ImportError:
            self.skipTest("本地无 PyYAML；CI 车道内执行本契约")
        return yaml.safe_load(WF.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 运行确认失败**

```bash
python3 -m unittest eval.tests.test_workflow_contract -v
```

预期：`ut-wf-tier1` FAIL（eval.yml 尚无 tier1 job），其余可能 SKIP/FAIL——保持红态进入实现。

- [ ] **Step 3: 最小实现（eval.yml 追加两 job）**

在 `eval.yml` 的 `eval-tier0` job 之后追加：

````yaml
  runner-probe:
    name: 云端探活（防 self-hosted 排队超时）
    if: github.event_name == 'schedule' || github.event_name == 'workflow_dispatch'
    runs-on: ubuntu-latest
    timeout-minutes: 10
    outputs:
      available: ${{ steps.probe.outputs.available }}
    steps:
      - name: 查询 cadence-eval runner 在线状态
        id: probe
        env:
          GH_TOKEN: ${{ secrets.EVAL_RUNNER_CHECK_TOKEN }}
          REPO: ${{ github.repository }}
        run: |
          set -euo pipefail
          if [ -z "${GH_TOKEN}" ]; then
            echo "available=true" >> "$GITHUB_OUTPUT"   # 未配 token：默认放行，Tier-1 首步自检兜底
            exit 0
          fi
          online=$(curl -sf -H "Authorization: Bearer ${GH_TOKEN}" \
            "https://api.github.com/repos/${REPO}/actions/runners" \
            | python3 -c 'import json,sys; d=json.load(sys.stdin); print(sum(1 for r in d.get("runners", []) if any(l.get("name") == "cadence-eval" for l in r.get("labels", [])) and r.get("status")=="online"))')
          echo "available=$( [ "${online:-0}" -gt 0 ] && echo true || echo false )" >> "$GITHUB_OUTPUT"

  eval-tier1-nightly:
    name: Tier-1 夜间矩阵（self-hosted；付费前 mock 自检）
    if: >-
      (github.event_name == 'schedule' || github.event_name == 'workflow_dispatch') &&
      needs.runner-probe.outputs.available == 'true'
    needs: runner-probe
    runs-on: [self-hosted, cadence-eval]
    timeout-minutes: 480
    env:
      EVAL_BASE: $HOME/eval-runs
    steps:
      - name: 检出代码
        uses: actions/checkout@v4

      - name: 付费矩阵前 mock 自检（harness 自身无误才进真实 CLI）
        run: |
          set -euo pipefail
          python3 -m eval.runner.cli smoke

      - name: 夜间流水线（阶段一 + 探针 + 对照组；断点续跑/熔断内置）
        run: |
          set -euo pipefail
          NIGHT_DATE="$(TZ=Asia/Shanghai date +%F)"  # 夜历法按北京时间判定（与调度表同口径）
          python3 -m eval.runner.cli night --date "$NIGHT_DATE" --base "$EVAL_BASE"

      - name: 四矩阵 + 双键基线 diff（红灯则本 job 失败）
        run: |
          set -euo pipefail
          NIGHT_DATE="$(TZ=Asia/Shanghai date +%F)"  # 与上一步同夜同口径
          python3 -m eval.runner.cli report --base "$EVAL_BASE"

      - name: Job Summary（连续失败端置顶告警）
        if: always()
        run: |
          set -euo pipefail
          REPORT="$(ls -1 "$EVAL_BASE"/reports/eval/*/report.md 2>/dev/null | tail -1 || true)"
          if [ -n "$REPORT" ]; then
            cat "$REPORT" >> "$GITHUB_STEP_SUMMARY"
          else
            echo "本夜无报告产出（可能全部 skip：runner 离线/配额耗尽——不误红）" \
              >> "$GITHUB_STEP_SUMMARY"
          fi
````

`cadence/readmes/2026-09-02_README_eval-self-hosted-runner注册_v1.0.md`：

````markdown
# eval 体系 self-hosted runner 注册与告警（rule-eval-p0 / tasks 4.5）

## 一次性注册（维护者操作）

1. GitHub 仓库 Settings → Actions → Runners → New self-hosted runner，按平台
   下载配置脚本在本机执行；注册名建议 `cadence-eval-runner`。
2. 给 runner 打标签 **`cadence-eval`**（Tier-1 job 以
   `runs-on: [self-hosted, cadence-eval]` 路由）。
3. 生成 fine-grained PAT（仅本仓库、Actions 只读），配为仓库 secret
   **`EVAL_RUNNER_CHECK_TOKEN`**——云端探活 job 用它查询 runner 在线状态；
   不配置时探活默认放行，由 Tier-1 首步 mock 自检兜底。
4. 确认四端 CLI 已在本机登录：`claude --version && codex --version &&
   pi --version && kimi --version`；以
   `python3 -m eval.runner.cli pins-audit` 回填 `eval/config/agents.json`
   的 `cli_version` 后提交（版本锁生效）。
5. Kimi 入矩阵前置：在 self-hosted 上执行
   `python3 -m eval.runner.cli verify-kimi --base /tmp/kimi-verify`，
   全绿后把 `agents.json` 的 `kimi.enabled` 置 `true` 提交。

## 告警通道

- **红灯**（基线具名降级/离线重跑翻转）：GitHub Actions 失败通知（邮件/App）。
- **连续 ≥3 夜失败端**：每夜 report.md 置顶告警 + job summary 展示；
  端级失败不阻塞其余端（矩阵该列标 unavailable / 缺测，不误红）。
- **runner 离线**：cron 触发时探活失败 → Tier-1 skip 结束，主干 CI 不受影响。

## 手动补跑与 Tier-2

- 断点续跑：直接重跑同一日期 `python3 -m eval.runner.cli night --date <日期>
  --base <同基目录>`，已有结果 JSON 自动跳过。
- 手动触发：Actions 页面选 `Eval CI` → Run workflow（`workflow_dispatch`）。
  runner-probe 与 eval-tier1-nightly 均允许手动触发（探活默认放行规则不变：
  未配 token 时默认 true，Tier-1 首步 mock 自检兑底）；手动触发时 Tier-0
  也会一并执行（零真实 CLI，无害）——即 Tier-2 手动车道入口（同一矩阵，
  白天补跑）；夜日期按北京时间（Asia/Shanghai）判定，手动补跑请传当夜日期。
- Tier-2 可选 judge（LLM 过程评审，~$5–15/次）：不在本体系交付内，另行手动执行。
````

- [ ] **Step 4: 运行测试确认通过**

```bash
python3 -m unittest eval.tests.test_workflow_contract -v
```

预期：3 个用例全部 PASS（无 PyYAML 时 SKIP 并注明由 CI 车道执行）。

- [ ] **Step 5: 提交建议**

```bash
git add .github/workflows/eval.yml cadence/readmes/2026-09-02_README_eval-self-hosted-runner注册_v1.0.md eval/tests/test_workflow_contract.py
git commit -m "feat(eval): Tier-1 夜间 workflow（self-hosted 路由/云端探活/端级降级）与 runner 注册文档"
```

> 产物自动提交开关当前=关闭：跳过 `git commit`，只报告上述变更路径，等待维护者确认。

---
## 任务组 5：收尾（tasks 5.1/5.2）

### Task 20: 首轮基线建立 + 连续 7 夜端到端演练 + golden 集扩充 + tasks 勾选

**Files:**
- Modify: `eval/runner/cli.py`（追加 `drill7` 子命令）
- Modify: `eval/runner/night.py`（追加 `drill7(base_dir, repo_root, mock=True)`）
- Modify: `openspec/changes/rule-eval-p0/tasks.md`（勾选全部完成项）
- Test: `eval/tests/test_drill7.py`

**Interfaces:**
- Consumes: Task 1–19 全部产物（`night.run_night`、`report.write_report`/`candidate_baseline`、`audit.audit_dirs`、`schedule.night_plan`、golden-verdicts）。
- Produces:
  - `night.drill7(base_dir: Path, repo_root: Path, mock: bool = True) -> int`——连续 7 夜演练（mock 加速：依次以今日倒推 7 个日期跑 `run_night` → `report` → 断言四矩阵+审计表+双键 diff 齐全）；真实 7 夜由 nightly cron 自动执行，本命令用于 mock 演练与回归
  - `cli drill7 [--base] [--mock]` 子命令
  - 首轮基线操作流程（真实数据，维护者执行）：7 夜真实夜跑后 `eval baseline` 生成候选 → 审阅 → 显式提交 `eval/baselines/baseline.json`
  - golden 集扩充流程：首夜真实 transcript 经脱敏脚本入库并登记 golden-verdicts
  - tasks.md 全部勾选。

- [ ] **Step 1: 写失败测试**

```python
"""eval/tests/test_drill7.py —— 连续 7 夜端到端演练（tasks 5.2，mock 加速）。"""
import json
import tempfile
import unittest
from pathlib import Path

from eval.runner import night


class TestDrill7(unittest.TestCase):
    def test_drill7_mock_produces_all_outputs(self):
        """ut-drill7：7 夜 mock 演练产出四矩阵+审计表+双键 diff 齐全。"""
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            repo = Path(__file__).resolve().parents[2]
            self.assertEqual(night.drill7(base, repo, mock=True), 0)
            # 四矩阵：report.json 含全部矩阵键
            reports = list((base / "reports/eval").glob("*/report.json"))
            self.assertTrue(reports, "无聚合报告")
            agg = json.loads(reports[-1].read_text(encoding="utf-8"))["aggregate"]
            for key in ("adherence", "mcp_usage", "weak_model", "cross_end",
                        "clause_probe", "control"):
                self.assertIn(key, agg)
            # 7 夜结果目录齐备
            nights = sorted(p.name for p in (base / "reports/nightly").iterdir())
            self.assertEqual(len(nights), 7)
            # 分夜轮转：奇偶夜探针集合互补（从各夜结果文件直接验证）
            probe_sets = set()
            for n in nights:
                # 只统计安装组主行：排除 strong 增补行（全部 8 探针）与对照组行，
                # 奇偶夜互补性才是本断言靶子
                ids = {json.loads(p.read_text(encoding="utf-8"))["probe_id"]
                       for p in (base / "reports/nightly" / n / "runs").glob("*.json")
                       if not p.name.endswith(".intermediate.json")
                       and "-strong-" not in p.name and "-control-" not in p.name}
                probe_sets.add(tuple(sorted(ids)))
            self.assertEqual(len(probe_sets), 2)  # 奇偶夜两套互补集合


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 运行确认失败**

```bash
python3 -m unittest eval.tests.test_drill7 -v
```

预期：ERROR/FAIL（`night` 无 `drill7` 属性）。

- [ ] **Step 3: 最小实现（night.py 追加 + cli 追加）**

`eval/runner/night.py` 末尾追加：

```python
def drill7(base_dir, repo_root, mock=True) -> int:
    """连续 7 夜端到端演练（mock 加速）：夜跑→聚合→审计→自检齐全性。"""
    from datetime import date, timedelta
    from eval.runner import report as rep
    base_dir = Path(base_dir)
    today = date.today()
    for offset in range(6, -1, -1):
        day = (today - timedelta(days=offset)).isoformat()
        rc = run_night(day, repo_root, base_dir, mock=mock)
        if rc != 0:
            return rc
    rc = rep.write_report(base_dir, None,
                          end_date=today.isoformat())
    if rc == 1 and mock:
        print("[drill7] mock 数据不应触发红灯——请检查断言器")
        return 1
    # 审计表演练：以 mock 夜的 transcripts 目录伪造四端输入（真实审计另行手动）
    from eval.runner import audit as aud
    paths = {"claude": base_dir / "reports/nightly"}
    aud.write_audit(base_dir / "reports/eval/audit" / today.isoformat(),
                    aud.audit_dirs(paths, limit_per_agent=5))
    print("[drill7] 7 夜演练完成：四矩阵+审计表+双键 diff 齐全")
    return 0
```

`eval/runner/cli.py` 追加：

```python
    p = sub.add_parser("drill7", help="连续 7 夜端到端演练（默认 mock 加速）")
    p.add_argument("--base", required=True)
    p.add_argument("--no-mock", dest="mock", action="store_false", default=True)
    p.set_defaults(func=cmd_drill7)
```

```python
def cmd_drill7(args):
    from eval.runner import night
    return night.drill7(Path(args.base).resolve(), REPO_ROOT, mock=args.mock)
```

- [ ] **Step 4: 运行测试与全量回归确认通过**

```bash
python3 -m unittest eval.tests.test_drill7 -v
python3 -m unittest discover -s eval/tests -t . -q
python3 -m eval.runner.cli drill7 --base /tmp/eval-drill7
```

预期：drill7 用例 PASS；全量测试零 FAIL；mock 演练退出码 0。

- [ ] **Step 5: 真实首夜前置（self-hosted，维护者在场）**

```bash
# 1) 版本 pin 固化：回填 agents.json 的 cli_version 后提交
python3 -m eval.runner.cli pins-audit
# 2) denial 字段取证（启用 deny 双分类 gate 的前置条件）
python3 -m eval.runner.cli forensics-denial --base /tmp/eval-forensics
#    → 证据落 eval/evidence/denial-fields-claude-<日期>.json 后提交；
#      按证据校准 claude.py DENIAL_MARKERS 并重跑 adapters 测试
# 3) kimi 单端验证（通过后 agents.json kimi.enabled=true 提交）
python3 -m eval.runner.cli verify-kimi --base /tmp/kimi-verify
# 4) 手动触发首夜（Tier-2 入口同型）
python3 -m eval.runner.cli night --date $(date -u +%F) --base ~/eval-runs
```

- [ ] **Step 6: 首夜真实 transcript 脱敏入库（golden 集扩充，只增不删）**

```bash
python3 - <<'PY'
import json, re
from pathlib import Path
src = Path.home() / "eval-runs/reports/nightly"
dst = Path("eval/transcripts")
HOME = str(Path.home())
copied = []
for run in sorted(src.glob("*/runs/*.json")):
    doc = json.loads(run.read_text(encoding="utf-8"))
    if doc.get("verdict") != "PASS" or not doc.get("transcript_path"):
        continue  # 首轮只入 PASS 样本；失败样本含敏感信息更多，人工筛选后再入
    raw = Path(doc["transcript_path"])
    text = raw.read_text(encoding="utf-8", errors="replace").replace(HOME, "<HOME>")
    agent = doc["agent"]
    out = dst / agent / f"night1-{run.stem}.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    copied.append({"path": str(out.relative_to(dst)), "agent": agent,
                   "probe_id": doc["probe_id"], "expect_verdict": "PASS",
                   "settings_snapshot": {"permissions": {"deny": [
                       "@@cadence-managed:permission-gate:v1:start@@", "Grep",
                       "Glob", "Bash(grep:*)",
                       "@@cadence-managed:permission-gate:v1:end@@"]}}})
golden = dst / "golden-verdicts.json"
entries = json.loads(golden.read_text(encoding="utf-8")) if golden.exists() else []
known = {e["path"] for e in entries}
entries += [e for e in copied if e["path"] not in known]
golden.write_text(json.dumps(entries, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"[scrub] 入库 {len(copied)} 条脱敏样本并登记 golden")
PY
python3 -m eval.runner.cli rerun --transcripts eval/transcripts \
  --golden eval/transcripts/golden-verdicts.json
```

预期：rerun 全部一致（判定翻转=0）；若翻转，先修断言器再入库。

- [ ] **Step 7: 首轮基线建立（tasks 5.1；p1 已合入，基线为 post-p1 口径）**

```bash
# 连续 7 夜真实夜跑完成后（cron 自动积累）：
python3 -m eval.runner.cli baseline --base ~/eval-runs \
  --out eval/baselines/baseline.candidate.json
# 维护者审阅候选（probe_agent / clause_probe / control 三视图）后：
cp eval/baselines/baseline.candidate.json eval/baselines/baseline.json
git add eval/baselines/baseline.json   # 仅维护者显式提交后生效
git commit -m "chore(eval): 首轮基线（post-p1，滚动 7 夜）"
```

> 产物自动提交开关当前=关闭：跳过 `git commit`，只报告基线文件路径，等待维护者确认。pre-p1 对照基线（可选）：若需补测，另建 `baseline.pre-p1.json` 标记文件，不参与默认 diff。

- [ ] **Step 8: 勾选 change tasks.md 并收尾汇报**

- [ ] 勾选 `openspec/changes/rule-eval-p0/tasks.md` 全部 19 项（1.1–5.2；证据引用本任务 Step 4–7 输出与各任务的测试运行记录）。
- [ ] 汇总全部变更文件路径、mock 演练与真实首夜证据、denial 取证与 kimi 验证结论，向维护者汇报；后续走 `requesting-code-review` → 归档（不在本 Plan 内展开）。

```bash
git add openspec/changes/rule-eval-p0/tasks.md
git commit -m "chore: 勾选 rule-eval-p0 全部工作包（演练与首夜证据见实施汇报）"
```

> 产物自动提交开关当前=关闭：跳过 `git commit`，只报告 tasks.md 变更路径，等待维护者确认。

---

## Self-Review（写 Plan 后自检记录）

**1. Spec 覆盖**：三份 delta spec 的每个 Requirement/Scenario → 任务映射：

- **eval-pipeline**
  - R1 三变体断言（全新全绿 / v3 升级 / mcp_pre 防重写）→ Task 1（变体生成）+ Task 2（断言表：`rules.manifest`/`l0.v4`/`gate.region`/`codex.inline`/`verify.exit0`/`mcp.pre-existing`/`v3.upgraded`/`v3.backup`/`v3.outside-verbatim`）+ Task 3（runner 依序四 command + verify 消费）；三个 Scenario 分别对应 `ut-s1-fresh`、`ut-s1-v3`、`ut-s1-mcppre`。
  - R2 幂等双跑（末遍 byte-identical；gate 过渡第三遍稳态）→ Task 4（`ut-idem-2pass`/`ut-idem-3pass`，锚点=rule-config SKILL 的 S8→S9 过渡说明）。
  - R3 探针确定性判分 + 漫游靶子 + 时序预期红 → Task 9（`roam_detect`，锚点=242 会话审计 ls 114/find 20/grep 4）+ Task 13（P1 `no_roam`；P3 `expected_red_pre_gate`）。
  - R4 fixture 隔离/防泄漏/全局配置快照/题库 → Task 1（临时目录、`ut-fx-noleak`、`snapshot_global_configs`、theme）+ Task 13（prompt_variants）。
  - R5 对照组 → Task 1（control 变体）+ Task 15（night runner 对照组执行）+ Task 16（`control` 差值行）。
- **eval-trajectory-scoring**
  - R1 四端适配/统一中间格式/模型实测回读/MODEL_DRIFT/kimi 先行 → Task 5（ifmt 含 model_readback/model_changes）+ Task 6/7/8（四适配器，字段锚点全部来自本机实测）+ Task 15（`guards.model_drift`、`ut-night-drift`；断言器只吃中间格式=Task 9 全部原语签名）。
  - R2 deny 双分类 + 取证 → Task 10（`classify_denials`/`reroute_ok`/`apply_deny_gate` + `forensics-denial` 命令与 evidence 入库；settings_snapshot 快照进结果 JSON=Task 5 契约 + Task 9 落盘）。
  - R3 排除规则原文 → Task 9（`tool_used` 只读 tool_calls 事件；`ut-asr-prose`）。
  - R4 fake MCP → Task 11（三角色 + 调用记录 + fixture 注入；`ut-mcp-rpc`）。
  - R5 env 注入 → Task 13（`probe_env` 唯一入口）+ Task 3（`build_argv` 只从 env 取 prompt；`ut-proc-env`/`ut-prb-env`）。
  - R6 infra 归因 → Task 9（`classify_infra`/`INFRA_FAIL`）+ Task 16（聚合剔除计 skip；缺测不判红）。
  - R7 schema 版本化 → Task 12（`SCHEMA_VERSION`/`STABLE_KEYS`/`load_baseline` 主版本拒比；`ut-schema-major`）。
- **eval-ci-matrix**
  - R1 Tier-0 零真实 CLI + 离线重跑 + 路径过滤 + Tier-1 mock 前置 → Task 18（`ut-wf-tier0` 断言无端调用；rerun job）+ Task 19（tier1 首步 smoke）。
  - R2 调度表 + 滚动聚合 + 缺测表达 → Task 14（`ut-sch-*`，含 v3 每周/strong 错峰/对照组轮换/theme 轮换）+ Task 15（run_night 消费 `v3_agents`/`control_agents`/`strong_agents` 分支）+ Task 16（`load_results` 7 夜窗口、`missing` 标注）。
  - R3 四矩阵 + 双键 diff + 基线治理 + 审计表不入 git → Task 16（`aggregate`/`named_diff`/`render_markdown` 具名降级 `▼`、`write_report` 不写基线、`candidate_baseline`）+ Task 17（审计表 + `.gitignore`）。
  - R4 续跑/熔断/双 pin/保留 → Task 15（`should_skip`/`CircuitBreaker`/`cli_version_check`+`pins-audit`/`apply_retention`；`ut-gd-*`）。
  - R5 端级/runner 级降级 → Task 15（streaks）+ Task 19（runner-probe 云端探活条件触发、skip 不误红、连续 3 夜置顶）。
  - R6 审计表 → Task 17（复用适配器离线解析；`cadence/reports/eval/audit/` 不入 git；不进 gate）。
- tasks.md 19 项（1.1–5.2）全部有映射（见"文件结构总览"前的映射表）；未发现缺口。

**2. 占位符扫描**：全文无 TBD/TODO/"适当处理"/"类似任务 N"；每个代码步骤含真实可运行代码；四端解析规则落到字段级（claude `message.model`/`tool_use`/`tool_result.is_error`/`result.duration_ms`；codex `session_meta`·`turn_context.payload.model`/`function_call`·`custom_tool_call`/`function_call_output`；pi `toolCall`/`role=toolResult`/`model_change.modelId`；kimi `metadata.protocol_version`/`config.update.modelAlias`/`usage.record.model`/`context.append_loop_event.event.tool.call`——全部为本机实测锚点）。两处有意为之的"桩→替换"（Task 9 的 denial_gate/schema 最小桩）均为 TDD 红绿顺序的显式设计并在对应任务内闭环，非未完成项。

**3. 类型/签名一致性**（交叉复核）：`gen.make_fixture(variant, base_dir, repo_root, theme, install) -> FixturePaths`（T1 定义；T3/T4/T8/T10/T15 消费同参）；`asrt.assert_stage1(variant, root, verify_exit, final_texts, extra) -> list[Assertion]`（T2；T3/T18）；`proc.run_cli(agent, prompt, cwd, home, pins, timeout_s, env_extra, bin_dir, out_dir, skill_env, session_root) -> dict`（T3；T8/T10/T15）；`proc.build_argv/extract_final_text/cli_version_check`（T3；T15）；`ifmt.*` dataclass 与 `dump/load`（T5；T6–T9/T15）；`base.AgentAdapter.parse_stream/parse_file/find_latest_session`、`base.normalize_tool/args_digest`、`get_adapter`（T6；T7/T8/T15/T17/T18）；`assertor.score_run(run_id, probe, traj, workspace, fake_mcp_log, pre_snapshot, returncode, stderr, timed_out) -> dict`（T9；T15/T18）；`denial_gate.managed_deny_entries/classify_denials/reroute_ok/apply_deny_gate`（T10；T9 内部）；`schema.build_result/validate_result/load_baseline`（T12；T9/T16）；`fake.ROLES/SERVER_NAMES/SEEDS/TOOLS/serve/fixture_mcp_config/read_calls`（T11；T13/T15）；`prb.PROBES/CONTROL_PROBES/probe_env/variant_for_night/get`（T13；T14/T15/T18）；`guards.load_config/model_drift/should_skip/CircuitBreaker/apply_retention/update_streak/streak_alerts`（T15；T16/T19）；`schedule.night_index/night_plan`（T14；T15/T20）；`night.run_night/run_single_probe/run_strong_rows/drill7`（T15 定义前三个、T16 接线报告调用、T20 定义 drill7；T18–T19 workflow 调 `cli night/report`）；`report.load_results/aggregate/named_diff/render_markdown/write_report/candidate_baseline`（T16；T19/T20）；`audit.audit_dirs/write_audit`（T17；T20）；`offline_rerun.run_rerun`（T18；T19 workflow）。deny gate 计数字段 `managed/unmanaged/abandoned/rerouted/silent_errors` 在 T9/T10 两处引用一致；`night.run_night(date_str, repo_root, base_dir, config_dir, mock)` 与 cli/cmd_drill7 调用一致。

## 遗留事项与实现边界（不属本 Plan 范围，如实记录）

- **Tier-2 judge**：LLM 过程评审（~$5–15/次）按设计 §10 与 proposal 明确为可选手动车道，本 Plan 仅提供 `workflow_dispatch` 手动入口，不实现 judge。
- **p1 未合入场景已消失**：仓库 2026-09-02 已归档 p1（`--verify`/权限区块/L0 v4/AGENTS 内联区块均已入库），本 Plan 断言锚点直接以 v4/`@@cadence-managed:permission-gate:v1@@`/`codex-rules-inline:v1` 为准；pre-p1 对照基线为可选手动项（Task 20 Step 7 附注）。
- **阶段一断言的 server 名下限**：`MCP_REQUIRED_SERVERS=("zai-mcp-server","MiniMax","codegraph")` 取自本仓库真实 `.mcp.json` 与 mcp-configuration SKILL 的权威集合；skill 未来增删 server 时该常量随源同步（与 p1 标记常量同类的耦合点，已在代码注释标注）。
- **claude 会话文件与 stream-json 双形态**：适配器按同构行协议解析（`type` 分派），`result`/`system` 行仅存在于 stream-json；session 文件缺 `result` 时 `duration_s=0`，不影响判分（时间序以 tool index 为准）。
- **codex/pi/kimi 的 denial 语义**：三端 deny 事件标记为启发式（真实样本稀疏），双分类 gate 的归属判定对全部端一致生效；forensics 取证流程（Task 20 Step 5）首夜后可对其他端复用同命令扩展。
- **量级实测回填**：调度表首版按拍板点 3 固定（2 runs/分夜/轮换）；首夜实测时长（oracle 建议"每端单会话时长进 dashboard"）由 `report.json` 的 duration 聚合承载，调参只改 `policy.json` 数据不改代码。

## 驳回修复记录（2026-09-03 评审驳回后定点修复；行号为本次修订后基准）

> 验证方式：从本文档抽取全部嵌入代码在独立工作区组装 `eval/` 包（含两段 yaml 拼接、cli.py 片段合并、night.py 尾部接线），按任务顺序执行各 Step 4 命令——**23 项套件命令全部通过，全量 discover 107 用例 0 失败**；Task 9 桩阶段另以文档内桩替换验证。未动架构与 tasks.md→Plan 任务映射。

### 十个阻塞的修复落点与推演结论

1. **P:4681-4682 语法错误**——Task 15 `run_night`：原对照组双层循环内 `session_count += 1    guards.apply_retention(...)` 同行双语句已拆行；`apply_retention` 移至 agent 循环外、strong 行之后单次正缩进调用（L4930-4935）。推演：探针/对照组/strong 全部结束后才清理，不会误删当夜 raw；循环内不再通次触发。
2. **调度历法**——Task 14：新增 `SCHED_START = date(2026, 9, 7)`（周一，实测校验）与 `night_index = (date - SCHED_START).days`（L4236-4245），废弃 toordinal。golden 值按新口径重算并实跑验证：`test_parity_probe_sets` 改用 09-08（夜 1，奇）/09-09（夜 2，偶）；v3 夜保持 **[7,14]**（夜序号 0/7）；strong 夜由 [3,10] 改为 **[10,17]**（夜序号 3/10，与 v3 错峰，扫描范围 range(7,18)；评审原文 [3,10] 在新历法下不成立）；`test_drifted_run_excluded_marker` 日期改 2026-09-09（偶夜，P2 必跑，glob 命中，L4628）。4/4 用例实跑 PASS。
3. **P:683 prx.not-rules**——Task 2：缺 `rules_before` 改判 skip（`_ok` + detail 前缀 `skip:`，L715-719），Interfaces 同步注明；`test_fresh_all_green`/`test_v3_upgrade_assertions` 未补传仍绿（8/8 实跑 PASS）。
4. **mock_cli 分支 + stdout 出 fixture 根 + P:797**——Task 3：`STAGE1_WRITERS` 按 `EVAL_COMMAND` 分支（L1127，pre-check 零写盘），`stage1.run_stage1` 注入该 env；`proc.run_cli` 新增 `out_dir`，捕获文件 `.eval-<agent>-<pid>-<ms>-stdout.jsonl` 移出 fixture 根（L971-975，缺省系统临时目录）；P:797 断言元组补 `"result"`（L834）。smoke 四端 OK、runner 5/5 实跑 PASS。
5. **P8 幂等可判**——Task 4：`snapshot_tree` 排除 `.eval-*`（L1497，断言器 `snapshot_unchanged` 同源复用），测试扩展覆盖；4/4 实跑 PASS。
6. **Task 7 digest**——codex list 分支 join 后剥 `bash -lc ` 前缀、str 分支取原文（L2306-2313）；golden `"ls src"` 与变体 `"find . -name x"` 两用例实跑双绿。
7. **Task 10 期望对齐实现**——`test_apply_gate_counts` 改为 `(1,1,1,0)`、`silent_errors==0`（L3219-3227）并注明推演（Grep 受管命中→managed=1+改道；Edit 无命中→unmanaged=1；全调用 is_error=False→silent=0）；选测试对齐实现。
8. **Task 16 数据/期望**——`_result` 加 verdict 序号消同名覆盖（L5036-5044）；比率对齐 **4/6**（两日各 PASS,PASS,FAIL）；对照差值随公式改 -8.3pp；`write_report` 期望 exit **1**（4/6≈67%<70% 下限且跌 33pp，L5131-5141）；7/7 实跑 PASS。
9. **Task 9 Step 4**——改为"10 个用例中 8 PASS；deny 双用例（ut-asr-deny-reroute/ut-asr-deny-unmanaged）桩阶段预期红，Task 10 转绿"（L3107-3111）；全文 11→10 修正（含 P:3741→L3873）。桩实装验证：恰好 `test_managed_deny_reroute_pass`/`test_unmanaged_deny_fail` 两红、8 绿——评审原文 "9/10" 与 "9+2>10" 不自洽，以逐用例推演+实跑为准。
10. **HOME 策略选 b**——Global Constraints 新增 HOME 策略条款含取舍理由（L26）；`agents.json` 四端增 `skill_env` 数据面（L4423-4443）；`proc.run_cli` 支持 `home=None`+`skill_env`、`run_night` 真实模式不覆写 HOME 且对照组不注入 skill_env（L4840 等）；`snapshot_global_configs`/`diff_global_configs` 接入 `run_night` 首尾，漂移落 `<夜>/global-config-drift.json`（L4936-4939）；`write_report`/`render_markdown` 增 `global_config_drift` 节（`_load_global_drift` L5394）；Task 1 新增 `ut-fx-realhome` 用例（10/10 PASS）。

### 九条建议采纳落点

s1 `run_single_probe` Interfaces 补 `transcripts_dir/base_dir`（L4312）；s2 显式函数 `night.run_strong_rows`（L4792-4825）+ 红→绿用例 `ut-night-strong`（实跑 PASS），Task 14 注释改指 Task 15、Task 16 仅接线报告调用；s3 `score_run` 两分支 `details` 增 `settings_snapshot`（L3058/3080）；s4 `validate_result` 枚举加 `MODEL_DRIFT`（L3847）；s5 fixture 生成 `assets/error.png`（1x1 PNG base64，L263-267）+魔数断言；s6 P2/P6/P7 forbidden 补 `zread`/`web-reader`（L4027/4080/4094）；s7 runner-probe/tier1 `if` 放行 `workflow_dispatch`（L6111/6136-6139）+契约断言+注册文档措辞；s8 mock 探针 Write 事件 `input` 改 `{"file_path":...}` 形状（L1144-1156）；s9 杂项：文件清单 17→21（L90）、`rule-config.py:879`→`:880`（L3133，与仓库实测一致）、Tier-1 夜日期 `TZ=Asia/Shanghai date +%F`（L6076/6082）、`_matches_entry` 参数限定比对（`Bash(grep:*)` 校验命令头前缀，L3300-3320+新用例 `ut-dg-param`）。

### 执行推演发现的连带修复（评审清单之外，均为本文档既有缺陷，最小修复）

1. T2 测试 helper `_installed_workspace` 缺 `rules.mkdir`（首用即 FileNotFoundError）；2. mock 包装器缺 `sys.path` 引导（子进程无法导入 eval 包，mock 全链路痪）——两处生成器同修；3. T4 测试导入 `idem` 应为 `idempotency as idem`；4. codex `_ts` 缺 None 守卫（mock 无 timestamp 行即崩）；5. T19 yaml `python -c` 续行顶行破坏块标量（PyYAML 实测 ScannerError），单行化；6. mock `_stage1_rule_config` 缺目录创建；7. `extract_final_text` 的 result 行仅限 claude 导致 mock 四端 pre-check 断言误红（真实 codex/pi/kimi 无 result 行，全端接受无副作用）；8. `run_cli` session 捕获未定位时回退 stdout（兼修 `home=None` 守卫）；9. T2 `ut-s1-prx` 快照口径 text→sha256 对齐实现；10. T4 `ut-idem-regress` 先落初始 .gitignore；11. `ut-night-strong`/`ut-drill7` 的 runs 目录 glob 排除 `.intermediate.json` 副本；12. `ut-drill7` 探针集合只计安装组主行（strong 夜全 8 探针会破"两套互补"不变量）；13. Task 19 用例计数 4→3。以上全部随 107 用例全绿验证。

### 残留风险

- pi/kimi 的 `skill_env` 键名为初值假设（真机首夜核定，只改 agents.json 数据）；Tier-1 真实 CLI 行为（登录态/config-dir 语义）仍以首夜实测为准。
- mock 模式下 pi/kimi 无 session 文件，轨迹回退 stdout 后按 pi 解析为空轨迹→判 MODEL_DRIFT（出矩阵不判红）——mock 冒烟语义可接受。真实模式（skill_env 注入）经 `run_cli(session_root=fixture.home)` 在 fixture 根下搜索 session（config-dir 已重定向至该根），捕获链闭合、不再无条件回退 stdout；对照组（不注入 skill_env）pi/kimi 会话落在真实 HOME、按 b 方案刻意不搜索，仍回退 stdout；pi/kimi 首夜仍需实测核定 skill_env 键名与 session 实际落点（见上条残留提示）。
- 2026-09-07 之前的夜序号为负，Python 模运算仍确定性（周行 v3/strong 可能在首调度夜前触发，仅影响演练数据分布，不影响生产）；drill7/调度测试已全部用 SCHED_START 之后的日期自洽验证。

### 二轮补修（2026-09-04 复审定点修复；行号为本轮修订后基准）

1. **pi/kimi 真实模式 session 捕获断链（中）**——`proc.run_cli` 新增 `session_root` 参数（签名 L951-952、docstring L958-963、捕获分支 L994-999）：`home=None` 且 skill_env 注入（真实模式）时以调用方传入的 `fixture.home` 为 SESSION_PATTERNS 搜索根（skill_env 已把 config-dir 重定向到 fixture 根，session 落其下），仅 `home=None` 且未传 `session_root`（mock 冒烟语义）才跳过定位、回退 stdout；同步点：Task 3 Interfaces（L756）、`run_single_probe` docstring 与传参（L4738-4740/L4751-4757，`session_root=fixture.home if real_home and skill_env else None`，strong 行经 run_strong_rows 同链路覆盖）、Task 15 Interfaces（L4318）、Self-Review 签名一致性（L6489）；残留风险节“真实模式不受影响”改为准确描述（真实模式经 fixture 根搜索；对照组不注入 skill_env 仍回退 stdout；首夜实测核定键名提示保留，L6528）。
2. **ut-night-drift glob 排除中间文件（低）**——`*P2*.json` 加 `.intermediate.json` 排除（与连带修复 #11 同型口径，L4636-4637），防 `results[0]` 命中轨迹副本致 verdict 断言误红。
3. **mock 模式首快照不触碰真实 HOME（低）**——`run_night` 快照根改为 `global_root = Path.home() if real_home else base_dir`（L4852-4855），尾快照同根（L4953）；mock 下 sandbox 根无 GLOBAL_CONFIG_FILES→空快照零漂移，真实模式语义不变；Task 15 Interfaces run_night 条目同步（L4317）。选改动最小方案（未另建 sandbox home 目录）。

