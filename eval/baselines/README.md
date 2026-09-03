# 基线治理

- 基线文件：`baseline.json`（仅本目录；`schema_version` 与结果契约同源，当前 1.0）。
- 生效条件：**仅维护者显式 git 提交后生效**；夜间运行只对比，绝不改写基线。
- 更新流程：`python3 -m eval.runner.cli baseline --base <夜跑基目录> --out eval/baselines/baseline.candidate.json` → 人工审阅 → 复制为 `baseline.json` 并提交。
- 主版本不匹配的基线不参与 diff，报告显式标注“基线 schema 不兼容，本次不比对”。
- `report` 命令只读取基线并写入滚动 7 夜报告，任何新结果都不会覆盖基线文件。
