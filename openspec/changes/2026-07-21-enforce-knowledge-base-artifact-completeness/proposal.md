## Why

一次真实的 KnowledgeBase 初始化（1340 文件产物）在 `global_validation: passed` 的情况下出厂，但产物存在五类内容缺失，根因是共性的：**assets/references 模板写得完整，而各 Skill 的完成条件与 global-validation 验收清单没有把模板关键产物列为强制验收项**，执行 Agent 跳过模板也不会失败。已核实证据：

1. API 文档未按模板：`interfaces/` 下 4 个接口只有自创 6 小节主文件，未遵循 11 节模板；请求响应能力必需的 `_参数与报文.md` 配套文件 0 个，完整字段表与报文示例全部丢失。
2. 未生成对内 REST：`interfaces/README.md` 无"对内能力"分区；指定模式豁免盘点后，没有任何 Skill 负责为页面用到的后端 REST 生成对内文档（前端 305/383 个能力编码无文档）。
3. 配置信息丢失：来源文件 587 个唯一配置键，生成的 `CONF-bss.md` 仅收录 27 个（丢失约 95%），10 节模板被 5 个自创小节替代，41 个敏感键只写总数。
4. pages 未按路由深挖：用户点名 2 条菜单，产物只有 6 个应用级概览，0 个 `PAGE-*`/`ROUTE-*` 实体、0 个单页面文档、页面到 API 的引用几乎为零链接。
5. knowledge-base-context 检索不准确、非渐进、无强制：渐进细节全部下沉 references，正文无逐层门禁、无输出门禁、无准确性自查。

执行日志进一步证实机制级根因：产物由后台子 Agent 直接写入、无模板符合性复核环节；目标项目的本地检查 hook 失效且 non-blocking；global-validation 现有清单只核对范围登记、链接、稳定 ID、分类、计数、占位符、敏感信息和服务导航，**不核对任何内容完整性维度**。

## What Changes

- `knowledge-base-api`：完成条件补"主文件+参数与报文配套文件必须同时存在、主文件遵循 11 节模板"硬验收；索引强制同时存在对外/对内两个分区；新增第三执行模式"页面链路模式"，消费 pages 登记的候选清单生成对内 REST 文档。
- `knowledge-base-base-info`：完成条件补"配置键清单逐键完整、来源文件键数与文档收录键数一致、配置文档遵循 10 节模板"硬验收；澄清脱敏边界——脱敏对象是值不是键。
- `knowledge-base-pages`：指定模式按对象粒度分流；用户点名路由/菜单时必须逐路由深挖，生成 `PAGE-*`/`ROUTE-*` 单页面文档与完整 API 映射；未登记 REST 按契约格式登记 `API-CANDIDATE-*` 到 interfaces 索引对内分区（pages 唯一获准写 interfaces 的位置）。
- `knowledge-base-context`：四条证据路径改为逐层输出硬门禁；新增上下文包输出门禁（十三节必填、结论必须挂证据载体、就绪判定硬性化）；新增输出前准确性自查（稳定 ID 解析复核、逐字一致复核、候选强制、证据矩阵必填）。
- `knowledge-base-bootstrap`：global-validation 新增内容完整性维度——API 配套文件存在性与索引双分区、配置键数一致性、PAGE 级实体存在性、模板节结构符合性；任一不过判 `failed`。

## Capabilities

### New Capabilities

- `knowledge-base-artifact-enforcement`: 定义 KnowledgeBase 各领域 Skill 的模板符合性硬验收、配置键完整性核对、pages 指定模式粒度分流与逐路由深挖、pages→api 候选清单交接契约、context 逐层与输出门禁，以及 global-validation 的内容完整性验收维度。

### Modified Capabilities

无。现有 `managed-rule-lifecycle`、`progressive-context-routing`、`routing-conformance` 三个 capability 与本变更无直接关系。

## Impact

- 影响 `cadence-init/skills/knowledge-base-api/SKILL.md`、`knowledge-base-base-info/SKILL.md`、`knowledge-base-pages/SKILL.md`、`knowledge-base-context/SKILL.md`、`knowledge-base-bootstrap/SKILL.md`，必要时同步各 Skill 的 `references/` 指南以避免正文与指南冲突。
- 全部为 Markdown 文档改动，不新增代码、脚本、Hook 或运行时组件（遵守本仓库"非必要不编写代码"规则）。
- 不修改任何 assets 模板与 demo 文件，避免与存量正确产物产生格式漂移。
- 不修改 `knowledge-base-overview` 与 `knowledge-base-update`。
- 不修复已生成的业务项目 KnowledgeBase 产物（含 `/tmp/knowledge-base-3`）；旧产物仅作为回溯验收的验证输入。
- 强化后首次执行的耗时与产物体量会上升，属于有意为之的成本转移：把"事后发现内容丢失"的代价前移为"当次执行做完整"。
