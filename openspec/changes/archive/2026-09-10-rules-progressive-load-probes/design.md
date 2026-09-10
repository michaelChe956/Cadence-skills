## Context

依赖 Change A(`support-omp-client`)已落地:规则 frontmatter 分桶、`.agents/rules` 软链桥、`.omp/AGENTS.md` 受管活引用、L0 v5(含 eval 断言层 `l0.v4`→`l0.v5` 改名)、omp 五端考场与 P1-P8 五端化。本 change 在其上加「规则渐进加载」的验证层,承接《设计文档》(`cadence/designs/2026-09-09_方案设计_五端渐进式规则架构_v1.0.md`)§6.6.2-§6.6.4 与 §8/§11。

现行 eval 机制关键事实(oracle 审核已核对):`eval/install/assertions.py` 的 `assert_stage1` 断言表;`eval/probes/definitions.py` 探针七字段;`eval/scoring/assertor.py` kind 分派(host runner 与 offline_rerun 消费);**`eval/docker/night.py` 的 `_score_probe_text` 是 P 组关键字硬编码分支,不读 `probe["assertions"]`**——docker 夜测是 omp 唯一可跑通道(host adapters 无 omp),评分接线是本 change 前置;`night.py __main__` 只消费单个逗号分隔探针参数;`report_matrix.py` 端×探针透视+`baseline.json` 基线对比。

## Goals / Non-Goals

**Goals:**

- Docker 评分消费探针断言(防假绿);四条净新增确定性断言;R1/R2/R3 探针(含 rollout 确定性审计)与 `text_contains`/`text_lacks` kind;Claude hook 常载审计(排除安装会话污染);stage1 断言落盘入透视;R 组基线与独立分组。

**Non-Goals:**

- 五端考场与 omp 容器化、`l0.v5`/`codex.inline` 断言本体(Change A 交付)。
- docker 通道的探针变体轮换(P 组现状为首变体内联,R 组与之一致;轮换属 host runner 机制,不在本期能力边界)。
- scout 子代理可见性的正向探针(omp 无 headless 子代理会话入口;「默认无 `agents` 字段=全 agent 可见」由 frontmatter 契约保证,后续入口:omp 若提供 agent 会话 CLI 或子代理 transcript 落盘)。
- 规则内容修改(模板正文不变)。

## Decisions

1. **确定性优先**——凡能用文件断言/hook 落盘/rollout grep 证明的,不用模型行为;模型探针仅承担「索引引述」「正文读取」两类正向行为。模型负向自报(「我没看到 X」)不作断言依据。
(已撤销)原 2. **R3 负向腿走会话 rollout 审计(确定性)**——实测通道(2026-09-09,本机 omp 18.1.14):`~/.omp/agent/sessions/<项目slug>/<时间戳>.jsonl` 的**系统提示记录**(首条/`role=system`)完整含 `<domain-rules>` 索引行;在该记录范围内断言:`agents: [scout]` fixture 索引条目 0 命中、fixture 正文独有 marker 0 命中(marker 取正文独有串,MUST NOT 取首标题)。预置 fixture 规则 `.claude/rules/scout-only-fixture.md`(带永不匹配 glob+`agents: [scout]`,正文含唯一 marker,仅 omp 容器注入)随 stage1 自动入桥接;审计范围限定系统提示记录,正向腿 `rule://` 读取进入工具结果/助手消息后不污染本审计;不经模型。
3. **评分接线先于探针**——R 组接入前先改 `_score_probe_text` 消费 `assertions`,失败测试证明「输出不含锚点必 FAIL」;P 组既有分支保留(语义不变)。
4. **stage1 断言落盘为 `probe_id="stage1"` 的 schema 1.0 记录**——透视自然出现 stage1 行,不建平行报告通道。
5. **marker 锚定正文首标题**——各模板首标题当下即可确定(`## 代码使用规则`、`## Markdown 格式规则`、`# OpenSpec 与 Superpowers 协作规则` 等),定义期直接内联真实文本,首轮夜测仅复核不回填。
(原 Decision 6 R3 端过滤已随 2026-09-10 用户裁决移除。)

## Risks / Trade-offs

| 风险 | 缓解 |
|---|---|
| omp rollout 文件位置/格式随版本变化 | 审计函数按「项目 slug 目录下最新 .jsonl」定位;omp 升级重跑校准;R3 正向腿不依赖 rollout |
| omp 索引行格式变化致 R1 误报 | 断言锚定规则名+description 子串,不锚定整行格式 |
| Claude `paths` 触发依赖探针 prompt 是否触达匹配路径 | R1/R2 不断言条件注入本身;条件注入行为由 hook 审计在触发场景任务中观测(非本期硬门槛) |
| R 组增加夜测时长 | 独立子集分组;透视含轮次/均时可观测成本 |

## Migration Plan

- 全部为 eval 侧新增,无用户仓动作;`baseline.json` 新增 R 组条目不触达既有 P 组基线键。

## Open Questions

无——断言与探针契约由 Change A 落地产物与《设计文档》§5/§8 完全确定;rollout 审计通道已实测。
