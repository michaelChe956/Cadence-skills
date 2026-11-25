"""连续升级时 L1 历史识别与 overlay 旧框架残留清理（回归）。

覆盖两项已复现缺陷：
  * 旧 CLI 连续升级把历史框架行（含人工确认门槛）误写入用户 overlay 自动区；
  * 无本地基线时用历史行全局并集剔除，误删用户追加章节正文。
旧 CLI 从本仓 ``462e56cf`` 归档到临时位置运行；报告文件始终落在项目根之外。
"""

import hashlib
import importlib.util
import io
import json
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
REPO = SKILL.parents[2]
SCRIPT = SKILL / 'scripts/rule-config.py'
HISTORY = SKILL / 'references/rules/l1-history'
L1_NAME = 'openspec-superpowers-workflow.md'
L1_REL = f'.claude/rules/{L1_NAME}'
OVERLAY_REL = f'.claude/rules/user-{L1_NAME}'
OLD_COMMIT = '462e56cf'

EF3F = (HISTORY / 'workflow-v1-ef3fb2d6.md').read_text(encoding='utf-8')
F681 = (HISTORY / 'workflow-v1-f681c587.md').read_text(encoding='utf-8')
OLD_L1 = '4. 用户审阅 OpenSpec 契约后，下一 Skill 必须是 `writing-plans`。'
OLD_GATE = '用户审阅 OpenSpec 书面契约后，下一 Skill 必须是 `writing-plans`。'
MANUAL = '# 合规覆盖\n\n财务项目需要财务负责人验收。\n'
USER_APPENDIX = '\n## 九、用户补充\n\n- 用户当前明确指令与既有契约冲突时停止，先更新权威产物。\n'


def snapshot(root):
    return {
        p.relative_to(root): (
            p.lstat().st_mtime_ns,
            os.readlink(p) if p.is_symlink() else p.read_bytes(),
        )
        for p in root.rglob('*')
        if p.is_file() or p.is_symlink()
    }


def extract_old_skill(dest):
    """从本仓 462e56cf 归档 rule-config skill 到临时目录并校验解包。"""
    if shutil.which('git') is None:
        raise unittest.SkipTest('git 不可用，无法归档历史 CLI')
    proc = subprocess.run(
        ['git', '-C', str(REPO), 'archive', '--format=tar',
         OLD_COMMIT, 'cadence-init/skills/rule-config'],
        capture_output=True,
    )
    if proc.returncode != 0:
        raise unittest.SkipTest(
            f'无法归档 {OLD_COMMIT}：{proc.stderr.decode("utf-8", "replace")}'
        )
    dest.mkdir(parents=True, exist_ok=True)
    with tarfile.open(fileobj=io.BytesIO(proc.stdout)) as archive:
        try:
            archive.extractall(dest, filter='data')
        except TypeError:  # Python < 3.12 无 filter 参数
            archive.extractall(dest)
    skill = dest / 'cadence-init/skills/rule-config'
    script = skill / 'scripts/rule-config.py'
    template = skill / 'references/rules' / L1_NAME
    if not script.is_file() or not template.is_file():
        raise AssertionError('历史 skill 解包不完整')
    # 解包校验：462e56cf 的真实 L1 模板就是历史 f681 正文。
    if template.read_text(encoding='utf-8') != F681:
        raise AssertionError('462e56cf 的 L1 模板与历史 f681 正文不一致')
    return script


def record_base(root, rel, text):
    """写入与 apply 等价的本地基线，模拟“主规则无漂移但 overlay 已污染”。"""
    state = root / 'cadence/framework-state'
    digest = hashlib.sha256(text.encode('utf-8')).hexdigest()
    (state / 'base').mkdir(parents=True, exist_ok=True)
    (state / 'base' / digest).write_text(text, encoding='utf-8')
    (state / 'manifest.json').write_text(
        json.dumps({'schema': 1, 'rules': {rel: {'base_sha': digest}}}),
        encoding='utf-8',
    )


class OverlayHistoryCliTests(unittest.TestCase):
    def setUp(self):
        home = tempfile.TemporaryDirectory()
        self.addCleanup(home.cleanup)
        self.home = Path(home.name)
        self.root = self.home / 'project'
        self.root.mkdir()
        self.report = self.home / 'report.json'  # 项目外报告

    def run_cli(self, script, command, root=None):
        proc = subprocess.run(
            [sys.executable, str(script), command,
             '--project-root', str(root or self.root),
             '--report', str(self.report)],
            capture_output=True, text=True, timeout=120,
            env={**os.environ, 'HOME': str(self.home)},
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        return json.loads(self.report.read_text(encoding='utf-8'))

    def assert_rerun(self):
        before = snapshot(self.root)
        self.assertEqual(self.run_cli(SCRIPT, 'apply').get('backups'), [])
        self.assertEqual(snapshot(self.root), before)

    def test_sequential_upgrade_removes_old_framework_gate(self):
        old_script = extract_old_skill(self.home / 'old-skill')
        rules = self.root / '.claude/rules'
        rules.mkdir(parents=True)
        addition = '\n## 用户新增\n\n项目范围包括清算单据。\n'
        (rules / L1_NAME).write_text(EF3F + addition, encoding='utf-8')
        (rules / f'user-{L1_NAME}').write_text(MANUAL, encoding='utf-8')

        self.run_cli(old_script, 'apply')
        polluted = (rules / f'user-{L1_NAME}').read_text(encoding='utf-8')
        self.assertIn(OLD_GATE, polluted)  # 复现：旧框架门槛被列为用户文本

        # 同文出现在手写区和代码示例中时保留原始换行与尾随空格。
        suffix = ('\r\n# 项目附录\r\n```text\r\n' + OLD_GATE + '  \r\n```\r\n').encode()
        target = rules / f'user-{L1_NAME}'
        marker = b'<!-- cadence-overlay:extracted:start'
        original = target.read_bytes()
        start = original.index(marker)
        # 用户在两个真实标记前粘贴了整段示例，连旧批次正文也相同。
        example = b'```markdown\n' + original[start:] + b'```\n'
        target.write_bytes((original[:start] + example + original[start:]).replace(b'\n', b'\r\n') + suffix)
        original_prefix = target.read_bytes().rsplit(marker, 1)[0]
        before = snapshot(self.root)
        preview = self.run_cli(SCRIPT, 'dry-run')
        self.assertEqual(snapshot(self.root), before)  # 预演零写入
        planned = {(a['path'], a['action']) for a in preview['planned_actions']}
        self.assertIn((OVERLAY_REL, 'overlay-extracted'), planned)
        self.assertIn(OVERLAY_REL, preview['planned_backups'])

        self.run_cli(SCRIPT, 'apply')
        cleaned = (rules / f'user-{L1_NAME}').read_text(encoding='utf-8')
        auto = cleaned.rsplit('<!-- cadence-overlay:extracted:start', 1)[1].split('<!-- cadence-overlay:extracted:end -->', 1)[0]
        self.assertNotIn(OLD_GATE, auto)
        self.assertIn('项目范围包括清算单据。', auto)
        self.assertNotIn('OpenSpec 契约后', auto)
        self.assertTrue(target.read_bytes().startswith(original_prefix))
        self.assertTrue(target.read_bytes().endswith(suffix))
        self.assertTrue(cleaned.startswith(MANUAL), cleaned[:120])
        self.assertIn(MANUAL.strip(), cleaned)
        self.assertEqual(
            (rules / L1_NAME).read_text(encoding='utf-8'),
            (SKILL / 'references/rules' / L1_NAME).read_text(encoding='utf-8'),
        )
        self.assert_rerun()

    def test_unknown_baseline_keeps_user_appendix_body(self):
        rules = self.root / '.claude/rules'
        rules.mkdir(parents=True)
        (rules / L1_NAME).write_text(F681 + USER_APPENDIX, encoding='utf-8')

        self.run_cli(SCRIPT, 'apply')
        overlay = (rules / f'user-{L1_NAME}').read_text(encoding='utf-8')
        self.assertIn('## 九、用户补充', overlay)
        self.assertIn(
            '- 用户当前明确指令与既有契约冲突时停止，先更新权威产物。', overlay,
        )
        self.assertIn('## 用户新增', overlay)
        # 当前项目所用旧模板已退役为 v2，且旧框架行未混入用户区。
        main = (rules / L1_NAME).read_text(encoding='utf-8')
        self.assertIn('openspec-superpowers-workflow:v2 -->', main)
        self.assertNotIn(OLD_L1, overlay)
        self.assert_rerun()

    def test_no_main_drift_still_cleans_polluted_overlay(self):
        old_script = extract_old_skill(self.home / 'old-skill')
        seed = self.home / 'seed'
        seed_rules = seed / '.claude/rules'
        seed_rules.mkdir(parents=True)
        (seed_rules / L1_NAME).write_text(EF3F, encoding='utf-8')
        (seed_rules / f'user-{L1_NAME}').write_text(MANUAL, encoding='utf-8')
        self.run_cli(old_script, 'apply', root=seed)

        rules = self.root / '.claude/rules'
        rules.mkdir(parents=True)
        template = (SKILL / 'references/rules' / L1_NAME).read_text(encoding='utf-8')
        (rules / L1_NAME).write_text(template, encoding='utf-8')
        (rules / f'user-{L1_NAME}').write_text(
            (seed_rules / f'user-{L1_NAME}').read_text(encoding='utf-8'),
            encoding='utf-8',
        )
        record_base(self.root, L1_REL, template)

        before = snapshot(self.root)
        preview = self.run_cli(SCRIPT, 'dry-run')
        self.assertEqual(snapshot(self.root), before)
        planned = {(a['path'], a['action']) for a in preview['planned_actions']}
        self.assertIn((OVERLAY_REL, 'overlay-cleaned'), planned)
        self.assertIn(OVERLAY_REL, preview['planned_backups'])

        self.run_cli(SCRIPT, 'apply')
        overlay = (rules / f'user-{L1_NAME}').read_text(encoding='utf-8')
        self.assertNotIn(OLD_GATE, overlay)
        self.assertIn(MANUAL.strip(), overlay)
        self.assert_rerun()


def load_rule_config():
    spec = importlib.util.spec_from_file_location(
        'rule_config_overlay_history', SCRIPT,
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class HistoricalRecognitionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rc = load_rule_config()
        cls.template = (SKILL / 'references/rules' / L1_NAME).read_text(
            encoding='utf-8',
        )

    def test_known_v2_baseline_extracts_nothing(self):
        path = HISTORY / 'workflow-v2-f6a0d281.md'
        old_v2 = path.read_text(encoding='utf-8')
        base = self.rc._historical_l1_base(old_v2, self.template)
        self.assertEqual(base, old_v2)
        _body, changed = self.rc.cadence_state.build_overlay_body(
            L1_NAME, base, old_v2, 'historical-v2',
        )
        self.assertFalse(changed)  # 审后第 41 行修订属框架升级，不进入用户覆盖

    def test_user_appendix_keeps_heading_and_body(self):
        existing = F681 + USER_APPENDIX
        base = self.rc._historical_l1_base(existing, self.template)
        self.assertIsNotNone(base)
        body, changed = self.rc.cadence_state.build_overlay_body(
            L1_NAME, base, existing, 'historical-v1',
        )
        self.assertTrue(changed)
        self.assertIn('## 九、用户补充', body)
        self.assertIn('用户当前明确指令与既有契约冲突时停止', body)

    def test_duplicate_historical_line_in_user_section_is_kept(self):
        existing = F681 + USER_APPENDIX + f'- {OLD_L1}\n'
        base = self.rc._historical_l1_base(existing, self.template)
        self.assertIsNotNone(base)
        body, _changed = self.rc.cadence_state.build_overlay_body(
            L1_NAME, base, existing, 'historical-v1',
        )
        self.assertEqual(body.count(OLD_L1), 1)
        self.assertIn('## 九、用户补充', body)

    def test_current_template_with_user_line_is_not_claimed(self):
        existing = self.template + '\nUSER-ONLY-LINE\n'
        self.assertIsNone(self.rc._historical_l1_base(existing, self.template))

    def test_renamed_heading_keeps_framework_body_attributed(self):
        existing = F681.replace('## 二、标准流程', '## 二、财务项目交付的标准流程')
        existing = existing.replace('1. 任何任务先调用', '1. 财务任务立项后先调用')
        base = self.rc._historical_l1_base(existing, self.template)
        body, _ = self.rc.cadence_state.build_overlay_body(L1_NAME, base, existing, 'historical-v1')
        self.assertIn('财务任务立项后先调用', body)
        self.assertIn('财务项目交付的标准流程', body)
        self.assertNotIn(OLD_L1, body)

    def test_abbreviated_old_with_user_rule_claims_only_framework(self):
        existing = (
            self.rc.L1_V1_MARKER
            + '\n# OpenSpec 与 Superpowers 协作规则\n'
            + OLD_L1 + '\n项目覆盖：迁移申请附上工单。\n'
        )
        base = self.rc._historical_l1_base(existing, self.template)
        self.assertIsNotNone(base)
        self.assertIn(OLD_L1, base)
        self.assertNotIn('项目覆盖：迁移申请附上工单。', base)


if __name__ == '__main__':
    unittest.main()
