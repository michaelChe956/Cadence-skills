# KnowledgeBase 自动化测试体系（kb-eval）实施计划 v1.3

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**v1.3 修订记录**（第二轮双评审 23 项全吸收 + 结构改革）：
- **环境事实修正**：本机无 docker，只有 rootless podman（夜测即 podman + `podman cp`）→ 全链改 podman；结果用 `podman cp` 拷出（rootless bind mount 不可写，实测 Permission denied）。
- **断点续跑改为常驻容器**：`podman run -d` 起常驻容器，kb_runner 单进程循环执行；阶段失败退出但容器保留，`podman exec … --resume` 同容器续跑；成功后 cp 结果 + rm。
- **三根分离**：`HOME=/home/tester`（CLI+认证+技能，永不被清理）；`WORK=/home/tester/work`（project+快照，prepare 只清 `work/project`）；`RESULTS=/home/tester/results`（唯一结果根，results.json/transcripts/runs/report 全在此，cp 出宿主）。
- **技能安装补齐**：装端后复制仓库到可写目录跑 `install.sh`（skill 之间互相调用需要技能进各端技能目录；对齐夜测做法，含预建 upstream 防 update 失败）。
- **kimi 端修正**：非 npm 包——从宿主 `~/.kimi-code` 拷贝官方二进制与认证；`--skills-dir` 参数；session 捕获 `.kimi-code/sessions/**`。
- **npm 权限修正**：Dockerfile 补 `npm config set prefix ~/.npm-global` + PATH（照夜测，否则 tester 装全局包 EACCES）。
- **已知代码 bug 修复入契约**：snapshot_fingerprint 排序 `key=lambda p: p.name`（原 lambda 引用未绑定变量必 NameError）；快照文件名取 `application.yml.parents[3].name`（服务名，原写法 TypeError+三文件重名）；快照导出后 `chmod -R a-w`（只读落实）；usage 记录（stream-json 解析，不可得写 null）。
- **探针隔离**：阶段 A 全绿后 `project → project.golden` 快照；每个探针从 golden 独立副本开始（P3/P4/P9 各自注入，零污染；P5 用探针前后 `git status --porcelain` 差分判改动集，非空且 ⊆ 影响面，且 stream-json 中首个写工具事件前存在读取知识库文件事件）；阶段 A 未全绿时探针全标 `blocked`。
- **内核接口改造**：`build_prompt(stage)->str`（非 print）；断言函数返回 bool 不 `sys.exit`；阶段成功 = CLI rc==0 且断言全过；`PROBE_ASSERTS` 扩至 P1–P9。
- **--fast 定义**：六阶段全跑（阶段顺序不可跳，pages 适用就必须跑）+ 仅 P1 探针。
- **结构改革**：fixture 静态内容全文内联（Task 1–4）；runner/断言器代码不再预写全文——改为**接口契约+关键算法+逐步验收命令**，实施时"写一段、立即 `py_compile`+干跑+selftest 验一段"（两轮评审证明计划预写未执行代码是缺陷来源）。
- pi 端：认证拷贝后剥离 `~/.pi/agent/settings.json` 的 `packages` 并带 `npm/git` 首启缓存（防 275MB 联网装扩展失败致空 transcript）。

**Goal:** evals/kb/：全埋点 fixture、三层断言器+自测、podman 独立容器考场（四端常规 CLI 当日版）、九探针、断点续跑；Tier-0 全绿、Tier-1 一条命令全链自动评分。

**Architecture:** fixture 静态阅读样本；容器常驻+exec 模型；夜测零耦合（不共用镜像/入口/结果目录；各端 headless 参数与 prompt 传输**参照** `eval/runner/proc.py` 的 INVOCATIONS 表——仅作参考，kb-eval 独立实现）。

**Spec:** `openspec/changes/kb-eval-pipeline/`（R3/R4 容器考场+九探针）。

## Global Constraints

- fixture 静态样本；断言只读产物与 transcript；不依赖 agent 自述。
- **禁止 `git commit`**（本仓库）；fixture git 历史只在容器内制造。
- 代码实施纪律：每个代码文件落盘后立即 `python3 -m py_compile` + 对应干跑/自测命令，绿后才进下一步。
- 嵌套代码块外 4 内 3 反引号；产物中文。

---

### Task 1: fixture 骨架

**Files:** `evals/kb/fixtures/standard/{埋点说明.md,README.md}` + 4 模块 `{pom.xml,Application 主类}`

- [ ] **Step 1: 埋点说明.md**（内容 = 附录 A.1 全文：F1–F10 → N1–N10 对照表 + 变体说明 + "完整性由 fixture_check.py 机械校验"）
- [ ] **Step 2: README.md**（过时文档：宣称系统只有 user-service，注明 account/order 为后来新增）
- [ ] **Step 3: 4×pom.xml**（parent spring-boot 3.2.5、java 17、web+mybatis+mysql；order 额外 amqp；artifactId 分别 user-service/account-service/order-service；web-portal 无 pom）
- [ ] **Step 4: 3×Application 主类**（标准 @SpringBootApplication，注释写服务职责）
- [ ] 验证：`find fixtures/standard -type f | wc -l` ≥ 9；artifactId/类名正确

### Task 2: user-service 与 account-service（F1/F2/F4-JOB/F5）

- [ ] user-service 全部类+Mapper XML（Controller `GET /api/user/basic/{userId}` 注释"对外能力 API-A"；Mapper XML 显式 `AS userId` 映射；application.yml 端口 8081+弱密码 Dev_Only_123）
- [ ] account-service 全部（Controller `GET /api/account/{userId}` 注释"对内 REST，供聚合能力复用"；**AccountMapper.xml 用 `SELECT *` 无映射+注释"历史遗留写法"**=F2；AccountEntity.balance 注释引表注释规则；ReconcileJob @Scheduled+类注释写明启用证据=配置 reconcile.enabled；application.yml 含 **Pr0d@Acct#2026** + **10.20.31.14** + reconcile 配置=F5/F4）
- [ ] 验证：grep 埋点四要素各 1 处；user 侧显式映射在

（两服务完整文件内容完整文件内容见附录 A.5/A.6，实施时照抄。）

### Task 3: order-service 与 web-portal（F3/F4-EVENT/F7）

- [ ] order-service 全部（OrderStatus 枚举含 CANCELLED；OrderService.ship 用 `OrderStatus.valueOf(order.getStatus())` 比较+"已取消订单不可发货"注释=F3；markPaid 显式调 orderEventProducer.sendOrderPaid；OrderEventProducer convertAndSend+OrderEventListener @RabbitListener=F4；ExportService RETENTION_DAYS=7+注释"历史 bug 曾误配 30 天"=F7；OrderServiceTest 匿名 StubOrderMapper 返回 CANCELLED 订单断言抛异常；application.yml 含 mq.internal.demo.local+Mq_2026_Order）
- [ ] web-portal 全部（package.json/vite.config/main.js 三路由/App.vue/request.js baseURL /api/api/index.js 四函数；UserList/OrderPage/AccountPage 三视图各自真实调用——附录 A.8 全文）
- [ ] 验证：grep F3/F4/F7；三视图文件存在且 api 调用一致

### Task 4: DDL、user-input 模板、F9 变更包

- [ ] db/init.sql（三库各 `CREATE DATABASE`+`USE`；4 表；t_user_account 表/列 COMMENT"余额不可为负"=F6）
- [ ] user-input-template/ 七文件+product.md（内容 = 附录 A.10 全文：base-info 含 YAML 证据块带 {{REPO_INIT}}；project-scope 工程清单表；data-model-scope 结构证据表（路径 `./db/init.sql`）；configuration-scope 完整快照元数据表带 {{SNAPSHOT_DIR}}/{{FINGERPRINT}}；middleware-scope 清单表；api-scope 对外清单+组合诉求行（来源=API-user-basic+对内账户 Method+Path 锚点）；page-scope 应用表）
- [ ] change-package-F9/ 五文件（code-change.md 声明：删 AccountController.java+AccountService.java、AccountPage.vue 改提示页、api/index.js 移除 queryAccount；F9_BASE/F9_HEAD 占位；change-summary 七行含业务知识=有变更）
- [ ] 验证：DDL 三库归属；模板 8 文件；变更包 5 文件与 apply 清单一致；`grep -c "{{" user-input-template/*` = 3 处占位符

### Task 5: 断言器（代码契约 + 逐步验收）

**Files:** `evals/kb/assertions/{common.py,tier0.py,named.py,negative.py,fixture_check.py,selftest.py}`、`fixtures-valid/`、`fixtures-broken/×4`

**接口契约（实施时逐文件落地，每文件落盘立即验证）：**

- `common.py`：`Result`（items 记 name/ok/detail，`failed_names()` 供红名单）；`SKILL_ROOT=parents[3]/cadence-init/skills`；`kb_files(kb)->dict`。
  验收：`python3 -c "from common import Result; r=Result(); r.check('x',1==1); assert r.report('t')"`。
- `tier0.py`：`--skill-src`（26 项源断言：词表 11+3 闭合/横向已启用标注/四模板表列一致/manifest 模板合法+三新键/契约 YAML 块可解析/固定产物两副本一致含 business+capabilities——从 `/tmp/kb-unified-check.py` 已验证逻辑移植）；`--kb-products D --stage S`（`STAGE_LEVEL` 阶段分级启用：bootstrap=manifest+输入七文件；base-info+=矩阵六列/词表/图三断言；api+=接口索引；pages+=页面索引；global-validation/update=全部）。**快照指纹算法独立实现处：`key=lambda p: p.name`**。
  验收：`--skill-src` 绿；对 fixtures-valid `--stage global-validation` 绿；对 broken-matrix/broken-graph 命中红名单。
- `named.py`：`--kb-products --stage --phase --variant`；`STAGE_N` 映射（api→N4；overview/global-validation→N1-N8；update→N9）；`cap_meta()` 解析 CAP 元数据表；N1 按相位分期望（init: proposed+实现空+COMPOSES≥2 且源皆 CAP-；post-update: 非断链 verified）；N2 JOIN_KEY 行含待确认；N3 取消规则+FLOW 状态流转+寄生原文保留；N4 PRODUCES/CONSUMES/JOB；N5 敏感值四项禁现+`<redacted>` 存在；N6 余额规则在同一 RULE 内含 ai-draft；N7 variant=full 时 `@[0-9a-f]{7,40}` 命中矩阵或 RULE，min 时跳过；N8 variant 分期望（full: README 含 [用户提供]；min: 含 未提供）；N9 CAP 待确认/retired。
  验收：fixtures-valid 全绿；构造反例（改 CAP 状态）判红。
- `negative.py`：敏感值+COMPOSES 源 CAP-+空实现不得 verified+business README 中 ai-draft 不被标 confirmed。
- `fixture_check.py`：16 项埋点 grep 判定+模板七文件（CHECKS 表 = 埋点说明的机械翻译）。
- `selftest.py`：正控（fixtures-valid 三件套全绿）+反控四例**红名单命中**（断言名精确匹配，崩溃/缺依赖不算红）；退出码 0=自测通过。
- `fixtures-valid/`：最小合法产物树（manifest 六列矩阵 3 行含 COMPOSES 源 CAP-/图边数一致/CAP proposed+实现空/RULE 余额+ai-draft/FLOW 状态流转/七输入/README 用户提供）——**构造后立即跑三件套全绿才算完成**。

### Task 6: podman 容器考场

**Files:** `evals/kb/docker/Dockerfile`、`evals/kb/run.py`（宿主机）、`evals/kb/runner/kb_runner.py`、`evals/kb/runner/agents.json`

- [ ] **Step 1: Dockerfile**（archlinux+国内源；pacman: git nodejs npm python python-pip which sudo；pip pyyaml；tester 用户+sudoers；**`mkdir ~/.npm-global && npm config set prefix ~/.npm-global` + `ENV PATH=/home/tester/.npm-global/bin:…`**；ENV `NPM_CONFIG_REGISTRY=https://registry.npmmirror.com`）
  验收：`podman build -t cadence-kb-eval evals/kb/docker/` 成功；`podman run --rm cadence-kb-eval node -v` 出版本。
- [ ] **Step 2: agents.json**（四端；kimi 特殊：`"install": null, "binary_from": "~/.kimi-code/bin/kimi", "auth_map": {"~/.kimi-code": ".kimi-code"}, "argv_extra": ["--skills-dir", "{home}/.kimi-code/skills"]`；claude cmd 含 `-p --dangerously-skip-permissions --output-format stream-json --verbose`；codex/pi 参数实施时照 `eval/runner/proc.py` INVOCATIONS 表核定（存在文件，仅参考）；pi 拷认证后剥离 settings.json packages+带 npm/git 缓存）
- [ ] **Step 3: 宿主机 run.py**（契约）：
  1. `podman build`（--no-build 跳过）
  2. 存在同名容器先 `podman rm -f`；`podman run -d --name kb-eval-<agent> -v <repo>:/opt/repo:ro -v ~/.claude:/mnt/auth-claude:ro …（只挂启用端）cadence-kb-eval sleep infinity`
  3. `podman exec … python3 /opt/repo/evals/kb/runner/kb_runner.py --agent A --variant V`；rc≠0 → 打印"容器保留，续跑：podman exec … kb_runner.py --resume"并退出 1
  4. rc==0 → `podman cp kb-eval-<agent>:/home/tester/results/. evals/kb/results/<日期>/<agent>-<variant>/` → `podman rm -f`
  验收：起停往返；失败保留容器可 exec；cp 出的目录含 results.json/report.md/transcripts/。
- [ ] **Step 4: kb_runner.py**（容器内单进程，契约）：
  - 常量：`HOME=/home/tester`、`WORK=/home/tester/work`、`RESULTS=/home/tester/results`、`PROJECT=WORK/project`；**prepare 只允许清 `WORK/project` 与 `WORK/snapshots`，禁止触碰 HOME 其他内容**。
  - `install_agent()`：npm 端 `npm install -g <pkg>`；kimi 端 `cp /mnt/auth-kimi/bin/kimi ~/.npm-global/bin/ && chmod +x`；随后 `--version` 记录（只记不锁）；失败 → results 记 `infrastructure_error` 并退出 3。
  - `install_skills()`：`cp -a /opt/repo ~/repo-writable && cd ~/repo-writable && git remote add upstream <本地路径> || true && bash install.sh`（对齐夜测防 update 失败做法）。
  - `prepare(variant)`：fixture→PROJECT（排除模板/变更包/埋点说明）；git 两步历史（先 sed RETENTION_DAYS 7→30 提交 init，再还原 7 提交"修复：导出文件保留期应为 7 天（原误配 30 天）"，取 root commit）；快照导出 `snapshots/baseline-config/<service>-application.yml`（**文件名 `c.parents[3].name + "-application.yml"`**）；指纹（**`key=lambda p: p.name`**）+ `chmod -R a-w snapshots/`；user-input 渲染三占位符（min 裁剪）；results.json 初始化（variant/budget/stages/probes/snapshot.readonly=true）。
  - `build_prompt(stage)->str`（六阶段指令+边界+预算+技能路径，返回字符串）；`run_cli(argv, prompt, cwd, timeout)`（env `EVAL_PROMPT` 注入、进程组超时 kill、stdout 原文+退出码+`parse_usage(stream_json)`→usage 或 null）。
  - `run_stage(stage)`：results 已 ok 且产物在→跳过；rc≠0 **或** 断言子集（tier0/named/negative `--stage`）任一失败→记 FAIL 后 `sys.exit(1)`（容器常驻，宿主可见续跑提示）；全过→记 {ok, asserts{pass,total}, duration, usage, transcript}。
  - 探针：阶段 A 全绿→`cp -a PROJECT PROJECT.golden`；**每探针前 `rm -rf PROJECT && cp -a PROJECT.golden PROJECT`**；P3 先 apply_f9（删两 Java+AccountPage 改提示页+index.js 删行+git commit+变更包拷入+占位符填真实提交）；P4/P9 各自 inject_drift；阶段 A 未全绿→九探针全记 `blocked`。
  - `PROBE_ASSERTS` P1–P9（九探针断言（正文 Task 8 Step 2 + v1.3 探针增强条款）；P5 增强：探针前后 `git status --porcelain` 差分非空且 ⊆ 影响面六文件；stream-json 中首个写类工具事件之前存在读取 `data-models/` 或 `interfaces/` 文件的事件）；探针成功=rc==0 且断言全过。
  - `--fast`：六阶段全跑+仅 P1。`--resume`：从 results.json 断点继续。
  - `report()`：**全部写 RESULTS**（results.json/runs/<run_id>.json（结构对齐夜测 build_result 字段名）/report.md（通过矩阵+基线具名 diff+失败 transcript 相对路径+CLI 版本））。
  - 实施纪律：每完成一个函数立即 py_compile+干跑（如 `--help`、prepare 后 tree 检查、`grep -r "{{" PROJECT/cadence/…/user-input/` 为空）。
- [ ] **Step 5: 端到端机制验证**（允许阶段失败）：run.py --agent claude --variant full → 容器起/CLI 装/技能装/prepare 渲染干净/阶段调用有 transcript/断言执行/results+report cp 出/失败时容器保留可续跑；`--fast` 生效；`git status` 本仓库无 `eval/`（夜测）改动。

### Task 7: Tier-0 三件套

- [ ] tier0 --skill-src 绿；fixture_check 绿；selftest 正控绿+反控红名单命中；全程无凭据零 LLM。

### Task 8: 首轮 Tier-1 与调优（WP5）

- [ ] Step 1: `run.py --agent claude --variant full` 全链；失败四分类（预期 2–3 处 skill 缺陷走小变更后 `--resume` 续跑）。
- [ ] Step 2: 九探针全量（含 golden 隔离机制验证：P3 后 P6 仍能排查账户规则——副本来自 golden 未受 P3 删除影响）。

**九探针定义（prompt + 可执行断言；每探针独立 golden 副本；阶段 A 未全绿则全记 blocked）：**

| 探针 | 类型 | 任务 prompt | 断言 |
|------|------|------------|------|
| P1 | 机制 | 我要对外提供全部用户信息，现有哪些能力可组合？限制是什么？（先执行 knowledge-base-context） | 输出含 `CAP-`、`/api/account/`、`待确认` |
| P2 | 机制 | 订单取消后还能发货吗？（先执行 knowledge-base-context） | 输出含 `不可发货`；ai-draft 条目带"未经人工核准"或无 ai-draft 引用 |
| P3 | 机制 | 执行 knowledge-base-update 消费 CHANGE-F9-REMOVE-ACCOUNT-API | 输出含 `待确认` 或 `retired`；产物 N9 通过+图等值复跑通过 |
| P4 | 机制 | （inject-drift 后）确认订单发货规则当前实现 | 输出含 `漂移` 且（`有条件就绪` 或 `阻断`） |
| P5 | 真实任务 | 给用户表加一个最后登录时间字段 last_login_at，更新相关接口 | 探针前后 `git status --porcelain` 差分**非空**且 ⊆ 影响面集 {db/init.sql, UserEntity, UserMapper.java, UserMapper.xml, UserBasicController, UserBasicService}；stream-json 中首个写类工具事件之前存在读取 `data-models/` 或 `interfaces/` 文件的事件 |
| P6 | 真实任务 | 测试反馈账户余额出现了负数，排查一下哪里没拦住 | 输出引用 `余额不可为负` 或 `RULE-` |
| P7 | 真实任务 | 想给订单加一种'货到付款'支付方式，评估一下影响面 | 输出引用 `OrderStatus` 或状态流转/FLOW，且提及受影响实体（表或接口至少其一） |
| P8 | 真实任务 | 运营要一份用户全景报表（基本信息+账户+订单），设计数据获取方案 | 输出引用 CAP 或 ≥2 个输入端点；对缺失能力（订单维组合）指出需新增/待确认而非编造 |
| P9 | 真实任务 | （inject-drift 后）Review 这个改动：发货条件从仅 PAID 放宽为 PAID 或 CREATED，有没有问题？ | 输出指出与状态机规则冲突（`PAID`/规则/`漂移` 至少其二），不无脑放行 |
- [ ] Step 3: variant-min 复跑（N8 分期望）；四端逐端跑（codex/pi/kimi）。
- [ ] Step 4: 首基线入档 + 首轮调优总结报告。

---

## 附录 A：fixture 全文（Task 1–4 的完整文件内容，自包含）

### A.1 埋点说明.md

```markdown
# fixture 埋点说明（标准版 v1.1）
>
> 本 fixture 是 KnowledgeBase skill 体系的静态测试样本：代码不需要编译运行，只需被 skill 阅读分析。每个埋点登记：位置 → 触发机制 → 具名断言编号（assertions/named.py）。fixture 完整性由 assertions/fixture_check.py 机械校验（Tier-0 三件套之一）。

| # | 埋点位置 | 触发机制 | 断言 |
|---|---------|---------|------|
| F1 | user-service GET /api/user/basic/{userId}（对外清单 API-user-basic）+ account-service GET /api/account/{userId}（对内，清单备注登记锚点）+ api-scope 组合诉求行 | CAP 全链 | N1 |
| F2 | account-service AccountMapper.xml 用 SELECT * 无显式映射 | JOIN_KEY 字段同名不算+断链待确认 | N2 |
| F3 | order-service OrderStatus 枚举+OrderService.ship 状态机+OrderServiceTest 桩断言+Controller 注释 | RULE/FLOW 生成+寄生迁移 | N3 |
| F4 | order-service OrderEventProducer/Listener（RabbitMQ 注解）+ account-service ReconcileJob（@Scheduled+reconcile.enabled） | EVENT/JOB 稳定 ID | N4 |
| F5 | account/application.yml 明文密码+内部 IP；order/application.yml MQ 密码 | 脱敏反例 | N5 |
| F6 | db/init.sql t_user_account 表注释"余额不可为负" | 寄生规则迁移（ai-draft） | N6 |
| F7 | runner 两步 git 提交（init=30 天→fix=7 天，message 带修复意图）+ git_history 声明（variant-full） | ref 型证据仅 ai-draft | N7 |
| F8 | variant-full 提供 product.md+三源；variant-min 全缺省 | 可选输入两形态 | N8 |
| F9 | change-package-F9 五文件 + runner apply-f9 严格执行同清单 | Update 横向重算+图重建 | N9 |
| F10 | runner inject-drift 改 OrderService.ship 注释语义（未提交未声明） | context 漂移分级 | N10 |

变体：user-input-template/ 为渲染源（占位符 {{REPO_INIT}}/{{SNAPSHOT_DIR}}/{{FINGERPRINT}}）；--variant min 裁剪 product.md 与业务知识证据节。
```

### A.2 README.md

```markdown
# demo 商城系统（过时文档）

本系统包含 user-service（用户服务）。所有功能由 user-service 提供。

> 注意：本文档写于项目早期，未更新。account-service 与 order-service 为后来新增。
```

### A.3 pom 模板（三后端服务；artifactId 替换；order 加 amqp）

```xml
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <parent>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-parent</artifactId>
    <version>3.2.5</version>
  </parent>
  <groupId>com.demo</groupId>
  <artifactId>user-service</artifactId>
  <version>1.0.0</version>
  <properties><java.version>17</java.version></properties>
  <dependencies>
    <dependency><groupId>org.springframework.boot</groupId><artifactId>spring-boot-starter-web</artifactId></dependency>
    <dependency><groupId>org.mybatis.spring.boot</groupId><artifactId>mybatis-spring-boot-starter</artifactId><version>3.0.3</version></dependency>
    <dependency><groupId>mysql</groupId><artifactId>mysql-connector-java</artifactId><version>8.0.33</version></dependency>
  </dependencies>
</project>
```

### A.4 Application 主类模板（包名/类名替换）

```java
package com.demo.user;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

/** 用户服务：维护用户基本信息 */
@SpringBootApplication
public class UserApplication {
    public static void main(String[] args) {
        SpringApplication.run(UserApplication.class, args);
    }
}
```

### A.5 user-service 全部文件

**controller/UserBasicController.java**

```java
package com.demo.user.controller;

import com.demo.user.entity.UserEntity;
import com.demo.user.service.UserBasicService;
import org.springframework.web.bind.annotation.*;

/** 用户基本信息查询接口（对外能力 API-A） */
@RestController
@RequestMapping("/api/user")
public class UserBasicController {

    private final UserBasicService userBasicService;

    public UserBasicController(UserBasicService userBasicService) {
        this.userBasicService = userBasicService;
    }

    /** 查询用户基本信息：userId、姓名、手机号、邮箱 */
    @GetMapping("/basic/{userId}")
    public UserEntity queryBasic(@PathVariable("userId") Long userId) {
        return userBasicService.queryBasic(userId);
    }
}
```

**service/UserBasicService.java**

```java
package com.demo.user.service;

import com.demo.user.entity.UserEntity;
import com.demo.user.mapper.UserMapper;
import org.springframework.stereotype.Service;

/** 用户基本信息业务逻辑 */
@Service
public class UserBasicService {

    private final UserMapper userMapper;

    public UserBasicService(UserMapper userMapper) {
        this.userMapper = userMapper;
    }

    /** 按用户 ID 查询基本信息（对应 t_user 表） */
    public UserEntity queryBasic(Long userId) {
        return userMapper.selectById(userId);
    }
}
```

**mapper/UserMapper.java**

```java
package com.demo.user.mapper;

import com.demo.user.entity.UserEntity;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

/** t_user 表数据访问 */
@Mapper
public interface UserMapper {
    UserEntity selectById(@Param("userId") Long userId);
}
```

**resources/mapper/UserMapper.xml**（F1-a 侧显式映射）

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE mapper PUBLIC "-//mybatis.org//DTD Mapper 3.0//EN" "http://mybatis.org/dtd/mybatis-3-mapper.dtd">
<mapper namespace="com.demo.user.mapper.UserMapper">
  <select id="selectById" resultType="com.demo.user.entity.UserEntity">
    SELECT user_id AS userId, user_name AS userName, mobile, email
    FROM t_user WHERE user_id = #{userId}
  </select>
</mapper>
```

**entity/UserEntity.java**

```java
package com.demo.user.entity;

/** 用户基本信息实体（对应 t_user.user_id，见 UserMapper.xml 显式 AS 映射） */
public class UserEntity {
    /** 用户唯一标识 */
    private Long userId;
    private String userName;
    private String mobile;
    private String email;
}
```

**resources/application.yml**

```yaml
server:
  port: 8081
spring:
  application:
    name: user-service
  datasource:
    url: jdbc:mysql://localhost:3306/demo_user?useSSL=false
    username: demo_user
    password: Dev_Only_123
```

### A.6 account-service 全部文件

**controller/AccountController.java**

```java
package com.demo.account.controller;

import com.demo.account.entity.AccountEntity;
import com.demo.account.service.AccountService;
import org.springframework.web.bind.annotation.*;

/** 用户账户信息查询接口（对外能力 API-B） */
@RestController
@RequestMapping("/api/account")
public class AccountController {

    private final AccountService accountService;

    public AccountController(AccountService accountService) {
        this.accountService = accountService;
    }

    /** 查询用户账户信息：账户号、余额、状态（对内 REST，供聚合能力复用） */
    @GetMapping("/{userId}")
    public AccountEntity queryAccount(@PathVariable("userId") Long userId) {
        return accountService.queryAccount(userId);
    }
}
```

**service/AccountService.java**

```java
package com.demo.account.service;

import com.demo.account.entity.AccountEntity;
import com.demo.account.mapper.AccountMapper;
import org.springframework.stereotype.Service;

/** 账户信息业务逻辑 */
@Service
public class AccountService {

    private final AccountMapper accountMapper;

    public AccountService(AccountMapper accountMapper) {
        this.accountMapper = accountMapper;
    }

    /** 按用户 ID 查询账户（对应 t_user_account 表） */
    public AccountEntity queryAccount(Long userId) {
        return accountMapper.selectByUserId(userId);
    }
}
```

**mapper/AccountMapper.java**

```java
package com.demo.account.mapper;

import com.demo.account.entity.AccountEntity;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

/** t_user_account 表数据访问 */
@Mapper
public interface AccountMapper {
    AccountEntity selectByUserId(@Param("userId") Long userId);
}
```

**resources/mapper/AccountMapper.xml**（F2 埋点：SELECT * 断链）

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE mapper PUBLIC "-//mybatis.org//DTD Mapper 3.0//EN" "http://mybatis.org/dtd/mybatis-3-mapper.dtd">
<mapper namespace="com.demo.account.mapper.AccountMapper">
  <!-- 历史遗留写法：未维护 resultMap，字段映射依赖隐式约定 -->
  <select id="selectByUserId" resultType="com.demo.account.entity.AccountEntity">
    SELECT * FROM t_user_account WHERE user_id = #{userId}
  </select>
</mapper>
```

**entity/AccountEntity.java**

```java
package com.demo.account.entity;

/** 账户信息实体（对应 t_user_account） */
public class AccountEntity {
    /** 用户唯一标识（与 t_user.user_id 同源） */
    private Long userId;
    /** 账户号 */
    private String accountNo;
    /** 账户余额，业务规则见表注释：余额不可为负 */
    private java.math.BigDecimal balance;
    /** 账户状态：NORMAL/FROZEN/CLOSED */
    private String status;
}
```

**job/ReconcileJob.java**（F4-JOB）

```java
package com.demo.account.job;

import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

/**
 * 每日账户对账定时任务。
 * 启用证据：@Scheduled 注解 + application.yml 的 reconcile.enabled=true；
 * 重试次数取 reconcile.retry-times 配置。
 */
@Component
public class ReconcileJob {

    @Scheduled(cron = "0 0 2 * * ?")
    public void reconcile() {
        // 对账逻辑（fixture 静态样本：实现省略，语义与启用证据见类注释与配置）
    }
}
```

**resources/application.yml**（F5 埋点）

```yaml
server:
  port: 8082
spring:
  application:
    name: account-service
  datasource:
    url: jdbc:mysql://10.20.31.14:3306/demo_account?useSSL=false
    username: acct_admin
    password: Pr0d@Acct#2026
reconcile:
  enabled: true
  retry-times: 3
```

### A.7 order-service 全部文件

**entity/OrderStatus.java**（F3）

```java
package com.demo.order.entity;

/** 订单状态机：CREATED → PAID → SHIPPED → COMPLETED；任意非终态 → CANCELLED */
public enum OrderStatus {
    CREATED("已创建"),
    PAID("已支付"),
    SHIPPED("已发货"),
    COMPLETED("已完成"),
    CANCELLED("已取消");

    private final String label;

    OrderStatus(String label) {
        this.label = label;
    }
}
```

**service/OrderService.java**（F3 状态机+寄生注释；markPaid 显式发事件）

```java
package com.demo.order.service;

import com.demo.order.entity.OrderEntity;
import com.demo.order.entity.OrderStatus;
import com.demo.order.mapper.OrderMapper;
import com.demo.order.mq.OrderEventProducer;
import org.springframework.stereotype.Service;

/** 订单业务逻辑：状态迁移、事件发布与导出 */
@Service
public class OrderService {

    private final OrderMapper orderMapper;
    private final OrderEventProducer orderEventProducer;

    public OrderService(OrderMapper orderMapper, OrderEventProducer orderEventProducer) {
        this.orderMapper = orderMapper;
        this.orderEventProducer = orderEventProducer;
    }

    /**
     * 订单发货：状态机约束——已取消（CANCELLED）的订单不允许再发货；
     * 只有 PAID 状态可以流转到 SHIPPED。
     */
    public void ship(Long orderId) {
        OrderEntity order = orderMapper.selectById(orderId);
        OrderStatus current = OrderStatus.valueOf(order.getStatus());
        if (current == OrderStatus.CANCELLED) {
            throw new IllegalStateException("已取消订单不可发货");
        }
        if (current != OrderStatus.PAID) {
            throw new IllegalStateException("仅已支付订单可发货");
        }
        orderMapper.updateStatus(orderId, OrderStatus.SHIPPED.name());
    }

    /** 订单支付成功回调：CREATED → PAID，并发布订单已支付事件 */
    public void markPaid(Long orderId) {
        orderMapper.updateStatus(orderId, OrderStatus.PAID.name());
        orderEventProducer.sendOrderPaid(orderId);
    }
}
```

**controller/OrderController.java**

```java
package com.demo.order.controller;

import com.demo.order.service.OrderService;
import org.springframework.web.bind.annotation.*;

/** 订单接口：状态流转由 OrderService 状态机约束（已取消订单不可发货） */
@RestController
@RequestMapping("/api/order")
public class OrderController {

    private final OrderService orderService;

    public OrderController(OrderService orderService) {
        this.orderService = orderService;
    }

    @PostMapping("/{orderId}/ship")
    public String ship(@PathVariable("orderId") Long orderId) {
        orderService.ship(orderId);
        return "ok";
    }
}
```

**mq/OrderEventProducer.java**（F4-EVENT 生产）

```java
package com.demo.order.mq;

import org.springframework.amqp.rabbit.core.RabbitTemplate;
import org.springframework.stereotype.Component;

/** 订单事件生产者：订单支付成功后发送 order.paid 事件 */
@Component
public class OrderEventProducer {

    public static final String EXCHANGE = "order.exchange";
    public static final String ROUTING_KEY = "order.paid";

    private final RabbitTemplate rabbitTemplate;

    public OrderEventProducer(RabbitTemplate rabbitTemplate) {
        this.rabbitTemplate = rabbitTemplate;
    }

    public void sendOrderPaid(Long orderId) {
        rabbitTemplate.convertAndSend(EXCHANGE, ROUTING_KEY, "{\"orderId\":" + orderId + "}");
    }
}
```

**mq/OrderEventListener.java**（F4-EVENT 消费）

```java
package com.demo.order.mq;

import org.springframework.amqp.rabbit.annotation.Exchange;
import org.springframework.amqp.rabbit.annotation.QueueBinding;
import org.springframework.amqp.rabbit.annotation.Queue;
import org.springframework.amqp.rabbit.annotation.RabbitListener;
import org.springframework.stereotype.Component;

/** 订单事件监听：消费 order.paid 完成后续处理（通知、积分） */
@Component
public class OrderEventListener {

    @RabbitListener(bindings = @QueueBinding(
            value = @Queue(value = "order.paid.queue", durable = "true"),
            exchange = @Exchange(value = OrderEventProducer.EXCHANGE),
            key = OrderEventProducer.ROUTING_KEY))
    public void onOrderPaid(String message) {
        // 支付后处理（fixture 静态样本）
    }
}
```

**service/ExportService.java**（F7）

```java
package com.demo.order.service;

import org.springframework.stereotype.Service;

/** 订单导出服务：导出文件保留 7 天后清理 */
@Service
public class ExportService {

    /** 导出文件保留期（天）。历史 bug：曾误配 30 天，经修复回归 7 天。 */
    public static final int RETENTION_DAYS = 7;
}
```

**controller/ExportController.java**

```java
package com.demo.order.controller;

import org.springframework.web.bind.annotation.*;

/** 订单导出接口：文件保留 7 天（ExportService.RETENTION_DAYS） */
@RestController
@RequestMapping("/api/order/export")
public class ExportController {

    @PostMapping
    public String export() {
        return "taskId";
    }
}
```

**mapper/OrderMapper.java 与 resources/mapper/OrderMapper.xml**

```java
package com.demo.order.mapper;

import com.demo.order.entity.OrderEntity;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

/** t_order 表数据访问 */
@Mapper
public interface OrderMapper {
    OrderEntity selectById(@Param("orderId") Long orderId);
    int updateStatus(@Param("orderId") Long orderId, @Param("status") String status);
}
```

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE mapper PUBLIC "-//mybatis.org//DTD Mapper 3.0//EN" "http://mybatis.org/dtd/mybatis-3-mapper.dtd">
<mapper namespace="com.demo.order.mapper.OrderMapper">
  <select id="selectById" resultType="com.demo.order.entity.OrderEntity">
    SELECT order_id AS orderId, user_id AS userId, status, amount FROM t_order WHERE order_id = #{orderId}
  </select>
  <update id="updateStatus">
    UPDATE t_order SET status = #{status} WHERE order_id = #{orderId}
  </update>
</mapper>
```

**entity/OrderEntity.java**

```java
package com.demo.order.entity;

/** 订单实体（对应 t_order） */
public class OrderEntity {
    private Long orderId;
    /** 下单用户 ID，与 t_user.user_id 同源 */
    private Long userId;
    /** 订单状态，取值见 OrderStatus 枚举 */
    private String status;
    private java.math.BigDecimal amount;
}
```

**resources/application.yml**

```yaml
server:
  port: 8083
spring:
  application:
    name: order-service
  rabbitmq:
    host: mq.internal.demo.local
    username: order_mq
    password: Mq_2026_Order
```

**src/test/java/com/demo/order/OrderServiceTest.java**（F3 行为规格）

```java
package com.demo.order;

import com.demo.order.entity.OrderEntity;
import com.demo.order.entity.OrderStatus;
import com.demo.order.mapper.OrderMapper;
import com.demo.order.mq.OrderEventProducer;
import com.demo.order.service.OrderService;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

/** 订单状态机行为规格（测试即规格） */
class OrderServiceTest {

    /** 业务规则：已取消订单不可发货（桩返回 CANCELLED 订单） */
    @Test
    void cancelledOrderCannotShip() {
        OrderMapper stub = new OrderMapper() {
            @Override public OrderEntity selectById(Long id) {
                OrderEntity o = new OrderEntity();
                o.setOrderId(id);
                o.setStatus(OrderStatus.CANCELLED.name());
                return o;
            }
            @Override public int updateStatus(Long id, String status) { return 1; }
        };
        OrderService service = new OrderService(stub, new OrderEventProducer(null));
        assertThrows(IllegalStateException.class, () -> service.ship(1L));
    }
}
```

（注：fixture 为静态阅读样本，OrderEntity 的 setter 以注释形态存在即可："fixture 静态样本：标准 getter/setter 略"。）

### A.8 web-portal 全部文件

**package.json**

```json
{
  "name": "web-portal",
  "version": "1.0.0",
  "scripts": { "dev": "vite", "build": "vite build" },
  "dependencies": { "vue": "^3.4.0", "vue-router": "^4.3.0", "axios": "^1.6.0" },
  "devDependencies": { "vite": "^5.2.0" }
}
```

**vite.config.js**

```javascript
import { defineConfig } from 'vite'
export default defineConfig({
  server: { proxy: { '/api': { target: 'http://localhost:8080', changeOrigin: true } } }
})
```

**src/main.js**

```javascript
import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import App from './App.vue'
import UserList from './views/UserList.vue'
import OrderPage from './views/OrderPage.vue'
import AccountPage from './views/AccountPage.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/users', component: UserList },
    { path: '/orders', component: OrderPage },
    { path: '/accounts', component: AccountPage }
  ]
})
createApp(App).use(router).mount('#app')
```

**src/App.vue**

```vue
<template><router-view /></template>
```

**src/api/request.js**

```javascript
import axios from 'axios'
// 统一请求封装：baseURL 走 vite 代理转发到后端网关
const request = axios.create({ baseURL: '/api', timeout: 10000 })
export default request
```

**src/api/index.js**

```javascript
import request from './request'
export const queryUserBasic = (userId) => request.get(`/user/basic/${userId}`)
export const queryAccount = (userId) => request.get(`/account/${userId}`)
export const shipOrder = (orderId) => request.post(`/order/${orderId}/ship`)
export const exportOrder = () => request.post('/order/export')
```

**src/views/UserList.vue**

```vue
<template>
  <div>
    <h2>用户列表</h2>
    <div v-for="u in users" :key="u.userId">{{ u.userName }}（{{ u.mobile }}）</div>
    <button @click="load">查询用户信息</button>
  </div>
</template>
<script setup>
import { ref } from 'vue'
import { queryUserBasic } from '../api'
const users = ref([])
const load = async () => { users.value = [await queryUserBasic(1)] }
</script>
```

**src/views/OrderPage.vue**

```vue
<template>
  <div>
    <h2>订单管理</h2>
    <button @click="ship">发货</button>
    <button @click="exportAll">导出订单</button>
  </div>
</template>
<script setup>
import { shipOrder, exportOrder } from '../api'
const ship = async () => { await shipOrder(1) }
const exportAll = async () => { await exportOrder() }
</script>
```

**src/views/AccountPage.vue**

```vue
<template>
  <div>
    <h2>账户查询</h2>
    <div v-if="acct">账户号：{{ acct.accountNo }} 余额：{{ acct.balance }}</div>
    <button @click="load">查询账户</button>
  </div>
</template>
<script setup>
import { ref } from 'vue'
import { queryAccount } from '../api'
const acct = ref(null)
const load = async () => { acct.value = await queryAccount(1) }
</script>
```

### A.9 db/init.sql

```sql
-- demo 商城 DDL（4 表，三库归属）
CREATE DATABASE IF NOT EXISTS demo_user;
USE demo_user;
CREATE TABLE t_user (
  user_id   BIGINT PRIMARY KEY COMMENT '用户唯一标识',
  user_name VARCHAR(64)  NOT NULL COMMENT '用户姓名',
  mobile    VARCHAR(20)  COMMENT '手机号',
  email     VARCHAR(128) COMMENT '邮箱',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
) COMMENT='用户基本信息表';

CREATE DATABASE IF NOT EXISTS demo_account;
USE demo_account;
-- F6 埋点：业务规则在表注释
CREATE TABLE t_user_account (
  id         BIGINT PRIMARY KEY COMMENT '主键',
  user_id    BIGINT NOT NULL COMMENT '用户唯一标识，同 t_user.user_id',
  account_no VARCHAR(32) NOT NULL COMMENT '账户号',
  balance    DECIMAL(18,2) NOT NULL DEFAULT 0 COMMENT '账户余额；业务规则：余额不可为负',
  status     VARCHAR(16) NOT NULL DEFAULT 'NORMAL' COMMENT '账户状态：NORMAL/FROZEN/CLOSED',
  UNIQUE KEY uk_account_no (account_no)
) COMMENT='用户账户表；本表余额字段不允许出现负值（业务硬约束）';

CREATE DATABASE IF NOT EXISTS demo_order;
USE demo_order;
CREATE TABLE t_order (
  order_id  BIGINT PRIMARY KEY COMMENT '订单号',
  user_id   BIGINT NOT NULL COMMENT '下单用户，同 t_user.user_id',
  status    VARCHAR(16) NOT NULL COMMENT '订单状态：CREATED/PAID/SHIPPED/COMPLETED/CANCELLED',
  amount    DECIMAL(18,2) NOT NULL COMMENT '订单金额',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
) COMMENT='订单表；状态迁移受 OrderService 状态机约束';

-- F7 语境
CREATE TABLE t_export_file (
  id         BIGINT PRIMARY KEY COMMENT '主键',
  order_id   BIGINT COMMENT '关联订单',
  file_path  VARCHAR(256) COMMENT '导出文件路径',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '导出时间；保留 7 天后清理'
) COMMENT='订单导出文件登记表';
```

### A.10 user-input-template/（八文件；占位符由容器内 prepare 渲染）

**base-info.md**

````markdown
# 基础信息

## 基线信息

- 项目名称：demo 商城系统
- 分析目标：建立 Schema 4.0 知识库

## 工程信息

- 状态：全量
- 资料：[工程范围](./project-scope.md)

## 数据模型

- 状态：全量
- 资料：[数据模型范围](./data-model-scope.md)

## 配置

- 状态：全量
- 资料：[配置范围](./configuration-scope.md)

## 中间件

- 状态：全量
- 资料：[中间件范围](./middleware-scope.md)

## 接口

- 状态：全量
- 资料：[接口范围](./api-scope.md)

## 页面

- 状态：全量
- 资料：[页面范围](./page-scope.md)

## 业务知识证据（可选）

本章节可整体省略：缺失时初始化正常继续。

```yaml
test_sources:
  - "**/src/test/**"
adr_sources: []
git_history:
  enabled: true
  range: "{{REPO_INIT}}..HEAD"
```
````

**project-scope.md**

```markdown
# 工程范围

- 状态：全量

## 工程清单

| 工程标识 | 本地路径 | Git 仓库 | 工程类型 | 纳入分析 |
|---------|---------|----------|----------|----------|
| user-service | ./user-service | 本仓库（单仓多模块） | Java 后端 | 是 |
| account-service | ./account-service | 本仓库 | Java 后端 | 是 |
| order-service | ./order-service | 本仓库 | Java 后端 | 是 |
| web-portal | ./web-portal | 本仓库 | Vue3 前端 | 是 |
```

**data-model-scope.md**

```markdown
# 数据模型范围

- 状态：全量

## 数据库与结构证据

| 数据库 | Schema | 结构证据（工程根相对路径） |
|--------|--------|---------------------------|
| demo_user | - | ./db/init.sql（DDL）、./user-service/src/main/resources/mapper/UserMapper.xml |
| demo_account | - | ./db/init.sql、./account-service/src/main/resources/mapper/AccountMapper.xml |
| demo_order | - | ./db/init.sql、./order-service/src/main/resources/mapper/OrderMapper.xml |
```

**configuration-scope.md**

```markdown
# 配置范围

- 状态：全量

## 基线快照

| 项目 | 值 |
|------|-----|
| snapshot_id | baseline-config-v1 |
| 环境 | 开发（fixture 本地快照） |
| 发布批次 | fixture-batch-001 |
| 外部目录（只读） | {{SNAPSHOT_DIR}} |
| 获取时间 | 由 runner 生成 |
| 来源类型 | 工作区配置导出快照（锁定） |
| 最终快照指纹 | {{FINGERPRINT}} |

## 范围摘要

- scope_summary：三服务 application.yml 全量纳入（3 文件）
- 纳入文件数：3
- 服务摘要：user-service、account-service、order-service
- 文件规则摘要：仅 src/main/resources/application.yml
```

**middleware-scope.md**

```markdown
# 中间件范围

- 状态：全量

## 中间件清单

| 中间件 | 用途 | 使用方 |
|--------|------|--------|
| MySQL | 三业务库存储 | 三服务 |
| RabbitMQ | 订单事件 | order-service |
```

**api-scope.md**

```markdown
# 对外能力清单与 API 执行范围

## 执行范围

- 模式：全量
- 指定能力：无

## 对外能力清单

| 标识 | 能力名称 | API 名称或逻辑标识 | 能力类型 | 版本 | 状态 | 调用方 | 落地方 | 备注 |
|------|----------|---------------------|----------|------|------|--------|--------|------|
| API-user-basic | 查询用户基本信息 | queryBasic | REST API | v1 | 使用中 | 客户端 | user-service |  |
| API-order-export | 订单导出 | export | REST API | v1 | 使用中 | 客户端 | order-service |  |

## 能力组合诉求（可选）

> 组合能力实体的用户权威输入：声明后由 knowledge-base-api 核实输入契约与连接键证据、knowledge-base-overview 生成 CAP 实体。未声明时不生成组合实体。

| 目标能力名 | 期望输出字段 | 来源能力 | 连接键 | 声明依据 |
|-----------|-------------|---------|--------|----------|
| 全部用户信息 | 用户基本信息+账户信息 | API-user-basic；对内 REST GET /api/account/{userId}（account-service，预期登记为对内能力） | userId | 业务需求：对外统一提供用户全景 |

## 能力类型参考

- REST API
- 消息生产
- 消息消费
- 定时任务
```

**page-scope.md**

```markdown
# 页面范围

- 状态：全量

## 前端应用清单

| 应用 | 路径 | 路由来源 |
|------|------|----------|
| web-portal | ./web-portal | 代码静态路由（src/main.js） |
```

**product.md**（variant-full 独有）

```markdown
# 产品信息（可选输入）

## 产品目的

为商城运营方提供用户、账户与订单的统一管理能力。

## 目标用户

内部运营人员。

## 关键特性

- 用户信息查询
- 账户查询
- 订单管理与导出

## 业务目标

未提供
```

### A.11 change-package-F9/（五文件）

**change-summary.md**

```markdown
# 变更摘要

## 基本信息

- 变更标识：CHANGE-F9-REMOVE-ACCOUNT-API
- 变更目的：下线账户查询端点（业务迁移至新网关）
- 目标环境：开发
- 涉及服务：account-service
- 业务影响：依赖该端点的组合能力需要重新评估
- 风险：聚合能力断链

## 领域变更矩阵

| 领域 | 变更状态 | 摘要或无变更判断依据 |
|------|----------|----------------------|
| 代码 | 有变更 | 删除 AccountController 与 AccountService、AccountPage 改提示页、api/index.js 移除调用 |
| 数据模型 | 无变更 | 未触及表结构，DDL 与 Entity 无改动 |
| 配置 | 无变更 | application.yml 未改动 |
| 中间件 | 无变更 | 未触及 RabbitMQ/MySQL 依赖 |
| 接口 | 有变更 | 对内 REST 端点 GET /api/account/{userId} 删除 |
| 页面 | 有变更 | AccountPage.vue 改写为提示页（移除调用） |
| 业务知识 | 有变更 | 组合能力 CAP 输入失效，需重算 |

## 关联说明

- 负责人或确认人：fixture 维护者
```

**code-change.md**

```markdown
# 代码变更

- MR：本地模拟（无平台 MR）
- 源分支：main，目标分支：main
- 起始提交：F9_BASE，结束提交：F9_HEAD（runner apply-f9 替换为实际值）
- 修改工程：account-service、web-portal
- 修改文件与符号：删除 AccountController.java、删除 AccountService.java、AccountPage.vue 改写为提示页、api/index.js 移除 queryAccount 导出行
- 代码变更说明：下线账户查询端点、服务层与前端调用（页面保留并改为提示页，路由不悬空）
- 本地可验证范围：git diff 与文件级核对
```

**database-change.md**

```markdown
# 数据库变更

- 状态：无变更
- 判断依据：本次变更未触及 DDL、迁移脚本与 Entity/Mapper（t_user_account 相关代码仅查询端点下线，表结构无改动）
```

**configuration-change.md**

```markdown
# 配置变更

- 状态：无变更
- 判断依据：三服务 application.yml 均无改动（git diff 可验证）；配置范围为全量，基线快照未变
```

**verification.md**

```markdown
# 验证记录

- 验证方式：静态核对（fixture 为静态样本，无可运行验证）
- 验证结果：文件删除与调用清理一致；无残留前端调用
```
