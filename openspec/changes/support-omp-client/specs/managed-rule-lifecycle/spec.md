# managed-rule-lifecycle Specification(Change A delta)

## ADDED Requirements

### Requirement: 规则模板必须携带共享 frontmatter 分桶契约

框架受管规则模板(`references/rules/` 下 8 个落地规则对应的 10 个源模板:`code-usage`/`code-reading` 各双源分化)MUST 按 bucket 分桶携带 YAML frontmatter,落地文件与模板逐字一致的既有权威覆盖语义不变:

- **常驻桶**(`language.md`):`description` + `alwaysApply: true`,无 `paths` —— Claude 端无条件强载,omp 端常驻;
- **条件桶**(`code-usage.md`、`code-reading.md`、`document-storage.md`、`markdown-format.md`、`playwright.md`):`description` + 非空 `paths` glob —— Claude 端仅在触达匹配路径时注入,omp 端进索引按需 `rule://` 读取;`code-usage`/`code-reading` 双源按项目类型分化,coding 落地源给源码扩展名 glob(`SOURCE_EXTS` 口径 + `tsx`/`jsx` 增补),non-coding 落地源给永不匹配 glob(退化为行为路由桶);
- **行为路由桶**(`openspec-superpowers-workflow.md`):`description` + 永不匹配 glob —— Claude 端不自动注入,仅经 L0 路由必读;omp 端索引全 agent 可见(框架模板 MUST NOT 携带 `agents` 限定——子代理自行读取初始化的规则;`agents:` 为 omp 原生可选字段,由用户在项目规则中自行添加,框架与 eval 均不使用);
- **媒体触发桶**(`mcp-servers.md`):`description` + 图片/媒体 glob —— Claude 端触图自动载,其余场景经 L0 路由必读;omp 端索引;
- `README.md` 模板不变(目录页常驻,不参与 omp 桥接)。

frontmatter 契约 MUST 对各端互不干扰:Claude 仅消费 `paths`,omp 仅消费 `description`/`alwaysApply`/`agents`,未知字段各端静默忽略(2026-09-09 实测交叉容忍)。永不匹配 glob 的文件内 MUST 附注释标注意图。

#### Scenario: 老项目重跑获得分桶 frontmatter

- **WHEN** 已有无 frontmatter 落地规则的项目重新运行 `rule-config`
- **THEN** 权威覆盖后落地文件与含 frontmatter 的模板逐字一致
- **AND** Claude Code 新会话启动时不再强载条件桶/行为路由桶/媒体触发桶规则正文

#### Scenario: omp 索引行含描述

- **WHEN** omp 会话在完成桥接的项目中启动
- **THEN** 系统提示的规则索引仅含各规则名与 description,不含任何规则正文

## MODIFIED Requirements

### Requirement: Claude Code、Kimi Code 与 Codex 入口必须语义等价

系统 SHALL 允许针对客户端入口语法进行适配,但 MUST 保持任务信号、Skill 顺序、阶段门禁、失败关闭和轻量豁免语义在 Claude Code、Kimi Code、Codex、pi 与 omp 五端等价。omp 端经 `.omp/AGENTS.md` 受管活引用获得与根 `AGENTS.md` 等价的路由语义;omp 调用 Skill 的形式为全文读取 `skill://<名>`(与 pi 的全文读取同类)。

#### Scenario: Kimi Code 使用 AGENTS 入口

- **WHEN** Kimi Code 读取项目 `AGENTS.md`
- **THEN** 它获得与 Claude Code 从 `CLAUDE.md` 获得的等价路由语义
- **AND** 新功能、直接 apply 和完工声明使用相同门禁

#### Scenario: omp 使用受管活引用入口

- **WHEN** omp 会话读取项目 `.omp/AGENTS.md`
- **THEN** 它获得与其他端从根入口获得的等价路由语义(CodeGraph 块经活引用无副本跟随)
- **AND** 新功能、直接 apply 和完工声明使用相同门禁

#### Scenario: 客户端语法不同

- **WHEN** 某客户端调用 Skill 的语法与其他客户端不同
- **THEN** 生成入口可以使用该客户端支持的语法
- **AND** 不得删除或改变规范 Skill 的触发顺序

### Requirement: L0 区块必须包含可见文本版本行

自 v4 起,L0 受管区块首行 MUST 包含可见文本版本标识(如 `Cadence L0 路由内核 v5`),与既有 HTML 注释标记并存:注释标记供脚本解析与受管识别,可见文本供 agent 在上下文中自报版本;v5 延续该要求。v5 的 Skill 调用客户端语义 MUST 覆盖五端(omp 归 pi 同类:经 `skill://` 全文读取)。既有确定性升级机制 MUST 将 v4 及更早版本升级为 v5;历史版本规范 MUST 归档进 `l0-history/`。框架升级 L0 版本时,eval 断言层(`eval/install/assertions.py` 的 L0 标记常量、`l0.v4` 断言名、升级文案与其测试 fixture)MUST 同步升版,不得留旧版断言名并行。

动机:Claude Code 注入上下文时剥离 HTML 注释(2026-09-02 实测);omp 调用 skill=全文读取 `skill://`(2026-09-09 omp 内置文档与实测)。

#### Scenario: v3 确定性升级为 v4

- **WHEN** 入口文件包含成对 v3 标记且完整区块内容与 v3 规范源一致,而框架当前版本为 v4
- **THEN** 系统 MUST 不经用户决策将区块升级为 v4 规范源,普通模式与 no-interrupt 模式同动作

#### Scenario: v4 确定性升级为 v5

- **WHEN** 入口文件包含成对 v4 标记且完整区块内容与 v4 规范源一致,而框架当前版本为 v5
- **THEN** 系统 MUST 不经用户决策将区块升级为 v5 规范源,普通模式与 no-interrupt 模式同动作

#### Scenario: eval 断言层随版本同步

- **WHEN** 框架 L0 当前版本为 v5
- **THEN** eval stage1 断言以 v5 标记判定入口区块,断言名为 `l0.v5`,不存在残留的 `l0.v4` 断言名

#### Scenario: Claude Code 回执可自报版本

- **WHEN** Claude Code 会话被要求复述当前生效的 L0 版本
- **THEN** 其可从上下文中的可见文本版本行读出版本号 v5,不依赖 HTML 注释标记
