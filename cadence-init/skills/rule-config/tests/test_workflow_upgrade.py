"""从真实初始化入口验收旧项目升级及二次发布。"""
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

SKILL = Path(__file__).resolve().parents[1]
SCRIPT = SKILL / 'scripts/rule-config.py'
OLD_CONTEXT = 'brainstorming 的确认结果必须持久化到 OpenSpec；OpenSpec 书面契约获批后才能调用 writing-plans。'
OLD_PLAN = '已存在 OpenSpec change 的多步实施必须先有位于 cadence/plans/ 的已确认 Plan；Plan 只能展开契约，不能重新定义范围、架构或验收。'
OLD_PROPOSAL = 'proposal 必须来自已经过用户确认的 brainstorming 结果。'
OLD_L1 = '4. 用户审阅 OpenSpec 契约后，下一 Skill 必须是 `writing-plans`。'


def snapshot(root):
    return {p.relative_to(root): (p.lstat().st_mtime_ns,
                                  os.readlink(p) if p.is_symlink() else p.read_bytes())
            for p in root.rglob('*') if p.is_file() or p.is_symlink()}


class WorkflowUpgradeTests(unittest.TestCase):
    def setUp(self):
        home = tempfile.TemporaryDirectory()
        self.addCleanup(home.cleanup)
        self.root = Path(home.name) / 'project'
        self.root.mkdir()
        self.report = Path(home.name) / 'report.json'

    def run_cli(self, command, expected=0):
        proc = subprocess.run([sys.executable, str(SCRIPT), command, '--project-root',
                               str(self.root), '--report', str(self.report)],
                              capture_output=True, text=True, timeout=60,
                              env={**os.environ, "HOME": str(self.report.parent)})
        self.assertEqual(proc.returncode, expected, proc.stdout + proc.stderr)
        return json.loads(self.report.read_text())

    def assert_rerun(self):
        before = snapshot(self.root)
        self.assertEqual(self.run_cli('apply')['backups'], [])
        self.assertEqual(snapshot(self.root), before)
        self.assertEqual(self.run_cli('verify')['overall'], 'healthy')

    def test_fresh_project_and_rerun(self):
        self.run_cli('apply')
        for name in ('CLAUDE.md', 'AGENTS.md'):
            self.assertEqual((self.root / name).read_text().count('routing:v6:start'), 1)
        self.assertNotIn(OLD_CONTEXT, (self.root / 'openspec/config.yaml').read_text())
        self.assert_rerun()

    def test_exact_field_scoped_migration(self):
        path = self.root / 'openspec/config.yaml'
        path.parent.mkdir()
        user_lines = ['保留项目领域上下文', OLD_CONTEXT + ' 仅适用历史部署。', ' ' + OLD_PLAN]
        old = {'schema': 'spec-driven', 'context': '\n'.join([OLD_CONTEXT, *user_lines, OLD_PLAN, OLD_CONTEXT]),
               'rules': {'proposal': [OLD_PROPOSAL, OLD_PROPOSAL + ' 项目例外'],
                         'tasks': [OLD_PROPOSAL]}, 'x-project': {'text': OLD_CONTEXT}}
        path.write_text(yaml.safe_dump(old, allow_unicode=True))
        before = snapshot(self.root)
        self.run_cli('dry-run')
        self.assertEqual(snapshot(self.root), before)
        self.run_cli('apply')
        new = yaml.safe_load(path.read_text())
        lines = new['context'].splitlines()
        self.assertNotIn(OLD_CONTEXT, lines)
        self.assertNotIn(OLD_PLAN, lines)
        self.assertEqual([s for s in lines if s in user_lines], user_lines)
        self.assertNotIn(OLD_PROPOSAL, new['rules']['proposal'])
        self.assertIn(OLD_PROPOSAL + ' 项目例外', new['rules']['proposal'])
        self.assertIn(OLD_PROPOSAL, new['rules']['tasks'])
        self.assertEqual(new['x-project'], old['x-project'])
        self.assert_rerun()

    def test_verify_detects_only_reverted_openspec_config(self):
        self.run_cli('apply')
        path = self.root / 'openspec/config.yaml'
        doc = yaml.safe_load(path.read_text())
        doc['context'] = OLD_CONTEXT + '\n项目自定义正文\n'
        doc['rules']['proposal'].append(OLD_PROPOSAL)
        doc['rules']['tasks'].append(OLD_PROPOSAL)
        doc['x-project'] = {'literal': OLD_CONTEXT}
        path.write_text(yaml.safe_dump(doc, allow_unicode=True))
        before = snapshot(self.root)
        self.assertIn('openspec/config.yaml', self.run_cli('dry-run')['planned_backups'])
        report = self.run_cli('verify', expected=1)
        self.assertEqual(report['overall'], 'drift')
        drift = [item['file'] for check in report['checks'] if check['status'] == 'drift'
                 for item in check['items']]
        self.assertEqual(drift, ['openspec/config.yaml'])
        self.assertEqual(snapshot(self.root), before)
        self.run_cli('apply')
        self.assertEqual(self.run_cli('verify')['overall'], 'healthy')
        current = yaml.safe_load(path.read_text())
        self.assertIn('项目自定义正文', current['context'].splitlines())
        self.assertNotIn(OLD_CONTEXT, current['context'].splitlines())
        self.assertNotIn(OLD_PROPOSAL, current['rules']['proposal'])
        self.assertIn(OLD_PROPOSAL, current['rules']['tasks'])
        self.assertEqual(current['x-project'], doc['x-project'])

    def upgrade_entry_and_rule(self, with_baseline):
        rules = self.root / '.claude/rules'
        rules.mkdir(parents=True)
        name = 'openspec-superpowers-workflow.md'
        old = '<!-- cadence-framework-rule:openspec-superpowers-workflow:v1 -->\n# OpenSpec 与 Superpowers 协作规则\n' + OLD_L1 + '\n'
        if not with_baseline:
            old = old.replace('v1 -->\n', 'v1 -->  \n')
        if with_baseline:
            state = self.root / 'cadence/framework-state'
            (state / 'base').mkdir(parents=True)
            digest = hashlib.sha256(old.encode()).hexdigest()
            (state / 'base' / digest).write_text(old)
            (state / 'manifest.json').write_text(json.dumps({'schema': 1, 'rules': {
                '.claude/rules/' + name: {'base_sha': digest}}}))
        user_rule = '项目覆盖：迁移申请附上工单。'
        (rules / name).write_text(old + user_rule + '\n')
        overlay = rules / ('user-' + name)
        manual = '# 合规覆盖\n\n财务项目需要财务负责人验收。\n'
        overlay.write_text(manual)
        old_gate = '| 契约获批 | `writing-plans` | Plan 写入 `cadence/plans/` |'
        toggle = '- **产物自动提交（design/plan/code）**：开启'
        intro = '# 自有入口\n\n```text\n示例第一段\n\n示例第二段\n```\n\n'
        for entry in ('CLAUDE.md', 'AGENTS.md'):
            (self.root / entry).write_text(intro + '<!-- cadence-managed:openspec-superpowers-routing:v5:start -->\n'
                + old_gate + '\n项目要求保留工单\n<!-- cadence-managed:openspec-superpowers-routing:v5:end -->\n\n## 项目配置\n\n' + toggle + '\n')
        preview = self.run_cli('dry-run')
        self.assertIn('.claude/rules/user-' + name, [a['path'] for a in preview['planned_actions']])
        self.run_cli('apply')
        for entry in ('CLAUDE.md', 'AGENTS.md'):
            text = (self.root / entry).read_text()
            self.assertNotIn(old_gate, text)
            self.assertNotIn('routing:v5:', text)
            self.assertEqual(text.count('routing:v6:start'), 1)
            self.assertEqual(text.count('项目要求保留工单'), 1)
            self.assertIn(toggle, text)
            self.assertTrue(text.startswith(intro), text[:200])
        self.assertNotIn(OLD_L1, (rules / name).read_text())
        self.assertNotIn(OLD_L1, overlay.read_text())
        self.assertIn(manual.strip(), overlay.read_text())
        self.assertIn(user_rule, overlay.read_text())
        self.assert_rerun()

    def test_upgrade_without_local_baseline(self):
        self.upgrade_entry_and_rule(False)

    def test_upgrade_with_local_baseline(self):
        self.upgrade_entry_and_rule(True)
