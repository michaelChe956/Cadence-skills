"""rule-config P0 回归：用户内容不得被 marker 子串误删，写入必须备份。"""

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "rule-config.py"
spec = importlib.util.spec_from_file_location("rule_config_p0", SCRIPT)
rc = importlib.util.module_from_spec(spec)
sys.modules["rule_config_p0"] = rc
spec.loader.exec_module(rc)


def _entry_with_user_tables() -> str:
    return """# CLAUDE.md

## 强制规则

> **🔴 必须遵守 - 无例外**
> 详细规则见 `.claude/rules/` 目录下的各规则文件。
> 用户自定义规则见 `cadence/project-rules/` 目录。

### 1. 语言规则
- **必须使用中文回答** → 详见 `.claude/rules/language.md`

### 2. 代码使用规则
- **遵循 TDD 和代码规范** → 详见 `.claude/rules/code-usage.md`

### 3. 文档存储规则
- **Cadence 产物文档必须存放在 `cadence` 目录下；Claude Code 框架规则保留在 `.claude/rules/` 目录下** → 详见 `.claude/rules/document-storage.md`

### 4. Markdown 格式规则
- **代码块嵌套使用 4 反引号/3 反引号** → 详见 `.claude/rules/markdown-format.md`

### 5. MCP Server 使用规则
- **各 MCP 工具及相关自动化工具的使用必须遵循项目规范** → 详见 `.claude/rules/mcp-servers.md`

### 6. 项目个性化规则（强制规则）
- **用户自定义规则只能存放在 `cadence/project-rules/` 目录**
- **禁止**在 `.claude/rules/` 目录中添加用户自定义规则
- **禁止**直接修改 `.claude/rules/` 目录下的框架内置规则文件
- 详见 `cadence/project-rules/README.md`

**本项目已定制模板（编写产物时直接引用，勿另起通用格式）**：

| 产物类型 | 模板路径 |
|----------|----------|
| 需求文档 | `cadence/project-rules/examples/requirement-template.md` |
| 设计文档 | `cadence/project-rules/examples/design-template.md` |

**本项目生效规范（写代码前必读）**：

| 规范 | 路径 |
|------|------|
| 项目代码开发规范 | `cadence/project-rules/coding-standards.md` |
| 前端 UI 组件规范 | `cadence/project-rules/frontend-ui-standards.md` |

### 7. 代码阅读规则
- **大范围检索使用 CodeGraph，精确结构阅读优先使用 ast-grep outline** → 详见 `.claude/rules/code-reading.md`

### 8. 开发环境与构建约定（强制）

> **🔴 本项目的构建、测试、依赖安装一律在 podman 容器内执行。**

**代码管理范围**

| 目录 | 是否进版本管理 | 说明 |
|------|----------------|------|
| `busi/` `gateway/` `frontend/` | ✅ 各自独立 git 仓库 | 唯一的代码库 |

```bash
# 构建命令
mvn -B package
```
"""


class TestEntryNormalizationP0(unittest.TestCase):
    def test_user_table_rows_and_custom_h3_are_preserved(self):
        out, warns = rc._normalize_mandatory_rules(
            _entry_with_user_tables(), "CLAUDE.md", "coding",
            {"language.md", "code-usage.md", "document-storage.md",
             "markdown-format.md", "mcp-servers.md", "code-reading.md"},
        )
        for expected in (
            "| 需求文档 | `cadence/project-rules/examples/requirement-template.md` |",
            "| 设计文档 | `cadence/project-rules/examples/design-template.md` |",
            "| 项目代码开发规范 | `cadence/project-rules/coding-standards.md` |",
            "| 前端 UI 组件规范 | `cadence/project-rules/frontend-ui-standards.md` |",
            "### 8. 开发环境与构建约定（强制）",
            "> **🔴 本项目的构建、测试、依赖安装一律在 podman 容器内执行。**",
            "```bash\n# 构建命令\nmvn -B package\n```",
            "mvn -B package",
        ):
            self.assertIn(expected, out)
        self.assertTrue(any(w["code"] == "USER_LINES_KEPT" for w in warns))

    def test_claude_rule6_uses_dot_claude_path(self):
        self.assertIn("`.claude/rules/`", rc.RULE6_BLOCK_CLAUDE)
        self.assertNotIn("禁止在 `rules/`", rc.RULE6_BLOCK_CLAUDE)

    def test_user_h3_with_playwright_reference_is_preserved(self):
        text = (
            "## 强制规则\n\n"
            "### 9. 我们的 Playwright 用法\n"
            "- 参考 `.claude/rules/playwright.md` 的约定\n"
            "- 只在 CI 里跑\n"
        )
        out, _ = rc._normalize_mandatory_rules(text, "CLAUDE.md", "coding", set())
        self.assertIn("### 9. 我们的 Playwright 用法", out)
        self.assertIn("只在 CI 里跑", out)

    def test_user_h3_block_idempotent(self):
        text = (
            "## 强制规则\n\n"
            "### 1. 语言规则\n- **必须使用中文回答** → 详见 `.claude/rules/language.md`\n\n"
            "### 8. 部署约定\n\n用户说明\n\n```bash\n# 注释\nmake build\n```\n\n"
            "### 9. 运维约定\n\n保留我\n"
        )
        once, _ = rc._normalize_mandatory_rules(text, "CLAUDE.md", "coding", set())
        twice, _ = rc._normalize_mandatory_rules(once, "CLAUDE.md", "coding", set())
        self.assertEqual(once, twice)

    def test_exact_playwright_heading_with_user_content_is_preserved(self):
        text = (
            "## 强制规则\n\n"
            "### 8. Playwright CLI 使用规则\n"
            "- 用户自定条目 A\n"
        )
        out, _ = rc._normalize_mandatory_rules(text, "CLAUDE.md", "coding", set())
        self.assertIn("用户自定条目 A", out)
        self.assertIn("### 8. Playwright CLI 使用规则", out)

    def test_duplicate_canonical_heading_is_preserved_as_user_block(self):
        text = (
            "## 强制规则\n\n"
            "### 2. 代码使用规则\n"
            "- **遵循 TDD 和代码规范** → 详见 `.claude/rules/code-usage.md`\n\n"
            "### 2. 代码使用规则（本项目补充）\n"
            "USER-JUNIT5-RULE\n"
        )
        out, warns = rc._normalize_mandatory_rules(text, "CLAUDE.md", "coding", set())
        self.assertIn("USER-JUNIT5-RULE", out)
        self.assertTrue(any(
            w["code"] == "USER_HEADING_NUMBER_COLLISION" for w in warns
        ))

    def test_old_rule6_wording_is_removed(self):
        text = (
            "## 强制规则\n\n"
            "### 6. 项目个性化规则\n"
            "- **用户自定义规则只能存放在 `cadence/project-rules/` 目录**\n"
            "- 禁止在 `.claude/rules/` 目录中添加用户自定义规则\n"
            "- 禁止直接修改 `.claude/rules/` 目录下的框架内置规则文件\n"
            "- 详见 `cadence/project-rules/README.md`\n"
        )
        out, _ = rc._normalize_mandatory_rules(text, "CLAUDE.md", "coding", set())
        self.assertNotIn("禁止在 `.claude/rules/` 目录中添加用户自定义规则", out)
        self.assertIn("用户覆盖写入 `.claude/rules/user-<框架文件名>.md`", out)

    def test_dry_run_previews_overlay_and_backup(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            rules = root / ".claude" / "rules"
            rules.mkdir(parents=True)
            template_root = Path(__file__).resolve().parents[1] / "references" / "rules"
            template = (template_root / "language.md").read_text(encoding="utf-8")
            target = rules / "language.md"
            target.write_text(template + "\nUSER-DRY-LINE\n", encoding="utf-8")
            report = rc.build_report("no-interrupt", root)
            intents = rc.Intents(
                no_interrupt=True, project_type=None, ignore_cadence=False,
                enable_playwright=False, enable_codegraph=False, decisions=None,
            )
            rc.run_dry_run(root, intents, report)
            self.assertTrue(report["planned_actions"])
            self.assertTrue(any("language.md" in p for p in report["planned_backups"]))
            self.assertTrue(report["pending"])
            self.assertEqual(target.read_text(encoding="utf-8"), template + "\nUSER-DRY-LINE\n")

    def test_toggle_alias_is_kept_and_not_invalid(self):
        text = (
            "# CLAUDE.md\n\n## 项目配置\n\n"
            "- **产物自动提交（design/plan/code）**：打开\n"
        )
        out, warns = rc._ensure_commit_toggle(text, "CLAUDE.md")
        self.assertIn("：打开", out)
        self.assertFalse(any(w["code"] == "INVALID_TOGGLE" for w in warns))
        self.assertTrue(any(w["code"] == "TOGGLE_ALIAS_KEPT" for w in warns))


class TestBackupRequiredP0(unittest.TestCase):
    def test_loss_guard_blocks_unaccounted_removal(self):
        with self.assertRaises(rc.PublishError):
            rc._assert_no_user_loss(
                "用户独有行不得删除\n", "", "CLAUDE.md"
            )

    def test_skip_backfill_requires_backup(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            entry = root / "CLAUDE.md"
            entry.write_text("# CLAUDE.md\n\n## 强制规则\n\n- 用户规则\n", encoding="utf-8")
            plan = {
                "project_type": "coding",
                "steps": {
                    rc.STEP_ENTRY_FILES: {
                        "assets": [{
                            "path": "CLAUDE.md",
                            "action": "skip",
                            "conflict": None,
                        }],
                    },
                },
            }
            intents = rc.Intents(
                no_interrupt=True, project_type=None, ignore_cadence=False,
                enable_playwright=False, enable_codegraph=False, decisions=None,
            )
            self.assertTrue(
                rc._backup_required_for(entry, root, plan, intents)
            )


if __name__ == "__main__":
    unittest.main()
