# KnowledgeBase 通用 Demo 与页面 API 关联实施计划

> **执行要求**：按任务顺序内联执行，每个任务完成后运行对应静态检查，再进入下一任务。

**目标**：将 KnowledgeBase API 案例完整改造成不含真实项目特征的通用订单案例，并让页面案例、模板和 Skill 明确关联接口知识库中的 REST API 主文件。

**实现方式**：统一使用虚构的订单管理领域作为跨 Skill 案例，保留 API 主文件全部 11 节以及参数、报文、调用链、数据库、中间件和证据维度。页面分析以接口知识库为匹配基准，记录稳定 API ID、HTTP 方法、标准路径、调用位置和接口主文件链接；无法匹配的调用使用候选 ID。

**技术栈**：Markdown、YAML Frontmatter、ripgrep 静态检查、Git。

## 全局约束

- API Demo 保留现有完整分析深度，不缩减为简单 REST 示例。
- Demo 不包含活动中心、真实组织、内部域名、内部 IP、真实包名、真实库表或其他项目专属内容。
- 数据库结论仅来自用户 DDL 和代码证据，不要求或暗示连接数据库。
- 页面使用的 API 必须关联 `cadence/knowledge-base/interfaces/` 下的接口主文件。
- 未匹配 API 使用 `API-CANDIDATE-*`，不得根据按钮名称或页面文案补造接口。
- 其他 Demo 只做跨案例 ID 一致性检查，不进行无关重写。

---

### 任务 1：通用化 API 主 Demo

**文件：**

- 修改：`cadence-init/skills/knowledge-base-api/references/demo.md`

**验收接口：**

- 产出：`API-order-page` 订单分页查询完整案例。
- 供下游使用：Pages Demo 引用的稳定 API ID、方法、路径和接口主文件名。

- [ ] 保留 11 节结构及每节现有分析维度。
- [ ] 替换为虚构订单服务、网关、RPC、Redis、消息、本地缓存、定时任务和数据库证据。
- [ ] 明确对外清单与代码入口的映射关系。
- [ ] 明确示例证据均为虚构路径，实际执行必须以用户资料和工程代码为准。
- [ ] 检查无活动中心及真实环境残留。

### 任务 2：通用化参数与报文 Demo

**文件：**

- 修改：`cadence-init/skills/knowledge-base-api/references/demo_参数与报文.md`

**验收接口：**

- 消费：任务 1 的 `API-order-page`、`POST /api/admin/orders/query` 和主文件名。
- 产出：完整输入参数、输出参数、请求示例、响应示例和错误载荷。

- [ ] 使用订单分页、筛选和状态字段替换活动查询字段。
- [ ] 保留嵌套对象、数组、条件字段、长度格式和字段来源示范。
- [ ] 补齐请求、响应和错误报文，不使用“参考附录”代替示例。
- [ ] 检查与主 Demo 的名称、ID、路径和模型一致。

### 任务 3：增强 Pages Demo 与模板

**文件：**

- 修改：`cadence-init/skills/knowledge-base-pages/references/demo.md`
- 修改：`cadence-init/skills/knowledge-base-pages/references/page-analysis-guide.md`
- 修改：`cadence-init/skills/knowledge-base-pages/assets/page-capabilities-template.md`

**验收接口：**

- 消费：`cadence/knowledge-base/interfaces/README.md` 和接口主文件。
- 产出：`ROUTE → PAGE → API → SERVICE/MODULE → TABLE/MIDDLEWARE` 可导航关系。

- [ ] 页面/API 映射包含 API ID、分类、HTTP 方法、标准路径、调用位置、请求封装、接口主文件、后端服务、数据实体、状态、可信度和证据。
- [ ] Vue 案例关联 `API-order-page`，并展示同页多接口。
- [ ] React 案例展示经 Hook 或 Store 的间接 API 调用。
- [ ] 未登记接口展示 `API-CANDIDATE-*` 和待补录状态。
- [ ] 使用相对链接示范接口主文件导航。

### 任务 4：强化 Pages Skill 契约

**文件：**

- 修改：`cadence-init/skills/knowledge-base-pages/SKILL.md`

**验收接口：**

- 产出：接口匹配顺序、链接要求、候选处理和完成条件。

- [ ] 要求先读取接口索引，再读取匹配的接口主文件。
- [ ] 要求规范化 baseURL、代理、BFF 和动态路径后匹配 Method + Path。
- [ ] 要求页面文档中的 API ID 链接到接口主文件。
- [ ] 无法唯一匹配时列出候选，不生成虚假链接。

### 任务 5：全仓验证与提交

**检查范围：**

- `cadence-init/skills/**/references/demo*.md`
- 本计划涉及的 Skill 和模板文件。

- [ ] 检查活动中心、组织域名、内部 IP、真实包名和真实库名残留为 0。
- [ ] 检查 API 主 Demo 11 个一级章节完整。
- [ ] 检查参数报文五个章节完整且 JSON 有效。
- [ ] 检查 Pages Demo 和模板包含接口主文件链接与候选规则。
- [ ] 检查其他 Demo 无项目专属内容，跨 Demo 的订单 API ID 一致。
- [ ] 检查 Markdown 格式和 Git Diff。
- [ ] 提交并推送到当前分支。
