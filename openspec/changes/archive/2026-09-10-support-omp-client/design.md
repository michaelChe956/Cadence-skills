## Context

五端规则加载机制调研与实测已完成并固化为获批设计文档:`cadence/designs/2026-09-09_方案设计_五端渐进式规则架构_v1.0.md`(下称《设计文档》),证据目录 `cadence/analysis-docs/2026-09-09_调研证据_五端规则与context发现机制/`。本 change 为《设计文档》§9 切分的 **Change A**;Change B(`rules-progressive-load-probes`,R 组探针与透视基线)依赖本 change 落地。

约束:

- omp 18.1.14 实测:`.agents/rules` 兼容层对文件级软链全链路支持(索引/`rule://`/`agents` 过滤/`paths` 容忍);目录级软链与原生 `.omp/rules` 内软链不发现;`.omp/AGENTS.md` 支持活 `@import`(含跨目录相对路径)。
- Claude Code 2.1.247 实测:仅 `paths` 非空=条件加载,其余一律 session_start 强载;frontmatter 注入前剥离;根外软链无头不装载(本设计不依赖根外软链)。
- eval Docker 考场现行机制:`eval/docker/{container,session,night,report_matrix}.py`、`eval/install/assertions.py`、`eval/baselines/baseline.json`、tier1 CI artifacts+失败仍出透视。

## Goals / Non-Goals

**Goals:**

- 五端渐进式规则的框架落地:规则模板共享 frontmatter 分桶、L0 v5(omp 客户端语义)、`s11_omp_bridge`(软链桥 + `.omp/AGENTS.md` 受管活引用 + 降级)、verify omp 资产断言。
- eval Docker 考场五端化:omp 容器化(ELF 复制+凭据最小集)、stage1 与既有 P1-P8 对 omp 同跑、透视端维度扩五端。

**Non-Goals:**

- R 组规则加载探针、六条确定性 stage1 断言、hook 审计、透视 R 组基线(Change B)。
- 用户仓(cadence-aria/naruto)吸收:后续各自重跑 `/rule-config` 升级。
- Windows symlink 原生支持:仅降级物化+warning。

## Decisions

1. **方案 A(单一物理源+软链桥)**——《设计文档》§3:物理源保持 `.claude/rules/`(RF-05 管线不动),omp 经 `.agents/rules` 文件级软链消费;否决生成式副本(漂移面)与中性源反转(主端吃软链风险)。
2. **共享 frontmatter 契约**——§4/§5:`description`(omp 索引)+`paths`(Claude 条件)+`agents`(omp 过滤)单文件共存,各端未知字段静默忽略(实测交叉容忍);`paths: []` 不构成行为路由桶(实测仍强载),永不匹配 glob 才是。
3. **`.omp/AGENTS.md` 两行活引用**——§6.3.2:整文件受管,`@../.claude/CLAUDE.md`+`@../AGENTS.md`;CodeGraph 副本漂移归零;旧文件(含 aria 手工过渡版)备份至 `cadence/legacy/` 后替换。
4. **s11 集合语义**——§6.3.1:源=落地规则集合减 README;创建/修复/清理/幂等;非管线文件逐字保留+warning;symlink 失败降级物化+`OMP_BRIDGE_MATERIALIZED`。
5. **L0 直升 v5**——§6.2:v4 尚未发布到用户仓,直接以 v5 首发;omp 归 pi 同类(`skill://` 全文读取=调用)。
6. **考场五端化随框架同 change**——§6.6 依赖注记:omp 在无规则桥的项目上跑 P1-P8 必然全盲失败,故考场 omp 化必须与框架改造同 change(A3 在 A1 后执行)。

## Risks / Trade-offs

| 风险 | 缓解(详见《设计文档》§10) |
|---|---|
| Claude `paths` 语义未来变化 | 依赖面仅 `paths` 非空;Change B 探针+hook 审计可重跑 |
| omp 升级改 rulebook 扫描/软链行为 | 验收锁 18.1.14;夜测回归可重跑 |
| omp 容器化未知面 | A2 首任务容器内 `omp -p` 冒烟;失败降级四端+宿主旁路取证并透视标注 |
| Windows checkout 无 symlink | s11 降级物化副本+warning |

## Migration Plan

- 老项目(含 aria 手工 `.omp/AGENTS.md` 过渡版):重跑 `/rule-config` 即完成升级——模板 drift 权威覆盖自动加 frontmatter,s11 归档旧 `.omp/AGENTS.md` 后替换,`cadence/legacy/` 留档可回滚。
- eval 侧:omp 列基线首轮建立,允许低于四端历史基线且透视可见。

## Open Questions

无——《设计文档》已获批,机制断言全部有实测或官方文档背书;omp 容器首启状态行为(可写目录需求)留 A2 冒烟时验证,不阻塞契约。
