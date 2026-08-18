# rule-config 脚本纯函数库单元测试（RED 骨架）
#
# 用例清单来源：tests/skill-clause-map.md（Task 1 产物）。
# 每个测试方法的 docstring 第一行标注对应 ut-* 测试 ID 与条款编号。
# 加载方式与签名由 Plan 全局约束冻结，Task 4-9 必须逐字实现：
#   rc.merge_markdown / rc.merge_yaml / rc.l0_block / rc.precheck_openspec_structure
#   rc.backup_file / rc.atomic_write / rc.sha256_file / rc.classify_l1
#   rc.detect_project / rc.locate_templates  （Task 5 实现）

import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

from unittest import mock

SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "rule-config.py"
spec = importlib.util.spec_from_file_location("rule_config", SCRIPT_PATH)
rc = importlib.util.module_from_spec(spec); spec.loader.exec_module(rc)

TPL = (Path(__file__).resolve().parents[1] / "references" / "openspec" / "config.yaml").read_text()
L0_SOURCE = (Path(__file__).resolve().parents[1] / "references" / "rules" / "agent-routing-kernel.md").read_text()
L0_V1_SOURCE = (Path(__file__).resolve().parents[1] / "references" / "rules" / "l0-history" / "agent-routing-kernel-v1.md").read_text()
L1_V1 = (Path(__file__).resolve().parents[1] / "references" / "rules" / "openspec-superpowers-workflow.md").read_text()

# L0 受管区块标记（v2 为当前版本；v1/v0 为受支持旧版本的合成样本）
V1_START = "<!-- cadence-managed:openspec-superpowers-routing:v1:start -->"
V1_END = "<!-- cadence-managed:openspec-superpowers-routing:v1:end -->"
V2_START = "<!-- cadence-managed:openspec-superpowers-routing:v2:start -->"
V2_END = "<!-- cadence-managed:openspec-superpowers-routing:v2:end -->"
V0_START = "<!-- cadence-managed:openspec-superpowers-routing:v0:start -->"
V0_END = "<!-- cadence-managed:openspec-superpowers-routing:v0:end -->"

# L1 版本标记（单行，位于文件首行）
V1_L1_MARKER = "<!-- cadence-framework-rule:openspec-superpowers-workflow:v1 -->"
V0_L1_MARKER = "<!-- cadence-framework-rule:openspec-superpowers-workflow:v0 -->"
V0_L1_TEXT = V0_L1_MARKER + "\n# 旧版协作规则\n旧版正文\n"


class TestArtifactPathOverrides(unittest.TestCase):
    def test_three_sources_verbatim_consistent(self):
        """ut-override-3src：内核/document-storage/脚本常量三源映射表逐字一致。"""
        refs = Path(__file__).resolve().parents[1] / "references" / "rules"
        kernel = (refs / "agent-routing-kernel.md").read_text()
        doc_storage = (refs / "document-storage.md").read_text()
        table = rc.ARTIFACT_PATH_OVERRIDE_TABLE
        self.assertIn(table, kernel)
        self.assertIn(table, doc_storage)
        self.assertIn("docs/superpowers/specs/", table)
        self.assertIn("cadence/designs/", table)
        self.assertIn("docs/superpowers/plans/", table)
        self.assertIn("cadence/plans/", table)
        self.assertIn("优先级高于任何 Skill 正文", kernel)

    def test_kernel_is_v2(self):
        """ut-kernel-v2：内核标记为 v2。"""
        kernel = (Path(__file__).resolve().parents[1] / "references" / "rules"
                  / "agent-routing-kernel.md").read_text()
        self.assertTrue(kernel.startswith(V2_START))
        self.assertIn("产物自动提交", kernel)

    def test_openspec_path_preserved_in_kernel(self):
        """ut-override-no-skill-rewrite：覆盖声明不改写 Skill 路径（openspec 保留）。"""
        kernel = (Path(__file__).resolve().parents[1] / "references" / "rules"
                  / "agent-routing-kernel.md").read_text()
        self.assertIn("openspec/", kernel)
        self.assertIn("优先级高于任何 Skill 正文", kernel)


class TestCanonicalRules(unittest.TestCase):
    def test_base_rendered_from_canonical_rules(self):
        """验证关键规则条目存在，且渲染结果无 serena 残留。"""
        for entry in ("CLAUDE.md", "AGENTS.md"):
            rendered = rc.render_base_entry(entry, "non-coding", set())
            self.assertIn("### 1. 语言规则", rendered)
            self.assertIn("### 7. 代码阅读规则", rendered)
            self.assertNotIn("serena", rendered.lower())

    def test_rule6_identity_marker(self):
        """ut-rule6-marker：规则 6 以 cadence/project-rules/ 为身份 marker。"""
        markers = dict()
        for m, title, _c, _a in rc.CANONICAL_RULES:
            markers[title] = m
        self.assertIn("cadence/project-rules/", markers["项目个性化规则"])

    def test_playwright_conditional(self):
        """ut-canonical-playwright：playwright.md 存在时清单含第 8 条。"""
        with_pw = rc._canonical_rules_for({"playwright.md"})
        without = rc._canonical_rules_for(set())
        self.assertEqual(len(with_pw), len(without) + 1)
        self.assertIn("playwright.md", with_pw[-1][0])

    def test_retired_list_seed(self):
        """ut-retired-seed：退役清单初始含 serena-usage.md。"""
        self.assertEqual(rc.RETIRED_RULE_FILES, ["serena-usage.md"])


class TestMergeMarkdown(unittest.TestCase):
    """merge_markdown 纯函数兼容测试；适用范围已收窄，不再用于框架受管规则文件。"""

    def test_appends_project_only_sections_in_order(self):
        """ut-merge_markdown-keep-project-sections / NC-02"""
        tpl = "# T\n\n## A\ntpl-a\n\n## B\ntpl-b\n"
        old = "# T\n\n## A\nold-a\n\n## C\nold-c\n"
        out = rc.merge_markdown(tpl, old)
        self.assertIn("tpl-a", out); self.assertIn("## C", out)
        self.assertLess(out.index("## B"), out.index("## C"))
    def test_same_name_section_gets_project_supplement(self):
        """ut-merge_markdown-same-section-append / NC-03"""
        tpl = "## 1. 规则\ntpl-line\n"
        old = "## 1. 规则\ntpl-line\nold-line\n"
        out = rc.merge_markdown(tpl, old)
        self.assertEqual(out.count("tpl-line"), 1)  # 去重
        self.assertIn("项目补充", out); self.assertIn("old-line", out)
    def test_numbering_stripped_for_identity(self):
        """ut-merge_markdown-section-identity / NB-01（去除开头编号后判同名）"""
        self.assertIn("old", rc.merge_markdown("## 规则\nx\n", "## 3. 规则\nx\nold\n"))
    def test_unparseable_returns_none(self):
        """ut-merge_markdown-unparseable-fallback / NC-08（函数级终止信号，备份与标准结构回退由调用方执行）"""
        self.assertIsNone(rc.merge_markdown("# T\nx\n", "\x00\x01binary"))

    def test_target_missing_returns_template(self):
        """ut-merge_markdown-target-missing / NC-01"""
        tpl = "# T\n\n## A\ntpl-a\n"
        self.assertEqual(rc.merge_markdown(tpl, None), tpl)

    def test_duplicate_content_kept_once(self):
        """ut-merge_markdown-dedupe / NC-07"""
        out = rc.merge_markdown("## A\nsame-line\n", "## A\nsame-line\n")
        self.assertEqual(out.count("same-line"), 1)

    def test_different_heading_level_not_same_section(self):
        """ut-merge_markdown-section-identity / NB-01（级别不同不判同名，项目章节原样保留）"""
        out = rc.merge_markdown("## 规则\ntpl\n", "### 规则\nold\n")
        self.assertIn("### 规则", out)
        self.assertIn("old", out)

    def test_mandatory_conflict_template_wins_user_config_preserved(self):
        """ut-merge_markdown-mandatory-override / NC-04"""
        tpl = "## 强制规则\n- 必须使用中文回答 → 详见 `.claude/rules/language.md`\n"
        old = "## 强制规则\n- 旧摘要\n\n## 项目技术栈\n- Python\n"
        out = rc.merge_markdown(tpl, old)
        self.assertIn("必须使用中文回答", out)
        self.assertIn("## 项目技术栈", out)
        self.assertIn("- Python", out)
        self.assertLess(out.index("必须使用中文回答"), out.index("## 项目技术栈"))

    def test_project_only_duplicate_lines_deduped_in_supplement(self):
        """ut-merge_markdown-project-supplement-dedup / NC-07（项目补充部分对项目侧独有行也去重）"""
        # 项目侧同名章节内同一独有行出现两次 → 合并结果只保留一次。
        tpl = "## A\ntpl-line\n"
        old = "## A\ntpl-line\n项目独有X\n项目独有X\n"
        out = rc.merge_markdown(tpl, old)
        self.assertEqual(out.count("项目独有X"), 1)
        self.assertIn("项目补充", out)

    def test_project_multiple_same_name_sections_merged(self):
        """ut-merge_markdown-project-multiple-same-name / NC-02+NC-07（项目侧多个同名章节内容都保留，去重）"""
        # 项目侧两个同名 ## 备注 章节 → 两段内容都保留（去重），不整个丢失。
        tpl = "# T\n\n## 主\n主文\n"
        old = "# T\n\n## 备注\n备注一\n\n## 备注\n备注二\n"
        out = rc.merge_markdown(tpl, old)
        # 两个备注行都保留
        self.assertIn("备注一", out)
        self.assertIn("备注二", out)
        # 只有一个 ## 备注 章节标题（项目独有同名章节合并为一个）
        self.assertEqual(out.count("## 备注"), 1)

    def test_project_multiple_same_name_sections_dedup_overlapping(self):
        """ut-merge_markdown-project-multiple-same-name-dedup / NC-07（多同名章节重叠行去重）"""
        # 项目侧两个同名章节含重叠行 → 重叠行只保留一次。
        tpl = "# T\n\n## 主\n主文\n"
        old = "# T\n\n## 备注\n共享行\n备注一\n\n## 备注\n共享行\n备注二\n"
        out = rc.merge_markdown(tpl, old)
        self.assertEqual(out.count("共享行"), 1)
        self.assertIn("备注一", out)
        self.assertIn("备注二", out)

    def test_no_headings_returns_none(self):
        """ut-merge_markdown-no-headings-fallback / NC-08 + 终审 I-1
        （existing 无任何 ATX 标题但有实质内容 → None，走 NC-08 fallback，不静默丢弃原文）"""
        tpl = "# T\n\n## A\ntpl-a\n"
        self.assertIsNone(rc.merge_markdown(tpl, "无标题用户内容"))
        # 多行无标题内容同样返回 None
        self.assertIsNone(rc.merge_markdown(tpl, "第一行\n第二行\n"))

    def test_substantial_preamble_returns_none(self):
        """ut-merge_markdown-preamble-fallback / NC-08 + 终审 I-1
        （首个标题前有实质前言 → None；parse_sections 会舍弃前言，合并将丢失原文）"""
        tpl = "# T\n\n## A\ntpl-a\n"
        old = "重要前言说明\n\n## A\nold-a\n"
        self.assertIsNone(rc.merge_markdown(tpl, old))

    def test_blank_preamble_still_merges(self):
        """ut-merge_markdown-blank-preamble-ok / 终审 I-1 边界
        （首个标题前仅空白行 → 正常章节合并，不误伤）"""
        tpl = "# T\n\n## A\ntpl-a\n"
        old = "\n\n## A\nold-a\n"
        out = rc.merge_markdown(tpl, old)
        self.assertIsNotNone(out)
        self.assertIn("old-a", out)

    def test_empty_existing_still_returns_template_merge(self):
        """ut-merge_markdown-empty-existing-ok / 终审 I-1 边界
        （existing 为空/纯空白 → 无内容可丢，返回模板合并结果而非 None）"""
        tpl = "# T\n\n## A\ntpl-a\n"
        # render_sections 不保留末尾换行 → 期望为 rstrip 后的模板
        self.assertEqual(rc.merge_markdown(tpl, ""), tpl.rstrip("\n"))
        self.assertEqual(rc.merge_markdown(tpl, "\n\n"), tpl.rstrip("\n"))

    def test_rerun_is_idempotent(self):
        """ut-merge_markdown-rerun-idempotent / NC-03（重跑幂等：merge(t, merge(t, x)) == merge(t, x)）"""
        tpl = "## 规则A\n\n模板行1\n模板行2\n\n## 规则B\n\n模板行3\n"
        old = "## 规则A\n\n模板行1\n模板行2\n\n项目独有行X\n\n## 规则B\n\n模板行3\n\n项目独有行Y\n"
        run1 = rc.merge_markdown(tpl, old)
        run2 = rc.merge_markdown(tpl, run1)
        run3 = rc.merge_markdown(tpl, run2)
        self.assertEqual(run1, run2)
        self.assertEqual(run2, run3)
        # 每个含项目补充的同名章节恰好一个标记行
        self.assertEqual(run2.count("**项目补充**"), 2)

    def test_polluted_file_self_heals(self):
        """ut-merge_markdown-polluted-self-heal / NC-03（历史重复标记污染 → 合并自愈为单标记且内容不丢）"""
        tpl = "## 规则A\n\n模板行1\n"
        polluted = "## 规则A\n\n模板行1\n\n\n**项目补充**\n**项目补充**\n项目独有行X\n"
        out = rc.merge_markdown(tpl, polluted)
        self.assertEqual(out.count("**项目补充**"), 1)
        self.assertIn("项目独有行X", out)
        self.assertEqual(out, rc.merge_markdown(tpl, out))


class TestL0Block(unittest.TestCase):
    def test_skip_when_v2_block_matches_source(self):
        """ut-l0_block-read-source / L0-P1 + L0-P6（v2 标记对且区块与规范源逐字一致）"""
        text = "# CLAUDE.md\n\n文件说明\n\n" + L0_SOURCE + "\n## 强制规则\n- x\n"
        self.assertEqual(rc.l0_block(text, L0_SOURCE), "skip")

    def test_drift_when_v2_markers_but_content_differs(self):
        """ut-l0_block-drift / L0-P7（v2 标记对但区块内容不同）"""
        text = V2_START + "\n本地修改内容\n" + V2_END + "\n"
        self.assertEqual(rc.l0_block(text, L0_SOURCE), "drift")

    def test_insert_when_no_markers(self):
        """ut-l0_block-insert / L0-05（两个标记都不存在）"""
        self.assertEqual(rc.l0_block("# 入口\n无标记内容\n", L0_SOURCE), "insert")

    def test_insert_position_two_branches(self):
        """ut-l0_block-insert-position / L0-P8（有/无 `## 强制规则` 均判 insert；无章节时插在 H1 简介之后）"""
        with_rules = "# 入口\n文件说明\n\n## 强制规则\n- x\n"
        without_rules = "# 入口\n文件说明\n"
        self.assertEqual(rc.l0_block(with_rules, L0_SOURCE), "insert")
        self.assertEqual(rc.l0_block(without_rules, L0_SOURCE), "insert")
        out = rc._insert_l0_block(without_rules, L0_SOURCE)
        self.assertEqual(out, "# 入口\n文件说明\n\n" + L0_SOURCE)

    def test_upgrade_when_v0_old_version_markers(self):
        """ut-l0_block-upgrade / L0-P9（v0 无真实规范源，成对标记维持 upgrade）。"""
        text = V0_START + "\n旧版区块内容\n" + V0_END + "\n"
        self.assertEqual(rc.l0_block(text, L0_SOURCE), "upgrade")

    def test_broken_when_single_side_marker(self):
        """ut-l0_block-broken / L0-P10（当前版本单侧标记）"""
        self.assertEqual(rc.l0_block(V2_START + "\n内容\n", L0_SOURCE), "broken")
        self.assertEqual(rc.l0_block("内容\n" + V2_END + "\n", L0_SOURCE), "broken")

    def test_broken_when_markers_out_of_order(self):
        """ut-l0_block-broken / L0-P10（当前版本标记顺序错误）"""
        text = V2_END + "\n内容\n" + V2_START + "\n"
        self.assertEqual(rc.l0_block(text, L0_SOURCE), "broken")

    def test_skip_requires_verbatim_match_no_strip(self):
        """ut-l0_block-verbatim / L0-P6（逐字比对：首尾空白差异即 drift，不 strip）"""
        # 区块内容与 source 逐字一致 → skip
        text = "# CLAUDE.md\n\n" + L0_SOURCE + "\n## 强制规则\n- x\n"
        self.assertEqual(rc.l0_block(text, L0_SOURCE), "skip")
        # 区块首部多一个空格（被 strip 吞掉的差异）→ 必须判 drift，不能误判 skip
        source_with_leading_space = V2_START + " " + L0_SOURCE[len(V2_START):]
        text_drift = "# CLAUDE.md\n\n" + source_with_leading_space + "\n## 强制规则\n- x\n"
        self.assertEqual(rc.l0_block(text_drift, L0_SOURCE), "drift")


class TestL0V2Migration(unittest.TestCase):
    def test_v1_history_source_loaded(self):
        """ut-l0-v2-history-source：脚本加载冻结 v1 内核全文用于升级前比对。"""
        self.assertEqual(rc.L0_OLD_SOURCES["v1"], L0_V1_SOURCE)

    def test_v1_pair_is_upgrade(self):
        """ut-l0-v2-upgrade：完整 v1 规范块对 v2 源判 upgrade（非 drift）。"""
        self.assertEqual(rc.l0_block(L0_V1_SOURCE, L0_SOURCE), "upgrade")

    def test_v1_pair_with_drift_is_drift(self):
        """ut-l0-v2-v1-drift：v1 成对但正文漂移必须判 drift。"""
        v1_drift = V1_START + "\n旧路由内容\n" + V1_END + "\n"
        self.assertEqual(rc.l0_block(v1_drift, L0_SOURCE), "drift")

    def test_upgrade_yields_single_v2_block(self):
        """ut-l0-v2-single：升级后恰好一个当前版本区块且区块外保留。"""
        v1_text = "# 头\n\n" + V1_START + "\n旧路由\n" + V1_END + "\n\n## 用户章节\nx\n"
        out, warns = rc._normalize_l0_to_single_block(v1_text, L0_SOURCE)
        self.assertEqual(out.count(V2_START), 1)
        self.assertEqual(out.count(V2_END), 1)
        self.assertIn("## 用户章节", out)
        self.assertNotIn("旧路由", out)

    def test_broken_nested_begin_preserves_user_section(self):
        """ut-l0-v2-nested-broken：孤儿 begin 不得跨块吞掉用户章节。"""
        broken = (
            V2_START + "\nbroken\n\n## 用户章节\nx\n\n"
            + V2_START + "\nfull\n" + V2_END
        )
        out, _ = rc._normalize_l0_to_single_block(broken, L0_SOURCE)
        self.assertEqual(out.count(V2_START), 1)
        self.assertEqual(out.count(V2_END), 1)
        self.assertIn("## 用户章节", out)
        self.assertIn("x", out)
        self.assertNotIn("full", out)

    def test_upgrade_orphan_between_v1_pairs_preserves_user_section(self):
        """ut-l0-v2-upgrade-orphan：旧版孤儿 begin 不得跨块吞掉用户章节。"""
        upgrade = (
            L0_V1_SOURCE + "\n\n" + V1_START
            + "\n## 用户章节\nx\n\n" + L0_V1_SOURCE
        )
        self.assertEqual(rc.l0_block(upgrade, L0_SOURCE), "upgrade")
        out, _ = rc._normalize_l0_to_single_block(upgrade, L0_SOURCE)
        self.assertEqual(out.count(V2_START), 1)
        self.assertEqual(out.count(V2_END), 1)
        self.assertIn("## 用户章节", out)
        self.assertIn("x", out)

    def test_overlapping_orphan_end_preserves_all_user_content(self):
        """ut-l0-v2-overlap：完整旧块内的异版孤儿 end 不得使重叠删除吞文本。"""
        overlap = "A\n" + V1_START + "\nX\n" + V2_END + "\nY\n" + V1_END + "\nB\n"
        out, _ = rc._normalize_l0_to_single_block(overlap, L0_SOURCE)
        self.assertEqual(out.count(V2_START), 1)
        self.assertEqual(out.count(V2_END), 1)
        for user_text in ("A", "X", "Y", "B"):
            self.assertIn(user_text, out)

    def test_orphan_current_marker_emits_l0_dedup(self):
        """ut-l0-v2-orphan-dedup：成对块加单侧当前标记会记录 L0_DEDUP。"""
        current_with_orphan = L0_SOURCE + "\n\n" + V2_START + "\n残留用户内容\n"
        out, warns = rc._normalize_l0_to_single_block(current_with_orphan, L0_SOURCE)
        warning = next(w for w in warns if w["code"] == "L0_DEDUP")
        self.assertEqual(warning["detail"]["orphan_markers"], 1)
        self.assertIn("残留用户内容", out)

    def test_mixed_markers_not_broken_residue(self):
        """ut-l0-v2-mixed：旧版成对+当前单侧残留 → 归并为一个规范区块。"""
        mixed = V1_START + "\n旧\n" + V1_END + "\n\n" + V2_START + "\n残留单侧\n"
        out, _ = rc._normalize_l0_to_single_block(mixed, L0_SOURCE)
        self.assertEqual(out.count(V2_START), 1)
        self.assertEqual(out.count(V2_END), 1)

    def test_current_pair_with_old_residue_is_not_skip(self):
        """ut-l0-v2-current-old-residue：当前规范块外旧标记残留必须进入归并路径。"""
        current_with_old_residue = L0_SOURCE + "\n" + V1_START + "\n旧残留\n"
        self.assertEqual(rc.l0_block(current_with_old_residue, L0_SOURCE), "broken")

    def test_duplicate_current_blocks_deduped(self):
        """ut-l0-v2-dedup：重复当前版本区块保留首个 + L0_DEDUP warning。"""
        first = V2_START + "\n首个当前块\n" + V2_END
        second = V2_START + "\n重复当前块\n" + V2_END
        dup = first + "\n\n## 中间\n\n" + second
        out, warns = rc._normalize_l0_to_single_block(dup, L0_SOURCE)
        self.assertEqual(out.count(V2_START), 1)
        self.assertEqual(out.count(V2_END), 1)
        self.assertTrue(any(w["code"] == "L0_DEDUP" for w in warns))
        self.assertIn("首个当前块", out)
        self.assertNotIn("重复当前块", out)
        self.assertIn("## 中间", out)

    def test_duplicate_current_blocks_classified_for_normalization(self):
        """ut-l0-v2-dedup-state：重复 v2 成对块走确定性 dedup，不可误判 skip/drift。"""
        dup = L0_SOURCE + "\n\n" + L0_SOURCE
        self.assertEqual(rc.l0_block(dup, L0_SOURCE), "dedup")

    def test_v2_skip_idempotent(self):
        """ut-l0-v2-skip：v2 与源一致判 skip。"""
        self.assertEqual(rc.l0_block(L0_SOURCE, L0_SOURCE), "skip")


class TestL0InsertPosition(unittest.TestCase):
    def test_insert_after_intro_when_no_section(self):
        """ut-l0-pos：无 ## 强制规则 时 L0 位于 H1+简介之后、用户内容之前。"""
        text = "# KB\n\n项目简介段落。\n\n## NOTES\n\n- 用户内容\n"
        out = rc._insert_l0_block(text, L0_SOURCE)
        idx_l0 = out.index("<!-- cadence-managed")
        idx_notes = out.index("## NOTES")
        idx_intro = out.index("项目简介段落。")
        self.assertLess(idx_intro, idx_l0)
        self.assertLess(idx_l0, idx_notes)  # 不再追加到文件末尾

    def test_insert_at_start_without_h1(self):
        """无 H1 时防御性地将 L0 插入文首。"""
        out = rc._insert_l0_block("用户内容\n", L0_SOURCE)
        self.assertTrue(out.startswith(L0_SOURCE))

    def test_global_order_end_to_end(self):
        """ut-global-order：H1/说明 → L0 → 强制规则 → 用户内容。"""
        import tempfile, subprocess
        from pathlib import Path
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "AGENTS.md").write_text("# KB\n\n简介。\n\n## NOTES\n\n- 用户内容\n")
            subprocess.run(["python3", str(SCRIPT_PATH), "apply", "--project-root", str(root),
                            "--report", str(Path(td).parent / "r.json"), "--no-interrupt"], check=True)
            out = (root / "AGENTS.md").read_text()
            i1, i2, i3 = out.index("<!-- cadence-managed"), out.index("## 强制规则"), out.index("## NOTES")
            self.assertLess(i1, i2)
            self.assertLess(i2, i3)


class TestMergeYaml(unittest.TestCase):
    def test_appends_template_rules_dedup_preserving_order(self):
        """ut-merge_yaml-rules-append / OS-N7"""
        existing = "schema: spec-driven\ncontext: |\n  line1\nrules:\n  proposal:\n    - keep-me\n"
        merged, conflicts = rc.merge_yaml(TPL, existing)
        doc = yaml.safe_load(merged)
        self.assertEqual(doc["rules"]["proposal"][0], "keep-me")
        self.assertIn("记录 Why、范围、非目标和受影响 capability；不要写精确文件级实施步骤。", doc["rules"]["proposal"])
    def test_rules_apply_reported_as_conflict(self):
        """ut-merge_yaml-rules-apply-conflict / NC-05 + OS-N8（函数级只报告冲突，备份与移除由调用方执行）"""
        _, conflicts = rc.merge_yaml(TPL, "rules:\n  apply:\n    - x\n")
        self.assertEqual(conflicts[0]["kind"], "rules.apply")

    def test_preserve_existing_schema_context_and_extra_rules(self):
        """ut-merge_yaml-preserve-existing / NC-05"""
        existing = "schema: custom-schema\ncontext: |\n  项目上下文行\nrules:\n  proposal:\n    - 项目额外规则\n"
        merged, _ = rc.merge_yaml(TPL, existing)
        doc = yaml.safe_load(merged)
        self.assertEqual(doc["schema"], "custom-schema")
        self.assertIn("项目上下文行", doc["context"])
        self.assertIn("项目额外规则", doc["rules"]["proposal"])

    def test_unparseable_returns_abort_signal(self):
        """ut-merge_yaml-unparseable-abort / NC-06（函数级终止信号；目标文件 sha256 不变与备份由调用方保证）"""
        merged, _ = rc.merge_yaml(TPL, "rules: [unclosed\n")
        self.assertIsNone(merged)

    def test_schema_written_when_missing(self):
        """ut-merge_yaml-schema-default / OS-N5（缺失时写入 spec-driven）"""
        merged, _ = rc.merge_yaml(TPL, "context: |\n  x\n")
        self.assertEqual(yaml.safe_load(merged)["schema"], "spec-driven")

    def test_context_append_dedup_preserving_order(self):
        """ut-merge_yaml-context-append / OS-N6（按完整行去重，保留原顺序与项目上下文）"""
        first_tpl_line = "OpenSpec 是契约层：proposal 记录 Why、范围和非目标，design 记录架构边界与权衡，specs 记录 MUST/SHALL 验收场景，tasks 只记录高层工作包。"
        existing = "context: |\n  项目上下文行\n  " + first_tpl_line + "\n"
        merged, _ = rc.merge_yaml(TPL, existing)
        doc = yaml.safe_load(merged)
        self.assertEqual(doc["context"].count(first_tpl_line), 1)
        self.assertLess(doc["context"].index("项目上下文行"), doc["context"].index(first_tpl_line))

    def test_all_four_artifact_groups_present(self):
        """ut-merge_yaml-rules-append / OS-N7（四个 artifact 分组均补齐模板规则）"""
        merged, _ = rc.merge_yaml(TPL, "schema: spec-driven\n")
        doc = yaml.safe_load(merged)
        for group in ("proposal", "design", "specs", "tasks"):
            self.assertIn(group, doc["rules"])
            self.assertTrue(doc["rules"][group])

    def test_rules_append_dedup_and_extra_preserved(self):
        """ut-merge_yaml-rules-append / OS-N7（数组按完整字符串去重，顺序稳定）"""
        existing = "rules:\n  proposal:\n    - 记录 Why、范围、非目标和受影响 capability；不要写精确文件级实施步骤。\n    - 项目额外规则\n"
        merged, _ = rc.merge_yaml(TPL, existing)
        doc = yaml.safe_load(merged)
        self.assertEqual(doc["rules"]["proposal"].count("记录 Why、范围、非目标和受影响 capability；不要写精确文件级实施步骤。"), 1)
        self.assertEqual(doc["rules"]["proposal"][0], "记录 Why、范围、非目标和受影响 capability；不要写精确文件级实施步骤。")
        self.assertEqual(doc["rules"]["proposal"][1], "项目额外规则")

    def test_missing_pyyaml_exits_77(self):
        """ut-merge_yaml-missing-dependency / XC-06（PyYAML 缺失时退出码恰为 77 且 stderr 说明）"""
        code = (
            "import sys; sys.modules['yaml'] = None; "
            "import runpy; runpy.run_path(sys.argv[1], run_name='__main__')"
        )
        proc = subprocess.run(
            [sys.executable, "-c", code, str(SCRIPT_PATH)],
            capture_output=True, text=True,
        )
        self.assertEqual(proc.returncode, 77)
        self.assertIn("yaml", (proc.stderr + proc.stdout).lower())


class TestPrecheckOpenspecStructure(unittest.TestCase):
    def test_type_conflict_listed(self):
        """ut-precheck_openspec_structure-type-matrix / OS-N2"""
        self.assertIn("rules.proposal", rc.precheck_openspec_structure({"rules": {"proposal": "not-a-list"}}))

    def test_valid_full_document_passes(self):
        """ut-precheck_openspec_structure-type-matrix / OS-N2（合法文档零冲突；自定义键原样保留）"""
        doc = {
            "schema": "spec-driven",
            "context": "ctx",
            "rules": {"proposal": ["a"], "design": ["b"], "specs": ["c"], "tasks": ["d"]},
            "custom-key": {"anything": [1, 2]},
        }
        self.assertEqual(rc.precheck_openspec_structure(doc), [])

    def test_empty_document_passes(self):
        """ut-precheck_openspec_structure-type-matrix / OS-N2（全部字段缺失均合法）"""
        self.assertEqual(rc.precheck_openspec_structure({}), [])

    def test_schema_scalar_passes(self):
        """ut-precheck_openspec_structure-type-matrix / OS-N2（schema 可保留标量）"""
        self.assertEqual(rc.precheck_openspec_structure({"schema": 1}), [])

    def test_root_must_be_mapping(self):
        """ut-precheck_openspec_structure-type-matrix / OS-N2（根非映射必报冲突）"""
        self.assertTrue(rc.precheck_openspec_structure(["not-a-mapping"]))

    def test_schema_must_be_scalar(self):
        """ut-precheck_openspec_structure-type-matrix / OS-N2"""
        self.assertIn("schema", rc.precheck_openspec_structure({"schema": ["x"]}))

    def test_context_must_be_string(self):
        """ut-precheck_openspec_structure-type-matrix / OS-N2"""
        self.assertIn("context", rc.precheck_openspec_structure({"context": {"k": 1}}))

    def test_rules_must_be_mapping(self):
        """ut-precheck_openspec_structure-type-matrix / OS-N2"""
        self.assertIn("rules", rc.precheck_openspec_structure({"rules": "x"}))

    def test_artifact_items_must_be_strings(self):
        """ut-precheck_openspec_structure-type-matrix / OS-N2（四个 artifact 必须为字符串数组）"""
        self.assertIn("rules.design", rc.precheck_openspec_structure({"rules": {"design": [1]}}))


class TestBackupFile(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "proj"
        self.root.mkdir()

    def test_backup_naming_and_original_kept(self):
        """ut-backup_file-naming / NB-02（归档路径含时间戳；原文件仍在且 sha256 不变）"""
        p = self.root / "rule.md"
        p.write_text("content\n")
        before = rc.sha256_file(p)
        backup = rc.backup_file(p, self.root)
        self.assertRegex(
            str(backup.relative_to(self.root)),
            r"^cadence/legacy/\d{14}/rule\.md$",
        )
        self.assertTrue(p.exists())
        self.assertEqual(rc.sha256_file(p), before)
        self.assertEqual(Path(backup).read_text(), "content\n")

    def test_backup_openspec_naming(self):
        """ut-backup_file-openspec-naming / OS-B1（归档保留 openspec/config.yaml 相对路径）"""
        d = self.root / "openspec"
        d.mkdir()
        p = d / "config.yaml"
        p.write_text("schema: spec-driven\n")
        backup = rc.backup_file(p, self.root)
        self.assertRegex(
            str(backup.relative_to(self.root)),
            r"^cadence/legacy/\d{14}/openspec/config\.yaml$",
        )

    def test_backup_l1_naming(self):
        """ut-backup_file-l1-naming / L1-B1（归档保留 .claude/rules 相对路径）"""
        d = self.root / ".claude" / "rules"
        d.mkdir(parents=True)
        p = d / "openspec-superpowers-workflow.md"
        p.write_text(L1_V1)
        backup = rc.backup_file(p, self.root)
        self.assertRegex(
            str(backup.relative_to(self.root)),
            r"^cadence/legacy/\d{14}/\.claude/rules/openspec-superpowers-workflow\.md$",
        )

    def test_backup_copies_to_legacy_with_relative_path(self):
        """ut-backup_file-legacy-copy / B2：复制归档，原位不动，相对路径结构"""
        (self.root / ".claude" / "rules").mkdir(parents=True)
        target = self.root / ".claude" / "rules" / "mcp-servers.md"
        target.write_text("old content", encoding="utf-8")

        backup_path = rc.backup_file(target, self.root)

        self.assertIn("cadence/legacy", str(backup_path))
        self.assertIn(".claude/rules/mcp-servers.md", str(backup_path))
        self.assertEqual(backup_path.read_text(encoding="utf-8"), "old content")
        self.assertEqual(target.read_text(encoding="utf-8"), "old content")  # 原位不动

    def test_backup_creates_and_repairs_gitignore(self):
        """ut-backup_file-legacy-gitignore / 每次归档前验证/修复 .gitignore"""
        (self.root / ".claude" / "rules").mkdir(parents=True)
        target = self.root / ".claude" / "rules" / "language.md"
        target.write_text("x", encoding="utf-8")
        rc.backup_file(target, self.root)
        gi = self.root / "cadence" / "legacy" / ".gitignore"
        self.assertEqual(gi.read_text(encoding="utf-8"), "*\n!.gitignore\n")
        # 损坏后再次归档自动修复
        gi.write_text("wrong", encoding="utf-8")
        rc.backup_file(target, self.root)
        self.assertEqual(gi.read_text(encoding="utf-8"), "*\n!.gitignore\n")

    def test_backup_gitignore_write_failure_raises_backup_error(self):
        """ut-backup_file-legacy-gitignore-fail / .gitignore 写失败统一包装 BackupError"""
        target = self.root / "rule.md"
        target.write_text("content\n", encoding="utf-8")
        with mock.patch.object(rc, "atomic_write", side_effect=rc.PublishError("write failed")):
            with self.assertRaises(rc.BackupError):
                rc.backup_file(target, self.root)

    def test_backup_same_second_unique_suffix(self):
        """ut-backup_file-unique-suffix / codex 终审 C1
        （同秒同文件重复备份 → 时间戳目录追加 -2/-3，三个恢复点互不覆盖）"""
        p = self.root / "config.yaml"
        p.write_text("v1\n")
        fixed = rc.datetime(2026, 7, 31, 12, 0, 0)
        with mock.patch.object(rc, "datetime") as mdt:
            mdt.now.return_value = fixed
            b1 = rc.backup_file(p, self.root)
            p.write_text("v2\n")
            b2 = rc.backup_file(p, self.root)
            p.write_text("v3\n")
            b3 = rc.backup_file(p, self.root)
        # 三个归档路径两两不同且全部存在（首次恢复点未被覆盖）
        names = [str(b) for b in (b1, b2, b3)]
        self.assertEqual(len(set(names)), 3)
        for b in (b1, b2, b3):
            self.assertTrue(Path(b).exists())
        # 同秒冲突后缀加在时间戳目录，而不是文件名
        self.assertEqual(Path(b1).parent.name, "20260731120000")
        self.assertEqual(Path(b2).parent.name, "20260731120000-2")
        self.assertEqual(Path(b3).parent.name, "20260731120000-3")
        self.assertEqual(Path(b1).name, "config.yaml")
        self.assertEqual(Path(b2).name, "config.yaml")
        self.assertEqual(Path(b3).name, "config.yaml")
        # 内容未被覆盖：每个备份保留各自时点内容
        self.assertEqual(Path(b1).read_text(), "v1\n")
        self.assertEqual(Path(b2).read_text(), "v2\n")
        self.assertEqual(Path(b3).read_text(), "v3\n")


class TestAtomicWrite(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def test_publish_content_consistent(self):
        """ut-atomic_write-publish / OS-N11（原子创建，发布后内容一致）"""
        target = Path(self.tmp.name) / "new.yaml"
        rc.atomic_write(target, "schema: spec-driven\n")
        self.assertEqual(target.read_text(), "schema: spec-driven\n")

    def test_replace_existing_atomically(self):
        """ut-atomic_write-replace / XC-07（经原子替换覆盖已有目标）"""
        target = Path(self.tmp.name) / "f.txt"
        target.write_text("old\n")
        rc.atomic_write(target, "new\n")
        self.assertEqual(target.read_text(), "new\n")

    def test_fail_readonly_dir_keeps_original(self):
        """ut-atomic_write-fail / OS-N13（fx-readonly-target：chmod 555 复现发布失败，原文件保持）"""
        d = Path(self.tmp.name) / "readonly"
        d.mkdir()
        target = d / "config.yaml"
        target.write_text("original\n")
        os.chmod(d, 0o555)
        self.addCleanup(os.chmod, d, 0o755)
        with self.assertRaises(OSError):
            rc.atomic_write(target, "new\n")
        self.assertEqual(target.read_text(), "original\n")


class TestSha256File(unittest.TestCase):
    def test_sha256_matches_hashlib(self):
        """ut-sha256_file-basic / XC-07（结果与 hashlib/系统工具一致）"""
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "f.txt"
            p.write_bytes(b"hello cadence\n")
            self.assertEqual(rc.sha256_file(p), hashlib.sha256(b"hello cadence\n").hexdigest())


class TestClassifyL1(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.known = {"v0": V0_L1_TEXT}

    def _write(self, content):
        p = Path(self.tmp.name) / "openspec-superpowers-workflow.md"
        p.write_text(content)
        return p

    def test_current_v1_returns_skip(self):
        """ut-classify_l1-current / L1-02（完整内容与当前框架 v1 一致）"""
        p = self._write(L1_V1)
        self.assertEqual(rc.classify_l1(p, L1_V1, self.known), "skip")

    def test_known_old_version_returns_upgrade(self):
        """ut-classify_l1-old-version / L1-03（完整内容与注入的 known_versions 旧版逐字一致）"""
        p = self._write(V0_L1_TEXT)
        self.assertEqual(rc.classify_l1(p, L1_V1, self.known), "upgrade")

    def test_old_marker_drift_returns_replace(self):
        """ut-classify_l1-old-marker-drift / L1-04（仅旧版标记匹配但内容不同 → 不匹配 → replace）"""
        p = self._write(V0_L1_MARKER + "\n# 漂移内容\n")
        self.assertEqual(rc.classify_l1(p, L1_V1, self.known), "replace")

    def test_v1_marker_drift_returns_replace(self):
        """ut-classify_l1-v1-marker-drift / L1-05（v1 标记存在但完整内容不同 → 不得当作 current）"""
        p = self._write(V1_L1_MARKER + "\n# 漂移内容\n")
        self.assertEqual(rc.classify_l1(p, L1_V1, self.known), "replace")

    def test_unmarked_returns_replace(self):
        """ut-classify_l1-unmarked / L1-06（无标记文件不得当作已知框架版本）"""
        p = self._write("# 无标记文件\ncontent\n")
        self.assertEqual(rc.classify_l1(p, L1_V1, self.known), "replace")

    def test_classification_by_full_content_not_marker(self):
        """ut-classify_l1-full-compare / L1-B2（标记只定位候选版本，最终识别必须比较完整内容）"""
        drift = self._write(V1_L1_MARKER + "\n篡改内容\n")
        self.assertEqual(rc.classify_l1(drift, L1_V1, self.known), "replace")
        exact_old = self._write(V0_L1_TEXT)
        self.assertEqual(rc.classify_l1(exact_old, L1_V1, self.known), "upgrade")


# ---------------------------------------------------------------------------
# Task 5：detect_project / locate_templates 纯函数单测（ut-detect_project-* / ut-locate_templates-*）
# 用例清单来源：tests/skill-clause-map.md §2.8（S1a-01~05 / S1b-01~04）与 §2.5/2.6（DF-01/02、IA-02）。
# 加载方式与 Task 4 一致；测试自建临时 fixture，不依赖仓库实际环境。
# ---------------------------------------------------------------------------

# locate_templates 成对校验所需的最小文件集（在线/离线路径三件套 + config.yaml）
_ONLINE_RULES = ("agent-routing-kernel.md", "language.md", "openspec-superpowers-workflow.md")
# 回退 glob 路径额外需要 document-storage.md（S1b-02）
_FALLBACK_EXTRA = ("document-storage.md",)


def _write_minimal_templates(rules_dir: Path, *, fallback: bool = False) -> None:
    """在 rules_dir 下创建成对校验所需的最小模板占位文件 + 同级 openspec/config.yaml。"""
    rules_dir.mkdir(parents=True, exist_ok=True)
    for name in _ONLINE_RULES:
        (rules_dir / name).write_text(f"# placeholder {name}\n", encoding="utf-8")
    if fallback:
        for name in _FALLBACK_EXTRA:
            (rules_dir / name).write_text(f"# placeholder {name}\n", encoding="utf-8")
    openspec_dir = rules_dir.parent / "openspec"
    openspec_dir.mkdir(parents=True, exist_ok=True)
    (openspec_dir / "config.yaml").write_text("schema: spec-driven\n", encoding="utf-8")


def _intents(**overrides):
    """构造 rc.Intents，默认空意图。"""
    defaults = dict(
        no_interrupt=False,
        project_type=None,
        ignore_cadence=False,
        enable_playwright=False,
        enable_codegraph=False,
        decisions=None,
    )
    defaults.update(overrides)
    return rc.Intents(**defaults)


class TestAuthoritativeOverwrite(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "proj"
        self.rules_root = Path(self.tmp.name) / "tpl"
        real_tpl = Path(__file__).resolve().parents[1] / "references" / "rules"
        self.rules_root.mkdir(parents=True)
        for f in real_tpl.iterdir():
            if f.is_file():
                (self.rules_root / f.name).write_bytes(f.read_bytes())
        self.openspec_yaml = (
            Path(__file__).resolve().parents[1]
            / "references" / "openspec" / "config.yaml"
        )
        self.mcp_tpl = (self.rules_root / "mcp-servers.md").read_text(
            encoding="utf-8"
        )

    def _apply(self):
        report = rc.build_report("no-interrupt", self.root)
        with mock.patch.object(
            rc,
            "locate_templates",
            return_value=(self.rules_root, self.openspec_yaml),
        ):
            result = rc.run_apply(
                self.root, _intents(no_interrupt=True), report
            )
        self.assertEqual(result, 0, report.get("failure"))
        return report

    def test_drift_overwrite_no_supplement(self):
        """ut-s3-authoritative-overwrite / RF-05：drift 全覆盖，无项目补充"""
        rules = self.root / ".claude" / "rules"
        rules.mkdir(parents=True)
        (rules / "mcp-servers.md").write_text(
            "### Serena MCP\nold\n", encoding="utf-8"
        )
        self._apply()
        content = (rules / "mcp-servers.md").read_text(encoding="utf-8")
        self.assertEqual(content, self.mcp_tpl)
        self.assertNotIn("Serena", content)
        self.assertNotIn("**项目补充**", content)
        self.assertTrue(
            any((self.root / "cadence" / "legacy").rglob("mcp-servers.md"))
        )

    def test_idempotent_skip_when_equal_template(self):
        """ut-s3-authoritative-idempotent / 内容==模板则跳过不归档"""
        rules = self.root / ".claude" / "rules"
        rules.mkdir(parents=True)
        (rules / "mcp-servers.md").write_text(
            self.mcp_tpl, encoding="utf-8"
        )
        self._apply()
        self.assertFalse((self.root / "cadence" / "legacy").exists())

    def test_legacy_code_usage_migrated_custom_kept(self):
        """历史 code-usage 双文件归档后移除；归档路径入报告；相似自定义文件保持不动。"""
        rules = self.root / ".claude" / "rules"
        rules.mkdir(parents=True)
        coding_legacy = rules / "code-usage-coding.md"
        noncoding_legacy = rules / "code-usage-noncoding.md"
        coding_legacy.write_text(
            "legacy", encoding="utf-8"
        )
        noncoding_legacy.write_text(
            "legacy", encoding="utf-8"
        )
        (rules / "code-usage-extra.md").write_text(
            "user custom", encoding="utf-8"
        )
        report = self._apply()
        self.assertFalse(coding_legacy.exists())
        self.assertFalse(noncoding_legacy.exists())
        coding_archives = list(
            (self.root / "cadence" / "legacy").rglob(
                "code-usage-coding.md"
            )
        )
        noncoding_archives = list(
            (self.root / "cadence" / "legacy").rglob(
                "code-usage-noncoding.md"
            )
        )
        self.assertTrue(coding_archives)
        self.assertTrue(noncoding_archives)
        expected_backups = {
            (str(coding_legacy), str(coding_archives[0])),
            (str(noncoding_legacy), str(noncoding_archives[0])),
        }
        reported_backups = {
            (item.get("file"), item.get("backup"))
            for item in report["backups"]
        }
        self.assertTrue(expected_backups.issubset(reported_backups))
        s3 = next(
            step for step in report["steps"]
            if step["name"] == rc.STEP_RULES_FILES
        )
        migrated = {
            action["path"]: action.get("backup")
            for action in s3.get("actions", [])
            if action.get("action") == "migrated-legacy"
        }
        self.assertEqual(
            migrated[".claude/rules/code-usage-coding.md"],
            str(coding_archives[0]),
        )
        self.assertEqual(
            migrated[".claude/rules/code-usage-noncoding.md"],
            str(noncoding_archives[0]),
        )
        self.assertEqual(
            coding_archives[0].read_text(encoding="utf-8"), "legacy"
        )
        self.assertEqual(
            noncoding_archives[0].read_text(encoding="utf-8"), "legacy"
        )
        self.assertEqual(
            (rules / "code-usage-extra.md").read_text(encoding="utf-8"),
            "user custom",
        )


class TestCodeUsageSingleSource(unittest.TestCase):
    """Task 2：code-usage 单选来源、固定落地名与 S3 资产来源字段。"""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "proj"
        self.rules_root = Path(self.tmp.name) / "tpl"
        real_tpl = Path(__file__).resolve().parents[1] / "references" / "rules"
        self.rules_root.mkdir(parents=True)
        for template in real_tpl.iterdir():
            if template.is_file():
                (self.rules_root / template.name).write_bytes(template.read_bytes())
        self.openspec_yaml = (
            Path(__file__).resolve().parents[1]
            / "references" / "openspec" / "config.yaml"
        )

    def _apply(self, **overrides):
        report = rc.build_report(
            "no-interrupt" if overrides.get("no_interrupt") else "normal",
            self.root,
        )
        with mock.patch.object(
            rc,
            "locate_templates",
            return_value=(self.rules_root, self.openspec_yaml),
        ), mock.patch.object(
            rc.subprocess,
            "run",
            return_value=mock.Mock(returncode=0),
        ):
            result = rc.run_apply(self.root, _intents(**overrides), report)
        self.assertEqual(result, 0, report.get("failure"))
        return report

    def _compute(self, **overrides):
        with mock.patch.object(
            rc,
            "locate_templates",
            return_value=(self.rules_root, self.openspec_yaml),
        ):
            return rc.compute_plan(self.root, _intents(**overrides))

    def test_coding_project_gets_code_usage_md(self):
        self.root.mkdir(parents=True)
        (self.root / "package.json").write_text(
            '{"scripts":{"test":"jest"}}', encoding="utf-8"
        )
        self._apply(no_interrupt=True)
        target = self.root / ".claude" / "rules" / "code-usage.md"
        self.assertTrue(target.exists())
        self.assertIn("遵循 TDD", target.read_text(encoding="utf-8"))
        self.assertFalse(
            (self.root / ".claude" / "rules" / "code-usage-coding.md").exists()
        )
        self.assertFalse(
            (self.root / ".claude" / "rules" / "code-usage-noncoding.md").exists()
        )

    def test_noncoding_project_gets_noncoding_source_at_fixed_name(self):
        self.root.mkdir(parents=True)
        self._apply(no_interrupt=True)
        target = self.root / ".claude" / "rules" / "code-usage.md"
        self.assertTrue(target.exists())
        self.assertIn("非必要不编写代码", target.read_text(encoding="utf-8"))
        self.assertFalse(
            (self.root / ".claude" / "rules" / "code-usage-coding.md").exists()
        )
        self.assertFalse(
            (self.root / ".claude" / "rules" / "code-usage-noncoding.md").exists()
        )

    def test_code_usage_asset_records_selected_template_source(self):
        self.root.mkdir(parents=True)
        plan = self._compute(project_type="coding")
        assets = plan["steps"][rc.STEP_RULES_FILES]["assets"]
        asset = next(a for a in assets if a["path"].endswith("/code-usage.md"))
        self.assertEqual(asset["template_source"], "code-usage-coding.md")
        self.assertEqual(Path(asset["path"]).name, "code-usage.md")

    def test_agent_routing_kernel_not_copied(self):
        self.root.mkdir(parents=True)
        self._apply(no_interrupt=True)
        self.assertFalse(
            (self.root / ".claude" / "rules" / "agent-routing-kernel.md").exists()
        )
        self.assertIn(
            "cadence-managed:openspec-superpowers-routing:v2",
            (self.root / "CLAUDE.md").read_text(encoding="utf-8"),
        )

    def test_existing_playwright_enters_unified_drift_detection(self):
        target = self.root / ".claude" / "rules" / rc.PLAYWRIGHT_RULE_FILE
        target.parent.mkdir(parents=True)
        target.write_text("# 项目自定义 Playwright\n", encoding="utf-8")
        plan = self._compute()
        assets = plan["steps"][rc.STEP_RULES_FILES]["assets"]
        asset = next(a for a in assets if a["path"].endswith("/playwright.md"))
        self.assertEqual(asset["action"], "replace")
        self.assertEqual(asset["conflict"], "drift")
        self.assertTrue(asset["backup_needed"])
        self.assertEqual(asset["template_source"], "playwright.md")


class TestDetectProject(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    # --- ut-detect_project-coding / DF-01（检测到源码 → Coding）---
    def test_source_file_detected_as_coding(self):
        """ut-detect_project-coding / DF-01（首命中源码即判 Coding；evidence 记录相对路径）"""
        (self.root / "app").mkdir()
        (self.root / "app" / "main.py").write_text("print('hi')\n")
        result = rc.detect_project(self.root, _intents())
        self.assertEqual(result["project_type"], "coding")
        self.assertIsInstance(result["evidence"], str)
        self.assertTrue(result["evidence"])  # 非空证据
        self.assertNotIn("tech_stack", result)

    # --- ut-detect_project-noncoding / DF-01（无源码无主配置 → 非 Coding）---
    def test_empty_project_is_noncoding(self):
        """ut-detect_project-noncoding / DF-01（无源码无主配置 → non-coding）"""
        (self.root / "README.md").write_text("docs only\n")
        result = rc.detect_project(self.root, _intents())
        self.assertEqual(result["project_type"], "non-coding")

    # --- ut-detect_project-bounded-scan / S1a-01（剪枝目录内源码不触发；首命中即停）---
    def test_pruned_dirs_skipped_and_first_match_stops(self):
        """ut-detect_project-bounded-scan / S1a-01（剪枝目录内源码不触发 Coding；首命中即返回）"""
        # node_modules 内有 .js（应被剪枝，不触发）
        nm = self.root / "node_modules" / "pkg"
        nm.mkdir(parents=True)
        (nm / "index.js").write_text("module.exports = 1;\n")
        # .venv 内有 .py（应被剪枝）
        venv = self.root / ".venv" / "lib"
        venv.mkdir(parents=True)
        (venv / "x.py").write_text("x = 1\n")
        result = rc.detect_project(self.root, _intents())
        self.assertEqual(result["project_type"], "non-coding")
        # 加入一个真实源码后应立即判 coding（首命中即停）
        src = self.root / "src"
        src.mkdir()
        (src / "a.ts").write_text("export const x = 1;\n")
        result2 = rc.detect_project(self.root, _intents())
        self.assertEqual(result2["project_type"], "coding")

    # --- ut-detect_project-main-config / S1a-03（仅主工程配置即判 Coding）---
    def test_main_config_without_source_is_coding(self):
        """ut-detect_project-main-config / S1a-03（仅 package.json/pyproject.toml 即判 Coding；evidence 记主配置）"""
        (self.root / "package.json").write_text('{"name": "demo"}\n', encoding="utf-8")
        result = rc.detect_project(self.root, _intents())
        self.assertEqual(result["project_type"], "coding")
        self.assertIn("package.json", result["evidence"])

    # --- ut-detect_project-ignores-cli / IA-02（重构：detect 只返回检测结果，CLI 完全不参与）---
    def test_detect_ignores_cli_project_type(self):
        """ut-detect_project-ignores-cli / IA-02 重构（detect_project 只做自动检测；
        intents.project_type 不影响检测结果，也不产生任何冲突）"""
        (self.root / "app.py").write_text("x = 1\n")  # 检测应为 coding
        # CLI 写 non-coding，检测结果仍应为 coding，且不再产 s1 冲突
        result = rc.detect_project(self.root, _intents(project_type="non-coding"))
        self.assertEqual(result["project_type"], "coding")
        self.assertIsNone(result.get("conflict"))

    # --- ut-detect_project-no-conflict-key / IA-02 重构（conflict 字段不再产生）---
    def test_detect_never_produces_project_type_conflict(self):
        """ut-detect_project-no-conflict / IA-02 重构（任意 detect+CLI 组合都不产冲突）

        用户裁决：删除 s1:project-type-conflict 机制；detect 只返回检测结果。
        """
        (self.root / "app.py").write_text("x = 1\n")  # 检测 coding + CLI non-coding
        for cli in (None, "coding", "non-coding"):
            result = rc.detect_project(self.root, _intents(project_type=cli))
            self.assertEqual(result["project_type"], "coding")
            self.assertIsNone(result.get("conflict"))



class TestLocateTemplates(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.home = Path(self.tmp.name) / "fakehome"
        self.home.mkdir()
        # 记录原始 HOME，用 addCleanup 恢复
        self._orig_home = os.environ.get("HOME")
        os.environ["HOME"] = str(self.home)
        self.addCleanup(self._restore_home)

    def _restore_home(self):
        if self._orig_home is None:
            os.environ.pop("HOME", None)
        else:
            os.environ["HOME"] = self._orig_home

    # --- ut-locate_templates-online / S1b-01（在线路径优先命中）---
    def test_online_path_preferred(self):
        """ut-locate_templates-online / S1b-01（在线 marketplace 路径完整时优先返回）"""
        online = (
            self.home / ".claude" / "plugins" / "marketplaces" / "cadence-skills-marketplace"
            / "cadence-init" / "skills" / "rule-config" / "references" / "rules"
        )
        _write_minimal_templates(online)
        rules_root, openspec_yaml = rc.locate_templates()
        self.assertEqual(rules_root, online)
        self.assertTrue(openspec_yaml.exists())
        self.assertEqual(openspec_yaml.name, "config.yaml")

    # --- ut-locate_templates-offline / S1b-01（离线路径命中）---
    def test_offline_path_used_when_online_missing(self):
        """ut-locate_templates-offline / S1b-01（在线缺失时回退到离线 cadence-skills-local）"""
        offline = (
            self.home / ".claude" / "plugins" / "marketplaces" / "cadence-skills-local"
            / "cadence-init" / "skills" / "rule-config" / "references" / "rules"
        )
        _write_minimal_templates(offline)
        rules_root, _ = rc.locate_templates()
        self.assertEqual(rules_root, offline)

    # --- ut-locate_templates-fallback / S1b-01（glob 回退；需 document-storage.md）---
    def test_glob_fallback_when_fixed_paths_missing(self):
        """ut-locate_templates-fallback / S1b-01（固定路径均缺失时 glob 回退；候选需含 document-storage.md）"""
        # 在 fakehome 下构造一个 glob 可命中的候选（带 document-storage.md）
        dev_candidate = (
            self.home / "workspace" / "proj" / "cadence-init" / "skills"
            / "rule-config" / "references" / "rules"
        )
        _write_minimal_templates(dev_candidate, fallback=True)
        rules_root, _ = rc.locate_templates()
        self.assertEqual(rules_root, dev_candidate)

    # --- ut-locate_templates-pair-check / S1b-02（缺成对文件或 config.yaml 的候选被跳过）---
    def test_incomplete_candidate_skipped(self):
        """ut-locate_templates-pair-check / S1b-02（在线候选缺 config.yaml → 跳过；落到 glob 回退完整候选）"""
        # 在线候选缺 config.yaml（不写 openspec/config.yaml）
        online_rules = (
            self.home / ".claude" / "plugins" / "marketplaces" / "cadence-skills-marketplace"
            / "cadence-init" / "skills" / "rule-config" / "references" / "rules"
        )
        online_rules.mkdir(parents=True)
        for name in _ONLINE_RULES:
            (online_rules / name).write_text("# x\n")
        # 故意不写 openspec/config.yaml → 该候选不完整
        # glob 回退候选完整（带 document-storage.md + config.yaml）
        dev_candidate = (
            self.home / "workspace" / "proj" / "cadence-init" / "skills"
            / "rule-config" / "references" / "rules"
        )
        _write_minimal_templates(dev_candidate, fallback=True)
        rules_root, _ = rc.locate_templates()
        self.assertEqual(rules_root, dev_candidate)

    # --- ut-locate_templates-mtime-latest / S1b-03（多候选取 mtime 最新）---
    def test_multiple_candidates_pick_latest_mtime(self):
        """ut-locate_templates-mtime-latest / S1b-03（glob 多候选通过校验后取修改时间最新者）"""
        old_candidate = (
            self.home / "workspace" / "old" / "cadence-init" / "skills"
            / "rule-config" / "references" / "rules"
        )
        new_candidate = (
            self.home / "workspace" / "new" / "cadence-init" / "skills"
            / "rule-config" / "references" / "rules"
        )
        _write_minimal_templates(old_candidate, fallback=True)
        _write_minimal_templates(new_candidate, fallback=True)
        # 确保老候选的 openspec_yaml（mtime 比较基准）严格更新
        import time as _time
        _time.sleep(0.05)
        (old_candidate.parent / "openspec" / "config.yaml").touch()
        # 断言：mtime 主导 → 老候选胜出
        rules_root, _ = rc.locate_templates()
        self.assertEqual(rules_root, old_candidate)

    # --- ut-locate_templates-online-preferred-over-offline / S1b-01（双有效场景在线优先）---
    def test_online_preferred_over_offline_when_both_valid(self):
        """ut-locate_templates-online-preferred / S1b-01（在线与离线均完整且离线 mtime 更新时仍返回在线）"""
        online = (
            self.home / ".claude" / "plugins" / "marketplaces" / "cadence-skills-marketplace"
            / "cadence-init" / "skills" / "rule-config" / "references" / "rules"
        )
        offline = (
            self.home / ".claude" / "plugins" / "marketplaces" / "cadence-skills-local"
            / "cadence-init" / "skills" / "rule-config" / "references" / "rules"
        )
        _write_minimal_templates(online)
        _write_minimal_templates(offline)
        # 让离线 mtime 严格更新，确保“在线优先”是短路优先级而非 mtime 选择
        import time as _time
        _time.sleep(0.05)
        (offline / "language.md").touch()
        rules_root, _ = rc.locate_templates()
        self.assertEqual(rules_root, online)

    # --- ut-locate_templates-error-lists-missing / S1b-04（TemplateError 列出每个候选缺失文件名）---
    def test_template_error_lists_missing_files(self):
        """ut-locate_templates-error-lists-missing / S1b-04（全不完整时 TemplateError 消息列出缺失文件名）"""
        # 在线候选：目录存在但缺 openspec/config.yaml（三件套齐全）
        online_rules = (
            self.home / ".claude" / "plugins" / "marketplaces" / "cadence-skills-marketplace"
            / "cadence-init" / "skills" / "rule-config" / "references" / "rules"
        )
        online_rules.mkdir(parents=True)
        for name in _ONLINE_RULES:
            (online_rules / name).write_text("# x\n", encoding="utf-8")
        # 离线候选：目录存在但缺 language.md
        offline_rules = (
            self.home / ".claude" / "plugins" / "marketplaces" / "cadence-skills-local"
            / "cadence-init" / "skills" / "rule-config" / "references" / "rules"
        )
        offline_rules.mkdir(parents=True)
        for name in (_ONLINE_RULES[0], _ONLINE_RULES[2]):  # 仅写 ark + osw，缺 language.md
            (offline_rules / name).write_text("# x\n", encoding="utf-8")
        # glob 回退候选：目录存在但缺 document-storage.md（fallback 额外要求）
        dev_rules = (
            self.home / "workspace" / "proj" / "cadence-init" / "skills"
            / "rule-config" / "references" / "rules"
        )
        dev_rules.mkdir(parents=True)
        for name in _ONLINE_RULES:
            (dev_rules / name).write_text("# x\n", encoding="utf-8")
        # 故意不写 document-storage.md，并补上 config.yaml 让 language.md 作为 glob 标识可命中
        openspec_dir = dev_rules.parent / "openspec"
        openspec_dir.mkdir(parents=True, exist_ok=True)
        (openspec_dir / "config.yaml").write_text("schema: spec-driven\n", encoding="utf-8")
        with self.assertRaises(rc.TemplateError) as ctx:
            rc.locate_templates()
        msg = str(ctx.exception)
        # 断言消息含每个候选具体缺失的文件名
        self.assertIn("openspec/config.yaml", msg)  # 在线候选缺
        self.assertIn("language.md", msg)  # 离线候选缺
        self.assertIn("document-storage.md", msg)  # 回退候选缺
        self.assertIn("在线候选", msg)
        self.assertIn("离线候选", msg)
        self.assertIn("回退候选", msg)

    # --- ut-locate_templates-all-incomplete / S1b-04（全不完整 → TemplateError）---
    def test_all_incomplete_raises_template_error(self):
        """ut-locate_templates-all-incomplete / S1b-04（所有候选均不完整 → TemplateError 终止）"""
        # 不创建任何模板候选；HOME 下无任何 cadence-init/skills/rule-config 路径
        # glob 也无命中 → TemplateError
        with self.assertRaises(rc.TemplateError):
            rc.locate_templates()


# ---------------------------------------------------------------------------
# Task 6：step_s3_rules_files / step_s4_entry_files step 级集成断言
# 验证 S3（含 L1 独立分支红线）与 S4（双入口合成 + 幂等 + 漂移修复）的核心行为。
# 不重复 Task 2 纯函数单测；聚焦 step 函数对 plan/report 的驱动与文件产出。
# ---------------------------------------------------------------------------


class TestStepS3RulesFiles(unittest.TestCase):
    """step_s3_rules_files 集成断言：普通规则分支、L1 独立分支、Playwright。"""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        # 模板根：复用 skill 自带 references/rules
        self.rules_root = Path(__file__).resolve().parents[1] / "references" / "rules"
        self.kernel = (self.rules_root / "agent-routing-kernel.md").read_text(encoding="utf-8")
        self.l1_v1 = (self.rules_root / rc.L1_RULE_FILENAME).read_text(encoding="utf-8")
        self.language_tpl = (self.rules_root / "language.md").read_text(encoding="utf-8")
        self.playwright_tpl = (self.rules_root / "playwright.md").read_text(encoding="utf-8")

    def _base_plan(self, **overrides):
        plan = {
            "project_type": "non-coding",
            "templates": {"rules_root": str(self.rules_root)},
            "decisions_map": {},
            "steps": {},
        }
        plan.update(overrides)
        return plan

    def test_ordinary_rule_created_when_missing(self):
        """ut-step_s3-ordinary-create / RF-01（普通规则不存在 → 读模板创建）"""
        rules_dir = self.root / ".claude" / "rules"
        rules_dir.mkdir(parents=True)
        target = rules_dir / "language.md"
        plan = self._base_plan(steps={
            rc.STEP_RULES_FILES: {
                "name": rc.STEP_RULES_FILES, "status": "ok",
                "assets": [{
                    "path": ".claude/rules/language.md", "action": "create",
                    "conflict": None, "backup_needed": False, "is_l1": False,
                }],
            }
        })
        rc.step_s3_rules_files(self.root, _intents(), plan, {})
        self.assertEqual(target.read_text(encoding="utf-8"), self.language_tpl)

    def test_l1_independent_branch_no_merge_no_supplement(self):
        """ut-step_s3-l1-red-line / L1 独立分支红线（no-interrupt → 直接写 v1 模板；
        结果不得含「项目补充」，不调 merge_markdown）"""
        rules_dir = self.root / ".claude" / "rules"
        rules_dir.mkdir(parents=True)
        target = rules_dir / rc.L1_RULE_FILENAME
        # 项目旧版内容（漂移）
        target.write_text("# 被篡改的旧版\n项目内容\n", encoding="utf-8")
        plan = self._base_plan(steps={
            rc.STEP_RULES_FILES: {
                "name": rc.STEP_RULES_FILES, "status": "ok",
                "assets": [{
                    "path": f".claude/rules/{rc.L1_RULE_FILENAME}", "action": "replace",
                    "conflict": "replace", "backup_needed": True, "is_l1": True,
                }],
            }
        })
        rc.step_s3_rules_files(self.root, _intents(no_interrupt=True), plan, {})
        result = target.read_text(encoding="utf-8")
        self.assertEqual(result, self.l1_v1)  # 逐字等于 v1 规范源
        self.assertNotIn("项目补充", result)  # 红线：不含项目补充

    def test_playwright_existing_not_overwritten(self):
        """ut-step_s3-playwright-no-overwrite / RF-02（已存在 playwright.md 不覆盖）"""
        rules_dir = self.root / ".claude" / "rules"
        rules_dir.mkdir(parents=True)
        target = rules_dir / "playwright.md"
        custom = "# 自定义 playwright\n保留\n"
        target.write_text(custom, encoding="utf-8")
        plan = self._base_plan(steps={
            rc.STEP_RULES_FILES: {
                "name": rc.STEP_RULES_FILES, "status": "ok",
                "assets": [{
                    "path": ".claude/rules/playwright.md", "action": "skip",
                    "conflict": None, "backup_needed": False, "is_l1": False,
                }],
            }
        })
        rc.step_s3_rules_files(
            self.root, _intents(no_interrupt=True, enable_playwright=True), plan, {}
        )
        self.assertEqual(target.read_text(encoding="utf-8"), custom)

    def test_ordinary_no_interrupt_overwrites_with_template(self):
        """ut-step_s3-authoritative-overwrite / RF-05（普通规则 no-interrupt → 模板权威全覆盖）"""
        rules_dir = self.root / ".claude" / "rules"
        rules_dir.mkdir(parents=True)
        target = rules_dir / "language.md"
        target.write_text(self.language_tpl + "\n项目独有行\n", encoding="utf-8")
        plan = self._base_plan(steps={
            rc.STEP_RULES_FILES: {
                "name": rc.STEP_RULES_FILES, "status": "ok",
                "assets": [{
                    "path": ".claude/rules/language.md", "action": "replace",
                    "conflict": "drift", "backup_needed": True, "is_l1": False,
                }],
            }
        })
        rc.step_s3_rules_files(self.root, _intents(no_interrupt=True), plan, {})
        result = target.read_text(encoding="utf-8")
        self.assertEqual(result, self.language_tpl)
        self.assertNotIn("项目补充", result)
        self.assertNotIn("项目独有行", result)

    def test_ordinary_no_interrupt_unchanged_skips_write(self):
        """ut-step_s3-ordinary-unchanged / RF-05（内容==模板 → 跳过写盘，报告 unchanged）"""
        rules_dir = self.root / ".claude" / "rules"
        rules_dir.mkdir(parents=True)
        target = rules_dir / "language.md"
        target.write_text(self.language_tpl, encoding="utf-8")
        plan = self._base_plan(steps={
            rc.STEP_RULES_FILES: {
                "name": rc.STEP_RULES_FILES, "status": "ok",
                "assets": [{
                    "path": ".claude/rules/language.md", "action": "replace",
                    "conflict": "drift", "backup_needed": True, "is_l1": False,
                }],
            }
        })
        report = {"steps": [], "overall": "ok"}
        with mock.patch.object(rc, "atomic_write") as m_write:
            rc.step_s3_rules_files(self.root, _intents(no_interrupt=True), plan, report)
        m_write.assert_not_called()
        s3 = next(s for s in report["steps"] if s["name"] == rc.STEP_RULES_FILES)
        self.assertTrue(
            any(
                a.get("action") == "unchanged"
                and a.get("branch") == "authoritative-idempotent"
                for a in s3.get("actions", [])
            )
        )
        self.assertEqual(target.read_text(encoding="utf-8"), self.language_tpl)


class TestCommitToggle(unittest.TestCase):
    def test_default_written_when_missing(self):
        """ut-toggle-default：缺失时写默认值 关闭。"""
        out, _ = rc._ensure_commit_toggle("# x\n", "CLAUDE.md")
        self.assertIn("- **产物自动提交（design/plan）**：关闭", out)
        self.assertIn("## 项目配置", out)
        self.assertGreater(out.index("## 项目配置"), out.index("# x"))
        self.assertTrue(out.endswith(rc.TOGGLE_PREFIX + "关闭\n"))

    def test_user_value_preserved(self):
        """ut-toggle-keep：用户值 开启 保留。"""
        text = "## 项目配置\n\n- **产物自动提交（design/plan）**：开启\n"
        out, warns = rc._ensure_commit_toggle(text, "CLAUDE.md")
        self.assertIn("：开启", out)
        self.assertEqual(warns, [])

    def test_invalid_value_kept_with_warning(self):
        """ut-toggle-invalid：非法值保留原文 + INVALID_TOGGLE。"""
        text = "## 项目配置\n\n- **产物自动提交（design/plan）**：也许\n"
        out, warns = rc._ensure_commit_toggle(text, "CLAUDE.md")
        self.assertIn("：也许", out)
        self.assertTrue(any(w["code"] == "INVALID_TOGGLE" for w in warns))

    def test_orphan_toggle_is_merged_into_config_section(self):
        """ut-toggle-orphan：章节外合法开关归并到项目配置并保留值。"""
        text = "# x\n\n" + rc.TOGGLE_PREFIX + "开启\n\n## 项目配置\n\n内容\n"
        out, warns = rc._ensure_commit_toggle(text, "CLAUDE.md")
        self.assertEqual(out.count(rc.TOGGLE_PREFIX), 1)
        section = out.split("## 项目配置", 1)[1]
        self.assertIn("内容", section)
        self.assertIn(rc.TOGGLE_PREFIX + "开启", section)
        self.assertEqual(warns, [])

    def test_orphan_and_section_same_value_are_deduped(self):
        """ut-toggle-orphan-same：章节外与章节内同值归并为一行。"""
        text = (
            rc.TOGGLE_PREFIX + "开启\n\n"
            "## 项目配置\n\n"
            + rc.TOGGLE_PREFIX + "开启\n"
        )
        out, warns = rc._ensure_commit_toggle(text, "CLAUDE.md")
        self.assertEqual(out.count(rc.TOGGLE_PREFIX), 1)
        self.assertIn(rc.TOGGLE_PREFIX + "开启", out)
        self.assertEqual(warns, [])

    def test_orphan_and_section_conflict_defaults_closed(self):
        """ut-toggle-orphan-conflict：孤儿与章节值冲突时关闭并告警。"""
        text = (
            rc.TOGGLE_PREFIX + "开启\n\n"
            "## 项目配置\n\n"
            + rc.TOGGLE_PREFIX + "关闭\n"
        )
        out, warns = rc._ensure_commit_toggle(text, "CLAUDE.md")
        self.assertEqual(out.count(rc.TOGGLE_PREFIX), 1)
        self.assertIn(rc.TOGGLE_PREFIX + "关闭", out)
        warning = next(w for w in warns if w["code"] == "INVALID_TOGGLE")
        self.assertIn("冲突", warning["detail"]["reason"])

    def test_orphan_toggle_merge_is_idempotent(self):
        """ut-toggle-orphan-idempotent：孤儿开关归并后二次运行逐字不变。"""
        text = rc.TOGGLE_PREFIX + "开启\n\n## 项目配置\n\n内容\n"
        once, _ = rc._ensure_commit_toggle(text, "CLAUDE.md")
        twice, warns = rc._ensure_commit_toggle(once, "CLAUDE.md")
        self.assertEqual(once, twice)
        self.assertEqual(warns, [])

    def test_toggle_after_techstack_block(self):
        """ut-toggle-position：落点在 ### 项目技术栈 块之后、章节末尾。"""
        text = ("## 项目配置\n\n### 项目技术栈\n- **语言**：Java\n\n## 其他\n")
        out, _ = rc._ensure_commit_toggle(text, "CLAUDE.md")
        self.assertLess(out.index("### 项目技术栈"), out.index(rc.TOGGLE_PREFIX))
        self.assertLess(out.index(rc.TOGGLE_PREFIX), out.index("## 其他"))

    def test_duplicate_toggle_deduped(self):
        """ut-toggle-dup：重复开关行保留首个。"""
        text = ("## 项目配置\n\n- **产物自动提交（design/plan）**：开启\n"
                "- **产物自动提交（design/plan）**：关闭\n")
        out, warns = rc._ensure_commit_toggle(text, "CLAUDE.md")
        self.assertEqual(out.count(rc.TOGGLE_PREFIX), 1)
        self.assertIn("：开启", out)

    def test_multiple_project_config_sections(self):
        """ut-toggle-multi-section：多个 ## 项目配置 仅处理首个 + DUPLICATE_H2。"""
        text = "## 项目配置\n\n- **产物自动提交（design/plan）**：开启\n\n## 项目配置\n\nx\n"
        out, warns = rc._ensure_commit_toggle(text, "CLAUDE.md")
        self.assertTrue(any(w["code"] == "DUPLICATE_H2" for w in warns))
        self.assertIn("：开启", out)
        self.assertIn("## 项目配置\n\nx\n", out)

    def test_idempotent(self):
        """ut-toggle-idempotent：幂等。"""
        once, _ = rc._ensure_commit_toggle("# x\n", "CLAUDE.md")
        twice, _ = rc._ensure_commit_toggle(once, "CLAUDE.md")
        self.assertEqual(once, twice)


class TestComposeEntryWarnings(unittest.TestCase):
    def test_existing_techstack_content_is_preserved(self):
        """入口已有用户技术栈章节时逐字保留，且开关仍落位。"""
        user_config = (
            "### 项目技术栈\n- 用户自定义技术栈\n\n"
            "### 包管理器规则\n- 用户指定 pnpm\n"
        )
        text = "# CLAUDE.md\n\n## 项目配置\n\n" + user_config
        out, warns = rc._compose_entry(
            text, rc._load_kernel_source(), state="skip",
            project_type="non-coding", entry_name="CLAUDE.md",
            existing_rule_files=set())
        self.assertIn(user_config, out)
        self.assertIn(rc.TOGGLE_PREFIX + "关闭", out)
        self.assertEqual(warns, [])

    def test_no_techstack_block_is_script_generated(self):
        """无技术栈块入口处理后不得出现脚本生成的技术栈字段。"""
        out, _warns = rc._compose_entry(
            "# CLAUDE.md\n", rc._load_kernel_source(), state="create",
            project_type="non-coding", entry_name="CLAUDE.md",
            existing_rule_files=set())
        self.assertNotIn("### 项目技术栈", out)
        self.assertNotIn("### 包管理器规则", out)
        self.assertNotIn("覆盖率阈值", out)

    def test_compose_returns_warnings(self):
        """ut-compose-warnings：_compose_entry 返回 (text, diffs, warnings)。"""
        text, warns = rc._compose_entry(
            "## 笔记\n\n遵循 TDD 和代码规范 保留我\n", rc._load_kernel_source(),
            state="insert", project_type="non-coding",
            entry_name="CLAUDE.md", existing_rule_files=set())
        self.assertIsInstance(warns, list)
        self.assertIn("遵循 TDD 和代码规范 保留我", text)  # 章节外不被全文替换

    def test_step_s4_aggregates_warnings_to_report(self):
        """ut-s4-warnings：S4 执行后 report['warnings'] 汇总入口类 warning。"""
        # 用 Task 1 的临时项目方式跑 apply，断言 report JSON 含 warnings 数组
        import tempfile, subprocess, json
        from pathlib import Path
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "AGENTS.md").write_text("## 强制规则\n\n- 我的行 `.claude/rules/my-x.md`\n")
            report_path = Path(td).parent / "r.json"
            subprocess.run(["python3", str(SCRIPT_PATH), "apply", "--project-root", str(root),
                            "--report", str(report_path), "--no-interrupt"], check=True)
            rep = json.loads(report_path.read_text())
            self.assertIn("warnings", rep)
            self.assertTrue(any(w["code"] == "USER_LINES_KEPT" for w in rep["warnings"]))
            self.assertEqual(rep["overall"], "ok")  # warning 不影响 overall


class TestStepS4EntryFiles(unittest.TestCase):
    """step_s4_entry_files 集成断言：双入口合成、幂等、漂移修复。"""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.rules_root = Path(__file__).resolve().parents[1] / "references" / "rules"
        self.kernel = (self.rules_root / "agent-routing-kernel.md").read_text(encoding="utf-8")

    def _base_plan(self, **overrides):
        plan = {
            "project_type": "non-coding",
            "templates": {"rules_root": str(self.rules_root)},
            "decisions_map": {},
            "steps": {},
        }
        plan.update(overrides)
        return plan

    def test_entry_created_from_base_when_missing(self):
        """ut-step_s4-base-created / L0-P5（入口不存在 → BASE 基线 + L0 + 强制规则）"""
        plan = self._base_plan(steps={
            rc.STEP_ENTRY_FILES: {
                "name": rc.STEP_ENTRY_FILES, "status": "ok",
                "assets": [{
                    "path": "CLAUDE.md", "action": "create",
                    "conflict": None, "backup_needed": False,
                }],
            }
        })
        rc.step_s4_entry_files(self.root, _intents(no_interrupt=True), plan, {})
        text = (self.root / "CLAUDE.md").read_text(encoding="utf-8")
        self.assertIn(rc.L0_BEGIN, text)
        self.assertIn(rc.L0_END, text)
        self.assertIn("## 强制规则", text)

    def test_skip_state_idempotent_no_change(self):
        """ut-step_s4-skip-idempotent / L0-P6+SM-01（skip 且摘要已收敛 → 幂等零写入）"""
        entry = self.root / "CLAUDE.md"
        # 构造收敛态入口（L0=规范源 + 全部摘要行）：skip 状态零写入
        converged, _warnings = rc._compose_entry(
            rc.BASE_CLAUDE_MD, self.kernel, state="create",
            project_type="non-coding", entry_name="CLAUDE.md",
        )
        entry.write_text(converged, encoding="utf-8")
        plan = self._base_plan(steps={
            rc.STEP_ENTRY_FILES: {
                "name": rc.STEP_ENTRY_FILES, "status": "ok",
                "assets": [{
                    "path": "CLAUDE.md", "action": "skip",
                    "conflict": None, "backup_needed": False,
                }],
            }
        })
        rc.step_s4_entry_files(
            self.root, _intents(no_interrupt=True), plan, {},
        )
        self.assertEqual(entry.read_text(encoding="utf-8"), converged)

    def test_skip_state_backfills_missing_summary(self):
        """ut-step_s4-skip-backfill：skip 状态仍补齐缺失摘要，不生成技术栈。"""
        entry = self.root / "CLAUDE.md"
        base = (
            "# CLAUDE.md\n\n说明\n\n" + self.kernel
            + "\n## 强制规则\n\n- 用户自定义规则\n"
        )
        entry.write_text(base, encoding="utf-8")
        plan = self._base_plan(steps={
            rc.STEP_ENTRY_FILES: {
                "name": rc.STEP_ENTRY_FILES, "status": "ok",
                "assets": [{
                    "path": "CLAUDE.md", "action": "skip",
                    "conflict": None, "backup_needed": False,
                }],
            }
        })
        rc.step_s4_entry_files(self.root, _intents(no_interrupt=True), plan, {})
        result = entry.read_text(encoding="utf-8")
        self.assertIn(
            "- **必须使用中文回答** → 详见 `.claude/rules/language.md`",
            result,
        )
        self.assertIn("- 用户自定义规则", result)
        self.assertNotIn("### 项目技术栈", result)
        begin = result.index(rc.L0_BEGIN)
        end = result.index(rc.L0_END, begin) + len(rc.L0_END)
        self.assertEqual(result[begin:end].strip(), self.kernel.strip())

    def test_drift_replaced_block_matches_source_outside_preserved(self):
        """ut-step_s4-drift-replace / L0-P7+L0-B2+codex 终审 I2
        （no-interrupt 修复 drift：区块=规范源，区块外用户内容保留；缺失摘要按 SM-02 补齐）"""
        entry = self.root / "CLAUDE.md"
        # 构造 drift：L0 区块内含漂移内容
        drift_block = rc.L0_BEGIN + "\n漂移内容\n" + rc.L0_END
        original = "# CLAUDE.md\n\n文件说明\n\n" + drift_block + "\n## 强制规则\n\n- 用户规则\n"
        entry.write_text(original, encoding="utf-8")
        plan = self._base_plan(steps={
            rc.STEP_ENTRY_FILES: {
                "name": rc.STEP_ENTRY_FILES, "status": "ok",
                "assets": [{
                    "path": "CLAUDE.md", "action": "replace",
                    "conflict": "drift", "backup_needed": True,
                }],
            }
        })
        rc.step_s4_entry_files(self.root, _intents(no_interrupt=True), plan, {})
        result = entry.read_text(encoding="utf-8")
        # 区块 = 规范源
        begin = result.index(rc.L0_BEGIN)
        end = result.index(rc.L0_END, begin) + len(rc.L0_END)
        self.assertEqual(result[begin:end].strip(), self.kernel.strip())
        # 区块外保留用户内容（漂移内容被移除）
        self.assertNotIn("漂移内容", result)
        self.assertIn("- 用户规则", result)
        # I2：缺失摘要按 SM-02 补齐（L0 处理与摘要补全是独立动作）
        self.assertIn("- **必须使用中文回答** → 详见 `.claude/rules/language.md`", result)


class TestStepS7OpenspecConfig(unittest.TestCase):
    """step_s7_openspec_config 集成断言：create/merge/rules.apply/结构冲突。"""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.openspec_yaml = Path(__file__).resolve().parents[1] / "references" / "openspec" / "config.yaml"
        self.tpl = self.openspec_yaml.read_text(encoding="utf-8")

    def _base_plan(self, **overrides):
        plan = {
            "project_type": "non-coding",
            "templates": {"openspec_yaml": str(self.openspec_yaml)},
            "decisions_map": {},
            "steps": {},
        }
        plan.update(overrides)
        return plan

    def test_create_when_missing(self):
        """ut-step_s7-create / OS-01（目标不存在 → 候选=模板，原子创建）"""
        plan = self._base_plan(steps={
            rc.STEP_OPENSPEC_CONFIG: {
                "name": rc.STEP_OPENSPEC_CONFIG, "status": "ok",
                "assets": [{
                    "path": "openspec/config.yaml", "action": "create",
                    "conflict": None, "backup_needed": False,
                }],
            }
        })
        rc.step_s7_openspec_config(self.root, _intents(no_interrupt=True), plan, {})
        target = self.root / "openspec" / "config.yaml"
        self.assertTrue(target.exists())
        # 内容应为模板的安全 dump 形式（merge_yaml 幂等点）
        merged, _ = rc.merge_yaml(self.tpl, "")
        self.assertEqual(target.read_text(encoding="utf-8"), merged)

    def test_merge_no_conflict_publishes(self):
        """ut-step_s7-merge / OS-02（无冲突 → 保守合并去重发布）"""
        cfg = self.root / "openspec" / "config.yaml"
        cfg.parent.mkdir(parents=True)
        cfg.write_text("schema: spec-driven\ncontext: |\n  项目上下文\n", encoding="utf-8")
        plan = self._base_plan(steps={
            rc.STEP_OPENSPEC_CONFIG: {
                "name": rc.STEP_OPENSPEC_CONFIG, "status": "ok",
                "assets": [{
                    "path": "openspec/config.yaml", "action": "merge",
                    "conflict": None, "backup_needed": True,
                }],
            }
        })
        rc.step_s7_openspec_config(self.root, _intents(no_interrupt=True), plan, {})
        doc = yaml.safe_load(cfg.read_text(encoding="utf-8"))
        self.assertIn("项目上下文", doc["context"])
        self.assertEqual(doc["schema"], "spec-driven")

    def test_rules_apply_no_interrupt_removed(self):
        """ut-step_s7-rules-apply-remove / OS-N8（no-interrupt → 候选移除 rules.apply）"""
        cfg = self.root / "openspec" / "config.yaml"
        cfg.parent.mkdir(parents=True)
        cfg.write_text(
            "schema: spec-driven\nrules:\n  proposal:\n    - custom\n  apply:\n    - x\n",
            encoding="utf-8",
        )
        plan = self._base_plan(steps={
            rc.STEP_OPENSPEC_CONFIG: {
                "name": rc.STEP_OPENSPEC_CONFIG, "status": "ok",
                "assets": [{
                    "path": "openspec/config.yaml", "action": "keep",
                    "conflict": {"kind": "rules.apply", "value": ["x"]},
                    "backup_needed": True,
                }],
            }
        })
        rc.step_s7_openspec_config(self.root, _intents(no_interrupt=True), plan, {})
        doc = yaml.safe_load(cfg.read_text(encoding="utf-8"))
        self.assertNotIn("apply", doc.get("rules", {}))
        self.assertIn("custom", doc["rules"]["proposal"])

    def test_rules_apply_normal_default_keep_preserved(self):
        """ut-step_s7-rules-apply-keep / OS 行（普通模式无决策 → 保留原文件）"""
        cfg = self.root / "openspec" / "config.yaml"
        cfg.parent.mkdir(parents=True)
        original = "schema: spec-driven\nrules:\n  apply:\n    - x\n"
        cfg.write_text(original, encoding="utf-8")
        plan = self._base_plan(steps={
            rc.STEP_OPENSPEC_CONFIG: {
                "name": rc.STEP_OPENSPEC_CONFIG, "status": "ok",
                "assets": [{
                    "path": "openspec/config.yaml", "action": "keep",
                    "conflict": {"kind": "rules.apply", "value": ["x"]},
                    "backup_needed": True,
                }],
            }
        })
        rc.step_s7_openspec_config(self.root, _intents(), plan, {})
        self.assertEqual(cfg.read_text(encoding="utf-8"), original)

    def test_structure_conflict_no_interrupt_raises(self):
        """ut-step_s7-structure-terminate / OS-N9（no-interrupt 结构冲突 → 终止原文件不变）"""
        cfg = self.root / "openspec" / "config.yaml"
        cfg.parent.mkdir(parents=True)
        original = "schema: spec-driven\nrules:\n  proposal: invalid-string\n"
        cfg.write_text(original, encoding="utf-8")
        plan = self._base_plan(steps={
            rc.STEP_OPENSPEC_CONFIG: {
                "name": rc.STEP_OPENSPEC_CONFIG, "status": "ok",
                "assets": [{
                    "path": "openspec/config.yaml", "action": "keep",
                    "conflict": {
                        "kind": "structure", "fields": ["rules.proposal"],
                        "field_types": {"rules.proposal": "str"},
                    },
                    "backup_needed": True,
                }],
            }
        })
        with self.assertRaises(rc.PublishError):
            rc.step_s7_openspec_config(
                self.root, _intents(no_interrupt=True), plan, {}
            )
        self.assertEqual(cfg.read_text(encoding="utf-8"), original)

    def test_structure_conflict_normal_preserved(self):
        """ut-step_s7-structure-preserve / OS-N9（普通模式结构冲突 → 保留+报告 status=0）"""
        cfg = self.root / "openspec" / "config.yaml"
        cfg.parent.mkdir(parents=True)
        original = "schema: spec-driven\nrules:\n  proposal: invalid-string\n"
        cfg.write_text(original, encoding="utf-8")
        plan = self._base_plan(steps={
            rc.STEP_OPENSPEC_CONFIG: {
                "name": rc.STEP_OPENSPEC_CONFIG, "status": "ok",
                "assets": [{
                    "path": "openspec/config.yaml", "action": "keep",
                    "conflict": {
                        "kind": "structure", "fields": ["rules.proposal"],
                        "field_types": {"rules.proposal": "str"},
                    },
                    "backup_needed": True,
                }],
            }
        })
        report = {"steps": [rc._step_skeleton(rc.STEP_OPENSPEC_CONFIG)]}
        rc.step_s7_openspec_config(self.root, _intents(), plan, report)
        self.assertEqual(cfg.read_text(encoding="utf-8"), original)
        # 报告含结构冲突字段路径
        s7_conflicts = report["steps"][0].get("conflicts", [])
        self.assertTrue(any(c.get("kind") == "structure" for c in s7_conflicts))

    def test_publish_candidate_precheck_fail_raises(self):
        """ut-s7-publish-or-abort-precheck-fail / OS-N12（候选结构预检失败→终止、原文件不变）

        codex 三轮 Important：_s7_publish_or_abort 的候选 precheck fail-closed 分支
        （scripts/rule-config.py:2700-2710）无直接测试。该分支为「保险层」——
        候选来自封闭来源（模板 + 预检通过的 existing 经 merge_yaml 去重追加），
        正常应总能通过；极端情况（如 merge_yaml 渲染异常）下候选结构非法时
        MUST raise PublishError 且原文件不变。本单测直接注入非法候选验证该分支。
        """
        cfg = self.root / "openspec" / "config.yaml"
        cfg.parent.mkdir(parents=True)
        original = "schema: spec-driven\ncontext: original\n"
        cfg.write_text(original, encoding="utf-8")
        # 构造非法候选：rules 为非映射（字符串），结构预检必失败
        invalid_candidate = "schema: spec-driven\nrules: not-a-mapping\n"
        report = {"steps": [rc._step_skeleton(rc.STEP_OPENSPEC_CONFIG)]}
        actions_log: list = []
        with self.assertRaises(rc.PublishError):
            rc._s7_publish_or_abort(
                cfg, invalid_candidate, report, actions_log,
                "openspec/config.yaml", branch="merge",
            )
        # 原文件不变（候选未发布）
        self.assertEqual(cfg.read_text(encoding="utf-8"), original)
        # 动作日志记录了 precheck 失败与字段路径
        self.assertTrue(any(
            a.get("action") == "aborted" and "fields" in a
            and "rules" in a.get("fields", [])
            for a in actions_log
        ))


class TestSummaryDedup(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "proj"
        self.root.mkdir(parents=True)
        self.rules_root = Path(self.tmp.name) / "tpl"
        real_tpl = Path(__file__).resolve().parents[1] / "references" / "rules"
        self.rules_root.mkdir(parents=True)
        for f in real_tpl.iterdir():
            if f.is_file():
                (self.rules_root / f.name).write_bytes(f.read_bytes())
        self.openspec_yaml = (
            Path(__file__).resolve().parents[1]
            / "references"
            / "openspec"
            / "config.yaml"
        )

    def test_different_wording_same_ref_not_duplicated(self):
        claude = self.root / "CLAUDE.md"
        custom_line = (
            "- **文档存放（项目措辞）** -> 详见 "
            "`.claude/rules/document-storage.md`"
        )
        standard_line = (
            "- **Cadence 产物文档必须存放在 `cadence` 目录下；Claude Code "
            "框架规则保留在 `.claude/rules/` 目录下** → 详见 "
            "`.claude/rules/document-storage.md`"
        )
        claude.write_text(
            "# CLAUDE.md\n\n## 强制规则\n\n" + custom_line + "\n",
            encoding="utf-8",
        )
        report = rc.build_report("no-interrupt", self.root)
        with mock.patch.object(
            rc,
            "locate_templates",
            return_value=(self.rules_root, self.openspec_yaml),
        ):
            rc.run_apply(self.root, _intents(no_interrupt=True), report)
        section = claude.read_text(encoding="utf-8")
        self.assertEqual(
            section.count(".claude/rules/document-storage.md"), 1
        )
        self.assertIn(standard_line, section.splitlines())
        self.assertNotIn(custom_line, section.splitlines())

    def test_duplicate_ref_deduped(self):
        claude = self.root / "CLAUDE.md"
        first_line = "- **A（保留首个）** -> 详见 language.md"
        duplicate_line = "- **B（删除后续）** -> 详见 language.md"
        claude.write_text(
            "# CLAUDE.md\n\n## 强制规则\n\n"
            + first_line + "\n" + duplicate_line + "\n",
            encoding="utf-8",
        )
        report = rc.build_report("no-interrupt", self.root)
        with mock.patch.object(
            rc,
            "locate_templates",
            return_value=(self.rules_root, self.openspec_yaml),
        ):
            rc.run_apply(self.root, _intents(no_interrupt=True), report)
        section = claude.read_text(encoding="utf-8")
        self.assertEqual(section.count("language.md"), 1)
        self.assertNotIn(first_line, section.splitlines())
        self.assertIn("- **必须使用中文回答** → 详见 `.claude/rules/language.md`", section.splitlines())
        self.assertNotIn(duplicate_line, section.splitlines())


class TestNormalizeMandatoryRulesLegacy(unittest.TestCase):
    """迁移自 _ensure_summary_lines 的规则 2/6 回归断言。"""

    def _base_rules_section(self, drop_lines=()):
        """构造一个含规则 1/3/4/5/7 但缺规则 2/6 的 ## 强制规则 章节（CLAUDE.md 风格）。"""
        lines = [
            "# CLAUDE.md",
            "",
            "说明",
            "",
            "## 强制规则",
            "",
            "> **🔴 必须遵守 - 无例外**",
            "",
            "### 1. 语言规则",
            "- **必须使用中文回答** → 详见 `.claude/rules/language.md`",
            "",
            "### 3. 文档存储规则",
            "- **Cadence 产物文档必须存放在 `cadence` 目录下；Claude Code 框架规则保留在 `.claude/rules/` 目录下** → 详见 `.claude/rules/document-storage.md`",
            "",
            "### 4. Markdown 格式规则",
            "- **代码块嵌套使用 4 反引号/3 反引号** → 详见 `.claude/rules/markdown-format.md`",
            "",
            "### 5. MCP Server 使用规则",
            "- **各 MCP 工具的使用规范** → 详见 `.claude/rules/mcp-servers.md`",
            "",
            "### 7. 代码阅读规则",
            "- **大范围检索使用 CodeGraph，精确结构阅读优先使用 ast-grep outline** → 详见 `.claude/rules/code-reading.md`",
            "",
        ]
        return "\n".join(lines)

    def test_missing_rule2_and_rule6_are_added_claude_noncoding(self):
        """ut-ensure_summary-missing-rule2-rule6 / Important 1（CLAUDE.md 非 Coding：补回规则 2 非必要 + 规则 6 块）"""
        text = self._base_rules_section()
        out = rc._normalize_mandatory_rules(text, "CLAUDE.md", "non-coding", set())[0]
        # 规则 2（非 Coding 文本）被补回
        self.assertIn(rc.RULE2_TEXT_NONCODING, out)
        self.assertNotIn(rc.RULE2_TEXT_CODING, out)
        # 规则 6 多行块被补回（至少首行 + 末行）
        self.assertIn("### 6. 项目个性化规则", out)
        self.assertIn("- 详见 `cadence/project-rules/README.md`", out)

    def test_rule6_restored_when_only_standard_reference_block_remains(self):
        """回归：标准引用块的 cadence/project-rules/ 路径不应伪装成规则 6 正文。"""
        text = (
            "# CLAUDE.md\n\n## 强制规则\n\n"
            "> **🔴 必须遵守 - 无例外**\n"
            "> 详细规则见 `.claude/rules/` 目录下的各规则文件。\n"
            "> 用户自定义规则见 `cadence/project-rules/` 目录。\n\n"
            "### 1. 语言规则\n"
            "- **必须使用中文回答** → 详见 `.claude/rules/language.md`\n\n"
            "### 2. 代码使用规则\n" + rc.RULE2_TEXT_NONCODING + "\n\n"
            "### 3. 文档存储规则\n"
            "- **Cadence 产物文档必须存放在 `cadence` 目录下；Claude Code 框架规则保留在 `.claude/rules/` 目录下** → 详见 `.claude/rules/document-storage.md`\n\n"
            "### 4. Markdown 格式规则\n"
            "- **代码块嵌套使用 4 反引号/3 反引号** → 详见 `.claude/rules/markdown-format.md`\n\n"
            "### 5. MCP Server 使用规则\n"
            "- **各 MCP 工具的使用规范** → 详见 `.claude/rules/mcp-servers.md`\n\n"
            "### 7. 代码阅读规则\n"
            "- **大范围检索使用 CodeGraph，精确结构阅读优先使用 ast-grep outline** → 详见 `.claude/rules/code-reading.md`\n"
        )
        out = rc._normalize_mandatory_rules(text, "CLAUDE.md", "non-coding", set())[0]
        self.assertIn("### 6. 项目个性化规则", out)

    def test_missing_rule2_coding_variant_added_for_coding_project(self):
        """ut-ensure_summary-rule2-coding / Important 1（Coding 项目补回规则 2 = 遵循 TDD）"""
        text = self._base_rules_section()
        out = rc._normalize_mandatory_rules(text, "CLAUDE.md", "coding", set())[0]
        self.assertIn(rc.RULE2_TEXT_CODING, out)
        self.assertNotIn(rc.RULE2_TEXT_NONCODING, out)

    def test_complete_section_unchanged(self):
        """ut-ensure_summary-complete-unchanged / Important 1（7 类摘要齐全则不动）"""
        # BASE_CLAUDE_MD 本身含 7 条摘要 → 不应改动
        out = rc._normalize_mandatory_rules(rc.BASE_CLAUDE_MD, "CLAUDE.md", "non-coding", set())[0]
        self.assertEqual(out, rc.BASE_CLAUDE_MD)

    def test_rule6_heading_is_canonical_for_both_entries(self):
        """规则 6 标题由权威清单统一渲染，入口差异仅保留在正文。"""
        for entry_name, base in (("CLAUDE.md", rc.BASE_CLAUDE_MD), ("AGENTS.md", rc.BASE_AGENTS_MD)):
            with self.subTest(entry_name=entry_name):
                out, _ = rc._normalize_mandatory_rules(base, entry_name, "non-coding", set())
                self.assertEqual(out.count("### 6. 项目个性化规则"), 1)
                self.assertNotIn("### 6. 项目个性化规则（强制规则）", out)

    def test_multi_marker_dedup_recomputes_missing_from_result(self):
        """删除含重复 marker 的多引用行后，补回该行承载的唯一规则引用。"""
        combined_line = "- **组合引用** language.md + code-usage.md"
        text = rc.BASE_CLAUDE_MD.replace(rc.RULE2_TEXT_NONCODING, combined_line)
        out = rc._normalize_mandatory_rules(text, "CLAUDE.md", "non-coding", set())[0]
        self.assertNotIn(combined_line, out.splitlines())
        self.assertIn(rc.RULE2_TEXT_NONCODING, out.splitlines())
        self.assertEqual(out.count("code-usage.md"), 1)

    def test_agents_rule6_block_variant(self):
        """ut-ensure_summary-agents-rule6 / Important 1（AGENTS.md 规则 6 块文本与 CLAUDE.md 不同）"""
        # 构造 AGENTS.md 风格、缺规则 6 的章节
        text = (
            "# AGENTS.md\n\n说明\n\n## 强制规则\n\n"
            "### 1. 语言规则\n- **必须使用中文回答** → 详见 `.claude/rules/language.md`\n\n"
            "### 2. 代码使用规则\n" + rc.RULE2_TEXT_NONCODING + "\n\n"
            "### 3. 文档存储规则\n- **Cadence 产物文档必须存放在 `cadence` 目录下；Claude Code 框架规则保留在 `.claude/rules/` 目录下** → 详见 `.claude/rules/document-storage.md`\n\n"
            "### 4. Markdown 格式规则\n- **代码块嵌套使用 4 反引号/3 反引号** → 详见 `.claude/rules/markdown-format.md`\n\n"
            "### 5. MCP Server 使用规则\n- **各 MCP 工具及相关自动化工具的使用必须遵循项目规范** → 详见 `.claude/rules/mcp-servers.md`\n\n"
            "### 7. 代码阅读规则\n- **大范围检索使用 CodeGraph，精确结构阅读优先使用 ast-grep outline** → 详见 `.claude/rules/code-reading.md`\n"
        )
        out = rc._normalize_mandatory_rules(text, "AGENTS.md", "non-coding", set())[0]
        self.assertIn("### 6. 项目个性化规则\n", out)
        self.assertIn("- 禁止在 `.claude/rules/` 目录中添加用户自定义规则", out)


KB_AGENTS = "# KB\n\nEnglish knowledge base content.\n\n## NOTES\n\n- keep me\n"


class TestNormalizeMandatoryRules(unittest.TestCase):
    def _norm(self, text, entry="AGENTS.md", ptype="non-coding", files=set()):
        return rc._normalize_mandatory_rules(text, entry, ptype, files)

    def test_create_section_when_missing(self):
        """ut-norm-create：无章节时创建（全局顺序在 Task 5 集成验证）。"""
        out, warns = self._norm(KB_AGENTS)
        self.assertIn("## 强制规则", out)
        self.assertIn("### 1. 语言规则", out)
        self.assertIn("### 7. 代码阅读规则", out)
        self.assertIn("English knowledge base content.", out)

    def test_serena_removed(self):
        """ut-norm-retired：退役清单命中删除。"""
        text = "## 强制规则\n\n### 5. Serena 使用规则\n- **禁止分析 .git 目录** → 详见 `.claude/rules/serena-usage.md`\n"
        out, _ = self._norm(text, "CLAUDE.md")
        self.assertNotIn("serena-usage.md", out)
        self.assertNotIn("Serena", out)

    def test_forward_reference_kept(self):
        """ut-norm-forward-ref：未在退役清单的不存在文件引用按用户内容保留。"""
        text = "## 强制规则\n\n### 9. 自定义规则\n- **我的规则** → 详见 `.claude/rules/my-future.md`\n"
        out, warns = self._norm(text)
        self.assertIn("my-future.md", out)
        self.assertTrue(any(w["code"] == "USER_LINES_KEPT" for w in warns))

    def test_renumber_1_to_9(self):
        """ut-norm-renumber：1-9 错乱重排为权威 1-7。"""
        text = ("## 强制规则\n\n### 5. Serena 使用规则\n- x `.claude/rules/serena-usage.md`\n"
                "### 1. 语言规则\n- **必须使用中文回答** → 详见 `.claude/rules/language.md`\n")
        out, _ = self._norm(text, "CLAUDE.md", "coding", set())
        self.assertIn("### 1. 语言规则", out)
        self.assertIn("### 2. 代码使用规则", out)
        self.assertIn("遵循 TDD", out)
        self.assertNotIn("### 8.", out)

    def test_dedup_same_ref(self):
        """ut-norm-dedup：同规则文件多引用保留首个。"""
        text = ("## 强制规则\n\n- **必须使用中文回答** → 详见 `.claude/rules/language.md`\n"
                "- 重复行 `.claude/rules/language.md`\n")
        out, _ = self._norm(text)
        self.assertEqual(out.count("language.md"), 1)

    def test_idempotent(self):
        """ut-norm-idempotent：二次运行逐字不变。"""
        once, _ = self._norm(KB_AGENTS)
        twice, warns2 = self._norm(once)
        self.assertEqual(once, twice)

    def test_idempotent_preserves_user_line_adjacent_to_canonical_h3(self):
        """ut-norm-idempotent-adjacent：权威 H3 尾部用户行不可在第二次收敛时丢失。"""
        text = (
            "## 强制规则\n\n"
            "### 7. 代码阅读规则\n"
            "- **大范围检索使用 CodeGraph，精确结构阅读优先使用 ast-grep outline** → 详见 `.claude/rules/code-reading.md`\n\n"
            "> **必须遵守 - 无例外**\n"
            "### 7. Playwright CLI 使用规则\n"
            "- **浏览器自动化工具必须遵循项目规范** → 详见 `.claude/rules/playwright.md`\n"
        )
        once, _ = self._norm(text)
        twice, _ = self._norm(once)
        self.assertEqual(once, twice)
        self.assertIn("> **必须遵守 - 无例外**", twice)

    def test_rule2_coding_switch(self):
        """ut-norm-rule2：规则 2 按 project_type 选文案。"""
        text = "## 强制规则\n\n- **非必要不编写代码** → 详见 `.claude/rules/code-usage.md`\n"
        out, _ = self._norm(text, "CLAUDE.md", "coding", set())
        self.assertIn("遵循 TDD", out)
        self.assertNotIn("非必要不编写代码", out)

    def test_playwright_included_when_file_exists(self):
        """ut-norm-playwright：条件项。"""
        out, _ = self._norm(KB_AGENTS, files={"playwright.md"})
        self.assertIn("Playwright", out)
        out2, _ = self._norm(KB_AGENTS)
        self.assertNotIn("Playwright", out2)

    def test_user_h3_block_moved_as_whole(self):
        """ut-norm-user-h3：用户 H3 小节整体平移到权威条目之后。"""
        text = ("## 强制规则\n\n### 1. 语言规则\n- **必须使用中文回答** → 详见 `.claude/rules/language.md`\n"
                "### 我的自定义小节\n正文第一行\n正文第二行\n")
        out, warns = self._norm(text)
        idx_custom = out.index("### 我的自定义小节")
        idx_rule7 = out.index("### 7. 代码阅读规则")
        self.assertGreater(idx_custom, idx_rule7)
        self.assertIn("正文第一行\n正文第二行", out)

    def test_orphan_rule6_outside_section_warns(self):
        """ut-norm-orphan-rule6：章节外孤立规则 6 H2 保留 + ORPHAN_RULE6。"""
        text = ("## 强制规则\n\n- **必须使用中文回答** → 详见 `.claude/rules/language.md`\n\n"
                "## 项目个性化规则（强制规则）\n\n- 旧文案\n")
        out, warns = self._norm(text)
        self.assertIn("## 项目个性化规则（强制规则）", out)
        self.assertTrue(any(w["code"] == "ORPHAN_RULE6" for w in warns))

    def test_duplicate_h2_only_first_normalized(self):
        """ut-norm-dup-h2：多个 ## 强制规则 仅规范化首个 + DUPLICATE_H2。"""
        text = "## 强制规则\n\n- x `.claude/rules/language.md`\n\n## 强制规则\n\n- 旧 `.claude/rules/serena-usage.md`\n"
        out, warns = self._norm(text)
        self.assertTrue(any(w["code"] == "DUPLICATE_H2" for w in warns))
        self.assertEqual(out.count("## 强制规则"), 2)
        self.assertIn("serena-usage.md", out.split("## 强制规则")[2])

    def test_rule6_old_wording_replaced(self):
        """ut-norm-rule6-old：旧 CLAUDE/AGENTS 规则 6 文案识别并替换为权威块。"""
        old = "## 强制规则\n\n### 6. 项目个性化规则（强制规则）\n- **用户自定义规则只能存放在 `cadence/project-rules/` 目录**\n- 禁止在 `rules/` 目录中添加用户自定义规则\n- 详见 `cadence/project-rules/README.md`\n"
        out, _ = self._norm(old, "CLAUDE.md")
        self.assertIn("### 6. 项目个性化规则", out)
        self.assertNotIn("（强制规则）", out.split("## 强制规则")[1])

    def test_rule2_text_outside_section_untouched(self):
        """ut-norm-outside-rule2：章节外规则 2 旧文案不被修改。"""
        text = "## 强制规则\n\n- x `.claude/rules/language.md`\n\n## 笔记\n\n遵循 TDD 和代码规范 是我的座右铭\n"
        out, _ = self._norm(text, "CLAUDE.md", "non-coding", set())
        self.assertIn("遵循 TDD 和代码规范 是我的座右铭", out)

    def test_empty_retired_list_no_deletion(self):
        """ut-norm-retired-empty：退役清单为空时无删除。"""
        with mock.patch.object(rc, "RETIRED_RULE_FILES", []):
            text = "## 强制规则\n\n- x `.claude/rules/serena-usage.md`\n"
            out, _ = self._norm(text)
            self.assertIn("serena-usage.md", out)

    def test_claude_agents_wording_differs(self):
        """ut-norm-wording：MCP/规则 6 双入口文案差异。"""
        out_c, _ = self._norm(KB_AGENTS, "CLAUDE.md")
        out_a, _ = self._norm(KB_AGENTS, "AGENTS.md")
        self.assertIn("各 MCP 工具的使用规范", out_c)
        self.assertIn("各 MCP 工具及相关自动化工具的使用必须遵循项目规范", out_a)


class TestEnsureGitignoreLine(unittest.TestCase):
    """ensure_gitignore_line 行级幂等（grep -qxF 等价）：
    已含整行→skipped；未含或不存在→added（创建/追加 comment+line）。
    """

    def setUp(self):
        self._tmpdirs = []

    def tearDown(self):
        import shutil
        for d in self._tmpdirs:
            shutil.rmtree(d, ignore_errors=True)

    def _mkroot(self):
        d = tempfile.mkdtemp()
        self._tmpdirs.append(d)
        return Path(d)

    def test_adds_line_when_gitignore_absent(self):
        """ut-gitignore-create / S7-02（.gitignore 不存在→创建含 comment+line）"""
        root = self._mkroot()
        status = rc.ensure_gitignore_line(root, "cadence/", "# Cadence 产物目录")
        self.assertEqual(status, "added")
        gi = (root / ".gitignore").read_text(encoding="utf-8")
        self.assertIn("# Cadence 产物目录", gi)
        self.assertIn("cadence/", gi)

    def test_skipped_when_exact_line_exists(self):
        """ut-gitignore-idempotent-exact / S7-02（整行精确匹配→skipped，幂等）"""
        root = self._mkroot()
        rc.ensure_gitignore_line(root, "cadence/", "# Cadence 产物目录")
        status2 = rc.ensure_gitignore_line(root, "cadence/", "# Cadence 产物目录")
        self.assertEqual(status2, "skipped")
        # 内容不重复（只有一个 cadence/ 行）
        gi = (root / ".gitignore").read_text(encoding="utf-8")
        self.assertEqual(gi.count("cadence/"), 1)

    def test_added_when_line_is_substring_only(self):
        """ut-gitignore-qxf-semantics / S7-02（grep -qxF 语义：仅作为子串/前缀不算匹配→added）

        例：已有 `cadence/foo` 不会让 `cadence/` 判为已存在；整行必须精确相等。
        """
        root = self._mkroot()
        (root / ".gitignore").write_text("cadence/foo\n", encoding="utf-8")
        status = rc.ensure_gitignore_line(root, "cadence/", "# Cadence 产物目录")
        self.assertEqual(status, "added")
        gi = (root / ".gitignore").read_text(encoding="utf-8")
        # 两行都保留：原 cadence/foo 与新增 cadence/（grep -qxF 语义下二者不同）
        self.assertIn("cadence/foo", gi)
        # 整行精确为 cadence/ 的行恰一条（不计 cadence/foo 这种子串行）
        exact = [ln for ln in gi.splitlines() if ln == "cadence/"]
        self.assertEqual(len(exact), 1)


class TestComputePlanFinalReview(unittest.TestCase):
    """终审修复回归：C-1 recommendation 保守默认；I-2 L0 insert/upgrade 确定性动作。"""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.refs = Path(__file__).resolve().parents[1] / "references"
        self.rules_root = self.refs / "rules"
        self.openspec_yaml = self.refs / "openspec" / "config.yaml"
        # 隔离 locate_templates 的真实 HOME 三级搜索，固定指向 skill 自带 references
        patcher = mock.patch.object(
            rc, "locate_templates", return_value=(self.rules_root, self.openspec_yaml)
        )
        patcher.start()
        self.addCleanup(patcher.stop)

    def _conflicts_by_id(self, plan):
        return {c["conflict_id"]: c for c in plan.get("conflicts", [])}

    def test_recommendations_are_conservative_keep(self):
        """ut-compute_plan-recommendation-keep / 终审 C-1
        （s3 普通 drift / s3 L1 / s4 L0 drift / s7 rules.apply 的 recommendation
        一律为保守 keep，不得推荐覆盖型决策）"""
        rules_dir = self.root / ".claude" / "rules"
        rules_dir.mkdir(parents=True)
        (rules_dir / "language.md").write_text("本地漂移\n", encoding="utf-8")
        (rules_dir / rc.L1_RULE_FILENAME).write_text("L1 本地漂移\n", encoding="utf-8")
        (self.root / "CLAUDE.md").write_text(
            "# CLAUDE.md\n\n" + V2_START + "\n漂移\n" + V2_END + "\n", encoding="utf-8"
        )
        (self.root / "AGENTS.md").write_text("# AGENTS.md\n无标记\n", encoding="utf-8")
        (self.root / "openspec").mkdir()
        (self.root / "openspec" / "config.yaml").write_text(
            "schema: spec-driven\nrules:\n  apply:\n    - x\n", encoding="utf-8"
        )
        plan = rc.compute_plan(self.root, _intents())
        conflicts = self._conflicts_by_id(plan)
        # s3 普通 drift / s3 L1 / s4 drift / s7 rules.apply 均产冲突且推荐 keep
        expected = [
            "s3:.claude/rules/language.md",
            f"s3:.claude/rules/{rc.L1_RULE_FILENAME}",
            "s4:CLAUDE.md",
            "s7:openspec/config.yaml",
        ]
        for cid in expected:
            self.assertIn(cid, conflicts)
            self.assertEqual(conflicts[cid].get("recommendation"), "keep", cid)
        # allowed_decisions 枚举不变（推荐保守不等于收窄决策空间）
        self.assertEqual(
            conflicts["s3:.claude/rules/language.md"]["allowed_decisions"],
            ["replace", "keep"],
        )
        self.assertEqual(
            conflicts["s7:openspec/config.yaml"]["allowed_decisions"],
            ["remove_apply", "keep"],
        )

    def test_insert_is_deterministic_action_not_conflict(self):
        """ut-compute_plan-l0-insert-deterministic / 终审 I-2 + L0-05
        （无 L0 标记 → insert 确定性动作：不产冲突、不要求备份）"""
        (self.root / "CLAUDE.md").write_text("# CLAUDE.md\n\n用户内容\n", encoding="utf-8")
        (self.root / "AGENTS.md").write_text("# AGENTS.md\n\n用户内容\n", encoding="utf-8")
        plan = rc.compute_plan(self.root, _intents())
        conflicts = self._conflicts_by_id(plan)
        self.assertNotIn("s4:CLAUDE.md", conflicts)
        self.assertNotIn("s4:AGENTS.md", conflicts)
        assets = {
            a["path"]: a for a in plan["steps"][rc.STEP_ENTRY_FILES]["assets"]
        }
        self.assertEqual(assets["CLAUDE.md"]["action"], "insert")
        self.assertEqual(assets["CLAUDE.md"]["backup_needed"], False)
        self.assertNotIn(self.root / "CLAUDE.md", plan["backup_needs"])

    def test_upgrade_is_deterministic_action_with_backup(self):
        """ut-compute_plan-l0-upgrade-deterministic / 终审 I-2 + L0-04
        （旧版标记成对 → upgrade 确定性动作：不产冲突、纳入备份屏障）"""
        (self.root / "CLAUDE.md").write_text(
            "# CLAUDE.md\n\n" + V0_START + "\n旧版\n" + V0_END + "\n", encoding="utf-8"
        )
        plan = rc.compute_plan(self.root, _intents())
        conflicts = self._conflicts_by_id(plan)
        self.assertNotIn("s4:CLAUDE.md", conflicts)
        assets = {
            a["path"]: a for a in plan["steps"][rc.STEP_ENTRY_FILES]["assets"]
        }
        self.assertEqual(assets["CLAUDE.md"]["action"], "upgrade")
        self.assertEqual(assets["CLAUDE.md"]["backup_needed"], True)
        self.assertIn(self.root / "CLAUDE.md", plan["backup_needs"])

    def test_duplicate_current_blocks_are_deterministic_not_conflicts(self):
        """ut-compute-plan-l0-dedup：重复 v2 块必须直接归并，普通模式不要求决策。"""
        duplicate = L0_SOURCE + "\n\n## 用户章节\nx\n\n" + L0_SOURCE
        (self.root / "CLAUDE.md").write_text(duplicate, encoding="utf-8")
        plan = rc.compute_plan(self.root, _intents())
        conflicts = self._conflicts_by_id(plan)
        self.assertNotIn("s4:CLAUDE.md", conflicts)
        asset = next(
            a for a in plan["steps"][rc.STEP_ENTRY_FILES]["assets"]
            if a["path"] == "CLAUDE.md"
        )
        self.assertEqual(asset["action"], "dedup")
        self.assertTrue(asset["backup_needed"])
        self.assertIn(self.root / "CLAUDE.md", plan["backup_needs"])

    def test_drift_still_conflict_with_allowed_decisions(self):
        """ut-compute_plan-l0-drift-conflict / 终审 I-2 边界
        （drift/broken 仍产 decision 冲突，allowed_decisions=['replace','keep']）"""
        (self.root / "CLAUDE.md").write_text(
            "# CLAUDE.md\n\n" + V2_START + "\n漂移\n" + V2_END + "\n", encoding="utf-8"
        )
        plan = rc.compute_plan(self.root, _intents())
        conflicts = self._conflicts_by_id(plan)
        self.assertIn("s4:CLAUDE.md", conflicts)
        self.assertEqual(
            conflicts["s4:CLAUDE.md"]["allowed_decisions"], ["replace", "keep"]
        )

    def test_step_s4_insert_executes_in_normal_mode_without_decisions(self):
        """ut-step_s4-insert-normal-executes / 终审 I-2 + L0-05
        （普通模式无 decisions：insert 确定性执行，L0 插入且用户内容保留）"""
        entry = self.root / "CLAUDE.md"
        entry.write_text("# CLAUDE.md\n\n用户自定义内容\n", encoding="utf-8")
        plan = {
            "project_type": "non-coding",
            "templates": {"rules_root": str(self.rules_root)},
            "decisions_map": {},
            "steps": {
                rc.STEP_ENTRY_FILES: {
                    "name": rc.STEP_ENTRY_FILES, "status": "ok",
                    "assets": [{
                        "path": "CLAUDE.md", "action": "insert",
                        "conflict": "insert", "backup_needed": False,
                    }],
                }
            },
        }
        rc.step_s4_entry_files(self.root, _intents(), plan, {})
        text = entry.read_text(encoding="utf-8")
        self.assertIn(rc.L0_BEGIN, text)
        self.assertIn("用户自定义内容", text)


class TestStepS8BinaryMissing(unittest.TestCase):
    """终审 C-2：codegraph 二进制缺失 → install 失败降级路径（CS-07），不 crashed。"""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def test_binary_missing_degraded_with_dual_configs(self):
        """ut-step_s8-binary-missing-degraded / 终审 C-2 + CS-07
        （subprocess 抛 FileNotFoundError → overall=degraded + 双配置补齐 + note，不抛错）"""
        plan = {"project_type": "coding"}
        report = {"overall": "ok", "steps": []}
        with mock.patch.object(
            rc.subprocess, "run", side_effect=FileNotFoundError("codegraph")
        ):
            rc.step_s8_codegraph(self.root, _intents(no_interrupt=True), plan, report)
        self.assertEqual(report["overall"], "degraded")
        self.assertTrue((self.root / ".mcp.json").is_file())
        self.assertTrue((self.root / ".codex" / "config.toml").is_file())
        step = next(s for s in report["steps"] if s["name"] == rc.STEP_CODEGRAPH)
        self.assertEqual(step["status"], "degraded")
        self.assertIn("codegraph", step["reason"])
        self.assertIn("elapsed_ms", step)


class TestFailureSchemaFinalReview(unittest.TestCase):
    """终审 I-4：overall 收敛 ok/degraded/fail；failure.file 从异常上下文提取。"""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.refs = Path(__file__).resolve().parents[1] / "references"

    def test_extract_failure_file_from_message(self):
        """ut-extract-failure-file-message / 终审 I-4（从异常消息提取受管文件路径）"""
        exc = rc.PublishError("openspec/config.yaml unparseable，无法无损规范化")
        self.assertEqual(
            rc._extract_failure_file(exc, "s7_openspec_config"), "openspec/config.yaml"
        )
        exc2 = rc.PublishError("原子写入失败：.claude/rules/language.md（mock）")
        self.assertEqual(
            rc._extract_failure_file(exc2, "s3_rules_files"), ".claude/rules/language.md"
        )

    def test_extract_failure_file_fallbacks(self):
        """ut-extract-failure-file-fallback / 终审 I-4（属性优先；兑底步骤标识，不为 None）"""
        exc = OSError("disk error")
        exc.filename = "CLAUDE.md"
        self.assertEqual(rc._extract_failure_file(exc, None), "CLAUDE.md")
        # 无属性、无已知路径 → 兑底为步骤标识
        self.assertEqual(
            rc._extract_failure_file(Exception("boom"), "s2_locate_templates"),
            "s2_locate_templates",
        )
        self.assertIsNotNone(rc._extract_failure_file(Exception("boom"), None))

    def test_run_apply_exception_lands_fail_with_file(self):
        """ut-run_apply-fail-schema / 终审 I-4
        （执行异常 → overall=fail（非 crashed）+ failure.file 非 None 且为实际文件）"""
        rules_root = self.refs / "rules"
        openspec_yaml = self.refs / "openspec" / "config.yaml"
        report = rc.build_report("no-interrupt", self.root)

        def _boom(root, intents, plan, report):
            raise rc.PublishError("原子写入失败：.claude/rules/language.md（mock）")

        patched_funcs = dict(rc.STEP_FUNCS)
        patched_funcs[rc.STEP_RULES_FILES] = _boom
        with mock.patch.object(
            rc, "locate_templates", return_value=(rules_root, openspec_yaml)
        ), mock.patch.dict(rc.STEP_FUNCS, patched_funcs, clear=True):
            code = rc.run_apply(self.root, _intents(no_interrupt=True), report)
        self.assertEqual(code, 1)
        self.assertIn(report["overall"], ("ok", "degraded", "fail"))
        self.assertEqual(report["overall"], "fail")
        self.assertEqual(report["failure"]["file"], ".claude/rules/language.md")
        self.assertTrue(report["failure"]["reason"])
        self.assertTrue(report["failure"]["recovery"])


class TestS8EnsureMcpConfigs(unittest.TestCase):
    """codex 终审 C2：.mcp.json 重写前必须备份（含无效 JSON），备份失败即终止。"""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def test_invalid_mcpjson_backed_up_before_rewrite(self):
        """ut-s8-mcpjson-invalid-backup / codex 终审 C2
        （无效 .mcp.json → 重写前备份存在 + 原子重写 + 原内容保留在备份中）"""
        mcp = self.root / ".mcp.json"
        mcp.write_text("{invalid json\n", encoding="utf-8")
        report = {"backups": []}
        actions: list = []
        rc._s8_ensure_mcp_configs(self.root, report, actions)
        backups = list(
            (self.root / "cadence" / "legacy").glob("*/.mcp.json")
        )
        self.assertEqual(len(backups), 1)
        self.assertEqual(backups[0].read_text(encoding="utf-8"), "{invalid json\n")
        doc = json.loads(mcp.read_text(encoding="utf-8"))
        self.assertIn("codegraph", doc["mcpServers"])
        self.assertEqual(report["backups"][0]["file"], str(mcp))
        self.assertEqual(report["backups"][0]["backup"], str(backups[0]))

    def test_valid_mcpjson_without_codegraph_backed_up_before_merge(self):
        """ut-s8-mcpjson-valid-backup / codex 终审 C2
        （有效但缺 codegraph 的 .mcp.json → 合并重写前同样备份，其他 server 保留）"""
        mcp = self.root / ".mcp.json"
        mcp.write_text(
            '{ "mcpServers": { "other": { "command": "other" } } }\n',
            encoding="utf-8",
        )
        report = {"backups": []}
        rc._s8_ensure_mcp_configs(self.root, report, [])
        backups = list(
            (self.root / "cadence" / "legacy").glob("*/.mcp.json")
        )
        self.assertEqual(len(backups), 1)
        doc = json.loads(mcp.read_text(encoding="utf-8"))
        self.assertIn("codegraph", doc["mcpServers"])
        self.assertIn("other", doc["mcpServers"])

    def test_missing_mcpjson_created_without_backup(self):
        """ut-s8-mcpjson-create-no-backup / codex 终审 C2（.mcp.json 不存在 → 原子创建，无原文件不备份）"""
        report = {"backups": []}
        rc._s8_ensure_mcp_configs(self.root, report, [])
        self.assertTrue((self.root / ".mcp.json").is_file())
        self.assertEqual(
            list((self.root / "cadence" / "legacy").glob("*/.mcp.json")), []
        )
        self.assertEqual(report["backups"], [])


class TestFilterBackupNeeds(unittest.TestCase):
    """codex 终审 I3：备份屏障只收集真实写入需求（keep 决策与幂等不备份）。"""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.refs = Path(__file__).resolve().parents[1] / "references"

    def _plan(self, s3_assets=None, s4_assets=None, s7_assets=None, decisions=None):
        return {
            "templates": {
                "rules_root": str(self.refs / "rules"),
                "openspec_yaml": str(self.refs / "openspec" / "config.yaml"),
            },
            "decisions_map": decisions or {},
            "backup_needs": [],
            "steps": {
                rc.STEP_RULES_FILES: {"assets": s3_assets or []},
                rc.STEP_ENTRY_FILES: {"assets": s4_assets or []},
                rc.STEP_OPENSPEC_CONFIG: {"assets": s7_assets or []},
            },
        }

    def test_s3_keep_decision_not_backed_up(self):
        """ut-filter-backup-s3-keep / codex 终审 I3（keep 决策 → 不生成备份；replace/no-interrupt → 备份）"""
        target = self.root / ".claude" / "rules" / "language.md"
        plan = self._plan(
            s3_assets=[{
                "path": ".claude/rules/language.md", "action": "replace",
                "conflict": "drift", "backup_needed": True,
            }],
            decisions={"s3:.claude/rules/language.md": "keep"},
        )
        plan["backup_needs"] = [target]
        self.assertEqual(rc._filter_backup_needs(plan, _intents(), self.root), [])
        plan["decisions_map"] = {"s3:.claude/rules/language.md": "replace"}
        self.assertEqual(rc._filter_backup_needs(plan, _intents(), self.root), [target])
        self.assertEqual(
            rc._filter_backup_needs(plan, _intents(no_interrupt=True), self.root),
            [target],
        )

    def test_s7_idempotent_merge_not_backed_up(self):
        """ut-filter-backup-s7-idempotent / codex 终审 I3（候选==现状 → 零备份；候选有差异 → 备份）"""
        config = self.root / "openspec" / "config.yaml"
        config.parent.mkdir(parents=True)
        tpl = (self.refs / "openspec" / "config.yaml").read_text(encoding="utf-8")
        merged, _ = rc.merge_yaml(tpl, "")
        config.write_text(merged, encoding="utf-8")
        plan = self._plan(s7_assets=[{
            "path": "openspec/config.yaml", "action": "merge",
            "conflict": None, "backup_needed": True,
        }])
        plan["backup_needs"] = [config]
        self.assertEqual(
            rc._filter_backup_needs(plan, _intents(no_interrupt=True), self.root), [],
        )
        # 候选确有差异 → 保留备份需求
        config.write_text("schema: spec-driven\ncontext: |\n  custom\n", encoding="utf-8")
        self.assertEqual(
            rc._filter_backup_needs(plan, _intents(no_interrupt=True), self.root),
            [config],
        )

    def test_s7_rules_apply_default_keep_not_backed_up(self):
        """ut-filter-backup-s7-rules-apply / codex 终审 I3
        （rules.apply 无决策默认 keep → 不备份；remove_apply/no-interrupt → 备份）"""
        config = self.root / "openspec" / "config.yaml"
        config.parent.mkdir(parents=True)
        config.write_text(
            "schema: spec-driven\nrules:\n  apply:\n    - x\n", encoding="utf-8",
        )
        plan = self._plan(s7_assets=[{
            "path": "openspec/config.yaml", "action": "keep",
            "conflict": {"kind": "rules.apply"}, "backup_needed": True,
        }])
        plan["backup_needs"] = [config]
        self.assertEqual(rc._filter_backup_needs(plan, _intents(), self.root), [])
        plan["decisions_map"] = {"s7:openspec/config.yaml": "remove_apply"}
        self.assertEqual(rc._filter_backup_needs(plan, _intents(), self.root), [config])
        plan["decisions_map"] = {}
        self.assertEqual(
            rc._filter_backup_needs(plan, _intents(no_interrupt=True), self.root),
            [config],
        )

    def test_s7_structure_conflict_normal_not_backed_up_no_interrupt_backed_up(self):
        """ut-filter-backup-s7-structure / codex 终审 I3
        （结构冲突：普通保留不备份；no-interrupt 备份后终止仍需备份）"""
        config = self.root / "openspec" / "config.yaml"
        config.parent.mkdir(parents=True)
        config.write_text("schema: [1]\n", encoding="utf-8")
        plan = self._plan(s7_assets=[{
            "path": "openspec/config.yaml", "action": "keep",
            "conflict": {"kind": "structure", "fields": ["schema"]},
            "backup_needed": True,
        }])
        plan["backup_needs"] = [config]
        self.assertEqual(rc._filter_backup_needs(plan, _intents(), self.root), [])
        self.assertEqual(
            rc._filter_backup_needs(plan, _intents(no_interrupt=True), self.root),
            [config],
        )

    def test_s4_upgrade_always_backed_up_drift_keep_not(self):
        """ut-filter-backup-s4-states / codex 终审 I3（upgrade 确定性升级必备份；drift keep 决策不备份）"""
        entry = self.root / "CLAUDE.md"
        plan = self._plan(s4_assets=[{
            "path": "CLAUDE.md", "action": "upgrade",
            "conflict": "upgrade", "backup_needed": True,
        }])
        plan["backup_needs"] = [entry]
        self.assertEqual(rc._filter_backup_needs(plan, _intents(), self.root), [entry])
        plan2 = self._plan(
            s4_assets=[{
                "path": "CLAUDE.md", "action": "replace",
                "conflict": "drift", "backup_needed": True,
            }],
            decisions={"s4:CLAUDE.md": "keep"},
        )
        plan2["backup_needs"] = [entry]
        self.assertEqual(rc._filter_backup_needs(plan2, _intents(), self.root), [])

    def test_unmatched_target_conservatively_kept(self):
        """ut-filter-backup-unmatched / codex 终审 I3（无法归属的备份需求保守保留，不放宽屏障）"""
        stray = self.root / "stray.txt"
        plan = self._plan()
        plan["backup_needs"] = [stray]
        self.assertEqual(rc._filter_backup_needs(plan, _intents(), self.root), [stray])


class TestFinalProjectTypeTwoModeRules(unittest.TestCase):
    """ut-final-project-type / IA-02 重构（codex 五轮）

    用户裁决的项目类型规则（删除 s1:project-type-conflict 后的唯一确定结果）：
      - no-interrupt：final = 检测结果（CLI --project-type 完全忽略）
      - 普通模式：检测 coding → coding（无论 CLI）；检测 non-coding + CLI coding → coding；
        检测 non-coding + CLI 不写或 non-coding → non-coding
    覆盖范围 = 两模式行表 + no-interrupt 忽略 CLI。
    """

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.refs = Path(__file__).resolve().parents[1] / "references"

    def _coding_root(self):
        (self.root / "application").mkdir(exist_ok=True)
        (self.root / "application" / "app.py").write_text("x = 1\n")

    def _noncoding_root(self):
        (self.root / "README.md").write_text("docs only\n")

    def _compute(self, **intents_overrides):
        with mock.patch.object(
            rc, "locate_templates",
            return_value=(self.refs / "rules", self.refs / "openspec" / "config.yaml"),
        ):
            return rc.compute_plan(self.root, _intents(**intents_overrides))

    # --- 行表 1：no-interrupt + 检测 non-coding + CLI coding → non-coding（CLI 被忽略）---
    def test_no_interrupt_ignores_cli_coding_when_detected_noncoding(self):
        self._noncoding_root()
        plan = self._compute(no_interrupt=True, project_type="coding")
        self.assertEqual(plan["project_type"], "non-coding")

    # --- 行表 2：no-interrupt + 检测 coding → coding（CLI 忽略，无论写什么）---
    def test_no_interrupt_detected_coding_ignores_cli_noncoding(self):
        self._coding_root()
        plan = self._compute(no_interrupt=True, project_type="non-coding")
        self.assertEqual(plan["project_type"], "coding")

    # --- 行表 3：普通模式 + 检测 non-coding + CLI coding → coding（CLI 提升）---
    def test_normal_cli_promotes_noncoding_to_coding(self):
        self._noncoding_root()
        plan = self._compute(no_interrupt=False, project_type="coding")
        self.assertEqual(plan["project_type"], "coding")

    # --- 行表 4：普通模式 + 检测 coding → coding（无论 CLI）---
    def test_normal_detected_coding_stays_coding(self):
        self._coding_root()
        plan = self._compute(no_interrupt=False, project_type="non-coding")
        self.assertEqual(plan["project_type"], "coding")

    # --- 行表 5：普通模式 + 检测 non-coding + 无 CLI → non-coding ---
    def test_normal_detected_noncoding_no_cli_stays_noncoding(self):
        self._noncoding_root()
        plan = self._compute(no_interrupt=False, project_type=None)
        self.assertEqual(plan["project_type"], "non-coding")

    # --- 行表 5b：普通模式 + 检测 non-coding + CLI non-coding → non-coding ---
    def test_normal_detected_noncoding_cli_noncoding_stays_noncoding(self):
        self._noncoding_root()
        plan = self._compute(no_interrupt=False, project_type="non-coding")
        self.assertEqual(plan["project_type"], "non-coding")

    # --- 连带：重构后 compute_plan 不再产 s1:project-type-conflict ---
    def test_compute_plan_no_s1_project_type_conflict(self):
        self._coding_root()
        for cli in (None, "coding", "non-coding"):
            for ni in (True, False):
                plan = self._compute(no_interrupt=ni, project_type=cli)
                ids = [c.get("conflict_id") for c in plan.get("conflicts", [])]
                self.assertNotIn("s1:project-type-conflict", ids)


class TestReportCompleteness(unittest.TestCase):
    """codex 终审 I4：报告 conflicts 含 allowed_decisions；S1-S7 真实计时。"""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.refs = Path(__file__).resolve().parents[1] / "references"

    def test_sync_plan_conflicts_include_allowed_decisions(self):
        """ut-report-conflicts-allowed-decisions / codex 终审 I4
        （报告顶层 conflicts 含 allowed_decisions，供 Agent 生成 decisions）"""
        plan = {
            "project_type": "non-coding",
            "steps": {},
            "conflicts": [{
                "conflict_id": "s3:.claude/rules/language.md",
                "asset": ".claude/rules/language.md",
                "state": "drift",
                "allowed_decisions": ["replace", "keep"],
                "question": "q", "recommendation": "keep",
            }],
        }
        report: dict = {}
        rc._sync_plan_to_report(plan, report, _intents())
        self.assertEqual(
            report["conflicts"][0]["allowed_decisions"], ["replace", "keep"],
        )

    def test_compute_plan_steps_have_real_elapsed(self):
        """ut-compute-plan-real-elapsed / codex 终审 I4
        （S1-S7 以 time.monotonic() 真实计时；单调时钟递进时各步 elapsed_ms>0）"""
        ticks = iter(range(0, 1000000, 5))
        with mock.patch.object(
            rc.time, "monotonic", side_effect=lambda: next(ticks) / 1000.0
        ), mock.patch.object(
            rc, "locate_templates",
            return_value=(self.refs / "rules", self.refs / "openspec" / "config.yaml"),
        ):
            plan = rc.compute_plan(self.root, _intents())
        for name in (
            rc.STEP_DETECT, rc.STEP_TEMPLATES, rc.STEP_RULES_FILES,
            rc.STEP_ENTRY_FILES, rc.STEP_SCAFFOLD, rc.STEP_GITIGNORE,
            rc.STEP_OPENSPEC_CONFIG,
        ):
            step = plan["steps"][name]
            self.assertIsInstance(step["elapsed_ms"], int)
            self.assertGreater(step["elapsed_ms"], 0, f"{name} 未真实计时")


class TestDriftConflictNoInterruptAction(unittest.TestCase):
    """P1-1：no-interrupt 下 drift 冲突条目携带真实执行动作字段，避免 recommendation=keep 误导。"""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.refs = Path(__file__).resolve().parents[1] / "references"
        rules = self.root / ".claude" / "rules"
        rules.mkdir(parents=True)
        (rules / "language.md").write_text("# 项目自定义语言规则\n\n与模板不同。\n", encoding="utf-8")

    def _compute(self, **overrides):
        with mock.patch.object(
            rc, "locate_templates",
            return_value=(self.refs / "rules", self.refs / "openspec" / "config.yaml"),
        ):
            return rc.compute_plan(self.root, _intents(**overrides))

    def test_no_interrupt_marks_real_action(self):
        """ut-compute-plan-no-interrupt-action / P1-1（no-interrupt drift 标注 authoritative-overwrite，recommendation 不变）"""
        plan = self._compute(no_interrupt=True)
        s3 = plan["steps"][rc.STEP_RULES_FILES]
        entry = next(c for c in s3["conflicts"] if str(c.get("asset", "")).endswith("language.md"))
        self.assertEqual(entry["no_interrupt_action"], "authoritative-overwrite")
        self.assertEqual(entry["recommendation"], "keep")
        top = next(c for c in plan["conflicts"] if str(c.get("asset", "")).endswith("language.md"))
        self.assertEqual(top["no_interrupt_action"], "authoritative-overwrite")

    def test_normal_mode_omits_field(self):
        """ut-compute-plan-normal-no-action-field / P1-1（普通模式冲突条目不新增字段）"""
        plan = self._compute()
        s3 = plan["steps"][rc.STEP_RULES_FILES]
        self.assertFalse(any("no_interrupt_action" in c for c in s3["conflicts"]))
        self.assertFalse(any("no_interrupt_action" in c for c in plan["conflicts"]))

    def test_report_no_interrupt_action(self):
        """ut-report-no-interrupt-action / P1-1（对外报告转发 no-interrupt 权威覆盖动作）"""
        plan = self._compute(no_interrupt=True)
        report: dict = {}
        rc._sync_plan_to_report(plan, report, _intents(no_interrupt=True))
        conflict = next(
            c for c in report["conflicts"]
            if str(c.get("asset", "")).endswith("language.md")
        )
        self.assertEqual(
            conflict["no_interrupt_action"], "authoritative-overwrite"
        )

    def test_report_normal_no_action_field(self):
        """ut-report-normal-no-action-field / P1-1（普通模式对外报告无 no-interrupt 动作）"""
        plan = self._compute()
        report: dict = {}
        rc._sync_plan_to_report(plan, report, _intents())
        conflict = next(
            c for c in report["conflicts"]
            if str(c.get("asset", "")).endswith("language.md")
        )
        self.assertNotIn("no_interrupt_action", conflict)


class TestTask6RegressionMatrix(unittest.TestCase):
    """Task 6：dry-run 字段、幂等与跨资产失败关闭回归矩阵。"""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "proj"
        self.root.mkdir(parents=True)
        self.rules_root = Path(__file__).resolve().parents[1] / "references" / "rules"
        self.openspec_yaml = (
            Path(__file__).resolve().parents[1]
            / "references"
            / "openspec"
            / "config.yaml"
        )

    def _apply(self, *, coding=False):
        report = rc.build_report("no-interrupt", self.root)
        patches = [
            mock.patch.object(
                rc,
                "locate_templates",
                return_value=(self.rules_root, self.openspec_yaml),
            )
        ]
        if coding:
            patches.append(
                mock.patch.object(
                    rc.subprocess, "run", return_value=mock.Mock(returncode=0)
                )
            )
        with patches[0]:
            if coding:
                with patches[1]:
                    code = rc.run_apply(
                        self.root, _intents(no_interrupt=True), report
                    )
            else:
                code = rc.run_apply(
                    self.root, _intents(no_interrupt=True), report
                )
        return code, report

    def _snapshot_files(self):
        return {
            str(path): path.read_bytes()
            for path in self.root.rglob("*")
            if path.is_file()
        }

    @staticmethod
    def _snapshot_paths(root):
        if not root.exists():
            return set()
        return {str(path) for path in root.rglob("*")}

    def test_dry_run_no_interrupt_action_field(self):
        rules = self.root / ".claude" / "rules"
        rules.mkdir(parents=True)
        (rules / "mcp-servers.md").write_text("drift", encoding="utf-8")
        report = {}
        with mock.patch.object(
            rc,
            "locate_templates",
            return_value=(self.rules_root, self.openspec_yaml),
        ):
            code = rc.run_dry_run(
                self.root, _intents(no_interrupt=True), report
            )
        self.assertEqual(code, 0)
        mcp = [
            conflict
            for conflict in report.get("conflicts", [])
            if "mcp-servers" in conflict.get("conflict_id", "")
        ]
        self.assertTrue(mcp)
        self.assertEqual(
            mcp[0]["no_interrupt_action"], "authoritative-overwrite"
        )

    def test_dry_run_normal_mode_no_field(self):
        rules = self.root / ".claude" / "rules"
        rules.mkdir(parents=True)
        (rules / "mcp-servers.md").write_text("drift", encoding="utf-8")
        report = {}
        with mock.patch.object(
            rc,
            "locate_templates",
            return_value=(self.rules_root, self.openspec_yaml),
        ):
            code = rc.run_dry_run(
                self.root, _intents(no_interrupt=False), report
            )
        self.assertEqual(code, 0)
        mcp = [
            conflict
            for conflict in report.get("conflicts", [])
            if "mcp-servers" in conflict.get("conflict_id", "")
        ]
        self.assertTrue(mcp)
        self.assertNotIn("no_interrupt_action", mcp[0])

    def test_double_apply_idempotent(self):
        (self.root / "package.json").write_text(
            '{"scripts":{"test":"jest"}}', encoding="utf-8"
        )
        code, report = self._apply(coding=True)
        self.assertEqual(code, 0, report.get("failure"))
        snapshot1 = self._snapshot_files()
        legacy_root = self.root / "cadence" / "legacy"
        legacy_paths1 = self._snapshot_paths(legacy_root)

        with mock.patch.object(
            rc, "atomic_write", wraps=rc.atomic_write
        ) as atomic_write_spy:
            code, report = self._apply(coding=True)

        self.assertEqual(code, 0, report.get("failure"))
        atomic_write_spy.assert_not_called()
        snapshot2 = self._snapshot_files()
        self.assertEqual(set(snapshot1), set(snapshot2))
        for path, content in snapshot1.items():
            self.assertEqual(snapshot2[path], content, f"changed: {path}")
        self.assertEqual(
            self._snapshot_paths(legacy_root), legacy_paths1
        )

    def test_drift_overwrite_then_rerun_no_archive(self):
        rules = self.root / ".claude" / "rules"
        rules.mkdir(parents=True)
        (rules / "mcp-servers.md").write_text(
            "### Serena\nold\n", encoding="utf-8"
        )
        code, report = self._apply()
        self.assertEqual(code, 0, report.get("failure"))
        snapshot1 = self._snapshot_files()
        legacy_root = self.root / "cadence" / "legacy"
        legacy_paths1 = self._snapshot_paths(legacy_root)

        with mock.patch.object(
            rc, "atomic_write", wraps=rc.atomic_write
        ) as atomic_write_spy:
            code, report = self._apply()

        self.assertEqual(code, 0, report.get("failure"))
        self.assertEqual(atomic_write_spy.call_count, 0)
        snapshot2 = self._snapshot_files()
        self.assertEqual(set(snapshot1), set(snapshot2))
        for path, content in snapshot1.items():
            self.assertEqual(snapshot2[path], content, f"changed: {path}")
        self.assertEqual(
            self._snapshot_paths(legacy_root), legacy_paths1
        )

    def test_type_switch_then_rerun_stable(self):
        rules = self.root / ".claude" / "rules"
        rules.mkdir(parents=True)
        (rules / "code-usage.md").write_text(
            "非必要不编写代码", encoding="utf-8"
        )
        (self.root / "package.json").write_text(
            '{"scripts":{"test":"jest"}}', encoding="utf-8"
        )
        code, report = self._apply(coding=True)
        self.assertEqual(code, 0, report.get("failure"))
        snapshot1 = self._snapshot_files()
        legacy_root = self.root / "cadence" / "legacy"
        legacy_dirs_before = (
            {path.name for path in legacy_root.iterdir() if path.is_dir()}
            if legacy_root.exists()
            else set()
        )

        with mock.patch.object(
            rc, "atomic_write", wraps=rc.atomic_write
        ) as atomic_write_spy:
            code, report = self._apply(coding=True)

        self.assertEqual(code, 0, report.get("failure"))
        self.assertEqual(atomic_write_spy.call_count, 0)
        snapshot2 = self._snapshot_files()
        self.assertEqual(set(snapshot1), set(snapshot2))
        for path, content in snapshot1.items():
            self.assertEqual(snapshot2[path], content, f"changed: {path}")
        legacy_dirs_after = (
            {path.name for path in legacy_root.iterdir() if path.is_dir()}
            if legacy_root.exists()
            else set()
        )
        self.assertEqual(legacy_dirs_after, legacy_dirs_before)

    def test_l0_second_archive_failure_keeps_both(self):
        """L0 双入口：第二个归档失败时两入口都不写入（构造 drift 触发备份）"""
        for entry in ("CLAUDE.md", "AGENTS.md"):
            (self.root / entry).write_text(
                f"# {entry}\n\n{rc.L0_BEGIN}\nDRIFTED\n{rc.L0_END}\n\n## 强制规则\n", encoding="utf-8")
        orig = rc.backup_file; calls = []
        def fail_second(path, r):
            calls.append(path)
            if len(calls) == 2:
                raise rc.BackupError("simulated")
            return orig(path, r)
        report = rc.build_report("no-interrupt", self.root)
        with mock.patch.object(
            rc, "backup_file", side_effect=fail_second
        ), mock.patch.object(
            rc,
            "locate_templates",
            return_value=(self.rules_root, self.openspec_yaml),
        ):
            code = rc.run_apply(
                self.root, _intents(no_interrupt=True), report
            )
        self.assertEqual(code, 1)
        # 两入口 L0 仍是 drift 状态（未写入）
        self.assertIn("DRIFTED", (self.root / "CLAUDE.md").read_text(encoding="utf-8"))
        self.assertIn("DRIFTED", (self.root / "AGENTS.md").read_text(encoding="utf-8"))

    def test_atomic_write_failure_keeps_original(self):
        rules = self.root / ".claude" / "rules"; rules.mkdir(parents=True)
        target = rules / "mcp-servers.md"
        target.write_text("old", encoding="utf-8")
        original_atomic_write = rc.atomic_write

        def fail_target(path, content):
            if Path(path) == target:
                raise OSError("simulated")
            return original_atomic_write(path, content)

        report = rc.build_report("no-interrupt", self.root)
        with mock.patch.object(rc, "atomic_write", side_effect=fail_target), \
             mock.patch.object(rc, "locate_templates", return_value=(self.rules_root, self.openspec_yaml)):
            rc.run_apply(self.root, _intents(no_interrupt=True), report)
        self.assertEqual(target.read_text(encoding="utf-8"), "old")  # 原文件不变
        self.assertTrue(any((self.root / "cadence" / "legacy").rglob("mcp-servers.md")))  # 归档保留

    def test_legacy_unlink_failure_keeps_file(self):
        rules = self.root / ".claude" / "rules"
        rules.mkdir(parents=True)
        legacy_file = rules / "code-usage-coding.md"
        legacy_file.write_text("legacy", encoding="utf-8")
        original_unlink = rc.Path.unlink
        unlink_calls = []

        def fail_legacy_unlink(path, *args, **kwargs):
            unlink_calls.append(Path(path))
            if Path(path) == legacy_file:
                raise OSError("simulated")
            return original_unlink(path, *args, **kwargs)

        report = rc.build_report("no-interrupt", self.root)
        with mock.patch.object(
            rc.Path, "unlink", new=fail_legacy_unlink
        ), mock.patch.object(
            rc,
            "locate_templates",
            return_value=(self.rules_root, self.openspec_yaml),
        ):
            code = rc.run_apply(
                self.root, _intents(no_interrupt=True), report
            )

        self.assertEqual(code, 1)
        self.assertEqual(report["overall"], "fail")
        self.assertIn(legacy_file, unlink_calls)
        self.assertTrue(legacy_file.exists())
        self.assertFalse((rules / "code-usage.md").exists())
        self.assertTrue(
            any(
                (self.root / "cadence" / "legacy").rglob(
                    "code-usage-coding.md"
                )
            )
        )

    def test_same_second_conflict_suffix(self):
        rules = self.root / ".claude" / "rules"; rules.mkdir(parents=True)
        target = rules / "language.md"; target.write_text("old", encoding="utf-8")
        # 固定时钟，确保两次归档确实发生在同一秒。
        fixed = rc.datetime(2026, 8, 1, 12, 0, 0)
        with mock.patch.object(rc, "datetime") as mocked_datetime:
            mocked_datetime.now.return_value = fixed
            rc.backup_file(target, self.root)
            rc.backup_file(target, self.root)
        legacy = self.root / "cadence" / "legacy"
        dirs = sorted(d.name for d in legacy.iterdir() if d.is_dir())
        self.assertEqual(dirs, ["20260801120000", "20260801120000-2"])


class TestCodegraphSectionUnifiedMerge(unittest.TestCase):
    """RF-04 去特判：缺 CodeGraph 段落的 code-reading.md 回归普通规则文件统一 drift 处理。"""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.refs = Path(__file__).resolve().parents[1] / "references"
        rules = self.root / ".claude" / "rules"
        rules.mkdir(parents=True)
        (rules / "code-reading.md").write_text(
            "# 旧版代码阅读规则\n\n仅 ast-grep，无其他内容。\n", encoding="utf-8",
        )

    def _compute(self):
        with mock.patch.object(
            rc, "locate_templates",
            return_value=(self.refs / "rules", self.refs / "openspec" / "config.yaml"),
        ):
            return rc.compute_plan(self.root, _intents())

    def test_missing_codegraph_section_is_plain_drift(self):
        """ut-s3-codegraph-section-unified-drift / RF-04（缺 CodeGraph 段落 → 普通 drift 冲突，进 decisions 与备份需求）"""
        plan = self._compute()
        s3 = plan["steps"][rc.STEP_RULES_FILES]
        asset = next(a for a in s3["assets"] if a["path"].endswith("code-reading.md"))
        self.assertEqual(asset["action"], "replace")
        self.assertEqual(asset["conflict"], "drift")
        self.assertTrue(asset["backup_needed"])
        self.assertTrue(
            any(str(c.get("asset", "")).endswith("code-reading.md")
                for c in plan["conflicts"])
        )
        self.assertTrue(
            any(str(b).endswith("code-reading.md") for b in plan["backup_needs"])
        )
        # codegraph-section-missing 冲突类型已移除
        self.assertFalse(
            any(c.get("kind") == "codegraph-section-missing"
                or c.get("conflict") == "codegraph-section-missing"
                for c in s3["conflicts"])
        )

    def test_no_interrupt_execute_merges_codegraph_section(self):
        """ut-s3-codegraph-section-unified-merge / RF-05（no-interrupt 权威覆盖为完整模板）"""
        plan = self._compute()
        report = {"steps": [], "overall": "ok"}
        rc._sync_plan_to_report(plan, report, _intents(no_interrupt=True))
        rc.step_s3_rules_files(self.root, _intents(no_interrupt=True), plan, report)
        result = (self.root / ".claude" / "rules" / "code-reading.md").read_text(encoding="utf-8")
        template = (self.refs / "rules" / "code-reading.md").read_text(encoding="utf-8")
        self.assertEqual(result, template)
        self.assertIn("CodeGraph", result)
        self.assertNotIn("仅 ast-grep", result)


class TestEndToEndRegression(unittest.TestCase):
    """ut-e2e-entry-kb / ut-e2e-entry-claude：问题入口文件端到端回归。

    fixture 来源于初始化问题现场的 /tmp/AGENTS.md 与 /tmp/CLAUDE.md；报告路径
    特意放在项目根外，覆盖真实 CLI ``apply --no-interrupt`` 而非仅调用内部函数。
    """

    FIXTURES = Path(__file__).resolve().parent / "fixtures"

    def _run(self):
        td = tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)
        root = Path(td.name)
        (root / "package.json").write_text(
            '{"scripts":{"test":"vitest","lint":"oxlint src"}}',
            encoding="utf-8",
        )
        (root / "AGENTS.md").write_text(
            (self.FIXTURES / "entry-kb-agents.md").read_text(encoding="utf-8"),
            encoding="utf-8",
        )
        (root / "CLAUDE.md").write_text(
            (self.FIXTURES / "entry-drift-claude.md").read_text(encoding="utf-8"),
            encoding="utf-8",
        )
        report_fd, report_name = tempfile.mkstemp(
            prefix="rule-config-entry-e2e-", suffix=".json"
        )
        os.close(report_fd)
        report = Path(report_name)
        self.addCleanup(lambda: report.unlink(missing_ok=True))
        self.assertNotIn(root, report.parents)
        subprocess.run(
            [
                "python3",
                str(SCRIPT_PATH),
                "apply",
                "--project-root",
                str(root),
                "--report",
                str(report),
                "--no-interrupt",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        result = json.loads(report.read_text(encoding="utf-8"))
        self.assertEqual(result["overall"], "ok")
        return root, result

    def test_kb_agents_gets_full_section(self):
        """ut-e2e-kb：KB 型 AGENTS.md 获得完整强制规则且用户内容保留。"""
        root, _report = self._run()
        agents = (root / "AGENTS.md").read_text(encoding="utf-8")
        for number, title in (
            (1, "语言规则"),
            (2, "代码使用规则"),
            (3, "文档存储规则"),
            (4, "Markdown 格式规则"),
            (5, "MCP Server 使用规则"),
            (6, "项目个性化规则"),
            (7, "代码阅读规则"),
        ):
            self.assertIn(f"### {number}. {title}", agents)
        self.assertIn(V2_START, agents)
        self.assertIn(V2_END, agents)
        self.assertIn("## WHERE TO LOOK", agents)  # 用户 KB 内容保留
        self.assertIn("产物自动提交（design/plan）**：关闭", agents)
        self.assertNotIn("serena-usage.md", agents)

    def test_dry_run_warnings_match_apply(self):
        """ut-e2e-warnings：dry-run 与无中断 apply 的 planned warnings 完全一致。"""
        td = tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)
        root = Path(td.name)
        (root / "package.json").write_text(
            '{"scripts":{"test":"vitest","lint":"oxlint src"}}',
            encoding="utf-8",
        )
        # 构造会触发纯函数 warnings 的入口：重复强制规则 H2、孤立规则 6，
        # 并保留正常用户内容以覆盖 warnings 的 code/file 字段。
        (root / "CLAUDE.md").write_text(
            "# CLAUDE.md\n\n"
            "## 强制规则\n\n"
            "### 1. 语言规则\n"
            "- **必须使用中文回答** → 详见 `.claude/rules/language.md`\n\n"
            "## 强制规则\n\n"
            "- 用户自定义说明\n\n"
            "## 项目个性化规则（强制规则）\n\n"
            "- 孤立说明\n",
            encoding="utf-8",
        )
        dry_fd, dry_name = tempfile.mkstemp(prefix="rule-config-dry-", suffix=".json")
        apply_fd, apply_name = tempfile.mkstemp(prefix="rule-config-apply-", suffix=".json")
        os.close(dry_fd); os.close(apply_fd)
        dry_report = Path(dry_name); apply_report = Path(apply_name)
        self.addCleanup(lambda: dry_report.unlink(missing_ok=True))
        self.addCleanup(lambda: apply_report.unlink(missing_ok=True))
        common = [
            "python3", str(SCRIPT_PATH), "--project-root", str(root),
        ]
        subprocess.run(
            common[:2] + ["dry-run"] + common[2:] + ["--report", str(dry_report)],
            check=True, capture_output=True, text=True,
        )
        subprocess.run(
            common[:2] + ["apply"] + common[2:] + [
                "--report", str(apply_report), "--no-interrupt",
            ],
            check=True, capture_output=True, text=True,
        )
        dry_warnings = json.loads(dry_report.read_text(encoding="utf-8"))["warnings"]
        apply_warnings = json.loads(apply_report.read_text(encoding="utf-8"))["warnings"]
        self.assertEqual(dry_warnings, apply_warnings)
        self.assertTrue(dry_warnings)
        self.assertEqual(
            {(item["code"], item["file"]) for item in dry_warnings},
            {(item["code"], item["file"]) for item in apply_warnings},
        )

    def test_claude_serena_removed_and_renumbered(self):
        """ut-e2e-claude：CLAUDE.md Serena 清理与规则重排。"""
        root, _report = self._run()
        claude = (root / "CLAUDE.md").read_text(encoding="utf-8")
        agents = (root / "AGENTS.md").read_text(encoding="utf-8")
        self.assertNotIn("Serena", claude)
        self.assertNotIn("serena-usage.md", claude)
        self.assertIn("### 1. 语言规则", claude)
        self.assertNotIn("### 8. Playwright", claude)  # 项目无 playwright.md
        self.assertNotIn("playwright.md", claude)
        self.assertIn(V2_START, claude)
        self.assertIn(V2_END, claude)


class TestOptionalRuleIntegrity(unittest.TestCase):
    """codex 终审 I5 / OP-01：可选规则文件+摘要均存在 → 仅检查完整性并报告，不重写。"""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.refs = Path(__file__).resolve().parents[1] / "references"
        rules = self.root / ".claude" / "rules"
        rules.mkdir(parents=True)
        self.template = (self.refs / "rules" / "code-reading.md").read_text(encoding="utf-8")
        (rules / "code-reading.md").write_text(self.template, encoding="utf-8")

    def _plan(self):
        return {
            "templates": {"rules_root": str(self.refs / "rules")},
            "decisions_map": {},
            "steps": {
                rc.STEP_RULES_FILES: {
                    "name": rc.STEP_RULES_FILES, "status": "ok",
                    "assets": [{
                        "path": ".claude/rules/code-reading.md", "action": "skip",
                        "conflict": None, "backup_needed": False, "is_l1": False,
                    }],
                },
            },
        }

    def _run(self):
        report = {"steps": []}
        rc.step_s3_rules_files(self.root, _intents(), self._plan(), report)
        s3 = next(s for s in report["steps"] if s["name"] == rc.STEP_RULES_FILES)
        return [a for a in s3["actions"] if a.get("action") == "optional-integrity"]

    def test_integrity_ok_when_rule_and_summary_present(self):
        """ut-s3-optional-integrity-ok / OP-01 + codex 终审 I5
        （规则文件+摘要均存在 → 报告完整性检查 ok，文件与摘要不重写）"""
        (self.root / "CLAUDE.md").write_text(
            "# CLAUDE.md\n\n- **大范围检索使用 CodeGraph** → 详见 `.claude/rules/code-reading.md`\n",
            encoding="utf-8",
        )
        rule_path = self.root / ".claude" / "rules" / "code-reading.md"
        entry_path = self.root / "CLAUDE.md"
        before_rule = rc.sha256_file(rule_path)
        before_entry = rc.sha256_file(entry_path)
        integrity = self._run()
        self.assertTrue(integrity)
        self.assertEqual(integrity[0]["result"], "ok")
        self.assertEqual(rc.sha256_file(rule_path), before_rule)
        self.assertEqual(rc.sha256_file(entry_path), before_entry)

    def test_integrity_summary_missing_reported(self):
        """ut-s3-optional-integrity-summary-missing / OP-01 + codex 终审 I5
        （规则文件存在但摘要缺失 → 报告 summary-missing，不重写规则文件）"""
        integrity = self._run()
        self.assertTrue(integrity)
        self.assertEqual(integrity[0]["result"], "summary-missing")


if __name__ == "__main__":
    unittest.main()
