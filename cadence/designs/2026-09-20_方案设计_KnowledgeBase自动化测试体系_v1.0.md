# 方案设计：KnowledgeBase 自动化测试体系（kb-eval）

- 日期：2026-09-20
- 版本：v1.0
- 状态：待评审
- 关联：三批 KB 变更（kb-matrix-contract-and-retrieval-fix / kb-business-knowledge-intake / kb-composition-and-index-layer）已实施待回归；架构对齐 `2026-09-02_方案设计_eval体系_四skill安装效果测试_v1.0.md`（rule-eval-p0，未实施）——**对齐约定、不共享依赖、先行实施**

## 1. 背景与目标

三批 KB 变更后的验证现状：静态验证 ✅（26 项结构断言 + 两轮 k3-reviewer）、**行为验证为零**。维护者的回归问题：skill 文本改动后，全链（bootstrap→base-info→api→pages→overview→global-validation→context→update）是否仍可执行、产物是否满足契约、各机制（组合/寄生迁移/横向重算/漂移分级）是否真实生效。

度量目标（对应 rule-eval-p0 四问的 KB 版）：

1. 全链是否可按 skill 文本执行（每阶段完成条件可达成）
2. 产物是否满足全部契约断言（global-validation 6 项 + 完成条件）
3. 机制级场景是否生效（埋点→期望产物）
4. 修改 skill 后回归是否可一键重跑

## 2. 已锁定决策

| # | 决策 |
|---|---|
| K1 | 架构对齐 rule-eval-p0（车道分层/确定性断言/成本熔断/报告约定），资产独立先行 |
| K2 | fixture 标准版全埋点（3 服务/7 API/4 表/3 页面） |
| K3 | Tier-1 手动触发；PR 车道只跑 Tier-0（$0）；夜间化待稳定后评估 |
| K4 | 幂等双跑不适用（LLM 非确定性）→ 改为"结构不变量双跑均满足" |
| K5 | 断言三层：结构不变量 / 具名实体期望 / 反例断言；LLM-judge 仅 Tier-2 可选 |

## 3. 架构：三车道

```
evals/kb/
├── fixtures/standard/      # Java+Vue fixture 源码（git 资产，全埋点）
├── assertions/             # Python 断言器：tier0.py（结构）/ named.py（具名）/ negative.py（反例）
├── probes/                 # 机制探针：prompt + 期望 + 断言 id
├── runner/                 # 编排：run.py（fixture→/tmp 副本、阶段调度、断点续跑、报告）
└── 报告 → cadence/reports/eval/<日期>/kb/（json + md 矩阵 + 失败 transcript 回放）
```

| 车道 | 内容 | 触发 | 成本 |
|------|------|------|------|
| Tier-0 | 结构校验（26 项正式化）+ 断言器自测（断言器对故意损坏样本必须红）+ fixture 完整性检查 | PR（路径过滤 `cadence-init/skills/knowledge-base-*`） | $0 |
| Tier-1 | fixture 全链流水线：阶段 A 六阶段初始化 + 阶段 B 机制探针（4 个） | 手动（`python runner/run.py --stage all`，支持 `--stage api` 单阶段） | 估 $2–5/轮（阶段化+熔断） |
| Tier-2 | LLM-judge 产物质量评审（可选） | 手动/周度 | ~$5/轮 |

## 4. fixture 设计（标准版全埋点）

```text
fixtures/standard/
├── user-service/          # Spring Boot：用户基本信息 CRUD（API-A）
├── account-service/       # Spring Boot：账户信息查询（API-B）+ 对账定时任务（JOB）
├── order-service/         # Spring Boot：订单 + 状态机 + 消息生产/消费（EVENT）
├── web-portal/            # Vue3：用户列表页 / 订单页 / 账户页（3 页面）
├── db/init.sql            # 4 表 DDL（含 COMMENT、枚举、约束）
└── README.md              # 少量过时文档（测"文档与代码冲突→待确认"）
```

**埋点 → 机制 → 具名断言（核心对照表）**

| # | 埋点 | 触发机制 | 具名期望（named.py 断言） |
|---|------|---------|--------------------------|
| F1 | API-A 查用户基本信息 + API-B 查账户信息 + api-scope 组合诉求表 1 行 | CAP 全链 | `CAP-USER-ALL-INFO.md` 存在、状态 `proposed`、`implementation_api_ids` 空、`COMPOSES` 边 2 条、JOIN_KEY 表含两侧映射链 |
| F2 | account-service 的 `userId` 与 user-service 的 `userId` 同名但映射不同表（其中一侧映射断链） | JOIN_KEY 字段同名不算 | F1 的 JOIN_KEY 行标 `待确认`，CAP 保持 proposed（反例：不得 verified） |
| F3 | order 状态枚举 + 迁移 switch + 测试断言"已取消订单不可发货" | RULE/FLOW 生成 | 存在 `RULE-order-cancel-ship`（来源=测试断言）且 `FLOW-order-lifecycle` 含状态流转表；寄生的 Controller 注释原文保留 + 追加 RULE 链接 |
| F4 | RabbitMQ 生产/消费 + `@Scheduled` 对账任务 | EVENT/JOB ID | 矩阵含 `PRODUCES`/`CONSUMES` 边、`JOB-*` 稳定 ID 存在 |
| F5 | application.yml 明文密码 + 内部 IP | 脱敏 | 产物全文无明文密码/IP；配置键逐键列出且值 `<redacted>` |
| F6 | 表注释含业务规则"余额不可为负" | 寄生规则迁移 | 对应 RULE 存在且状态 `ai-draft`（仅代码证据） |
| F7 | git 历史：一条 fix commit 写明业务意图（"修复：导出文件保留期应为 7 天"）+ input 声明 git_history | ref 型证据 | 该规则 RULE 状态 `ai-draft`、证据含 `@<commit>` |
| F8 | 未提供 product.md / 部分提供两变体 | 可选输入 | 变体 1：相关位置记`未提供`；变体 2：README 标 `[用户提供]` |
| F9 | 一个破坏性变更模拟（删 API-B 的一个端点）+ 完整五文件变更包 | Update 横向重算 | F1 的 CAP 转 `待确认`/`retired`；图重建后边数==矩阵行数（等值断言） |
| F10 | 变更后 context 探针查询组合能力 | 漂移分级 | 探针输出含"未经人工核准"/阻断或漂移明细 |

fixture 两变体管理：`variant-full`（product.md+git_history 提供，F7/F8-v2 生效）、`variant-min`（全缺省，F8-v1 生效）。runner 按 `--variant` 生成 /tmp 副本。

## 5. 断言器三层

| 层 | 文件 | 性质 | 示例 |
|----|------|------|------|
| 结构不变量 | `tier0.py`（26 项正式化+扩充） | 确定性，与产物内容无关 | 矩阵六列、词表枚举、图边数==矩阵行数、documents 域计数一致、节序模板符合 |
| 具名期望 | `named.py` | 确定性，依赖 fixture 埋点 | F1–F10 对照表逐条 |
| 反例 | `negative.py` | 确定性 | 无明文敏感值、api/pages 阶段产物无横向边、无断链 verified、ai-draft 未被当 confirmed 引用（产物文本检查） |

**断言器自测（Tier-0 必含）**：对故意损坏的样本目录（assertions/fixtures-broken/）断言器必须全部红——防止断言器自身失效假绿（对齐 rule-eval-p0 的 E6-4 mock 冒烟前置）。

## 6. runner 与阶段编排

```text
run.py 流程：
1. fixture → /tmp/kb-eval-<ts>/（干净副本，git init 打基线标签）
2. 写 user-input/（六领域 scope 文件 + 变体注入 F7/F8 声明）
3. 阶段 A：for stage in [bootstrap, base-info, api, pages, overview, global-validation]：
     - 派 agent 会话（headless），prompt=skill 全文+阶段指令+产物目录
     - 会话结束 → 跑该阶段断言（tier0+named 子集）→ 失败即停并留 transcript
     - 通过 → 记录 results.json（阶段/耗时/token/产物路径）→ 下一阶段
     （断点续跑：results.json 已有且产物在 → 跳过，与 coverage.initialization 状态机双保险）
4. 阶段 B：探针 4 个（context 查询×2、update 变更包×1、漂移×1），各自独立 agent 会话+断言
5. 报告：通过矩阵 + 具名 diff（对基线 results.json）+ 失败 transcript 路径
熔断：每阶段 --max-turns / timeout / 累计成本上限（对齐 E6-5）
```

**探针集（阶段 B）**

| 探针 | 任务 | 断言 |
|------|------|------|
| P1 组合查询 | "我要对外提供全部用户信息，现有哪些能力可组合？限制是什么？" | 输出引用 CAP + 输入 API；JOIN_KEY 待确认被显式指出；无编造 verified |
| P2 规则检索 | "订单取消后还能发货吗？" | 命中 RULE-order-cancel-ship（种子直取路径）；ai-draft 标注正确 |
| P3 变更更新 | 消费 F9 变更包 | CAP 失效传播 + 等值校验通过 + 锚点复核执行 |
| P4 漂移分级 | 基线后追加未声明代码改动，再查询 | 漂移分级输出正确（普通→有条件就绪/关键→阻断） |

## 7. 非确定性与假绿对策（对齐并修订 rule-eval-p0 十条）

沿用：成本熔断、transcript 全量留存、断点续跑、prompt 经 env 注入、具名 diff 报告。
修订：幂等双跑→结构不变量双跑（K4）；轨迹断言弱化（KB 阶段无 stream-json 轨迹可判，改为产物+transcript 抽查）；模型 pin 沿用。
新增：**判分不依赖 agent 自述**——断言只读产物文件与 transcript 中的工具调用记录，agent 说"完成"不算数。

## 8. 与 skill 调优的接口

失败分类与处理：

| 分类 | 判定 | 处理 |
|------|------|------|
| skill 文本缺陷 | 换 agent 重跑仍失败且指令可改进 | 走 OpenSpec 小变更修 skill → 重跑受影响阶段 |
| 断言缺陷 | 期望本身不合理 | 修 named.py（需设计评审，防"改答案凑通过"） |
| fixture 缺陷 | 埋点未真正触发机制 | 修 fixture + 补埋点说明 |
| agent 遵循问题 | 特定模型失败、其他模型通过 | 记录为 skill 措辞强化项，进 Tier-2 观察 |

**红线**：断言只允许因"期望错了"而改，不允许因"agent 做不到"而放松——做不到就是 skill 缺陷。

## 9. 风险与对策

| 风险 | 对策 |
|------|------|
| Tier-1 单轮 $2–5 × 迭代轮次累积 | 阶段化重跑（只跑受影响阶段）；results.json 断点续跑 |
| LLM 产物结构漂移导致断言误红 | 断言只断不变量与具名锚点；失败样本归档供断言器改进 |
| fixture 过拟合（断言背死埋点，skill 换实现方式即红） | 具名断言锚定"机制生效证据"而非精确文本；季度审视 |
| 执行环境差异（headless vs 交互） | 探针 prompt 显式给任务边界；Tier-2 人工复核抽样 |
| rule-eval-p0 后续落地后的双轨维护 | 共享约定层（报告路径/熔断参数/车道语义）抽出为公共 README，实施时对齐 |

## 10. 非目标

- 触发识别/路由测试（KB skill 的选择门禁已有独立 spec）
- 多端×多模型矩阵（首期单执行端跑通，矩阵化待 rule-eval-p0 落地后共用其 runner）
- 性能/成本基准化（只记录不设阈值）
- 真实开源存量项目第二轮验证（fixture 稳定后的后续项）

## 11. 估算

fixture 标准版全埋点 1–1.5d；断言器三层+自测样本 1.5d；runner（阶段调度/续跑/熔断/报告）1d；探针 4 个 0.5d；首轮跑通+调优迭代 1–2d（含预计 2–3 处 skill 缺陷修复走小变更）≈ **5–7 人日**。
