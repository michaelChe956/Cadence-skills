---
name: knowledge-base-bootstrap
description: "Use when Codex 需要为 Java 与 Vue/React 存量项目首次建立 KnowledgeBase，或用户已显式授权重新初始化现有 Schema 4.0 KnowledgeBase，且已准备工程、数据模型、配置快照、中间件、接口和页面六领域范围。"
---

# KnowledgeBase 初始化

## 概述

以目标项目的 `cadence/knowledge-base/user-input/base-info.md` 为唯一入口。先校验六领域输入，再生成 Manifest Schema 4.0 和固定目录；输入不完整时停止，不扫描代码或生成半成品。

## 必读资源

- 执行前完整读取 `references/input-contract.md`。
- 缺失输入时引用 `user-input/` 下的模板，不代替用户填写。
- 使用 `assets/input-inventory-template.md` 生成输入解析清单。
- 使用 `assets/manifest-template.yaml` 生成 Manifest。
- 需要核对典型判定时读取 `references/demo.md`。

## 固定输入

```text
cadence/knowledge-base/user-input/
├── base-info.md
├── project-scope.md
├── data-model-scope.md
├── configuration-scope.md
├── middleware-scope.md
├── api-scope.md
├── page-scope.md
└── database-ddl.sql（可选）
```

用户输入和外部配置快照只读，不得覆盖、补写、复制或迁入知识库。

## 工作流程

1. 读取目标项目适用的代理规则，定位唯一输入入口。
2. 在读取六领域输入前检查目标目录中的既有 `cadence/knowledge-base/manifest.yaml`：
   - Manifest 存在且 `schema_version` 不是 `4.0` 时立即停止，不覆盖、不迁移、不删除。
   - Manifest 为 `4.0` 但用户未显式授权“重新初始化”时立即停止，不修改现有 KnowledgeBase。
   - 只有用户显式授权重新初始化现有 Schema 4.0 KnowledgeBase 时才可继续重建，并在输入清单记录授权来源；不得把普通初始化请求推断为重建授权。
3. 按 `references/input-contract.md` 校验六领域状态、资料引用和指定范围。
4. 数据模型为 `全量` 或 `指定` 时，确认至少一种可定位结构证据；DDL 可缺省，其他证据有效时继续，没有任何结构证据时停止或要求改为 `不适用`。
5. 配置为 `全量` 或 `指定` 时，确认来源是锁定发布批次的不可变快照且外部目录可读。配置仓库必须固定到明确提交、标签或导出快照，不得使用持续变化的工作目录。校验范围摘要、纳入文件数量或清单摘要、服务摘要和文件规则摘要完整且相互一致；同一 `snapshot_id` 不得映射到不同环境或不同外部目录。分析开始和结束时分别计算最终快照指纹；指纹不一致、范围摘要不一致或目录内容变化时停止，且不得连接配置中心或远程环境补取。
6. 生成 `input-inventory.md` 与 `manifest.yaml`。只接受 `schema_version: "4.0"`，不兼容、不迁移其他版本；首次建立时 `generated_at` 写入本次生成时间，显式重新初始化时写入新知识库的首次生成时间；`open_questions.blocking/high/medium/low` 按新生成的待确认文档初始化为可审计计数。
7. 以 Manifest 的 `scope.projects`、`scope.data_models`、`scope.configurations`、`scope.middleware`、`scope.api` 和 `scope.pages` 作为领域 Skills 的唯一授权范围。
8. 初始化固定目录并执行一致性检查；状态为 `不适用` 的领域记录原因后跳过。

## 固定输出

```text
cadence/knowledge-base/
├── user-input/
├── input-inventory.md
├── manifest.yaml
├── README.md
├── base-information.md
├── development-guide.md
├── interfaces/
├── pages/
├── services/
├── data-models/
├── configurations/
├── evidence/
│   ├── source-index.md
│   └── traceability-matrix.md
├── domain-glossary.md
├── open-questions.md
└── change-history.md
```

只使用上述 Schema 4.0 目录，不读取或迁移其他版本目录。API 目录只使用 `interfaces/`。

## 安全与完成条件

- 只分析用户声明的本地工程、结构证据和外部快照目录，不连接外部系统。
- 不修改业务代码、DDL、运行配置或生产系统。
- 迁移文件、部署脚本、发布脚本和启动脚本只能作为只读证据，不得执行。
- 不输出密码、Token、AccessKey、Secret、密钥、私钥、完整连接串，以及内部域名、IP、URL 等敏感内部地址。Manifest 可以记录用户授权的本地文件系统路径；配置值中的内部端点必须脱敏，实际值统一写为 `<redacted>`，不得保存敏感值哈希或其他可关联的确定性衍生物。
- 配置证据写入 `evidence.configuration_snapshots.baseline`，最终快照指纹固定写入 `evidence.configuration_snapshots.baseline.fingerprint`；同时保存 `scope_summary`、纳入文件数量或清单摘要、服务摘要和文件规则摘要，不保存原始配置内容。
- 增量包状态写入 `update.processed_packages`；首次初始化为空列表。
- 既有 Manifest 的版本门禁和显式重新初始化授权已经通过；未经授权时没有覆盖任何 KnowledgeBase 文件。
- Manifest、输入清单、固定目录和六领域范围必须一致；同一快照标识的环境与目录映射唯一，重要结论必须有可信度与可定位证据。
