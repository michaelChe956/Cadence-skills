"""用同一份原生记录检查宿主、容器评分入口和离线重放。"""
import json
import tempfile
import unittest
from pathlib import Path

from eval.adapters import get_adapter
from eval.docker.night import _score_probe_text
from eval.probes.definitions import get
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
            golden = []
            for name, (files, expected) in cases.items():
                with self.subTest(name=name):
                    proj = root / name
                    for path, text in files.items():
                        file = proj / path
                        file.parent.mkdir(parents=True, exist_ok=True)
                        file.write_text(text, encoding='utf-8')
                    raw = root / (name + '.jsonl')
                    raw.write_bytes((RAW_FIXTURES / f'p3-{name}.jsonl').read_bytes())
                    evidence = workspace_evidence(proj, {})
                    save_evidence(raw, evidence)
                    traj = get_adapter('claude').parse_file(raw)
                    online = score_run(name, get('P3'), traj, workspace=proj, pre_snapshot={})
                    docker = _score_probe_text('claude', 'P3', {'returncode': 0, 'transcript_path': str(raw),
                        'workflow_files': evidence['changes'], 'design_documents': evidence['documents']})
                    self.assertEqual((online['verdict'], docker['verdict']), (expected, expected), (online, docker))
                    golden.append({'agent': 'claude', 'path': raw.name, 'probe_id': 'P3', 'expect_verdict': expected})
            manifest = root / 'golden.json'
            manifest.write_text(json.dumps(golden), encoding='utf-8')
            self.assertEqual(run_rerun(root, manifest), 0)
