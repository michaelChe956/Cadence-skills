## 1. B1 — 评分接线与断言 kind(防假绿前置)

- [x] 1.1 `eval/scoring/assertor.py` 增 `text_contains`/`text_lacks` 断言 kind(最终输出文本包含/不包含判定);断言器自测与离线重跑 job 语义回归
- [x] 1.2 `eval/docker/night.py` `_score_probe_text` 消费 `probe["assertions"]`:对 `text_contains`/`text_lacks` 逐条以最终输出文本判定,任一不满足即 FAIL;既有 P 组关键字分支语义不变;失败测试:构造不含锚点的输出断言 R1 判 FAIL(证明无「无条件 PASS」路径)
- [x] 1.3 单测:`eval/tests/test_probes.py`(断言 kind 注册)与 `eval/tests/test_mock_cli_phases.py` 回归全绿

## 2. B2 — 确定性断言、stage1 记录与 hook 审计

- [x] 2.1 `eval/install/assertions.py` 净新增四条断言:`rules.frontmatter`(逐文件断言 frontmatter 分桶契约)、`omp.symlinks`(软链集合==规则集合减 README 且指向正确)、`omp.agents-md`(受管两行活引用逐字一致)、`agents-md.budget`(行数≤阈值);不新增 `l0.v5`(Change A 已将 `l0.v4` 改名交付)与 `codex.inline`(既有);四条可在 mock 工程离线自测,单测覆盖正反例
- [x] 2.2 夜测 stage1 后接入:容器产物 copy_out 后调 `assert_stage1`;断言结果以 `probe_id="stage1"` 的 schema 1.0 记录落盘,任一失败判 FAIL 并进透视
- [x] 2.3 Claude 常载审计:测试项目 `.claude/settings.json` 预置 InstructionsLoaded hook(追加写 loaded.log);**stage1 完成后截断 loaded.log** 再跑探针(排除安装会话污染);审计允许清单=入口文件+用户级 `~/.claude/CLAUDE.md`+`language.md`+`README.md`,条件桶/行为路由桶/媒体触发桶出现即 FAIL;结果进 run 记录
- [x] 2.4 mock 冒烟与既有 eval 套件回归全绿

## 3. B3 — R 组探针、rollout 审计与端过滤

- [x] 3.1 `eval/probes/definitions.py` 新增 R1(索引可见,五端)/R2(正文按需,五端,omp 走 `rule://`)探针:断言 pattern 直接内联模板首标题真实文本(`## Markdown 格式规则`等,定义期取自 Change A 落地模板)。(原 R3+agents_only 已按 2026-09-10 用户裁决移除)
- [x] 3.2~3.4 (2026-09-10 用户裁决撤销:fixture 预置/rollout 审计/agents_only 过滤全部移除,相关代码与测试已删)

## 4. B4 — 透视、基线与取证

- [x] 4.1 R 组与 stage1 记录入 schema 1.0 结果流与 `eval/results/docker-night/` 既有路径;透视矩阵自动含 R 组与 stage1 行(端×探针/合计/均时轮次);`night.py` 调用命令用逗号分隔探针参数(`sys.argv[2].split(",")` 契约)
- [x] 4.2 `eval/baselines/baseline.json` 增 R 组五端 `probe_agent` 基线(不动 P 组键);基线对比覆盖 R 组
- [x] 4.3 R 组按 `CONTROL_PROBES` 同法设独立子集分组(`R_GROUP = ("R1", "R2", "R3")`),调度可仅跑 R 组
- [x] 4.4 取证:五端×(P+R) 夜测运行(命令:`python3 -m eval.docker.night <agent> R1,R2,R3` 等,逗号分隔)+ 透视输出归档;按《设计文档》§11 逐条核对 R1-R5 验收对应断言条目;README 表述同步
