# KnowledgeBase 对外与对内 API Demo 拆分实施计划

> **执行要求**：在当前会话内按顺序执行，每完成一套 Demo 后立即进行结构与分类检查。

**目标**：把 KnowledgeBase API 参考案例拆分成独立的对外 API 和对内 REST 两套完整 Demo，避免页面接口案例覆盖对外能力分析语义。

**实现方式**：现有 `demo.md` 与 `demo_参数与报文.md` 固定为对外能力案例，展示用户清单、开放网关、协议转换或 Provider、内部调用链和数据副作用；现有订单管理 REST 案例迁移为 `demo_对内REST.md` 与配套参数报文。API Skill 和分析指南明确两套案例的选择条件，Pages Demo 只引用对内 REST 案例。

**技术栈**：Markdown、YAML Frontmatter、ripgrep、jq、Git。

## 全局约束

- 对外能力分类只能来自用户提供的对外能力清单。
- 工程扫描发现但未登记的页面 REST、服务间 REST 等能力归为对内。
- 对外 Demo 和对内 REST Demo 均保留完整 11 节主文件结构。
- 两套 Demo 使用不同稳定 API ID、路径、调用方和入口模型。
- Demo 不包含真实组织、内部域名、内部 IP、真实包名、真实库表或项目专属内容。
- Pages Demo 主要关联对内 REST；只有代码证明页面实际调用对外 API 时才允许关联对外能力。

---

### 任务 1：迁移对内 REST Demo

**文件：**

- 创建：`cadence-init/skills/knowledge-base-api/references/demo_对内REST.md`
- 创建：`cadence-init/skills/knowledge-base-api/references/demo_对内REST_参数与报文.md`

**产出契约：**

- 稳定 ID：`API-order-page`
- 分类：对内
- 入口：`POST /api/admin/orders/query`
- 调用链：`PAGE → 请求封装 → 内部网关 → Controller → Service → 数据与中间件`

- [ ] 将当前订单分页查询主 Demo 完整迁移到对内 REST 文件。
- [ ] 将当前订单参数与报文完整迁移到对内 REST 配套文件。
- [ ] 更新两个文件之间的相互引用，不再占用默认对外 Demo 文件名。
- [ ] 验证主文件 11 节与参数文件 5 节完整。

### 任务 2：重建对外 API Demo

**文件：**

- 修改：`cadence-init/skills/knowledge-base-api/references/demo.md`
- 修改：`cadence-init/skills/knowledge-base-api/references/demo_参数与报文.md`

**产出契约：**

- 稳定 ID：`API-partner-order-query`
- 分类：对外
- 入口：`POST /openapi/order-center/partnerOrderQuery/v1`
- 调用链：`外部合作方 → 开放网关 → 协议转换或 Provider → 内部服务 → 数据与中间件`

- [ ] 明确该能力登记在 `api-scope.md`，所以保持对外分类。
- [ ] 保留主文件 11 节，覆盖网关映射、Provider、分支、数据库、缓存、消息、搜索、RPC、HTTP 和定时任务。
- [ ] 参数文件包含公共报文头、业务请求、业务响应、请求示例、响应示例和错误载荷。
- [ ] 使用虚构订单合作方查询案例，不复用对内页面 REST 的鉴权和入口模型。

### 任务 3：明确 Skill 与指南选择规则

**文件：**

- 修改：`cadence-init/skills/knowledge-base-api/SKILL.md`
- 修改：`cadence-init/skills/knowledge-base-api/references/api-analysis-guide.md`
- 修改：`cadence-init/skills/knowledge-base-pages/SKILL.md`
- 修改：`cadence-init/skills/knowledge-base-pages/references/demo.md`
- 修改：`cadence/plans/2026-07-16_计划文档_Skill优化_KnowledgeBase通用Demo与页面API关联_v1.0.md`

**产出契约：**

- 对外能力读取默认 `demo.md` 套件。
- 对内前端 REST 读取 `demo_对内REST.md` 套件。
- Pages Demo 明确 `API-order-page` 来源于对内 REST 案例。

- [ ] 在必读资源中分别列出对外和对内 REST 两套 Demo。
- [ ] 增加对外 API 与对内 REST 的分类依据、调用方、入口和页面关联对照表。
- [ ] 禁止根据 Controller 或页面调用把未登记能力升级为对外。
- [ ] Pages Demo 说明页面通常关联对内 REST，而不是默认关联开放平台 API。

### 任务 4：验证、提交和推送

- [ ] 两套主文件均为 11 节，两套参数文件均为 5 节。
- [ ] 对外 Demo 包含 `分类：对外` 和对外清单证据。
- [ ] 对内 REST Demo 包含 `分类：对内` 和未登记证据。
- [ ] API Skill 和指南包含双 Demo 路由规则。
- [ ] Pages Demo 的 `API-order-page` 与对内 REST Method + Path 一致。
- [ ] 所有 JSON 示例通过 `jq` 解析。
- [ ] 项目专属关键词扫描结果为 0。
- [ ] Skill 快速校验和 `git diff --check` 通过。
- [ ] 提交并推送到当前分支。
