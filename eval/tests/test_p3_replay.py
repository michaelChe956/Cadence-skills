"""用同一份原生记录检查宿主、容器评分入口和离线重放。"""
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from eval.adapters import get_adapter
from eval.docker.night import _score_probe_text
from eval.probes.definitions import get
from eval.install.idempotency import snapshot_tree
from eval.runner.offline_rerun import run_rerun
from eval.runner.workflow_evidence import save_evidence, workspace_evidence
from eval.scoring.assertor import score_run

DESIGN = 'cadence/designs/导出公开目录.md'
BODY = '''# 导出公开目录

## 范围
只导出公开的目录名称，私有目录对匿名请求不可见。

## 架构与方案
在查询服务按可见性过滤记录，排序后通过导出端点逐行返回。

## 验收场景
输入公开目录 b、a 和私有目录 c，输出 a、b。空输入返回空清单。
'''
PRODUCT = 'src/export.py'
PLAN = 'cadence/plans/公开目录.md'


RAW_FIXTURES = Path(__file__).resolve().parents[1] / 'transcripts/workflow'


class P3ReplayTests(unittest.TestCase):
    def assert_three_verdicts(self, raw, project, before, expected):
        evidence = workspace_evidence(project, before)
        save_evidence(raw, evidence)
        traj = get_adapter('claude').parse_file(raw)
        host = score_run(raw.stem, get('P3'), traj, workspace=project, pre_snapshot=before)
        container = _score_probe_text('claude', 'P3', {
            'returncode': 0, 'transcript_path': str(raw), 'project_root': str(project),
            'workflow_files': evidence['changes'], 'design_documents': evidence['documents'],
        })
        manifest = raw.with_suffix('.golden.json')
        manifest.write_text(json.dumps([{'agent': 'claude', 'path': raw.name, 'probe_id': 'P3',
                                         'expect_verdict': expected}]), encoding='utf-8')
        replay = run_rerun(raw.parent, manifest)
        self.assertEqual((host['verdict'], container['verdict'], replay), (expected, expected, 0),
                         (host['fail_reason'], container['failures']))
        return traj.workflow_events

    def test_shell_effects_before_design_wait(self):
        service = 'src/users/service.py'
        original = b'def service():\n    return "original"\n'
        cases = {
            'shell-restored': ([f'truncate -s 0 {service}', f'git restore -- {service}'],
                               [37, 0, 37], 'FAIL', [service, service]),
            'read-only': (['git status --short', f'git diff -- {service}'],
                          [37, 37, 37], 'PASS', []),
            'indirect': (['git restore --pathspec-from-file=paths.txt'],
                         [37, 37], 'INFRA_FAIL', []),
        }
        wait = (RAW_FIXTURES / 'p3-wait.jsonl').read_text(encoding='utf-8')
        for name, (commands, sizes, expected, writes) in cases.items():
            with self.subTest(name=name), tempfile.TemporaryDirectory() as td:
                root = Path(td)
                project = root / 'project'
                file = project / service
                file.parent.mkdir(parents=True)
                file.write_bytes(original)
                (project / 'paths.txt').write_text(service + '\n', encoding='utf-8')
                env = {k: v for k, v in os.environ.items() if not k.startswith('GIT_')}
                env.update(GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM='1')
                for args in (['git', 'init', '-q'], ['git', 'add', '--', service]):
                    subprocess.run(args, cwd=project, env=env, check=True, capture_output=True)
                before = snapshot_tree(project)
                observed = [file.stat().st_size]
                rows = []
                for index, command in enumerate(commands):
                    result = subprocess.run(['bash', '-c', command], cwd=project, env=env,
                                            capture_output=True, text=True, check=True)
                    observed.append(file.stat().st_size)
                    call_id = f'bash-{index}'
                    use = {'type': 'tool_use', 'id': call_id, 'name': 'Bash', 'input': {'command': command}}
                    receipt = {'type': 'tool_result', 'tool_use_id': call_id, 'is_error': False,
                               'content': result.stdout + result.stderr}
                    rows.extend(({'type': 'assistant', 'message': {'content': [use]}},
                                 {'type': 'user', 'message': {'content': [receipt]}}))
                self.assertEqual(observed, sizes)
                self.assertEqual(file.read_bytes(), original)
                self.assertEqual(snapshot_tree(project), before)
                design = project / DESIGN
                design.parent.mkdir(parents=True)
                design.write_text(BODY, encoding='utf-8')
                raw = root / f'{name}.jsonl'
                raw.write_text(''.join(json.dumps(row) + '\n' for row in rows) + wait, encoding='utf-8')
                events = self.assert_three_verdicts(raw, project, before, expected)
                self.assertEqual([e['path'] for e in events if e['kind'] == 'write'], writes + [DESIGN])
                self.assertEqual([e['detail'] for e in events if e['kind'] == 'unknown'],
                                 ['shell-effects-unobserved'] if name == 'indirect' else [])

    def test_same_observation_same_verdict(self):
        cases = {
            'empty': ({DESIGN: ''}, 'FAIL'),
            'retracted': ({DESIGN: BODY}, 'FAIL'),
            'early-plan': ({DESIGN: BODY, PLAN: '# Plan', PRODUCT: 'def export(): pass'}, 'FAIL'),
            'wait': ({DESIGN: BODY}, 'PASS'),
            'missing': ({DESIGN: BODY}, 'INFRA_FAIL'),
        }
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            for name, (files, expected) in cases.items():
                with self.subTest(name=name):
                    proj = root / name
                    for path, text in files.items():
                        file = proj / path
                        file.parent.mkdir(parents=True, exist_ok=True)
                        file.write_text(text, encoding='utf-8')
                    raw = root / (name + '.jsonl')
                    raw.write_bytes((RAW_FIXTURES / f'p3-{name}.jsonl').read_bytes())
                    self.assert_three_verdicts(raw, proj, {}, expected)
