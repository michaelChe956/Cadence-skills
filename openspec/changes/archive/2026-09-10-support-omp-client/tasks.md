- [x] 1.1 为 `references/rules/` 下 10 个源模板(8 个落地规则;`code-usage`/`code-reading` 双源分化)按《设计文档》§5 分桶添加 frontmatter(language 常驻桶;双源按项目类型分化 glob(`SOURCE_EXTS` 口径 + tsx/jsx 增补);document-storage/markdown-format/playwright 条件桶;mcp-servers 媒体触发桶;openspec-superpowers-workflow 行为路由桶(不设 `agents`——框架不携带 agent 限定);永不匹配 glob 附意图注释);更新模板快照测试
- [x] 1.2 L0 内核升 v5:`agent-routing-kernel.md` 客户端语义行补 omp(`Codex/pi/omp … omp 经 skill://`),v4 归档入 `l0-history/`;**同步 eval 断言层**:`eval/install/assertions.py` 的 `L0_BEGIN` 标记常量升 v5(或改为由版本构造)、~352 行正则硬编码的 `v4:end` 结束标记与 ~3 行 docstring 同步、断言名 `l0.v4` 改名 `l0.v5`、`v3.upgraded` 升级文案适配 v3→v5、`eval/tests/test_stage1_assertions.py` fixture 内嵌标记同步升 v5;`references/merge-semantics.md` §4 L0 全节版本表述 v2→v5(~113「当前 L0 版本为 v2」及 L0-01/L0-04 行)
- [x] 1.3 实现 `s11_omp_bridge` 步骤:`.agents/rules/` 文件级相对软链集合管理(创建/修复/清理/幂等,排除 README,非管线文件保留+warning)+ `.omp/AGENTS.md` 整文件受管(两行活引用,旧文件备份归档后替换)+ symlink 失败降级物化副本与 `OMP_BRIDGE_MATERIALIZED` warning;接入 STEP_ORDER 与 dry-run/apply 两阶段
- [x] 1.4 `PRUNE_DIRS` 与 SKILL.md 有界扫描 find 块同步加 `.omp`(双向断言延续);`merge-semantics.md` 新增 OR-01~07 表(创建/修复/清理/用户文件保留/降级/受管活引用/同名普通文件归档替换);SKILL.md 编排与 warnings code 更新;`skill-clause-map.md` 对账
- [x] 1.5 `verify` 子命令增 omp 资产断言(软链集合一致、`.omp/AGENTS.md` 与受管内容一致)
- [x] 1.6 单测:s11 创建/修复/清理/幂等/降级/用户文件保留;frontmatter 分桶快照;L0 v5 升级路径(v4/v3 及更早 → v5);`verify-managed-lifecycle.sh` 端到端断言
- [x] 1.7 回归:rule-config 既有全部测试(`tests/test_rule_config.py`、`tests/verify-managed-lifecycle.sh`)全绿

## 2. A2 — omp 考场化(容器/凭据/无头冒烟)

- [x] 2.1 `eval/docker/container.py`:`cli_map`/`_copy_auth` 增 omp(ELF 复制同 kimi 模式;auth 最小集 `~/.omp/agent/{models.yml, config.yml}`),容器内 `omp -p` 无头冒烟通过(含首启状态写入行为验证)
- [x] 2.2 `eval/docker/session.py`:`_cli_command` 增 `"omp": "omp -p"`、`_PERMISSION_FLAG["omp"]=""`;确认 stage1 四命令流水线与探针会话对 omp 可跑

## 3. A3 — 既有测试五端化与透视

- [x] 3.1 夜测矩阵对 omp 跑 stage1 + P1-P8 全量探针(依赖 1.x 落地后启用);结果落 `eval/results/docker-night/` 既有路径
- [x] 3.2 `eval/docker/report_matrix.py`:`AGENTS` 元组扩五端(omp 列入端×探针矩阵/合计行/均时轮次);omp 基线首轮建立并允许低于四端基线
- [x] 3.3 omp 考场降级路径:容器化或无头失败时不阻塞四端;omp 端 run 记录(schema 1.0 JSON)落盘并携带 `degrade` 字段说明原因,`report_matrix.py` 检测该字段并在透视输出打印降级注记
- [x] 3.4 取证:五端夜测运行记录 + `python3 eval/docker/report_matrix.py` 透视输出归档;README 相关表述同步(四端→五端)
