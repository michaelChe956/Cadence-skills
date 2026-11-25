"""P3 工作区证据随原始轨迹保存，供离线使用相同输入判分。"""
import hashlib
import json
from pathlib import Path

from eval.install.idempotency import diff_trees, snapshot_tree


def design_paths(changes):
    return [name for name, action in changes.items()
            if name.startswith('cadence/designs/') and name.endswith('.md') and action != 'removed'
            and '..' not in Path(name).parts]


def workspace_evidence(root, pre_snapshot):
    root = Path(root).resolve()
    changes = diff_trees(pre_snapshot, snapshot_tree(root))
    documents = {}
    for name in design_paths(changes):
        path = root / name
        if path.resolve().is_relative_to(root):
            try:
                documents[name] = path.read_text(encoding='utf-8')
            except (OSError, UnicodeError):
                pass  # 保留缺失状态，由评分器报告证据不足。
    return {'changes': changes, 'documents': documents, 'project_root': str(root)}


def save_evidence(transcript, evidence):
    transcript = Path(transcript)
    payload = {'transcript_sha256': hashlib.sha256(transcript.read_bytes()).hexdigest(), **evidence}
    transcript.with_suffix(transcript.suffix + '.p3.json').write_text(
        json.dumps(payload, ensure_ascii=False), encoding='utf-8')


def load_evidence(transcript):
    transcript = Path(transcript)
    sidecar = transcript.with_suffix(transcript.suffix + '.p3.json')
    if not sidecar.is_file():
        return None
    payload = json.loads(sidecar.read_text(encoding='utf-8'))
    if not isinstance(payload, dict) or payload.get('transcript_sha256') != hashlib.sha256(transcript.read_bytes()).hexdigest():
        raise ValueError('P3 附件与原始轨迹不匹配')
    for key in ('changes', 'documents'):
        values = payload.get(key)
        if not isinstance(values, dict) or any(not isinstance(v, str) for v in values.values()):
            raise ValueError(f'P3 附件字段 {key} 无效')
    project_root = payload.get('project_root')
    if project_root is not None and not isinstance(project_root, str):
        raise ValueError('P3 附件的项目根目录无效')
    return {'changes': payload['changes'], 'documents': payload['documents'], 'project_root': project_root}
