## Why

五端(claude code / codex / kimi code / pi / oh-my-pi)共享同一套 Cadence 规则,当前只有四端有框架支持,omp 侧存在两类极端:

1. **omp 端盲区**:omp 的 context 遮蔽机制(`.omp/AGENTS.md`=100 > `.claude/CLAUDE.md`=80 > 根=10)使 omp 会话看不到项目总述与 L0 路由;`.claude/rules/` 不在 omp rulebook 扫描范围,无 frontmatter 的规则进不了任何桶——omp 侧规则等于不存在。
2. **Claude 端反向全量强载**:`.claude/rules/*.md` 无 frontmatter → 启动时全量强载(实测 8 文件全部 session_start 载入,含 8.7KB 的 mcp-servers.md),「渐进式加载」在两端都未达成。

机制调研与实测(2026-09-09,证据:`cadence/analysis-docs/2026-09-09_调研证据_五端规则与context发现机制/`)已定案可行路径:omp 兼容层 `.agents/rules` 对文件级软链全链路支持(索引、`rule://` 正文、`agents` 过滤、容忍 Claude `paths` 字段),`.omp/AGENTS.md` 支持活 `@import`;Claude 2.1.247 惰性唯一锚点是 `paths` frontmatter。

设计文档:`cadence/designs/2026-09-09_方案设计_五端渐进式规则架构_v1.0.md`(已获批;本 change 为其 §9 切分中的 **Change A**)。

## What Changes
1. **规则模板共享 frontmatter**:8 个落地规则(10 个源模板,`code-usage`/`code-reading` 双源分化)按设计文档 §5 分桶加 `description`/`paths`/`alwaysApply` frontmatter(框架模板不设置 `agents`——不携带 agent 限定,omp 子代理默认可见全部规则;`agents:` 为可选能力字段,仅 eval 测试 fixture 使用);RF-05 权威覆盖语义不变,老项目重跑即升级。
2. **L0 路由内核升 v5 与 eval 断言层同步**:内核客户端语义行补 omp(omp 调用 skill=全文读取 `skill://`,与 pi 同类);`eval/install/assertions.py` 的 L0 标记常量、`l0.v4` 断言名、升级文案与测试 fixture 同步升 v5(不留旧断言名并行)。
3. **rule-config 新步骤 `s11_omp_bridge`**:`.agents/rules/<名>.md` 文件级相对软链集合管理(创建/修复/清理,排除 README,保留用户文件)+ `.omp/AGENTS.md` 受管两行活引用(`@../.claude/CLAUDE.md` + `@../AGENTS.md`,旧文件备份归档)+ symlink 失败降级物化副本 warning;`PRUNE_DIRS`/SKILL.md find 块同步加 `.omp`;verify 增 omp 资产断言。
4. **eval Docker 考场五端化**:`container.py`/`session.py` 增 omp(ELF 复制 + auth 最小集 `~/.omp/agent/{models.yml, config.yml}` + `omp -p` 无头);既有 P1-P8 探针对 omp 同跑;`report_matrix.py` 的 `AGENTS` 元组扩五端,omp 结果进夜测矩阵与透视。

非目标:R 组规则加载探针/确定性断言/透视基线扩展属 **Change B**(`rules-progressive-load-probes`,依赖本 change 落地);用户仓(cadence-aria/naruto)吸收不在本期范围;Windows symlink 支持仅做降级不做原生化。

## Capabilities

### New Capabilities

- `omp-client-support`: omp 作为第五客户端的规则桥接——`.agents/rules` 软链集合管理、`.omp/AGENTS.md` 受管活引用、symlink 降级、verify omp 资产断言、扫描剪枝 `.omp`。

### Modified Capabilities

- `managed-rule-lifecycle`: 规则模板增加共享 frontmatter 分桶契约(description/paths/agents/alwaysApply),落地文件与模板逐字一致语义不变。
- `progressive-context-routing`: L0 路由内核版本升 v5,Skill 调用客户端语义行补 omp(`omp 经 skill:// 全文读取`)。
- `eval-ci-matrix`: Docker 夜测考场由四端扩五端(omp 容器化/auth/P1-P8 全量探针五端同跑/透视 AGENTS 元组扩五端;omp 基线首轮建立)。
