## Why

《方案设计:多 CLI 渐进式规则架构》(`cadence/designs/2026-09-09_方案设计_五端渐进式规则架构_v1.0.md`,已获批)要求 R1-R5 验收可观察、可回归:

1. 渐进式加载的关键承诺(「索引可见/正文按需可达/强载总量受控」)目前没有任何自动化验证——Change A(`support-omp-client`)只保证产物落地正确,不证明五端会话实际按渐进方式消费规则。
2. 2026-09-02 四端探针实验已证明「规则进上下文」需要实证而非假设;且 ClaudeResearch 实测「模型自报不可靠」,强载审计必须走确定性通道(hook 落盘/文件断言),不能依赖模型复述。
3. 结果需要进入既有 Docker 夜测透视(`report_matrix.py` 端×探针矩阵+基线对比),与 P1-P8 同流观测,否则规则加载回归不可持续。
4. Docker 夜测现有评分是 P 组关键字硬编码分支,不读探针断言——R 组接入前必须先打通「评分消费断言 spec」的接线,否则新增探针无条件假绿。

## What Changes

1. **Docker 夜测评分接线**(`eval/docker/night.py`):`_score_probe_text` 消费 `probe["assertions"]`(`text_contains`/`text_lacks` 对最终输出判定);既有 P 组评分语义不变;含失败测试证明无假绿路径。
2. **确定性 stage1 断言**(`eval/install/assertions.py` 净新增四条):`rules.frontmatter`、`omp.symlinks`、`omp.agents-md`、`agents-md.budget`;`l0.v5` 由 Change A 将既有 `l0.v4` 改名交付、`codex.inline` 既有——本 change 仅消费;断言结果以 schema 1.0 记录(`probe_id="stage1"`)落盘并入透视。
3. **R 组行为探针**(`eval/probes/definitions.py` 新增 R1/R2):R1 索引可见(五端)、R2 正文按需(五端,omp 走 `rule://`);断言 kind 扩 `text_contains`/`text_lacks`(`eval/scoring/assertor.py`)。(原 R3 agent 过滤探针与 scout fixture/rollout 审计已按 2026-09-10 用户裁决撤销——`agents:` 为 omp 原生能力,由用户在项目规则中自行添加,框架与 eval 均不预置、不测试。)
4. **Claude 常载审计走确定性通道**:测试项目 `.claude/settings.json` 预置 InstructionsLoaded hook 写 loaded.log;stage1 后截断日志排除安装会话污染;允许清单含入口+用户级 `~/.claude/CLAUDE.md`+常驻桶+目录页。
5. **透视与基线扩展**:R 组入既有结果流与端×探针矩阵;`eval/baselines/baseline.json` 增 R 组五端键(不动 P 组);R 组按 CONTROL 子集机制独立分组。

依赖:Change A(`support-omp-client`)——断言锚定其落地产物,omp 探针需要其五端考场与 `l0.v5` 改名。

## Capabilities

### New Capabilities

- `rules-load-probes`: 规则渐进加载的五端验证——确定性产物断言、R 组行为探针(R1 索引/R2 正文/R3 agent 过滤含 rollout 审计)、Claude hook 常载审计、R 组基线。

### Modified Capabilities

- `eval-ci-matrix`: Docker 夜测评分消费探针断言 spec(消除「无断言分支即 PASS」路径);stage1 确定性断言落盘为 schema 1.0 记录并入透视。
