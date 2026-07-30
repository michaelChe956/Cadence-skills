# rule-config 初始化稳定性修复技术方案

## 1. 背景

`/rule-config --no-interrupt` 在新建或尚未创建 OpenSpec change 的 Coding 项目中会在仓库注册阶段失败。目标项目只应作为只读参考，本次修复仅修改 Cadence-skills 的 `bugfix-b-0730` 工作树。

已验证的故障链有两条：

1. OpenSpec 候选配置验证直接执行未携带 `--change` 的 `openspec instructions <artifact> --json`。当项目没有任何 change 时，OpenSpec 返回 `No changes found`，导致候选配置不能发布。
2. 源码项目检测对整个仓库执行无界 Glob，未排除 `.venv`、`venv`、`node_modules` 等依赖目录。参考项目一次命中 30,481 个文件，其中绝大多数来自 Python 虚拟环境，产生无关且截断的工具输出。

## 2. 目标与非目标

### 目标

- 新项目没有 `openspec/changes/<id>` 时，`rule-config` 仍能安全创建或合并 `openspec/config.yaml`。
- 候选配置继续在发布前经过真实 OpenSpec instructions 校验，失败时不修改目标配置。
- 源码检测只需证明项目包含源码，不扫描或输出依赖目录中的全部文件。
- 回归测试不再依赖已经归档的仓库内 change，并覆盖无 change 的验证前置条件。

### 非目标

- 不修改目标项目 `/Users/michaelche/Desktop/ontology`。
- 不改变 `rule-config` 的 OpenSpec 配置内容、L0/L1 合并规则或 CodeGraph 功能范围。
- 不将临时 validation change 发布到目标项目的 `openspec/changes/`。

## 3. 方案比较

| 方案 | 优点 | 缺点 | 结论 |
|---|---|---|---|
| 保留真实 instructions 验证，并创建临时 change | 保持原子发布前的语义校验；适用于全新项目 | 临时工作区多一个受控步骤 | 采用 |
| 仅校验 YAML 语法和字段类型 | 实现较简单 | 无法证明 OpenSpec 真能读取对应 artifact 规则 | 不采用 |
| 复用目标项目已有 change | 修改量小 | 新项目仍会失败，且依赖用户业务状态 | 不采用 |

## 4. 选定设计

### 4.1 有界源码探测

将项目类型检测改为一次有界的源码存在性探测：显式剪枝 `.git`、`.claude`、`.claude-plugin`、`.codex`、`.pi`、`.codegraph`、`cadence-init`、`Cadence-skills`、`.venv`、`venv`、`env`、`.env`、`node_modules`、`vendor`、构建目录和缓存目录；发现首个支持的源码文件后立即停止。

目录或主工程配置仍是 Coding 项目判定依据。探测不到源码不是工具失败，只返回“未发现源码”，再按现有主工程配置与默认策略继续判断。

### 4.2 OpenSpec 候选验证

1. 通过不会产生工具错误的存在性检查区分“目标 config 不存在”和“目标 config 已存在”。前者是正常初始状态。
2. 在与目标配置同一文件系统的临时工作区构建候选 `openspec/config.yaml`。
3. 仅在该临时工作区执行 `openspec new change cadence-rule-config-validation`，创建验证所需的 change 上下文。
4. 对 proposal、design、specs、tasks 依次执行 `openspec instructions <artifact> --change cadence-rule-config-validation --json`。
5. 四项均成功后才原子创建或替换目标 `openspec/config.yaml`；任一失败时清理或保留临时工作区以便诊断，但目标文件保持原样。

临时 change 只存在于临时验证工作区，不能进入目标项目或 Git 工作区。

### 4.3 回归验证

现有 Shell 生命周期参考模型将自行在验证工作区生成最小 change，而非复制仓库内某个具体 change。这样测试既不受归档目录移动影响，也直接覆盖“项目没有业务 change”这一失败场景。

测试将验证：

- 未携带 change 上下文的当前基线会失败；
- 生成临时 change 并带 `--change` 后四项 instructions 校验通过；
- `rule-config` 的源码探测文本明确剪枝常见依赖目录，避免无界 Glob 回归；
- 原有候选失败、备份失败与原子发布失败场景继续保持目标文件不变。

## 5. 成功标准

- 在没有 OpenSpec change 的新项目中，临时验证可通过并发布有效的 `openspec/config.yaml`。
- 依赖目录包含大量 Python 或 Node 文件时，源码探测只返回首个有效源码证据，不输出依赖文件清单。
- `cadence-init/skills/rule-config/tests/verify-managed-lifecycle.sh` 不再因缺少归档前路径失败，且全部断言通过。
- 目标项目没有任何新增、修改或删除。
