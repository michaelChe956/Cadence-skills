# RuoYi-Cloud-Plus Knowledge Base

**Generated:** 2026-07-03
**Version:** 6.0.0-BETA

## OVERVIEW

RuoYi-Cloud-Plus is a Java 21 microservice management system built on Spring Boot 4.1 + Spring Cloud 2025. It uses Maven multi-module architecture with Nacos for service discovery/config, Sa-Token for auth, MyBatis-Plus for ORM, and Dubbo for RPC.

## STRUCTURE

```
market-cloud/
├── pom.xml                       # Parent POM (flatten-maven-plugin for ${revision})
├── ruoyi-auth/                   # Auth service (port 9210)
├── ruoyi-gateway/                # Spring Cloud Gateway (port 8080)
├── ruoyi-visual/                 # Visualization layer
│   ├── ruoyi-monitor/            # Spring Boot Admin monitoring (port 9100)
│   ├── ruoyi-snailai-server/     # AI Agent chat server (port 8900)
│   └── ruoyi-snailjob-server/    # Distributed job scheduler (port 8800)
├── ruoyi-modules/                # Business service modules
│   ├── ruoyi-system/             # System management (port 9201)
│   ├── ruoyi-gen/                # Code generator (port 9202)
│   ├── ruoyi-job/                # Job scheduling (port 9203)
│   ├── ruoyi-resource/           # Resources/OSS (port 9204)
│   ├── ruoyi-workflow/           # Workflow engine (port 9205)
│   ├── ruoyi-ai/                 # AI integration (port 9206)
│   └── ruoyi-ops/                # Operations
├── ruoyi-api/                    # Shared API contracts (Feign interfaces + DTOs)
│   ├── ruoyi-api-system/
│   ├── ruoyi-api-resource/
│   ├── ruoyi-api-workflow/
│   ├── ruoyi-api-ops/
│   └── ruoyi-api-bom/
├── ruoyi-common/                 # Shared utility library (30+ modules)
│   ├── ruoyi-common-core/        # Base exceptions, utils, i18n
│   ├── ruoyi-common-security/    # Sa-Token integration
│   ├── ruoyi-common-web/         # Web MVC config, filters
│   ├── ruoyi-common-mybatis/     # MyBatis-Plus config, handlers
│   ├── ruoyi-common-redis/       # Redis/Redisson config
│   ├── ruoyi-common-dubbo/       # Dubbo RPC config
│   ├── ruoyi-common-log/         # Log annotation + aspect
│   ├── ruoyi-common-satoken/     # Sa-Token config
│   └── ... (30+ more)
├── ruoyi-example/                # Demo/test modules
│   ├── ruoyi-demo/
│   └── ruoyi-test-mq/
└── script/                       # Deployment infrastructure
    ├── docker/                   # Docker Compose + Dockerfiles
    ├── k8s/                      # Kubernetes manifests
    ├── sql/                      # DB schemas (MySQL/Oracle/Postgres)
    └── config/                   # Nacos/Grafana configs
```

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| Add new business module | `ruoyi-modules/ruoyi-{name}/` | Copy ruoyi-system structure |
| Add shared utility | `ruoyi-common/ruoyi-common-{name}/` | Add to ruoyi-common-bom |
| Add Feign API contract | `ruoyi-api/ruoyi-api-{name}/` | Add to ruoyi-api-bom |
| Auth logic | `ruoyi-auth/` + `ruoyi-common-security/` | Sa-Token based |
| DB schema changes | `script/sql/` | MySQL + Oracle + Postgres variants |
| Deploy locally | `script/docker/docker-compose.yml` | Full stack: MySQL, Redis, Nacos, etc. |
| K8s deployment | `script/k8s/` | Infrastructure + services manifests |
| Config changes | `script/config/nacos/` | Per-service Nacos YAML configs |
| Add new service port | Check `docker-compose.yml` | Ports 9201-9206 assigned |

## CONVENTIONS

- **Package namespace:** `org.dromara.{module}` (e.g., `org.dromara.system`, `org.dromara.auth`)
- **Version management:** `${revision}` property + `flatten-maven-plugin` — never hardcode versions in child POMs
- **BOM pattern:** Each layer has a BOM (`ruoyi-common-bom`, `ruoyi-api-bom`, `ruoyi-common-alibaba-bom`) — add new deps there
- **Config per environment:** Maven profiles `dev`/`prod` activate via `-Pprod`
- **Tests skipped by default:** `maven.test.skip=true` in root POM
- **Annotation processors:** Lombok + MapStruct Plus + Spring Boot Config Processor — IDE must enable annotation processing
- **Code style:** 4-space indent (2 for YAML/JSON), LF line endings, UTF-8 (see `.editorconfig`)
- **i18n:** `ruoyi-common-core/src/main/resources/i18n/messages_{locale}.properties`

## ANTI-PATTERNS

- Never hardcode version numbers in child POMs — use `${revision}` or BOM
- Never add business logic to `ruoyi-common` — it's shared infrastructure only
- Never modify `ruoyi-api` without updating all dependent modules
- Never commit `target/` directories — already gitignored
- Never use `fastjson` for new code — it's only for backward compat (security workaround)

## COMMANDS

```bash
# Build (skip tests - default)
mvn clean package

# Build with tests
mvn clean package -Dmaven.test.skip=false

# Build specific module
mvn clean package -pl ruoyi-modules/ruoyi-system -am

# Run locally (requires Docker infrastructure)
docker-compose -f script/docker/docker-compose.yml up -d

# Deploy to K8s
kubectl apply -f script/k8s/base/
kubectl apply -f script/k8s/infrastructure/
kubectl apply -f script/k8s/services/
```

## NOTES

- **Java 21 required** — uses virtual threads and record patterns
- **Spring Boot 4.1** — requires Jakarta EE namespace (not javax)
- **Nacos v3.2.2** — config center + service discovery; configs in `script/config/nacos/`
- **Port assignments:** Gateway=8080, Auth=9210, System=9201, Gen=9202, Job=9203, Resource=9204, Workflow=9205, AI=9206
- **SkyWalking** — all services mount `/docker/skywalking/agent` for APM
- **Seata** — distributed transactions (port 8091)
- **SnailJob** — distributed job scheduler with SnailAI agent integration

<!-- cadence-managed:openspec-superpowers-routing:v1:start -->
## OpenSpec 与 Superpowers 任务路由（强制）

> 先通过客户端原生机制选择 `using-superpowers` 与当前阶段必调 Skill；首个用户可见段落输出路由回执；Skill 调用完成后才允许读取仓库规则或使用仓库工具。

| 任务或阶段信号 | 必读规则 | 必调 Superpowers Skill | 门禁 |
|---|---|---|---|
| 会话开始且任务需要仓库操作，或 resume/clear/compact 后恢复仓库任务 | `openspec-superpowers-workflow.md` | `using-superpowers` | 原生调用 Skill 后，第一段输出完整路由回执 |
| 新功能、行为变化、方案讨论 | 协作规则；产物相关文档规则 | `using-superpowers` → `brainstorming` | 设计确认后写入 OpenSpec |
| OpenSpec 书面契约获批 | 协作规则、文档规则 | `using-superpowers` → `writing-plans` | Plan 写入 `cadence/plans/` |
| 读代码、架构摸底、影响面分析 | `code-reading.md` | `using-superpowers` → 按任务选择 | 摸底完成后重新路由 |
| Bug、测试失败、异常行为 | `code-usage.md` | `using-superpowers` → `systematic-debugging` | 根因确认后才进入 TDD |
| `/opsx:apply` 或恢复实施 | 协作规则、代码规则 | 无 Plan：`using-superpowers` → `writing-plans`；有 Plan：→ `executing-plans` 或 `subagent-driven-development` | 无已确认 Plan 则停止 |
| 写代码、修 Bug、重构 | `code-usage.md` | `using-superpowers` → `test-driven-development` | 先失败测试，后实现 |
| 写 Markdown 或 Cadence 产物 | `document-storage.md`、`markdown-format.md` | `using-superpowers` → 按阶段选择 | 遵守目录和命名 |
| 联网、图片、浏览器自动化 | `mcp-servers.md` 或专项规则 | `using-superpowers` → 按任务选择 | 不加载无关工具正文 |
| 声称完成、修复或通过 | 协作规则 | `using-superpowers` → `verification-before-completion` | 必须读取新鲜证据 |
| 实施与验证均完成 | 协作规则 | `using-superpowers` → `requesting-code-review` | 审查通过后勾选工作包并 sync/archive |
| OpenSpec 已归档 | 协作规则 | `using-superpowers` → `finishing-a-development-branch` | 选择分支集成方式 |

`knowledge-base-context` 选择前置门禁：仅当只读确认 `cadence/knowledge-base/manifest.yaml` 存在且 `schema_version` 为 `"4.0"` 时才可选择；Manifest 缺失或版本不符时不得选择、调用或读取该 Skill，不输出知识库相关提示，按普通流程继续。

阶段切换必须重新路由：新仓库任务、讨论、分析或只读调查转为创建/修改文件、契约获批、apply 前、resume/clear/compact 后、完工声明前。
需要仓库操作时：Claude/Kimi 必须把全部 Skill 调用及失败重试作为连续工具事件；首个调用前、事件之间和重试前均保持用户可见输出静默，禁止输出“我先调用 Skill”等引导句；随后第一段输出 `工作流路由：阶段=...；Change=...；Plan=...；必调 Skill=...`。Codex 先显式选择 Skill，将用途并入首段回执，随后立即全文读取 Skill。pi 与 Codex 同类：从 Skill 清单显式选择 Skill，将用途并入首段回执，随后立即全文读取对应 SKILL.md 作为调用，Skill 未读完前不得读取仓库规则或使用仓库工具。Skill 调用完成后才读取仓库规则和使用仓库工具。
纯概念问答只调用全局 `using-superpowers` 后直接回答，不输出仓库路由回执，不加载仓库规则或其他无关 Skill；Codex/pi 可先输出 Skill 用途公告。一旦转为仓库操作，必须重新路由。
需要仓库勘察的新功能或行为变化，必须先原生调用 `using-superpowers`、`brainstorming`，再输出回执；回执必须先于 change、Plan、目录或文件勘察，澄清问题不得替代回执。
Claude/Kimi 的 Skill 参数使用表中不带命名空间的原名；pi 以全文读取对应 SKILL.md 作为 Skill 调用；调用失败必须按客户端已注册清单重试，未成功加载则失败关闭。
失败关闭本身也属于当前阶段动作，不能用“只判断/只拒绝”豁免 Skill：无 Plan 时先调用 `using-superpowers`、`writing-plans` 再拒绝 apply；即使禁止运行验证命令，也必须先调用 `using-superpowers`、`verification-before-completion` 加载验证纪律，再拒绝无证据完成声明；其他必调 Skill 未加载则停止。
<!-- cadence-managed:openspec-superpowers-routing:v1:end -->

## 项目个性化规则（强制规则）

> **🔴 必须遵守 - 无例外**

- **用户自定义规则只能存放在 `cadence/project-rules/` 目录**
- 禁止在 `rules/` 目录中添加用户自定义规则
- 禁止直接修改 `rules/` 目录下的框架内置规则文件
- 详见 `cadence/project-rules/README.md`

## 项目配置

> 以下内容由初始化脚本根据项目环境自动检测生成，非通用规则。

### 项目技术栈
- **语言**：未检测到
- **包管理器**：未检测到
- **测试命令**：未检测到
- **检查命令**：未检测到
- **格式化命令**：未检测到
- **覆盖率阈值**：80%
