# Task 11 端到端回归报告

## 范围

本任务以初始化问题现场的两个入口文件执行端到端回归，覆盖真实 CLI：

```text
python3 cadence-init/skills/rule-config/scripts/rule-config.py apply \
  --project-root <temporary-project-root> \
  --report <external-report-path> \
  --no-interrupt
```

测试项目在临时目录创建 `package.json`，内容为：

```json
{"scripts":{"test":"vitest","lint":"oxlint src"}}
```

报告文件通过 `tempfile.mkstemp()` 创建在临时项目根目录之外，符合报告路径契约；测试使用 `subprocess.run(..., check=True)` 验证 CLI 成功退出，并检查报告 `overall == "ok"`。

## Fixture 来源

- `tests/fixtures/entry-kb-agents.md`：由任务 brief 指定的 `/tmp/AGENTS.md` 复制而来。该文件是英文 Knowledge Base 型入口，包含 `OVERVIEW`、`STRUCTURE`、`WHERE TO LOOK` 等用户内容、孤立的“项目个性化规则（强制规则）”H2 以及“未检测到”技术栈占位。
- `tests/fixtures/entry-drift-claude.md`：由任务 brief 指定的 `/tmp/CLAUDE.md` 复制而来。该文件包含旧版 v1 L0、Serena 残留、1-9 编号规则和 Java/Vue/TypeScript 旧技术栈值。

## 端到端断言结果

### `test_kb_agents_gets_full_section`

通过。真实 `apply --no-interrupt` 后：

- AGENTS.md 含完整强制规则 1-7；
- L0 已收敛为 v2，含 `V2_START` / `V2_END`；
- `## WHERE TO LOOK` 等 Knowledge Base 用户内容保留；
- 产物自动提交开关默认为“关闭”；
- 不含 `serena-usage.md`。

### `test_claude_serena_removed_and_renumbered`

未通过，失败发生在 brief 要求的断言：

```python
self.assertNotIn("### 8. Playwright", claude)
```

已观察到的结果：

- Serena 及 `serena-usage.md` 已清除；
- 规则 1-7 已重排；
- L0 已收敛为 v2；
- package.json 检测结果已写入双入口，AGENTS.md 与 CLAUDE.md 均为 `JavaScript/TypeScript`；
- 但 CLAUDE.md 中原有的 `### 8. Playwright CLI 使用规则` 被实现作为无对应受管 marker 的用户 H3 保留；项目确实没有 `.claude/rules/playwright.md`，且初始化没有创建该文件。

因此没有为通过测试而放宽断言，也没有修改实现。该失败表明实现对“无 Playwright 文件时清除旧 Playwright 条目”的问题入口场景仍存在洞，需后续实现任务处理。

## 验证命令

- `python3 -m unittest cadence-init.skills.rule-config.tests.test_rule_config.TestEndToEndRegression -v`：失败，1 通过、1 失败（预期洞复现）。
- `python3 -m unittest discover -s cadence-init/skills/rule-config/tests -v`：失败，216 个测试中 215 通过、1 失败（上述回归失败）。
- `bash cadence-init/skills/rule-config/tests/verify-managed-lifecycle.sh`：通过，`SUMMARY pass=104 fail=0`。

## 结论

Fixture 与回归测试已落地，问题入口文件的绝大多数规范化行为均得到真实 CLI 验证；全量测试唯一失败与 brief 的无 Playwright 条目要求一致，已保留为实现风险，不通过修改断言规避。
