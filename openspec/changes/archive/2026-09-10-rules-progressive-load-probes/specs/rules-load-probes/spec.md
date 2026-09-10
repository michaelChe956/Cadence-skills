# rules-load-probes Specification(Change B delta:新增能力)

## ADDED Requirements

### Requirement: stage1 后必须执行规则资产确定性断言

夜测 stage1(安装流水线)完成后,系统 MUST 对测试项目执行以下确定性断言(不依赖模型行为):

- `omp.symlinks`:`.agents/rules/` 软链集合==规则文件集合减 README,且指向正确目标;
- `rules.frontmatter`:落地 `.claude/rules/*.md` 逐文件断言 frontmatter 分桶契约(常驻/条件/行为路由/媒体触发桶的字段组合与 glob);R 组 fixture 规则(测试注入)仅断言 `description` 在场,豁免桶组合校验;
- `agents-md.budget`:AGENTS.md 行数不超过预算阈值;
- `l0.v5`(断言名由 Change A 将既有 `l0.v4` 改名交付)与 `codex.inline`(既有断言)MUST 在场且通过——本能力不重复实现,仅消费。

断言定义与实现 MUST 可离线(mock 工程上)自测。

#### Scenario: 软链缺失导致 stage1 断言失败

- **WHEN** 测试项目的 `.agents/rules/` 缺少一个应有软链
- **THEN** `omp.symlinks` 断言失败,stage1 结果为 FAIL,夜测记录与透视可见失败条目

### Requirement: R 组探针必须验证渐进加载两要素

夜测 MUST 含两个规则加载探针,每个探针使用全新会话:

- **R1 索引可见**(五端):要求逐字引用上下文中的规则索引或强制规则指针,断言输出含锚点(omp 为 `<domain-rules>` 索引行;Claude 为入口指针节;Codex/Kimi/pi 为 AGENTS.md 指针);
- **R2 正文按需**(五端):要求读取指定规则正文并逐字引用其首个标题行,断言正结果;omp 端经 `rule://<名>` 读取;
- **agents 限定**(2026-09-10 用户裁决):`agents:` 为 omp 原生可选字段——由用户在项目规则中自行添加、随时调整,框架模板与 eval 均 MUST NOT 预置或测试(原始 R3 需求的机器验收随之撤销;框架保证仅剩「不阻挡」——规则经软链桥字节透传,用户自行添加的 `agents:` 对 omp 原样生效)。
#### Scenario: omp 索引可见且正文按需可达

- **WHEN** R1/R2 探针在 omp 会话运行
- **THEN** 输出可逐字引用索引行;`rule://` 读取得到规则正文首标题行

### Requirement: Claude 常载审计必须走确定性通道

Claude 端「强载总量受控」MUST NOT 依赖模型自报;测试项目 MUST 在其 `.claude/settings.json` 预置 InstructionsLoaded hook 将装载事件追加落盘(loaded.log),且 MUST 在 stage1 完成后截断该日志再运行探针(排除安装会话污染,其中部分会话先于规则落地)。夜测读取该文件断言 session_start 常载清单仅含:入口文件(CLAUDE.md、`.claude/CLAUDE.md`)、用户级 `~/.claude/CLAUDE.md`(CodeGraph 块,容器内 install 落地)、常驻桶规则(`language.md`)与目录页(`README.md`);条件桶/行为路由桶/媒体触发桶规则正文 MUST NOT 出现。

#### Scenario: 条件桶规则未被强载

- **WHEN** Claude 会话启动且未触达任何 `paths` 匹配路径
- **THEN** loaded.log 中不出现条件桶/行为路由桶/媒体触发桶规则文件的 session_start 装载记录

### Requirement: R 组必须进入透视与基线治理

R 组探针结果 MUST 与 P 组同流(schema 1.0 结果文件、`eval/results/docker-night/` 路径),端×探针透视矩阵与基线对比 MUST 覆盖 R 组;`baseline.json` MUST 建立 R 组五端基线(仅新增键,不触达 P 组);R 组 MUST 支持按既有 CONTROL 子集机制独立分组运行,不与 P 组全量互相阻塞;(R3/agents_only 端过滤机制已随 R3 撤除。)

#### Scenario: 透视含 R 组行列

- **WHEN** 五端夜测完成并运行透视汇总
- **THEN** 矩阵含 R1/R2/R3 行,各端有成功率/均时/轮次,基线对比覆盖 R 组

#### Scenario: R 组独立运行

- **WHEN** 仅调度 R 组子集
- **THEN** 夜测执行 R 组探针并产出透视,不要求 P 组全量同跑
